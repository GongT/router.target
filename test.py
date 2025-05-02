from pprint import pprint

from router.config_file import KeyValueConfig

if __name__ == "__main__":
    config = KeyValueConfig("services/pppoe/pppoe.service")
    config.load()
    config.set("X-Container.wow-such", "doge")
    config.commit("/tmp/xxx.service")
    pprint(config.sections, width=120, indent=4, compact=False)
