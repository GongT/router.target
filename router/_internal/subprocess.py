import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from . import logger


def _run(cmds: Iterable[str], **kwargs):
    try:
        return subprocess.run(list(cmds), **kwargs)
    except Exception as e:
        logger.warning(f"the command is: {' ' .join(cmds)}")
        logger.warning(f"working directory: {kwargs.get('cwd', os.getcwd())}")
        logger.die(f"process start failed. error: {e}")


def execute_mute(*cmds: str, cwd: str | Path = os.getcwd(), ignore=False):
    execute_output_error(*cmds, cwd=cwd, ignore=ignore, join=True)


def execute_passthru(*cmds: str, cwd: str | Path = os.getcwd(), ignore=False):
    logger.dim(f"$ {' ' .join(cmds)}")
    result = _run(cmds, stdout=sys.stdout, stderr=sys.stderr, text=True, cwd=cwd)

    if result.returncode != 0 and not ignore:
        logger.warning(f"the command is: {' ' .join(cmds)}")
        logger.die(f"command failed with return code: {result.returncode}")


def execute_output(*cmds: str, cwd: str | Path = os.getcwd(), ignore=False):
    return execute_output_error(*cmds, cwd=cwd, ignore=ignore)[0]


def execute_output_error(
    *cmds: str, cwd: str | Path = os.getcwd(), ignore=False, join=False
):
    logger.dim(f"$ {' ' .join(cmds)}")
    stderr_option = subprocess.STDOUT if join else subprocess.PIPE

    result = _run(
        cmds, stdout=subprocess.PIPE, stderr=stderr_option, text=True, cwd=cwd
    )

    if result.returncode != 0 and not ignore:
        logger.dim(result.stdout if join else result.stderr)
        logger.print("")
        logger.warning(f"the command is: {' ' .join(cmds)}")
        logger.die(f"command failed with return code: {result.returncode}")

    return (result.stdout.strip(), result.stderr.strip() if not join else "")


def execute_json(*cmds: str, cwd: str | Path = os.getcwd()):
    text = execute_output(*cmds, cwd=cwd)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.dim(text)
        logger.print("")
        logger.warning(f"the command is: {' ' .join(cmds)}")
        logger.die(f"command output is not valid JSON")


def execute_result(*cmds: str, mute: bool = False, cwd: str | Path = os.getcwd()):
    stream = subprocess.DEVNULL if mute else sys.stderr
    result = _run(cmds, stdout=stream, stderr=stream, text=True, cwd=cwd)
    return result.returncode == 0
