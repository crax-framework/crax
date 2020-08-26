from crax.middleware.base import ResponseMiddleware


class ReplaceMiddleware(ResponseMiddleware):
    async def process_headers(self):
        pass
