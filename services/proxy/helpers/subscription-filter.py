# https://github.com/boypt/vmess2json

import json
from pathlib import Path
from os import environ, path
from sys import stderr
import idna
import traceback
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
# outbound
########################
outbounds = []
outboundTitles = []
used_domains = set()
collection_increament = {}


def handle_config_data(provider: str, data):
    obs = data["outbounds"]
    for ob in obs:
        if block_by_tag(ob["tag"]):
            print("ignore tag: " + ob["tag"])
            continue

        ob["tag"] = f"[{provider}] {ob["tag"]}".replace("\n", "").replace("\r", "")

        outboundTitles.append(ob["tag"])
        outbounds.append(ob)
        used_domains.add(ob["server"])


def block_by_tag(name: str) -> bool:
    blnames = [
        "剩余",
        "到期",
        "官网",
        "续费",
        "过期",
    ]
    for bln in blnames:
        if bln in name:
            return True
    return False


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
        try:
            line = idna.decode(line)
        except:
            print("invalid domain: " + line)
            traceback.print_exc()
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


STATE_DIR = environ.get("STATE_DIRECTORY", "/var/lib/proxy")
APP_DATA_DIR = environ.get("AppDataDir", default="/data/AppData/router")
OUTPUT_FILE = environ.get("CONFIG_FILE", "/tmp/config.json")
rules = []

subsDir = Path(STATE_DIR).joinpath("tmp/subscriptions")

for file in subsDir.glob("*.json"):
    try:
        print("processing: " + file.as_posix())
        provider = path.splitext(file.name)[0]
        content = file.read_text()

        handle_config_data(provider, json.loads(content))
    except:
        print("FILE: " + file.as_posix())
        raise

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
# may_add_domain_rule(
#     {
#         "$comment": "china sites (freedom)",
#         "tag": "rule.china",
#         "type": "field",
#         "_priority": -500,
#         "domain": list(set(cn_domain)),
#         # "domain": list(),
#         "inboundTag": ["in.http", "in.socks"],
#         "outboundTag": "out.direct",
#     }
# )
# may_add_domain_rule(
#     {
#         "$comment": "blacklist sites (blackhole)",
#         "tag": "rule.blacklist",
#         "type": "field",
#         "_priority": -1000,
#         "domain": parse_domain_list(DOMAINS_DIR.joinpath("blacklist.list").as_posix()),
#         "inboundTag": ["in.http", "in.socks"],
#         "outboundTag": "out.deny",
#     }
# )


####### write out
if len(outbounds) == 0:
    die("no outbound exists!!")


r = dump_json(
    {
        "dns": {
            "servers": [
                {
                    "tag": "dns-direct",
                    "address": "tcp://[::1]:5306",
                    "detour": "direct",
                },
                {"tag": "dns-local", "address": "local", "detour": "direct"},
                {"tag": "dns-block", "address": "rcode://success"},
            ],
            "rules": [
                {
                    "domain": list(used_domains),
                    "server": "dns-direct",
                }
            ],
            "final": "dns-local",
            "static_ips": {
                # "sky.rethinkdns.com": [
                #     "104.17.148.22",
                #     "104.17.147.22",
                #     "2606:4700:3030::ac43:d6f6",
                #     "2606:4700:3030::6815:533e",
                #     "172.67.214.246",
                #     "104.21.83.62",
                # ]
            },
        },
        "outbounds": [
            {
                "type": "selector",
                "tag": "select",
                "outbounds": ["auto", *outboundTitles],
                "default": "auto",
                "interrupt_exist_connections": True,
            },
            {"type": "urltest", "tag": "auto", "outbounds": outboundTitles},
            *outbounds,
        ],
        "route": {
            "rules": rules,
            "final": "select",
            "auto_detect_interface": True,
            # "override_android_vpn": True,
        },
        "experimental": {
            "cache_file": {"enabled": True, "path": "clash.db"},
            "clash_api": {
                "external_controller": "0.0.0.0:3276",
                "external_ui": "webui",
                "secret": "123456",
            },
        },
    }
)

print(f"write to file: {OUTPUT_FILE}")
with open(OUTPUT_FILE, "wt") as f:
    f.write(r)
