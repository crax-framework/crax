import os

from crax import Crax

try:
    from test_app_auth.routers import Handler500
    from test_app_auth.urls_auth import url_list
except ImportError:
    from ..test_app_auth.routers import Handler500
    from ..test_app_auth.urls_auth import url_list

ALLOWED_HOSTS = ["*"]
BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "qwerty1234567"
MIDDLEWARE = [
    "crax.auth.middleware.AuthMiddleware",
    "crax.middleware.x_frame.XFrameMiddleware",
    "crax.middleware.max_body.MaxBodySizeMiddleware",
    "crax.auth.middleware.SessionMiddleware",
    "crax.middleware.cors.CorsHeadersMiddleware",
]

APPLICATIONS = ["test_app_common", "test_app_auth"]
URL_PATTERNS = url_list
STATIC_DIRS = ["static", "test_app_common/static"]

ERROR_HANDLERS = {
    "500_handler": Handler500,
}

X_FRAME_OPTIONS = "DENY"
app = Crax(settings='tests.config_files.conf_db_missed')
