import os

from crax import Crax

try:
    from test_app_auth.routers import Handler500
    from test_app_auth.urls_auth import url_list
except ImportError:
    from ..test_app_auth.routers import Handler500
    from ..test_app_auth.urls_auth import url_list

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

APPLICATIONS = ["test_app_common", "test_app_auth"]
URL_PATTERNS = url_list
STATIC_DIRS = ["static", "test_app/static"]

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


ERROR_HANDLERS = {
    "500_handler": Handler500,
}

X_FRAME_OPTIONS = "DENY"
app = Crax(settings='tests.config_files.conf_auth_right')
