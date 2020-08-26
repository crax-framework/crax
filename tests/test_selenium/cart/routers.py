from crax.response_types import JSONResponse
from crax.views import TemplateView


class Cart(TemplateView):
    template = "index.html"
    methods = ["POST"]
    enable_csrf = False

    async def post(self):
        """
        :par pic: file
        :content_type: multipart/form-data
        """
        if self.request.files:
            await self.request.files["pic"].save()
        response = JSONResponse(self.request, self.request.post)
        return response
