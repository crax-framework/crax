import os

from crax.urls import Route

try:
    from test_app_common.routers import Home
except ImportError:
    from ..test_app_common.routers import Home

ALLOWED_HOSTS = ["*"]
BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "qwerty1234567"
MIDDLEWARE = []

APPLICATIONS = ["test_app_common"]
URL_PATTERNS = [Route("/", Home)]
STATIC_DIRS = []

DATABASES = {}
ERROR_HANDLERS = {}
