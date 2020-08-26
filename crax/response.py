"""
Crax Response. Resolves path that given in Request object, checks if
path static or path that should be handled with view. If handler found
it checks whether or not request method can be processed by view.
If no errors detected processed request, otherwise handles error
depending if debug mode is on or off.
"""
import binascii
import inspect
import os
import re
import typing
from base64 import b64decode

import itsdangerous
from itsdangerous import BadTimeSignature, BadSignature, SignatureExpired

from crax.data_types import Request, Scope, Receive, Send
from crax.exceptions import (
    CraxEmptyMethods,
    CraxMethodNotAllowed,
    CraxNoMethodGiven,
    CraxPathNotFound,
    CraxForbidden,
    CraxImproperlyConfigured,
    CraxUnauthorized)
from crax.response_types import FileResponse, TextResponse
from crax.utils import get_error_handler, get_settings_variable, unpack_urls
from crax.views import DefaultCrax, DefaultError


class Response:
    available_methods = []

    def __init__(self, request: Request, debug: bool = False) -> None:
        self.debug = debug
        self.request = request
        self.url_patterns = get_settings_variable("URL_PATTERNS")
        self.enable_csrf = get_settings_variable("ENABLE_CSRF")
        self.error_handlers = get_settings_variable("ERROR_HANDLERS")
        self.static_dirs = get_settings_variable("STATIC_DIRS", default=["static"])
        self.base_url = get_settings_variable(
            "BASE_URL",
            default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        self.headers = {}
        self.status = 200
        self.errors = None

    def resolve_path(self) -> typing.Optional[typing.Callable]:
        handler = None
        url_list = list(unpack_urls(self.url_patterns))
        if not url_list:
            handler = DefaultCrax
        else:
            for url in url_list:
                handler = url.get_match(self.request)
                if handler is not None:
                    handler = url.get_match(self.request)
                    break
            if handler is None:
                if self.request.scheme in ["http", "http.request"]:
                    if self.debug is True:
                        handler = DefaultError(
                            self.request, CraxPathNotFound(self.request.path)
                        )
                    else:
                        handler = get_error_handler(CraxPathNotFound(self.request.path))

                elif self.request.scheme == "websocket":
                    raise CraxPathNotFound(self.request.path)
        return handler

    def check_allowed(self, handler: typing.Callable):
        errors = None
        if self.request.user is not None:
            if hasattr(handler, "login_required"):
                login_required = handler.login_required
                if (
                    hasattr(self.request.user, "pk")
                    and self.request.user.pk == 0
                    and login_required is True
                ):
                    errors = {
                        "error_handler": CraxUnauthorized,
                        "error_message": self.request.path,
                        "status_code": 401,
                    }

            if hasattr(handler, "staff_only"):
                staff_only = handler.staff_only
                if self.request.user.is_staff is False and staff_only is True:
                    errors = {
                        "error_handler": CraxForbidden,
                        "error_message": self.request.path,
                        "status_code": 403,
                    }

            if hasattr(handler, "superuser_only"):
                superuser_only = handler.superuser_only
                if self.request.user.is_superuser is False and superuser_only is True:
                    errors = {
                        "error_handler": CraxForbidden,
                        "error_message": self.request.path,
                        "status_code": 403,
                    }
        if hasattr(handler, "methods") and self.request.scheme in [
            "http",
            "http.request",
        ]:
            if self.enable_csrf is True and self.request.method in ["POST", "PATCH"]:
                if hasattr(handler, "enable_csrf") and handler.enable_csrf is True:
                    if "csrf_token" not in self.request.post:
                        errors = {
                            "error_handler": CraxForbidden,
                            "error_message": "CSRF token missed",
                            "status_code": 403,
                        }
                    elif not self.request.post["csrf_token"]:
                        errors = {
                            "error_handler": CraxForbidden,
                            "error_message": "CSRF token is empty",
                            "status_code": 403,
                        }
                    else:
                        secret_key = get_settings_variable("SECRET_KEY")
                        if secret_key is None:
                            raise CraxImproperlyConfigured(
                                '"SECRET_KEY" string should be defined in settings to use CSRF Protection'
                            )
                        try:
                            token = self.request.post["csrf_token"]
                            signer = itsdangerous.TimestampSigner(str(secret_key))
                            max_age = get_settings_variable(
                                "SESSION_EXPIRES", default=1209600
                            )
                            session_cookie = b64decode(token)
                            signer.unsign(session_cookie, max_age=max_age)
                        except (
                            binascii.Error,
                            BadTimeSignature,
                            BadSignature,
                            SignatureExpired,
                        ):
                            errors = {
                                "error_handler": CraxForbidden,
                                "error_message": "CSRF token is incorrect",
                                "status_code": 403,
                            }
            if not self.request.method:  # pragma: no cover
                errors = {
                    "error_handler": CraxNoMethodGiven,
                    "error_message": handler,
                    "status_code": 500,
                }

            elif not handler.methods:
                errors = {
                    "error_handler": CraxEmptyMethods,
                    "error_message": handler,
                    "status_code": 500,
                }
            else:
                handler.methods += ["HEAD", "OPTIONS"]
                if self.request.method not in handler.methods:
                    errors = {
                        "error_handler": CraxMethodNotAllowed,
                        "error_message": handler,
                        "status_code": 405,
                    }
        return errors

    def dispatch(self) -> typing.Callable:
        if not self.request.path.endswith("/"):
            self.static_dirs += ["swagger/static/"]
            detect_static = [
                x for x in self.request.path.split("/")
                if x in self.static_dirs or re.match(r"(\w+\.)(png|ico|css|js|jpeg|jpg)", x)
            ]
        else:
            detect_static = None
        if detect_static:
            try:
                crax_path = __import__(FileResponse.__module__)
                path = f"{crax_path.__path__[0]}{self.request.path}"
                os.stat(path)
                response = FileResponse(path)
            except FileNotFoundError:
                try:
                    os.stat(self.request.path)
                    response = FileResponse(self.request.path)
                except FileNotFoundError:
                    try:
                        os.stat(self.request.path[1:])
                        response = FileResponse(self.request.path[1:])
                    except FileNotFoundError:
                        try:
                            path = self.base_url + self.request.path
                            os.stat(path)
                            response = FileResponse(path)
                        except FileNotFoundError as e:
                            response = TextResponse(self.request, b"File not found", status_code=404)
        else:
            resolver = self.resolve_path()
            error = self.check_allowed(resolver)
            if not error:
                response = resolver
            else:
                if self.request.scheme in ["http", "http.request"]:
                    if self.debug is True:
                        response = DefaultError(
                            self.request,
                            error["error_handler"](error["error_message"]),
                            status_code=error["status_code"],
                        )
                    else:
                        response = get_error_handler(
                            error["error_handler"](error["error_message"])
                        )
                else:
                    raise error["error_handler"](error["error_message"])
        return response

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = self.dispatch()
        if response:
            if inspect.iscoroutinefunction(response):
                await response(self.request, scope, receive, send)
            else:
                if isinstance(response, FileResponse):
                    await response(scope, receive, send)
                else:
                    try:
                        _response = response(self.request)
                        await _response(scope, receive, send)
                    except (TypeError, RuntimeError):
                        await response(scope, receive, send)
