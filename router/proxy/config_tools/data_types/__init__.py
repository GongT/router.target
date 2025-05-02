from .shadowsocks import ShadowSocksOutbound
from .vmess import V2RayTransport

Outbound = ShadowSocksOutbound | V2RayTransport
