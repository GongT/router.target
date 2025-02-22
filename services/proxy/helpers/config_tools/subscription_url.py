import json
from .functions import base64_decode, is_dict_empty, die, dump_json, note, dict_pop

import urllib.parse
import base64
from typing import TypedDict


class AbsLinkObj(TypedDict, total=False):
    protocol: str
    v: str
    
    # platform spec
    remark: str
    class_: str

    # vmess
    ps: str  # 别名
    add: str  # ip地址
    port: str  # 端口
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


def parse_url(url: str):
    vmess = "vmess://"
    ss = "ss://"
    link = AbsLinkObj()
    if url.startswith(ss):
        link["protocol"] = "ss"
        parse_ss_url(link, url[len(ss) :])
    elif url.startswith(vmess):
        link["protocol"] = "vmess"
        parse_vmess_url(link, url[len(vmess) :])
    else:
        die(
            "ERROR: This script supports only vmess://(N/NG) and ss:// links\nURL: "
            + url
        )

    return link


def parse_ss_url(link: AbsLinkObj, data: str):
    if data.rfind("#") > 0:
        data, _ps = data.split("#", 2)
        link["ps"] = urllib.parse.unquote(_ps)

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
    link["port"] = port
    link["method"] = method
    link["password"] = password
    return link


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

    if "headerType" in body:
        link["type"] = dict_pop(body, "headerType")
        
    link['class_'] = dict_pop(body, 'class')

    if not is_dict_empty(body):
        note("未知vmess url字段: " + dump_json(body, None) + "\nURL: " + text)
