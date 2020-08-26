"""
Route and Url objects that provides Crax url resolving system.
"""
import re
from typing import Optional

import typing

from crax.data_types import Request
from crax.exceptions import CraxImproperlyConfigured, CraxPathNotFound
from crax.views import DefaultError


def include(module: str) -> Optional[list]:
    try:
        spl_module = module.split(".")
        urls = __import__(module, fromlist=spl_module)
        url_list = urls.url_list
        for route in url_list:
            for url in route.urls:
                if not url.namespace:
                    url.namespace = urls.__package__
        return url_list
    except (ModuleNotFoundError, ImportError, AttributeError) as e:
        raise e.__class__(e) from e


class Url:
    def __init__(self, path: str, **kwargs: typing.Any) -> None:
        self.path = path
        self.name = kwargs.pop("name", None)
        self.type_ = kwargs.pop("type", "path")
        self.scheme = kwargs.pop("scheme", ["http", "http.request"])
        self.masquerade = kwargs.pop("masquerade", False)
        self.namespace = kwargs.pop("namespace", "")
        self.tag = kwargs.get("tag")
        self.methods = kwargs.get("methods")


class Route:
    def __init__(self, urls: typing.Any, handler: typing.Callable) -> None:
        self.handler = handler
        try:
            self.urls = tuple(urls)
        except TypeError:
            self.urls = (urls,)

    @staticmethod
    def create_path(url: Url, path: str) -> typing.Tuple[str, str]:
        if url.masquerade is False and not path.endswith("/"):
            path = path + "/"
        else:
            path = path
        if url.namespace:
            namespace = "/".join(url.namespace.split("."))
            final_path = f"/{namespace}{url.path}"
        else:
            final_path = url.path
        return final_path, path

    def check_len(self, url: Url, request_path: str) -> typing.Tuple[bool, dict]:
        find_path, path = self.create_path(url, request_path)
        matched = False
        params = {}
        if find_path == path:
            matched = True
        elif url.masquerade is True:
            split_req_path = [x for x in request_path.split("/") if x]
            split_path = [x for x in find_path.split("/") if x]
            if split_path == split_req_path[:-1]:
                matched = True
            else:
                matched = False
        else:
            split_req_path = [x for x in request_path.split("/") if x]
            split_path = [x for x in find_path.split("/") if x]
            intersection = set(split_req_path).intersection(split_path)
            if url.namespace:
                if len(intersection) == len(url.namespace.split(".")) + 1 and len(
                    split_path
                ) == len(split_req_path):
                    if all([x in split_req_path for x in split_path if "<" not in x]):
                        matched = True
            else:
                if len(intersection) > 0 and len(split_path) == len(split_req_path):
                    if all([x in split_req_path for x in split_path if "<" not in x]):
                        matched = True
            if matched is True:
                pattern = re.compile("<([a-zA-Z0-9_:]+)>")
                names = [
                    "".join(re.split(pattern, x)).split(":")[0]
                    for x in split_path
                    if re.match(pattern, x)
                ]
                values = [x for x in split_req_path if x not in intersection]
                params = dict(zip(names, values))
        return matched, params

    def get_match(self, request: Request) -> Optional[typing.Callable]:
        scheme = request.scheme
        handler = None
        matched = False
        params = {}
        for url in self.urls:
            if isinstance(url, Url):
                find_path, path = self.create_path(url, request.path)
                if url.type_ == "re_path":
                    match = re.match(find_path, path)
                    if match:
                        params = match.groupdict()
                        matched = True
                else:
                    matched, params = self.check_len(url, path)
                if matched is True and scheme in url.scheme:
                    handler = self.handler
                    request.params = params
                    if url.masquerade is True:
                        if hasattr(handler, "scope"):
                            masqueraded = [
                                x
                                for x in handler.scope
                                if x == request.path.split("/")[-1]
                            ]
                            if not masqueraded:
                                handler = DefaultError(
                                    request, CraxPathNotFound(request.path)
                                )
                            else:
                                handler.template = masqueraded[0]
                        else:
                            handler = DefaultError(
                                request, CraxPathNotFound(request.path)
                            )
            else:
                handler = DefaultError(
                    request,
                    CraxImproperlyConfigured(f'{url} should be instance of "Url"'),
                )
        return handler
