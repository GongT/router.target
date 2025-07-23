import os
from pathlib import Path
from sys import argv

from dotenv import load_dotenv

from . import fs as _fs
from . import logger as _logger

relative_dir = Path(__file__).parent


def set_working_directory(path: str | Path) -> None:
    global relative_dir
    relative_dir = Path(relative_dir, path).absolute()


def get_working_path(path: str | Path) -> Path:
    return relative_dir / path


def get_assets_path(path: str | Path) -> Path:
    return LIBEXEC_ROOT / relative_dir.name / path


LIBROOT_DIR = Path(__file__).absolute().parent
ROOT_DIR = LIBROOT_DIR.parent.parent
load_dotenv(ROOT_DIR / ".env")

SERVICES_DIR = ROOT_DIR / "services"
UNIT_ROOT = Path("/usr/local/lib/systemd/system")
LIBEXEC_ROOT = Path("/usr/local/libexec/router")
SCRIPTS_ROOT = LIBEXEC_ROOT / "scripts"
BINARY_DIR = LIBEXEC_ROOT / "bin"
DIST_ROOT = LIBEXEC_ROOT / "dist"
TEMPDIR = Path("/tmp/router.target/installer")
CACHE_ROOT = (
    Path(os.environ.get("SYSTEM_COMMON_CACHE", "/var/cache")) / "Download/router.target"
)

_rp = os.environ.get("ROUTER_DATA_PATH", None)
if not _rp:
    _ap = os.environ.get("APP_DATA_PATH", default=None)
    if not _ap:
        _logger.die(
            "both APP_DATA_PATH and ROUTER_DATA_PATH not set in .env or environment variable. set ROUTER_DATA_PATH in .env file."
        )

    ROUTER_DATA_PATH = Path(_ap) / "router"
else:
    ROUTER_DATA_PATH = Path(_rp)


RUNTIME_ENVFILE = LIBEXEC_ROOT / ".env"
PYENV = Path()


def set_pyenv(path: str):
    global PYENV
    PYENV = Path(path)
    make_environ_file()


def get_python():
    if not PYENV.exists():
        _logger.die(f"PYENV path does not exist: {PYENV}")
    return PYENV.joinpath("bin/python").as_posix()


def make_environ_file():
    path_map = {
        "ROUTER_DATA_PATH": ROUTER_DATA_PATH.as_posix(),
        "ROOT_DIR": ROOT_DIR.as_posix(),
        "DIST_ROOT": DIST_ROOT.as_posix(),
        "LIBEXEC_ROOT": LIBEXEC_ROOT.as_posix(),
        "SCRIPTS_ROOT": SCRIPTS_ROOT.as_posix(),
        "RUNTIME_ENVFILE": RUNTIME_ENVFILE.as_posix(),
        "VIRTUAL_ENV": PYENV.as_posix(),
        "BINARY_DIR": BINARY_DIR.as_posix(),
        "PYTHON3": get_python(),
    }

    r = ""
    for k, v in path_map.items():
        _logger.dim(f": {k}={v}")
        r += f"{k}={v}\n"

    _fs.write_if_change(RUNTIME_ENVFILE, r)


os.chdir(ROOT_DIR)

is_force = "--force" in argv
is_install = "--install" in argv
