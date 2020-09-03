"""
System helpers.
"""
import os

import typing
from crax.response_types import TextResponse


def get_settings(settings: str = None) -> typing.Any:
    if settings is None:
        settings = os.environ.get("CRAX_SETTINGS", "crax.conf")
    try:
        spl_settings = settings.split(".")
        return __import__(settings, fromlist=spl_settings)
    except (ImportError, ModuleNotFoundError) as ex:
        raise ex.__class__(ex) from ex


def get_settings_variable(variable: str, default=None) -> typing.Any:
    settings = get_settings()
    var = None
    if hasattr(settings, variable):
        var = getattr(settings, variable)
    else:
        if default is not None:
            var = default
    return var


async def collect_middleware(based: str) -> typing.Any:
    middleware = get_settings_variable("MIDDLEWARE")
    middleware_list = []
    if middleware:
        for m in middleware:
            spl_middleware = m.split(".")
            try:
                module = __import__(
                    ".".join(spl_middleware[:-1]), fromlist=spl_middleware[:-1]
                )
                middle = getattr(module, spl_middleware[-1])
                if based in [x.__name__ for x in middle.__bases__]:
                    middleware_list.append(middle)
            except (ImportError, AttributeError, ModuleNotFoundError) as ex:
                return ex
    return middleware_list


def unpack_urls(nest: typing.Any) -> typing.Generator:
    if isinstance(nest, list):
        for lst in nest:
            yield from unpack_urls(lst):
    else:
        yield nest


def get_error_handler(error: typing.Any) -> typing.Callable:
    error_handlers = get_settings_variable("ERROR_HANDLERS")
    if hasattr(error, 'status_code'):
        status_code = error.status_code
    else:
        status_code = 500
    handler = None
    if error_handlers is not None:
        if isinstance(error_handlers, dict) and error_handlers:
            try:
                if hasattr(error, "status_code"):
                    handler = error_handlers[f"{status_code}_handler"]
                else:
                    handler = error_handlers["500_handler"]
            except KeyError:  # pragma: no cover
                pass
    else:
        if hasattr(error, 'message'):
            message = error.message
        else:
            message = 'Internal server error'
        handler = TextResponse(None, message, status_code=status_code)
    return handler
