import json
import os
import shutil

import pytest
from databases import Database
from tests.app_one.models import CustomerB
from tests.test_files.command_utils import (
    cleaner,
    Commands,
    check_table_exists,
    checking_query,
    migration_assertions,
    replacement,
)


@pytest.fixture
def create_command(request):
    return Commands(request.param)


@pytest.mark.parametrize(
    "create_command", [["config_files.conf_db_missed", True, {}]], indirect=True
)
def test_missed_db(create_command):
    with cleaner("alembic_env"):
        try:
            make_migrations = create_command.make_migrations()
            make_migrations()
        except Exception as e:
            assert "Invalid configuration:  Missed required parameter DATABASES" in str(
                e
            )


@pytest.mark.parametrize("create_command", [["app_one.conf", True, {}]], indirect=True)
def test_missed_not_migrated(create_command):
    with cleaner("alembic_env"):
        try:
            migrate = create_command.migrate()
            migrate()
        except Exception as e:
            assert (
                "You can not run migrate command before migrations not created"
                in str(e)
            )


@pytest.mark.parametrize("create_command", [["app_one.conf", True, {}]], indirect=True)
def test_missed_not_migrated_history(create_command):
    with cleaner("alembic_env"):
        try:
            show_history = create_command.show_history()
            show_history()
        except Exception as e:
            assert (
                "You can not run show history command before migrations not created"
                in str(e)
            )


@pytest.mark.parametrize(
    "create_command", [["config_files.conf_db_wrong_type", True, {}]], indirect=True
)
def test_db_wrong_type(create_command):
    try:
        make_migrations = create_command.make_migrations()
        make_migrations()
    except Exception as e:
        assert "Invalid configuration:  DATABASES parameter should be a dict" in str(e)


@pytest.mark.parametrize(
    "create_command",
    [["config_files.conf_auth_no_default_db", True, {}]],
    indirect=True,
)
def test_no_default_db(create_command):
    try:
        make_migrations = create_command.make_migrations()
        make_migrations()
    except Exception as e:
        assert (
            "Invalid configuration:  "
            'DATABASES dictionary should contain "default" database' in str(e)
        )


@pytest.mark.parametrize(
    "create_command", [["app_one.conf", True, {"database": "custom"}]], indirect=True
)
def test_initial_migrations_key_error(create_command):
    try:
        make_migrations = create_command.make_migrations()
        make_migrations()
    except Exception as e:
        assert "Database connection improperly configured 'custom'" in str(e)


@pytest.mark.asyncio
@pytest.mark.parametrize("create_command", [["app_one.conf", True, {}]], indirect=True)
async def test_initial_migrations(create_command):
    with cleaner("alembic_env"):
        make_migrations = create_command.make_migrations()
        make_migrations()
        config = create_command.config
        assert config.get_main_option("crax_migrated") == "not migrated"
        migration_assertions(config)
        create_all = create_command.create_all()
        create_all()

        check = await check_table_exists(
            create_command.default_connection, "customer_b"
        )
        assert check is True
        customer = await checking_query()
        assert customer["bio"] == "Python Core Developer"
        assert customer["discount"] == 4
        drop_all = create_command.drop_all()
        drop_all()
        check = await check_table_exists(
            create_command.default_connection, "customer_b"
        )
        assert check is False

        if os.path.exists("alembic_env"):
            shutil.rmtree("alembic_env")
            os.remove("alembic.ini")
        shutil.rmtree("app_one/migrations")
        shutil.rmtree("app_two/migrations")
        shutil.rmtree("app_three/migrations")
        make_migrations()
        migrate = create_command.migrate()
        migrate()
        check = await check_table_exists(
            create_command.default_connection, "customer_b"
        )
        assert check is True
        customer = await checking_query()
        assert customer["bio"] == "Python Core Developer"
        assert customer["discount"] == 4


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "create_command",
    [["app_one.conf", True, {"apps": ["app_one", "app_two"]}]],
    indirect=True,
)
async def test_initial_migrations_apps(create_command):
    with cleaner("alembic_env"):
        make_migrations = create_command.make_migrations()
        make_migrations()
        config = create_command.config
        assert config.get_main_option("crax_migrated") == "not migrated"
        migration_assertions(config, apps=True)
        create_all = create_command.create_all()
        create_all()

        check = await check_table_exists(
            create_command.default_connection, "customer_b"
        )
        assert check is True
        customer = await checking_query()
        assert customer["bio"] == "Python Core Developer"
        assert customer["discount"] == 4
        drop_all = create_command.drop_all()
        drop_all()
        check = await check_table_exists(
            create_command.default_connection, "customer_b"
        )
        assert check is False

        if os.path.exists("alembic_env"):
            shutil.rmtree("alembic_env")
            os.remove("alembic.ini")
        shutil.rmtree("app_one/migrations")
        shutil.rmtree("app_two/migrations")

        make_migrations()
        migrate = create_command.migrate()
        migrate()
        check = await check_table_exists(
            create_command.default_connection, "customer_b"
        )
        assert check is True
        check = await check_table_exists(create_command.default_connection, "orders")
        assert check is False
        customer = await checking_query()
        assert customer["bio"] == "Python Core Developer"
        assert customer["discount"] == 4


@pytest.mark.parametrize(
    "create_command", [["app_one.conf", True, {"sql": True}]], indirect=True
)
def test_initial_migrations_sql(create_command):
    with cleaner("alembic_env"):
        make_migrations = create_command.make_migrations()
        make_migrations()
        config = create_command.config
        assert config.get_main_option("crax_migrated") == "not migrated"
        migrate = Commands(["app_one.conf", True, {"sql": True}]).migrate()
        migrate()
        assert os.path.exists("app_one/migrations/sql")
        assert os.path.exists("app_two/migrations/sql")
        assert os.path.exists("app_three/migrations/sql")


@pytest.mark.parametrize(
    "create_command", [["app_one.conf", True, {"sql": True}]], indirect=True
)
def test_initial_migrations_history(create_command, capsys):
    with cleaner("alembic_env"):
        make_migrations = create_command.make_migrations()
        make_migrations()
        config = create_command.config
        assert config.get_main_option("crax_migrated") == "not migrated"
        migrate = Commands(["app_one.conf", True, {}]).migrate()
        migrate()
        migration_assertions(config)

        show_history = Commands(["app_one.conf", True, {}]).show_history()
        show_history()
        config = create_command.config
        versions = config.get_main_option("crax_latest_revisions")
        versions = json.loads(versions)
        captured = capsys.readouterr()

        captured = captured.out
        for x in versions.values():
            assert x in captured

        show_history = Commands(["app_one.conf", True, {"latest": True}]).show_history()
        show_history()
        for x in versions.values():
            assert x in captured


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "create_command", [["app_one.conf", True, {"sql": True}]], indirect=True
)
async def test_initial_migrations_downgrade(create_command):
    with cleaner("alembic_env"):
        make_migrations = create_command.make_migrations()
        make_migrations()
        config = create_command.config
        assert config.get_main_option("crax_migrated") == "not migrated"

        migration_assertions(config)

        migrate = Commands(["app_one.conf", True, {}]).migrate()
        migrate()

        check = await check_table_exists(create_command.default_connection, "orders")
        assert check is True
        config = create_command.config
        versions = config.get_main_option("crax_latest_revisions")
        versions = json.loads(versions)
        migrate = Commands(["app_one.conf", True, {"down": True}]).migrate()
        migrate()
        check = await check_table_exists(create_command.default_connection, "orders")
        assert check is False

        migrate = Commands(
            ["app_one.conf", True, {"revision": versions["default/app_two"]}]
        ).migrate()
        migrate()
        check = await check_table_exists(
            create_command.default_connection, "customer_discount"
        )
        assert check is True
        check = await check_table_exists(create_command.default_connection, "orders")
        assert check is False
        try:
            migrate = Commands(
                ["app_one.conf", True, {"down": True, "revision": "wrong_revision"}]
            ).migrate()
            migrate()
        except Exception as e:
            assert "Can't locate revision identified by 'wrong_revision'" in str(e)


@pytest.mark.asyncio
@pytest.mark.parametrize("create_command", [["app_one.conf", True, {}]], indirect=True)
async def test_initial_migrations_deleted(create_command):
    with cleaner("alembic_env"):
        make_migrations = create_command.make_migrations()
        make_migrations()
        config = create_command.config
        migration_assertions(config)
        migrate = Commands(["app_one.conf", True, {}]).migrate()
        migrate()

        check = await check_table_exists(create_command.default_connection, "orders")
        assert check is True

        connection = create_command.default_connection
        if "mysql+pymysql" in connection:
            connection = connection.replace("mysql+pymysql", "mysql")
        database = Database(connection)
        if "sqlite" not in connection:
            query = (
                "DROP TABLE IF EXISTS orders, customer_a, customer_b,"
                " vendor, customer_discount, vendor_discount;"
            )
            await database.connect()
            await database.execute(query=query)
            await database.disconnect()
        else:
            async with database.transaction():
                await database.execute(query="DROP TABLE IF EXISTS orders;")
                await database.execute(query="DROP TABLE IF EXISTS customer_a; ")
                await database.execute(query="DROP TABLE IF EXISTS customer_b; ")
                await database.execute(query="DROP TABLE IF EXISTS vendor; ")
                await database.execute(query="DROP TABLE IF EXISTS customer_discount; ")
                await database.execute(query="DROP TABLE IF EXISTS vendor_discount; ")

        shutil.rmtree("app_one/migrations")
        shutil.rmtree("app_two/migrations")
        shutil.rmtree("app_three/migrations")
        if os.path.exists("../crax/auth/migrations"):
            shutil.rmtree("../crax/auth/migrations")
        assert not os.path.exists("app_one/migrations")
        assert not os.path.exists("app_two/migrations")
        assert not os.path.exists("app_three/migrations")
        make_migrations = Commands(["app_one.conf", True, {}]).make_migrations()
        make_migrations()
        assert os.path.exists("app_one/migrations")
        assert os.path.exists("app_two/migrations")
        assert os.path.exists("app_three/migrations")


@pytest.mark.asyncio
@pytest.mark.parametrize("create_command", [["app_one.conf", True, {}]], indirect=True)
async def test_initial_migrations_and_env_deleted(create_command):
    with cleaner("alembic_env"):
        make_migrations = create_command.make_migrations()
        make_migrations()
        config = create_command.config
        migration_assertions(config)
        migrate = Commands(["app_one.conf", True, {}]).migrate()
        migrate()

        check = await check_table_exists(create_command.default_connection, "orders")
        assert check is True
        drop_all = Commands(["app_one.conf", True, {}]).drop_all()
        drop_all()
        shutil.rmtree("alembic_env")
        shutil.rmtree("app_one/migrations")
        shutil.rmtree("app_two/migrations")
        shutil.rmtree("app_three/migrations")
        if os.path.exists("../crax/auth/migrations"):
            shutil.rmtree("../crax/auth/migrations")
        assert not os.path.exists("app_one/migrations")
        assert not os.path.exists("app_two/migrations")
        assert not os.path.exists("app_three/migrations")
        make_migrations = Commands(["app_one.conf", True, {}]).make_migrations()
        make_migrations()
        assert os.path.exists("app_one/migrations")
        assert os.path.exists("app_two/migrations")
        assert os.path.exists("app_three/migrations")


@pytest.mark.asyncio
@pytest.mark.parametrize("create_command", [["app_one.conf", True, {}]], indirect=True)
async def test_migrations(create_command):

    make_migrations = create_command.make_migrations()
    make_migrations()
    config = create_command.config
    migration_assertions(config)
    migrate = create_command.migrate()
    migrate()

    check = await check_table_exists(create_command.default_connection, "orders")
    assert check is True

    try:
        values = {
            "username": "chris",
            "password": "qwerty",
            "bio": "Nil!",
            "first_name": "Chris",
            "age": 27,
        }
        await CustomerB.query.insert(values=values)
    except Exception as e:
        assert "Unconsumed column names: age" in str(e)

    replacement(
        "app_two/models.py",
        "# start_date = sa.Column(sa.DateTime(), nullable=True)",
        "start_date = sa.Column(sa.DateTime(), nullable=True)",
    )
    replacement(
        "app_one/models.py",
        "# age = sa.Column(sa.Integer(), nullable=True)",
        "age = sa.Column(sa.Integer(), nullable=True)",
    )
