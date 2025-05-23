from os import path
from pathlib import Path

import commentjson as json

from router.target import APP_DATA_DIR, die, dump_json, proxy

template = Path(__file__).parent.joinpath("template.json")
config = proxy.load_config_template(template)

custom = Path(APP_DATA_DIR).joinpath("proxy/custom.json")
if custom.exists():
    custom_config = json.loads(custom.read_text())
    proxy.merge_object(config, custom_config)

output_file = Path(proxy.STATE_DIR).joinpath("subscription.json")
print(f"write to file: {output_file}")
with open(output_file, "wt") as f:
    f.write(dump_json(config))
