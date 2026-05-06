import base64
from typing import TypeVar

T = TypeVar("T")


def is_dict_empty(d: dict):
    return len(d) == 0


def dict_pop(d: dict, field: str, Type: type[T] | None = str) -> T | None:
    v = d.pop(field, None)
    if v is None:
        return None
    if Type is not None and not isinstance(v, Type):
        raise ValueError(
            f"字段 {field} 应为 {Type.__name__}，实际是 {type(v).__name__}"
        )
    return v


def array_dict_pop(d: dict, field: str, Type: type[T] | None = str) -> T | None:
    v = d.pop(field, None)

    if v is None:
        return None

    if isinstance(v, list):
        r = v[0]
        if Type is not None and not isinstance(r, Type):
            raise ValueError(
                f"字段 {field} 应为 {Type.__name__} 数组，实际是 {type(r).__name__} 数组"
            )
        return r
    else:
        raise ValueError(f"字段 {field} 应为数组，实际是 {type(r).__name__}")


def base64_decode(data: str):
    blen = len(data)
    if blen % 4 > 0:
        data += "=" * (4 - blen % 4)
    return base64.b64decode(data).decode()
