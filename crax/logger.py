"""
Base Logger class. All loggers should inherit from this one or
"get_logger" method should be defined if custom logger does not inherit
from BaseLogger class. By default logging disabled and should be set to
on in project settings.
"""
from abc import ABC, abstractmethod
import logging
import sys
from logging.handlers import TimedRotatingFileHandler

import typing

from crax.utils import get_settings_variable

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration

except ImportError:
    LoggingIntegration: typing.Any
    sentry_sdk = LoggingIntegration = None


class BaseLogger(ABC):
    def __init__(self):
        log_format = get_settings_variable(
            "LOG_FORMAT", default="%(asctime)s — %(name)s — %(levelname)s — %(message)s"
        )
        project_base_url = get_settings_variable("BASE_URL", default=".")
        self.formatter = logging.Formatter(log_format)
        self.logger_name = get_settings_variable("LOGGER_NAME", default="crax")
        self.log_file = get_settings_variable(
            "LOG_FILE", default=f"{project_base_url}/crax.log"
        )
        self.log_level = get_settings_variable("LOG_LEVEL", default="INFO")
        self.log_rotate_time = get_settings_variable(
            "LOG_ROTATE_TIME", default="midnight"
        )
        self.console = get_settings_variable("LOG_CONSOLE", default=False)
        self.streams = get_settings_variable(
            "LOG_STREAMS", default=[sys.stdout, sys.stderr]
        )

        enable_sentry = get_settings_variable("ENABLE_SENTRY", default=False)
        if enable_sentry is True:  # pragma: no cover
            assert sentry_sdk is not None and LoggingIntegration is not None
            sentry_dsn = get_settings_variable("LOG_SENTRY_DSN")
            assert sentry_dsn is not None
            sentry_log_level = get_settings_variable(
                "SENTRY_LOG_LEVEL", default=self.log_level
            )
            sentry_event_level = get_settings_variable(
                "SENTRY_EVENT_LEVEL", default="ERROR"
            )
            sentry_logging = LoggingIntegration(
                level=getattr(logging, sentry_log_level),
                event_level=getattr(logging, sentry_event_level),
            )
            sentry_sdk.init(dsn=sentry_dsn, integrations=[sentry_logging])

    @abstractmethod
    def get_logger(self):
        raise NotImplementedError  # pragma: no cover


class CraxLogger(BaseLogger):
    def get_console_handler(self):
        assert isinstance(self.streams, list)
        console_handlers = []
        for stream in self.streams:
            console_handler = logging.StreamHandler(stream)
            console_handler.setFormatter(self.formatter)
            console_handlers.append(console_handler)
        return console_handlers

    def get_file_handler(self) -> TimedRotatingFileHandler:
        file_handler = TimedRotatingFileHandler(
            self.log_file, when=self.log_rotate_time
        )
        file_handler.setFormatter(self.formatter)
        return file_handler

    def get_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(getattr(logging, self.log_level))
        if self.console is True:
            handlers = self.get_console_handler()
            for handler in handlers:
                logger.addHandler(handler)

        logger.addHandler(self.get_file_handler())
        logger.propagate = False
        return logger
