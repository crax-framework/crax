"""
Max body size protection middleware that checks if request body is not
larger then defined in project settings. Surly we can manage this with
web server options, but why not?
"""
import typing

from crax.data_types import ExceptionType
from crax.middleware.base import RequestMiddleware
from crax.utils import get_settings_variable

from crax.data_types import Request


class MaxBodySizeMiddleware(RequestMiddleware):
    async def process_headers(self) -> typing.Union[Request, ExceptionType]:
        max_body = get_settings_variable("MAX_BODY_SIZE", default=1024 * 1024)
        content_length = self.request.headers.get("content-length")
        if content_length and int(content_length) > int(max_body):
            self.request.status_code = 400
            return RuntimeError(
                f"Too large body. Allowed body size up to {max_body} bytes"
            )
        return self.request
