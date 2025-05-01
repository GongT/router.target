import json
from os import environ
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

# Timer reference
timer = None
interval = 5

STATE_DIR = Path(environ.get("STATE_DIRECTORY", "/var/lib/ipchange"))
STATE_DIR.mkdir(parents=True, exist_ok=True)


class StateSave:
    state: dict[str, list[str]]

    def __init__(self):
        self.state_file = STATE_DIR.joinpath("ipchange_state.json")
        state = None
        if self.state_file.exists():
            try:
                state = json.loads(self.state_file.read_text())
            except json.JSONDecodeError:
                pass

        if not state:
            state = {}
        if type(state) is not dict:
            state = {}

        self.state = state

    def load(self):
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                self.state = json.load(f)

    def update(self, name: str, state: list[str]):
        if state:
            self.state[name] = state
        else:
            if name in self.state:
                del self.state[name]

    def save(self):
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=4)

    def get(self):
        return self.state


def execute_get_output(command: str):
    """Execute a command and return its output."""
    result = subprocess.run(
        command,
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return result.stdout.strip()


def reset_timer(state: StateSave):
    global timer

    # Cancel the existing timer if it exists
    if timer:
        timer.cancel()

    # Start a new N-second timer
    timer = threading.Timer(interval, execute_script, args=(state,))
    timer.start()


def get_ip_addresses() -> dict[str, list[str]]:
    """Get the current IP addresses of all interfaces."""
    ip_addresses = {}
    output = json.loads(execute_get_output("ip --json addr show"))
    for info in output:
        ip_addresses[info["ifname"]] = []
    for info in output:
        for addr in info.get("addr_info", []):
            ip_addresses[info["ifname"]].append(addr["local"])

    for info in output:
        ip_addresses[info["ifname"]].sort()

    return ip_addresses


def calc_diff(state: StateSave, new_state: dict[str, list[str]]) -> list[str]:
    """Calculate the difference between the current and new state."""
    diff = []
    old_state = state.get()
    for interface, ips in new_state.items():
        if interface not in old_state:
            diff.append(interface)
        elif old_state[interface] != ips:
            diff.append(interface)

    for interface in old_state:
        if interface not in new_state:
            diff.append(interface)

    return diff


def execute_script(state: StateSave):
    new_addresses = get_ip_addresses()
    changes = calc_diff(state, new_addresses)
    if not len(changes):
        print("nothing change")
        return

    print(f"+ systemctl restart ipchange.service...")
    r = subprocess.run(["systemctl", "--no-block", "restart", "ipchange.service"])
    if r.returncode != 0:
        print(f"failed execute!")

    for ch in changes:
        print(f"+ systemctl restart ipchange@{ch}.service...")
        r = subprocess.run(
            ["systemctl", "restart", f"ipchange@{ch}.service"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if r.returncode != 0:
            print(f"failed call systemctl:\n{r.stdout.strip()}", file=sys.stderr)
        else:
            state.update(ch, new_addresses.get(ch, None))

    state.save()
    print("done.")


def monitor_ip():
    state = StateSave()

    print("initialize run...")
    execute_script(state)

    print("waitting IP changes...")
    try:
        # Start the subprocess for "ip monitor address"
        process = subprocess.Popen(
            ["ip", "monitor", "address"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Read the output line by line
        for line in iter(process.stdout.readline, ""):
            line = line.strip()
            if not line:
                continue
            print(f"[ip] {line.strip()}")
            reset_timer(state)

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        if process:
            process.kill()
        print("Monitor process ended.")


if __name__ == "__main__":
    try:
        monitor_ip()
    except KeyboardInterrupt:
        print("\nquitting...")
