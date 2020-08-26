from crax.urls import Route, Url

from .routers import (
    Home,
    GuestView,
    EmptyView,
    BytesView,
    PostView,
    PostViewTemplateRender,
    guest_view_coroutine,
    PostViewTemplateView,
    guest_coroutine_view,
    ZeroDivision,
    WsEcho,
)

url_list = [
    Route(Url("/", name="home"), Home),
    Route(Url("guest_view"), GuestView),
    Route(Url("no_body"), EmptyView),
    Route(Url("bytes_body"), BytesView),
    Route(Url("guest_coroutine_view"), guest_coroutine_view),
    Route(Url("guest_view_coroutine"), guest_view_coroutine),
    Route(Url("post_view"), PostView),
    Route(Url("post_view_render"), PostViewTemplateView),
    Route(Url("post_view_render_custom"), PostViewTemplateRender),
    Route(Url("zero_division"), ZeroDivision),
    Route(Url("/", scheme="websocket"), WsEcho),
]
