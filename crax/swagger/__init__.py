from crax.views import SwaggerCrax
from crax.urls import Route, Url

urls = [Route(Url("/api_doc", tag="crax"), SwaggerCrax)]
