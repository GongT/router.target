########################
# 链接处理
########################
from .data_types.trojan import TrojanOutbound

from .data_types.basic import TlsFields

from .subscription_url import AbsLinkObj
from .data_types.vmess import VMessOutbound, V2RayTransport
from .data_types.shadowsocks import ShadowSocksOutbound
from .functions import dict_pop, is_dict_empty
from ...target import logger, dump_json

def create_transport_object(
    ln: AbsLinkObj,
) -> ShadowSocksOutbound | VMessOutbound | TrojanOutbound | None:
    protocol = dict_pop(ln, "protocol")
    r = None
    if protocol == "ss":
        r = transport_make_shadowsocks(ln)
    elif protocol == "vmess":
        version = int(ln.get("v", 0))
        if version != 2:
            logger.dim("ignore invalid link: URL: " + dump_json(ln, None))
            return
        ln.pop("v", None)

        r = transport_make_vmess(ln)
    elif protocol == "trojan":
        r = transport_make_trojan(ln)
    else:
        logger.die("程序错误: " + protocol)

    ln.pop("remark", None)
    ln.pop("class_", None)

    if not is_dict_empty(ln):
        logger.dim(
            "未知连接信息字段: "
            + ", ".join(ln.keys())
            + "\nURL: "
            + dump_json(ln, None)
        )

    return r


def transport_make_shadowsocks(link: AbsLinkObj) -> ShadowSocksOutbound:
    ss_server = ShadowSocksOutbound(
        type="shadowsocks",
        tag=link.pop("title"),
        server=link.pop("add"),
        server_port=link.pop("port"),
        method=link.pop("method"),
        password=link.pop("password"),
    )
    return ss_server


def transport_make_vmess(link: AbsLinkObj) -> VMessOutbound | None:
    tagName = link.get("title")
    r = VMessOutbound(
        type="vmess",
        tag=link.pop("title"),
        server=link.pop("add"),
        server_port=link.pop("port"),
        alter_id=int(link.pop("aid")),
        uuid=link.pop("id"),
        security="auto",
        authenticated_length=True,
        packet_encoding="xudp",
    )

    sn = link.pop("host", None)
    verify_cert = link.pop("verify_cert", False)
    net = link.pop("net")
    tls = link.pop("tls", "")
    path = link.pop("path", "/")
    transport = link.pop("type", "none")

    if tls == "tls":
        r["tls"] = TlsFields(
            enabled=True,
            insecure=not verify_cert,
        )
        if sn:
            r["tls"]["server_name"] = sn

    if net == "kcp":
        logger.dim(f"unsupported transport: KCP ({tagName})")
        return None
    elif net == "ws":
        r["transport"] = V2RayTransport(
            type="ws",
            path=path,
            early_data_header_name="Sec-WebSocket-Protocol",
        )
        if sn:
            r["transport"]["headers"] = {"Host": sn}
    elif net == "h2":
        logger.dim(f"not implemented transport: H2 ({tagName})")
        return None
    elif net == "quic":
        logger.dim(f"not implemented transport: QUIC ({tagName})")
        return None
    elif net == "tcp":
        if transport == "http":
            logger.dim(f"not implemented transport: HTTP ({tagName})")
            return None
        elif transport == "" or transport == "none":
            pass
        else:
            die("未知的tcp类型: " + transport)
    else:
        die(f"未知的net类型: {net} ({tagName})")

    return r


def transport_make_trojan(link: AbsLinkObj) -> TrojanOutbound | None:
    r = TrojanOutbound(
        type="trojan",
        tag=link.pop("title"),
        server=link.pop("server"),
        server_port=link.pop("port"),
        password=link.pop("password"),
    )
    
    tls_insecure = link.pop("tls_insecure")
    tls_server_name = link.pop("tls_server_name", "")
    udp = link.pop("udp")
    
    if tls_insecure or tls_server_name:
        r["tls"] = TlsFields(
            enabled=True,
            insecure=tls_insecure,
        )
        if tls_server_name:
            r["tls"]["server_name"] = tls_server_name

    return r
