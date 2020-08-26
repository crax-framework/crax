import asyncio
from crax import Crax
from uvicorn import Server, Config as UvConfig

from contextlib import asynccontextmanager


class SimpleResponseTest:
    def __init__(self, test_func, *args, settings=None, debug=False, on_startup=None):
        self.func = test_func
        self.on_startup = on_startup
        if settings is None:
            self.app = Crax()
        else:
            self.app = Crax(settings=settings, debug=debug, on_startup=on_startup)
        self.args = args

    @staticmethod
    @asynccontextmanager
    async def create_server(config):
        server = Server(config)
        task = asyncio.ensure_future(server.serve())
        try:
            yield task
        finally:
            await server.shutdown()
            task.cancel()

    async def _run(self):
        config = UvConfig(self.app)
        async with self.create_server(config):
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.func, *self.args)
            return result

    def __await__(self):
        return self._run().__await__()
