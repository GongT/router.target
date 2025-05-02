import os
import tarfile
import zipfile
from pathlib import Path
from shutil import copy2

from . import constants, logger

output_paths: list[str] = []
changed_paths: list[str] = []


def read_filtered_file(src: str | Path) -> str:
    if isinstance(src, str):
        src = constants.get_working_path(src)
    data = src.read_text()

    variables_map = {
        "APP_DATA_DIR": constants.APP_DATA_DIR.as_posix(),
        "__dirname": src.parent.as_posix(),
        "__filename": src.as_posix(),
        "ROOT_DIR": constants.ROOT_DIR.as_posix(),
        "DIST_ROOT": constants.DIST_ROOT.as_posix(),
        "PWD": constants.relative_dir.as_posix(),
        "RUNTIME_ENVFILE": constants.RUNTIME_ENVFILE.as_posix(),
        "VIRTUAL_ENV": constants.PYENV.as_posix(),
        "PYTHON3": constants.PYENV.joinpath("bin/python").as_posix(),
    }

    for key, value in variables_map.items():
        data = data.replace("${" + key + "}", value)

    return data


def write_if_change(filepath: Path, data: str) -> bool:
    pathstr = filepath.as_posix()
    if pathstr in output_paths:
        logger.die(f"the file {filepath} write twice")
    output_paths.append(pathstr)

    if filepath.exists():
        if filepath.read_text() == data:
            return False
    else:
        filepath.parent.mkdir(parents=True, exist_ok=True)

    filepath.write_text(data)
    changed_paths.append(pathstr)
    return True


def ensure_symlink(link_file: Path | str, target: Path, relative: bool = False) -> None:
    if isinstance(link_file, str):
        link_file = Path(link_file)

    if not link_file.is_absolute():
        logger.die(f"the link file {link_file} must be absolute path")

    output_paths.append(link_file.as_posix())

    if relative and target.is_absolute():
        target = Path(os.path.relpath(target, link_file.parent))
    if link_file.is_symlink():
        if link_file.readlink() == target:
            return
        else:
            link_file.unlink()
    elif link_file.is_file():
        link_file.unlink()
    elif link_file.exists():
        link_file.unlink()

    changed_paths.append(link_file.as_posix())
    link_file.parent.mkdir(parents=True, exist_ok=True)
    link_file.symlink_to(target)


def remove_unknown_files(basedir: Path) -> list[Path]:
    removed = []
    for file in basedir.glob("**"):
        if file.is_file() and file.as_posix() not in output_paths:
            file.unlink()
            removed.append(file)
            logger.dim(f"  * unlink {file}")
    return removed


def install_directory(src: Path, dst: Path):
    """
    recursive copy directory, ignore exists files
    """
    for file in src.glob("**"):
        dstfile = dst / file.relative_to(src)
        if dstfile.exists() or dstfile.is_symlink():
            continue

        dstfile.parent.mkdir(parents=True, exist_ok=True)

        if file.is_symlink():
            target = file.readlink()
            dstfile.symlink_to(target)
            logger.dim(f"  * symlink {file} -> {dstfile}")
        elif file.is_file():
            copy2(file, dstfile)
            logger.dim(f"  * copy {file} -> {dstfile}")


def extract_archive(archive_path: Path, dest_dir: Path, stripe_components=0) -> None:
    """
    Extract a tar.gz or zip archive to a destination directory.
    """
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(dest_dir)
    else:
        with tarfile.open(archive_path, "r") as tar_ref:
            members = tar_ref.getmembers()

            def stripe(member: tarfile.TarInfo, path: str) -> tarfile.TarInfo:
                parts = member.path.split("/")[stripe_components:]

                if len(parts) == 0:
                    return None

                member.path = "/".join(parts)
                return member

            tar_ref.extractall(dest_dir, members=members, filter=stripe)
