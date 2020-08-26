import sqlalchemy as sa
from crax.database.model import BaseTable


class Customer(BaseTable):
    database = "users"
    bio = sa.Column(sa.String(length=100))
