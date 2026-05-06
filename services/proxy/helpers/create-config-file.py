from os import path
from pathlib import Path

import commentjson as json

from router.target import (
    ROUTER_DATA_PATH,
    dump_json,
    logger,
    proxy,
    write_file_if_changed,
)

logger.dim(f"ROUTER_DATA_PATH: {ROUTER_DATA_PATH}")


template = Path(__file__).parent.joinpath("template.json")
config = proxy.load_config_template(template)

custom = Path(ROUTER_DATA_PATH).joinpath("proxy/custom.json")
if custom.exists():
    custom_config = json.loads(custom.read_text())
    proxy.merge_object(config, custom_config)

output_file = Path(proxy.STATE_DIR).joinpath("subscription.json")
write_file_if_changed(output_file, dump_json(config))
