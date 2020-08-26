from crax.urls import Route, Url

from .routers import Home, StreamView, CoverageView, WsHome

url_list = [
    Route(urls=(Url(r"/")), handler=Home),
    Route(urls=(Url(r"/coverage/", masquerade=True)), handler=CoverageView),
    Route(urls=(Url(r"/", scheme="websocket")), handler=WsHome),
    Route(urls=(Url(r"/get_stream")), handler=StreamView),
]
