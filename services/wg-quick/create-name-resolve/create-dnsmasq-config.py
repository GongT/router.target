import ipaddress
import sys
from os import environ
from pathlib import Path
import netifaces as ni

from router.target import tools, write_if_change

ifname = sys.argv[1] if len(sys.argv) > 1 else None
if ifname is None:
    print("Usage: create-dnsmasq-config.py <config-name>")
    sys.exit(1)

config_file = Path("/etc/wireguard").joinpath(f"{ifname}.conf")
state_directory = environ.get("STATE_DIRECTORY", "/var/lib/wireguard")
output_file = Path(state_directory).joinpath(f"hosts/{ifname}")

print(f"reading config from {config_file}")
config = tools.wireguard.read_wireguard_config(config_file)

domain = config.get("# Domain")
print("domain = ", domain)

if not domain:
    print("No domain specified in config, skipping dnsmasq config generation")
    sys.exit(0)


def toArray(value: str | None):
    r: list[str] = []
    if value is None:
        return r

    r = value.split(",")
    return [x.strip() for x in r]


def sanity_ip(ip_or_net: str):
    if "/" in ip_or_net:
        network = ipaddress.ip_network(ip_or_net, strict=False)
        if network.num_addresses > 1:
            return None
        return ip_or_net.split("/")[0]
    else:
        return ip_or_net


output: dict[str, set[str]] = {}

hostnames = toArray(config.get("# Hostname"))
ip_addr = None
try:
    addrs = ni.ifaddresses(ifname)
    print(f"{ifname} IP: {addrs}")
except Exception as e:
    print(f"Could not get IP for {ifname}: {e}")

for peer in config.peers():
    ip_addrs = toArray(peer.get("AllowedIPs"))
    hostnames = toArray(peer.get("# Hostname"))
    print("peer: ", ip_addrs, hostnames)

    if not ip_addrs or not hostnames:
        continue

    ip_addrs = [sanity_ip(ip) for ip in ip_addrs]
    ip_addrs = [ip for ip in ip_addrs if ip is not None]
    if not ip_addrs:
        print("No valid IP address found for named peer:", hostnames[0])
        continue

    for ip_addr in ip_addrs:
        if ip_addr not in output:
            output[ip_addr] = set()

        output[ip_addr].update(hostnames)
        output[ip_addr].update([f"{hostname}.{domain}" for hostname in hostnames])

config_text = ""
for ip_addr, hostnames in sorted(output.items()):
    config_text += f"{ip_addr} {' '.join(sorted(hostnames))}\n"

ch = write_if_change(output_file, config_text)
print(f"hosts file: {output_file}{' (ok)' if ch else ' (unchanged)'}")
