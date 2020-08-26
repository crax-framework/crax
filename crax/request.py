"""
Crax Request. Sure, i've read about standard lib SimpleCookie problem
and I hope it will be fixed soon. So I do not like to replace stdlib
code with my own.
"""
from http.cookies import SimpleCookie
from urllib import parse
import typing


class Request:
    def __init__(self, scope: typing.MutableMapping[str, typing.Any]) -> None:
        self.scope = scope
        self.params = {}
        self.query = {}
        self.data = None
        self.headers = None
        self.server = None
        self.client = None
        self.cookies = {}
        self.session = {}
        self.user = None
        self.ws_secret = None
        self.scheme = scope.get("type", "http")
        self.method = scope.get("method", None)
        self.path = scope.get("path", None)
        self.content_type = None
        self.prepare_request()
        self.post = {}
        self.files = {}
        self.messages = []
        self.response_headers = {}

    @property
    def session(self) -> dict:
        return self._session

    @session.setter
    def session(self, val) -> None:
        self._session = val

    def prepare_request(self) -> None:
        self.headers = dict(
            [
                (x[0].decode("utf-8"), x[1].decode("utf-8"))
                for x in self.scope["headers"]
            ]
        )
        self.server = ":".join([str(x) for x in self.scope["server"]])
        self.client = ":".join([str(x) for x in self.scope["client"]])
        self.content_type = self.headers.get("content-type", None)
        if "cookie" in self.headers:
            cookie = SimpleCookie()
            cookie.load(self.headers["cookie"])
            for key, morsel in cookie.items():
                self.cookies[key] = morsel.value

        if "query_string" in self.scope and self.scope["query_string"]:
            self.query = parse.parse_qs(self.scope["query_string"].decode("utf-8"))

        if self.scheme == "websocket":
            if "sec-websocket-key" in self.headers:
                self.cookies.update({"ws_secret": self.headers["sec-websocket-key"]})
