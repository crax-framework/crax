import os

from crax import Crax
from crax.swagger.types import SwaggerInfo
from crax.swagger import urls

try:
    from test_selenium.urls import url_list
except ImportError:
    from ..test_selenium.urls import url_list


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

APPLICATIONS = ["test_selenium"]
URL_PATTERNS = url_list + urls
STATIC_DIRS = ["static", "test_selenium/static"]


TEST_MODE = os.environ["CRAX_TEST_MODE"]
DB_USERS = {"postgresql": "postgres", "mysql": "root", "sqlite": "root"}
DB_NAMES = {
    "postgresql": "test_crax",
    "mysql": "test_crax",
    "sqlite": f"/{BASE_URL}/test_crax.sqlite",
}
if TEST_MODE != "sqlite":
    OPTIONS = {"min_size": 5, "max_size": 20}
else:
    OPTIONS = {}


def get_db_host():
    docker_db_host = os.environ.get("DOCKER_DATABASE_HOST", None)
    if docker_db_host:
        host = docker_db_host
    else:
        host = "127.0.0.1"
    return host


if "TRAVIS" not in os.environ:
    DATABASES = {
        "default": {
            "driver": TEST_MODE,
            "host": get_db_host(),
            "user": "crax",
            "password": "CraxPassword",
            "name": DB_NAMES[TEST_MODE],
            "options": OPTIONS,
        },
    }

else:
    DATABASES = {
        "default": {
            "driver": TEST_MODE,
            "host": "127.0.0.1",
            "user": DB_USERS[TEST_MODE],
            "password": "",
            "name": DB_NAMES[TEST_MODE],
            "options": OPTIONS,
        },
    }


SWAGGER = SwaggerInfo(
    description="This is a simple example of OpenAPI (Swagger) documentation. "
    " You can find out more about Swagger at "
    "[http://swagger.io](http://swagger.io) or on "
    "[irc.freenode.net, #swagger](http://swagger.io/irc/).  ",
    version="0.0.3",
    title="Crax Swagger Example",
    termsOfService="https://github.com/ephmann/crax",
    contact={"email": "ephmanns@gmail.com"},
    license={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    servers=[
        {"url": "http://127.0.0.1:8000", "description": "Development server http"},
        {"url": "https://127.0.0.1:8000", "description": "Staging server"},
    ],
    basePath="/api",
)


X_FRAME_OPTIONS = "DENY"
ENABLE_CSRF = True


def square_(a):
    return a * a


def hello():
    return "Hello world"


TEMPLATE_FUNCTIONS = [square_, hello]
app = Crax(settings='tests.config_files.conf_csrf')
