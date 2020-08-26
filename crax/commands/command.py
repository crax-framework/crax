"""
Base command class. In case if user wants to use crax commands, "from_shell" function
should be placed to main application file.
"""
import argparse
import os
import re
import sys
import shlex
import subprocess

import typing

sys.path = ["", ".."] + sys.path[1:]
COMMANDS_URL = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/commands"


def from_shell(
    args: typing.Union[tuple, list], settings: str = None
) -> None:  # pragma: no cover
    command = args[1]
    commands = [x for x in os.listdir(COMMANDS_URL) if x.split(".")[0] == command]
    if commands:
        if settings:
            os.environ["CRAX_SETTINGS"] = settings
        else:
            os.environ["CRAX_SETTINGS"] = "crax.conf"
        str_args = " ".join(args[1:])
        keys = re.findall(r"--?\w+ ?.* ?", str_args)
        command_str = f'python {COMMANDS_URL}/{commands[0]} {" ".join(keys)}'
        subprocess.call(shlex.split(command_str))

    else:
        raise RuntimeError(f"Unknown command {command} \n")


class BaseCommand:
    def __init__(
        self, opts: typing.List[typing.Union[tuple]], **kwargs: typing.Any
    ) -> None:
        self.opts = opts
        self.kwargs = kwargs
        self.args = self.collect_args()

    def collect_args(self):
        parser = argparse.ArgumentParser()
        if self.opts:
            for option in self.opts:
                parser.add_argument(*option[0], **option[1])
        args = parser.parse_args()
        return args
