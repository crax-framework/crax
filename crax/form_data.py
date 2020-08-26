"""
Form data processing. Thanks for some ideas and code snippets to Starlette framework
that really shines.
"""
import tempfile
from dataclasses import dataclass

import typing
from urllib.parse import unquote_plus

import aiofiles
from multipart import multipart
from multipart.multipart import parse_options_header

from crax.data_types import Request


@dataclass(frozen=True)
class FormMultiPartData:
    part_begin: str = "part_begin"
    part_data: str = "part_data"
    part_end: str = "part_end"

    header_field: str = "header_field"
    header_value: str = "header_value"
    header_end: str = "header_end"
    headers_finished: str = "headers_finished"

    end: str = "end"


@dataclass(frozen=True)
class FormUrlencodedData:
    key: str = "key"
    value: str = "value"


class UploadFile:

    spool_max_size = 1024 * 1024

    def __init__(self, filename: str, content_type: str = "") -> None:
        self.filename = filename
        self.content_type = content_type
        self.file = tempfile.SpooledTemporaryFile(max_size=self.spool_max_size)

    @property
    def _in_memory(self) -> bool:
        rolled_to_disk = getattr(self.file, "_rolled", True)
        return not rolled_to_disk

    async def write(self, data) -> None:
        if self._in_memory:
            self.file.write(data)

    async def read(self, size: int = -1):
        if self._in_memory:
            return self.file.read(size)

    async def seek(self, offset: int) -> None:
        if self._in_memory:
            self.file.seek(offset)

    async def close(self) -> None:
        if self._in_memory:
            self.file.close()

    async def save(self, path=None):
        if path:
            save_path = f"{path}/{self.filename}"
        else:
            save_path = self.filename
        if self._in_memory:
            async with aiofiles.open(save_path, mode="wb") as f:
                await f.write(self.file.read())


class FormData:
    def __init__(
        self, request: Request, body: typing.AsyncGenerator[bytes, None]
    ) -> None:
        self.request = request
        self.body = body
        self.messages = []
        _type = self.request.headers.get("content-type", None)
        self.content_type, self.params = parse_options_header(_type)

    @staticmethod
    def _decode(src: bytes, encode: str) -> str:
        if isinstance(encode, bytes):
            encode = encode.decode("latin-1")
        if isinstance(src, bytes):
            try:
                return src.decode(encode)
            except (UnicodeDecodeError, LookupError):
                return src.decode("latin-1")
        elif isinstance(src, str):
            return src

    async def multi_part(self) -> None:
        header_field = b""
        header_value = b""
        content_disposition = None
        field_name = ""
        _data = b""
        file = None

        boundary = self.params.get(b"boundary")
        charset = self.params.get(b"charset", "utf-8")
        callbacks = {
            "on_part_begin": lambda: self.messages.append(
                (FormMultiPartData.part_begin, b"")
            ),
            "on_part_data": lambda i, j, k: self.messages.append(
                (FormMultiPartData.part_data, i[j:k])
            ),
            "on_part_end": lambda: self.messages.append(
                (FormMultiPartData.part_end, b"")
            ),
            "on_header_field": lambda i, j, k: self.messages.append(
                (FormMultiPartData.header_field, i[j:k])
            ),
            "on_header_value": lambda i, j, k: self.messages.append(
                (FormMultiPartData.header_value, i[j:k])
            ),
            "on_header_end": lambda: self.messages.append(
                (FormMultiPartData.header_end, b"")
            ),
            "on_headers_finished": lambda: self.messages.append(
                (FormMultiPartData.headers_finished, b"")
            ),
            "on_end": lambda: self.messages.append((FormMultiPartData.end, b"")),
        }
        parser = multipart.MultipartParser(boundary, callbacks)
        async for chunk in self.body:
            parser.write(chunk)
            messages = list(self.messages)
            self.messages.clear()
            for message_type, message_bytes in messages:
                if message_type == FormMultiPartData.part_begin:
                    content_disposition = None
                    self.content_type = b""
                    _data = b""
                elif message_type == FormMultiPartData.header_field:
                    header_field += message_bytes
                elif message_type == FormMultiPartData.header_value:
                    header_value += message_bytes
                elif message_type == FormMultiPartData.header_end:
                    field = header_field.lower()
                    if field == b"content-disposition":
                        content_disposition = header_value
                    elif field == b"content-type":
                        self.content_type = header_value
                    header_field = b""
                    header_value = b""
                elif message_type == FormMultiPartData.headers_finished:
                    disposition, options = parse_options_header(content_disposition)
                    field_name = self._decode(options[b"name"], charset)
                    if b"filename" in options:
                        filename = self._decode(options[b"filename"], charset)
                        file = UploadFile(
                            filename=filename,
                            content_type=self.content_type.decode("latin-1"),
                        )
                    else:
                        file = None
                elif message_type == FormMultiPartData.part_data:
                    if file is None:
                        _data += message_bytes
                    else:
                        await file.write(message_bytes)
                elif message_type == FormMultiPartData.part_end:
                    if file is None:
                        self.request.post[field_name] = self._decode(_data, charset)
                    else:
                        await file.seek(0)
                        self.request.files[field_name] = file
                elif message_type == FormMultiPartData.end:
                    pass

    async def urlencoded(self) -> None:
        field_name = b""
        callbacks = {
            "on_field_name": lambda data, start, end: self.messages.append(
                (FormUrlencodedData.key, data[start:end])
            ),
            "on_field_data": lambda data, start, end: self.messages.append(
                (FormUrlencodedData.value, data[start:end])
            ),
        }
        parser = multipart.QuerystringParser(callbacks)
        async for chunk in self.body:
            if chunk:
                parser.write(chunk)
            else:
                parser.finalize()  # pragma: no cover
            messages = list(self.messages)
            self.messages.clear()
            for message_type, message_bytes in messages:
                if message_type == FormUrlencodedData.key:
                    field_name = message_bytes.decode("latin-1")
                    self.request.post[field_name] = None
                elif message_type == FormUrlencodedData.value:
                    self.request.post[field_name] = unquote_plus(
                        message_bytes.decode("latin-1")
                    )

    async def plain(self) -> None:
        body = b""
        charset = self.params.get(b"charset", "utf-8")
        async for chunk in self.body:
            if chunk:
                body += chunk
        _body = self._decode(body, charset)
        self.request.post = _body

    async def process(self) -> None:
        if self.content_type == b"multipart/form-data":
            await self.multi_part()

        elif self.content_type == b"application/x-www-form-urlencoded":
            await self.urlencoded()

        elif self.content_type in [b"text/plain", b"application/json"]:
            await self.plain()
