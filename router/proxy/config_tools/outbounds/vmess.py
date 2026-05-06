import json
from typing import Any, TypedDict

from ....target import dump_json, logger
from ..data_types.outbound import Outbound
from ..functions import array_dict_pop, is_dict_empty


class VmessOutbound(Outbound):
    TYPE = "vmess"

    class config(TypedDict, total=False):
        # https://sing-box.sagernet.org/zh/configuration/outbound/vmess/
        server: str
        server_port: int

        uuid: str
        security: str
        alter_id: int
        global_padding: bool
        authenticated_length: bool
        network: str
        packet_encoding: str

    @staticmethod
    def can_parse(url: str):
        return url.startswith("vmess://")

    def _parse(self, url: str) -> None:
        self.options = self.config()

        try:
            text = base64_decode(data)
        except:
            print("==================================")
            print(data)
            print("==================================")
            raise
        body = json.loads(text)

        for i in AbsLinkObj.__annotations__.keys():
            if i in body:
                v = dict_pop_str(body, i)
                if v is not None:
                    link[i] = v

        title = dict_pop_str(body, "ps")
        if title:
            link["title"] = title

        if "port" in link:
            link["port"] = int(link["port"])

        if "headerType" in body:
            link["type"] = dict_pop_str(body, "headerType")

        link["class_"] = dict_pop_str(body, "class")

        ltype = dict_pop_str(body, "type")
        if ltype and ltype != "tcp":
            logger.die(f"不支持的 vmess 传输协议: {ltype}")

        if not is_dict_empty(body):
            logger.warning(f"未知 {self.TYPE} 字段: {dump_json(dic, None)} | URL: {url}")

    @property
    def domains(self):
        domain = self.options.get("server", None)
        return [domain] if domain else []

    def _to_json(self) -> Any:
        obj: dict[str, str] = json.loads(json.dumps(self.options))
        for key in obj.keys():
            if key.startswith("_"):
                del obj[key]
        return obj
