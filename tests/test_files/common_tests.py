import asyncio
import os
import random
import re
import sys
import time

from lxml import html
import pytest
import requests
from crax import get_settings
from crax.utils import get_settings_variable
from .utils import SimpleResponseTest
import websockets
from crax import Crax
from uvicorn import Server, Config


def test_auth_models_no_alchemy():
    try:
        from crax.auth.models import User

        User()
    except Exception as e:
        assert "SQLAlchemy should be installed to use Crax Auth Models" in str(e)


@pytest.mark.asyncio
async def test_first_launch_root():
    def root_no_settings(host):
        time.sleep(1)
        x = requests.get(host)
        return x.status_code, x.content

    res_root = await SimpleResponseTest(root_no_settings, "http://127.0.0.1:8000")

    assert res_root[0] == 200
    assert "WELCOME TO CRAX" in res_root[1].decode("utf-8")


@pytest.mark.asyncio
async def test_first_launch_any():
    def any_no_settings(host):
        time.sleep(1)
        x = requests.get(host)
        return x.status_code, x.content

    res_any = await SimpleResponseTest(
        any_no_settings, "http://127.0.0.1:8000/any_path/"
    )
    assert res_any[0] == 200
    assert "WELCOME TO CRAX" in res_any[1].decode("utf-8")


@pytest.mark.asyncio
async def test_app_missed_conf_debug_false():
    missed = "tests.config_files.conf_missed"

    def missed_settings_debug_false_no_handler(host):
        time.sleep(1)
        x = requests.get(host)
        return x.status_code, x.content

    res_any = await SimpleResponseTest(
        missed_settings_debug_false_no_handler,
        "http://127.0.0.1:8000/",
        settings=missed,
    )
    assert b'Internal Server Error' == res_any[1]
    assert res_any[0] == 500


@pytest.mark.asyncio
async def test_first_app_wrong_settings():
    settings = "tests.config_files.conf_minimal"

    def any_no_settings():
        time.sleep(1)
        try:
            get_settings("tests.config_files.conf_")
        except ModuleNotFoundError as e:
            return str(e)

    res = await SimpleResponseTest(any_no_settings, settings=settings, debug=True,)
    assert "No module named 'tests.config_files.conf_'" == res


@pytest.mark.asyncio
async def test_app_missed_conf_debug_true():
    missed = "tests.config_files.conf_missed"

    def missed_settings_debug_true(host):
        time.sleep(1)
        x = requests.get(host)
        return x.status_code, x.content

    res_any = await SimpleResponseTest(
        missed_settings_debug_true,
        "http://127.0.0.1:8000/",
        settings=missed,
        debug=True,
    )
    assert "CRAX 500 ERROR" in res_any[1].decode("utf-8")
    assert "ModuleNotFoundError" in res_any[1].decode("utf-8")
    assert res_any[0] == 500


@pytest.mark.asyncio
async def test_first_app():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)

        assert resp.status_code == 200
        assert "Testing index page" in resp.content.decode("utf-8")

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/",
        settings="tests.config_files.conf_minimal",
    )


@pytest.mark.asyncio
async def test_first_app_no_body():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 200
        assert not resp.content

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/no_body",
        settings="tests.config_files.conf_minimal",
    )


@pytest.mark.asyncio
async def test_first_app_bytes_body():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 200
        assert "Testing bytes" in resp.content.decode("utf-8")

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/bytes_body",
        settings="tests.config_files.conf_minimal",
    )


@pytest.mark.asyncio
async def test_first_app_on_startup_coroutine(capsys):
    async def on_start():
        await asyncio.sleep(0.1)
        sys.stdout.write("Testing coroutine start up\n")

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 200
        captured = capsys.readouterr()
        assert "Testing index page" in resp.content.decode("utf-8")
        return captured.out.split("\n")

    on_start_res = await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/",
        settings="tests.config_files.conf_minimal",
        on_startup=on_start,
    )

    assert "Testing coroutine start up" in on_start_res


@pytest.mark.asyncio
async def test_first_app_on_startup_function(capsys):
    def on_start():
        sys.stdout.write("Testing coroutine start up\n")

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 200
        captured = capsys.readouterr()
        assert "Testing index page" in resp.content.decode("utf-8")
        return captured.out.split("\n")

    on_start_res = await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/",
        settings="tests.config_files.conf_minimal",
        on_startup=on_start,
    )

    assert "Testing coroutine start up" in on_start_res


@pytest.mark.asyncio
async def test_first_app_x_frame():
    settings = "tests.config_files.conf_minimal_middleware_no_auth"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        __import__(settings)
        spl_settings = settings.split(".")
        app_settings = __import__(settings, fromlist=spl_settings)
        assert app_settings.X_FRAME_OPTIONS == resp.headers["x-frame-options"]
        assert resp.status_code == 200
        assert "Testing index page" in resp.content.decode("utf-8")

    await SimpleResponseTest(
        any_no_settings, "http://127.0.0.1:8000/", settings=settings
    )


@pytest.mark.asyncio
async def test_first_app_405_debug_true():
    settings = "tests.config_files.conf_minimal_middleware_no_auth"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.post(host, data={"data": "test_data"})
        assert resp.status_code == 405
        assert "CRAX 405 ERROR" in resp.content.decode("utf-8")

    await SimpleResponseTest(
        any_no_settings, "http://127.0.0.1:8000/", settings=settings, debug=True
    )


@pytest.mark.asyncio
async def test_first_app_405_debug_false_no_handler():
    settings = "tests.config_files.conf_minimal_middleware_no_auth"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.post(host, data={"data": "test_data"})
        assert resp.status_code == 500
        assert b'Internal Server Error' == resp.content

    await SimpleResponseTest(
        any_no_settings, "http://127.0.0.1:8000/", settings=settings
    )


@pytest.mark.asyncio
async def test_first_app_405_debug_false_handler():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.post(host, data={"data": "test_data"})
        body = resp.json()
        assert body["Error"] == "Testing Method Not Allowed"
        assert resp.status_code == 405

    await SimpleResponseTest(
        any_no_settings, "http://127.0.0.1:8000/", settings=settings
    )


@pytest.mark.asyncio
async def test_first_app_404_debug_false_handler():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.content.decode("utf-8") == "Testing Not Found"
        assert resp.status_code == 404

    await SimpleResponseTest(
        any_no_settings, "http://127.0.0.1:8000/missed/", settings=settings
    )


@pytest.mark.asyncio
async def test_app_missed_conf_debug_false_handler_500():
    missed = "tests.config_files.conf_handler_500"

    def missed_settings_debug_true(host):
        time.sleep(1)
        x = requests.get(host)
        assert "<h1>Test custom 500 handler</h1>" in x.content.decode("utf-8")
        assert x.status_code == 500

    await SimpleResponseTest(
        missed_settings_debug_true,
        "http://127.0.0.1:8000/zero_division/",
        settings=missed,
    )


@pytest.mark.asyncio
async def test_app_missed_conf_debug_wrong_file_inclusion():
    missed = "tests.config_files.conf_wrong_url_inclusion"

    def missed_settings_debug_true(host):
        time.sleep(1)
        x = requests.get(host)
        assert "<h2>ModuleNotFoundError</h2>" in x.content.decode("utf-8")
        assert x.status_code == 500

    await SimpleResponseTest(
        missed_settings_debug_true,
        "http://127.0.0.1:8000/",
        settings=missed,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_url_wrong_type():
    settings = "tests.config_files.conf_url_wrong_type"

    def any_no_settings(host):
        time.sleep(1)
        try:
            requests.get(host)
        except Exception as e:
            assert 'should be instance of "Url"' in str(e)

    await SimpleResponseTest(
        any_no_settings, "http://127.0.0.1:8000/", settings=settings
    )


@pytest.mark.asyncio
async def test_first_app_auth_no_alchemy():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 500
        assert (
            '<h2 class="crax_mark">SQLAlchemy should be '
            "installed to use Crax Auth Models</h2>" in resp.content.decode("utf-8")
        )

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/",
        settings="tests.config_files.conf_auth",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_custom_class_view():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.content.decode("utf-8") == "Testing Custom View"
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings, "http://127.0.0.1:8000/guest_view/", settings=settings
    )


@pytest.mark.asyncio
async def test_first_app_custom_coroutine_view():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert "Testing index page" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/guest_view_coroutine/",
        settings=settings,
    )


@pytest.mark.asyncio
async def test_first_app_post_view():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        test_data = "Test data"
        resp = requests.post(host, data={"data": test_data})
        body = resp.json()
        assert body["data"] == test_data
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_post_view_render():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        test_data = "Test data"
        resp = requests.post(host, data={"data": test_data})
        assert test_data in resp.content.decode("utf-8")
        assert resp.status_code == 201

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view_render/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_post_view_render_custom():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        test_data = "Test data"
        resp = requests.post(host, data={"data": test_data})
        assert test_data in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view_render_custom/",
        settings=settings,
    )


@pytest.mark.asyncio
async def test_first_app_get_file_404():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 404

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/some_path/static/bootstrap.css",
        settings=settings,
    )


@pytest.mark.asyncio
async def test_first_app_get_file_200():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/test_app_common/static/bootstrap.css",
        settings=settings,
    )


@pytest.mark.asyncio
async def test_first_app_get_file_304_not_modified():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        headers = {
            "Accept": "text/css,*/*;q=0.1",
            "If-Modified-Since": "Fri, 10 Jul 2122 12:05:43 GMT",
            "If-None-Match": "bd0529deb11c0691f359f941aee82408",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
        }
        resp = requests.get(host, headers=headers)
        assert resp.status_code == 304

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/test_app_common/static/bootstrap.css",
        settings=settings,
    )


@pytest.mark.asyncio
async def test_first_app_get_file_200_modified():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        headers = {
            "Accept": "text/css,*/*;q=0.1",
            "If-Modified-Since": "Fri, 10 Jul 2012 12:05:43 GMT",
            "If-None-Match": "bd0529deb11c0691f359f941aee82408",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
        }
        resp = requests.get(host, headers=headers)
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/test_app_common/static/bootstrap.css",
        settings=settings,
    )


@pytest.mark.asyncio
async def test_first_app_max_body_error():
    settings = "tests.config_files.conf_max_body_error"

    def any_no_settings(host):
        time.sleep(1)
        _settings = get_settings()
        assert _settings.__name__ == settings
        resp = requests.post(host, data={"data": "Test body error"})
        assert "CRAX 400 ERROR" in resp.content.decode("utf-8")
        assert resp.status_code == 400

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view_render/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_post_multipart():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        test_data = "Test data"
        files = {
            "test_file": (
                "python_logo.png",
                open("test_files/media_files/python_logo.png", "rb"),
            ),
            "action": (None, "store"),
            "path": (None, "."),
        }
        resp = requests.post(host, files=files, data={"data": test_data})
        assert test_data in resp.content.decode("utf-8")
        assert "test_file" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view_render_custom/",
        settings=settings,
    )


@pytest.mark.asyncio
async def test_first_app_post_text_plain():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        test_data = {"data": "Test data"}
        resp = requests.post(host, json=test_data)
        assert test_data["data"] in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view_render_custom/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_test_params():
    settings = "tests.config_files.conf_minimal_two_apps"
    value_1 = "value_1"
    value_2 = "value_2"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert f"param_1 = {value_1}" in resp.content.decode(
            "utf-8"
        ) and f"param_2 = {value_2}" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        f"http://127.0.0.1:8000/tests/test_app_nested/test_param/{value_1}/{value_2}/",
        settings=settings,
    )


@pytest.mark.asyncio
async def test_first_app_test_query():
    settings = "tests.config_files.conf_minimal_two_apps"
    value_1 = "value_1"
    value_2 = "value_2"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert f"param_1 = {value_1}" in resp.content.decode(
            "utf-8"
        ) and f"param_2 = {value_2}" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        f"http://127.0.0.1:8000/tests/test_app_nested/"
        f"test_param/?param_1={value_1}&param_2={value_2}",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_test_jinja_ex():
    settings = "tests.config_files.conf_minimal_two_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert " <h2>CraxNoTemplateGiven</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 500

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/test_missed_template/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_test_template_ex():
    settings = "tests.config_files.conf_minimal_two_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert "<h2>CraxNoTemplateGiven</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 500

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/test_missed_template/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_test_not_found_template():
    settings = "tests.config_files.conf_minimal_two_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert "<h2>TemplateNotFound</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 404

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/test_not_found_template/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_test_inner_template_ex():
    settings = "tests.config_files.conf_minimal_two_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert "<h2>TemplateNotFound</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 404

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/inner_template_ex/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_test_json_view():
    settings = "tests.config_files.conf_minimal_two_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.json()["data"] == "Test_data"
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/test_json_view/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_send_cookies_back():
    settings = "tests.config_files.conf_minimal_two_apps"

    def any_no_settings(host):
        time.sleep(1)
        cookies = [("test_cookie", "Test cookie value")]
        resp = requests.get(host, cookies=dict(cookies))
        body = resp.json()
        assert body["data"] == "=".join(cookies[0])
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/test_send_cookies_back/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_set_cookies():
    settings = "tests.config_files.conf_minimal_two_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert (
            resp.headers["set-cookie"]
            == "test_cookie=test_cookie_value; HttpOnly; Path=/"
        )
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/test_set_cookies/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_test_params_regex():
    settings = "tests.config_files.conf_minimal_two_apps"
    value_1 = "value_1"
    value_2 = "value_2"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert f"param_1 = {value_1}" in resp.content.decode(
            "utf-8"
        ) and f"param_2 = {value_2}" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        f"http://127.0.0.1:8000/tests/test_app_nested/test_param_regex/{value_1}/{value_2}/",
        settings=settings,
    )


@pytest.mark.asyncio
async def test_first_app_test_empty_method():
    settings = "tests.config_files.conf_minimal_two_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert "<h2>CraxEmptyMethods</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 500

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/test_empty_method/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_masquerade_200():
    settings = "tests.config_files.conf_minimal_two_apps"
    scope = ["masquerade_1.html", "masquerade_2.html", "masquerade_3.html"]
    url = random.choice(scope)

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert "<h1>Test Masquerade</h1>" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        f"http://127.0.0.1:8000/tests/test_app_nested/test_masquerade/{url}",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_masquerade_404():
    settings = "tests.config_files.conf_minimal_two_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert "<h2>CraxPathNotFound</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 404

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/test_masquerade/masquerade_5.html",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_masquerade_no_scope():
    settings = "tests.config_files.conf_minimal_two_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert "<h2>CraxPathNotFound</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 404

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/masquerade_no_scope/masquerade_2.html",
        settings=settings,
        debug=True,
    )


def logger_settings(
    host, log_file, logger_name, log_level, capsys, method, console=False
):
    time.sleep(1)
    resp = getattr(requests, method)(host)
    assert resp.status_code == 200
    log_path = f"./{log_file}"
    assert "Testing index page" in resp.content.decode("utf-8")
    assert os.path.isfile(log_path)
    with open(log_path, "r") as log:
        log_line = log.readlines()[0]
        info_message = (
            f" {logger_name} — {log_level} — http GET "
            f'{re.split(r"http://", host)[1].replace("/", "")}'
        )
        assert info_message in log_line
    if os.path.isfile(log_path):
        os.remove(log_path)
    assert os.path.isfile(log_path) is False
    if console is True:
        captured = capsys.readouterr()
        assert any(info_message in x for x in captured.err.split("\n"))


@pytest.mark.asyncio
async def test_first_app_logger_default(capsys):

    await SimpleResponseTest(
        logger_settings,
        "http://127.0.0.1:8000/",
        "crax.log",
        "crax",
        "INFO",
        capsys,
        "get",
        settings="tests.config_files.conf_logging",
    )


@pytest.mark.asyncio
async def test_first_app_logger_custom(capsys):
    await SimpleResponseTest(
        logger_settings,
        "http://127.0.0.1:8000/",
        "app.log",
        "test_logger",
        "INFO",
        capsys,
        "get",
        True,
        settings="tests.config_files.conf_logging_custom",
    )


@pytest.mark.asyncio
async def test_first_app_logger_custom_error():
    def logger_error(host, log_file, logger_name, log_level):
        time.sleep(1)
        resp = requests.post(host)
        log_path = f"./{log_file}"
        assert resp.status_code == 405
        assert os.path.isfile(log_path)
        with open(log_path, "r") as log:
            log_line = log.readlines()[1]
            info_message = (
                f" {logger_name} — {log_level} — Method not allowed for this view"
            )
            assert info_message in log_line
        if os.path.isfile(log_path):
            os.remove(log_path)
        assert os.path.isfile(log_path) is False

    await SimpleResponseTest(
        logger_error,
        "http://127.0.0.1:8000/",
        "app.log",
        "test_logger",
        "CRITICAL",
        settings="tests.config_files.conf_logging_custom",
    )


@pytest.mark.asyncio
async def test_first_app_middleware_error():
    def middleware_error(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 500
        assert "<h2>AttributeError</h2>" in resp.content.decode("utf-8")

    await SimpleResponseTest(
        middleware_error,
        "http://127.0.0.1:8000/",
        settings="tests.config_files.conf_middleware_error",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_middleware_no_response():
    settings = "tests.config_files.conf_minimal_middleware_no_auth_handlers"

    def any_no_settings(host):
        time.sleep(1)
        headers = {
            "origin": "127.0.0.1:3000",
            "access-control-request-method": "POST",
            "access-control-request-headers": "content_type",
        }
        resp = requests.options(host, headers=headers)

        assert resp.content == b""

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view_render/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_url_creation():
    settings = "tests.config_files.conf_minimal_two_apps"

    def create_url(host):
        time.sleep(1)
        resp = requests.get(host)
        tree = html.fromstring(resp.content)
        param_path = tree.xpath('//*[@id="namespaced_url"]/@href')
        param_path_regex = tree.xpath('//*[@id="namespaced_url_regex"]/@href')
        resp_param = requests.get(f"http://127.0.0.1:8000{param_path[0]}")
        resp_param_regex = requests.get(f"http://127.0.0.1:8000{param_path_regex[0]}")
        assert "param_1 = value_1" in resp_param.content.decode(
            "utf-8"
        ) and "param_2 = value_2" in resp_param.content.decode("utf-8")

        assert "param_1 = value_1" in resp_param.content.decode(
            "utf-8"
        ) and "param_2 = value_2" in resp_param_regex.content.decode("utf-8")
        assert resp.status_code == 200
        assert resp_param.status_code == 200
        assert resp_param_regex.status_code == 200

    await SimpleResponseTest(
        create_url,
        "http://127.0.0.1:8000/tests/test_app_nested/test_create_url/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_cors_no_dict():
    settings = "tests.config_files.conf_cors_no_dict"

    def any_no_settings(host):
        time.sleep(1)
        headers = {"origin": host, "access-control-request-method": "POST"}
        resp = requests.options(host, headers=headers)
        assert resp.status_code == 500
        assert resp.content == b"Cors options should be a dict"

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_cors_default():
    settings = "tests.config_files.conf_cors_default"

    def any_no_settings(host):
        time.sleep(1)
        headers = {"origin": host, "access-control-request-method": "POST"}
        resp = requests.options(host, headers=headers)
        preflight = {
            "access-control-allow-origin": "*",
            "access-control-allow-methods": "*",
            "access-control-allow-headers": "*",
            "access-control-max-age": "600",
        }
        assert all(
            x in resp.headers and resp.headers[x] == preflight[x] for x in preflight
        )
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_cors_custom():
    settings = "tests.config_files.conf_cors_custom"

    def any_no_settings(host):
        time.sleep(1)
        headers = {
            "origin": "http://127.0.0.1:8000",
            "access-control-request-method": "POST",
        }
        resp = requests.options(host, headers=headers)
        preflight = {
            "access-control-allow-origin": "http://127.0.0.1:8000, http://127.0.0.1:3000",
            "access-control-allow-methods": "POST, PATCH",
            "access-control-allow-headers": "content-type",
            "access-control-max-age": "600",
        }
        assert all(
            x in resp.headers and resp.headers[x] == preflight[x] for x in preflight
        )
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_cors_custom_fail_method():
    settings = "tests.config_files.conf_cors_custom"

    def any_no_settings(host):
        time.sleep(1)
        headers = {
            "origin": "http://127.0.0.1:8000",
            "access-control-request-method": "DELETE",
        }
        resp = requests.options(host, headers=headers)
        assert (
            resp.content
            == b'Cross Origin Request with method: "DELETE" not allowed on this server'
        )
        assert resp.status_code == 400

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_cors_custom_fail_origin():
    settings = "tests.config_files.conf_cors_custom"

    def any_no_settings(host):
        time.sleep(1)
        headers = {
            "origin": "http://127.0.0.1:5000",
            "access-control-request-method": "PATCH",
        }
        resp = requests.options(host, headers=headers)
        assert (
            resp.content
            == b'Cross Origin Request from: "http://127.0.0.1:5000" not allowed on this server'
        )
        assert resp.status_code == 400

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_cors_custom_fail_header():
    settings = "tests.config_files.conf_cors_custom"

    def any_no_settings(host):
        time.sleep(1)
        headers = {
            "origin": "http://127.0.0.1:8000",
            "access-control-request-method": "PATCH",
            "access-control-request-headers": "suspicious_header",
        }
        resp = requests.options(host, headers=headers)
        assert (
            resp.content
            == b'Cross Origin Request with headers: "suspicious_header" not allowed on this server'
        )
        assert resp.status_code == 400

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/post_view/",
        settings=settings,
        debug=True,
    )


def success_custom_cors(host, as_string=False):
    time.sleep(1)
    headers = {
        "origin": "http://127.0.0.1:8000",
        "access-control-request-method": "PATCH",
        "Allow-By-Cookie": "true",
    }
    cors_options = get_settings_variable("CORS_OPTIONS", default={})
    origins = cors_options["origins"]
    if isinstance(origins, list):
        origins = ", ".join(origins)
    resp = requests.options(host, headers=headers)
    if as_string is True:
        allow_headers = "*"
    else:
        allow_headers = "content-type, allow-by-cookie"
    preflight = {
        "access-control-allow-origin": origins,
        "access-control-allow-methods": "POST, PATCH",
        "access-control-allow-headers": allow_headers,
        "access-control-max-age": "600",
        "vary": "Origin",
        "access-control-expose-headers": "Exposed_One, Exposed_Two",
    }
    assert all(
        x in resp.headers and all(k in resp.headers[x] for k in preflight[x])
        for x in preflight
    )
    assert resp.status_code == 200

    headers = {"Allow-By-Cookie": "true"}
    resp = requests.post(host, headers=headers, data={"data": "Test data"})
    no_preflight = {
        "access-control-allow-origin": origins,
        "access-control-allow-methods": "POST, PATCH",
        "access-control-max-age": "600",
        "vary": "Origin",
    }
    assert all(
        x in resp.headers and resp.headers[x] == no_preflight[x] for x in no_preflight
    )
    assert resp.status_code == 200
    assert resp.json()["data"] == "Test data"


@pytest.mark.asyncio
async def test_first_app_cors_custom_success_str():
    settings = "tests.config_files.conf_cors_custom_str"

    await SimpleResponseTest(
        success_custom_cors,
        "http://127.0.0.1:8000/post_view/",
        True,
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_cors_custom_success():
    settings = "tests.config_files.conf_cors_custom_cookie"

    await SimpleResponseTest(
        success_custom_cors,
        "http://127.0.0.1:8000/post_view/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_nested_first_level_index():
    settings = "tests.config_files.conf_nested_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host,)
        assert "<h1>LeagueA Index Page</h1>" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/leagueA/first_league/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_nested_first_level_scores():
    settings = "tests.config_files.conf_nested_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host,)
        assert "<h1>LeagueA Scores Page</h1>" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/leagueA/first_league_scores/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_nested_second_level_index():
    settings = "tests.config_files.conf_nested_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host,)
        assert "<h1>LeagueA Teams Index Page</h1>" in resp.content.decode("utf-8")
        assert "<h2>Params: Oilers</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/leagueA/teams/first_league/Oilers",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_nested_second_level_scores():
    settings = "tests.config_files.conf_nested_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host,)
        assert "<h1>LeagueA Teams Scores Page</h1>" in resp.content.decode("utf-8")
        assert "<h2>Oilers</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/leagueA/teams/first_league_scores/Oilers/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_nested_second_level_index_with_query():
    settings = "tests.config_files.conf_nested_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host,)
        assert "<h1>LeagueA Teams Index Page</h1>" in resp.content.decode("utf-8")
        assert "<h2>Params: Oilers</h2>" in resp.content.decode("utf-8")
        assert "<h2>Query: Capitals</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/leagueA/teams/"
        "first_league/Oilers/?team_name=Capitals",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_nested_third_level_scores():
    settings = "tests.config_files.conf_nested_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host,)
        assert "<h1>LeagueA Players Scores Page</h1>" in resp.content.decode("utf-8")
        assert "<h2>Oilers McDavid</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/leagueA/"
        "teams/players/first_league_scores/Oilers/McDavid",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_nested_third_level_index_no_options():
    settings = "tests.config_files.conf_nested_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host,)
        assert "<h1>LeagueA Players Index Page</h1>" in resp.content.decode("utf-8")
        assert "<h2>Params: Oilers McDavid</h2>" in resp.content.decode("utf-8")
        assert "<h2>Query: Capitals</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/leagueA/teams/"
        "players/first_league/Oilers/McDavid/?team_name=Capitals",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_nested_third_level_index_missed_param():
    settings = "tests.config_files.conf_nested_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host,)
        assert resp.status_code == 404

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/leagueA/teams/players/first_league/Oilers/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_nested_third_level_index_options():
    settings = "tests.config_files.conf_nested_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host,)
        assert "<h1>LeagueA Players Index Page</h1>" in resp.content.decode("utf-8")
        assert "<h2>Params: Oilers McDavid</h2>" in resp.content.decode("utf-8")
        assert "<h3>97</h3>" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/"
        "leagueA/teams/players/first_league/Oilers/McDavid/97/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_nested_third_level_index_namespaced():
    settings = "tests.config_files.conf_nested_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host,)
        assert "<h1>LeagueA Coaches Index Page</h1>" in resp.content.decode("utf-8")
        assert "<h2>Params: Oilers Tippett</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/leagueA/coaches/first_league_coaches/Oilers/Tippett/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_nested_third_level_results_namespaced():
    settings = "tests.config_files.conf_nested_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host,)
        assert "<h1>LeagueA Coaches Results Page</h1>" in resp.content.decode("utf-8")
        assert "<h2>Oilers Tippett</h2>" in resp.content.decode("utf-8")
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/first_league_scores/leagueA/coaches/Oilers/Tippett/",
        settings=settings,
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_nested_follow_created_urls():
    settings = "tests.config_files.conf_nested_apps"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host,)
        assert "<h1>LeagueA Index Page</h1>" in resp.content.decode("utf-8")
        tree = html.fromstring(resp.content)
        home = tree.xpath('//*[@id="home_url"]/@href')[0]
        nested_first_level_url = tree.xpath('//*[@id="nested_first_level_url"]/@href')[
            0
        ]
        nested_second_level_url = tree.xpath(
            '//*[@id="nested_second_level_url"]/@href'
        )[0]
        nested_third_level_no_options = tree.xpath(
            '//*[@id="nested_third_level_no_options"]/@href'
        )[0]
        nested_third_level_options = tree.xpath(
            '//*[@id="nested_third_level_options"]/@href'
        )[0]

        nested_third_level_namespace = tree.xpath(
            '//*[@id="nested_third_level_namespace"]/@href'
        )[0]

        resp_home = requests.get(f"http://127.0.0.1:8000{home}")
        resp_nested_first_level_url = requests.get(
            f"http://127.0.0.1:8000{nested_first_level_url}"
        )

        resp_nested_second_level_url = requests.get(
            f"http://127.0.0.1:8000{nested_second_level_url}"
        )

        resp_nested_third_level_no_options = requests.get(
            f"http://127.0.0.1:8000{nested_third_level_no_options}"
        )
        resp_nested_third_level_options = requests.get(
            f"http://127.0.0.1:8000{nested_third_level_options}"
        )

        resp_nested_third_level_namespace = requests.get(
            f"http://127.0.0.1:8000{nested_third_level_namespace}"
        )

        assert resp.status_code == 200
        assert resp_home.status_code == 200

        assert resp_nested_first_level_url.status_code == 200
        assert resp_nested_second_level_url.status_code == 200
        assert resp_nested_third_level_no_options.status_code == 200
        assert resp_nested_third_level_options.status_code == 200
        assert resp_nested_third_level_namespace.status_code == 200
        assert (
            "<h2>Params: Penguins</h2>"
            in resp_nested_second_level_url.content.decode("utf-8")
        )

        assert (
            "<h2>Params: Penguins Crosby</h2>"
            in resp_nested_third_level_no_options.content.decode("utf-8")
        )
        assert (
            "<h2>Params: Penguins Crosby</h2>"
            in resp_nested_third_level_options.content.decode("utf-8")
        )
        assert "<h3>87</h3>" in resp_nested_third_level_options.content.decode("utf-8")

        assert (
            "<h2>Params: Oilers Tippett</h2>"
            in resp_nested_third_level_namespace.content.decode("utf-8")
        )

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/tests/test_app_nested/leagueA/first_league/",
        settings=settings,
        debug=True,
    )


async def send_websocket_message(text):
    uri = "ws://127.0.0.1:8000"
    await asyncio.sleep(1)
    async with websockets.connect(uri) as websocket:
        await websocket.send(text)
        z = await websocket.recv()
        return z


async def create_crax_server():
    config = Config(Crax("tests.config_files.conf_minimal"))
    server = Server(config)
    await server.serve()


async def wait_first(text):
    done, pending = await asyncio.wait(
        [create_crax_server(), send_websocket_message(text)],
        return_when=asyncio.FIRST_COMPLETED,
    )
    sys.stdout.write(list(done)[0].result())


def test_websocket_message(capsys):
    text = "Test websocket message"
    asyncio.get_event_loop().run_until_complete(wait_first(text))
    captured = capsys.readouterr()
    assert "Accepted" in captured.out.split("\n")
    assert text in captured.out.split("\n")
