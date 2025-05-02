from typing import TypedDict

from .vmess import V2RayTransport

from .basic import (
    MultiplexFields,
    TlsFields,
)

type HeadersMap = dict[str, str]


class TrojanOutbound(TypedDict, total=False):
    # https://sing-box.sagernet.org/configuration/outbound/trojan/
    type: str
    tag: str

    server: str
    server_port: int

    password: str
    network: str

    tls: TlsFields
    multiplex: MultiplexFields
    transport: V2RayTransport
