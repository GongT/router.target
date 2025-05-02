import time
from pathlib import Path
from sys import argv

is_force = "--force" in argv


class TimestampFile:
    def __init__(self, filepath: Path, expires=60 * 60 * 1):
        self.path = filepath
        self.expires = expires

    def is_expired(self):
        if is_force:
            return True

        if not self.path.exists():
            return True

        last_do_time = int(self.path.read_text())
        if (last_do_time + self.expires) > int(time.time()):
            return False

        return True

    def update(self):
        self.path.write_text(str(int(time.time())))

    def remove(self):
        self.path.unlink(missing_ok=True)
