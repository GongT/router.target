import ipaddress as ipa
import json
from operator import add
from os import environ
from pathlib import Path
from pprint import pprint
import sys
import subprocess
from typing import TypedDict

__dirname = Path(__file__).parent.absolute()


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def exec_result(*cmds):
    result = subprocess.run(cmds, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def exec_mute(*cmds):
    result = subprocess.run(
        cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    print(f"$ {' '.join(cmds)}")
    if result.returncode != 0:
        die(f"{result.stdout}\n\n$ {' '.join(cmds)}\ncommand failed!")


def exec_json(*cmds):
    result = subprocess.run(cmds, stdout=subprocess.PIPE, stderr=sys.stderr, text=True)
    if result.returncode != 0:
        die(f"{result.stderr}\n\n$ {' '.join(cmds)}\ncommand failed")
    return json.loads(result.stdout)


class Address(TypedDict):
    family: str
    local: str
    prefixlen: int
    scope: str
    label: str
    valid_life_time: int
    preferred_life_time: int


class Interface(TypedDict):
    ifindex: int
    ifname: str
    flags: list[str]
    mtu: int
    qdisc: str
    operstate: str
    group: str
    txqlen: int
    link_type: str
    addr_info: list[Address]


class Route(TypedDict):
    dst: str
    dev: str
    protocol: str
    scope: str
    gateway: str
    prefsrc: str
    flags: list[str]
    pref: str
    metric: int
    expires: int


def is_local_4(addr: Address) -> bool:
    return addr["family"] == "inet" and addr["prefixlen"] == 32


def is_local_6(addr: Address) -> bool:
    return addr["family"] == "inet6" and addr["prefixlen"] == 128


def detect_overlap(network1: str, network2: str) -> bool:
    return ipa.ip_network(network1).overlaps(ipa.ip_network(network2))


def calculate_network_union(network1, network2):
    # 将输入转换为ip_network对象
    net1 = ipa.ip_network(network1, strict=False)
    net2 = ipa.ip_network(network2, strict=False)

    # 找到两个网络的最小起始IP和最大结束IP
    start_ip = min(net1.network_address, net2.network_address)
    end_ip = max(net1.broadcast_address, net2.broadcast_address)

    # 使用 summarize_address_range 找到覆盖整个范围的最小网络
    union_networks = list(ipa.summarize_address_range(start_ip, end_ip))

    return union_networks


if __name__ == "__main__":
    STATE_DIRECTORY = Path(environ.get("STATE_DIRECTORY", "/var/lib/ipchange"))
    STATE_DIRECTORY.mkdir(parents=True, exist_ok=True)

    address = exec_json("ip", "--json", "addr")
    ifaces: list[Interface] = []
    for item in address:
        iface = Interface(item)
        iface["addr_info"] = list(map(Address, iface["addr_info"]))
        ifaces.append(iface)

    routes: list[Route] = [
        *exec_json("ip", "-4", "--json", "route"),
        *exec_json("ip", "-6", "--json", "route"),
    ]
    routes = list(map(Route, routes))

    nft = {
        "wan": {
            "4": [],
            "6": [],
        },
        "lan": {
            "4": [],
            "6": [],
        },
        "localhost": {
            "4": [],
            "6": [],
        },
    }

    for iface in ifaces:
        print(iface["ifname"])
        for addr in iface["addr_info"]:
            print("\t", addr["family"], addr["prefixlen"], addr["local"])
            if is_local_4(addr):
                nft["localhost"]["4"].append(addr["local"])
                if iface["ifname"] == "wan" or iface["ifname"] == "ppp0":
                    nft["wan"]["4"].append(addr["local"])

            elif is_local_6(addr):
                nft["localhost"]["6"].append(addr["local"])
                if iface["ifname"] == "wan" or iface["ifname"] == "ppp0":
                    nft["wan"]["6"].append(addr["local"])

    for route in routes:
        if route["dev"] == "wan" or route["dev"] == "ppp0":
            continue

        if "/" in route["dst"]:
            if ":" in route["dst"]:
                nft["lan"]["6"].append(route["dst"])
            else:
                nft["lan"]["4"].append(route["dst"])

    for name, reg in nft.items():
        for family, ips in reg.items():
            file = STATE_DIRECTORY.joinpath(f"ipset-{name}{family}.nft")
            print(f"writing {file.name} with {len(ips)} elements.")
            if len(ips) == 0:
                file.write_text("")
            else:
                r = "elements = {"
                for ip in ips:
                    r += f"\t{ip},\n"
                r += "}"
                file.write_text(r)

    entry_file = __dirname.joinpath("ipsets.nft").as_posix()
    exec_mute(
        "nft",
        "--includepath",
        __dirname.as_posix(),
        "-f",
        entry_file,
    )

    def get_elements(set_name: str):
        json = exec_json(
            "nft",
            "--json",
            "list",
            "set",
            "inet",
            "router",
            set_name,
        )
        ret = []
        for m in json["nftables"][1]["set"]["elem"]:
            if type(m) == str:
                ret.append(m)
            else:
                ret.append(f"{m['prefix']['addr']}/{m['prefix']['len']}")
        return ret

    inner_file = __dirname.joinpath("ipsets-inner.nft").as_posix()
    sync_file = Path("/var/lib/nftables/router/ipchange.nft")
    if not sync_file.exists():
        sync_file.parent.mkdir(parents=True, exist_ok=True)

    sync_file.write_text(f'include "{inner_file}"\n')

    nft["lan"]["4"] = get_elements("lan4")
    nft["lan"]["6"] = get_elements("lan6")
    did_change = False
    for name, reg in nft.items():
        for family, ips in reg.items():
            file = Path(f"/etc/firewalld/ipsets/{name}{family}.xml")
            print(f"writing {file.name} with {len(ips)} elements.")

            inet = "inet" if family == "4" else "inet6"
            hash_type = "net" if name == "lan" else "ip"
            r = f"""<?xml version="1.0" encoding="utf-8"?>
<ipset type="hash:{hash_type}">
    <option name="family" value="{inet}"/>
"""
            for ip in ips:
                r += f"\t<entry>{ip}</entry>\n"

            r += "</ipset>\n"

            original = file.read_text()
            if original != r:
                file.write_text(r)
                did_change = True

    firewalld_running = exec_result("systemctl", "--quiet", "is-active", "firewalld")
    if firewalld_running:
        if did_change:
            succ = exec_result("firewall-cmd", "--reload")

            if succ:
                print("firewalld reloaded.")
            else:
                print("firewalld reload failed!")
        else:
            print("no changes, not reloading firewalld.")
    else:
        print("firewalld not running, skipping reload.")
