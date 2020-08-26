"""
Configuration example file. Also used if no real configuration is given.
"""
import os

# ######################## BASE ######################################
BASE_URL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIRS = ["static"]
URL_PATTERNS = []
APPLICATIONS = ["crax"]
MIDDLEWARE = []
ALLOWED_HOSTS = ["*"]
SECRET_KEY = ""
DATABASES = {}
ERROR_HANDLERS = {}


# ######################## AUTH ######################################
SESSION_COOKIE_NAME = "session_id"
SESSION_EXPIRES = 14 * 24 * 60 * 60


# ######################## MIDDLEWARE ######################################
CORS_OPTIONS = {"origins": ["http://localhost:8080"], "cors_cookie": "zzzzzz"}

X_FRAME_OPTIONS = "DENY"


# ######################## LOGGING ######################################
DISABLE_LOGS = False
LOGGING_BACKEND = "crax.logger.CraxLogger"
LOGGER_NAME = "crax"
LOG_FILE = ""
LOG_LEVEL = "INFO"
LOG_ROTATE_TIME = "midnight"
LOG_CONSOLE = False
LOG_STEAMS = []
ENABLE_SENTRY = True
SENTRY_LOG_LEVEL = "INFO"
SENTRY_EVENT_LEVEL = "ERROR"
LOG_SENTRY_DSN = ""
