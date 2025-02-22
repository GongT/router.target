from os import environ


STATE_DIR = environ.get("STATE_DIRECTORY", default="/var/lib/proxy")
APP_DATA_DIR = environ.get("AppDataDir", default="/data/AppData/router")
OUTPUT_FILE = environ.get("CONFIG_FILE", "/tmp/config.json")
