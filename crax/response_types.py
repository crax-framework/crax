"""
Response types. Can be used in Crax views or as part of any other ASGI
compatible view
"""
import asyncio
import hashlib
import http.cookies
import json
import os
import typing
from email.utils import formatdate, parsedate
from mimetypes import guess_type

from crax.data_types import Request, Scope, Receive, Send

import aiofiles
from aiofiles.os import stat as aio_stat


def set_headers(request, body, content_type):
    if hasattr(request, "response_headers") and request.response_headers:
        response_headers = request.response_headers
    else:
        response_headers = None
    if response_headers is None:
        headers = []
        content_length = True
    else:
        headers = [
            (k.lower().encode("latin-1"), v.encode("latin-1"))
            for k, v in response_headers.items()
        ]
        keys = [x[0] for x in headers]
        content_length = b"content-length" not in keys

    if body and content_length:
        content_length = str(len(body))
        headers.append((b"content-length", content_length.encode("latin-1")))
        if content_type:
            headers.append(
                (b"content-type", f"{content_type}; charset=utf-8".encode("latin-1"),)
            )
    return headers


async def run_until_first_complete(*args: typing.Tuple[typing.Callable, dict]) -> None:
    tasks = [handler(**kwargs) for handler, kwargs in args]
    (done, pending) = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    [task.cancel() for task in pending]
    [task.result() for task in done]


class BaseResponse:
    content_type = "text/plain"

    def __init__(
        self,
        request: Request = None,
        content: typing.Any = None,
        status_code: int = 200,
        stat_result: os.stat_result = None,
    ) -> None:
        self.request = request
        self.content = content

        if hasattr(self.request, "status_code") and self.request.status_code in [
            x for x in range(200, 227)
        ]:
            self.status_code = self.request.status_code
        else:
            self.status_code = status_code
        self.stat_result = stat_result
        body = self.render(self.content)
        if body:
            self.body = body
        else:
            self.body = b""
        self.headers = set_headers(self.request, body, self.content_type)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.headers,
            }
        )
        await send({"type": "http.response.body", "body": self.body})

    @staticmethod
    def render(content: typing.Union[str, bytes]) -> bytes:
        if content is None:
            return b""
        if isinstance(content, bytes):
            return content
        return content.encode("utf-8")

    def set_cookies(self, key: str, val: str = "", rest: dict = None) -> None:
        cookie = http.cookies.SimpleCookie()
        cookie[key] = val
        if rest:
            for k, v in rest.items():
                try:
                    cookie[key][k] = v
                except http.cookies.CookieError:  # pragma: no cover
                    pass

        cookie_val = cookie.output(header="").strip()
        self.headers.append((b"set-cookie", cookie_val.encode("latin-1")))


class TextResponse(BaseResponse):
    content_type = "text/html"


class JSONResponse(BaseResponse):
    content_type = "application/json"

    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


class FileResponse(BaseResponse):
    chunk_size = 4096

    def __init__(
        self, path: str, status_code: int = 200, static_res: os.stat_result = None,
    ) -> None:
        super(FileResponse, self).__init__()
        self.path = path
        self.status_code = status_code
        self.headers = []
        self.static_res = static_res
        if static_res:
            self.static_headers(static_res)

    def static_headers(self, stat_result: os.stat_result) -> None:
        content_length = str(stat_result.st_size)
        last_modified = formatdate(stat_result.st_mtime, usegmt=True)
        etag_base = str(stat_result.st_mtime) + "-" + str(stat_result.st_size)
        etag = hashlib.md5(etag_base.encode()).hexdigest()
        self.content_type = guess_type(self.path)[0] or "text/plain"
        self.headers.append((b"content-type", self.content_type.encode("latin-1")))
        self.headers.append((b"content-length", content_length.encode("latin-1")))
        self.headers.append((b"last-modified", last_modified.encode("latin-1")))
        self.headers.append((b"etag", etag.encode("latin-1")))

    @staticmethod
    def check_modified(request_headers: dict, response_headers: dict) -> bool:
        if b"if-modified-since" in request_headers:
            if_modified_since = parsedate(
                request_headers[b"if-modified-since"].decode("utf-8")
            )
            last_modified = parsedate(
                response_headers[b"last-modified"].decode("utf-8")
            )
            if if_modified_since >= last_modified:
                return True
        return False

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self.static_res:
            static_res = await aio_stat(self.path)
            self.static_headers(static_res)
            if self.check_modified(dict(scope["headers"]), dict(self.headers)):
                available_keys = [
                    "cache-control",
                    "content-location",
                    "date",
                    "etag",
                    "expires",
                    "vary",
                ]
                headers = [x for x in self.headers if x[0].decode() in available_keys]
                await send(
                    {"type": "http.response.start", "status": 304, "headers": headers}
                )
                await send({"type": "http.response.body", "body": b""})
            else:
                await send(
                    {
                        "type": "http.response.start",
                        "status": self.status_code,
                        "headers": self.headers,
                    }
                )
                async with aiofiles.open(self.path, mode="rb") as file:
                    _continue = True
                    while _continue:
                        chunk = await file.read(self.chunk_size)
                        if len(chunk) != self.chunk_size:
                            _continue = False
                        await send(
                            {
                                "type": "http.response.body",
                                "body": chunk,
                                "more_body": _continue,
                            }
                        )


class StreamingResponse:
    # Thanks again to Tom Christie;)
    # Streaming Response and Response middleware stolen from Starlette.
    def __init__(
        self,
        request,
        content: typing.Any,
        status_code: int = 200,
        media_type: str = None,
    ) -> None:
        self.body_iterator = content
        self.status_code = status_code
        self.media_type = media_type
        self.request = request
        body = getattr(self, "body", b"")
        self.headers = set_headers(self.request, body, None)

    @staticmethod
    async def listen_for_disconnect(receive: Receive) -> None:
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                break

    async def stream_response(self, send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.headers,
            }
        )
        async for chunk in self.body_iterator:
            if not isinstance(chunk, bytes):
                chunk = chunk.encode("latin-1")
            await send({"type": "http.response.body", "body": chunk, "more_body": True})

        await send({"type": "http.response.body", "body": b"", "more_body": False})

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await run_until_first_complete(
            (self.stream_response, {"send": send}),
            (self.listen_for_disconnect, {"receive": receive}),
        )
