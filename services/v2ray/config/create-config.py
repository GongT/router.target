# https://github.com/boypt/vmess2json

import json
from pathlib import Path
from os import environ, path
from sys import stderr
import urllib.parse
import base64


########################
# helpers
########################
def die(msg: str):
    print(msg, file=stderr)
    exit(1)


def note(msg: str):
    print(f"\x1B[2m{msg}\x1B[0m", file=stderr)


def dict_empty(d: dict):
    return len(d) == 0


def take(d: dict, field: str):
    r = d[field]
    del d[field]
    return r


def dump_json(data, indent: int | None = 2):
    return json.dumps(data, indent=indent, ensure_ascii=False, check_circular=False)


########################
# 链接处理
########################
type LinkObj = dict[str, str]


def parse_url(url: str) -> LinkObj:
    vmess = "vmess://"
    ss = "ss://"
    link = {
        "protocol": "",
        "v": "",
        "ps": "",
        "add": "",
        "port": "",
        "id": "",
        "aid": "",
        "net": "",
        "type": "",
        "host": "",
        "path": "",
        "tls": "",
        "verify_cert": False,
    }
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


def parse_ss_url(link: LinkObj, data: str):
    if data.rfind("#") > 0:
        data, _ps = data.split("#", 2)
        link["ps"] = urllib.parse.unquote(_ps)

    if data.find("@") < 0:
        # old style link
        # paddings
        blen = len(data)
        if blen % 4 > 0:
            data += "=" * (4 - blen % 4)

        data = base64.b64decode(data).decode()

        atidx = data.rfind("@")
        method, password = data[:atidx].split(":", 2)
        addr, port = data[atidx + 1 :].split(":", 2)
    else:
        atidx = data.rfind("@")
        addr, port = data[atidx + 1 :].split(":", 2)

        data = data[:atidx]
        blen = len(data)
        if blen % 4 > 0:
            data += "=" * (4 - blen % 4)

        data = base64.b64decode(data).decode()
        method, password = data.split(":", 2)

    link["add"] = addr
    link["port"] = port
    link["aid"] = method
    link["id"] = password
    return link


def parse_vmess_url(link: LinkObj, data: str):
    blen = len(data)
    if blen % 4 > 0:
        data += "=" * (4 - blen % 4)

    text = base64.b64decode(data).decode()
    body = json.loads(text)

    for i in link:
        if i in body:
            v = take(body, i)
            if v is not None:
                link[i] = v

    if "headerType" in body:
        link["type"] = take(body, "headerType")

    if not dict_empty(body):
        note("未知字段: " + dump_json(body, None) + "\nURL: " + text)


########################
# outbound
########################
outbounds = []
used_domains = set()
collection_increament = {}


def create_outbound(protocol: str, collection: str):
    out = make_outbound(protocol)
    outbounds.append(out)

    if collection not in collection_increament:
        collection_increament[collection] = 0
    collection_increament[collection] += 1
    out["tag"] = f"out.{collection}_{collection_increament[collection]}"

    return out


def make_outbound(protocol):
    outbound = {
        # https://www.v2ray.com/chapter_02/01_overview.html#outboundobject
        "sendThrough": "0.0.0.0",
        "protocol": protocol,
        "settings": {},
        # "tag": "",
        "streamSettings": {},
        # "proxySettings": {"tag": "another-outbound-tag"},
        "mux": {"enabled": True, "concurrency": 16},
    }

    if protocol == "vmess":
        outbound["settings"] = {
            # https://www.v2ray.com/chapter_02/protocols/vmess.html#outboundconfigurationobject
            "vnext": []
        }
    elif protocol == "shadowsocks":
        outbound["settings"] = {
            # https://www.v2ray.com/chapter_02/protocols/shadowsocks.html#outboundconfigurationobject
            "servers": []
        }
    else:
        die(f"发现暂不支持的协议: `{protocol}`")
    return outbound


def new_shadowsocks(title: str, link: dict):
    l = dict(link)
    ss_server = {
        "email": take(link, "ps") + "@ss",
        "address": take(link, "add"),
        "method": take(link, "aid"),
        "ota": False,
        "password": take(link, "id"),
        "port": int(take(link, "port")),
    }
    if not dict_empty(l):
        die("未知字段: " + ", ".join(l.keys()) + "\nURL: " + dump_json(link, None))

    create_outbound("shadowsocks", title)["settings"]["servers"].append(ss_server)
    used_domains.add(ss_server["address"])


def new_vmess(title: str, link):
    net = link["net"]

    outbound = create_outbound("vmess", title)

    vnext = {
        "address": link["add"],
        "port": int(link["port"]),
        "users": [
            {
                "email": "user@v2ray.com",
                "id": link["id"],
                "alterId": int(link["aid"]),
                "security": "auto",
            }
        ],
    }
    outbound["settings"]["vnext"].append(vnext)
    used_domains.add(vnext["address"])

    streamSettings = outbound["streamSettings"]

    if link["tls"] == "tls":
        streamSettings["security"] = "tls"
        streamSettings["tlsSettings"] = {"allowInsecure": not link["verify_cert"]}
        if link["host"]:
            streamSettings["tlsSettings"]["serverName"] = link["host"]

    streamSettings["network"] = net
    if net == "kcp":
        streamSettings["kcpSettings"] = {
            "mtu": 1350,
            "tti": 50,
            "uplinkCapacity": 12,
            "downlinkCapacity": 100,
            "congestion": False,
            "readBufferSize": 2,
            "writeBufferSize": 2,
            "header": {"type": link["type"]},
        }
    elif net == "ws":
        streamSettings["wsSettings"] = {
            "connectionReuse": True,
            "path": link["path"],
            "headers": {"Host": link["host"]},
        }
    elif net == "h2":
        streamSettings["httpSettings"] = {"host": [link["host"]], "path": link["path"]}
    elif net == "quic":
        streamSettings["quicSettings"] = {
            "security": link["host"],
            "key": link["path"],
            "header": {"type": link["type"]},
        }
    elif net == "tcp":
        if link["type"] == "http":
            streamSettings["tcpSettings"] = {
                "header": {
                    "type": "http",
                    "request": {
                        "version": "1.1",
                        "method": "GET",
                        "path": [link["path"] or "/"],
                        "headers": {
                            "Host": (
                                link["host"].split(",")
                                if link["host"]
                                else ["www.cloudflare.com", "www.amazon.com"]
                            ),
                            "User-Agent": [
                                "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.75 Safari/537.36",
                                "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36",
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0",
                            ],
                            "Accept": [
                                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
                            ],
                            "Accept-language": ["zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4"],
                            "Accept-Encoding": ["gzip, deflate, br"],
                            "Cache-Control": ["no-cache"],
                            "Pragma": "no-cache",
                        },
                    },
                }
            }
        elif link["type"] == "" or link["type"] == "none":
            streamSettings["tcpSettings"] = {"header": {"type": "none"}}
        else:
            die("未知的tcp类型: " + link["type"])
    else:
        die("未知的net类型: " + net + "\nlink: " + dump_json(link))


########################
# main dispatch for v2ray
########################
def process_line(title: str, line: str):
    ln = parse_url(line)
    if not ln["v"] or int(ln["v"]) != 2:
        note("ignore invalid link: URL: " + dump_json(ln, None))
        return

    if ln["protocol"] == "ss":
        new_shadowsocks(title, ln)
    elif ln["protocol"] == "vmess":
        new_vmess(title, ln)
    else:
        die("程序错误: " + ln["protocol"])


########################
# chinadns config bridge
########################
def parse_domain_list(filename: str):
    domain = []
    file = Path(filename)

    if not file.exists():
        return domain

    content = file.read_text()
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        if "." in line:
            domain.append(f"domain:{line}")
        else:
            domain.append(f"regexp:\\.{line}$")

    return domain


def may_add_domain_rule(rule):
    if len(rule["domain"]) > 0:
        rules.append(rule)


########################
if __name__ != "__main__":
    die("this is a script, not a library.")


STATE_DIR = environ.get("STATE_DIRECTORY", "/var/lib/v2ray")
APP_DATA_DIR = environ.get("AppDataDir", "/data/AppData/router")
OUTPUT_FILE = "/tmp/config.json"
rules = []

####### v2ray
subsDir = Path(STATE_DIR).joinpath("subscriptions")
subsDir.mkdir(0o755, True, True)

balancers = [
    {
        "tag": "balance.all",
        "selector": [],
        "_priority": 65535,
    }
]
for file in subsDir.glob("*.txt"):
    title = path.splitext(file.name)[0]

    balancers.append({"tag": f"balance.{title}", "selector": [f"out.{title}"]})
    balancers[0]["selector"].append(f"out.{title}")

    content = file.read_text()

    for line in content.splitlines():
        line = line.strip()
        process_line(title, line)


####### DOMAINS
DOMAINS_DIR: Path = Path(APP_DATA_DIR).joinpath("dns/dispatch")

may_add_domain_rule(
    {
        "$comment": "oversea sites (proxy)",
        "tag": "rule.oversea",
        "type": "field",
        "_priority": -501,
        "domain": parse_domain_list(
            DOMAINS_DIR.joinpath("force.oversea.list").as_posix()
        ),
        "inboundTag": ["in.http", "in.socks"],
        "balancerTag": "balance.all",
    }
)

cn_domain = (
    []
    + parse_domain_list(DOMAINS_DIR.joinpath("force.china.list").as_posix())
    + parse_domain_list("/var/lib/lists/chnlist.txt")
)
may_add_domain_rule(
    {
        "$comment": "china sites (freedom)",
        "tag": "rule.china",
        "type": "field",
        "_priority": -500,
        "domain": list(set(cn_domain)),
        "inboundTag": ["in.http", "in.socks"],
        "outboundTag": "out.direct",
    }
)
may_add_domain_rule(
    {
        "$comment": "blacklist sites (blackhole)",
        "tag": "rule.blacklist",
        "type": "field",
        "_priority": -1000,
        "domain": parse_domain_list(DOMAINS_DIR.joinpath("blacklist.list").as_posix()),
        "inboundTag": ["in.http", "in.socks"],
        "outboundTag": "out.deny",
    }
)


####### write out
r = dump_json(
    {
        "dns": {
            "servers": [
                {
                    "_priority": -1,
                    "address": "::1",
                    "port": 8806,
                    "domains": list(used_domains),
                }
            ]
        },
        "outbounds": outbounds,
        "routing": {
            "balancers": balancers,
            "rules": rules,
        },
    }
)

with open(OUTPUT_FILE, "wt") as f:
    f.write(r)
