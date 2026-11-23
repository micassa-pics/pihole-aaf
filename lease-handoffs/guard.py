"""Serialize authenticated DHCP reservation writes. Listen on a private Unix socket."""
import argparse
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import socketserver
import sqlite3
import sys
import time
import tomllib
import traceback
from urllib.parse import urlsplit

from checkpoint import publication_lock, read_committed, sync_directory

MAC = re.compile(r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}")
MAX_BODY = 512 * 1024


class Problem(Exception):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


def groups(lines):
    result = {}
    for line in lines:
        macs = [x.strip().lower() for x in line.split(",") if MAC.fullmatch(x.strip().lower())]
        key = macs[0] if len(macs) == 1 else "manual"
        result.setdefault(key, []).append(line)
    return result


def ip_of(lines):
    if len(lines) == 1:
        for field in lines[0].split(","):
            try:
                return str(ipaddress.IPv4Address(field.strip()))
            except ValueError:
                pass
    return None


def edit(lines, desired, keys):
    # Keep unrelated rows, including changes made since the editor opened.
    wanted = groups(desired)
    result = []
    used = set()
    for line in lines:
        key = next(iter(groups([line])))
        if key not in keys:
            result.append(line)
        elif key not in used:
            result.extend(wanted.get(key, []))
            used.add(key)
    for key in wanted:
        if key in keys and key not in used:
            result.extend(wanted[key])
    return result


class Journal:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=DELETE")
        self.db.execute("PRAGMA synchronous=EXTRA")
        self.db.execute("CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY, data TEXT NOT NULL)")

    def load(self):
        row = self.db.execute("SELECT data FROM journal WHERE id=1").fetchone()
        return json.loads(row[0]) if row else {"known": None, "rev": {}, "locks": {}, "receipts": {}, "intent": None}

    def store(self, s):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO journal VALUES (1,?)", (json.dumps(s),))


def bump(s, key):
    s["rev"][key] = s["rev"].get(key, 0) + 1


def finish(s, intent, now):
    previous = groups(intent.get("before", []))
    desired = groups(intent["after"])
    last_changes = s.setdefault("last_changes", {})
    for key in intent["keys"]:
        bump(s, key)
        s["locks"].pop(key, None)
        if "before" in intent and previous.get(key) != desired.get(key):
            last_changes[key] = {"before":previous.get(key, []), "requested":desired.get(key, [])}
        lock = intent["locks"].get(key)
        if lock:
            s["locks"][key] = lock
    s["receipts"][intent["id"]] = [intent["digest"], now, "saved"]
    s["known"] = groups(intent["after"])
    s["known_order"] = intent["after"]
    if not intent["keys"] and "before" in intent and intent["before"] != intent["after"]:
        s["last_order"] = {"before":intent["before"], "requested":intent["after"]}
    s["intent"] = None


def reconcile(s, current, monitor, now, sync_config):
    actual = groups(current)
    intent = s["intent"]
    if intent:
        after = groups(intent["after"])
        if (current == intent["after"] if not intent["keys"] else
                all(actual.get(k, []) == after.get(k, []) for k in intent["keys"])):
            sync_config(current)
            finish(s, intent, now)
        else:
            # An interrupted PATCH is never replayed. Require a human to review.
            previous = groups(intent.get("before", []))
            for key in intent["keys"] or ["order"]:
                bump(s, key)
                recovery = {"before":previous.get(key, []), "requested":after.get(key, [])}
                if key == "order":
                    recovery = {"before":intent.get("before", []), "requested":intent["after"]}
                s["locks"][key] = {"kind":"review", "ip":ip_of(actual.get(key, [])), "recovery":recovery}
            s["receipts"][intent["id"]] = [intent["digest"], now, "review"]
            s["intent"] = None
    old = s["known"]
    old_order = s.get("known_order")
    last_order = s.get("last_order")
    if last_order and old_order == last_order["requested"] and current != old_order and sorted(current) == sorted(old_order):
        bump(s, "order")
        s["locks"]["order"] = {"kind":"review", "ip":None, "recovery":last_order}
    if old is not None:
        for key in old.keys() | actual.keys():
            if old.get(key) != actual.get(key):
                bump(s, key)
                existing = s["locks"].get(key, {})
                recovery = existing.get("recovery", s.get("last_changes", {}).get(key))
                s["locks"][key] = {"kind":"review", "ip":ip_of(actual.get(key, []))}
                if recovery is not None:
                    s["locks"][key]["recovery"] = recovery
    s["known"] = actual
    s["known_order"] = current
    if monitor:
        recorded = groups(monitor.get("host_rules", []))
        for key, lock in list(s["locks"].items()):
            if lock["kind"] == "review" or monitor["last"] <= lock["since"]:
                continue
            target = lock["ip"]
            recorded_ip = (monitor["reservations"].get(key) if monitor.get("dhcp_enabled", True)
                           else ip_of(recorded.get(key, [])))
            if recorded_ip != target or key in monitor["pending"]:
                continue
            if lock["kind"] == "lease":
                observed = monitor.get("observed_leases", {}).get(key)
                if not observed or observed[0] != target or observed[1] <= lock["since"]:
                    continue
            del s["locks"][key]
            bump(s, key)
    s["receipts"] = {k:v for k,v in s["receipts"].items() if now-v[1] < 7*86400}


def snapshot(s, current, monitor):
    locks = {k:{"kind":v["kind"], "ip":v["ip"]} for k,v in s["locks"].items()}
    for key, lock in s["locks"].items():
        if lock["kind"] != "review" and "before" not in lock:
            locks[key]["waitOnly"] = True
        if "recovery" in lock:
            locks[key]["recovery"] = lock["recovery"]
    for k, ip in (monitor or {}).get("pending", {}).items():
        if ip == ip_of(s["known"].get(k, [])):
            locks.setdefault(k, {"kind":"review", "ip":ip})
    return {"hosts":current, "versions":s["rev"], "locks":locks, "checkpointReady": monitor is not None}


def operate(journal, api, monitor, req):
    now = int(time.time())
    current = api.read()
    s = journal.load()
    prior = json.dumps(s)
    reconcile(s, current, monitor, now, api.sync_config)
    if json.dumps(s) != prior:
        journal.store(s)
    view = snapshot(s, current, monitor)
    action = req.get("action")
    if action == "read":
        return view
    if action == "status":
        rid = req.get("id")
        if not isinstance(rid,str) or not re.fullmatch("[0-9a-f]{32}",rid):
            raise Problem("Invalid request ID.",400)
        receipt = s["receipts"].get(rid)
        return {**view,"outcome":receipt[2] if receipt else "unknown"}
    rid = req.get("id", "")
    if action not in ("save","cancel","review") or not isinstance(rid,str) or not re.fullmatch("[0-9a-f]{32}",rid):
        raise Problem("Invalid reservation request.",400)
    digest = hashlib.sha256(json.dumps(req,sort_keys=True).encode()).hexdigest()
    receipt = s["receipts"].get(rid)
    if receipt:
        if receipt[0] != digest or receipt[2] != "saved":
            raise Problem("This request requires review.")
        return view
    versions = req.get("versions")
    if not isinstance(versions,dict):
        raise Problem("Missing device revisions.",400)
    locks = {}
    if action == "save":
        before, after = req.get("before"), req.get("after")
        for lines in (before,after):
            if not isinstance(lines,list) or any(not isinstance(x,str) or not x.strip() or any(ord(c)<32 for c in x) for x in lines):
                raise Problem("Invalid reservation list.",400)
        base, desired = groups(before), groups(after)
        keys = {k for k in base.keys() | desired.keys() if base.get(k) != desired.get(k)}
    else:
        key = req.get("key")
        if not isinstance(key,str) or key not in view["locks"]:
            raise Problem("The move has already changed. Refresh the reservation.")
        keys = {key}
        base = s["known"]
        if action == "review" and view["locks"][key]["kind"] != "review":
            raise Problem("This reservation is waiting for a handoff.")
        if action == "cancel" and view["locks"][key]["kind"] == "review":
            raise Problem("Review the current reservation first.")
        lock = s["locks"].get(key, {})
        if action == "cancel" and not isinstance(lock.get("before"), list):
            raise Problem("The journal has no previous reservation to restore.")
        after = edit(current, lock["before"], keys) if action == "cancel" else current
        pending = (monitor or {}).get("pending", {}).get(key)
        if action == "review" and pending and pending == ip_of(base.get(key, [])):
            locks[key] = {"kind":"lease", "since":monitor["last"], "ip":pending}
        desired = groups(after)
    for key in keys:
        if versions.get(key,0) != s["rev"].get(key,0) or base.get(key) != s["known"].get(key):
            raise Problem("Another editor changed this device. Review the current row before saving.")
        if action == "save" and key in view["locks"]:
            raise Problem("This device already has a pending move. Review the current row.")
        if action == "save" and MAC.fullmatch(key) and not monitor:
            raise Problem("The lease monitor has no current checkpoint.",503)
        old_ip, new_ip = ip_of(base.get(key, [])), ip_of(desired.get(key, []))
        if action != "review" and MAC.fullmatch(key) and new_ip and new_ip != old_ip:
            if not monitor:
                raise Problem("The lease monitor has no current checkpoint.",503)
            if "host_rules" in monitor:
                caught_up = groups(monitor["host_rules"]).get(key) == base.get(key)
            else:
                caught_up = monitor["reservations"].get(key) == old_ip
            if action != "cancel" and not caught_up:
                raise Problem("Waiting for the monitor to record the current reservation.")
            check_lease_target(monitor, key, new_ip)
            observed = monitor.get("observed_leases", {}).get(key)
            kind = "lease" if monitor.get("dhcp_enabled", True) and not old_ip and observed and observed[0] != new_ip else "checkpoint"
            locks[key] = {"kind":kind, "since":max(now,monitor["last"]), "ip":new_ip, "before":base.get(key,[])}
    if action == "save" and before != after and not keys:
        if "order" in view["locks"] or current != before:
            raise Problem("Review the current reservation order before reordering again.")
    target = after if action == "save" and current == before else edit(current, after, keys)
    # Refuse to merge a stale draft onto an IP now reserved by another device.
    owners = {}
    new_targets = {}
    previous = groups(current)
    for key, rows in groups(target).items():
        for line in rows:
            addr = ip_of([line])
            if addr and addr in owners and owners[addr] != key and (key in keys or owners[addr] in keys):
                raise Problem("The selected IP is already reserved.")
            if addr:
                owners[addr] = key
                if key in keys and not any(ip_of([old]) == addr for old in previous.get(key, [])):
                    new_targets[addr] = key
    if new_targets and not monitor:
        raise Problem("The lease monitor has no current checkpoint.", 503)
    if new_targets and monitor.get("dhcp_enabled", True):
        for lease in api.active_leases():
            address = lease["ip"]
            if address not in new_targets:
                continue
            if lease["expires"] and lease["expires"] <= now:
                continue
            if lease.get("hwaddr", "").lower() != new_targets[address]:
                raise Problem("This IP is currently leased to another device.")
    intent = {"id":rid,"digest":digest,"before":current,"after":target,"keys":sorted(keys),"locks":locks}
    s["intent"] = intent
    journal.store(s)
    if target != current:
        try:
            if api.read() != current:
                raise Problem("The reservation list changed before the save. Refresh and try again.")
        except (OSError, http.client.HTTPException, Problem, ValueError, KeyError):
            s["intent"] = None
            journal.store(s)
            raise
        try:
            api.write(target)
        except Problem as err:
            if err.status in (400,401,403):
                s["intent"] = None
                journal.store(s)
            raise
        if api.read() != target:
            raise Problem("Pi-hole returned different reservations. Review the device.")
        api.sync_config(target)
    finish(s,intent,now)
    journal.store(s)
    return snapshot(s,target,monitor)


def check_lease_target(monitor, key, address):
    if not monitor.get("dhcp_enabled", True):
        return
    if address in monitor.get("ambiguous_ips", []) or key in monitor.get("ambiguous_macs", []):
        raise Problem("Lease ownership is ambiguous. Wait for DHCP to resolve it.")
    if any(owner != key and ip == address for owner, ip in monitor.get("active_leases", {}).items()):
        raise Problem("This IP is currently leased to another device.")


class API:
    def __init__(self, origin, headers, config=None):
        self.origin, self.headers = origin, headers
        self.config = config

    def sync_config(self, expected):
        if self.config is None:
            return
        path = self.config / "pihole.toml"
        with path.open("rb") as file:
            if tomllib.load(file)["dhcp"]["hosts"] != expected:
                raise Problem("The saved rules are awaiting disk verification. Refresh before retrying.", 503)
            os.fsync(file.fileno())
            sync_directory(self.config)
            final = path.stat()
            original = os.fstat(file.fileno())
            if (final.st_dev, final.st_ino) != (original.st_dev, original.st_ino):
                raise Problem("Pi-hole replaced its config during disk verification. Refresh before retrying.", 503)

    def call(self, method, path, data=None):
        cls = http.client.HTTPSConnection if self.origin.scheme == "https" else http.client.HTTPConnection
        conn = cls(self.origin.hostname,self.origin.port,timeout=8)
        try:
            if self.origin.scheme == "http":
                # Minimal OpenWrt Python omits the optional IDNA tables.
                conn.sock = socket.create_connection((self.origin.hostname.encode("ascii"),
                                                      self.origin.port or 80),timeout=8)
            conn.request(method,self.origin.path.rstrip("/") + path,body=json.dumps(data).encode() if data else None,
                         headers={**self.headers,"Content-Type":"application/json"})
            r = conn.getresponse()
            body = r.read()
            if r.status >= 300:
                raise Problem("Pi-hole refused the reservation request.",r.status if r.status in (400,401,403) else 502)
            return json.loads(body) if body else {}
        finally:
            conn.close()

    def read(self):
        # FTL can briefly restart its HTTP listener after a hosts update.
        # Retry reads only. Every PATCH is sent at most once.
        deadline = time.monotonic() + 6
        while True:
            try:
                return self.call("GET","/config/dhcp?detailed=true")["config"]["dhcp"]["hosts"]["value"]
            except (OSError,http.client.HTTPException,Problem) as err:
                if getattr(err,"status",503) in (400,401,403) or time.monotonic() >= deadline:
                    raise
                time.sleep(0.35)

    def write(self,lines):
        self.call("PATCH","/config",{"config":{"dhcp":{"hosts":lines}}})

    def active_leases(self):
        return self.call("GET", "/dhcp/leases")["leases"]


class Handler(BaseHTTPRequestHandler):
    timeout = 15

    def log_message(self,*args):
        pass

    def do_POST(self):
        try:
            if self.path != "/reservation-guard" or self.headers.get("X-Reservation-Guard") != "1":
                raise Problem("Invalid reservation endpoint.",403)
            origin = urlsplit(self.headers.get("Origin",""))
            if (origin.scheme not in ("http","https") or origin.netloc != self.headers.get("Host")
                    or self.headers.get("Origin") not in self.server.origins):
                raise Problem("A same-origin request is required.",403)
            n = int(self.headers.get("Content-Length","0"))
            if not 0 < n <= MAX_BODY:
                raise Problem("Invalid reservation request size.",413)
            req = json.loads(self.rfile.read(n))
            if not isinstance(req,dict):
                raise Problem("Expected a JSON object.",400)
            auth = {k:self.headers[k] for k in ("Cookie","X-FTL-SID","X-CSRF-TOKEN") if self.headers.get(k)}
            try:
                with publication_lock(self.server.state):
                    monitor = read_committed(self.server.state, self.server.view)
                    if monitor.get("checkpoint_format") != 1 or not 0 <= time.time()-monitor["last"] <= 30:
                        monitor = None
                    else:
                        # Make a publication durable even if the worker stopped just after rename.
                        sync_directory(self.server.view.parent)
            except (OSError,KeyError,ValueError,TypeError):
                monitor = None
            result = operate(self.server.journal, API(self.server.origin, auth, self.server.config), monitor, req)
            code = 200
        except Problem as err:
            result, code = {"error":str(err)}, err.status
        except (ValueError,TypeError):
            result, code = {"error":"Invalid reservation request."},400
        except (OSError,sqlite3.Error,KeyError,http.client.HTTPException) as err:
            # Log the failing code location without credentials or reservation data.
            site = traceback.extract_tb(err.__traceback__)[-1]
            print(f"Reservation error: {type(err).__name__} in {site.name}:{site.lineno} "
                  f"({getattr(err,'sqlite_errorname',getattr(err,'errno',None))})",
                  file=sys.stderr,flush=True)
            result, code = {"error":"Reservation service unavailable. Refresh before retrying."},503
        payload = json.dumps(result).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main():
    import fcntl
    p = argparse.ArgumentParser()
    p.add_argument("state",type=Path)
    p.add_argument("socket",type=Path)
    p.add_argument("api")
    p.add_argument("--view", type=Path, help="Path to the published handoff view")
    p.add_argument("--config-dir", type=Path, help="Read-only Pi-hole config directory for durable save verification")
    p.add_argument("--web-origin", action="append", default=[], help="Allowed external admin origin")
    args = p.parse_args()
    if os.getuid() == 0:
        p.error("Run the reservation guard as an unprivileged user")
    os.umask(0o077)
    lock = (args.state/"guard.lock").open("a")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    args.socket.unlink(missing_ok=True)
    with socketserver.UnixStreamServer(str(args.socket), Handler) as server:
        args.socket.chmod(0o660)
        server.journal = Journal(args.state/"guard.sqlite")
        server.state = args.state
        server.config = args.config_dir
        server.view = args.view or args.state/"published/view.txt"
        server.origin = urlsplit(args.api)
        server.origins = set(args.web_origin or [f"{server.origin.scheme}://{server.origin.netloc}"])
        server.serve_forever()


if __name__ == "__main__":
    main()

