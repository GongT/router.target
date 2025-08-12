from os import path
from pathlib import Path

import commentjson as json

from router.target import logger, dump_json, proxy

if __name__ != "__main__":
    logger.die("this is a script, not a library.")


template = Path(__file__).parent.joinpath("template.json")
config = proxy.load_config_template(template)

inbounds = []


def make(remote: str):
    index = len(inbounds)
    e = {
        "type": "direct",
        "tag": f"in.dns{index}",
        "listen": "::1",
        "listen_port": 5342 + index,
        "override_address": remote,
        "override_port": 53,
        "udp_fragment": False,
        "tcp_fast_open": True,
    }
    inbounds.append(e)


for ip in [
    "1.1.1.1",
    "8.8.8.8",
    "2a03:90c0:999d::1",  # G-Core
    "2a02:6b8::feed:0ff",  # Yandex
    "2620:fe::fe",  # Quad9
    "94.140.14.14",  # AdGuard
]:
    make(ip)

config["inbounds"] = inbounds


output_file = Path(proxy.STATE_DIR) / "dnsproxy.json"
print(f"write to file: {output_file}")
with open(output_file, "wt") as f:
    f.write(dump_json(config))
