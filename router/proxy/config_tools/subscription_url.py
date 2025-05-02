import json
import urllib.parse
from typing import TypedDict

from ...target import dump_json, logger
from .functions import base64_decode, dict_pop, is_dict_empty


class AbsLinkObj(TypedDict):
    protocol: str
    title: str
    v: str

    # platform spec
    remark: str
    class_: str

    # vmess
    # ps: str  # 别名
    add: str  # ip地址
    port: int  # 端口
    id: str  # uuid
    aid: str  # alterid
    net: str  # 传输协议
    type: str  # 伪装类型
    host: str  # http header参数
    tls: str  # 底层传输安全

    # shadowsocks
    path: str
    verify_cert: bool
    method: str
    password: str

    # trojan
    server: str
    port: int
    password: str
    tls_insecure: bool
    tls_server_name: str
    udp: bool


def parse_url(url: str):
    vmess = "vmess://"
    ss = "ss://"
    trojan = "trojan://"
    link: AbsLinkObj = {}
    if url.startswith(ss):
        link["protocol"] = "ss"
        parse_ss_url(link, url[len(ss) :])
    elif url.startswith(vmess):
        link["protocol"] = "vmess"
        parse_vmess_url(link, url[len(vmess) :])
    elif url.startswith(trojan):
        link["protocol"] = "trojan"
        parse_trojan_url(link, url[len(trojan) :])
    else:
        logger.error(
            "ERROR: This script supports only vmess://(N/NG), ss://, and trojan:// links\nURL: "
            + url
        )
        return None

    return link


def parse_ss_url(link: AbsLinkObj, data: str):
    if data.rfind("#") > 0:
        data, _ps = data.split("#", 2)
        link["title"] = urllib.parse.unquote(_ps)

    if data.find("@") < 0:
        # 老式链接，对整个url进行base64
        data = base64_decode(data)

        atidx = data.rfind("@")
        method, password = data[:atidx].split(":", 2)
        addr, port = data[atidx + 1 :].split(":", 2)
    else:
        # 现在的链接只有认证部分进行base64
        atidx = data.rfind("@")
        addr, port = data[atidx + 1 :].split(":", 2)

        data = base64_decode(data[:atidx])
        method, password = data.split(":", 2)

    link["add"] = addr
    link["port"] = int(port)
    link["method"] = method
    link["password"] = password


def parse_vmess_url(link: AbsLinkObj, data: str):
    try:
        text = base64_decode(data)
    except:
        print("==================================")
        print(data)
        print("==================================")
        raise
    body = json.loads(text)

    for i in AbsLinkObj.__annotations__.keys():
        if i in body:
            v = dict_pop(body, i)
            if v is not None:
                link[i] = v

    title = dict_pop(body, "ps")
    if title:
        link["title"] = title

    if "port" in link:
        link["port"] = int(link["port"])

    if "headerType" in body:
        link["type"] = dict_pop(body, "headerType")

    link["class_"] = dict_pop(body, "class")

    if not is_dict_empty(body):
        logger.dim("未知vmess url字段: " + dump_json(body, None) + "\nURL: " + text)


def parse_trojan_url(link: AbsLinkObj, data: str):
    url = urllib.parse.urlparse(data)
    qs = urllib.parse.parse_qs(url.query)
    link["title"] = urllib.parse.unquote(url.fragment)

    if url.path and not url.netloc:
        url = urllib.parse.urlparse("trojan://" + url.path)

    if url.hostname:
        link["server"] = url.hostname
    if url.port:
        link["port"] = url.port
    if url.username:
        link["password"] = url.username

    insecure = qs.get("allowInsecure")
    if insecure is not None:
        link["tls_insecure"] = bool(int(insecure[0]))

    link["udp"] = bool(qs.get("udp", [None])[0])
    # link['xxxx'] = qs.get('peer', [None])[0]

    sni = qs.get("sni")
    if sni is not None:
        link["tls_server_name"] = sni[0]

    peer = qs.get("peer")
