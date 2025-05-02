import re
from pathlib import Path

from . import constants, logger
from .config_file import KeyValueConfig
from .constants import UNIT_ROOT, get_working_path, write_if_change
from .fs import ensure_symlink, read_filtered_file, remove_unknown_files
from .subprocess import (
    execute_mute,
    execute_output,
    execute_output_error,
    execute_passthru,
)

registed_systemd_units: list[str] = []


def service_is_last_section(data: str) -> bool:
    """
    检查文件的[Service]是否在最后一节
    """
    lines = data.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("[Service]"):
            # 找到[Service]节
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("["):
                    # 找到下一个节，说明[Service]不在最后
                    return False
            return True
    # 没找到[Service]节
    return False


def filter_unit_file(src: Path) -> str:
    data = read_filtered_file(src)

    if src.name.endswith(".service"):
        if not service_is_last_section(data):
            logger.die(f"文件 {src} 的[Service]没有放在最后一节")
        data += f"""
Slice=router.target
EnvironmentFile={constants.RUNTIME_ENVFILE.as_posix()}
"""

    return f"""##### ROUTER GENERATED
## source={src}

{data}
"""


changed_unit_files: list[str] = []


def systemd_add_unit(install_name: str, source: None | str | Path = None):
    if source:
        source = get_working_path(source)
    else:
        source = get_working_path(install_name)
    install_name = Path(install_name).name

    unitfile = get_working_path(install_name)
    target = constants.UNIT_ROOT / install_name

    if not source.exists():
        logger.die(f"missing systemd unit file: {source}")

    # 过滤文件内容
    filtered = filter_unit_file(source)
    ch = write_if_change(target, filtered)
    if ch:
        changed_unit_files.append(target.as_posix())

    logger.dim(
        f"  * systemd unit file: {unitfile.relative_to(constants.ROOT_DIR)} -> {target}{'' if ch else ' (unchanged)'}"
    )

    if "[Install]" in filtered:
        if unitfile.stem.endswith("@") and "DefaultInstance=" not in filtered:
            pass
        else:
            registed_systemd_units.append(install_name)

    # 处理别名
    aliases = []
    for line in filtered.splitlines():
        if not line.startswith("Alias="):
            continue
        aliases.extend(line.split("=")[1].split(" "))

    for a in aliases:
        logger.dim(f"      -> alias: {a}")
        ensure_symlink(constants.UNIT_ROOT / a, unitfile, True)


def systemd_enable_unit(what: str):
    registed_systemd_units.append(what)


def systemd_override(unit_name: str, source: str | Path):
    if isinstance(source, str):
        source = get_working_path(source)

    target_dir = constants.UNIT_ROOT / f"{unit_name}.d/router-override.conf"
    filtered = read_filtered_file(source)
    ch = write_if_change(target_dir, filtered)

    print(f"  * systemd override file: {target_dir}{'' if ch else ' (unchanged)'}")
    if "@." not in unit_name and "[Install]" in filtered:
        registed_systemd_units.append(unit_name)


def cleanup_and_enable_services():
    removed = remove_unknown_files(constants.UNIT_ROOT)
    if len(removed) > 0:
        logger.info(f"removed {len(removed)} unknown systemd unit files")
        names = [file.name for file in removed]
        execute_mute("systemctl", "disable", *names, ignore=True)

    execute_passthru("systemctl", "daemon-reload")

    for path in changed_unit_files:
        error_found, _ = execute_output_error(
            "systemd-analyze", "verify", path, join=True, ignore=True
        )
        for line in error_found.splitlines():
            if not line.startswith(UNIT_ROOT.as_posix()):
                logger.warning(line)
            if not line.startswith(path):
                continue  # not this unit problem

            if "Failed to assign slice router.target" in line:
                continue  # exectuion order problem

            logger.warning(line)

    logger.info(f"enable {len(registed_systemd_units)} units...")
    execute_passthru("systemctl", "enable", *registed_systemd_units)


def simulate_systemd_enable_one(unit_name: str):
    """
    模拟 systemd enable 的行为，但是发生在 UNIT_ROOT 而非 /etc/systemd/system
    """
    istemplate = "@" in unit_name

    unit_file = unit_name if not istemplate else re.sub(r"@.*\.", "@.", unit_name)
    filepath = constants.UNIT_ROOT / unit_file

    unit = KeyValueConfig(filepath)
    unit.load()

    for field, revert in [
        (
            "WantedBy",
            "wants",
        ),
        (
            "RequiredBy",
            "requires",
        ),
        (
            "UpheldBy",
            "upholds",
        ),
    ]:
        for target in flatten_multi_line(unit.get_all(f"Install.{field}", [])):
            dir = constants.UNIT_ROOT / f"{target}.{revert}"
            logger.dim(f"[units] {unit_name} is {field} {target}")
            ensure_symlink(dir / unit_name, filepath, True)


def flatten_multi_line(values: list[str]) -> list[str]:
    r: list[str] = []
    for val in values:
        r.extend(val.split(" "))
    return r
