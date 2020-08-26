from dataclasses import dataclass
import typing

from databases import Database

from crax.exceptions import CraxDataBaseImproperlyConfigured

try:
    from sqlalchemy import MetaData, Table, UniqueConstraint, Column, Integer, select
except ImportError:  # pragma: no cover
    raise

from crax.utils import get_settings


@dataclass
class Connection:
    pool: typing.Any = None
    driver: str = None
    main: bool = True


async def create_connections() -> dict:
    configuration = get_settings()
    connections = {}
    if not hasattr(configuration, "DATABASES"):
        raise CraxDataBaseImproperlyConfigured(
            "Improperly configured project settings. "
            'Missed required parameter "DATABASES"'
        )
    databases = configuration.DATABASES
    if not isinstance(databases, dict):
        raise CraxDataBaseImproperlyConfigured(
            "Improperly configured project settings."
            " DATABASES parameter should be a dict"
        )

    elif "default" not in databases:
        raise CraxDataBaseImproperlyConfigured(
            "Improperly configured project settings. "
            'DATABASES dictionary should contain "default" database'
        )
    for table in configuration.DATABASES:
        table_base = configuration.DATABASES[table]
        driver = table_base["driver"]

        if "options" in table_base:
            connection_options = table_base["options"]
        else:
            connection_options = {}
        if table_base["driver"] != 'sqlite':
            port = table_base.get('port')
            if port:
                connection_string = (
                    f'{table_base["driver"]}://{table_base["user"]}:'
                    f'{table_base["password"]}@{table_base["host"]}:{port}/{table_base["name"]}'
                )
            else:
                connection_string = (
                    f'{table_base["driver"]}://{table_base["user"]}:'
                    f'{table_base["password"]}@{table_base["host"]}/{table_base["name"]}'
                )
        else:
            connection_string = (
                f'{table_base["driver"]}://{table_base["name"]}'
            )
        connection = Database(connection_string, **connection_options)
        await connection.connect()

        connection = Connection(pool=connection, driver=driver)
        connections[table] = connection

    return connections


async def close_pool(connections):
    if connections:
        for connection in connections:
            await connection.pool.disconnect()
