import os
import sys
from importlib import import_module, resources
from itertools import chain
from typing import Optional

import typing

try:
    from sqlalchemy import MetaData
except ImportError:  # pragma: no cover
    MetaData = None

sys.path = ["", ".."] + sys.path[1:]


def get_metadata(app: str) -> Optional[MetaData]:
    meta = []
    control = []
    if callable(MetaData):
        metadata = MetaData()

        for name in resources.contents(app):
            if name == "models.py":
                _module = import_module(f"{app}.{name[:-3]}")
                for model in dir(_module):
                    table = getattr(_module, model)
                    if hasattr(table, "metadata") and hasattr(table, "database"):
                        table_module = getattr(table, "__module__", None)
                        if (
                            table_module == _module.__name__
                            and table.database == os.environ["CRAX_DB_NAME"]
                        ):
                            meta.append(table)
                            control.append(table.table.name)

                for base in meta:
                    for (table_name, table) in base.metadata.tables.items():
                        if table_name in control:
                            metadata._add_table(table_name, table.schema, table)
        return metadata


def sort_applications(
    table_map: typing.Mapping[str, typing.List[set]], revers=False
) -> typing.List[str]:
    def get_index(lst, elem):
        for x in lst:
            if x == elem:
                return lst.index(x)

    p = []
    c = {x: [] for x in table_map.keys()}
    for x, y in table_map.items():
        diff = set.difference(y[0], y[1])
        if diff:
            for k, v in table_map.items():
                if set.intersection(diff, v[1]):
                    c[k].append(x)
    for k, v in c.items():
        for i in c.keys():
            if i in v:
                if k not in p:
                    p.append(k)
                ind = get_index(p, k)
                if i in p:
                    p.remove(i)
                p.insert(ind + 1, i)
            else:
                if i not in p:
                    p.append(i)
    res = list(chain([x for x in p if c[x]], [x for x in p if not c[x]]))
    if revers is True:
        return res[::-1]
    return res
