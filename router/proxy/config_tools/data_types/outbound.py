from abc import ABC, abstractmethod
from typing import Any, Protocol

from ..functions import array_dict_pop, dict_pop
from .basic import DialFields, TlsFields, V2RayTransportFields


class outbound_is_typed(Protocol):
    TYPE: str


class Outbound(ABC, outbound_is_typed):
    def __init__(self, url: str) -> None:
        self._category = ""
        self._url = url
        self._tls = None
        self._dial = None
        self._transport = None

        if not url:
            raise ValueError("invalid url, must be string and not empty")

        self._parse(url)

    @abstractmethod
    def _parse(self, url: str) -> None:
        pass

    @abstractmethod
    def _to_json(self) -> dict:
        pass

    def to_json(self) -> dict:
        options: dict[str, Any] = {
            "type": self.TYPE,
            "tag": "",
        }

        body = self._to_json()
        if not isinstance(body, dict):
            raise ValueError(f"invalid _to_json result: {body}")
        options.update(body)

        if self._tls:
            options["tls"] = self._tls
        if self._dial:
            options.update(self._dial)
        if self._transport:
            if not self._transport.get("type", None):
                raise ValueError("已设置v2ray传输协议，但type字段为空")
            options["transport"] = self._transport

        options["tag"] = self.tag
        return options

    @staticmethod
    @abstractmethod
    def can_parse(url: str) -> bool:
        pass

    @property
    def url(self) -> str:
        return self._url

    def _common_tls_options(self, options: dict):
        insecure = (
            array_dict_pop(options, "allowInsecure")
            or array_dict_pop(options, "allow_insecure")
            or array_dict_pop(options, "insecure")
        )
        if insecure is not None:
            self.tls["insecure"] = bool(int(insecure))

        peer = array_dict_pop(options, "peer")
        sni = array_dict_pop(options, "sni")
        if sni is not None:
            self.tls["server_name"] = sni
        elif peer is not None:
            self.tls["server_name"] = peer

        disable_sni = array_dict_pop(options, "disable_sni")
        if disable_sni is not None:
            self.tls["disable_sni"] = bool(int(disable_sni))

        alpn = dict_pop(options, "alpn", list)
        if alpn is not None:
            self.tls["alpn"] = alpn

    ### tag: 写入配置文件的标签
    @property
    def tag(self) -> str:
        r = ""
        if self._category:
            r += f"[{self._category}] "

        if not self._title:
            raise RuntimeError("missing title field")

        r += self._title

        return r

    def set_category(self, name: str):
        if self._category:
            raise RuntimeError(
                f"category already set to {self._category}, can not set to {name}"
            )

        self._category = name

    ### title: URL中的原始标题，即 fragment
    # @property
    # def title(self) -> str:
    #     return self._title
    def _set_title(self, title: str):
        self._title = title

    @property
    def tls(self):
        if self._tls is None:
            self._tls = TlsFields(enabled=True)
        return self._tls

    @property
    def dial(self):
        if self._dial is None:
            self._dial = DialFields()
        return self._dial

    @property
    def transport(self):
        if self._transport is None:
            self._transport = V2RayTransportFields()
        return self._transport

    #####
    @property
    @abstractmethod
    def domains(self) -> list[str]:
        pass
