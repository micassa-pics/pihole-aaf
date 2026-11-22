"""Apply authenticated sidebar requests and restore groups when their timers end."""
from contextlib import closing
import argparse
import ipaddress
import json
import logging
import re
import sqlite3
import socket
import subprocess
import time
from pathlib import Path

PREFIX = "awesome-a-fyer-pause-"
REQUEST = re.compile(PREFIX + "[0-9a-f]{32}")
MAX_SECONDS = 2**31 - 1


DONE_PREFIX = "awesome-a-fyer-done-"
DEVICE_PREFIX = "awesome-a-fyer-device-"


def exact_ip(value):
    try:
        network = ipaddress.ip_network(value, strict=False)
        if network.num_addresses == 1 and "%" not in value:
            return str(network.network_address)
    except ValueError:
        pass
    return None


def pause_device(db, ip, rid, request, deadline):
    if db.execute("SELECT 1 FROM scheduler.device_timers WHERE ip=?", (ip,)).fetchone():
        return False
    matches = [(cid, address) for cid, address in db.execute("SELECT id,ip FROM client") if exact_ip(address) == ip]
    if len(matches) > 1:
        return False
    temporary = not matches
    cid = db.execute("INSERT INTO client(ip) VALUES(?)", (ip,)).lastrowid if temporary else matches[0][0]
    old = [g for (g,) in db.execute("SELECT group_id FROM client_by_group WHERE client_id=?", (cid,))]
    marker = DEVICE_PREFIX + request[len(PREFIX):]
    db.execute('UPDATE "group" SET name=?, description=? WHERE id=?', (marker, ip, rid))
    db.execute("DELETE FROM client_by_group WHERE client_id=?", (cid,))
    db.execute("INSERT INTO client_by_group(client_id,group_id) VALUES(?,?)", (cid, rid))
    db.execute("INSERT INTO scheduler.device_timers VALUES(?,?,?,?,?,?,?)",
               (ip, cid, rid, marker, json.dumps(old), temporary, deadline))
    return True


def restore_device(db, row):
    ip, cid, gid, marker, old, temporary, _ = row
    client = db.execute("SELECT ip,comment FROM client WHERE id=?", (cid,)).fetchone()
    groups = {g for (g,) in db.execute("SELECT group_id FROM client_by_group WHERE client_id=?", (cid,))}
    owned = db.execute('SELECT 1 FROM "group" WHERE id=? AND name=?', (gid, marker)).fetchone()
    if client and exact_ip(client[0]) == ip and (groups == {gid} or (not owned and not groups)):
        if temporary:
            # Remove the exact-IP override to recover subnet, MAC or interface rules.
            if client[1]:
                db.execute("INSERT INTO scheduler.client_notes VALUES(?,?,?)", (ip, client[1], int(time.time())))
            db.execute("DELETE FROM client WHERE id=?", (cid,))
        else:
            db.execute("DELETE FROM client_by_group WHERE client_id=? AND group_id=?", (cid, gid))
            for original in json.loads(old):
                db.execute('INSERT OR IGNORE INTO client_by_group SELECT ?,id FROM "group" WHERE id=?', (cid, original))
    if owned:
        db.execute('DELETE FROM "group" WHERE id=? AND name=?', (gid, marker))
    db.execute("DELETE FROM scheduler.device_timers WHERE ip=?", (ip,))


def finish_request(db, name, now, seconds=0):
    deadline = now + seconds if seconds else 0
    db.execute("INSERT OR IGNORE INTO scheduler.receipts(name, changed, deadline) VALUES(?,?,?)",
               (DONE_PREFIX + name[len(PREFIX):], now, deadline))


def process(db, now):
    """Keep each group update and its recovery record in one transaction."""
    changed = False
    for gid, created, deadline in db.execute("SELECT id, created, deadline FROM scheduler.timers").fetchall():
        group = db.execute('SELECT enabled, date_added FROM "group" WHERE id=?', (gid,)).fetchone()
        if group == (0, created) and deadline > now:
            continue
        if group == (0, created):
            db.execute('UPDATE "group" SET enabled=1 WHERE id=?', (gid,))
            changed = True
        db.execute("DELETE FROM scheduler.timers WHERE id=?", (gid,))

    for row in db.execute("SELECT t.* FROM scheduler.device_timers t LEFT JOIN [group] g ON g.id=t.gid AND g.name=t.marker WHERE (t.deadline>0 AND t.deadline<=?) OR g.id IS NULL", (now,)).fetchall():
        restore_device(db, row)
        changed = True

    requests = db.execute(
        'SELECT id,name,description,date_added FROM "group" WHERE enabled=0 AND name GLOB ?',
        (PREFIX + "*",),
    ).fetchall()
    for rid, name, description, submitted in requests:
        if not REQUEST.fullmatch(name):
            continue
        try:
            if not isinstance(description, str) or len(description) > 65536:
                raise ValueError("Invalid command")
            req = json.loads(description)
            seconds = req["seconds"]
            if type(seconds) is not int or not 0 <= seconds <= MAX_SECONDS:
                raise ValueError("Invalid duration")
            if "device" in req:
                ip = req["device"]
                if isinstance(ip, str) and exact_ip(ip) == ip and 0 <= now - submitted <= 15:
                    if req.get("resume") is True:
                        row = db.execute("SELECT * FROM scheduler.device_timers WHERE ip=?", (ip,)).fetchone()
                        if row:
                            restore_device(db, row)
                            finish_request(db, name, now)
                            changed = True
                    elif pause_device(db, ip, rid, name, now + seconds if seconds else 0):
                        finish_request(db, name, now, seconds)
                        changed = True
                        continue
                db.execute('DELETE FROM "group" WHERE id=?', (rid,))
                continue
            targets = req["groups"]
            if not isinstance(targets, list) or not 1 <= len(targets) <= 1024:
                raise ValueError("Invalid targets")
            if not all(isinstance(t, dict) and type(t.get("id")) is int and 0 <= t["id"] < 2**63
                       and isinstance(t.get("name"), str)
                       and not t["name"].lower().startswith((PREFIX, DONE_PREFIX, DEVICE_PREFIX))
                       for t in targets):
                raise ValueError("Invalid group")
        except (KeyError, ValueError, TypeError, RecursionError):
            db.execute('DELETE FROM "group" WHERE id=?', (rid,))
            continue
        # A stopped worker must never start an old pause when it comes back.
        if 0 <= now - submitted <= 15:
            groups = [db.execute('SELECT id,date_added FROM "group" WHERE id=? AND name=? AND enabled=1',
                                 (t["id"], t["name"])).fetchone() for t in targets]
            if all(groups) and len(set(groups)) == len(groups):
                for gid, created in groups:
                    db.execute('UPDATE "group" SET enabled=0 WHERE id=?', (gid,))
                    if seconds:
                        db.execute("INSERT OR REPLACE INTO scheduler.timers VALUES (?,?,?)", (gid, created, now + seconds))
                finish_request(db, name, now, seconds)
                changed = True
        db.execute('DELETE FROM "group" WHERE id=?', (rid,))
    if changed:
        db.execute("INSERT OR IGNORE INTO scheduler.reload_pending VALUES (1)")


def tick(gravity, state, reload_lists):
    # Reopen each time because Pi-hole can replace gravity.db during an update.
    with closing(sqlite3.connect(gravity.resolve().as_uri() + "?mode=rw", uri=True, timeout=5)) as db:
        db.execute("ATTACH DATABASE ? AS scheduler", (str(state),))
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE IF NOT EXISTS scheduler.timers (id INTEGER PRIMARY KEY, created INTEGER, deadline INTEGER)")
        db.execute("CREATE TABLE IF NOT EXISTS scheduler.reload_pending (id INTEGER PRIMARY KEY)")
        db.execute("CREATE TABLE IF NOT EXISTS scheduler.device_timers (ip TEXT PRIMARY KEY, cid INTEGER, gid INTEGER, marker TEXT, original_groups TEXT, temporary INTEGER, deadline INTEGER)")
        db.execute("CREATE TABLE IF NOT EXISTS scheduler.receipts (name TEXT PRIMARY KEY, changed INTEGER, deadline INTEGER)")
        columns = {column[1] for column in db.execute("PRAGMA scheduler.table_info(receipts)")}
        if "changed" not in columns:
            # Upgrade old state. Receipts without a known deadline cannot confirm a pause.
            db.execute("ALTER TABLE scheduler.receipts ADD COLUMN changed INTEGER")
            db.execute("ALTER TABLE scheduler.receipts ADD COLUMN deadline INTEGER")
        db.execute("CREATE TABLE IF NOT EXISTS scheduler.client_notes (ip TEXT, comment TEXT, archived INTEGER)")
        queued = db.execute('SELECT 1 FROM "group" WHERE enabled=0 AND name GLOB ? LIMIT 1', (PREFIX + "*",)).fetchone()
        tracking = db.execute('SELECT 1 FROM scheduler.timers t LEFT JOIN [group] g ON g.id=t.id WHERE t.deadline<=? OR g.id IS NULL OR g.enabled!=0 OR g.date_added!=t.created LIMIT 1', (int(time.time()),)).fetchone()
        due = db.execute("SELECT 1 FROM scheduler.device_timers t LEFT JOIN [group] g ON g.id=t.gid AND g.name=t.marker WHERE (deadline>0 AND deadline<=?) OR g.id IS NULL LIMIT 1", (int(time.time()),)).fetchone()
        if queued or tracking or due:
            db.execute("BEGIN IMMEDIATE")
            process(db, int(time.time()))
            db.commit()
        if db.execute("SELECT 1 FROM scheduler.reload_pending").fetchone():
            started = time.time()
            if len(reload_lists) == 1 and reload_lists[0].endswith(".sock"):
                with socket.socket(socket.AF_UNIX) as sock:
                    sock.settimeout(12)
                    sock.connect(reload_lists[0])
                    if sock.makefile("rb").readline(16) != b"OK\n":
                        raise OSError("List reload unconfirmed")
            else:
                subprocess.run(reload_lists, check=True, timeout=30)
            completed = time.time()
            db.execute("BEGIN IMMEDIATE")
            for name, changed, deadline in db.execute("SELECT name,changed,deadline FROM scheduler.receipts"):
                expired = deadline is None or (deadline and completed >= deadline)
                result = "expired" if expired else "applied"
                db.execute("INSERT OR IGNORE INTO [group](name,enabled,date_added,description) VALUES(?,0,?,?)",
                           (name, int(completed), result))
                logging.info("Pause result=%s changed=%s reload_started=%.3f completed=%.3f deadline=%s",
                             result, changed, started, completed, deadline)
            db.execute("DELETE FROM scheduler.receipts")
            db.execute("DELETE FROM scheduler.reload_pending")
            db.commit()
        cutoff = int(time.time()) - 60
        expired = " FROM [group] WHERE name GLOB ? AND date_added<?"
        params = (DONE_PREFIX + "?" * 32, cutoff)
        if db.execute("SELECT 1" + expired + " LIMIT 1", params).fetchone():
            db.execute("DELETE" + expired, params)
            db.commit()


if __name__ == "__main__":
    import fcntl
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("gravity", type=Path)
    parser.add_argument("state", type=Path)
    parser.add_argument("reload_lists", nargs="+")
    args = parser.parse_args()
    lock = args.state.with_suffix(".lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    while True:
        try:
            tick(args.gravity, args.state, args.reload_lists)
        except (sqlite3.Error, OSError, subprocess.SubprocessError):
            logging.exception("Group timer will retry")
        time.sleep(1)
