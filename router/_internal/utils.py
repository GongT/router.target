import json


def dump_json(data, indent: int | None = 2):
    return json.dumps(data, indent=indent, ensure_ascii=False, check_circular=False)
