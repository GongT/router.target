import base64
import json
from sys import stderr


def die(msg: str):
    print(msg, file=stderr)
    exit(1)


def note(msg: str):
    print(f"\x1B[2m{msg}\x1B[0m", file=stderr)


def is_dict_empty(d: dict):
    return len(d) == 0


def dict_pop(d: dict, field: str):
    return d.pop(field, None)


def dump_json(data, indent: int | None = 2):
    return json.dumps(data, indent=indent, ensure_ascii=False, check_circular=False)


def base64_decode(data: str):
    blen = len(data)
    if blen % 4 > 0:
        data += "=" * (4 - blen % 4)
    return base64.b64decode(data).decode()
