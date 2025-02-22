from typing import TypedDict

from .basic import BaseOutbound, DialFields, MultiplexFields, UDPOverTCP


class ShadowSocksOutbound(BaseOutbound, DialFields, TypedDict, total=False):
    type: str
    tag: str
    server: str
    server_port: int
    method: str
    password: str
    plugin: str
    plugin_opts: str
    network: str
    udp_over_tcp: bool | UDPOverTCP
    multiplex: MultiplexFields
