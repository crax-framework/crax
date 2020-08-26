"""
Command to get OpenApi 3.0 schema for Swagger UI
"""
import json
import os
import re
import sys
import uuid

import typing

from crax.swagger.types import SwaggerTag, SwaggerMethod

from crax.commands.command import BaseCommand
from crax.exceptions import CraxImproperlyConfigured, CraxUnknownUrlParameterTypeError
from crax.utils import get_settings_variable, unpack_urls
from crax.conf import BASE_URL

COERCE_MAP = {
    "int": ["integer", "int64"],
    "float": ["number", "float"],
    "str": ["string", "string"],
    "date": ["string", "date"],
    "date-time": ["string", "date-time"],
    "password": ["string", "password"],
    "bytes": ["string", "byte"],
    "binary": ["string", "binary"],
    "bool": ["boolean", ""],
    "list": ["array", "{}"],
    "dict": ["object", "{}"],
    "file": ["file", "binary"],
}


class CreateSwagger(BaseCommand):
    def __init__(self, opts=None) -> None:
        super(CreateSwagger, self).__init__(opts)
        sys.path = ["", ".."] + sys.path[1:]
        self.info = {"openapi": "3.0.0"}
        url_patterns = get_settings_variable("URL_PATTERNS")
        swagger_info = get_settings_variable("SWAGGER")
        if not swagger_info:
            raise CraxImproperlyConfigured(
                "'SWAGGER' variable should"
                " be defined in configuration file to use Swagger"
            )
        elif swagger_info.servers is None or swagger_info.basePath is None:
            raise CraxImproperlyConfigured(
                "'SWAGGER_HOST' and 'SWAGGER_BASE_PATH' should"
                " be defined in configuration file to use Swagger"
            )
        self.base_path = swagger_info.basePath
        self.swagger_file = f"{BASE_URL}/crax/swagger/static/swagger.json"
        info = {
            k: v
            for k, v in swagger_info.__dict__.items()
            if k not in ["host", "basePath", "schemes"]
        }
        self.info["info"] = info
        self.info["host"] = swagger_info.host
        self.info["basePath"] = swagger_info.basePath
        self.info["servers"] = swagger_info.servers
        self.info["tags"] = []
        self.url_list = list(unpack_urls(url_patterns))

    @staticmethod
    def get_url_params(path: str, re_path=False) -> typing.List:
        if re_path is False:
            pattern = re.compile("<([a-zA-Z0-9_:]*)>")
        else:
            pattern = re.compile("<([a-zA-Z0-9_]*)>?[\a-z]{2}")
        spl = (i for i in path.split("/") if i)
        parts = []
        for i in spl:
            if re.search(pattern, i):
                match = re.search(pattern, i).group(0).replace("<", "").replace(">", "")
                if i.endswith("?"):
                    match = match + "?"
                parts.append(match)
        return parts

    @staticmethod
    def prepare_url(path: typing.List, re_path=False) -> str:
        parts = []
        path = path[0].split("/")
        if re_path is False:
            pattern = re.compile("<([a-zA-Z0-9_:]*)>")
            for i in path:
                if re.match(pattern, i):
                    param = i.split(":")[0]
                    param = "%s}" % param.replace("<", "{")
                    parts.append(param)
                else:
                    parts.append(i)
        else:
            for i in path:
                if i:
                    match = re.findall(r"<[a-zA-Z0-9_]*>", i)
                    if match:
                        parts.append("".join(match).replace("<", "{").replace(">", "}"))
                    else:
                        parts.append(i)
        uri = "/".join(parts)
        if not uri.startswith("/"):
            uri = "/" + uri
        return uri

    @staticmethod
    def create_parameters(parameter: list, pass_type: str, required=True):
        param_desc = {"name": parameter[0], "in": pass_type, "required": required}
        try:
            type_ = COERCE_MAP[parameter[1]][0]
            format_ = COERCE_MAP[parameter[1]][1]
            if parameter[1] == "list":
                param_desc.update({"type": type_, "items": format_})
            elif parameter[1] == "dict":
                param_desc.update({"type": type_, "additionalProperties": format_})
            else:
                param_desc.update({"type": type_, "format": format_})
        except KeyError:
            raise CraxUnknownUrlParameterTypeError(
                f"Unknown parameter type {parameter[1]}"
            )
        return param_desc

    def create_path_parameters(
        self, path: str, re_path=False, required=True
    ) -> typing.List:
        parameters = []
        if re_path is False:
            for param in self.get_url_params(path):
                parameter = param.split(":")
                if len(parameter) > 1:
                    parameters.append(
                        self.create_parameters(parameter, "path", required=required)
                    )
        else:
            replacements = {"w": "str", "d": "int", "W": "str", "D": "int"}
            for param in self.get_url_params(path, re_path=True):
                parameter = param.split("\\")
                if len(parameter) > 1:
                    if parameter[1].endswith("?"):
                        parameter[1] = replacements[parameter[1][:-1]]
                        required = False
                    else:
                        parameter[1] = replacements[parameter[1]]
                    parameters.append(
                        self.create_parameters(parameter, "path", required=required)
                    )
        return parameters

    @staticmethod
    def create_responses(resp_lst):
        responses = {}
        for x in resp_lst:
            description = ""
            if len(x) > 1:
                description = x[1]
            responses[x[0].strip()] = {"description": description.strip()}
        return responses

    def get_description(self, method, http_method):
        method_status_codes = {
            "GET": 200,
            "POST": 201,
            "PUT": 204,
            "PATCH": 204,
            "DELETE": 204,
        }
        pattern = re.compile(r".*:\w+ ?\w+:?\w+")
        method_parameters = request_body = query_parameters = common_description = None
        responses = {
            method_status_codes[http_method.upper()]: {
                "description": "Success operation"
            }
        }
        if http_method.upper() in ["POST", "PUT", "PATCH"]:
            pass_type = "formData"
            content_type = "application/json"
        else:
            content_type = None
            pass_type = "path"
        if method.__doc__ is not None:
            doc_string = str(method.__doc__)
            match = re.search(pattern, doc_string)
            if match:
                common_description = re.split(r".*:\w+ ?\w+:?\w+", doc_string)[0]
                return_pattern = re.compile(r"(.*:return:)( ?\d+)( ?.*)")
                return_code = re.findall(return_pattern, doc_string)
                if return_code:
                    responses = self.create_responses([x[1:] for x in return_code])
                else:
                    responses = {
                        method_status_codes[http_method.upper()]: {
                            "description": "Success operation"
                        }
                    }
                params_pattern = re.compile(r".*:par \w+: ?\w+ ?\w+ ?\w+")
                content_type_pattern = re.compile(r"(.*:content_type:)( ?\w+/.*)")
                c_type = re.search(content_type_pattern, doc_string)
                if c_type:
                    content_type = c_type.group(2).strip()
                params = re.findall(params_pattern, doc_string)
                if params:
                    parameters = []
                    for param in params:
                        parameter = param.strip().split()
                        parameters.append(" ".join(parameter[1:]).replace(":", ""),)
                    if parameters:
                        method_parameters = parameters
                if method_parameters:
                    request_body, query_parameters = self.create_doc_parameters(
                        method_parameters, content_type
                    )
                type_pattern = re.compile(r".*:in: ?\w+")
                type_ = re.findall(type_pattern, doc_string)
                if type_:
                    pass_type = "".join(type_).split(":")[-1].strip()
            else:
                common_description = doc_string
        return (
            common_description,
            content_type,
            responses,
            request_body,
            query_parameters,
            pass_type,
        )

    def create_doc_parameters(self, parameters_lst, content_type):
        bulk = [x for x in parameters_lst if "bulk" in x]
        query_params = [x for x in parameters_lst if "query" in x]
        request_body = None
        resp_params = [
            x.split()
            for x in parameters_lst
            if x not in query_params and "bulk" not in x
        ]
        if resp_params:
            if bulk:
                request_body = {
                    "content": {
                        content_type: {
                            "schema": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        x[0]: {
                                            "type": COERCE_MAP[x[1]][0],
                                            "format": COERCE_MAP[x[1]][0],
                                        }
                                        for x in resp_params
                                    },
                                },
                            }
                        }
                    }
                }
            else:
                request_body = {
                    "content": {
                        content_type: {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    x[0]: {
                                        "type": COERCE_MAP[x[1]][0],
                                        "format": COERCE_MAP[x[1]][0],
                                    }
                                    for x in resp_params
                                },
                            }
                        }
                    }
                }

        if query_params:
            parameters = []
            required = False
            param_lst = [x.split() for x in query_params]
            for param in param_lst:
                if param[-1] == "required":
                    required = True
                    param = param[:-1]
                parameters.append(
                    self.create_parameters(param, "query", required=required)
                )
            query_params = parameters
        return request_body, query_params

    def create_swagger(self) -> None:
        paths = {}
        tags = {}

        for url in self.url_list:
            for u in url.urls:
                if self.base_path in u.path and u.tag != "crax":
                    uri = re.split(self.base_path, u.path)[1:]
                    if u.type_ != "re_path":
                        path = self.prepare_url(uri).replace("<", "{").replace(">", "}")
                    else:
                        path = (
                            self.prepare_url(uri, re_path=True)
                            .replace("<", "{")
                            .replace(">", "}")
                        )
                    if u.tag is None:
                        tag = [x for x in "".join(uri).split("/") if x][0]
                    else:
                        tag = u.tag
                    if tag not in tags:
                        tags[tag] = SwaggerTag(
                            name=tag, description=url.handler.__doc__
                        )
                    if u.methods is not None:
                        methods = [
                            x for x in url.handler.methods if x.upper() in u.methods
                        ]
                    else:
                        methods = url.handler.methods
                    path_methods = {}

                    for method in methods:
                        if hasattr(url.handler, method.lower()):
                            description_ = self.get_description(
                                getattr(url.handler, method.lower()), method
                            )
                            description = description_[0]
                            if description:
                                desc = description.split()
                                if len(desc) > 5:
                                    summary = f'{" ".join(desc[0:5])}...'
                                else:
                                    summary = description
                            else:
                                summary = description = ""
                            if u.type_ != "re_path":
                                parameters = self.create_path_parameters(u.path)
                            else:
                                parameters = self.create_path_parameters(
                                    u.path, re_path=True
                                )
                            if description_[3] is not None:
                                request_body = description_[3]
                            else:
                                request_body = None
                            if description_[4] is not None:
                                parameters += description_[4]

                            method_description = SwaggerMethod(
                                tags=[tag],
                                summary=summary,
                                description=description,
                                operationId=str(uuid.uuid4()),
                                parameters=parameters,
                                responses=description_[2],
                                requestBody=request_body,
                            )
                            path_methods[method.lower()] = method_description.__dict__
                            if u.namespace:
                                namespace = "/" + u.namespace.replace(".", "/")
                            else:
                                namespace = ""
                            if path.startswith("/"):
                                uri = f"{namespace}{self.base_path}{path}"
                            else:
                                uri = f"{namespace}{self.base_path}/{path}"
                            paths[uri] = path_methods
        self.info["tags"] = [x.__dict__ for x in tags.values()]
        self.info["paths"] = paths
        if os.path.isfile(self.swagger_file):
            os.remove(self.swagger_file)
        with open(self.swagger_file, "w") as swagger_file:
            swagger_file.write(json.dumps(self.info))


if __name__ == "__main__":  # pragma: no cover
    create_swagger = CreateSwagger().create_swagger
    create_swagger()
