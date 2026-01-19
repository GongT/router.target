import argparse
import json
import random
import re
import string
import subprocess
import threading
import time
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from sys import stderr
from typing import NoReturn, Text, TextIO, TypedDict

from router.target import logger, tools

confdir = Path(f"/etc/wireguard")
confs = [f.stem for f in confdir.glob("*.conf")]


def debug(*args):
    logger.dim(*args)


def die(*args) -> NoReturn:
    logger.die("Fatal Error:", *args)


parser = argparse.ArgumentParser(
    description="\tWireGuard VPN deploy tool",
    epilog="\x1b[2m\x1b[0m",
)
parser.add_argument(
    "--vpn",
    help="vpn name, requires /etc/wireguard/{vpn}.conf, optional if only one .conf at that location",
    choices=confs,
    default=confs[0] if len(confs) == 1 else None,
)
parser.add_argument(
    "--name",
    help='remote interface name, eg: "wg0", defaults to the same as --vpn',
    default=None,
)
parser.add_argument(
    "--hostname", required=True, help="target machine's virtual hostname"
)
parser.add_argument(
    "--ip",
    default="alloc",
    help="target machine's virtual IP address, defaults to auto increment",
)
parser.add_argument(
    "remote",
    help="ssh server argument, eg: root@1.2.3.4 -p 2222",
    nargs="*",
    metavar="-- REMOTE",
)
parser.add_argument(
    "--sudo",
    help="force use sudo to run remote commands",
    action="store_true",
)

parser.usage = re.sub(r"^usage: ", "", parser.format_help(), count=1)

args = parser.parse_args()

hostname: str = args.hostname
vpn: str = args.vpn
vpn_ifname: str = args.name or vpn
force_sudo: bool = args.sudo

if not re.fullmatch(r"^[a-zA-Z0-9._-]+$", hostname):
    die(f"Invalid hostname format: {hostname}")

config_file = Path(f"/etc/wireguard/{vpn}.conf")
if not config_file.exists():
    die(f'Configuration file "{config_file}" does not exist.')

config = tools.wireguard.read_wireguard_config(config_file)


def alloc_ip(input: str = args.ip):
    if input != "alloc":
        ip = str(IPv4Address(input))
        debug("using ip address from argument:", ip)
        return ip

    if_net_range = config.get("Address")
    if not if_net_range:
        die(f"missing Address field in [Interface]")

    try:
        allow_net_addr = IPv4Network(if_net_range, strict=False)
    except:
        die(f"Invalid Address format in [Interface]: {config.get('Address')}")

    debug("allocate ip address in range:", str(allow_net_addr))
    ip_addr = 0
    for item in config.peers():
        ip = item.get("AllowedIPs")
        if not ip:
            continue

        ip_addr_match = re.search(r"^[^/#\s]+", ip)
        if not ip_addr_match:
            continue

        inet_addr = int(IPv4Address(ip_addr_match[0]))
        if inet_addr > ip_addr:
            ip_addr = inet_addr
    ip_addr += 1

    ip = IPv4Address(ip_addr)
    # 判断ip是否在allow_net_addr中
    if ip not in allow_net_addr:
        die(
            f"failed alloc ip address, next ip {str(ip)} out of allowed range {str(allow_net_addr)}"
        )

    result = str(ip)
    debug("    ->", result)
    return result


def find_exists_hostname(hostname: str = hostname):
    for item in config.peers():
        ip = item.get("AllowedIPs")
        if not ip:
            continue

        if hostname in ip:
            debug("found exists config section for this hostname:", ip)
            return item

    return None


def restart_my_service():
    subprocess.run(
        ["systemctl", "restart", f"wg-quick@{vpn}.service"],
        stdout=stderr,
        stderr=subprocess.STDOUT,
        check=False,
    )


def genpubkey(prikey: str):
    return subprocess.run(
        ["wg", "pubkey"],
        input=prikey,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def make_keypair():
    prikey = subprocess.run(
        ["wg", "genkey"], capture_output=True, text=True, check=True
    ).stdout.strip()
    pubkey = genpubkey(prikey)
    debug("new pubkey:", pubkey)

    return (prikey, pubkey)


class Info(TypedDict):
    public_access: str
    public_key: str
    private_address: str
    domain_suffix: str | None


def get_public_addr():
    public_address = config.get("# PublicAddress")
    if public_address:
        return public_address

    debug("public address is not set in config file, detecting...")
    public_address = subprocess.run(
        ["hostname"], capture_output=True, text=True, check=True
    ).stdout.strip()

    debug(f"    {public_address}")
    if public_address.split(".")[-1].upper() in tools.www.tlds():
        port = int(config.get("ListenPort") or "51820")
        return f"{public_address}:{port}"

    die(
        "can not find public address for this server, you must set # PublicAddress in config file"
    )


def get_my_information():
    if_net_range = config.get("Address")
    if not if_net_range:
        die(f"missing Address field in [Interface]")
    ip = IPv4Address(if_net_range.split("/")[0])

    my_prikey = config.get("PrivateKey")
    if not my_prikey:
        die(f"missing PrivateKey field in [Interface]")

    return Info(
        public_access=get_public_addr(),
        public_key=genpubkey(my_prikey),
        private_address=str(ip),
        domain_suffix=get_vpn_domain(),
    )


def make_server_script(ip_str: str, prikey: str, my: Info):
    dns = my["private_address"]
    dns_scripts = []
    dns_scripts.append(f"PostUp = resolvectl dns %i {my['private_address']}")
    if my["domain_suffix"]:
        dns = f"{dns},{my['domain_suffix']}"
        dns_scripts.append(f"PostUp = resolvectl domain %i {my['domain_suffix']}")
    dns_scripts.append(f"PostUp = resolvectl default-route %i false")
    dns_scripts.append(f"# DNS = {dns}")

    script = f"""#!/usr/bin/bash

set -Eeuo pipefail

is_apt() {{
	command -v apt &>/dev/null
}}
is_dnf() {{
	command -v dnf &>/dev/null
}}

if ! command -v wg-quick &>/dev/null; then
	echo "installing wg-quick..."
	if is_apt; then
		apt install -y wireguard-tools
	elif is_dnf; then
		dnf install -y wireguard-tools
	else
		echo "unsupported package manager"
		exit 1
	fi
fi

mkdir -p /etc/wireguard
cat <<-EOF > "/etc/wireguard/{vpn_ifname}.conf"
	[Interface]
	Address = {ip_str}/32
	PrivateKey = {prikey}
	{"\n".join(dns_scripts)}
	ListenPort = 45148
	
	[Peer]
	PublicKey = {my['public_key']}
	AllowedIPs = {my['private_address']}
	Endpoint = {my['public_access']}
	PersistentKeepalive = 15
EOF

systemctl enable "wg-quick@{vpn_ifname}.service"
systemctl restart --no-block "wg-quick@{vpn_ifname}.service"
sleep 2
systemctl status "wg-quick@{vpn_ifname}.service"

echo "service is: $(systemctl is-active "wg-quick@{vpn_ifname}.service")"
"""

    return script


def get_vpn_domain():
    jsonTxt = subprocess.run(
        ["networkctl", "status", "--json=short", vpn],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        check=True,
    ).stdout

    data = json.loads(jsonTxt)
    for domains in data.get("SearchDomains", []):
        first = domains.get("Domain")
        if first:
            debug("found vpn domain:", first)
            return first

    return None


rand_strA = "".join(random.choices(string.ascii_letters + string.digits, k=4))
rand_strB = "".join(random.choices(string.ascii_letters + string.digits, k=4))
rand_str = rand_strA + rand_strB
printf_cmd = f"printf '%s%s\\n' '{rand_strA}' '{rand_strB}'\n"


def wait_ack(p: subprocess.Popen):
    signal = threading.Event()
    th = threading.Thread(target=_wait_ack_main, args=(p.stdin, signal))
    th.start()

    stdout: TextIO = p.stdout  # type: ignore
    while True:
        line = stdout.readline().rstrip()

        if rand_str in line:
            signal.set()
            th.join()
            return

        logger.dim(f"\x1b[48;5;8m \x1b[49m {line}")

        if p.poll() is not None:
            logger.die("thread unexpected died")


def _wait_ack_main(stdin: TextIO, signal: threading.Event):
    while signal.is_set() is False:
        stdin.write(printf_cmd)
        stdin.flush()
        time.sleep(1)


def execute(p: subprocess.Popen, script: str):
    stdin: TextIO = p.stdin  # type: ignore
    stdout: TextIO = p.stdout  # type: ignore

    # logger.dim(f"\x1b[48;5;8m \x1b[49m+ execute: {script}")
    stdin.write(f"\n{script}\n{printf_cmd}")
    stdin.flush()

    readed = ""
    while True:
        line = stdout.readline().rstrip()

        if rand_str in line:
            return readed

        logger.dim(f"\x1b[48;5;8m \x1b[49m {line}")
        readed = line + "\n"

        if p.poll() is not None:
            logger.die("thread unexpected died")


def execute_remote_script(script: str):
    # cmds = ["bash","-c","echo 123123"]
    cmds = ["ssh", *args.remote, "/bin/bash", "--norc", "--noprofile"]
    debug("executing remote script:", cmds)
    p = subprocess.Popen(
        cmds,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert p.stdin is not None, "stdin should not be None"
    assert p.stdout is not None, "stdout should not be None"

    wait_ack(p)
    logger.success("remote shell start working.")

    try:
        if force_sudo:
            id = -1
        else:
            id = execute(p, "/usr/bin/id -u")
            id = int(id)
        if id != 0:
            logger.dim(f"user {id} is not root, switching...")
            p.stdin.write(f"sudo bash --norc --noprofile\n{printf_cmd}")
            p.stdin.flush()
            line = p.stdout.readline().rstrip()
            if rand_str not in line:
                logger.die("failed to switch to root")
            else:
                logger.info("success switch user to root")
    except Exception as e:
        logger.die(f"failed to detect user id: {e}")

    output = execute(p, script)

    if "service is:" in output:
        logger.success("service install success", "(not sure execute ok)")
    else:
        logger.error("can not install service on remote machine")

    p.stdin.write("\nexit\nexit\nexit\nexit\n")
    p.stdin.flush()

    code = p.wait()
    if code != 0:
        logger.die("failed to execute remote script")


def main():
    exists = find_exists_hostname()
    if exists:
        ip_line_str = exists.get("AllowedIPs")
        if not ip_line_str:
            die(f"Invalid AllowedIPs format: {ip_line_str}")
        ip_m = re.search(r"^[^/#\s]+", ip_line_str)
        if not ip_m:
            die(f"Invalid AllowedIPs format: {ip_line_str}")

        ip_str = str(IPv4Address(ip_m[0]))

        prikey = exists.get("# private")
        pubkey = exists.get(name="PublicKey")
        if not prikey or not pubkey:
            prikey, pubkey = make_keypair()
        else:
            debug("using exists pubkey:", pubkey)
    else:
        ip_str = alloc_ip()
        prikey, pubkey = make_keypair()
        config.new_peer(prikey, pubkey, ip_str, hostname)

    debug("update config file:", config_file.as_posix())
    ch = config.update()
    if ch:
        restart_my_service()
        logger.success("  * saved")
    else:
        logger.dim("  * unchanged")

    info = get_my_information()
    script = make_server_script(ip_str, prikey, info)
    execute_remote_script(script)


if __name__ != "__main__":
    raise Exception("This script is not intended to be imported")

main()
