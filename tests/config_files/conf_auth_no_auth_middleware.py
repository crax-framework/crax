import os

try:
    from test_app_auth.routers import Handler500, Handler403
    from test_app_auth.urls_auth import url_list
except ImportError:
    from ..test_app_auth.routers import Handler500, Handler403
    from ..test_app_auth.urls_auth import url_list

ALLOWED_HOSTS = ["*"]
BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "SuperSecretKey1234567"
MIDDLEWARE = [
    "crax.middleware.x_frame.XFrameMiddleware",
    "crax.middleware.max_body.MaxBodySizeMiddleware",
    "crax.middleware.cors.CorsHeadersMiddleware",
]

APPLICATIONS = ["test_app_common", "test_app_nested"]
URL_PATTERNS = url_list
STATIC_DIRS = ["static", "test_app/static"]

DATABASES = {}

ERROR_HANDLERS = {
    "500_handler": Handler500,
    "403_handler": Handler403,
}
X_FRAME_OPTIONS = "DENY"
