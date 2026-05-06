import json
import urllib.parse
from typing import Any, TypedDict

from ....target import dump_json, logger
from ..data_types.outbound import Outbound
from ..functions import array_dict_pop, is_dict_empty


class TrojanOutbound(Outbound):
    TYPE = "trojan"

    class config(TypedDict, total=False):
        # https://sing-box.sagernet.org/zh/configuration/outbound/trojan/
        server: str
        server_port: int

        password: str

        network: str
        udp: bool

    @staticmethod
    def can_parse(url: str):
        return url.startswith("trojan://")

    def _parse(self, url: str) -> None:
        self.options = self.config()

        info = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(info.query)
        self._set_title(urllib.parse.unquote(info.fragment))
        # print(f"test: {qs} | {url}")

        if info.hostname:
            self.options["server"] = info.hostname
        if info.port:
            self.options["server_port"] = info.port
        if info.username:
            self.options["password"] = info.username

        insecure = (
            array_dict_pop(qs, "allowInsecure")
            or array_dict_pop(qs, "allow_insecure")
            or array_dict_pop(qs, "insecure")
        )
        if insecure is not None:
            self.tls["insecure"] = bool(int(insecure))

        udp = array_dict_pop(qs, "udp")
        # if udp is not None:
        #     self.options["udp"] = bool(udp)

        peer = array_dict_pop(qs, "peer")
        sni = array_dict_pop(qs, "sni")
        if sni is not None:
            self.tls["server_name"] = sni
        elif peer is not None:
            self.tls["server_name"] = peer

        ltype = array_dict_pop(qs, "type")
        if ltype and ltype != "tcp" and ltype != "udp":
            raise ValueError(f"不支持的传输协议: {ltype}")
        # self.options["network"] = ltype if ltype else "tcp"

        if not is_dict_empty(qs):
            dic = {k: v[0] for k, v in qs.items()}
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
