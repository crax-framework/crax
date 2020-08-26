"""
Base classes to create views. Crax will work perfect without this.
Any handler that manages path (or scope of paths) can be written
without standard Crax views.
"""
import os
import re
import time
import traceback

import typing
from base64 import b64encode

import itsdangerous

from crax.data_types import ExceptionType, Request, Scope, Receive, Send
from crax.exceptions import CraxNoTemplateGiven, CraxImproperlyConfigured
from crax.response_types import JSONResponse, TextResponse
from crax.utils import get_settings_variable, unpack_urls
from jinja2 import (
    Environment,
    PackageLoader,
    FileSystemLoader,
    TemplateNotFound,
    Template,
)


def prepare_url(path: str) -> typing.Generator:
    pattern = re.compile("<([a-zA-Z0-9_]*)>")
    spl = (i for i in path.split("/") if i)
    parts = (
        re.search(pattern, i).group(0) if re.search(pattern, i) else i for i in spl
    )
    lst = ("".join(re.split(pattern, i)).split(":")[0] for i in parts)
    return lst


def create_path(lst: typing.Generator, namespace: str, kw: dict) -> str:
    res = ""
    for x in lst:
        param = x.replace("<", "").replace(">", "")
        if param in kw:
            res += f"/{kw[param]}"
        elif param:
            res += "/" + param
    path = f"/{'/'.join(namespace.split('.'))}{res}"
    return path


def url(*args: typing.Union[tuple, list], **kwargs: typing.Any) -> typing.Optional[str]:
    url_patterns = get_settings_variable("URL_PATTERNS")

    params = kwargs.keys()
    path = f'/{args[0]}/{"/".join(params)}/'
    match = None
    urls = unpack_urls(url_patterns)
    for route in urls:
        for u in route.urls:
            if u.name == args[0]:
                match = u
            else:
                if u.path == path:
                    match = u
                if u.type_ == "re_path":
                    m = re.match(u.path, path)
                    if m:
                        if len(params) == len(m.groupdict()):
                            match = u
                else:
                    split_req_path = [x for x in path.split("/") if x]
                    split_path = [x for x in u.path.split("/") if x]
                    intersection = set(split_req_path).intersection(split_path)
                    if len(intersection) == len(params):
                        match = u
    if match is not None:
        if match.type_ == "re_path":
            lst = prepare_url(match.path)
        else:
            lst = (x for x in match.path.split("/") if x)
        res = create_path(lst, match.namespace, kwargs)
        return res


def csrf_token():
    secret_key = get_settings_variable("SECRET_KEY")
    if secret_key is None:
        raise CraxImproperlyConfigured(
            '"SECRET_KEY" string should be defined in settings to use CSRF Protection'
        )

    signer = itsdangerous.TimestampSigner(str(secret_key))
    sign = signer.sign(str(int(time.time())))
    encoded = b64encode(sign)
    csrf_key = encoded.decode("utf-8")
    return csrf_key


class BaseView:
    methods = ["GET"]
    login_required = False
    staff_only = False
    superuser_only = False
    enable_csrf = True

    def __init__(
        self, request: Request, *args: typing.Any, **kwargs: typing.Any
    ) -> None:
        self.request = request
        self.kwargs = kwargs
        self.context = {}
        self.status_code = 200

    def get_status_code(self):
        if hasattr(self.request, "status_code"):
            self.status_code = self.request.status_code

        elif "status_code" in self.kwargs:
            self.status_code = self.kwargs["status_code"]

    async def get(self) -> typing.Callable:
        pass

    async def post(self) -> typing.Callable:
        pass

    async def put(self) -> typing.Callable:
        pass

    async def patch(self) -> typing.Callable:
        pass

    async def delete(self) -> typing.Callable:
        pass

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if self.request.method == "GET":
            self.request.status_code = 200
            response = await self.get()

        elif self.request.method == "POST":
            self.request.status_code = 201
            response = await self.post()

        elif self.request.method == "PUT":
            self.request.status_code = 204
            response = await self.put()

        elif self.request.method == "PATCH":
            self.request.status_code = 204
            response = await self.patch()

        elif self.request.method == "DELETE":
            self.request.status_code = 204
            response = await self.delete()
        else:
            response = TextResponse(self.request, b"", status_code=self.status_code)

        if response is not None:
            await response(scope, receive, send)


class JSONView(BaseView):
    def __init__(self, request, **kwargs) -> None:
        super(JSONView, self).__init__(request, **kwargs)
        self.get_status_code()

    async def create_context(self) -> JSONResponse:
        response = JSONResponse(self.request, self.context, status_code=self.status_code)
        return response

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await super(JSONView, self).__call__(scope, receive, send)
        if self.request.method == "GET":
            response = await self.create_context()
            await response(scope, receive, send)


class WsView(BaseView):
    async def on_connect(self, scope: Scope, receive: Receive, send: Send) -> None:
        await send({"type": "websocket.accept"})

    async def on_disconnect(self, scope: Scope, receive: Receive, send: Send) -> None:
        pass

    async def on_receive(self, scope: Scope, receive: Receive, send: Send) -> None:
        pass

    async def dispatch(self, scope: Scope, receive: Receive, send: Send) -> None:

        while True:
            event = await receive()
            if event["type"] == "websocket.connect":
                await self.on_connect(scope, receive, send)

            if event["type"] == "websocket.disconnect":
                break

            if event["type"] == "websocket.receive":
                self.kwargs = event
                await self.on_receive(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self.dispatch(scope, receive, send)


class TemplateView(BaseView):
    template = None

    def __init__(self, request: Request = None, **kwargs: typing.Any) -> None:
        super(TemplateView, self).__init__(request=None, **kwargs)
        self.request = request
        self.kwargs = kwargs
        self.apps = get_settings_variable("APPLICATIONS")
        self.get_status_code()

    def format_traceback(self, trace: ExceptionType) -> None:
        ex_class = trace.__class__.__name__
        ex_value = trace
        if hasattr(trace, "status_code"):
            self.status_code = trace.status_code
        _traceback = traceback.format_exception(
            etype=type(trace), value=trace, tb=trace.__traceback__
        )
        self.context.update(
            {
                "ex_class": ex_class,
                "ex_value": ex_value,
                "traceback": _traceback,
                "status_code": self.status_code,
            }
        )

    def get_template(self) -> Template:

        if (
            not self.apps
            or "error_message" in self.kwargs
            or self.template in ["default.html", "swagger.html"]
        ):
            env = Environment(
                loader=PackageLoader("crax", "templates/"),
                autoescape=True,
                enable_async=True,
            )
            template = env.get_template(self.template)
        else:
            template_dirs = [".", "crax"]
            for app in self.apps:
                template_dirs += [
                    root for root, _, _ in os.walk(app) if "templates" in root
                ]
            env = Environment(
                loader=FileSystemLoader(template_dirs),
                autoescape=True,
                enable_async=True,
            )
            template = env.get_template(self.template)
        env.globals.update(url=url)
        env.globals.update(csrf_token=csrf_token)
        custom_functions = get_settings_variable("TEMPLATE_FUNCTIONS")
        if custom_functions and isinstance(custom_functions, list):
            for func in custom_functions:
                env.globals.update(**{func.__name__: func})
        return template

    async def create_error_content(self, ex: ExceptionType, status_code: int) -> str:
        self.status_code = status_code
        env = Environment(
            loader=PackageLoader("crax", "templates/"),
            autoescape=True,
            enable_async=True,
        )
        template = env.get_template("error.html")
        self.format_traceback(ex)
        content = await template.render_async(**self.context)
        return content

    async def render_response(self) -> TextResponse:
        if self.template:
            try:
                template = self.get_template()
                if self.request:
                    self.kwargs["user"] = self.request.user
                content = await template.render_async(**self.context)
                response = TextResponse(
                    self.request, content, status_code=self.status_code
                )
            except TemplateNotFound as ex:
                self.status_code = 404
                content = await self.create_error_content(ex, 404)
                response = TextResponse(self.request, content)
        else:
            self.status_code = 500
            content = await self.create_error_content(
                CraxNoTemplateGiven(self.request.path), 500
            )
            response = TextResponse(self.request, content)
        response.status_code = self.status_code
        return response

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await super(TemplateView, self).__call__(scope, receive, send)
        if self.request.method == "GET":
            response = await self.render_response()
            await response(scope, receive, send)


class DefaultError(TemplateView):
    template = "error.html"

    def __init__(
        self, request: Request, ex: ExceptionType, **kwargs: typing.Any
    ) -> None:
        self.request = request
        self.kwargs = kwargs
        self.ex = ex
        super(DefaultError, self).__init__(request, **kwargs)

    async def render_response(self) -> TextResponse:
        env = Environment(
            loader=PackageLoader("crax", "templates/"),
            enable_async=True,
            autoescape=True,
        )
        template = env.get_template(self.template)
        self.format_traceback(self.ex)
        content = await template.render_async(**self.context)
        response = TextResponse(self.request, content, status_code=self.status_code)
        response.status_code = self.status_code
        return response

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = await self.render_response()
        await response(scope, receive, send)


class DefaultCrax(TemplateView):
    template = "default.html"


class SwaggerCrax(TemplateView):
    template = "swagger.html"
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
    enable_csrf = False
