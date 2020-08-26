"""
Command to get migrations history, latest migration according to project application.
All revision branches are linked to applications defined in project settings
"""

import os
import sys
from typing import Optional

import typing
from alembic.command import history
from alembic.script import ScriptDirectory

from crax.database.command import DataBaseCommands
from crax.exceptions import CraxMigrationsError

options = [
    (["--database", "-b"], {"type": str, "help": "specify database to run migrations"}),
    (["--apps", "-a"], {"type": str, "help": "specify app", "nargs": "*"},),
    (
        ["--latest", "-l"],
        {"help": "get latest revisions", "action": "store_true", "dest": "latest"},
    ),
    (["--step", "-s"], {"help": "specify step"}),
]


class DBHistory(DataBaseCommands):
    def __init__(self, opts: typing.List[typing.Union[tuple]], **kwargs) -> None:
        super(DBHistory, self).__init__(opts, **kwargs)
        self.kwargs = kwargs

    def get_revision(self, app: str, index_: int) -> Optional[str]:
        script = ScriptDirectory.from_config(self.config)
        rev = script.walk_revisions(
            f"{self.db_name}/{app}@base", f"{self.db_name}/{app}@head"
        )
        revision = next(filter(lambda x: x[0] == index_, enumerate(rev)), None)
        if revision:
            return revision[1]

    def show_history(self) -> None:
        step = self.get_option("step")
        latest = self.get_option("latest")
        dir_exists = os.path.exists(f"{self.project_url}/{self.alembic_dir}")
        if self.config is None or not dir_exists:
            raise CraxMigrationsError(
                "You can not run show history command before migrations not created"
            )

        for app in self.applications:
            if self.check_branch_exists(f"{self.db_name}/{app}"):
                os.environ["CRAX_ONLINE"] = "true"
                os.environ["CRAX_CURRENT"] = app
                top_formatter = (
                    f'{app} history. Database: {self.db_name} \n {"*" * 40} \n'
                )
                bottom_formatter = f'\n {"*" * 40} \n'
                if step is not None:
                    revision = self.get_revision(app, int(step))
                elif latest is True:
                    revision = self.get_revision(app, 0)
                else:
                    revision = None
                    history(self.config, f":{self.db_name}/{app}@head")
                if revision:
                    sys.stdout.write(top_formatter)
                    self.config.print_stdout(revision)
                    sys.stdout.write(bottom_formatter)


if __name__ == "__main__":  # pragma: no cover
    show_history = DBHistory(options).show_history
    show_history()
