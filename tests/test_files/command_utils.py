import json
import os
import re
import shutil

from alembic.config import Config
from databases import Database
import in_place
from pymysql import OperationalError

from sqlalchemy import create_engine, and_
from sqlalchemy_utils import database_exists, create_database, drop_database

from yaml import load, FullLoader
from crax.commands.history import DBHistory
from crax.commands.makemigrations import MakeMigrations
from crax.commands.migrate import Migrate
from crax.commands.db_create_all import CreateAll
from crax.commands.db_drop_all import DropAll
from crax.auth.models import User
from tests.app_one.models import CustomerB
from tests.app_two.models import CustomerDiscount


def get_config_variable(variable):
    config = load(open("config.yaml", "r"), Loader=FullLoader)
    ret = load(config, Loader=FullLoader)[variable]
    return ret


OPTIONS = get_config_variable("COMMAND_OPTIONS")


def get_db_engine():
    test_mode = os.environ["CRAX_TEST_MODE"]
    docker_db_host = os.environ.get("DOCKER_DATABASE_HOST", None)
    if docker_db_host:
        engine = get_config_variable(docker_db_host)
    else:
        engines = get_config_variable("ENGINES")
        engine_type = engines[test_mode]
        if "TRAVIS" not in os.environ:
            engine = engine_type[0]
        else:
            engine = engine_type[1]
    return engine


async def check_table_exists(connection, table_name):
    query = None
    test_mode = os.environ["CRAX_TEST_MODE"]
    if test_mode != "sqlite":
        engine = get_db_engine()
        driver = re.split(r"://", engine)[0]
    else:
        driver = "sqlite"
    if "postgresql" in driver:
        query = "SELECT EXISTS(SELECT FROM information_schema.tables  WHERE table_name = :t_name);"
        database = Database(connection)
        await database.connect()
        check = await database.execute(query=query, values={"t_name": table_name})
        await database.disconnect()
    else:
        if "mysql" in driver:
            connection = connection.replace("mysql+pymysql", "mysql")
            query = (
                "SELECT COUNT(*) FROM information_schema.tables"
                " WHERE table_schema = 'test_crax' AND table_name = :t_name;"
            )
        elif "sqlite" in driver:
            query = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=:t_name;"
        if query:
            try:
                database = Database(connection)
                async with database as conn:
                    check = await conn.fetch_one(
                        query=query, values={"t_name": table_name}
                    )
                    check = bool(check[0])
            except OperationalError:
                check = False
        else:
            check = False
    return check


async def checking_query():
    bulk_users = get_config_variable("TEST_USERS")
    customer_ext = {
        "bio": "Python Core Developer",
        "discount": 4,
        "customer_discount_id": 1,
    }
    bulk_customers = [{**x, **customer_ext} for x in bulk_users]
    await CustomerDiscount.query.insert(
        values={"name": "Customer Discount", "percent": 10}
    )
    await User.query.bulk_insert(values=bulk_users)
    await CustomerB.query.bulk_insert(values=bulk_customers)
    query = CustomerB.select().where(
        and_(CustomerB.c.username == "tom", CustomerB.c.customer_discount_id == 1)
    )
    last = await CustomerB.query.last()
    all_ = await CustomerB.query.all()
    all_rows = [x["username"] for x in all_]
    assert all_rows == ["jamie", "rob", "tom"]
    assert last["username"] == "tom"
    row = await CustomerB.query.fetch_one(query=query)
    return row


def replacement(target_file, old, new):
    with in_place.InPlace(target_file) as fil:
        for line in fil:
            if old in line:
                new_line = line.replace(old, new)
            else:
                new_line = line
            fil.write(new_line)


def migration_assertions(config, apps=False):
    assert os.path.exists("alembic_env")
    assert os.path.isfile("alembic.ini")
    conf_map = config.get_main_option("crax_db_map")
    # In case if migrations was not applied config have got no db map. Thus we skip this step
    if conf_map is not None:
        db_map = json.loads(conf_map)["default"]
        assert ["app_one", "app_two", "app_three", "crax.auth"] == list(db_map)
        assert db_map["app_one"] == ["customer_a", "customer_b", "vendor"]
        assert db_map["app_two"] == ["customer_discount", "vendor_discount"]
        assert db_map["app_three"] == ["orders"]
        assert db_map["crax.auth"] == [
            "groups",
            "permissions",
            "users",
            "group_permissions",
            "user_groups",
            "user_permissions",
        ]

    assert os.path.exists("app_one/migrations")
    assert os.path.exists("app_two/migrations")
    if apps is False:
        assert os.path.exists("app_three/migrations")
    else:
        assert not os.path.exists("app_three/migrations")


class cleaner:
    def __init__(self, alembic_path):
        self.alembic_path = alembic_path

    def __enter__(self):
        if os.path.exists("alembic_env"):
            shutil.rmtree("alembic_env")
            os.remove("alembic.ini")

    def __exit__(self, exc_type, exc_value, traceback):
        if os.path.exists("alembic_env"):
            shutil.rmtree("alembic_env")
            os.remove("alembic.ini")
        if os.path.exists("app_one/migrations"):
            shutil.rmtree("app_one/migrations")
        if os.path.exists("app_two/migrations"):
            shutil.rmtree("app_two/migrations")
        if os.path.exists("app_three/migrations"):
            shutil.rmtree("app_three/migrations")
        if os.path.exists("app_five/migrations"):
            shutil.rmtree("app_five/migrations")
        if os.path.exists("../crax/auth/migrations"):
            shutil.rmtree("../crax/auth/migrations")


class Commands:
    def __init__(self, request):
        self.request = request
        self.settings = request[0]
        self.del_db = request[1]
        self.kwargs = request[2]
        os.environ["CRAX_SETTINGS"] = self.settings
        test_mode = os.environ["CRAX_TEST_MODE"]
        if self.del_db is True:
            if test_mode != "sqlite":
                e = get_db_engine()
                engine = create_engine(e)
                if not database_exists(engine.url):
                    create_database(engine.url)
                else:
                    drop_database(engine.url)
                    create_database(engine.url)
            else:
                if os.path.isfile("test_crax.sqlite"):
                    os.remove("test_crax.sqlite")
                _file = open("test_crax.sqlite", "w")
                _file.close()

    @property
    def config(self):
        return Config("alembic.ini")

    @property
    def default_connection(self):
        return MakeMigrations(OPTIONS, **self.kwargs).default_connection

    def make_migrations(self):
        return MakeMigrations(OPTIONS, **self.kwargs).make_migrations

    def migrate(self):
        return Migrate(OPTIONS, **self.kwargs).migrate

    def create_all(self):
        return CreateAll(OPTIONS, **self.kwargs).create_all

    def drop_all(self):
        return DropAll(OPTIONS, **self.kwargs).drop_all

    def show_history(self):
        return DBHistory(OPTIONS, **self.kwargs).show_history
