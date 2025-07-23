from pathlib import Path


def fix_base64_padding(encoded_file: str | Path):
    """
    修正base64文件的填充
    """
    with open(encoded_file, "rb+") as f:
        content = f.read()
        mod = len(content) % 4
        if mod != 0:
            padding_num = 4 - mod
            f.write(b"=" * padding_num)
