"""
Authentication backend middleware classes that might be activated in project settings
"""
import binascii
import json
import time
from base64 import b64decode

import typing

from crax.data_types import Request
from itsdangerous import BadTimeSignature, SignatureExpired, BadSignature

from crax.auth.models import User
from crax.auth.authentication import (
    AnonymousUser,
    create_session_signer,
    create_session_cookie,
)
from crax.middleware.base import RequestMiddleware, ResponseMiddleware


class AuthMiddleware(RequestMiddleware):
    def __init__(self, **kwargs: typing.Any) -> None:
        super(AuthMiddleware, self).__init__(**kwargs)
        self.signer, self.max_age, self.cookie_name, _ = create_session_signer()

    async def process_headers(self) -> Request:
        if self.cookie_name in self.request.cookies:
            session_cookie = self.request.cookies[self.cookie_name]
            try:
                session_cookie = b64decode(session_cookie)
                user = self.signer.unsign(session_cookie, max_age=self.max_age)
                user = user.decode("utf-8")
                user_id = user.split(":")[1]
                if user_id != "0":
                    query = User.select().where(User.c.id == int(user_id))
                    user = await User.query.fetch_one(query=query)
                    if user:
                        if user["last_name"] is not None:
                            full_name = (
                                f'{user["username"]}'
                                f' {user["first_name"]} {user["last_name"]}'
                            )
                        else:
                            full_name = f'{user["username"]} {user["first_name"]}'
                        request_user = User
                        request_user.pk = user["id"]
                        request_user.username = user["username"]
                        request_user.is_staff = bool(user["is_staff"])
                        request_user.is_superuser = bool(user["is_superuser"])
                        request_user.is_active = bool(user["is_active"])
                        request_user.full_name = full_name
                        request_user.session = self.request.cookies[self.cookie_name]
                        self.request.user = User()
                        self.request.user.session = self.request.cookies[
                            self.cookie_name
                        ]
                    else:  # pragma: no cover
                        # Stupid case if user was removed from database but session cookies are sent
                        self.request.user = AnonymousUser()
                else:
                    self.request.user = AnonymousUser()
            except (binascii.Error, BadTimeSignature, BadSignature, SignatureExpired):
                self.request.user = AnonymousUser()
        else:
            self.request.user = AnonymousUser()
        return self.request


class SessionMiddleware(ResponseMiddleware):
    def __init__(self, **kwargs: typing.Any):
        super(SessionMiddleware, self).__init__(**kwargs)
        self.signer, self.max_age, self.cookie_name, _ = create_session_signer()

    async def process_headers(self) -> None:
        response = await super(SessionMiddleware, self).process_headers()
        anonymous_cookie = create_session_cookie(str(int(time.time())), 0)[1]
        if self.request.session:
            session = json.loads(self.request.session)
            session_value = list(session.values())[0]
            try:
                spl = list(session)[0].split(":")
                if int(spl[1]) != 0:
                    session_cookie = b64decode(session_value)
                    self.signer.unsign(session_cookie, max_age=self.max_age)
                    cookie = create_session_cookie(
                        spl[0], spl[1], session=session_value
                    )[1]
                else:
                    cookie = anonymous_cookie
                self.request.session = {}
            except (
                binascii.Error,
                BadTimeSignature,
                BadSignature,
                SignatureExpired,
            ):
                cookie = anonymous_cookie
            self.headers.append((b"Set-Cookie", cookie.encode("latin-1")))
        else:
            if self.cookie_name in self.request.cookies:
                session_cookie = self.request.cookies[self.cookie_name]
                try:
                    session_cookie = b64decode(session_cookie)
                    self.signer.unsign(session_cookie, max_age=self.max_age)
                except (
                    binascii.Error,
                    BadTimeSignature,
                    BadSignature,
                    SignatureExpired,
                ):  # pragma: no cover
                    # No need to cover this case 'cause same cases covered above several times
                    self.headers.append(
                        (b"Set-Cookie", anonymous_cookie.encode("latin-1"))
                    )
            else:
                self.headers.append(
                    (b"Set-Cookie", anonymous_cookie.encode("latin-1"))
                )
        response.headers += self.headers
        return response
