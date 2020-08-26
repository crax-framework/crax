import json
import sys

from crax.response_types import JSONResponse, TextResponse
from crax.views import TemplateView, WsView
from jinja2 import Environment, PackageLoader


class Home(TemplateView):
    template = "index.html"
    methods = ["GET"]


class GuestView:
    def __init__(self, request):
        self.request = request

    async def __call__(self, scope, receive, send):
        response = TextResponse(self.request, "Testing Custom View")
        await response(scope, receive, send)


class EmptyView:
    def __init__(self, request):
        self.request = request

    async def __call__(self, scope, receive, send):
        response = TextResponse(self.request, None)
        await response(scope, receive, send)


class BytesView:
    def __init__(self, request):
        self.request = request

    async def __call__(self, scope, receive, send):
        response = TextResponse(self.request, b"Testing bytes")
        await response(scope, receive, send)


async def guest_view_coroutine(request, scope, receive, send):
    env = Environment(
        loader=PackageLoader("tests.test_app_common", "templates/"), autoescape=True
    )
    template = env.get_template("index.html")
    content = template.render()
    response = TextResponse(request, content)
    await response(scope, receive, send)


class PostView:
    methods = ["GET", "POST"]

    def __init__(self, request):
        self.request = request

    async def __call__(self, scope, receive, send):
        if self.request.method == "POST":
            self.context = {"data": self.request.post["data"]}
            response = JSONResponse(self.request, self.context)
        else:
            response = TextResponse(self.request, "Text content")
        await response(scope, receive, send)


class PostViewTemplateView(TemplateView):
    template = "index.html"
    methods = ["GET", "POST"]

    async def post(self):
        self.context = {"data": self.request.post["data"]}
        env = Environment(
            loader=PackageLoader("tests.test_app_common", "templates/"),
            autoescape=True,
        )
        template = env.get_template("index.html")
        content = template.render(self.context)
        response = TextResponse(self.request, content)
        return response


class PostViewTemplateRender:
    methods = ["GET", "POST"]

    def __init__(self, request):
        self.request = request

    async def __call__(self, scope, receive, send):
        if self.request.method == "POST":
            if isinstance(self.request.post, str):
                data = json.loads(self.request.post)
            else:
                data = self.request.post
            self.context = {"data": data["data"], "files": self.request.files}
            env = Environment(
                loader=PackageLoader("tests.test_app_common", "templates/"),
                autoescape=True,
            )
            template = env.get_template("index.html")
            content = template.render(self.context)
            response = TextResponse(self.request, content)
            await response(scope, receive, send)


async def guest_coroutine_view(request, scope, receive, send):
    env = Environment(
        loader=PackageLoader("tests.test_app_common", "templates/"), autoescape=True
    )
    template = env.get_template("index.html")
    content = template.render()
    response = TextResponse(request, content)
    await response(scope, receive, send)


class ZeroDivision(TemplateView):
    template = "index.html"
    methods = ["GET"]

    async def get(self):
        result = 1 / 0
        return result


class Handler500(TemplateView):
    template = "500.html"

    async def get(self):
        self.request.status_code = 500


class Handler404:
    def __init__(self, request):
        self.request = request

    async def __call__(self, scope, receive, send):
        response = TextResponse(self.request, "Testing Not Found")
        response.status_code = 404
        await response(scope, receive, send)


class Handler405:
    def __init__(self, request):
        self.request = request

    async def __call__(self, scope, receive, send):
        response = JSONResponse(self.request, {"Error": "Testing Method Not Allowed"})
        response.status_code = 405
        await response(scope, receive, send)


class WsEcho(WsView):
    async def on_connect(self, scope, receive, send) -> None:
        sys.stdout.write("Accepted\n")
        await send({"type": "websocket.accept"})

    async def on_receive(self, scope, receive, send):
        await send({"type": "websocket.send", "text": self.kwargs["text"]})
