from dataclasses import dataclass, field


@dataclass
class SwaggerInfo:
    description: str = None
    version: str = None
    title: str = None
    termsOfService: str = None
    contact: dict = None
    license: dict = None
    host: str = None
    basePath: str = None
    servers: list = field(default_factory=list)


@dataclass
class SwaggerTag:
    name: str = None
    description: str = None
    externalDocs: dict = None


@dataclass
class SwaggerMethod:
    tags: list = field(default_factory=list)
    summary: str = ""
    description: str = ""
    operationId: str = None
    parameters: list = field(default_factory=list)
    responses: dict = None
    requestBody: dict = None
