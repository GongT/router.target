from typing import TypedDict


class DialFields(TypedDict, total=False):
    # https://sing-box.sagernet.org/zh/configuration/shared/dial/
    detour: str
    bind_interface: str
    inet4_bind_address: str
    inet6_bind_address: str
    routing_mark: int
    reuse_addr: bool
    connect_timeout: str
    tcp_fast_open: bool
    tcp_multi_path: bool
    udp_fragment: bool
    domain_resolver: str
    network_strategy: str
    network_type: list[str]
    fallback_network_type: list[str]
    fallback_delay: str


class TlsEchFields(TypedDict, total=False):
    enabled: bool
    pq_signature_schemes_enabled: bool
    dynamic_record_sizing_disabled: bool
    config: list[str]
    config_path: str


class TlsUtlsFields(TypedDict, total=False):
    enabled: bool
    fingerprint: str


class TlsRealityFields(TypedDict, total=False):
    enabled: bool
    public_key: str
    short_id: str


class TlsFields(TypedDict, total=False):
    # https://sing-box.sagernet.org/zh/configuration/shared/tls/
    enabled: bool
    disable_sni: bool
    server_name: str
    insecure: bool
    alpn: list[str]
    min_version: str
    max_version: str
    cipher_suites: list[str]
    certificate: list[str]
    certificate_path: str
    ech: TlsEchFields
    utls: TlsUtlsFields
    reality: TlsRealityFields


class TCPBrutalFields(TypedDict, total=False):
    # https://sing-box.sagernet.org/zh/configuration/shared/tcp-brutal/
    enabled: bool
    up_mbps: int
    down_mbps: int


class MultiplexFields(TypedDict, total=False):
    # https://sing-box.sagernet.org/zh/configuration/shared/multiplex/
    enabled: bool
    protocol: str
    max_connections: int
    min_streams: int
    max_streams: int
    padding: bool
    brutal: TCPBrutalFields


class UDPOverTCP(TypedDict, total=False):
    # https://sing-box.sagernet.org/zh/configuration/shared/udp-over-tcp/
    enabled: bool
    version: int

class BaseOutbound(TypedDict, total=False):
    _provider: str
