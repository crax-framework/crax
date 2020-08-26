"""
Command that helps to create migrations.
At the first launch "makemigrations" command creates
alembic working directory and alembic.ini file if not exist.
Creates revision branches according to applications that defined in
project settings. Creates initial migrations. All next times it
checks whether all previous migrations are applied and creates if it is.

"""
import json
import os
import shutil
import sys
from typing import Optional

import typing
from alembic.command import init, revision, stamp
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.util import CommandError
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.orm import sessionmaker

from crax.database import env
from crax.database.command import DataBaseCommands, OPTIONS

OPTIONS += [
    (["--message", "-m"], {"type": str, "help": "specify revision message"}),
]


class MakeMigrations(DataBaseCommands):
    def create_model_branch(self, apps: typing.List[typing.Union[str]]) -> None:
        for app in apps:
            os.environ["CRAX_CURRENT"] = app
            version_path = self.create_version_dir(app)
            try:
                self.config.set_main_option("version_locations", version_path)
                revision(
                    self.config,
                    branch_label=f"{self.db_name}/{app}",
                    autogenerate=True,
                    version_path=version_path,
                    message=self.args.message,
                )
            except CommandError as e:
                sys.stderr.write(f"Failed to create initial migrations: {e} \n")
                break

    def get_revisions(self) -> dict:
        revisions = {}
        for app in self.applications:
            alembic_script = ScriptDirectory.from_config(self.config)
            try:
                rev = alembic_script.get_revisions(f"{self.db_name}/{app}@head")
                if rev:
                    label = list(rev[0].branch_labels)[0]
                    revisions.update({label: [rev[0].revision, rev[0].down_revision]})
            except (CommandError, KeyError):
                pass
        return revisions

    def wipe_existing_versions(self) -> None:
        engine = create_engine(self.default_connection, echo=False)
        session = sessionmaker()
        _session = session(bind=engine)
        try:
            _session.execute("delete from alembic_version")
            _session.commit()
        except (ProgrammingError, OperationalError):
            sys.stdout.write(
                "Failed to delete alembic versions. If you had an errors, please check it out. \n"
            )

    def check_migrations_exist(self, app: str) -> Optional[bool]:
        if app != "crax.auth":
            app_dir = f"{self.project_url}/{app}"
        else:
            module = "crax.auth"
            spl_module = module.split(".")
            auth_path = __import__(module, fromlist=spl_module)
            app_dir = auth_path.__path__[0]
        if "models.py" in os.listdir(app_dir):
            if len(self.databases) > 1:
                try:
                    app_content = os.listdir(f"{app_dir}/{self.migrations_dir}")
                    check_path = self.db_name
                except FileNotFoundError:
                    return False
            else:
                try:
                    app_content = os.listdir(app_dir)
                    check_path = self.migrations_dir
                except FileNotFoundError:  # pragma: no cover
                    return False
            if check_path in app_content:
                return True
            else:
                return False

    def delete_crax_migrations(self, module: str) -> None:
        spl_module = module.split(".")
        auth_path = __import__(module, fromlist=spl_module)
        path = f"{auth_path.__path__[0]}/{self.migrations_dir}"
        if os.path.exists(path):
            shutil.rmtree(path)

    def check_deleted(self) -> None:
        dir_exists = os.path.exists(f"{self.project_url}/{self.alembic_dir}")
        if self.config is not None and dir_exists:
            if len(self.databases) > 1:
                migration_dirs = [
                    f"{self.project_url}/{app}/{self.migrations_dir}/{self.db_name}"
                    for app in self.applications
                    if app != "crax.auth"
                ]
            else:
                migration_dirs = [
                    f"{self.project_url}/{app}/{self.migrations_dir}"
                    for app in self.applications
                    if app != "crax.auth"
                ]

            engine = create_engine(self.default_connection, echo=False)
            session = sessionmaker()
            _session = session(bind=engine)
            try:
                existing_versions = [
                    x for x in _session.execute("select * from alembic_version")
                ]
                not_existing_dirs = any([not os.path.exists(x) for x in migration_dirs])
                if existing_versions and not_existing_dirs:
                    self.delete_crax_migrations("crax.auth")
                    if os.path.isfile(f"{self.project_url}/alembic.ini"):
                        self.write_config("alembic", "crax_migrated", "migrated")
                    self.wipe_existing_versions()
            except (ProgrammingError, OperationalError):
                sys.stdout.write(
                    "Failed to get alembic versions. If you had an errors, please check it out. \n"
                )

    def make_migrations(self) -> None:
        os.environ["CRAX_ONLINE"] = "true"
        dir_exists = os.path.exists(f"{self.project_url}/{self.alembic_dir}")

        if self.config is None or not dir_exists:
            if os.path.isfile(f"{self.project_url}/alembic.ini"):
                os.remove(f"{self.project_url}/alembic.ini")
            if os.path.exists(f"{self.project_url}/{self.alembic_dir}"):
                shutil.rmtree(f"{self.project_url}/{self.alembic_dir}")

            self.delete_crax_migrations("crax.auth")
            self.wipe_existing_versions()
            self.config = Config("alembic.ini")
            init(self.config, self.alembic_dir, package=True)
            shutil.copy(env.__file__, f"{self.project_url}/{self.alembic_dir}/env.py")
            self.create_model_branch(self.applications)
            self.create_db_map()

        else:
            self.check_deleted()
            migrated = self.config.get_main_option("crax_migrated")
            if migrated == "not migrated":
                sys.stderr.write(
                    "You have unapplied migrations. Please run migrate command first. \n"
                )
                sys.exit(1)
            db_map = self.config.get_main_option("crax_db_map")

            if db_map:
                try:
                    map_dict = json.loads(self.config.get_main_option("crax_db_map"))
                    current_db_map = map_dict[self.db_name]
                    if isinstance(current_db_map, dict):
                        os.environ["CRAX_DB_TABLES"] = json.dumps(current_db_map)
                except KeyError:
                    pass
            for app in self.applications:
                os.environ["CRAX_CURRENT"] = app
                version_dir = self.create_version_dir(app)
                exists = self.check_migrations_exist(app)
                message = self.get_option("message")
                if exists is not None:
                    if exists is False:
                        revision(
                            self.config,
                            branch_label=f"{self.db_name}/{app}",
                            head="base",
                            version_path=version_dir,
                            autogenerate=True,
                            message=message,
                        )
                        if self.check_branch_exists(f"{self.db_name}/{app}"):
                            revisions = self.get_revisions()
                            if revisions:
                                try:
                                    stamp(
                                        self.config,
                                        revisions[f"{self.db_name}/{app}"][0],
                                    )
                                except (KeyError, IndexError):
                                    stamp(self.config, f"{self.db_name}/{app}@head")

                    else:
                        revision(
                            self.config,
                            head=f"{self.db_name}/{app}@head",
                            version_path=version_dir,
                            autogenerate=True,
                            message=message,
                        )
                        if self.check_branch_exists(f"{self.db_name}/{app}"):
                            revisions = self.get_revisions()
                            if revisions:
                                try:
                                    stamp(
                                        self.config,
                                        revisions[f"{self.db_name}/{app}"][0],
                                    )
                                except (KeyError, IndexError):
                                    stamp(self.config, f"{self.db_name}/{app}@head")
                else:
                    sys.stdout.write(
                        f"No models found in application {app}. Skipping. \n"
                    )
            revisions = self.get_revisions()
            for app in self.applications:
                if revisions:
                    if self.check_branch_exists(f"{self.db_name}/{app}"):
                        try:
                            conf_latest = self.config.get_main_option(
                                "crax_latest_revisions", None
                            )
                            if conf_latest:
                                latest = json.loads(conf_latest)
                                app_latest = latest[f"{self.db_name}/{app}"]
                                if revisions[f"{self.db_name}/{app}"][0] != app_latest:
                                    if (
                                        revisions[f"{self.db_name}/{app}"][1]
                                        is not None
                                    ):
                                        stamp(
                                            self.config,
                                            revisions[f"{self.db_name}/{app}"][1],
                                        )
                                    else:
                                        stamp(self.config, f"{self.db_name}/{app}@base")
                        except (KeyError, IndexError, CommandError) as e:
                            branch = f"{self.db_name}/{app}"
                            if branch in revisions:
                                stamp(self.config, f"{self.db_name}/{app}@base")
                            else:
                                sys.stderr.write(
                                    f"Failed to stamp: {e}. Please check it out. \n"
                                )
        self.write_config("alembic", "crax_migrated", "not migrated")


if __name__ == "__main__":  # pragma: no cover
    make_migrations = MakeMigrations(OPTIONS).make_migrations
    make_migrations()
