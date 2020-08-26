"""
Common functions for default auth backend
"""
import datetime
import hashlib
import hmac
import json
from base64 import b64decode, b64encode

import itsdangerous
import typing

from crax.auth.models import AnonymousUser, User
from crax.data_types import Request
from crax.exceptions import CraxImproperlyConfigured
from crax.utils import get_settings_variable


def create_password(password: str) -> str:
    secret = get_settings_variable("SECRET_KEY")
    if not secret:
        raise CraxImproperlyConfigured(
            '"SECRET_KEY" variable should be defined to use Authentication backends'
        )
    secret = secret.encode()
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), secret, 100000)
    return hashed.hex()


def check_password(hashed: str, password: str) -> bool:
    secret = get_settings_variable("SECRET_KEY")
    if not secret:
        raise CraxImproperlyConfigured(
            '"SECRET_KEY" variable should be defined to use Authentication backends'
        )
    secret = secret.encode()
    return hmac.compare_digest(
        bytearray.fromhex(hashed),
        hashlib.pbkdf2_hmac("sha256", password.encode(), secret, 100000),
    )


def create_session_signer() -> tuple:
    secret_key = get_settings_variable("SECRET_KEY")
    if secret_key is None:
        raise CraxImproperlyConfigured(
            '"SECRET_KEY" string should be defined in settings to use Crax Sessions'
        )
    signer = itsdangerous.TimestampSigner(str(secret_key), algorithm=itsdangerous.signer.HMACAlgorithm())
    max_age = get_settings_variable("SESSION_EXPIRES", default=1209600)
    cookie_name = get_settings_variable("SESSION_COOKIE_NAME", default="session_id")
    same_site = get_settings_variable("SAME_SITE_COOKIE_MODE", default="lax")
    return signer, max_age, cookie_name, same_site


def create_session_cookie(username: str, pk: int, session: str = None) -> tuple:
    signer, max_age, cookie_name, same_site = create_session_signer()
    if session is None:
        sign = signer.sign(f"{username}:{pk}")
        encoded = b64encode(sign)
        session = encoded.decode("utf-8")
    session_cookie = (
        f"{cookie_name}={session}; path=/;"
        f" Max-Age={max_age}; httponly; samesite={same_site}"
    )
    return session, session_cookie


async def set_user(
    request: Request, username: str, password: str, user_pk: int = 0
) -> None:
    request.session = {}
    query = User.select().where(User.c.username == username)
    user = await User.query.fetch_one(query=query)
    if user:
        hashed = user["password"]
        pk = user["id"]
        res = check_password(hashed, password)
        if res is True:
            if user["last_name"] is not None:
                full_name = f'{username} {user["first_name"]} {user["last_name"]}'
            else:
                full_name = f'{username} {user["first_name"]}'
            request_user = User
            request_user.pk = pk
            request_user.username = username
            request_user.is_staff = bool(user["is_staff"])
            request_user.is_superuser = bool(user["is_superuser"])
            request_user.is_active = bool(user["is_active"])
            request_user.full_name = full_name
            session_cookie = create_session_cookie(username, pk)[0]
            signed = {f"{username}:{pk}": session_cookie}
            if user_pk == 0:
                request.session = json.dumps(signed)
                request_user.session = signed
            request.user = request_user()
        else:
            request.user = AnonymousUser()
    else:
        request.user = AnonymousUser()


async def login(
    request: Request, username: str, password: str
) -> typing.Union[User, AnonymousUser]:
    secret = get_settings_variable("SECRET_KEY")
    signer = itsdangerous.TimestampSigner(str(secret))
    max_age = get_settings_variable("SESSION_EXPIRES", default=1209600)
    cookie_name = get_settings_variable("SESSION_COOKIE_NAME", default="session_id")

    if not secret:
        raise CraxImproperlyConfigured(
            '"SECRET_KEY" variable should be defined to use Authentication backends'
        )
    if hasattr(request, "cookies"):
        cookies = request.cookies
        if cookie_name in cookies:
            session_cookie = cookies[cookie_name]
            session_cookie = b64decode(session_cookie)
            user = signer.unsign(session_cookie, max_age=max_age)
            user = user.decode("utf-8")
            await set_user(request, username, password, user_pk=int(user.split(":")[1]))
        else:
            await set_user(request, username, password)
    return request.user


async def logout(request: Request) -> None:
    if "cookie" in request.headers:
        del request.headers["cookie"]
    request.user = None


async def create_user(username: str, password: str, **kwargs) -> None:
    password = create_password(password)
    values = {
        "username": username,
        "password": password,
        "first_name": kwargs.get("first_name"),
        "middle_name": kwargs.get("middle_name", ""),
        "last_name": kwargs.get("last_name", ""),
        "phone": kwargs.get("phone", ""),
        "email": kwargs.get("email", ""),
        "is_active": kwargs.get("is_active", True),
        "is_staff": kwargs.get("is_staff", False),
        "is_superuser": kwargs.get("is_superuser", False),
        "date_joined": datetime.datetime.now(),
        "last_login": datetime.datetime.now(),
    }
    await User.query.insert(query=User.table.insert(), values=values)
