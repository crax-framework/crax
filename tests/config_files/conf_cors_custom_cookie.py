import os

try:
    from test_app_common.routers import Handler404, Handler500, Handler405
    from test_app_common.urls_two_apps import url_list
except ImportError:
    from ..test_app_common.urls_two_apps import url_list
    from ..test_app_common.routers import Handler404, Handler500, Handler405


ALLOWED_HOSTS = ["*"]
BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "qwerty1234567"
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
    "404_handler": Handler404,
    "405_handler": Handler405,
}

X_FRAME_OPTIONS = "DENY"
CORS_OPTIONS = {
    "origins": ["http://127.0.0.1:8000", "http://127.0.0.1:3000"],
    "methods": ["POST", "PATCH"],
    "headers": ["content-type"],
    "cors_cookie": "Allow-By-Cookie",
    "expose_headers": ["Exposed_One", "Exposed_Two"],
}
