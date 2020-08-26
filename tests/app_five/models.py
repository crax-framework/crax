import sqlalchemy as sa
from crax.auth.models import User
from tests.app_two.models import CustomerDiscount, VendorDiscount


class BaseUser(User):
    database = "custom"
    bio = sa.Column(sa.String(length=100), nullable=False)

    class Meta:
        abstract = True


class CustomerA(BaseUser):
    database = "custom"
    ave_bill = sa.Column(sa.Integer)


class CustomerB(BaseUser):
    database = "custom"
    discount = sa.Column(sa.Integer)
    customer_discount_id = sa.Column(sa.Integer, sa.ForeignKey(CustomerDiscount.id))


class Vendor(BaseUser):
    database = "custom"
    vendor_discount_id = sa.Column(sa.Integer, sa.ForeignKey(VendorDiscount.id))
