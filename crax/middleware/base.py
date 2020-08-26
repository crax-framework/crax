"""
Base classes to write middleware. All middleware should inherit from this
classes. To modify Request should be used RequestMiddleware. To modify
Response should be used ResponseMiddleware. The difference is that the
first ones will be processed BEFORE application will launched. If any
errors will raised during middleware processing application process
will not be continued. ResponseMiddleware modifies headers and body
AFTER request processed.
"""
import asyncio
from abc import ABC, abstractmethod

import typing
from crax.request import Request
from crax.response_types import StreamingResponse


class ResponseMiddleware(ABC):
    # Thanks to Starlette for the idea of ​​implementing the Response Middleware call stack.

    def __init__(self, app) -> None:
        self.app = app
        self.request = app.request
        self.headers = []

    async def __call__(self, scope, receive, send) -> None:
        self.receive = receive
        response = await self.process_headers()
        await response(scope, receive, send)

    async def call_next(self, request: Request):
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()
        scope = request.scope
        receive = self.receive
        send = queue.put

        async def task() -> None:
            try:
                await self.app(scope, receive, send)
            finally:
                await queue.put(None)

        _task = loop.create_task(task())
        message = await queue.get()
        if message is None:
            _task.result()
            raise RuntimeError("No response returned.")

        async def body_stream() -> typing.AsyncGenerator[bytes, None]:
            while True:
                m = await queue.get()
                if m is None:
                    break
                yield m["body"]
            _task.result()

        response = StreamingResponse(
            self.request, status_code=message["status"], content=body_stream()
        )
        response.headers = message["headers"]
        return response

    @abstractmethod
    async def process_headers(self):
        response = await self.call_next(self.request)
        return response


class RequestMiddleware(ABC):
    def __init__(self, request: Request) -> None:
        self.request = request
        self.headers = self.request.response_headers

    @abstractmethod
    async def process_headers(self) -> typing.Any:  # pragma: no cover
        pass
