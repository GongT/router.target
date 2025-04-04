########################
# chinadns config bridge
########################
from pathlib import Path
import traceback

import idna

from config_tools.functions import dump_json
from config_tools.env import APP_DATA_DIR, STATE_DIR


def parse_domain_list(file: Path):
    domains = []

    if not file.exists():
        return domains

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
        domains.append(line)

    return domains


def create_ruleset_file(source: Path, output: Path, additinal_domains=[]):
    domains = [*parse_domain_list(source), *additinal_domains]

    print(f"write to file: {output}")

    text = dump_json(
        {
            "version": 3,
            "rules": [
                {
                    "domain": domains,
                    "domain_suffix": list(map(lambda x: f".{x}", domains)),
                }
            ],
        }
    )
    output.write_text(text)


####### DOMAINS
DOMAINS_DIR = Path(APP_DATA_DIR).joinpath("dns/dispatch")
RULES_DIR = Path(STATE_DIR).joinpath("my-rules")

RULES_DIR.mkdir(exist_ok=True)


create_ruleset_file(
    DOMAINS_DIR.joinpath("force.oversea.list"), RULES_DIR.joinpath("force.json")
)

create_ruleset_file(
    DOMAINS_DIR.joinpath("force.china.list"),
    RULES_DIR.joinpath("direct.json"),
)

create_ruleset_file(
    DOMAINS_DIR.joinpath("blacklist.list"), RULES_DIR.joinpath("blacklist.json")
)
