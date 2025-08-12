import builtins
import sys
from typing import Any, NoReturn


def die(msg: str, *ex: Any) -> NoReturn:

    builtins.print("", file=sys.stderr)
    error(f"{msg}", *ex)
    builtins.print("", file=sys.stderr)

    sys.exit(1)


def dim(s: str, *ex: Any):
    builtins.print(f"\x1b[2m{s}\x1b[0m", *ex, file=sys.stderr)


def print(s: str, *ex: Any):
    builtins.print(s, *ex, file=sys.stderr)


def error(s: str, *ex: Any):
    builtins.print(f"\x1b[38;5;9m{s}\x1b[0m", *ex, file=sys.stderr)


def warning(s: str, *ex: Any):
    builtins.print(f"\x1b[38;5;11m{s}\x1b[0m", *ex, file=sys.stderr)


def success(s: str, *ex: Any):
    builtins.print(f"\x1b[38;5;10m{s}\x1b[0m", *ex, file=sys.stderr)


def info(s: str, *ex: Any):
    builtins.print(f"\x1b[38;5;14m{s}\x1b[0m", *ex, file=sys.stderr)
