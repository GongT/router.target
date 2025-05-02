import re
from pathlib import Path
from typing import TypedDict

from . import logger


class ConfigValue(TypedDict):
    value: str
    values: list[str]
    lines: list[int]


class SectionValue(TypedDict):
    configs: dict[str, ConfigValue]
    start: int


class PendingEdit(TypedDict):
    content: str
    line: int


class KeyValueConfig:
    """A class to manage a key-value configuration file."""

    def __init__(self, filename: Path | str):
        self.filepath = Path(filename)
        self.config = {}
        

        self.allow_space_around_equals = False
        self.using_section_format = False
        self.value_need_quote = False
        self.sections: dict[str, SectionValue] = {}
        self.load_cursor = 0
        self.eof = False
        self.pending_insertion: list[PendingEdit] = []

    def load(self):
        """Load the configuration from the file."""
        if self.eof:
            logger.die("config file already loaded")

        if not self.filepath.exists():
            logger.die("missing required config file: " + self.filepath.as_posix())
        self.lines = self.filepath.read_text().splitlines()

        self.rewind()
        while self.move_next(True):
            line, _ = self.current_line()

            if line.startswith("[") and line.endswith("]"):
                self.using_section_format = True
            elif " =" in line or "= " in line:
                self.allow_space_around_equals = True

            if self.using_section_format and self.allow_space_around_equals:
                break

        self.rewind()
        self.load_key_value_format("*")
        if self.using_section_format:
            self.load_section_format()
        if not self.eof:
            logger.die("expect EOF, but got: " + self.current_line()[0])

    def should_ignore(self, ignore_invalid: bool) -> bool:
        line = self.lines[self.load_cursor]
        if line.startswith("#") or line.startswith(";") or line.strip() == "":
            return True
        if line.startswith("[") and line.endswith("]"):
            return False

        if "=" not in line:
            if ignore_invalid:
                return True
            logger.die("invalid line: " + line)

        return False

    def lookahead(self):
        nextline = self.load_cursor + 1
        return (self.lines[nextline] if nextline < len(self.lines) else None, nextline)

    def move_next(self, ignore_invalid=False) -> bool:
        self.load_cursor += 1
        while self.load_cursor < len(self.lines):
            if self.should_ignore(ignore_invalid):
                # print("\x1b[2m!!!", self.lines[self.load_cursor], "\x1b[0m")
                self.load_cursor += 1
            else:
                # print("\x1b[2m???", self.lines[self.load_cursor], "\x1b[0m")
                return True

        # print("\x1b[2m>>> EOF\x1b[0m")

        self.eof = True
        return False

    def rewind(self):
        self.load_cursor = -1
        self.eof = False

    def current_line(self):
        return self.lines[self.load_cursor], self.load_cursor

    def load_section_format(self):
        """Load the configuration in section format."""
        while self.move_next():
            line, _ = self.current_line()

            if line.startswith("[") and line.endswith("]"):
                # print("[read] section: ", line)
                section = line[1:-1].strip()
                self.load_key_value_format(section)
                continue
            else:
                logger.die(f"expect next section, but got: {line}")

    def load_key_value_format(self, section: str):
        """Load the configuration in key-value format."""
        if section not in self.sections:
            self.sections[section] = {
                "start": self.load_cursor,
                "configs": {},
            }

        while self.move_next():
            line, _ = self.current_line()

            if line.startswith("["):
                # print("[read] section ending")
                self.load_cursor -= 1
                break

            key, value = line.split("=", 1)
            if self.value_need_quote:
                value = value.strip()
            key = key.strip()
            value = value.strip()

            # print(f"[read] value: {section}.{key} = [{value}]")

            lines = [self.load_cursor]
            if re.search(r"\s+\\$", value):
                line, _ = self.lookahead()
                self.load_cursor += 1
                # print(f"[read] continues line: {line}")
                if line is None:
                    logger.die("expect next line, but got EOF")
                value = f"{value[:-1]}{line}"
                lines.append(self.load_cursor)

            sect = self.sections[section]["configs"]

            if key in sect:
                sect[key]["values"].append(value)
            else:
                sect[key] = {
                    "lines": lines,
                    "value": value,
                    "values": [value],
                }

    def get_all(self, sectiondotvalue: str, defaults: list[str] | None):
        d = self._get(sectiondotvalue)
        if d:
            return d["values"]

        if defaults is not None:
            return defaults
        logger.die("missing required config value: " + sectiondotvalue)

    def get(self, sectiondotvalue: str, defaults: str | None) -> str:
        d = self._get(sectiondotvalue)
        if d:
            return d["value"]

        if defaults:
            return defaults
        logger.die("missing required config value: " + sectiondotvalue)

    def _get(self, sectiondotvalue: str):
        if "." not in sectiondotvalue:
            sectiondotvalue = "*." + sectiondotvalue

        section, value = sectiondotvalue.split(".", 1)
        if section not in self.sections:
            return None
        if value not in self.sections[section]["configs"]:
            return None
        return self.sections[section]["configs"][value]

    def set(self, sectiondotvalue: str, value: str):
        """
        设置配置项的值，不支持多个值，只修改第一个
        """
        if "." not in sectiondotvalue:
            if self.using_section_format:
                logger.die("missing section in set operation: " + sectiondotvalue)
            else:
                sectiondotvalue = "*." + sectiondotvalue

        section, value_key = sectiondotvalue.split(".", 1)
        if section not in self.sections:
            self.lines.append(f"")
            self.lines.append(f"[{section}]")
            self.sections[section] = {
                "start": len(self.lines) - 1,
                "configs": {},
            }

        sect = self.sections[section]
        if value_key not in sect["configs"]:
            value = self.format(value_key, value)
            sect["configs"][value_key] = {
                "lines": [],
                "value": value,
                "values": [value],
            }
            self.pending_insertion.append({"line": sect["start"], "content": value})
        else:
            original = sect["configs"][value_key]
            if not original["lines"]:
                logger.die("config value insert twice: " + value_key)

            sect["configs"][value_key]["value"] = value
            self.lines[sect["configs"][value_key]["lines"][0]] = self.format(
                value_key, value
            )

    def format(self, key: str, value: str) -> str:
        """Format the key-value pair for output."""
        if self.value_need_quote:
            value = f'"{value}"'
        if self.allow_space_around_equals:
            return f"{key} = {value}"
        else:
            return f"{key}={value}"

    def commit(self, saveAs: str | None = None):
        """Commit the changes to the configuration file."""
        for line in reversed(self.pending_insertion):
            self.lines.insert(line["line"] + 1, line["content"])
        self.pending_insertion = []

        if saveAs:
            Path(saveAs).write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        else:
            self.filepath.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
