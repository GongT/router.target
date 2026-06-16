import base64
from os import path
from pathlib import Path

import commentjson as json

from .._internal.constants import ROUTER_DATA_PATH
from ..target import DIST_ROOT, logger, read_filtered_file
from .config_tools import parse_url
from .config_tools.data_types.outbound import Outbound
from .config_tools.env import STATE_DIR

__all__ = ["load_config_template", "build_outbounds"]


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
        logger.warning(f"不支持此类型的节点: {line}")
        return

    if block_by_tag(ln.tag):
        logger.dim(f"[{provider}] 根据名称忽略: {line}")
        return

    logger.dim(f"[{provider}] 成功解析节点: {line}")

    return ln


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

    subscription_files = []
    subscription_files.extend(Path(STATE_DIR).glob("subscriptions/*.txt"))
    subscription_files.extend(ROUTER_DATA_PATH.glob("proxy/custom-subscriptions/*.txt"))

    for file in subscription_files:
        try:
            logger.print("处理文件: " + file.as_posix())
            provider = path.splitext(file.name)[0]
            outbounds = []

            content: str = file.read_text()

            if ":" not in content and "\n" not in content.strip():
                logger.dim("parsing file as base64 encoded")
                try:
                    content = base64.b64decode(content, validate=True).decode("utf-8")
                except Exception:
                    logger.warning("文件是单行但不是有效的 base64 编码")
                    continue

            for line in content.splitlines():
                line = line.strip()
                outbound = process_line(provider, line)

                if outbound is None:
                    continue

                outbounds.append(outbound)

            groups[provider] = outbounds

            logger.print(f"[完成] 文件: {file.as_posix()} ({len(outbounds)} 个节点)\n")

        except:
            logger.warning("处理错误！文件: " + file.as_posix())
            raise

    if len(groups) == 0:
        logger.die("没有可用的出站连接!!")

    if len(groups) > 1:
        for provider, outbounds in groups.items():
            for outbound in outbounds:
                outbound.set_category(provider)

    return groups


def outbounds_names(outbounds: list[Outbound]) -> list[str]:
    outboundTitles = []
    for ob in outbounds:
        outboundTitles.append(ob.tag)
    outboundTitles.sort()
    return outboundTitles


def outbounds_domains(outbounds: list[Outbound]) -> list[str]:
    used_domains = set()
    for ob in outbounds:
        used_domains.add(*ob.domains)
    result = list(used_domains)
    result.sort()
    return result


def collect_outbound_domains(config) -> list[str]:
    results = set()
    special_types = ['direct', 'selector', 'urltest']
    for item in config['outbounds']:
        if item['type'] in special_types: continue
        tag = item.get('tag', '*missing tag*')
        server = item.get('server', None)
        if server is None:
            logger.warn(f"outbound [{tag}] missing server field.")

        results.add(server)
    return sorted(list(results))

def load_config_template(file: Path | str):
    if isinstance(file, str):
        file = Path(file)

    groups = build_outbounds()
    outbounds: list[Outbound] = []
    for outbounds_group in groups.values():
        for outbound in outbounds_group:
            outbounds.append(outbound)

    outboundTitles = outbounds_names(outbounds)
    # used_domains = outbounds_domains(outbounds)

    template = read_filtered_file(file)
    config = json.loads(template)

    config["experimental"]["clash_api"]["external_ui"] = Path(
        DIST_ROOT, "sing-box/webui"
    ).as_posix()

    meta_outbounds: list = config["outbounds"]
    found = False
    for ob in meta_outbounds:
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

    outbound_dicts: list[dict] = []
    for outbound in outbounds:
        obj = outbound.to_json()
        obj["routing_mark"] = 100
        # obj["$url"] = outbound.url
        outbound_dicts.append(obj)

    config["outbounds"] = meta_outbounds + outbound_dicts

    # rules: list = config["dns"]["rules"]
    # rules.insert(
    #     0,
    #     {
    #         "domain": used_domains,
    #         "action": "route",
    #         "server": "dns.china",
    #     },
    # )

    return config
