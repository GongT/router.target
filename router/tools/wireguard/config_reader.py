from errno import EMULTIHOP
from hmac import new
from pathlib import Path
from sys import stderr


class Option:
    def __init__(self, name: str, value: str, position: int) -> None:
        self._name = name
        self.__old_value = value
        self._new_value = value
        self._position = position
        self._deleted = False

    @property
    def changed(self):
        return self._new_value != self.__old_value

    @property
    def deleted(self):
        return self._deleted

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._new_value

    @value.setter
    def value(self, new_value: str):
        self._new_value = new_value

    def print(self):
        return f"{self._name} = {self._new_value}"

    def delete(self):
        self._deleted = True


class RawString:
    def __init__(self, value: str, position: int) -> None:
        self._text = value
        self._deleted = False
        self._position = position

    def print(self):
        return self._text

    @property
    def deleted(self):
        return self._deleted

    def delete(self):
        self._deleted = True


class Section:
    def __init__(self, section_title: str) -> None:
        self.section_title = section_title
        self.lines: list[RawString | Option] = []
        self.options: dict[str, Option] = {}

    @property
    def is_empty(self):
        for line in self.lines:
            if line.deleted or line.print() == "":
                continue
            return False
        return True

    def _add_line(self, line: str) -> None:
        if "=" not in line:
            self.lines.append(RawString(line, len(self.lines)))
            # print('get line: ',line, file=stderr)
            return

        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        # print('get key: ', name, file=stderr)
        self._push(name, value)

    def _push(self, name: str, value: str):
        opt = Option(name, value, len(self.lines))
        self.options[name] = opt
        self.lines.append(opt)

    def _find_name(self, fname: str):
        for name, opt in self.options.items():
            if name.lower() == fname.lower():
                return opt
        return None

    def _find_last_empty_line(self):
        for l in reversed(self.lines):
            if l.deleted:
                continue

            if isinstance(l, RawString):
                if l.print() == "":
                    return l._position

        return None

    def get(self, name: str):
        opt = self._find_name(name)
        if opt:
            return opt.value
        return None

    def set(self, name: str, value: str):
        opt = self._find_name(name)
        if opt:
            # print("update value: ", name, file=stderr)
            opt.value = value
        else:
            # print("create value: ", name, file=stderr)
            replace_to = self._find_last_empty_line()
            if replace_to:
                opt = Option(name, value, replace_to)
                self.lines[replace_to] = opt
                self.options[name] = opt
            else:
                self._push(name, value)
            self.lines.append(RawString("", len(self.lines)))

    def delete(self, name: str):
        opt = self._find_name(name)
        if opt:
            # print("delete value: ", name, file=stderr)
            opt.delete()

    def keys(self):
        return self.options.keys()

    def itr_lines(self):
        for line in self.lines:
            if line.deleted:
                pass
            else:
                yield line.print()


class Config:
    _info: Section

    def __init__(self, file: Path):
        self._sections: list[Section] = []
        self._info = None
        self._file = file
        self._read()

    def update(self, saveAs: Path | None = None):
        new_text = self.to_string()
        if saveAs:
            saveAs.write_text(new_text, "utf8")
            return True

        if new_text != self._text:
            self._file.write_text(new_text, "utf8")
            return True
        else:
            return False

    def _read(self):
        if not self._file.exists():
            self._text = ""
            return

        text = self._file.read_text("utf8")
        current_section = self.insert_section("")
        for line in text.splitlines():
            sline = line.strip()
            if sline.startswith("[") and sline.endswith("]"):
                current_section = self.insert_section(sline[1:-1])
            else:
                current_section._add_line(line)

        self._text = text

    def insert_section(self, name: str):
        section = Section(name)
        if name.lower() == "interface":
            if not self._info:
                self._info = section
            else:
                raise ValueError("Multiple interface sections are not allowed.")

        self._sections.append(section)

        return section

    def keys(self):
        self._info.keys()

    def get(self, name: str):
        return self._info.get(name)

    def set(self, name: str, value: str):
        self._info.set(name, value)

    def delete(self, name: str):
        self._info.delete(name)

    def itr_lines(self):
        sections = []
        for p in self._sections:
            if p.is_empty:
                pass
            sections.append(p)

        if not sections:
            return

        for section in sections:
            if section.section_title:
                yield f"[{section.section_title}]"
            last_line =''
            for last_line in section.itr_lines():
                yield last_line
            if last_line != '':
                yield ''

    def to_string(self):
        if not self._info:
            raise ValueError("No interface section found.")

        return "\n".join(self.itr_lines())

    def new_peer(self, prikey: str, pubkey: str, ip: str, hostname: str):
        section = self.insert_section("peer")
        section.set("# private", prikey)
        section.set("PublicKey", pubkey)
        section.set("AllowedIPs", f"{ip} # {hostname}")
        return section

    def peers(self):
        for section in self._sections:
            if section.section_title.lower() != "peer":
                continue
            if section.is_empty:
                continue

            yield section


def read_wireguard_config(file_path: Path):
    return Config(file_path)
