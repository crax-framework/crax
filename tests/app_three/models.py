from crax.database.model import BaseTable
import sqlalchemy as sa
from tests.app_one.models import CustomerB, Vendor


class Orders(BaseTable):
    # database = 'custom'
    staff = sa.Column(sa.String(length=100), nullable=False)
    price = sa.Column(sa.Integer, nullable=False)
    customer_id = sa.Column(sa.Integer, sa.ForeignKey(CustomerB.id))
    vendor_id = sa.Column(sa.Integer, sa.ForeignKey(Vendor.id))
