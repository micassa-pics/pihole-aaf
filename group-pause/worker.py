"""Apply authenticated sidebar requests and restore groups when their timers end."""
from contextlib import closing
import argparse
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

    requests = db.execute(
        'SELECT id,name,description,date_added FROM "group" WHERE enabled=0 AND name GLOB ?',
        (PREFIX + "*",),
    ).fetchall()
    for rid, name, description, submitted in requests:
        if not REQUEST.fullmatch(name):
            continue
        try:
            req = json.loads(description)
            seconds, targets = req["seconds"], req["groups"]
            if type(seconds) is not int or not 0 <= seconds <= MAX_SECONDS or not isinstance(targets, list) or not targets:
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
        queued = db.execute('SELECT 1 FROM "group" WHERE enabled=0 AND name GLOB ? LIMIT 1', (PREFIX + "*",)).fetchone()
        tracking = db.execute("SELECT 1 FROM scheduler.timers LIMIT 1").fetchone()
        if queued or tracking:
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
