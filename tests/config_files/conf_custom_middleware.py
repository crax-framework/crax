import os

try:
    from test_app_common.urls_two_apps import url_list
except ImportError:
    from ..test_app_common.urls_two_apps import url_list


ALLOWED_HOSTS = ["*"]
BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "qwerty1234567"
MIDDLEWARE = [
    "test_app.middleware.ReplaceMiddleware",
]

APPLICATIONS = ["test_app_common"]
URL_PATTERNS = url_list
