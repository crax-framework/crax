import sqlalchemy as sa
from crax.auth.models import User
from tests.app_two.models import CustomerDiscount, VendorDiscount


class BaseUser(User):
    bio = sa.Column(sa.String(length=100), nullable=False)
    # age = sa.Column(sa.Integer(), nullable=True)

    class Meta:
        abstract = True


class CustomerA(BaseUser):
    ave_bill = sa.Column(sa.Integer)


class CustomerB(BaseUser):
    discount = sa.Column(sa.Integer)
    customer_discount_id = sa.Column(sa.Integer, sa.ForeignKey(CustomerDiscount.id))

    class Meta:
        order_by = "username"


class Vendor(BaseUser):
    vendor_discount_id = sa.Column(sa.Integer, sa.ForeignKey(VendorDiscount.id))
