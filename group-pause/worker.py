"""Apply authenticated sidebar requests and restore groups when their timers end."""
from contextlib import closing
import argparse
import ipaddress
import json
import logging
import re
import sqlite3
import subprocess
import time
from pathlib import Path

PREFIX = "awesome-a-fyer-pause-"
REQUEST = re.compile(PREFIX + "[0-9a-f]{32}")
MAX_SECONDS = 2**31 - 1


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
    if db.execute("SELECT 1 FROM device_timers WHERE ip=?", (ip,)).fetchone():
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
    db.execute("INSERT INTO device_timers VALUES(?,?,?,?,?,?,?)",
               (ip, cid, rid, marker, json.dumps(old), temporary, deadline))
    return True


def restore_device(db, row):
    ip, cid, gid, marker, old, temporary, _ = row
    client = db.execute("SELECT ip,comment FROM client WHERE id=?", (cid,)).fetchone()
    groups = {g for (g,) in db.execute("SELECT group_id FROM client_by_group WHERE client_id=?", (cid,))}
    owned = db.execute('SELECT 1 FROM "group" WHERE id=? AND name=?', (gid, marker)).fetchone()
    if client and exact_ip(client[0]) == ip and (groups == {gid} or (not owned and not groups)):
        if temporary and not client[1]:
            db.execute("DELETE FROM client WHERE id=?", (cid,))
        else:
            for original in json.loads(old):
                db.execute('INSERT OR IGNORE INTO client_by_group SELECT ?,id FROM "group" WHERE id=?', (cid, original))
    if owned:
        db.execute('DELETE FROM "group" WHERE id=? AND name=?', (gid, marker))
    db.execute("DELETE FROM device_timers WHERE ip=?", (ip,))


def process(db, now):
    """Keep each group update and its recovery record in one transaction."""
    changed = False
    for gid, created, deadline in db.execute("SELECT id, created, deadline FROM timers").fetchall():
        group = db.execute('SELECT enabled, date_added FROM "group" WHERE id=?', (gid,)).fetchone()
        if group == (0, created) and deadline > now:
            continue
        if group == (0, created):
            db.execute('UPDATE "group" SET enabled=1 WHERE id=?', (gid,))
            changed = True
        db.execute("DELETE FROM timers WHERE id=?", (gid,))

    for row in db.execute("SELECT * FROM device_timers WHERE deadline>0 AND deadline<=?", (now,)).fetchall():
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
            req = json.loads(description)
            seconds = req["seconds"]
            if type(seconds) is not int or not 0 <= seconds <= MAX_SECONDS:
                continue
            if "device" in req:
                ip = req["device"]
                if isinstance(ip, str) and exact_ip(ip) == ip and 0 <= now - submitted <= 15:
                    if req.get("resume") is True:
                        row = db.execute("SELECT * FROM device_timers WHERE ip=?", (ip,)).fetchone()
                        if row:
                            restore_device(db, row)
                            changed = True
                    elif pause_device(db, ip, rid, name, now + seconds if seconds else 0):
                        changed = True
                        continue
                db.execute('DELETE FROM "group" WHERE id=?', (rid,))
                continue
            targets = req["groups"]
            if not isinstance(targets, list) or not targets:
                continue
            if not all(isinstance(t, dict) and type(t.get("id")) is int and isinstance(t.get("name"), str) for t in targets):
                continue
        except (KeyError, ValueError, TypeError):
            continue
        # A stopped worker must never start an old pause when it comes back.
        if 0 <= now - submitted <= 15:
            groups = [db.execute('SELECT id,date_added FROM "group" WHERE id=? AND name=? AND enabled=1',
                                 (t["id"], t["name"])).fetchone() for t in targets]
            if all(groups) and len(set(groups)) == len(groups):
                for gid, created in groups:
                    db.execute('UPDATE "group" SET enabled=0 WHERE id=?', (gid,))
                    if seconds:
                        db.execute("INSERT OR REPLACE INTO timers VALUES (?,?,?)", (gid, created, now + seconds))
                changed = True
        db.execute('DELETE FROM "group" WHERE id=?', (rid,))
    if changed:
        db.execute("INSERT OR IGNORE INTO reload_pending VALUES (1)")


def tick(gravity, state, reload_lists):
    # Reopen each time because Pi-hole can replace gravity.db during an update.
    with closing(sqlite3.connect(gravity.resolve().as_uri() + "?mode=rw", uri=True, timeout=5)) as db:
        db.execute("ATTACH DATABASE ? AS scheduler", (str(state),))
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("CREATE TABLE IF NOT EXISTS scheduler.timers (id INTEGER PRIMARY KEY, created INTEGER, deadline INTEGER)")
        db.execute("CREATE TABLE IF NOT EXISTS scheduler.reload_pending (id INTEGER PRIMARY KEY)")
        db.execute("CREATE TABLE IF NOT EXISTS scheduler.device_timers (ip TEXT PRIMARY KEY, cid INTEGER, gid INTEGER, marker TEXT, original_groups TEXT, temporary INTEGER, deadline INTEGER)")
        queued = db.execute('SELECT 1 FROM "group" WHERE enabled=0 AND name GLOB ? LIMIT 1', (PREFIX + "*",)).fetchone()
        tracking = db.execute("SELECT 1 FROM scheduler.timers LIMIT 1").fetchone()
        due = db.execute("SELECT 1 FROM device_timers WHERE deadline>0 AND deadline<=? LIMIT 1", (int(time.time()),)).fetchone()
        if queued or tracking or due:
            db.execute("BEGIN IMMEDIATE")
            process(db, int(time.time()))
            db.commit()
        if db.execute("SELECT 1 FROM scheduler.reload_pending").fetchone():
            subprocess.run(reload_lists, check=True, timeout=30)
            db.execute("DELETE FROM scheduler.reload_pending")
            db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("gravity", type=Path)
    parser.add_argument("state", type=Path)
    parser.add_argument("reload_lists", nargs="+")
    args = parser.parse_args()
    while True:
        try:
            tick(args.gravity, args.state, args.reload_lists)
        except (sqlite3.Error, OSError, subprocess.SubprocessError):
            logging.exception("Group timer will retry")
        time.sleep(1)
