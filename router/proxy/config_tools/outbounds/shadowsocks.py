import json
import urllib.parse
from typing import Any, TypedDict

from ....target import dump_json, logger
from ..data_types.basic import UDPOverTCP
from ..data_types.outbound import Outbound
from ..functions import array_dict_pop, base64_decode, is_dict_empty


class ShadowsocksOutbound(Outbound):
    TYPE = "shadowsocks"

    class config(TypedDict, total=False):
        # https://sing-box.sagernet.org/zh/configuration/outbound/shadowsocks/
        server: str
        server_port: int
        method: str
        password: str
        plugin: str
        plugin_opts: str
        network: str
        udp_over_tcp: bool | UDPOverTCP

    @staticmethod
    def can_parse(url: str):
        return url.startswith("ss://")

    def _parse(self, url: str) -> None:
        self.options = self.config()

        url = url[5:]  # ss://
        if url.rfind("#") > 0:
            url, _ps = url.split("#", 2)
            self._set_title(urllib.parse.unquote(_ps))

        if url.find("@") < 0:
            # 老式链接，对整个url进行base64
            url = base64_decode(url)

            atidx = url.rfind("@")
            method, password = url[:atidx].split(":", 2)
            addr, port_and_path = url[atidx + 1 :].split(":", 2)
        else:
            # 现在的链接只有认证部分进行base64
            atidx = url.rfind("@")
            addr, port_and_path = url[atidx + 1 :].split(":", 2)

            url = base64_decode(url[:atidx])
            method, password = url.split(":", 2)

        if '/' in port_and_path:
            port, pathname = port_and_path.split("/", 2)
        else:
            port = port_and_path
            pathname = ''

        # query string
        query = ''
        if '?' in pathname:
            pathname, query = pathname.split("?", 2)

        self.options["server"] = addr
        self.options["server_port"] = int(port)
        self.options["method"] = method
        self.options["password"] = password

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
