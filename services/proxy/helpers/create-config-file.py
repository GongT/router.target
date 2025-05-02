from os import path
from pathlib import Path

import commentjson as json
from config_tools.data_types.shadowsocks import ShadowSocksOutbound
from config_tools.data_types.vmess import V2RayTransport
from config_tools.env import APP_DATA_DIR, DIST_DIR, OUTPUT_FILE, STATE_DIR
from config_tools.functions import die, dump_json
from config_tools.subscription_url import parse_url
from config_tools.trasnports import create_transport_object

if __name__ != "__main__":
    die("this is a script, not a library.")


outbounds: list[ShadowSocksOutbound | V2RayTransport] = []


def process_line(provider: str, line: str):
    ln = parse_url(line)
    if ln is None:
        return

    if block_by_tag(ln["title"]):
        return

    ob = create_transport_object(ln)
    if not ob:
        return

    ob["_provider"] = provider

    outbounds.append(ob)


# def handle_config_data(provider: str, data):
#     obs = data["outbounds"]
#     for ob in obs:
#         if block_by_tag(ob["tag"]):
#             print("ignore tag: " + ob["tag"])
#             continue

#         ob["tag"] = f"[{provider}] {ob["tag"]}".replace("\n", "").replace("\r", "")

#         outbounds.append(ob)


def block_by_tag(name: str) -> bool:
    if not name:
        return True
    blnames = [
        "剩余",
        "到期",
        "官网",
        "网址",
        "续费",
        "过期",
        "超时",
        "Traffic:",
        "Expire:",
    ]
    for bln in blnames:
        if bln in name:
            return True
    return False


########################
subsDir = Path(STATE_DIR).joinpath("subscriptions")

for file in subsDir.glob("*.txt"):
    try:
        print("processing: " + file.as_posix())
        provider = path.splitext(file.name)[0]

        content = file.read_text()

        for line in content.splitlines():
            line = line.strip()
            process_line(provider, line)
    except:
        print("FILE: " + file.as_posix())
        raise

####### write out
if len(outbounds) == 0:
    die("no outbound exists!!")


if len(outbounds) > 1:
    for ob in outbounds:
        ob["tag"] = f"[{ob['_provider']}] {ob['tag']}"

used_domains = set()
outboundTitles = []
for ob in outbounds:
    del ob["_provider"]

    outboundTitles.append(ob["tag"])
    used_domains.add(ob["server"])

template = Path(__file__).parent.joinpath("template.json").read_text()
template = template.replace("${APP_DATA_DIR}", APP_DATA_DIR)
config = json.loads(template)


def merge_object(a: dict, b: dict, _dpath=""):
    for k, v in b.items():
        if k not in a:
            a[k] = v
            continue

        if isinstance(a[k], dict):
            merge_object(a[k], v, _dpath + "." + k)
        elif isinstance(a[k], list):
            print(f"concat array at {_dpath}.{k}")
            a[k] = v + a[k]
        else:
            print(f"set value {_dpath}.{k}")
            a[k] = v


custom = Path(APP_DATA_DIR).joinpath("proxy/custom.json")
if custom.exists():
    custom_config = json.loads(custom.read_text())
    merge_object(config, custom_config)


rules: list = config["dns"]["rules"]
rules.insert(
    0,
    {
        "domain": list(used_domains),
        "server": "dns.direct",
    },
)

inputObs: list = config["outbounds"]
for ob in inputObs:
    if (
        ob["tag"] == "out.select"
        or ob["tag"] == "out.manual"
        or ob["tag"] == "out.auto"
    ):
        ob["outbounds"] += outboundTitles

config["outbounds"] = inputObs + outbounds

config["experimental"]["clash_api"]["external_ui"] = Path(
    DIST_DIR, "sing-box/webui"
).as_posix()

print(f"write to file: {OUTPUT_FILE}")
with open(OUTPUT_FILE, "wt") as f:
    f.write(dump_json(config))
