from os import environ


STATE_DIR = environ.get("STATE_DIRECTORY", default="/var/lib/proxy")
APP_DATA_DIR = environ.get("APP_DATA_DIR", default="/data/AppData/router")
DIST_DIR = environ.get("DIST_ROOT", default="/usr/local/libexec/router/dist")
OUTPUT_FILE = environ.get("CONFIG_FILE", "/tmp/config.json")
