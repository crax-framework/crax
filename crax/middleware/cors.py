"""
Cross Origin Request Middleware. Checks if it was preflight request
and can be real request processed. In basic scheme only preflight request's
headers will be modified. So we can get data that was sent from cross origin.
However response will possibly can not be read. To make response modified as
cors special cookie name should be defined in project settings.
"""
import typing

from crax.response_types import TextResponse

from crax.middleware.base import ResponseMiddleware
from crax.utils import get_settings_variable


class CorsHeadersMiddleware(ResponseMiddleware):
    @staticmethod
    def check_allowed(param: typing.Any, check: set) -> typing.Optional[str]:
        if param != "*":
            if not isinstance(param, list):
                param = set([x.strip() for x in param.split(",")])
            if "*" in param:
                param = "*"

        if param == "*":
            return param
        else:
            if len(check.intersection(param)) == len(check):
                if isinstance(param, (set, list)):
                    return ", ".join(param)
                else:
                    return param

    async def process_headers(self) -> typing.Any:
        response = await super(CorsHeadersMiddleware, self).process_headers()
        cors_options = get_settings_variable("CORS_OPTIONS", default={})
        preflight = True
        error = None
        status_code = 200
        if self.request.method == "OPTIONS":
            if not isinstance(cors_options, dict):
                error = RuntimeError("Cors options should be a dict")
                status_code = 500
                response = TextResponse(
                    self.request, str(error), status_code=status_code
                )
                return response

        origin = cors_options.get("origins", "*")
        method = cors_options.get("methods", "*")
        header = cors_options.get("headers", "*")
        expose_headers = cors_options.get("expose_headers", None)
        max_age = cors_options.get("max_age", "600")

        request_origin = self.request.headers.get("origin")
        request_method = self.request.headers.get("access-control-request-method")
        request_headers = self.request.headers.get("access-control-request-headers")

        if request_method is None:
            request_method = self.request.scope["method"]

        if self.request.method == "OPTIONS":
            if request_headers:
                request_headers = set(request_headers.split(","))
            else:
                request_headers = {"content-type"}
            request_method = {request_method}
            request_origin = {request_origin}
            if header != "*" and "cors_cookie" in cors_options:
                if "*" in header:
                    pass  # pragma: no cover
                else:
                    header = [x for x in header]
                    header.append(cors_options["cors_cookie"].lower())

            cors_headers = self.check_allowed(header, request_headers)
            if cors_headers is None:
                error = RuntimeError(
                    f"Cross Origin Request with headers: "
                    f'"{list(request_headers)[0]}" not allowed on this server'
                )
                status_code = 400
            cors_methods = self.check_allowed(method, request_method)
            if cors_methods is None:
                error = RuntimeError(
                    f"Cross Origin Request with method: "
                    f'"{list(request_method)[0]}" not allowed on this server'
                )
                status_code = 400

            cors_origins = self.check_allowed(origin, request_origin)
            if cors_origins is None:
                error = RuntimeError(
                    f"Cross Origin Request from: "
                    f'"{list(request_origin)[0]}" not allowed on this server'
                )
                status_code = 400

        elif (
            "cors_cookie" in cors_options
            and cors_options["cors_cookie"].lower() in self.request.headers
        ):
            preflight = False
            if not isinstance(origin, str):
                cors_origins = ", ".join(origin)
            else:
                cors_origins = origin

            if not isinstance(method, str):
                cors_methods = ", ".join(method)
            else:
                cors_methods = method
            if not isinstance(header, str):
                cors_headers = ", ".join(header)
            else:
                cors_headers = header
        else:
            return response

        if error is None:
            cors_headers = [
                (b"Access-Control-Allow-Origin", cors_origins.encode("latin-1")),
                (b"Access-Control-Allow-Methods", cors_methods.encode("latin-1")),
                (b"Access-Control-Allow-Headers", cors_headers.encode("latin-1")),
                (b"Access-Control-Max-Age", max_age.encode("latin-1")),
                (b"Vary", b"Origin"),
            ]

            if expose_headers is not None and preflight is True:
                if isinstance(expose_headers, str):
                    expose_headers = [x.strip() for x in expose_headers.split(",")]
                assert type(expose_headers) == list
                cors_headers.append(
                    (b"Access-Control-Expose-Headers", ", ".join(expose_headers).encode("latin-1"))
                )

            if preflight is False:
                if self.request.content_type is not None:
                    cors_headers.append(
                        (b"Content-Type", self.request.content_type.encode("latin-1"))
                    )
            self.headers.append(cors_headers)
            response.headers.extend(*self.headers)
        else:
            response = TextResponse(self.request, str(error), status_code=status_code)

        return response
