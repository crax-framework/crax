import os

try:
    from test_app_auth.routers import Handler500, Handler403
    from test_app_common.urls import url_list
except ImportError:
    from ..test_app_auth.routers import Handler500, Handler403
    from ..test_app_common.urls import url_list

ALLOWED_HOSTS = ["*"]
BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


MIDDLEWARE = [
    "crax.auth.middleware.AuthMiddleware",
    "crax.middleware.x_frame.XFrameMiddleware",
    "crax.middleware.max_body.MaxBodySizeMiddleware",
    "crax.auth.middleware.SessionMiddleware",
    "crax.middleware.cors.CorsHeadersMiddleware",
]

APPLICATIONS = ["tests", "test_app", "test_app_auth"]
URL_PATTERNS = url_list
STATIC_DIRS = ["static", "test_app/static"]

DATABASES = {}

ERROR_HANDLERS = {
    "500_handler": Handler500,
    "403_handler": Handler403,
}
X_FRAME_OPTIONS = "DENY"
