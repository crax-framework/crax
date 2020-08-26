import os

try:
    from test_app_common.urls import url_list
except ImportError:
    from ..test_app_common.urls import url_list

ALLOWED_HOSTS = ["*"]
BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "qwerty1234567"
MIDDLEWARE = [
    "crax.middleware.x_frame.XF",
]

APPLICATIONS = ["test_app_common", "test_app_nested"]
URL_PATTERNS = url_list
STATIC_DIRS = ["static", "test_app/static"]
