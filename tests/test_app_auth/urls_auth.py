from crax.urls import Route, Url

from .routers import (
    Home,
    ProtectedView,
    StaffRequired,
    SuperuserRequired,
    AuthView,
    LogoutView,
    WrongSessionView,
    AnonymousSessionView,
    CreateView,
    InsertView,
    WrongInsertView,
    WrongMethodInsertView,
    WrongTableMethodView,
)

url_list = [
    Route(Url("/"), Home),
    Route(Url("/protected"), ProtectedView),
    Route(Url("/staff_only"), StaffRequired),
    Route(Url("/superuser_only"), SuperuserRequired),
    Route(Url("/login"), AuthView),
    Route(Url("/logout"), LogoutView),
    Route(Url("/wrong_session"), WrongSessionView),
    Route(Url("/anonymous_session"), AnonymousSessionView),
    Route(Url("/create"), CreateView),
    Route(Url("/insert"), InsertView),
    Route(Url("/wrong_insert"), WrongInsertView),
    Route(Url("/wrong_method_insert"), WrongMethodInsertView),
    Route(Url("/wrong_table_method"), WrongTableMethodView),
]
