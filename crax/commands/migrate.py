"""
Command that applies migrations. Every time you
changes are made, "makemigrations" command should ba ran
and then created migrations have to be applied with this command.
If no tables detected in target database (or some of tables are not present in database)
it will be created. If no changes detected no error will be raised. All above id for
"online mode". If for any reasons migrations should not be processed against target
database, command should be ran in "offline mode" that just creates sql file.
It is the common behaviour of alembic "upgrade" command. Command, launched with
-d flag will work same way with alembic "downgrade".
"""

import json
import os
import sys

import typing
from alembic.command import downgrade, upgrade
from alembic.script import ScriptDirectory
from alembic.util import CommandError

from crax.database import sort_applications
from crax.database.command import DataBaseCommands, OPTIONS
from crax.exceptions import CraxMigrationsError

OPTIONS += [
    (
        ["--sql", "-s"],
        {"help": "generate sql script", "action": "store_true", "dest": "sql"},
    ),
    (
        ["--revision", "-r"],
        {"type": str, "help": "specify revision you want to migrate"},
    ),
]


class Migrate(DataBaseCommands):
    def __init__(
        self, opts: typing.List[typing.Union[tuple]], **kwargs: typing.Any
    ) -> None:
        super(Migrate, self).__init__(opts, **kwargs)
        dir_exists = os.path.exists(f"{self.project_url}/{self.alembic_dir}")
        if self.config is None or not dir_exists:
            raise CraxMigrationsError(
                "You can not run migrate command before migrations not created"
            )

        self.dependency_map = self.create_dependency_map()
        self.script = ScriptDirectory.from_config(self.config)
        self.kwargs = kwargs

    def run_migrations(self) -> None:
        sql = self.get_option("sql")
        down = self.get_option("down")

        sorted_applications = sort_applications(
            self.dependency_map, revers=self.args.down
        )
        for app in sorted_applications:
            if app == "crax.auth" or "migrations" in os.listdir(f"{self.project_url}/{app}"):
                os.environ["CRAX_CURRENT"] = app
                conf_latest = self.config.get_main_option("crax_latest_revisions", None)
                if conf_latest is None:
                    try:
                        rev = self.script.get_revision(f"{self.db_name}/{app}@head")
                        crax_latest_revisions = json.dumps(
                            {f"{self.db_name}/{app}": rev.revision}
                        )
                        self.config.set_main_option(
                            "crax_latest_revisions", crax_latest_revisions
                        )
                    except CommandError:
                        raise CraxMigrationsError(
                            f"No such revision or branch {self.db_name}/{app}"
                        )
                if sql:
                    os.environ["CRAX_SQL_PATH"] = f"{self.create_version_dir(app)}/sql"
                    kwargs = {"sql": True}
                    if "CRAX_ONLINE" in os.environ:
                        del os.environ["CRAX_ONLINE"]
                else:
                    os.environ["CRAX_ONLINE"] = "true"
                    kwargs = {}
                if self.check_branch_exists(f"{self.db_name}/{app}"):
                    if down is True:
                        downgrade(self.config, f"{self.db_name}/{app}@base", **kwargs)
                    else:
                        upgrade(self.config, f"{self.db_name}/{app}@head", **kwargs)
                self.create_db_map()
            else:
                sys.stdout.write(f"No migrations found in {app} application. Skipping.\n")

    def migrate(self) -> None:
        revision = self.get_option("revision")
        sql = self.get_option("sql")
        down = self.get_option("down")
        if revision:
            try:
                rev = self.script.get_revision(revision)
                os.environ["CRAX_CURRENT"] = list(rev.branch_labels)[0].split("/")[1]
                if sql:
                    if "CRAX_ONLINE" in os.environ:
                        del os.environ["CRAX_ONLINE"]
                    if len(self.databases) > 1:
                        sql_path = (
                            f"{self.project_url}/{list(rev.branch_labels)[0].split('/')[1]}/"
                            f"{self.migrations_dir}/{self.db_name}/sql"
                        )
                    else:
                        sql_path = (
                            f"{self.project_url}/{list(rev.branch_labels)[0].split('/')[1]}/"
                            f"{self.migrations_dir}/sql"
                        )
                    os.environ["CRAX_SQL_PATH"] = sql_path
                    if down is True:
                        downgrade(self.config, revision, sql=True)
                    else:
                        upgrade(self.config, revision, sql=True)
                else:
                    os.environ["CRAX_ONLINE"] = "true"
                    if down is True:
                        downgrade(self.config, revision)
                    else:
                        upgrade(self.config, revision)
            except AttributeError:
                raise CraxMigrationsError("Failed to get revision")
        else:
            self.run_migrations()
        self.write_config("alembic", "crax_migrated", "migrated")


if __name__ == "__main__":  # pragma: no cover
    migrate = Migrate(OPTIONS).migrate
    migrate()
