"""
Base Exception classes. In case if debug mode is set to ON, exceptions
will be shown in browser, otherwise crax will try to find user defined
views according to error status code. If no error view will be found
exception will be raised common way. If logging system was enabled
in project settings all exceptions will be logged.
"""
import typing


class BaseCraxException(Exception):
    message = None
    status_code = 500

    def __init__(self, *args: typing.Optional[typing.Any]) -> None:
        super(BaseCraxException, self).__init__("%s %s" % (self.message, *args))
        raise self


class CraxUnauthorized(BaseCraxException):
    message = "Not Authorized"
    status_code = 401


class CraxForbidden(BaseCraxException):
    message = "Access Denied"
    status_code = 403


class CraxTemplateNotFound(BaseCraxException):
    message = "Template not found"
    status_code = 404


class CraxPathNotFound(BaseCraxException):
    message = "Path not found"
    status_code = 404


class CraxImproperlyConfigured(BaseCraxException):
    message = "Invalid configuration: "
    status_code = 500


class CraxNoTemplateGiven(BaseCraxException):
    message = "No template given"
    status_code = 500


class CraxNoMethodGiven(BaseCraxException):
    message = "No method was given for the view"
    status_code = 500


class CraxEmptyMethods(BaseCraxException):
    message = "No methods was specified for the view"
    status_code = 500


class CraxMethodNotAllowed(BaseCraxException):
    message = "Method not allowed for this view"
    status_code = 405


class CraxNoRootPath(BaseCraxException):
    message = "No root path in url lists found"
    status_code = 500


class CraxDataBaseImproperlyConfigured(BaseCraxException):
    message = "Database connection improperly configured"
    status_code = 500


class CraxDataBaseNotFound(BaseCraxException):
    message = "Database not found"
    status_code = 500


class CraxMigrationsError(BaseCraxException):
    message = "Migration Error"
    status_code = 500


class CraxUnknownUrlParameterTypeError(BaseCraxException):
    message = "Swagger Error"
    status_code = 500
