from crax.urls import Route, Url
from .routers import Cart

url_list = [
    Route(Url("/api/cart"), Cart),
]
