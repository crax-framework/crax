"""
Base classes for crax models and queries. Nothing more than very thin wrapper around
wellknown packages "SQLAlchemy Core Table" and "Databases" written by "Encode team".
Thank you, guys, for your great job.
"""
import re
from typing import Optional

import typing

from databases import Database

from crax.database.connection import Connection

from crax.data_types import Model, DBQuery, Selectable
from crax.exceptions import CraxDataBaseImproperlyConfigured

try:
    from sqlalchemy import MetaData, Table, UniqueConstraint, Column, Integer, select, text, and_
except ImportError:  # pragma: no cover
    raise

from crax.utils import get_settings


def to_snake_case(cls: Model) -> Optional[str]:
    if hasattr(cls, "__name__"):
        _str = cls.__name__[0].upper() + cls.__name__[1:]
        if _str[-1].isupper():
            name = _str[:-1]
        else:
            name = _str
        c = [x for x in re.split(r"[A-Z]", name) if x]
        f = [x.lower() for x in re.split(r"[a-z]", name) if x]
        table_name = "_".join(["".join(x) for x in zip(f, c)])
        if len(_str) > len(name):
            table_name = f"{table_name}_{_str[-1].lower()}"
        return table_name


class Query:
    def __init__(self, cls: Model) -> None:
        self._method = None
        self.cls = cls
        self.driver = None

    async def get_connection_pool(self):
        configuration = get_settings()
        connections = configuration.app.db_connections
        main = True
        if not connections:
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
            try:
                databases = configuration.DATABASES
                table_base = databases[self.cls.database]
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
                connection = Database(connection_string)
                connection_pool = connection
                self.driver = table_base["driver"]
                main = False
            except (KeyError, RuntimeError):
                raise CraxDataBaseImproperlyConfigured(
                    f"No database connection found. Check your configuration."
                )
        else:
            try:
                connection_pool = connections[self.cls.database].pool
                self.driver = connections[self.cls.database].driver
            except (KeyError, RuntimeError):
                raise CraxDataBaseImproperlyConfigured(
                    f"No database connection found. Check your configuration."
                )
        connection = Connection(
            pool=connection_pool,
            driver=self.driver,
            main=main)
        return connection

    async def process_method(self, connection, **kwargs):
        if hasattr(connection, self._method):
            res = await getattr(connection, self._method)(**kwargs)
        else:
            raise AttributeError(
                f"{self.cls.__name__} model has no method {self._method}"
            )
        return res

    async def __call__(
        self, *args: Optional[tuple], **kwargs: typing.Mapping[str, typing.Any]
    ) -> typing.Optional[typing.Any]:

        connection = await self.get_connection_pool()
        if connection.main is False:
            async with connection.pool as conn:
                res = await self.process_method(conn, **kwargs)
        else:
            res = await self.process_method(connection.pool, **kwargs)
        return self.prepare_result(res)

    def __getattr__(
        self,
        method: str,
        *args: Optional[tuple],
        **kwargs: typing.Mapping[str, typing.Any],
    ) -> DBQuery:
        self._method = method
        return self

    def prepare_result(self, result):
        res = result
        if result and not isinstance(result, (int, bool)):
            if self.driver == "mysql" or self.driver == "sqlite":
                if isinstance(result, list):
                    res = [dict(x) for x in result]
                else:
                    res = dict(result)
            if self.driver == "postgresql":
                if isinstance(result, list):
                    res = [dict(x._row) for x in result]
                else:
                    res = dict(result._row)
        return res

    def get_column(self, column_name: str) -> Optional[Column]:
        columns = [x for x in self.cls.table.columns if x.name == column_name]
        if columns:
            column = columns[0]
        else:
            raise KeyError(
                f'Model {self.cls.__name__} has no column named "{column_name}"'
            )
        return column

    def prepare_query(self) -> Selectable:
        if self.cls.ordering is not None:
            column = self.get_column(self.cls.ordering)
            assert callable(select)
            query = select([self.cls.table]).order_by(column.asc())
        else:
            assert callable(select)
            query = select([self.cls.table])
        return query

    async def all(self) -> typing.List[typing.Mapping]:
        query = self.prepare_query()
        connection = await self.get_connection_pool()
        if connection.main is False:
            async with connection.pool as conn:
                res = await conn.fetch_all(query=query)
        else:
            res = await connection.pool.fetch_all(query=query)
        return self.prepare_result(res)

    async def first(self) -> typing.Optional[typing.Mapping]:
        query = self.prepare_query()
        connection = await self.get_connection_pool()
        if connection.main is False:
            async with connection.pool as conn:
                res = await conn.fetch_one(query=query)
        else:
            res = await connection.pool.fetch_one(query=query)
        return self.prepare_result(res)

    async def last(self) -> typing.Optional[typing.Mapping]:
        constraints = list(self.cls.table.primary_key)
        if self.cls.ordering is not None:
            column = self.get_column(self.cls.ordering)
        else:
            column = list(constraints)[0]
        assert callable(select)
        query = select([self.cls.table]).order_by(column.desc())
        connection = await self.get_connection_pool()
        if connection.main is False:
            async with connection.pool as conn:
                res = await conn.fetch_one(query=query)
        else:
            res = await connection.pool.fetch_one(query=query)
        return self.prepare_result(res)

    async def insert(self, **kwargs: Optional[dict]) -> None:
        query = self.cls.table.insert()
        connection = await self.get_connection_pool()
        if connection.main is False:
            async with connection.pool as conn:
                await conn.execute(query=query, values=kwargs["values"])
        else:
            await connection.pool.execute(query=query, values=kwargs["values"])

    async def bulk_insert(
        self, **kwargs: Optional[typing.List[Optional[dict]]]
    ) -> None:
        connection = await self.get_connection_pool()
        if connection.main is False:
            async with connection.pool as conn:
                await conn.execute_many(
                    query=self.cls.table.insert(), values=kwargs["values"]
                )
        else:
            await connection.pool.execute_many(
                query=self.cls.table.insert(), values=kwargs["values"]
            )


class CraxTableMeta(type):
    def __new__(
        mcs, name: str, bases: Optional[typing.Any], attrs: typing.Dict[str, typing.Any]
    ) -> type:
        mcs.fields = []
        mcs.constraints = []
        mcs.no_magics = {}
        mcs.database = "default"
        mcs.ordering = None
        for key, value in attrs.items():
            if isinstance(value, Column):
                value.name = key
                mcs.fields.append(value)
            elif isinstance(value, UniqueConstraint):
                mcs.constraints.append(value)

        return super(CraxTableMeta, mcs).__new__(mcs, name, bases, attrs)

    def __init__(
        cls, name: str, bases: Optional[typing.Any], attrs: typing.Dict[str, typing.Any]
    ) -> None:
        primary = True
        abstract = False

        if "database" in attrs:
            cls.database = attrs["database"]
        else:
            cls.database = "default"

        if "Meta" in attrs:
            cls._meta = attrs["Meta"]
        else:
            cls._meta = None

        if cls._meta:
            cls.no_magics.update(
                {
                    x: y
                    for x, y in vars(cls._meta).items()
                    if not re.match(r"__\w+__", x)
                }
            )
            cls.ordering = cls.no_magics.pop("order_by", None)
            if "abstract" in cls.no_magics:
                del cls.no_magics["abstract"]
            elif "primary" in cls.no_magics:
                del cls.no_magics["primary"]
        table = Table(cls.create_name(attrs), MetaData(), **cls.no_magics)
        if cls.fields:
            for field in cls.fields:
                field.table = table
                if field.name not in [x.name for x in table.columns]:
                    table.append_column(field)

        if cls._meta and hasattr(cls._meta, "abstract") and cls._meta.abstract is True:
            abstract = True
        elif cls._meta and hasattr(cls._meta, "primary") and cls._meta.primary is False:
            primary = False

        if primary is True and cls.__name__ != "BaseTable":
            id_ = Column("id", Integer, primary_key=True, autoincrement=True)
            table.append_column(id_)
            cls.id = id_

        if cls.constraints:
            for cons in cls.constraints:
                table.append_constraint(cons)
        if abstract is False:
            cls.query = Query(cls)
            cls.metadata = table.metadata
        else:
            cls.metadata = MetaData()
        base_columns = [x for c in bases for x in c.table.columns]
        for column in base_columns:
            column_dict = column.__dict__
            new_column = cls.create_column(column_dict, table)
            table.append_column(new_column)
        cls.table = table
        super(CraxTableMeta, cls).__init__(name, bases, attrs)

    def create_name(cls, attrs) -> typing.Union[str, typing.Callable]:
        if "table_name" in attrs and attrs["table_name"] is not None:
            name = attrs["table_name"]
        else:
            name = to_snake_case(cls)
        return name

    def __getattribute__(self, item):
        if item == "c":
            getter = self.table.__getattribute__(item)
            return getter
        return object.__getattribute__(self, item)

    def __getattr__(self, method: str, *args: Optional[tuple]) -> typing.Callable:
        self._method = method
        return self._compile

    def _compile(self, *args: Optional[tuple]) -> Optional[typing.Callable]:
        if hasattr(self.table, self._method):
            method = getattr(self.table, self._method)
            return method(*args)
        else:
            raise AttributeError(f"{self.__name__} has no attribute {self._method}")

    @staticmethod
    def create_column(column_dict, table):
        name = column_dict["name"]
        type_ = column_dict["type"]
        available_attrs = [
            "autoincrement",
            "default",
            "doc",
            "key",
            "index",
            "info",
            "nullable",
            "onupdate",
            "primary_key",
            "server_default",
            "server_onupdate",
            "quote",
            "unique",
            "system",
            "comment",
        ]
        column_extras = {k: v for k, v in column_dict.items() if k in available_attrs}
        column = Column(name, type_, **column_extras)
        column.constraints = column_dict["constraints"]
        column.foreign_keys = column_dict["foreign_keys"]
        column.is_literal = column_dict["is_literal"]
        column.table = table
        return column


class BaseTable(metaclass=CraxTableMeta):
    pass
