import json
from base64 import b64encode

import itsdangerous

from crax.auth import login, create_user
from crax.auth.authentication import logout
from crax.auth.models import User
from crax.response_types import JSONResponse, TextResponse
from crax.utils import get_settings_variable
from crax.views import TemplateView, BaseView
from .models import Customer


class Home(TemplateView):
    template = "index.html"
    methods = ["GET"]


class LoginRequired(TemplateView):
    login_required = True

    template = "index.html"
    methods = ["GET"]


class ProtectedView(LoginRequired):
    pass


class StaffRequired(TemplateView):
    staff_only = True

    template = "index.html"
    methods = ["GET"]


class SuperuserRequired(TemplateView):
    superuser_only = True

    template = "index.html"
    methods = ["GET"]


class AuthView(TemplateView):
    template = "index.html"
    methods = ["GET", "POST"]

    async def get(self):
        await login(self.request, "mark", "qwerty")

    async def post(self):
        username = self.request.post["username"]
        password = self.request.post["password"]
        await login(self.request, username, password)
        response = JSONResponse(
            self.request,
            {
                "username": username,
                "session": self.request.user.session,
                "pk": self.request.user.pk,
                "is_authenticated": self.request.user.is_authenticated,
                "is_active": self.request.user.is_active,
                "is_staff": self.request.user.is_staff,
                "is_superuser": self.request.user.is_superuser,
            },
        )
        return response


class CreateView(TemplateView):
    template = "index.html"
    methods = ["GET", "POST"]

    async def post(self):
        before_users = await User.query.all()
        username = self.request.post["username"]
        password = self.request.post["password"]
        first_name = self.request.post["first_name"]
        last_name = self.request.post["last_name"]
        await create_user(
            username,
            password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_superuser=False,
        )
        first_user = await User.query.first()
        new_user = await User.query.last()
        after_users = await User.query.all()
        await login(self.request, username, password)
        response = JSONResponse(
            self.request,
            {
                "first_username": first_user["username"],
                "username": new_user["username"],
                "len_before": len(before_users),
                "len_after": len(after_users),
                "names_after": [x["username"] for x in after_users],
            },
        )
        return response


class InsertView(TemplateView):
    template = "index.html"
    methods = ["GET", "POST"]

    async def post(self):
        before_users = await User.query.all()
        users = self.request.post["users"]
        if isinstance(json.loads(users), list):
            await User.query.bulk_insert(values=json.loads(users))
        else:
            await User.query.insert(values=json.loads(users))
        after_users = await User.query.all()
        response = JSONResponse(
            self.request,
            {"len_before": len(before_users), "len_after": len(after_users)},
        )
        return response


class WrongInsertView(TemplateView):
    template = "index.html"
    methods = ["GET"]

    async def get(self):
        await Customer.query.all()


class WrongMethodInsertView(TemplateView):
    template = "index.html"
    methods = ["GET"]

    async def get(self):
        await User.query.unexpected_method()


class WrongTableMethodView(TemplateView):
    template = "index.html"
    methods = ["GET"]

    async def get(self):
        await User.prefetch_seclect()


class LogoutView(TemplateView):
    template = "index.html"
    methods = ["GET"]

    async def get(self):
        await logout(self.request)


class WrongSessionView(BaseView):
    template = "index.html"
    methods = ["GET"]

    async def get(self):
        signer = itsdangerous.TimestampSigner("WrongKey")
        max_age = 600
        cookie_name = "session_id"
        sign = signer.sign("mark:4")
        encoded = b64encode(sign)
        session = encoded.decode("utf-8")
        session_cookie = (
            f"{cookie_name}={session}; path=/;"
            f" Max-Age={max_age}; httponly; samesite=lax"
        )
        signed = {"mark:4": session_cookie}
        self.request.session = json.dumps(signed)

        response = JSONResponse(self.request, {"user": self.request.session},)
        return response


class AnonymousSessionView(BaseView):
    template = "index.html"
    methods = ["GET"]

    async def get(self):
        secret_key = get_settings_variable("SECRET_KEY")
        max_age = get_settings_variable("SESSION_EXPIRES", default=1209600)
        cookie_name = get_settings_variable("SESSION_COOKIE_NAME", default="session_id")
        signer = itsdangerous.TimestampSigner(str(secret_key))

        sign = signer.sign("Anonymous:0")
        encoded = b64encode(sign)
        session = encoded.decode("utf-8")
        session_cookie = (
            f"{cookie_name}={session}; path=/;"
            f" Max-Age={max_age}; httponly; samesite=lax"
        )
        signed = {"Anonymous:0": session_cookie}
        self.request.session = json.dumps(signed)

        response = JSONResponse(self.request, {"user": self.request.session},)
        return response


class Handler500(TemplateView):
    template = "500.html"

    async def get(self):
        self.status_code = 500


class Handler404:
    def __init__(self, request):
        self.request = request

    async def __call__(self, scope, receive, send):
        response = TextResponse(self.request, "Testing Not Found")
        response.status_code = 404
        await response(scope, receive, send)


class Handler403:
    def __init__(self, request):
        self.request = request

    async def __call__(self, scope, receive, send):
        response = JSONResponse(self.request, {"Error": "Testing Access Denied"})
        response.status_code = 403
        await response(scope, receive, send)
