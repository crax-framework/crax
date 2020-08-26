import datetime
import json
import os
import shutil

import pytest
from databases import Database

from tests.app_six.models import CustomerDiscount
from tests.test_files.command_utils import Commands, replacement, cleaner


@pytest.fixture
def create_command(request):
    return Commands(request.param)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "create_command", [["app_four.conf", False, {"database": "custom"}]], indirect=True
)
async def test_migrations_multi(create_command):
    make_migrations = create_command.make_migrations()
    make_migrations()
    migrate = Commands(
        [
            "app_four.conf",
            False,
            {"database": "custom", "revision": "custom/app_four@head", "sql": True},
        ]
    ).migrate()
    migrate()
    assert os.path.exists("app_four/migrations/custom/sql")
    migrate = Commands(
        [
            "app_four.conf",
            False,
            {"database": "custom", "revision": "custom/app_four@head"},
        ]
    ).migrate()
    migrate()
    connection = create_command.default_connection
    if "mysql+pymysql" in connection:
        connection = connection.replace("mysql+pymysql", "mysql")
    database = Database(connection)
    query = (
        "INSERT INTO customer_b("
        "username, password, bio, first_name, age)"
        " VALUES (:username, :password, :bio, :first_name, :age)"
    )
    await database.connect()
    values = {
        "username": "chris",
        "password": "qwerty",
        "bio": "Nil!",
        "first_name": "Chris",
        "age": 27,
    }
    await database.execute(query=query, values=values)
    config = create_command.config
    versions = config.get_main_option("crax_latest_revisions")
    versions = json.loads(versions)
    migrate = Commands(
        [
            "app_four.conf",
            False,
            {
                "down": True,
                "revision": versions["custom/app_six"],
                "database": "custom",
            },
        ]
    ).migrate()
    migrate()
    try:
        await CustomerDiscount.query.insert(
            values={
                "name": "Customer Discount",
                "percent": 10,
                "start_date": datetime.datetime.now(),
            }
        )
    except Exception as e:
        assert "start_date" in str(e)
    replacement(
        "app_six/models.py",
        "start_date = sa.Column(sa.DateTime(), nullable=True)",
        "# start_date = sa.Column(sa.DateTime(), nullable=True)",
    )
    replacement(
        "app_four/models.py",
        "age = sa.Column(sa.Integer(), nullable=True)",
        "# age = sa.Column(sa.Integer(), nullable=True)",
    )

    if os.path.exists("app_one/migrations"):
        shutil.rmtree("app_one/migrations")
    if os.path.exists("app_two/migrations"):
        shutil.rmtree("app_two/migrations")
    if os.path.exists("app_three/migrations"):
        shutil.rmtree("app_three/migrations")
    if os.path.exists("app_four/migrations"):
        shutil.rmtree("app_four/migrations")
    if os.path.exists("app_five/migrations"):
        shutil.rmtree("app_five/migrations")
    if os.path.exists("app_six/migrations"):
        shutil.rmtree("app_six/migrations")


@pytest.mark.asyncio
@pytest.mark.parametrize("create_command", [["app_one.conf", True, {}]], indirect=True)
async def test_double_migrations(create_command, capsys):
    with cleaner("alembic_env"):
        make_migrations = create_command.make_migrations()
        make_migrations()
        try:
            make_migrations = Commands(["app_one.conf", True, {}]).make_migrations()
            make_migrations()
        except:
            captured = capsys.readouterr()
            assert (
                "You have unapplied migrations. "
                "Please run migrate command first" in captured.err
            )
