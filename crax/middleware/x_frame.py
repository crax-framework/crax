"""
Dummy Clickjacking Protection.
"""
from crax.middleware.base import RequestMiddleware
from crax.utils import get_settings_variable

from crax.data_types import Request


class XFrameMiddleware(RequestMiddleware):
    async def process_headers(self) -> Request:
        x_frame_options = get_settings_variable("X_FRAME_OPTIONS", default="SAMEORIGIN")
        self.request.response_headers["X-Frame-Options"] = x_frame_options
        return self.request
