import json
from pathlib import Path

from . import logger


def dump_json(data, indent: int | None = 2):
    return json.dumps(data, indent=indent, ensure_ascii=False, check_circular=False)


def write_file_if_changed(file: Path, data: str):
    try:
        content = file.read_text()
    except FileNotFoundError:
        content = None

    if content != data:
        file.write_text(data)
        logger.success(f"写入文件 {file}")

        if content is not None:
            file.with_suffix(f"{file.suffix}.bak").write_text(content)
        return True

    logger.dim(f"跳过写入，文件未改变: {file}")
    return False
