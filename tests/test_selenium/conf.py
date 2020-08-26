import os

from crax import Crax
from crax.swagger.types import SwaggerInfo
from .urls import url_list
from crax.swagger import urls

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

DATABASES = {
    "default": {"driver": "sqlite", "name": f"/{os.path.dirname(os.path.abspath(__file__))}/test.sqlite"},
}

X_FRAME_OPTIONS = "DENY"
ENABLE_CSRF = True

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


def square_(a):
    return a * a


def hello():
    return "Hello world"


TEMPLATE_FUNCTIONS = [square_, hello]

CORS_OPTIONS = {
    "origins": ["*"],
    "methods": ["*"],
    "headers": ["content-type"],
    "cors_cookie": "Allow-By-Cookie",
}
DISABLE_LOGS = False
app = Crax(settings="test_selenium.app", debug=True)
