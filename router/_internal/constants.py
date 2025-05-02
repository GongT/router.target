import os
from pathlib import Path
from sys import argv

from dotenv import dotenv_values

from . import logger
from .fs import write_if_change

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
SERVICES_DIR = ROOT_DIR / "services"
UNIT_ROOT = Path("/usr/local/lib/systemd/system")
LIBEXEC_ROOT = Path("/usr/local/libexec/router")
SCRIPTS_ROOT = LIBEXEC_ROOT / "scripts"
DIST_ROOT = LIBEXEC_ROOT / "dist"
TEMPDIR = Path("/tmp/router.target/installer")
CACHE_ROOT = (
    Path(os.environ.get("SYSTEM_COMMON_CACHE", "/var/cache")) / "Download/router.target"
)

dotenv_file_content = {
    **dotenv_values(ROOT_DIR / ".env.sample", verbose=True),
    **dotenv_values(ROOT_DIR / ".env", verbose=True),
}
_ap = dotenv_file_content.get("APP_DATA_DIR")
if not _ap:
    logger.die("APP_DATA_DIR not set in .env")

APP_DATA_DIR = Path(_ap)

RUNTIME_ENVFILE = LIBEXEC_ROOT / ".env"
PYENV = Path()


def set_pyenv(path: str):
    global PYENV
    PYENV = Path(path)
    make_environ_file()


def make_environ_file():
    path_map = {
        "APP_DATA_DIR": APP_DATA_DIR.as_posix(),
        "ROOT_DIR": ROOT_DIR.as_posix(),
        "DIST_ROOT": DIST_ROOT.as_posix(),
        "LIBEXEC_ROOT": LIBEXEC_ROOT.as_posix(),
        "SCRIPTS_ROOT": SCRIPTS_ROOT.as_posix(),
        "RUNTIME_ENVFILE": RUNTIME_ENVFILE.as_posix(),
        "VIRTUAL_ENV": PYENV.as_posix(),
        "PYTHON3": PYENV.joinpath("bin/python").as_posix(),
    }

    r = ""
    for k, v in path_map.items():
        logger.dim(f": {k}={v}")
        r += f"{k}={v}\n"

    write_if_change(RUNTIME_ENVFILE, r)


os.chdir(ROOT_DIR)

is_force = "--force" in argv
is_install = "--install" in argv
