import importlib
import importlib.util
from os import chmod
from pathlib import Path

from . import constants, logger
from .constants import get_working_path
from .fs import read_filtered_file, write_if_change


def execute_python_script(file: Path):
    location = file.relative_to(constants.ROOT_DIR).as_posix()
    module = location.replace("/", ".").replace(".py", "")
    spec = importlib.util.spec_from_file_location(module, file.as_posix())
    if not spec:
        logger.die(f"failed to load {file} (spec is None)")
    foo = importlib.util.module_from_spec(spec)
    if not spec.loader:
        logger.die(f"failed to load {file} (spec.loader is None)")
    spec.loader.exec_module(foo)


def copy_script_file(file: Path):
    if file.suffix != ".sh":
        logger.die(f"install_script_file: {file} is not a shell script")

    src_file = file

    content = read_filtered_file(file)
    dest_file = constants.BINARY_DIR / file.stem

    if not content.startswith("#"):
        shebang_bash = "#!/usr/bin/env bash"
        content = shebang_bash + "\n" + content

    ch = write_if_change(dest_file, "\n".join(content))
    chmod(dest_file, 0o755)

    logger.dim(
        f"  * install binary: {dest_file.as_posix()} -> {src_file.relative_to(constants.ROOT_DIR)}{'' if ch else ' (unchanged)'}"
    )


def install_python_binary(dest_name: str, source_file: str | Path | None):
    if source_file is None:
        source_file = f"{dest_name}.py"

    src_file: Path
    if isinstance(source_file, str):
        src_file = get_working_path(source_file)
    elif source_file.is_absolute():
        src_file = Path(source_file)
    else:
        src_file = get_working_path(source_file)

    dest_file = constants.BINARY_DIR / dest_name
    content = ["#!/usr/bin/bash"]
    content.append(f"export PYTHONPATH={constants.ROOT_DIR.as_posix()}")
    content.append(f'exec "{constants.get_python()}" "{src_file.as_posix()}" "$@"')

    ch = write_if_change(dest_file, "\n".join(content))
    chmod(dest_file, 0o755)

    logger.dim(
        f"  * install binary: {dest_file.as_posix()} -> {src_file.relative_to(constants.ROOT_DIR)}{'' if ch else ' (unchanged)'}"
    )


def copy_libexec(source_file: str | Path):
    src_file: Path
    if isinstance(source_file, str):
        src_file = get_working_path(source_file)
    elif source_file.is_absolute():
        src_file = Path(source_file)
    else:
        src_file = get_working_path(source_file)

    output_file = constants.SCRIPTS_ROOT.joinpath(src_file.name)
    content = read_filtered_file(src_file)
    ch = write_if_change(output_file, content)
    logger.dim(
        f"  * install asset: {output_file.as_posix()} -> {src_file.relative_to(constants.ROOT_DIR)}{'' if ch else ' (unchanged)'}"
    )
