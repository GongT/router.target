########################
# 链接处理
########################
import json
from typing import cast

from .data_types.basic import TlsFields

from .subscription_url import AbsLinkObj
from .data_types.vmess import VMessOutbound, VMessTransport
from .data_types.shadowsocks import ShadowSocksOutbound
from .functions import die, dump_json, note, dict_pop, is_dict_empty

import urllib.parse
import base64


def create_transport_object(
    ln: AbsLinkObj,
) -> ShadowSocksOutbound | VMessOutbound | None:
    protocol = dict_pop(ln, "protocol")
    r = None
    if protocol == "ss":
        r = transport_make_shadowsocks(ln)
    elif protocol == "vmess":
        version = int(ln.get('v', 0))
        if version != 2:
            note("ignore invalid link: URL: " + dump_json(ln, None))
            return
        ln.pop('v', None)
        
        r = transport_make_vmess(ln)
    else:
        die("程序错误: " + protocol)

    ln.pop("remark", None)
    ln.pop("class_", None)

    if not is_dict_empty(ln):
        note("未知连接信息字段: " + ", ".join(ln.keys()) + "\nURL: " + dump_json(ln, None))

    return r


def transport_make_shadowsocks(link: AbsLinkObj) -> ShadowSocksOutbound:
    ss_server = ShadowSocksOutbound(
        type="shadowsocks",
        tag=link.pop("ps"),
        server=link.pop("add"),
        server_port=int(link.pop("port")),
        method=link.pop("method"),
        password=link.pop("password"),
    )
    return ss_server


def transport_make_vmess(link: AbsLinkObj) -> VMessOutbound | None:
    tagName = link.get("ps")
    r = VMessOutbound(
        type="vmess",
        tag=link.pop("ps"),
        server=link.pop("add"),
        server_port=int(link.pop("port")),
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
        note(f"unsupported transport: KCP ({tagName})")
        return None
    elif net == "ws":
        r["transport"] = VMessTransport(
            type="ws",
            path=path,
            early_data_header_name="Sec-WebSocket-Protocol",
        )
        if sn:
            r["transport"]["headers"] = {"Host": sn}
    elif net == "h2":
        note(f"not implemented transport: H2 ({tagName})")
        return None
    elif net == "quic":
        note(f"not implemented transport: QUIC ({tagName})")
        return None
    elif net == "tcp":
        if transport == "http":
            note(f"not implemented transport: HTTP ({tagName})")
            return None
        elif transport == "" or transport == "none":
            r["network"] = "tcp"
        else:
            die("未知的tcp类型: " + transport)
    else:
        die(f"未知的net类型: {net} ({tagName})")

    return r
