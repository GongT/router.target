import importlib
import importlib.util
from pathlib import Path

from .fs import read_filtered_file

from . import constants
from . import logger


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
    if  file.suffix != ".sh":
        logger.die(f"install_script_file: {file} is not a shell script")
        
    data = read_filtered_file(file)
    dest = constants.LIBROOT_DIR / "bin" / file.name
