from typing import TypedDict

from .basic import (
    BaseOutbound,
    DialFields,
    MultiplexFields,
    TlsFields,
)

type HeadersMap = dict[str, str]


class V2RayTransport(BaseOutbound, DialFields, TypedDict, total=False):
    # https://sing-box.sagernet.org/zh/configuration/shared/v2ray-transport/
    type: str

    host: list[str] | str

    # HTTP
    # type: "http",
    # host: list[str]
    path: str
    method: str
    headers: HeadersMap
    idle_timeout: str
    ping_timeout: str

    # WebSocket
    # type: "ws",
    path: str
    headers: HeadersMap
    max_early_data: int
    early_data_header_name: str

    # QUIC

    # gRPC
    # type: "grpc",
    service_name: str
    idle_timeout: str
    ping_timeout: str
    permit_without_stream: bool

    # HTTPUpgrade
    # type: "httpupgrade"
    # host: str
    path: str
    headers: HeadersMap


class VMessOutbound(TypedDict, total=False):
    # https://sing-box.sagernet.org/zh/configuration/outbound/vmess/
    type: str
    tag: str

    server: str
    server_port: int

    uuid: str
    security: str
    alter_id: int
    global_padding: bool
    authenticated_length: bool
    network: str
    tls: TlsFields
    packet_encoding: str
    multiplex: MultiplexFields
    transport: V2RayTransport
