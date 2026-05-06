import json
import urllib.parse
from typing import Any, TypedDict

from ....target import dump_json, logger
from ..data_types.outbound import Outbound
from ..functions import array_dict_pop, is_dict_empty


class TuicOutbound(Outbound):
    TYPE = "tuic"

    class config(TypedDict, total=False):
        # https://sing-box.sagernet.org/zh/configuration/outbound/tuic/
        server: str
        server_port: int
        uuid: str
        password: str
        congestion_control: str
        udp_relay_mode: str
        udp_over_stream: bool
        zero_rtt_handshake: bool
        heartbeat: str
        network: str

    @staticmethod
    def can_parse(url: str):
        return url.startswith("tuic://")

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
            self.options["uuid"] = info.username
        if info.password:
            self.options["password"] = info.password

        self._common_tls_options(qs)

        ltype = array_dict_pop(qs, "type")
        if ltype and ltype != "tcp" and ltype != "udp":
            raise ValueError(f"不支持的传输协议: {ltype}")
        # self.options["network"] = ltype if ltype else "tcp"

        congestion_control = array_dict_pop(qs, "congestion-control")
        if congestion_control is not None:
            self.options["congestion_control"] = congestion_control

        udp_relay_mode = array_dict_pop(qs, "udp_relay_mode")
        if udp_relay_mode is not None:
            self.options["udp_relay_mode"] = udp_relay_mode

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
