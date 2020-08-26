import json
import os
import shutil
import time
from base64 import b64decode

import pytest
import requests
from lxml import html
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database, drop_database
from crax.auth.models import AnonymousUser, User
from crax.commands.create_swagger import CreateSwagger
from crax.utils import get_settings_variable, unpack_urls
from crax.auth.authentication import (
    create_session_signer,
    check_password,
    create_password,
    login,
)

from .utils import SimpleResponseTest
from .command_utils import get_db_engine, get_config_variable

OPTIONS = get_config_variable("COMMAND_OPTIONS")


def test_properties():
    assert AnonymousUser().username == ""
    user = User()
    user.session = "session"
    user.pk = 13
    user.full_name = "Joe Doe"
    assert user.session == "session"
    assert user.pk == 13
    assert user.full_name == "Joe Doe"
    assert user.__str__() == "Joe Doe"


@pytest.fixture(name="test_db")
def create_test_db():
    test_mode = os.environ["CRAX_TEST_MODE"]
    docker_db_host = os.environ.get("DOCKER_DATABASE_HOST", None)
    if test_mode != "sqlite":
        e = get_db_engine()
        engine = create_engine(e)
        if docker_db_host is None:
            if not database_exists(engine.url):
                create_database(engine.url)
            else:
                drop_database(engine.url)
                create_database(engine.url)
            sql_dump = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), f"test_{test_mode}.sql"
            )
            if test_mode == "postgresql":
                os.system('psql test_crax -c "DROP SCHEMA public CASCADE;"')
                os.system('psql test_crax -c "CREATE SCHEMA public;"')
                os.system('psql test_crax -c "GRANT ALL ON SCHEMA public TO postgres;"')
                os.system('psql test_crax -c "GRANT ALL ON SCHEMA public TO crax;"')
                os.system('psql test_crax -c "GRANT ALL ON SCHEMA public TO public;"')
                os.system('psql test_crax -c "COMMENT ON SCHEMA public IS \'standard public schema\';"')
                os.system(f"psql test_crax < {sql_dump}")
            elif test_mode == "mysql":
                if "TRAVIS" not in os.environ:
                    os.system(f"mysql test_crax < {sql_dump} -u crax -pCraxPassword")
                else:
                    os.system(f"mysql test_crax < {sql_dump} -u root")
    else:
        if os.path.isfile("test_files/test_crax.sqlite"):
            shutil.copyfile("test_files/test_crax.sqlite", "test_crax.sqlite")


@pytest.mark.asyncio
async def test_first_app_no_auth():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert "set-cookie" not in resp.headers
        assert resp.status_code == 200
        assert "Testing index page" in resp.content.decode("utf-8")

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/",
        settings="tests.config_files.conf_auth_no_auth_middleware",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert "set-cookie" in resp.headers
        assert "session_id" in resp.headers["set-cookie"]
        signer, _, _, _ = create_session_signer()
        cookie = b64decode(resp.headers["set-cookie"][11:])
        user = signer.unsign(cookie, max_age=600)
        user_lst = user.decode("utf-8").split(":")
        assert user_lst[1] == "0"
        assert resp.status_code == 200
        assert "Testing index page" in resp.content.decode("utf-8")

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/",
        settings="tests.config_files.conf_auth",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_secret_missed():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert (
                ' <h2 class="crax_mark">Invalid configuration:  &#34;SECRET_KEY&#34; '
                "string should be defined in settings to use Crax Sessions</h2>"
                in resp.content.decode("utf-8")
        )
        assert resp.status_code == 500

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/",
        settings="tests.config_files.conf_auth_no_secret",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_create_user_no_key():
    def any_no_settings(host):
        time.sleep(1)

        resp = requests.post(host, data={"username": "mark", "password": "qwerty"})
        assert (
                '<h2 class="crax_mark">Invalid configuration:  '
                "&#34;SECRET_KEY&#34; string should be defined in settings to use"
                " Crax Sessions</h2>" in resp.content.decode("utf-8")
        )
        assert resp.status_code == 500

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/login",
        settings="tests.config_files.conf_auth_no_secret",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_create_password_no_key():
    def any_no_settings():
        time.sleep(1)
        try:
            create_password("qwerty")
        except Exception as e:
            return str(e)

    password = await SimpleResponseTest(
        any_no_settings, settings="tests.config_files.conf_auth_no_secret", debug=True
    )
    assert (
            "Invalid configuration:  "
            '"SECRET_KEY" variable should be defined to use'
            " Authentication backends" in password
    )


@pytest.mark.asyncio
async def test_first_app_check_password_no_key():
    def any_no_settings():
        time.sleep(1)
        try:
            check_password("qwerty", "qwerty")
        except Exception as e:
            return str(e)

    password = await SimpleResponseTest(
        any_no_settings, settings="tests.config_files.conf_auth_no_secret", debug=True
    )
    assert (
            "Invalid configuration:  "
            '"SECRET_KEY" variable should be defined to use '
            "Authentication backends" in password
    )


@pytest.mark.asyncio
async def test_first_app_login_secret_missed():
    time.sleep(1)
    try:
        await login(None, "qwerty", "qwerty")
    except Exception as e:

        assert (
                "Invalid configuration:  "
                '"SECRET_KEY" variable should be defined to use'
                " Authentication backends" in str(e)
        )


@pytest.mark.asyncio
async def test_first_app_login_required_debug():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 401
        assert "<h2>CraxUnauthorized</h2>" in resp.content.decode("utf-8")

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/protected/",
        settings="tests.config_files.conf_auth",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_login_required_no_debug():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 403
        assert resp.json()["Error"] == "Testing Access Denied"

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/protected/",
        settings="tests.config_files.conf_auth",
    )


@pytest.mark.asyncio
async def test_first_app_auth_missed_db_conf():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.post(host, data={"username": "mark", "password": "qwerty"})
        assert resp.status_code == 500
        assert (
                '<h2 class="crax_mark">Database connection improperly configured'
                " Improperly configured project settings. "
                "Missed required parameter &#34;DATABASES&#34;</h2>"
                in resp.content.decode("utf-8")
        )

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/login",
        settings="tests.config_files.conf_db_missed",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_missed_db_key():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 500
        assert (
                'No database connection found. Check your configuration.'
                in resp.content.decode("utf-8")
        )

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/wrong_insert",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_no_db():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.post(host, data={"username": "mark", "password": "qwerty"})
        assert resp.status_code == 500
        assert (
                ' <h2 class="crax_mark">Database connection improperly '
                "configured Improperly configured project settings."
                " DATABASES dictionary should contain &#34;default&#34; database</h2>"
                in resp.content.decode("utf-8")
        )

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/login",
        settings="tests.config_files.conf_auth_no_default_db",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_db_wrong_type(test_db):
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.post(host, data={"username": "mark", "password": "qwerty"})
        assert resp.status_code == 500
        assert (
                ' <h2 class="crax_mark">Database connection improperly configured '
                "Improperly configured project settings. "
                "DATABASES parameter should be a dict</h2>" in resp.content.decode("utf-8")
        )

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/login",
        settings="tests.config_files.conf_db_wrong_type",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_wrong_query_method():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 500
        assert (
                '<h2 class="crax_mark">User model has no method unexpected_method</h2>'
                in resp.content.decode("utf-8")
        )

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/wrong_method_insert",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_wrong_table_method():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert resp.status_code == 500
        assert (
                ' <h2 class="crax_mark">User has no attribute prefetch_seclect</h2>'
                in resp.content.decode("utf-8")
        )

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/wrong_table_method",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_right_superuser(test_db):
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.post(host, data={"username": "mark", "password": "qwerty"})
        body = resp.json()
        assert body["username"] == "mark"
        assert resp.status_code == 201
        cookies = resp.cookies
        resp = requests.get("http://127.0.0.1:8000/protected/", cookies=cookies)
        assert resp.status_code == 200
        resp = requests.get("http://127.0.0.1:8000/staff_only/", cookies=cookies)
        assert resp.status_code == 200
        resp = requests.get("http://127.0.0.1:8000/superuser_only/", cookies=cookies)
        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/login",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_right_simple_user_perms(test_db):
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.post(host, data={"username": "joe", "password": "qwerty"})
        body = resp.json()
        assert body["username"] == "joe"
        assert body["pk"] != 0
        assert body["is_authenticated"] is True
        assert body["is_active"] is True
        assert body["is_staff"] is False
        assert body["is_superuser"] is False
        assert resp.status_code == 201
        cookies = resp.cookies
        resp = requests.get("http://127.0.0.1:8000/staff_only/", cookies=cookies)
        assert resp.status_code == 403
        resp = requests.get("http://127.0.0.1:8000/superuser_only/", cookies=cookies)
        assert resp.status_code == 403

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/login",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_create_user(test_db):
    def any_no_settings(host):
        time.sleep(1)

        resp = requests.post(
            host,
            data={
                "username": "sid",
                "password": "qwerty",
                "first_name": "Sidney",
                "last_name": "Crosby",
            },
        )
        body = resp.json()
        assert body["first_username"] == "mark"
        assert body["username"] == "sid"
        assert int(body["len_after"]) == int(body["len_before"]) + 1
        assert body["names_after"] == ["mark", "joe", "sid"]
        assert resp.status_code == 201
        cookies = resp.cookies
        resp = requests.get("http://127.0.0.1:8000/protected/", cookies=cookies)
        assert resp.status_code == 200
        resp = requests.get("http://127.0.0.1:8000/login/", cookies=cookies)
        assert resp.status_code == 200
        resp = requests.get("http://127.0.0.1:8000/staff_only/", cookies=cookies)
        assert resp.status_code == 200
        resp = requests.get("http://127.0.0.1:8000/superuser_only/", cookies=cookies)
        assert resp.status_code == 403
        logout_resp = requests.get("http://127.0.0.1:8000/logout/", cookies=cookies)
        logout_cookies = logout_resp.cookies
        resp = requests.get("http://127.0.0.1:8000/protected/", cookies=logout_cookies)
        assert resp.status_code == 401

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/create",
        settings="tests.config_files.conf_auth_right_no_db_options",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_missed_user(test_db):
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.post(host, data={"username": "william", "password": "qwerty"})
        assert resp.status_code == 201
        cookies = resp.cookies
        resp = requests.get("http://127.0.0.1:8000/protected/", cookies=cookies)
        assert resp.status_code == 401

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/login",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_wrong_password(test_db):
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.post(host, data={"username": "mark", "password": "123456"})
        assert resp.status_code == 201
        cookies = resp.cookies
        resp = requests.get("http://127.0.0.1:8000/protected/", cookies=cookies)
        assert resp.status_code == 401

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/login",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_wrong_user():
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)
        assert (
                ' <h2 class="crax_mark">Invalid configuration:'
                "  &#34;SECRET_KEY&#34; string should be defined in settings"
                " to use Crax Sessions</h2>" in resp.content.decode("utf-8")
        )
        assert resp.status_code == 500

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/login",
        settings="tests.config_files.conf_auth_no_secret",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_right_simple_user_logout(test_db):
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.post(host, data={"username": "joe", "password": "qwerty"})
        assert resp.status_code == 201
        cookies = resp.cookies
        resp = requests.get("http://127.0.0.1:8000/protected/", cookies=cookies)
        assert resp.status_code == 200
        logout_resp = requests.get("http://127.0.0.1:8000/logout/", cookies=cookies)
        logout_cookies = logout_resp.cookies
        resp = requests.get("http://127.0.0.1:8000/protected/", cookies=logout_cookies)
        assert resp.status_code == 401

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/login",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_right_simple_user(test_db):
    def any_no_settings(host):
        time.sleep(1)
        resp = requests.post(host, data={"username": "joe", "password": "qwerty"})
        assert resp.status_code == 201
        cookies = resp.cookies
        resp = requests.get("http://127.0.0.1:8000/protected/", cookies=cookies)
        assert resp.status_code == 200
        logout_resp = requests.get("http://127.0.0.1:8000/logout/", cookies=cookies)
        logout_cookies = logout_resp.cookies
        resp = requests.get("http://127.0.0.1:8000/protected/", cookies=logout_cookies)
        assert resp.status_code == 401

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/login",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_bad_signature():
    def any_no_settings(host):
        time.sleep(1)
        session = requests.Session()
        session.cookies.set(
            "session_id", "bWFyazo0LlhJSdG9rbno1a0V", domain="127.0.0.1", path="/"
        )
        resp = session.get("http://127.0.0.1:8000/protected/")
        assert resp.status_code == 401

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/wrong_session",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_bad_session():
    def any_no_settings(host):
        time.sleep(1)
        session = requests.Session()
        resp = session.get(host)
        assert resp.status_code == 200
        resp = session.get("http://127.0.0.1:8000/protected/")
        assert resp.status_code == 401

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/wrong_session",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_anonymous_session():
    def any_no_settings(host):
        time.sleep(1)
        session = requests.Session()
        resp = session.get(host)
        assert resp.status_code == 200
        resp = session.get("http://127.0.0.1:8000/protected/")
        assert resp.status_code == 401

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/anonymous_session",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_auth_insert_users(test_db):
    def any_no_settings(host):
        time.sleep(1)
        session = requests.Session()
        users = {
            "username": "willy",
            "password": "qwerty",
            "first_name": "William",
        }
        resp = session.post(host, data={"users": json.dumps(users)})
        assert resp.status_code == 201
        body = resp.json()
        assert int(body["len_after"]) == int(body["len_before"]) + 1

        bulk_users = [
            {
                "username": "jamie",
                "password": "qwerty",
                "first_name": "James",
            },
            {"username": "rob", "password": "qwerty", "first_name": "Robert"},
            {"username": "tom", "password": "qwerty", "first_name": "Tomas"},
        ]
        resp = session.post(host, data={"users": json.dumps(bulk_users)})
        assert resp.status_code == 201
        body = resp.json()
        assert int(body["len_after"]) == int(body["len_before"]) + 3

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/insert",
        settings="tests.config_files.conf_auth_right",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_rest(test_db):
    def any_no_settings(host):
        time.sleep(1)
        users = [
            {
                "username": "jamie",
                "password": "qwerty",
                "first_name": "James",
                "bio": "Python Developer",
            },
            {
                "username": "rob",
                "password": "qwerty",
                "first_name": "Robert",
                "bio": "Python Developer",
            },
            {
                "username": "tom",
                "password": "qwerty",
                "first_name": "Tomas",
                "bio": "Python Developer",
            },
        ]

        resp = requests.post(host, json=users)
        assert resp.status_code == 201
        resp = requests.get(host)
        body = resp.json()
        assert [x["first_name"] for x in body] == [x["first_name"] for x in users]

        res = requests.post(
            "http://127.0.0.1:8000/api/discounts",
            json={"name": "XMas Discount", "percent": 15},
        )
        assert res.status_code == 201

        res = requests.get("http://127.0.0.1:8000/api/customer/2/")
        body = res.json()
        assert body == {"id": 2, "name": "XMas Discount"}
        res = requests.patch(
            "http://127.0.0.1:8000/api/discount/1/",
            data={"discount": json.dumps({"name": "Liberty Day Discount"})},
        )

        assert res.status_code == 204
        res = requests.get("http://127.0.0.1:8000/api/customer/2/")
        body = res.json()
        assert body == {"id": 2, "name": "Liberty Day Discount"}

        res = requests.post(
            "http://127.0.0.1:8000/api/orders",
            data={
                "order": json.dumps(
                    {"staff": "Good Stuff", "price": 150, "customer_id": 2}
                )
            },
        )
        assert res.status_code == 201
        res = requests.get("http://127.0.0.1:8000/api/order/1/")
        body = res.json()
        assert body == {
            "id": 1,
            "staff": "Good Stuff",
            "price": 150,
            "vendor_id": None,
            "customer_id": 2,
        }

        res = requests.delete("http://127.0.0.1:8000/api/order/1/")
        assert res.status_code == 204

        resp = requests.get("http://127.0.0.1:8000/api/order/1/")
        body = resp.json()
        assert body is None

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/api/customers",
        settings="tests.config_files.conf_rest",
        debug=True,
    )


@pytest.mark.asyncio
async def test_first_app_csrf():
    def any_no_settings(host):
        time.sleep(1)

        resp = requests.post(host, data={"data": json.dumps({"test": "test data"})})
        assert resp.status_code == 403
        assert (
            '<h2 class="crax_mark">Access Denied CSRF token missed</h2>'
            in resp.content.decode("utf-8")
        )
        resp = requests.get(host)
        tree = html.fromstring(resp.content)
        csrf = tree.xpath('//*[@id="csrf_token"]/@value')[0]
        square = tree.xpath('//*[@id="square"]/@value')[0]
        hello = tree.xpath('//*[@id="hello"]/@value')[0]
        assert int(square) == 4
        assert hello == "Hello world"
        resp = requests.post(
            host, data={"data": json.dumps({"test": "test data"}), "csrf_token": csrf}
        )
        assert resp.status_code == 201
        resp = requests.post(
            host, data={"data": json.dumps({"test": "test data"}), "csrf_token": "csrf"}
        )
        assert resp.status_code == 403
        assert (
            '<h2 class="crax_mark">Access Denied CSRF token is incorrect</h2>'
            in resp.content.decode("utf-8")
        )
        resp = requests.patch(
            host, data={"data": json.dumps({"test": "test data"}), "csrf_token": ""}
        )
        assert resp.status_code == 403
        assert (
            '<h2 class="crax_mark">Access Denied CSRF token is empty</h2>'
            in resp.content.decode("utf-8")
        )

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/protected",
        settings="tests.config_files.conf_csrf",
        debug=True,
    )


@pytest.mark.asyncio
async def test_swagger():
    crax_path = __import__(CreateSwagger.__module__)
    swagger_file = f"{crax_path.__path__[0]}/swagger/static/swagger.json"
    with open(swagger_file, "w") as f:
        f.write("")
    os.environ["CRAX_SETTINGS"] = "config_files.conf_csrf"
    create_swagger = CreateSwagger(OPTIONS).create_swagger
    create_swagger()
    url_patterns = get_settings_variable("URL_PATTERNS")
    expected_urls = []
    url_list = [
        y
        for x in unpack_urls(url_patterns)
        for y in x.urls
        if "api" in y.path and y.tag != "crax"
    ]
    for u in url_list:
        re_path = False
        if u.type_ == "re_path":
            re_path = True
        z = CreateSwagger(OPTIONS).prepare_url([u.path], re_path=re_path)
        expected_urls.append(z)

    with open(swagger_file, "r") as f:
        swagger_data = json.load(f)
        urls = list(swagger_data["paths"])
        assert all(x in list(urls) for x in expected_urls)
        test_path = [x for x in expected_urls if "optional" in x][0]
        swagger_path = swagger_data["paths"][test_path]
        swagger_params = [x["name"] for x in swagger_path["get"]["parameters"]]
        test_params = test_path.replace("{", "").replace("}", "").split("/")
        assert swagger_params == test_params[3:]
        assert swagger_path["get"]["tags"] == [test_params[2]]
        assert swagger_path["delete"]["tags"] == [test_params[2]]
        assert swagger_path["patch"]["tags"] == [test_params[2]]
        assert swagger_path["patch"]["parameters"][0]["type"] == "integer"
        assert swagger_path["patch"]["parameters"][0]["format"] == "int64"
        assert swagger_path["patch"]["parameters"][1]["type"] == "string"
        assert swagger_path["patch"]["parameters"][1]["format"] == "string"

    def any_no_settings(host):
        time.sleep(1)
        resp = requests.get(host)

        assert resp.status_code == 200

    await SimpleResponseTest(
        any_no_settings,
        "http://127.0.0.1:8000/api_doc",
        settings="tests.config_files.conf_csrf",
        debug=True,
    )
