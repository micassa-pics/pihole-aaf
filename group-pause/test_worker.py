import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import worker


class GroupPauseTest(unittest.TestCase):
    def test_timer_lifecycle(self):
        with tempfile.TemporaryDirectory() as root:
            gravity = Path(root) / "gravity.db"
            state = Path(root) / "timer.db"
            db = sqlite3.connect(gravity)
            self.addCleanup(db.close)
            db.execute('CREATE TABLE "group"(id INTEGER PRIMARY KEY,name TEXT,enabled INTEGER,date_added INTEGER,description TEXT)')
            db.executemany('INSERT INTO "group" VALUES(?,?,?,1000,NULL)',
                           [(0, "Default", 1), (1, "TV", 1), (2, "Music", 1), (3, "Off", 0)])
            db.commit()

            def request(groups, seconds, now):
                targets = [{"id": i, "name": name} for i, name in groups]
                db.execute('INSERT INTO "group" VALUES(10,?,0,?,?)',
                           (worker.PREFIX + "a" * 32, now, json.dumps({"groups": targets, "seconds": seconds})))
                db.commit()

            def check(now, flags):
                with patch.object(worker.time, "time", return_value=now), patch.object(worker.subprocess, "run"):
                    worker.tick(gravity, state, ["reload"])
                self.assertEqual([r[0] for r in db.execute('SELECT enabled FROM "group" ORDER BY id')], flags)

            request([(1, "TV"), (2, "Music")], 10, 1000)
            check(1000, [1, 0, 0, 0])
            check(1009, [1, 0, 0, 0])
            check(1011, [1, 1, 1, 0])
            request([(1, "TV"), (3, "Off")], 10, 1011)
            check(1012, [1, 1, 1, 0])
            request([(1, "TV")], 0, 1012)
            check(1012, [1, 0, 1, 0])
            request([(2, "Music")], 10, 1012)
            check(1030, [1, 0, 1, 0])
            db.execute("CREATE TABLE client(id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT UNIQUE, comment TEXT)")
            db.execute("CREATE TABLE client_by_group(client_id INTEGER REFERENCES client ON DELETE CASCADE, group_id INTEGER REFERENCES \"group\" ON DELETE CASCADE, PRIMARY KEY(client_id, group_id))")
            db.executemany("INSERT INTO client VALUES(?,?,?)", [(1, "192.0.2.1/32", "keep"), (2, "192.0.2.2", None)])
            db.executemany("INSERT INTO client_by_group VALUES(?,?)", [(1, 0), (1, 2), (2, 2)])
            db.commit()

            def device(ip, seconds, now, resume=False):
                payload = json.dumps({"device": ip, "seconds": seconds, "resume": resume})
                db.execute('INSERT INTO "group"(name,enabled,date_added,description) VALUES(?,0,?,?)',
                           (worker.PREFIX + "b" * 32, now, payload))
                db.commit()
                advance(now)

            def advance(now):
                with patch.object(worker.time, "time", return_value=now), patch.object(worker.subprocess, "run"):
                    worker.tick(gravity, state, ["reload"])

            def membership(cid):
                return set(db.execute("SELECT group_id FROM client_by_group WHERE client_id=?", (cid,)))

            device("192.0.2.1", 10, 1100)
            self.assertEqual(membership(2), {(2,)})
            self.assertFalse(membership(1) & {(0,), (2,)})
            self.assertEqual(len(membership(1)), 1)
            advance(1110)
            self.assertEqual(membership(1), {(0,), (2,)})
            self.assertEqual(db.execute("SELECT ip,comment FROM client WHERE id=1").fetchone(), ("192.0.2.1/32", "keep"))

            device("2001:db8::5", 0, 1120)
            advance(9000)
            self.assertTrue(db.execute("SELECT 1 FROM client WHERE ip='2001:db8::5'").fetchone())
            device("2001:db8::5", 0, 9000, resume=True)
            self.assertFalse(db.execute("SELECT 1 FROM client WHERE ip='2001:db8::5'").fetchone())
            db.close()


if __name__ == "__main__":
    unittest.main()
