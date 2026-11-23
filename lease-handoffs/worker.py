"""Track IPv4 lease handoffs without opening the query database."""
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
import time
import tomllib

PERIOD = 15
KEEP = 91 * 86400
MAC = re.compile(r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}")


def unique_pairs(pairs):
    by_mac, by_ip = {}, {}
    for mac, ip in pairs:
        by_mac.setdefault(mac, set()).add(ip)
        by_ip.setdefault(ip, set()).add(mac)
    return {mac: next(iter(ips)) for mac, ips in by_mac.items()
            if len(ips) == 1 and len(by_ip[next(iter(ips))]) == 1}


def snapshot(config, now):
    with (config / "pihole.toml").open("rb") as f:
        dhcp = tomllib.load(f)["dhcp"]
    leases, reservations = [], []
    for line in (config / "dhcp.leases").read_text().splitlines():
        fields = line.lower().split()
        if not fields or fields[0] == "duid":
            continue
        if len(fields) < 5:
            raise ValueError("Incomplete DHCP lease file")
        if ":" in fields[2]:
            continue
        expires, mac, ip = fields[:3]
        if MAC.fullmatch(mac) and (int(expires) == 0 or int(expires) > now):
            leases.append((mac, str(ipaddress.IPv4Address(ip))))
    for host in dhcp.get("hosts", []):
        fields = [x.strip().lower() for x in host.split(",")]
        macs = [x for x in fields if MAC.fullmatch(x)]
        ips = [str(ipaddress.IPv4Address(x)) for x in fields if re.fullmatch(r"(?:\d+\.){3}\d+", x)]
        if len(macs) == len(ips) == 1:
            reservations.append((macs[0], ips[0]))
    if not dhcp["active"]:
        return {}, {}, set(), set()
    owners = unique_pairs(leases)
    conflicts = [(m, ip) for m, ip in leases if owners.get(m) != ip]
    return owners, unique_pairs(reservations), {m for m, _ in conflicts}, {ip for _, ip in conflicts}


def update(state, now, leases, reservations, ambiguous_macs=(), ambiguous_ips=()):
    windows = state.setdefault("windows", {})
    moves = state.setdefault("moves", {})
    previous = state.get("reservations", {})
    pending = state.get("pending", {})
    if now <= state.get("last", 0):
        raise ValueError("Waiting for the clock to advance")
    for mac in list(windows):
        windows[mac] = [w for w in windows[mac] if w[2] >= now - KEEP]
        if not windows[mac]:
            del windows[mac]
    former_owners = {}
    for mac, history in windows.items():
        for address, _, _ in history:
            former_owners.setdefault(address, set()).add(mac)
    active = dict(leases)
    for mac, ip in reservations.items():
        history = windows.get(mac, [])
        old = previous.get(mac)
        if mac in pending and old != ip:
            pending[mac] = ip
        elif old and old != ip:
            moves[mac] = ip
            pending.pop(mac, None)
        elif old != ip or (mac not in moves and mac not in pending):
            if leases.get(mac) != ip and history and history[-1][0] != ip:
                pending[mac] = ip
            if mac in leases and leases[mac] != ip:
                pending[mac] = ip
        if ((ip in leases.values() and leases.get(mac) != ip)
                or ip in ambiguous_ips or mac in ambiguous_macs
                or (old != ip and leases.get(mac) != ip and former_owners.get(ip, set()) - {mac})):
            pending[mac] = ip
        if pending.get(mac) == ip and leases.get(mac) == ip:
            moves[mac] = ip
            del pending[mac]
        if (mac not in active and mac not in pending and ip not in leases.values()
                and mac not in ambiguous_macs and ip not in ambiguous_ips
                and old is not None):
            active[mac] = ip
    for mac, ip in active.items():
        history = windows.setdefault(mac, [])
        if (history and history[-1][0] == ip and mac in state.get("active", [])
                and now - history[-1][2] <= PERIOD * 2):
            history[-1][2] = now
        else:
            history.append([ip, now, now])
    result = [f"T {now}"]
    for mac, ip in reservations.items():
        history = windows.get(mac, [])
        # An observed lease at another address is evidence of a move. A
        # same-address reservation without such evidence is an ordinary view.
        if mac not in pending and (any(w[0] != ip for w in history)
                                   or former_owners.get(ip, set()) - {mac}):
            moves[mac] = ip
        result.append(f"R {mac} {ip} {'pending' if mac in pending else 'ready'}")
        if moves.get(mac) == ip and mac not in pending and history:
            for old_ip, start, end in history:
                result.append(f"{ip} {old_ip} {max(start, now - KEEP)} {end}")
    state["moves"] = {m: ip for m, ip in moves.items() if reservations.get(m) == ip and m in windows}
    state["pending"] = {m: ip for m, ip in pending.items() if reservations.get(m) == ip}
    state["reservations"] = reservations.copy()
    state["active"] = list(active)
    state["last"] = now
    return "\n".join(result) + "\n"


def write(path, data, mode):
    tmp = path.with_suffix(".tmp")
    with tmp.open("w") as f:
        f.write(data)
        f.flush()
        os.fchmod(f.fileno(), mode)
        os.fsync(f.fileno())
    tmp.replace(path)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def main():
    import fcntl
    os.umask(0o077)
    root = Path("/state")
    writer_lock = (root / "worker.lock").open("a")
    fcntl.flock(writer_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    path = root / "state.json"
    state = json.loads(path.read_text()) if path.exists() else {}
    while True:
        try:
            now = int(time.time())
            rows = update(state, now, *snapshot(Path("/config"), now))
            write(path, json.dumps(state), 0o600)
            write(root / "view.txt", rows, 0o640)
        except (OSError, ValueError, KeyError, IndexError) as err:
            print(f"Handoff snapshot skipped: {type(err).__name__}", file=sys.stderr, flush=True)
        time.sleep(PERIOD)


if __name__ == "__main__":
    main()
