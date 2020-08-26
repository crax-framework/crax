import os

try:
    from test_app_common.routers import Handler404, Handler500, Handler405
    from test_app_common.urls_two_apps import url_list
except ImportError:
    from tests.test_app_common.urls_two_apps import url_list
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
STATIC_DIRS = ["static", "test_app_common/static"]

DATABASES = {}
ERROR_HANDLERS = {
    "500_handler": Handler500,
    "404_handler": Handler404,
    "405_handler": Handler405,
}
DISABLE_LOGS = False
LOG_FILE = "app.log"
LOGGER_NAME = "test_logger"
LOG_LEVEL = "DEBUG"
LOG_CONSOLE = True
X_FRAME_OPTIONS = "DENY"
