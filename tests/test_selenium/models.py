import sqlalchemy as sa
from crax.auth.models import User
from crax.database.model import BaseTable


class BaseDiscount(BaseTable):
    name = sa.Column(sa.String(length=100), nullable=False)
    percent = sa.Column(sa.Integer, nullable=False)

    class Meta:
        abstract = True


class CustomerDiscount(BaseDiscount):
    pass


class VendorDiscount(BaseDiscount):
    pass


class UserInfo(BaseTable):
    age = sa.Column(sa.Integer(), nullable=True)


class BaseUser(User):
    bio = sa.Column(sa.String(length=100), nullable=False)

    class Meta:
        abstract = True


class CustomerA(BaseUser, UserInfo):
    ave_bill = sa.Column(sa.Integer)


class CustomerB(BaseUser, UserInfo):
    discount = sa.Column(sa.Integer)
    customer_discount_id = sa.Column(sa.Integer, sa.ForeignKey(CustomerDiscount.id))

    class Meta:
        order_by = "username"


class Vendor(BaseUser, UserInfo):
    vendor_discount_id = sa.Column(sa.Integer, sa.ForeignKey(VendorDiscount.id))


class Orders(BaseTable):
    staff = sa.Column(sa.String(length=100), nullable=False)
    price = sa.Column(sa.Integer, nullable=False)
    customer_id = sa.Column(sa.Integer, sa.ForeignKey(CustomerB.id), nullable=True)
    vendor_id = sa.Column(sa.Integer, sa.ForeignKey(Vendor.id), nullable=True)
