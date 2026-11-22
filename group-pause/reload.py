"""Signal the running resolver and wait for a fresh completion from that PID."""
import argparse
import re
import subprocess
import time
from pathlib import Path


def reload(log_path, container):
    prefix = ["/usr/bin/docker", "exec", container] if container else []
    # Keep the signal command independent of client data and validate the PID
    # before doing any arithmetic or sending a signal.
    signal = r'''
        set -eu
        pid=$(cat /run/pihole-FTL.pid)
        case "$pid" in ""|*[!0-9]*|0|1) exit 1;; esac
        test "$(cat "/proc/$pid/comm")" = pihole-FTL
        sig=$(pihole-FTL sigrtmin)
        case "$sig" in ""|*[!0-9]*|0) exit 1;; esac
        kill -"$sig" "$pid"
        printf '%s\n' "$pid"
    '''
    with Path(log_path).open("rb") as log:
        log.seek(0, 2)
        pid = subprocess.check_output([*prefix, "/bin/sh", "-c", signal], timeout=4).strip()
        daemon = re.compile(rb"\[" + re.escape(pid) + rb"/T\d+\] ")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            line = log.readline()
            if not line:
                time.sleep(0.05)
                continue
            if not daemon.search(line):
                continue
            if b"database is locked" in line or b"Reloading the domainlists failed" in line:
                raise RuntimeError("FTL could not read the policy database")
            if b" INFO: Compiled " in line and b" deny regex for " in line:
                return
    raise RuntimeError("FTL reload completion timed out")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("log")
    parser.add_argument("--container")
    args = parser.parse_args()
    reload(args.log, args.container)
    print("OK", flush=True)
