from crax.urls import Route, Url, include

from .routers import (
    Home,
    GuestView,
    PostView,
    PostViewTemplateRender,
    guest_view_coroutine,
    PostViewTemplateView,
    guest_coroutine_view,
)

url_list = [
    Route(Url("/"), Home),
    Route(Url("guest_view"), GuestView),
    Route(Url("guest_coroutine_view"), guest_coroutine_view),
    Route(Url("guest_view_coroutine"), guest_view_coroutine),
    Route(Url("post_view"), PostView),
    Route(Url("post_view_render"), PostViewTemplateView),
    Route(Url("post_view_render_custom"), PostViewTemplateRender),
    include("tests.test_app_nested.urls"),
    include("tests.test_app_nested.leagueA.urls"),
    include("tests.test_app_nested.leagueA.teams.urls"),
    include("tests.test_app_nested.leagueA.teams.players.urls"),
    include("tests.test_app_nested.leagueA.teams.coaches.urls"),
]
