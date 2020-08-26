import json

from sqlalchemy import select

from crax.response_types import JSONResponse
from crax.views import TemplateView, BaseView
from .models import CustomerB, CustomerDiscount, Orders


class Home(TemplateView):
    template = "home.html"
    methods = ["GET", "POST", "PATCH"]
    enable_csrf = False

    async def post(self):
        await self.request.files["pic"].save()
        response = JSONResponse(self.request, self.request.post)
        return response


class ProtectedView(TemplateView):
    template = "home.html"
    methods = ["GET", "POST", "PATCH"]

    async def post(self):
        response = JSONResponse(self.request, self.request.post)
        return response


class APIView(TemplateView):
    template = "index.html"


class Customers(BaseView):
    """
        Customers view
    """

    methods = ["GET", "POST"]
    enable_csrf = False

    async def get(self):
        """Get list of customers"""
        self.context = await CustomerB.query.all()
        response = JSONResponse(self.request, self.context)
        return response

    async def post(self):
        """
        Create new customer
        :return: 201 {"success": "Created"}
        :return: 400 Bad Request
        :par bulk: true
        :par first_name: str required
        :par username: str
        :par password: str
        :par bio: str
        """

        if self.request.post:
            # This for compatibility with swagger and vue both
            if isinstance(self.request.post, str):
                self.request.post = json.loads(self.request.post)
            if "users" in self.request.post:
                data = self.request.post["users"]
            else:
                data = self.request.post
            if isinstance(data, str):
                data = json.loads(data)
            try:
                await CustomerB.query.bulk_insert(values=data)
                self.context = {"success": "Created"}
            except Exception as e:
                self.context = {"error": str(e)}
        else:
            self.context = {"error": "No data for creation given"}
        response = JSONResponse(self.request, self.context)
        return response


class CustomersView(BaseView):
    """
        Customers view
    """

    methods = ["GET", "PATCH", "DELETE"]
    enable_csrf = False

    async def get(self):
        """
        get customer by ID
        """
        query = select([CustomerB.c.id, CustomerDiscount.c.name]).where(
            CustomerB.c.id == int(self.request.params["customer_id"])
        )
        self.context = await CustomerB.query.fetch_one(query=query)
        response = JSONResponse(self.request, self.context)
        return response

    async def patch(self):
        """
        Update customer
        """
        CustomerB.query.execute(
            CustomerB.table.update()
            .where(CustomerB.c.id == self.request.params["customer_id"])
            .values({"first_name": "Fred"})
        )
        response = JSONResponse(self.request, self.context)
        return response

    async def delete(self):
        """
        Delete customer
        """
        response = JSONResponse(self.request, self.context)
        return response


class CustomerDiscounts(BaseView):
    methods = ["GET", "POST"]
    enable_csrf = False

    async def get(self):
        """
        Get customer's discounts list
        """
        if not self.request.params:
            self.context = await CustomerDiscount.query.all()
        response = JSONResponse(self.request, self.context)
        return response

    async def post(self):
        """
            Create new discount
            :par name: str required
            :par percent: int
            :content_type: application/x-www-form-urlencoded
        """
        if isinstance(self.request.post, str):
            self.request.post = json.loads(self.request.post)
        if "discount" in self.request.post:
            data = self.request.post["discount"]
        else:
            data = self.request.post
        if isinstance(data, str):
            data = json.loads(data)
        await CustomerDiscount.query.insert(values=data)
        self.context = {"success": "Created"}
        response = JSONResponse(self.request, self.context)
        return response


class CustomerDiscountView(BaseView):
    """
        Customer's discounts
    """

    methods = ["GET", "PATCH", "DELETE"]
    enable_csrf = False

    async def get(self):
        """
        Get customer's discount by ID
        """
        query = select([CustomerDiscount.c.name, CustomerDiscount.c.percent]).where(
            CustomerDiscount.c.id == self.request.params["discount_id"]
        )
        self.context = await CustomerDiscount.query.fetch_one(query=query)
        response = JSONResponse(self.request, self.context)
        return response

    async def patch(self):
        """
        Update customer's discount
        """
        if isinstance(self.request.post, str):
            self.request.post = json.loads(self.request.post)
        await CustomerDiscount.query.execute(
            query=CustomerDiscount.table.update()
            .where(CustomerDiscount.c.id == int(self.request.params["discount_id"]))
            .values(json.loads(self.request.post["discount"]))
        )
        response = JSONResponse(self.request, self.context)
        return response

    async def delete(self):
        """
        Delete discount
        :return:
        """
        await CustomerDiscount.query.execute(
            query=CustomerDiscount.table.delete().where(
                CustomerDiscount.c.id == int(self.request.params["discount_id"])
            )
        )
        response = JSONResponse(self.request, self.context)
        return response


class Order(BaseView):
    methods = ["GET", "POST"]

    async def get(self):
        self.context = await Orders.query.all()
        response = JSONResponse(self.request, self.context)
        return response

    async def post(self):
        if isinstance(self.request.post, str):
            self.request.post = json.loads(self.request.post)
        if "order" in self.request.post:
            data = self.request.post["order"]
        else:
            data = self.request.post
        if isinstance(data, str):
            data = json.loads(data)
        await Orders.query.insert(values=data)

        self.context = {"success": "Created"}
        response = JSONResponse(self.request, self.context)
        return response


class OrderView(BaseView):
    methods = ["GET", "DELETE"]

    async def get(self):
        self.context = await Orders.query.fetch_one(
            query=Orders.table.select().where(
                Orders.c.id == int(self.request.params["order_id"])
            )
        )
        response = JSONResponse(self.request, self.context)
        return response

    async def delete(self):
        query = Orders.table.delete().where(
            Orders.c.id == int(self.request.params["order_id"])
        )
        self.context = await CustomerB.query.execute(query=query)
        response = JSONResponse(self.request, self.context)
        return response
