import base64

def is_dict_empty(d: dict):
    return len(d) == 0


def dict_pop(d: dict, field: str):
    return d.pop(field, None)


def base64_decode(data: str):
    blen = len(data)
    if blen % 4 > 0:
        data += "=" * (4 - blen % 4)
    return base64.b64decode(data).decode()
