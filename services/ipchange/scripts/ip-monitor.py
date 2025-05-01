import subprocess
import threading


OBJECTS = [
    "address",
    "link",
    "mroute",
    "neigh",
    "netconf",
    "nexthop",
    "nsid",
    "prefix",
    "route",
    "rule",
    "stats",
]


def run_monitor(t):
    try:
        # Start the subprocess for "ip monitor address"
        process = subprocess.Popen(
            ["ip", "monitor", t],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Read the output line by line
        for line in iter(process.stdout.readline, ""):
            if line.strip():  # Non-empty output
                print(f"[{t}] {line.strip()}")

    except KeyboardInterrupt:
        print(f"[{t}] quitting...")
    except Exception as e:
        print(f"[{t}] Error occurred: {e}")
    finally:
        if process:
            process.kill()


if __name__ == "__main__":
    print("Starting IP monitor...")
    from concurrent.futures import ThreadPoolExecutor

    executor= ThreadPoolExecutor(max_workers=len(OBJECTS))
    for t in OBJECTS:
        executor.submit(run_monitor, t)

    try:
        executor.shutdown(wait=True)
    except KeyboardInterrupt:
        print("\nquitting...")
        executor.shutdown(wait=False)
