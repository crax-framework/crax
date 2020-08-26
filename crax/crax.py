"""
Project facade. All application work starts here. Several important
steps:
Start and Shutdown scripts ran.
Detected request type.
Request object created from each request's Scope object.
Project settings passed to environment.
Logging system activated.
Request object modified with request middleware.
Checked if there were no errors.
"""
import inspect
import os
import sys

import typing
from crax.data_types import Scope, Receive, Send
from crax.form_data import FormData
from crax.request import Request
from crax.response import Response
from crax.utils import collect_middleware, get_error_handler, get_settings_variable
from crax.views import DefaultError


class Crax:
    def __init__(
        self,
        settings: str = None,
        debug: bool = False,
        on_startup: typing.Union[typing.Callable, typing.Coroutine] = None,
    ) -> None:
        self.settings = settings
        self.debug = debug
        self.on_startup = on_startup
        self.errors = None
        self.request = None
        self.app_logger = None
        self.status_code = None
        self.db_connections = {}

        if not settings:
            os.environ["CRAX_SETTINGS"] = "crax.conf"
        else:
            try:
                __import__(settings)
                os.environ["CRAX_SETTINGS"] = settings
                disable_logging = get_settings_variable("DISABLE_LOGS", default=True)
                if disable_logging is False:
                    logging_backend = get_settings_variable(
                        "LOGGING_BACKEND", default="crax.logger.CraxLogger"
                    )
                    spl_middleware = logging_backend.split(".")
                    module = __import__(
                        ".".join(spl_middleware[:-1]), fromlist=spl_middleware[:-1]
                    )
                    logger = getattr(module, spl_middleware[-1])
                    app_logger = logger()
                    self.app_logger = app_logger.get_logger()

            except (ModuleNotFoundError, ImportError) as ex:
                self.errors = ex
                self.status_code = 500

    @staticmethod
    def process_resp_middleware(app, middleware_list):
        for cls in middleware_list:
            app = cls(app=app)
        return app

    async def process_middleware(self, base):
        middleware_list = await collect_middleware(base)
        if isinstance(middleware_list, list) and middleware_list:
            for middleware in middleware_list:
                processed = await middleware(request=self.request).process_headers()
                try:
                    self.request, self.errors = processed
                except TypeError:
                    if isinstance(processed, Request):
                        self.request = processed
                    else:
                        self.errors = processed
        elif not isinstance(middleware_list, list):
            self.errors = middleware_list
            self.status_code = 500

    async def process_errors(self, scope, receive, send):
        if self.status_code is not None:
            self.request.status_code = self.status_code

        if self.app_logger is not None:
            self.app_logger.critical(self.errors, exc_info=True)
        if self.debug is True:
            response = DefaultError(self.request, self.errors)
            await response(scope, receive, send)
        else:
            response = get_error_handler(self.errors)
            if response is not None:
                try:
                    await response(scope, receive, send)
                except TypeError:
                    _response = response(self.request)
                    await _response(scope, receive, send)

    async def _receive(self, receive: Receive) -> typing.AsyncGenerator:
        more_body = True
        while more_body:
            self.rec = await receive()
            more_body = self.rec.get("more_body", False)
            if self.rec["type"] == "http.request":
                body = self.rec.get("body", b"")
                if body:
                    yield body
            elif self.rec["type"] == "http.disconnect":  # pragma: no cover
                break
        yield b""

    async def process_request(self, scope: Scope, receive: Receive, send: Send) -> None:

        if self.errors is None:
            await self.process_middleware("RequestMiddleware")
            if self.errors is None:
                app = Response(self.request, self.debug)
                if scope["type"] in ["http", "http.request"]:
                    middleware_list = await collect_middleware("ResponseMiddleware")
                    app = self.process_resp_middleware(app, middleware_list)
                await app(scope, receive, send)
            else:
                await self.process_errors(scope, receive, send)
                self.errors = None
        else:
            await self.process_errors(scope, receive, send)
            self.errors = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            databases = get_settings_variable('DATABASES')
            message = await receive()
            if message["type"] == "lifespan.startup":
                if databases:
                    from crax.database.connection import create_connections
                    self.db_connections = await create_connections()
                start_message = "STARTING CRAX FRAMEWORK"
                sys.stdout.write(f"\033[36m{start_message}\033[0m \n")
                if self.on_startup is not None:
                    if inspect.iscoroutinefunction(self.on_startup):
                        await self.on_startup()
                    else:
                        self.on_startup()
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                if databases:
                    from crax.database.connection import close_pool
                    await close_pool(self.db_connections)
                await send({"type": "lifespan.shutdown.complete"})

        elif scope["type"] in ["http", "websocket"]:
            self.request = Request(scope)
            if "method" in scope and scope["method"] in ["POST", "PATCH"]:
                form_data = FormData(self.request, self._receive(receive))
                await form_data.process()

            if self.app_logger is not None:
                client = self.request.client
                server = self.request.server
                method = self.request.method
                user_agent = self.request.headers.get("user-agent", "Unknown")
                message = f'{scope["type"]} {method} {server} {client} {user_agent} {scope["path"]}'
                self.app_logger.info(message)
            try:
                await self.process_request(scope, receive, send)
            except Exception as ex:
                self.status_code = 500
                self.errors = ex
                await self.process_errors(scope, receive, send)
                self.errors = None
        else:
            raise NotImplementedError("Unknown request type")  # pragma: no cover
