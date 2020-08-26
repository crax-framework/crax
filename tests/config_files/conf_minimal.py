import os

try:
    from test_app_common.urls import url_list
except ImportError:
    from ..test_app_common.urls import url_list

ALLOWED_HOSTS = ["*"]
BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "qwerty1234567"
MIDDLEWARE = []

APPLICATIONS = ["test_app_common"]
URL_PATTERNS = url_list
STATIC_DIRS = []

DATABASES = {}
ERROR_HANDLERS = {}
