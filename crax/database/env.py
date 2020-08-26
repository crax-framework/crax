"""
Alembic environment file. This file will be placed into the Alembic working
directory while creating initial migrations and alembic infrastructure
"""
import configparser
import json
import os
from itertools import chain
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config

from crax.database import get_metadata


def run_migrations_online() -> None:  # pragma: no cover
    # This file will never be called, but copy of this file will.
    # Migrations won't work without it and it is assumed that it is tested
    # if migrations work properly
    try:
        config = context.config
        fileConfig(config.config_file_name)
    except AttributeError:
        config = None

    if config:
        current_app = os.environ["CRAX_CURRENT"]
        current_db = os.environ["CRAX_DB_NAME"]
        target_metadata = get_metadata(os.environ["CRAX_CURRENT"])

        def filter_actual(*args):
            get_map = os.environ.get("CRAX_DB_TABLES", None)
            control_metadata = get_metadata(current_app)
            meta_tables = [x.name for x in control_metadata.sorted_tables]
            if get_map:
                db_map = json.loads(get_map)
                tables = list(
                    chain(*[v for k, v in db_map.items() if k in current_app])
                )
                check = tables if len(tables) > len(meta_tables) else meta_tables
                res = args[0] in check
            else:
                res = args[0] in meta_tables
            return res

        def process_revision_directives(*args):
            script = args[2][0]
            if script.upgrade_ops.is_empty():
                args[2][:] = []

        config.set_main_option("sqlalchemy.url", os.environ["CRAX_DB_CONNECTION"])
        engine = engine_from_config(
            config.get_section(config.config_ini_section), prefix="sqlalchemy."
        )
        online = os.environ.get("CRAX_ONLINE", None)
        with engine.connect() as connection:
            if online:
                context.configure(
                    render_as_batch=True,
                    include_symbol=filter_actual,
                    compare_type=True,
                    process_revision_directives=process_revision_directives,
                    connection=connection,
                    target_metadata=target_metadata,
                )
                if context.get_context().opts["fn"].__name__ in [
                    "upgrade",
                    "downgrade",
                ]:
                    try:
                        end_version = context.get_revision_argument()
                        conf_latest = config.get_main_option(
                            "crax_latest_revisions", None
                        )
                        if conf_latest is not None:
                            latest = json.loads(conf_latest)
                            latest.update({f"{current_db}/{current_app}": end_version})
                            latest = json.dumps(latest)
                        else:
                            latest = json.dumps(
                                {f"{current_db}/{current_app}": end_version}
                            )
                        conf = configparser.ConfigParser()
                        conf.read(config.config_file_name)
                        conf["alembic"]["crax_latest_revisions"] = latest
                        config.set_main_option("crax_latest_revisions", latest)
                        with open(config.config_file_name, "w") as cf:
                            conf.write(cf)
                    except KeyError:
                        pass
                context.run_migrations()
            else:
                path = os.environ.get("CRAX_SQL_PATH", None)
                _file = f"{context.get_revision_argument()}_.sql"
                if path and _file:
                    if not os.path.exists(path):
                        os.mkdir(path)
                    if os.path.isfile(f"{path}/{_file}"):
                        os.remove(f"{path}/{_file}")
                    context.configure(
                        connection=connection,
                        transactional_ddl=False,
                        output_buffer=open(f"{path}/{_file}", "a"),
                    )
                    context.run_migrations()


run_migrations_online()
