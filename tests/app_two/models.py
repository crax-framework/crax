from crax.database.model import BaseTable
import sqlalchemy as sa


class BaseDiscount(BaseTable):
    # database = 'custom'
    name = sa.Column(sa.String(length=100), nullable=False)
    percent = sa.Column(sa.Integer, nullable=False)
    # start_date = sa.Column(sa.DateTime(), nullable=True)

    class Meta:
        abstract = True


class CustomerDiscount(BaseDiscount):
    # database = 'custom'
    pass


class VendorDiscount(BaseDiscount):
    # database = 'custom'
    pass
