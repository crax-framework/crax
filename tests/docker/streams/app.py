import os

from crax import Crax
from .urls import url_list


BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = "qwerty1234567"
MIDDLEWARE = [
    "crax.auth.middleware.AuthMiddleware",
    "crax.auth.middleware.SessionMiddleware",
]

APPLICATIONS = ["streams"]
URL_PATTERNS = url_list
STATIC_DIRS = ["static", "streams/static"]

DATABASES = {
    "default": {"driver": "sqlite", "name": f"/{BASE_URL}/test_crax.sqlite"},
}
app = Crax(settings="streams.app", debug=True)
