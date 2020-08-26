"""
Base classes for all database commands
"""
import configparser
import json
import os
from importlib import import_module, resources
from itertools import chain
from typing import Optional

import typing
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import MetaData, create_engine

from crax import get_settings
from crax.commands import BaseCommand
from crax.database import get_metadata, sort_applications
from crax.exceptions import CraxDataBaseImproperlyConfigured, CraxImproperlyConfigured


OPTIONS = [
    (["--database", "-d"], {"type": str, "help": "specify database to run migrations"}),
    (
        ["--apps", "-a"],
        {"type": str, "help": "generate migrations for app", "nargs": "*"},
    ),
    (
        ["--down", "-n"],
        {"help": "downgrade migrations", "action": "store_true", "dest": "down"},
    ),
]


class DataBaseCommands(BaseCommand):
    def __init__(self, opts: typing.List[typing.Union[tuple]], **kwargs) -> None:
        super(DataBaseCommands, self).__init__(opts)
        self.kwargs = kwargs
        self.db_map = {}
        self.db_keys = {}
        self.db_tables = []
        self.sorted_tables = []
        settings = os.environ.get("CRAX_SETTINGS", None)
        self.configuration = get_settings(settings=settings)
        required_params = ["BASE_URL", "APPLICATIONS", "DATABASES"]
        for x in required_params:
            if not hasattr(self.configuration, x):
                raise CraxImproperlyConfigured(f"Missed required parameter {x}")
        self.project_applications = self.configuration.APPLICATIONS

        self.project_url = self.configuration.BASE_URL

        self.databases = self.configuration.DATABASES
        if not isinstance(self.databases, dict):
            raise CraxImproperlyConfigured("DATABASES parameter should be a dict")

        elif settings is not None and "default" not in self.databases:
            raise CraxImproperlyConfigured(
                'DATABASES dictionary should contain "default" database'
            )

        self.default_connection = None
        self.db_name = None

        self.config_file = "alembic.ini"
        self.alembic_dir = "alembic_env"
        self.migrations_dir = "migrations"

        db = self.get_option("database")
        if db is None:
            self.set_database("default")
        else:
            self.set_database(db)

        if hasattr(self.configuration, "MIDDLEWARE"):
            middleware = self.configuration.MIDDLEWARE
            check_auth = [
                x
                for x in middleware
                if x.split(".")[-1] == "SessionMiddleware"
                or x.split(".")[-1] == "AuthMiddleware"
            ]
            if len(check_auth) == 2 and self.db_name == "default":
                self.project_applications.append("crax.auth")
        apps = self.get_option("apps")
        self.applications = []

        if apps:
            applications = [
                x for x in self.project_applications if x in apps or x == "crax.auth"
            ]
        else:
            applications = self.project_applications

        for app in applications:
            if app != "crax.auth":
                if "models.py" in os.listdir(f'{self.project_url}/{app}'):
                    content = open(f'{self.project_url}/{app}/models.py', "r").read()
                    if content:
                        self.applications.append(app)
            else:
                self.applications.append(app)
        if self.db_name != "default" and "crax.auth" in self.applications:
            self.applications.remove("crax.auth")

        self.config = self.check_config()

        if self.config is not None:
            self.config.set_main_option(
                "version_locations",
                " ".join(
                    [self.create_version_dir(app) for app in self.project_applications]
                ),
            )

        os.environ["CRAX_DB_CONNECTION"] = self.default_connection
        os.environ["CRAX_FULL_METADATA"] = " ".join(self.project_applications)

    def get_option(self, option):
        val = None
        if hasattr(self.args, option) and getattr(self.args, option, None) is not None:
            val = getattr(self.args, option)
        if option in self.kwargs:
            val = self.kwargs[option]
        return val

    def create_version_dir(self, app: str) -> str:
        if app == "crax.auth":
            module = "crax.auth"
            spl_module = module.split(".")
            auth_path = __import__(module, fromlist=spl_module)
            app_dir = auth_path.__path__[0]
        else:
            app_dir = f"{self.project_url}/{app}"
        if len(self.databases) > 1:
            version_dir = f"{app_dir}/{self.migrations_dir}/{self.db_name}"
        else:
            version_dir = f"{app_dir}/{self.migrations_dir}"
        return version_dir

    def set_database(self, name: str) -> None:
        try:
            table_base = self.databases[name]
            if table_base["driver"] == "mysql":
                driver = "mysql+pymysql"
            else:
                driver = table_base["driver"]
            if driver != "sqlite":
                self.default_connection = (
                    f'{driver}://{table_base["user"]}:'
                    f'{table_base["password"]}@{table_base["host"]}/{table_base["name"]}'
                )
            else:
                self.default_connection = (
                    f'{table_base["driver"]}://{table_base["name"]}'
                )
            self.db_name = name
            os.environ["CRAX_DB_NAME"] = name

        except (IndexError, KeyError) as e:
            raise CraxDataBaseImproperlyConfigured(e)

    def check_config(self) -> Optional[Config]:
        if not os.path.isfile(f"{self.project_url}/{self.config_file}"):
            config = None
        else:
            config = Config(self.config_file)
        return config

    def write_config(self, section: str, var: str, value: str) -> None:
        if self.config:
            config = configparser.ConfigParser()
            config.read(self.config_file)
            config[section][var] = value
            with open(self.config_file, "w") as cf:
                config.write(cf)

    def create_db_map(self) -> None:
        existing_map = self.config.get_main_option("crax_db_map", None)
        if existing_map is None:
            existing_map = {k: None for k in self.databases.keys()}
        else:
            existing_map = json.loads(existing_map)

        for app in self.project_applications:
            meta = get_metadata(app).sorted_tables
            self.db_map.update({app: [x.name for x in meta]})
        existing_map[self.db_name] = self.db_map

        self.write_config("alembic", "crax_db_map", json.dumps(existing_map))

    def create_dependency_map(self) -> typing.Mapping[str, typing.List[set]]:
        dep_map = {x: ([], []) for x in self.applications}
        for app in self.applications:
            for name in resources.contents(app):
                if name == "models.py":
                    _module = import_module(f"{app}.{name[:-3]}")
                    for x in dir(_module):
                        table = getattr(_module, x)
                        if (
                            hasattr(table, "metadata")
                            and hasattr(table, "database")
                            and table.__name__ != "BaseTable"
                        ):
                            dep_map[app][0].extend(
                                [x.name for x in table.metadata.sorted_tables]
                            )
                            dep_map[app][1].extend(
                                [x.name for x in get_metadata(app).sorted_tables]
                            )
        return {x: [set(y[0]), set(y[1])] for x, y in dep_map.items()}

    def check_branch_exists(self, branch: str) -> bool:
        script = ScriptDirectory.from_config(self.config)
        bases = script.get_bases()
        branches = list(chain(*[script.get_revision(x).branch_labels for x in bases]))
        return branch in branches


class MetadataCommands(DataBaseCommands):
    def __init__(self, opts: list, **kwargs) -> None:
        super(MetadataCommands, self).__init__(opts, **kwargs)
        engine = create_engine(self.default_connection, echo=False)
        self.metadata = MetaData(bind=engine)
        self.dependency_map = self.create_dependency_map()
        self.collect_metadata()

    def collect_metadata(self) -> None:
        meta = []
        sorted_applications = sort_applications(
            self.dependency_map, revers=self.args.down
        )
        for app in sorted_applications:
            m = get_metadata(app)
            meta.append(m)
        for m in meta:
            for (table_name, table) in m.tables.items():
                self.metadata._add_table(table_name, table.schema, table)
