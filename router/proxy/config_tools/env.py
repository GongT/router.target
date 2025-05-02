from os import environ

STATE_DIR = environ.get("STATE_DIRECTORY", default="/var/lib/proxy")
