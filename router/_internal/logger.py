import builtins
import sys
from typing import NoReturn


def die(msg: str) -> NoReturn:
    error(f"\n{msg}\n")
    sys.exit(1)


def dim(s: str):
    builtins.print(f"\x1b[2m{s}\x1b[0m", file=sys.stderr)


def print(s: str):
    builtins.print(s, file=sys.stderr)


def error(s: str):
    builtins.print(f"\x1b[38;5;9m{s}\x1b[0m", file=sys.stderr)


def warning(s: str):
    builtins.print(f"\x1b[38;5;11m{s}\x1b[0m", file=sys.stderr)


def success(s: str):
    builtins.print(f"\x1b[38;5;10m{s}\x1b[0m", file=sys.stderr)


def info(s: str):
    builtins.print(f"\x1b[38;5;14m{s}\x1b[0m", file=sys.stderr)
