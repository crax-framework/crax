from crax.views import TemplateView, JSONView


class TestGetParams(TemplateView):
    template = "test_params.html"
    methods = ["GET"]

    async def get(self):
        params = self.request.params
        query = self.request.query
        self.context = {"query": query, "params": params}


class TestMissedTemplate(TemplateView):
    methods = ["GET"]


class TestNotFoundTemplate(TemplateView):
    template = "not_found_template"
    methods = ["GET"]


class TestInnerTemplateExceptions(TemplateView):
    template = "not_found_template"
    methods = ["GET"]


class TestGetParamsRegex(TemplateView):
    template = "test_params.html"
    methods = ["GET", "POST"]

    async def get(self):
        params = self.request.params
        query = self.request.query
        self.context = {"query": query, "params": params}


class TestJSONView(JSONView):
    methods = ["GET"]

    async def get(self):
        self.context = {"data": "Test_data"}


class TestSendCookiesBack(JSONView):
    methods = ["GET"]

    async def get(self):
        self.context = {"data": self.request.headers["cookie"]}


class TestSetCookies(JSONView):
    methods = ["GET"]

    async def create_context(self):
        self.context = {"data": "Test_data"}
        response = await super(TestSetCookies, self).create_context()
        response.set_cookies(
            "test_cookie", "test_cookie_value", {"path": "/", "httponly": "true"}
        )
        return response


class TestEmptyMethods(TemplateView):
    template = "index.html"
    methods = []


class TestMasquerade(TemplateView):
    template = "index.html"
    scope = [
        "index.html",
        "masquerade_1.html",
        "masquerade_2.html",
        "masquerade_3.html",
    ]


class TestMasqueradeNoScope(TemplateView):
    template = "index.html"


class TestUrlCreation(TemplateView):
    template = "create_url.html"
