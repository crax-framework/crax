import asyncio
import json
import os
import re
import shutil
from pathlib import Path

import aio_pika
import in_place
from crax.response_types import StreamingResponse, JSONResponse
from crax.utils import get_settings_variable
from crax.views import TemplateView, WsView

from websockets.exceptions import ConnectionClosedOK


CLIENTS = {}
STARTED = False

REPLACEMENTS = [
    ('href="style.css"', 'href="/static/style.css"'),
    ('src="jquery.min.js"', 'src="/static/jquery.min.js"'),
    ('src="jquery.hotkeys.js"', 'src="/static/jquery.hotkeys.js"'),
    ('src="jquery.isonscreen.js"', 'src="/static/jquery.isonscreen.js"'),
    ('src="coverage_html.js"', 'src="/static/coverage_html.js"'),
    (
        'src="jquery.ba-throttle-debounce.min.js"',
        'src="/static/jquery.ba-throttle-debounce.min.js"',
    ),
    ('src="jquery.tablesorter.min.js"', 'src="/static/jquery.tablesorter.min.js"'),
    ('src="keybd_closed.png"', 'src="/static/keybd_closed.png"'),
    ('src="keybd_open.png"', 'src="/static/keybd_open.png"'),
]


def replacement(target_file, old, new):
    with in_place.InPlace(target_file) as fil:
        for line in fil:
            if old in line:
                new_line = line.replace(old, new)
            else:
                new_line = line
            fil.write(new_line)


class Home(TemplateView):
    template = "get_stream.html"

    async def render_response(self):
        response = await super(Home, self).render_response()
        return response


class WsHome(WsView):
    async def on_connect(self, scope, receive, send):
        await super(WsHome, self).on_connect(scope, receive, send)
        ws_key = self.request.cookies.get("ws_secret")
        session_key = self.request.cookies.get("session_id")
        if ws_key and session_key:
            if f"{ws_key}:{session_key}" not in CLIENTS:
                CLIENTS.update({f"{ws_key}:{session_key}": receive.__self__})

    async def on_disconnect(self, scope, receive, send):
        ws_key = self.request.cookies.get("ws_secret")
        session_key = self.request.cookies.get("session_id")
        if ws_key and session_key and f"{ws_key}:{session_key}" in CLIENTS:
            del CLIENTS[f"{ws_key}:{session_key}"]

    async def dispatch(self, scope, receive, send):
        await super(WsHome, self).dispatch(scope, receive, send)
        connection = await aio_pika.connect_robust(
            "amqp://guest:guest@rabbitmq-container/"
        )
        async with connection:
            queue_name = "stream_messages"
            channel = await connection.channel()
            queue = await channel.declare_queue(queue_name)
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        message = json.loads(message.body.decode(encoding="utf-8"))
                        for client in CLIENTS.values():
                            try:
                                await client.send(message["body"])
                            except (
                                ConnectionClosedOK,
                                asyncio.streams.IncompleteReadError,
                            ):
                                await client.close()


async def pub(queue):
    base_url = get_settings_variable("BASE_URL")
    file_ = open(f"{base_url}/test.log", "r")
    while True:
        where = file_.tell()
        line = file_.readline()
        if not line:
            await asyncio.sleep(0.1)
            file_.seek(where)
        else:
            await queue.put(line)


async def sub(queue):
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq-container/")
    channel = await connection.channel()
    while True:
        line = await queue.get()
        queue.task_done()
        if line:
            message = {"body": line}
            await channel.default_exchange.publish(
                aio_pika.Message(body=bytes(json.dumps(message), encoding="utf-8")),
                routing_key="stream_messages",
            )

        if "ALL TESTS DONE" in line:
            loop = asyncio.get_running_loop()
            pub_id = os.environ.get("CRAX_PUB_TEST_CORO")
            sub_id = os.environ.get("CRAX_SUB_TEST_CORO")
            run_id = os.environ.get("CRAX_RUN_TEST_CORO")
            tasks = [
                x
                for x in asyncio.Task.all_tasks(loop=loop)
                if id(x) in [int(pub_id), int(sub_id), int(run_id)]
            ]
            [x.cancel() for x in tasks]


async def run_pub_sub():
    queue = asyncio.Queue()
    pub_ = asyncio.create_task(pub(queue))
    sub_ = asyncio.create_task(sub(queue))
    os.environ["CRAX_PUB_TEST_CORO"] = str(id(pub_))
    os.environ["CRAX_SUB_TEST_CORO"] = str(id(sub_))
    await pub_
    await queue.join()


async def send_file():
    base_url = get_settings_variable("BASE_URL")
    file_ = f"{base_url}/test.log"
    if os.path.isfile(file_):
        with open(file_, "r") as f:
            z = f.readlines()
            for i in z:
                yield i
    else:
        yield ""


class CoverageView(TemplateView):
    temp_dir = (
        f"{str(Path(os.path.abspath(__file__)).parents[2])}/docker/streams/templates"
    )
    scope = [page for page in os.listdir(temp_dir)]

    async def render_response(self):
        response = await super(CoverageView, self).render_response()
        return response


class StreamView:
    methods = ["GET", "POST"]

    def __init__(self, request):
        self.request = request

    async def __call__(self, scope, receive, send):
        base_url = get_settings_variable("BASE_URL")
        if self.request.method == "POST":
            test_dir = f"{os.path.dirname(os.path.dirname(base_url))}/tests"
            command_ = f"cd .. && {test_dir}/venv/bin/python3 -m coverage html"
            os.system(command_)
            cove_dir = f"{test_dir}/htmlcov"
            docker_dir = f"{test_dir}/docker"
            static_dir = f"{docker_dir}/static"
            if not os.path.exists(static_dir):
                os.mkdir(static_dir)
            template_dir = f"{docker_dir}/streams/templates"
            if os.path.exists(cove_dir):
                for file_ in os.listdir(cove_dir):
                    if file_.endswith(".html"):
                        shutil.copyfile(
                            f"{cove_dir}/{file_}", f"{template_dir}/{file_}"
                        )
                        for match in REPLACEMENTS:
                            replacement(f"{template_dir}/{file_}", match[0], match[1])
                    elif re.match(r".*\.js|.*css|.*\.png", file_):
                        shutil.copyfile(f"{cove_dir}/{file_}", f"{static_dir}/{file_}")
                response = JSONResponse(self.request, {"success": "Coverage created"})
            else:
                response = JSONResponse(
                    self.request, {"error": "Failed to create coverage report"}
                )
            await response(scope, receive, send)
        else:
            response = StreamingResponse(self.request, send_file())
            await response(scope, receive, send)
            started = os.environ.get("CRAX_TEST_SESSION_STARTED")
            if started is None:
                file_path = f"{base_url}/test.log"
                if os.path.isfile(file_path):
                    run_ = asyncio.create_task(run_pub_sub())
                    os.environ["CRAX_RUN_TEST_CORO"] = str(id(run_))
                    os.environ["CRAX_TEST_SESSION_STARTED"] = "Started"
