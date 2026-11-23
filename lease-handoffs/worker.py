"""Track IPv4 lease handoffs without opening the query database."""
import ipaddress
from copy import deepcopy
import os
from pathlib import Path
import re
import sys
import time
import tomllib

from checkpoint import publication_lock, publish, read_committed, write

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
    hosts = dhcp.get("hosts", [])
    if not dhcp["active"]:
        return {}, {}, set(), set(), hosts, False
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
    for host in hosts:
        fields = [x.strip().lower() for x in host.split(",")]
        macs = [x for x in fields if MAC.fullmatch(x)]
        ips = [str(ipaddress.IPv4Address(x)) for x in fields if re.fullmatch(r"(?:\d+\.){3}\d+", x)]
        if len(macs) == len(ips) == 1:
            reservations.append((macs[0], ips[0]))
    owners = unique_pairs(leases)
    conflicts = [(m, ip) for m, ip in leases if owners.get(m) != ip]
    return owners, unique_pairs(reservations), {m for m, _ in conflicts}, {ip for _, ip in conflicts}, hosts, True


def update(state, now, leases, reservations, ambiguous_macs=(), ambiguous_ips=(), hosts=None, enabled=True):
    if now <= state.get("last", 0):
        raise ValueError("Waiting for the clock to advance")
    if state.get("checkpoint_format") != 1:
        # Old windows combine observed leases and inferred static ownership.
        # Preserve them for conflict detection, but never publish them as proof.
        state["legacy_windows"] = state.pop("windows", {})
        state["active"] = []
        state["checkpoint_format"] = 1
    windows = state.setdefault("windows", {})
    moves = state.setdefault("moves", {})
    previous = state.get("reservations", {})
    pending = state.get("pending", {})
    former_owners = {}
    for records in (windows, state["legacy_windows"]):
        for mac, history in list(records.items()):
            recent = [window for window in history if window[2] >= now - KEEP]
            if not recent:
                del records[mac]
                continue
            records[mac] = recent
            for address, _, _ in recent:
                former_owners.setdefault(address, set()).add(mac)
    for mac, ip in reservations.items():
        old = previous.get(mac)
        if mac in pending and old != ip:
            pending[mac] = ip
        elif old and old != ip:
            moves[mac] = ip
            pending.pop(mac, None)
        elif old != ip or (mac not in moves and mac not in pending):
            seen = state.get("observed_leases", {}).get(mac)
            if leases.get(mac) != ip and seen and seen[0] != ip and seen[1] >= now - KEEP:
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
    for mac, ip in leases.items():
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
        status = "pending" if mac in pending else "ready"
        if status == "ready" and moves.get(mac) == ip and not history:
            status = "unverified"
        result.append(f"R {mac} {ip} {status}")
        if moves.get(mac) == ip and mac not in pending and history:
            for old_ip, start, end in history:
                result.append(f"{ip} {old_ip} {max(start, now - KEEP)} {end}")
    state["moves"] = {m: ip for m, ip in moves.items() if reservations.get(m) == ip}
    state["pending"] = {m: ip for m, ip in pending.items() if reservations.get(m) == ip}
    state["reservations"] = reservations.copy()
    state["active_leases"] = leases.copy()
    state["ambiguous_macs"] = sorted(ambiguous_macs)
    state["ambiguous_ips"] = sorted(ambiguous_ips)
    observed = state.setdefault("observed_leases", {})
    observed.update({mac: [ip, now] for mac, ip in leases.items()})
    state["observed_leases"] = {m:v for m,v in observed.items() if v[1] >= now - KEEP}
    state["active"] = list(leases)
    state["last"] = now
    if hosts is not None:
        state["host_rules"] = hosts
        state["dhcp_enabled"] = enabled
    return "\n".join(result) + "\n"


def main():
    import fcntl
    os.umask(0o077)
    root = Path("/state")
    view = Path(os.environ.get("HANDOFF_PUBLISH", "/state")) / "view.txt"
    writer_lock = (root / "worker.lock").open("a")
    fcntl.flock(writer_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    while True:
        try:
            if not view.exists() and not (root / "state.json").exists():
                write(view, "T 0\n", 0o640)
            previous = read_committed(root, view)
            state = deepcopy(previous)
            now = int(time.time())
            rows = update(state, now, *snapshot(Path("/config"), now))
            with publication_lock(root, exclusive=True):
                publish(root, view, previous, state, rows)
        except (OSError, ValueError, KeyError, IndexError, TypeError) as err:
            print(f"Handoff checkpoint unavailable: {type(err).__name__}", file=sys.stderr, flush=True)
        time.sleep(PERIOD)


if __name__ == "__main__":
    main()
