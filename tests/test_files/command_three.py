import datetime
import json
import os

import pytest

from tests.app_one.models import CustomerB
from tests.app_two.models import CustomerDiscount
from tests.test_files.command_utils import Commands, replacement


@pytest.fixture
def create_command(request):
    return Commands(request.param)


@pytest.mark.asyncio
@pytest.mark.parametrize("create_command", [["app_one.conf", False, {}]], indirect=True)
async def test_initial_migrations(create_command):
    make_migrations = create_command.make_migrations()
    make_migrations()
    migrate = Commands(["app_one.conf", False, {}]).migrate()
    migrate()
    values = {
        "username": "chris",
        "password": "qwerty",
        "bio": "Nil!",
        "first_name": "Chris",
        "age": 27,
    }
    await CustomerB.query.insert(values=values)
    await CustomerDiscount.query.insert(
        values={
            "name": "Customer Discount",
            "percent": 10,
            "start_date": datetime.datetime.now(),
        }
    )
    config = create_command.config
    versions = config.get_main_option("crax_latest_revisions")
    versions = json.loads(versions)
    version = [
        x
        for x in os.listdir("app_two/migrations")
        if x != "__pycache__" and versions["default/app_two"] not in x
    ][0][:-4]

    migrate = Commands(
        ["app_one.conf", False, {"down": True, "revision": version}]
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
        "app_two/models.py",
        "start_date = sa.Column(sa.DateTime(), nullable=True)",
        "# start_date = sa.Column(sa.DateTime(), nullable=True)",
    )
    replacement(
        "app_one/models.py",
        "age = sa.Column(sa.Integer(), nullable=True)",
        "# age = sa.Column(sa.Integer(), nullable=True)",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "create_command", [["app_four.conf", True, {"database": "custom"}]], indirect=True
)
async def test_migrations_multi(create_command):

    make_migrations = create_command.make_migrations()
    make_migrations()
    migrate = create_command.migrate()
    migrate()

    try:
        values = {
            "id": 33,
            "username": "chris",
            "password": "qwerty",
            "bio": "Nil!",
            "first_name": "Chris",
            "age": 27,
        }
        await CustomerB.query.insert(values=values)
    except Exception as e:
        assert "age" in str(e)

    replacement(
        "app_six/models.py",
        "# start_date = sa.Column(sa.DateTime(), nullable=True)",
        "start_date = sa.Column(sa.DateTime(), nullable=True)",
    )
    replacement(
        "app_four/models.py",
        "# age = sa.Column(sa.Integer(), nullable=True)",
        "age = sa.Column(sa.Integer(), nullable=True)",
    )
