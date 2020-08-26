from crax.urls import Route, Url
from .routers import (
    Home,
    Customers,
    CustomersView,
    CustomerDiscountView,
    CustomerDiscounts,
    OrderView,
    ProtectedView,
    APIView,
    Order,
)
from .cart.urls import url_list as cart_urls

url_list = [
    Route(Url("/home"), Home),
    Route(Url("/protected"), ProtectedView),
    Route(urls=(Url("/api/customers", tag="customer")), handler=Customers),
    Route(Url("/api/customer/<customer_id:int>"), handler=CustomersView),
    Route(urls=(Url("/api/discounts", tag="discount")), handler=CustomerDiscounts),
    Route(
        Url(
            r"/api/discount/(?P<discount_id>\d+)/(?:(?P<optional>\w+))?", type="re_path"
        ),
        handler=CustomerDiscountView,
    ),
    Route(Url("/api/orders", tag="order", methods=["GET", "POST"]), handler=Order),
    Route(Url("/api/order/<order_id:int>"), handler=OrderView),
    Route(
        urls=(
            Url("/"),
            Url("/v1/customers"),
            Url("/v1/discounts"),
            Url("/v1/cart"),
            Url("/v1/customer/<customer_id:int>"),
            Url("/v1/discount/<discount_id:int>/<optional:str>/"),
        ),
        handler=APIView,
    ),
] + cart_urls
