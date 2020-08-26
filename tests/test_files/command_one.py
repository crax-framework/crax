import json
import os

import shutil
import pytest
from alembic.config import Config

from tests.test_files.command_utils import (
    get_config_variable,
    cleaner,
    Commands,
    replacement,
    check_table_exists,
)

OPTIONS = get_config_variable("COMMAND_OPTIONS")


@pytest.fixture
def create_command(request):
    return Commands(request.param)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "create_command", [["app_five.conf", True, {"database": "custom"}]], indirect=True
)
async def test_initial_migrations_custom_db(create_command):
    replacement("app_two/models.py", "# database = 'custom'", "database = 'custom'")
    replacement("app_three/models.py", "# database = 'custom'", "database = 'custom'")
    replacement(
        "app_three/models.py",
        "from tests.app_one.models import CustomerB, Vendor",
        "from tests.app_five.models import CustomerB, Vendor",
    )
    with cleaner("alembic_env"):
        make_migrations = create_command.make_migrations()
        make_migrations()
        config = Config("alembic.ini")
        db_map = json.loads(config.get_main_option("crax_db_map"))["custom"]
        assert ["app_five", "app_two", "app_three"] == list(db_map)
        assert config.get_main_option("crax_migrated") == "not migrated"
        assert os.path.exists("alembic_env")
        assert os.path.isfile("alembic.ini")
        assert os.path.exists("app_three/migrations/custom")
        assert os.path.exists("app_five/migrations/custom")
        assert os.path.exists("app_two/migrations/custom")

        create_all = Commands(
            ["app_five.conf", True, {"database": "custom"}]
        ).create_all()
        create_all()
        check = await check_table_exists(
            create_command.default_connection, "customer_b"
        )
        assert check is not False
        drop_all = Commands(["app_five.conf", True, {"database": "custom"}]).drop_all()
        drop_all()
        check = await check_table_exists(
            create_command.default_connection, "customer_b"
        )
        assert check is False
        if os.path.exists("alembic_env"):
            shutil.rmtree("alembic_env")
            os.remove("alembic.ini")
        shutil.rmtree("app_five/migrations")
        shutil.rmtree("app_two/migrations")
        shutil.rmtree("app_three/migrations")
        make_migrations()
        assert os.path.exists("alembic_env")
        assert os.path.isfile("alembic.ini")
        assert os.path.exists("app_five/migrations/custom")
        assert os.path.exists("app_two/migrations/custom")
        assert os.path.exists("app_three/migrations/custom")
        migrate = Commands(["app_five.conf", True, {"database": "custom"}]).migrate()
        migrate()
        check = await check_table_exists(
            create_command.default_connection, "customer_b"
        )
        assert check is True
        replacement("app_two/models.py", "database = 'custom'", "# database = 'custom'")
        replacement(
            "app_three/models.py", "database = 'custom'", "# database = 'custom'"
        )
        replacement(
            "app_three/models.py",
            "from tests.app_five.models import CustomerB, Vendor",
            "from tests.app_one.models import CustomerB, Vendor",
        )
