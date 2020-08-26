import os

try:
    from test_app_common.urls import url_list
except ImportError:
    from ..test_app_common.urls import url_list

ALLOWED_HOSTS = ["*"]
BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "qwerty1234567"
MIDDLEWARE = [
    "crax.middleware.x_frame.XFrameMiddleware",
    "crax.middleware.max_body.MaxBodySizeMiddleware",
    "crax.middleware.cors.CorsHeadersMiddleware",
]

APPLICATIONS = ["test_app_common"]
URL_PATTERNS = url_list
STATIC_DIRS = []

DATABASES = {}
ERROR_HANDLERS = {}
X_FRAME_OPTIONS = "DENY"
MAX_BODY_SIZE = 8
