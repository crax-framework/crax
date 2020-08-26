"""
Type hint variables
"""
import typing

Scope = typing.MutableMapping[str, typing.Any]

Message = typing.MutableMapping[str, typing.Any]

Receive = typing.Callable[[], typing.Awaitable[Message]]

Send = typing.Callable[[Message], typing.Awaitable[None]]

ASGIApp = typing.TypeVar("ASGIApp")

Request = typing.TypeVar("Request")

Model = typing.TypeVar("Model")

DBQuery = typing.TypeVar("DBQuery")

Selectable = typing.TypeVar("Selectable")

ExceptionType = typing.TypeVar("ExceptionType")
