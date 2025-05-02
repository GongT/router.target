from os import path
from pathlib import Path

import commentjson as json

from ..target import DIST_ROOT, logger, read_filtered_file
from .config_tools.data_types import Outbound
from .config_tools.env import STATE_DIR
from .config_tools.subscription_url import parse_url
from .config_tools.trasnports import create_transport_object


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


def process_line(provider: str, line: str):
    ln = parse_url(line)
    if ln is None:
        return

    if block_by_tag(ln["title"]):
        return

    ob = create_transport_object(ln)
    if not ob:
        return

    return ob


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


def build_outbounds():
    groups: dict[str, list[Outbound]] = {}

    subscriptions_folder = Path(STATE_DIR).joinpath("subscriptions")

    for file in subscriptions_folder.glob("*.txt"):
        try:
            logger.print("processing: " + file.as_posix())
            provider = path.splitext(file.name)[0]
            outbounds = []

            content = file.read_text()

            for line in content.splitlines():
                line = line.strip()
                outbound = process_line(provider, line)

                if outbound is None:
                    continue

                outbounds.append(outbound)

            groups[provider] = outbounds

        except:
            logger.warning("FILE: " + file.as_posix())
            raise

    if len(groups) == 0:
        logger.die("no outbound exists!!")

    if len(groups) > 1:
        for provider, outbounds in groups.items():
            for outbound in outbounds:
                outbound["tag"] = f"[{provider}] {outbound['tag']}"

    return groups


def outbounds_names(outbounds: list[Outbound]) -> list[str]:
    outboundTitles = []
    for ob in outbounds:
        outboundTitles.append(ob["tag"])
    return outboundTitles


def outbounds_domains(outbounds: list[Outbound]) -> list[str]:
    used_domains = set()
    for ob in outbounds:
        used_domains.add(ob["server"])
    return list(used_domains)


def load_config_template(file: Path | str):
    if isinstance(file, str):
        file = Path(file)

    groups = build_outbounds()
    outbounds: list[Outbound] = []
    for outbounds_group in groups.values():
        for outbound in outbounds_group:
            outbounds.append(outbound)

    outboundTitles = outbounds_names(outbounds)
    used_domains = outbounds_domains(outbounds)

    template = read_filtered_file(file)
    config = json.loads(template)

    config["experimental"]["clash_api"]["external_ui"] = Path(
        DIST_ROOT, "sing-box/webui"
    ).as_posix()

    inputObs: list = config["outbounds"]
    found = False
    for ob in inputObs:
        if (
            ob["tag"] == "out.select"
            or ob["tag"] == "out.manual"
            or ob["tag"] == "out.auto"
        ):
            ob["outbounds"] += outboundTitles
            found = True

    if not found:
        logger.die(
            f"no out.<select, manual, auto> in config file '{file}', nowhere to add outbounds"
        )

    config["outbounds"] = inputObs + outbounds

    rules: list = config["dns"]["rules"]
    rules.insert(
        0,
        {
            "domain": used_domains,
            "server": "dns.china",
        },
    )

    return config
