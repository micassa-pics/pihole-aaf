import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from guard import Journal, Problem, operate

MAC = "02:00:00:00:00:01"
OTHER = "02:00:00:00:00:02"


def row(mac, n):
    return mac + ",192.0.2." + str(n) + ",example" + str(n)


class FakeAPI:
    def __init__(self):
        self.rows = [row(MAC,1),row(OTHER,8)]
        self.writes = 0

    def read(self):
        return self.rows[:]

    def write(self, rows):
        self.writes += 1
        self.rows = rows[:]


class GuardTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name)/"journal"
        self.j = Journal(self.path)
        self.addCleanup(lambda:self.j.db.close())
        self.api = FakeAPI()
        self.monitor = {"last":99,"reservations":{MAC:"192.0.2.1",OTHER:"192.0.2.8"},"pending":{},"observed_leases":{}}
        self.base = self.call()
        self.seq = 0

    def call(self, req=None):
        with patch("guard.time.time",return_value=100):
            return operate(self.j,self.api,self.monitor,req or {"action":"read"})

    def save(self, after, base=None):
        self.seq += 1
        base = base or self.base
        return {"id":f"{self.seq:032x}","action":"save","before":base["hosts"],"after":after,"versions":base["versions"]}

    def test_conflict_disjoint_edit_and_replay(self):
        original = self.base["hosts"]
        first = self.save([row(MAC,2),original[1]])
        self.call(first)
        with self.assertRaises(Problem):
            self.call(self.save([row(MAC,3),original[1]]))
        self.call(self.save([original[0],row(OTHER,9)]))
        self.call(first)
        self.assertEqual(self.api.rows,[row(MAC,2),row(OTHER,9)])
        self.assertEqual(self.api.writes,2)

    def test_crash_between_patch_and_receipt(self):
        request = self.save([row(MAC,2),row(OTHER,8)])
        def interrupted(rows):
            FakeAPI.write(self.api,rows)
            raise OSError("lost connection")
        with patch.object(self.api,"write",side_effect=interrupted), self.assertRaises(OSError):
            self.call(request)
        self.j.db.close()
        self.j = Journal(self.path)
        self.assertIn(MAC,self.call(request)["locks"])
        self.assertEqual(self.api.writes,1)
        self.assertEqual(self.call({"action":"status","id":request["id"]})["outcome"],"saved")

    def test_manual_order_preserved_and_stale_reorder_refused(self):
        self.call(self.save(self.base["hosts"][::-1]))
        self.assertEqual(self.api.rows,self.base["hosts"][::-1])
        self.api.rows.append("192.0.2.50,external")
        with self.assertRaises(Problem):
            self.call(self.save(self.base["hosts"][::-1]))

    def test_uncertain_write_requires_review(self):
        with patch.object(self.api,"write",side_effect=OSError()), self.assertRaises(OSError):
            self.call(self.save([row(MAC,2),row(OTHER,8)]))
        v=self.call()
        self.assertEqual(v["locks"][MAC]["kind"],"review")
        self.call({"action":"review","key":MAC,"id":"f"*32,"versions":v["versions"]})
        self.assertNotIn(MAC,self.call()["locks"])

    def test_static_release_external_and_cancel(self):
        self.call(self.save([row(MAC,2),row(OTHER,8)]))
        v=self.call()
        with self.assertRaises(Problem):
            self.call(self.save([row(MAC,3),row(OTHER,8)],v))
        self.monitor["last"]=101
        self.monitor["reservations"][MAC]="192.0.2.2"
        v=self.call()
        self.assertNotIn(MAC,v["locks"])
        v=self.call(self.save([row(MAC,3),row(OTHER,8)],v))
        self.monitor["reservations"][MAC]="192.0.2.3"
        self.call({"action":"cancel","key":MAC,"id":"a"*32,"versions":v["versions"]})
        self.assertEqual(self.api.rows[0],row(MAC,2))
        self.api.rows[0]=row(MAC,4)
        self.assertEqual(self.call()["locks"][MAC]["kind"],"review")

    def test_lease_release_requires_actual_matching_lease(self):
        mac = "02:00:00:00:00:03"
        self.monitor["observed_leases"][mac]=["192.0.2.7",99]
        v=self.call(self.save(self.base["hosts"]+[row(mac,5)]))
        self.assertEqual(v["locks"][mac]["kind"],"lease")
        self.monitor["last"]=110
        self.monitor["reservations"][mac]="192.0.2.5"
        self.assertIn(mac,self.call()["locks"])
        self.monitor["observed_leases"][mac]=["192.0.2.5",110]
        self.assertNotIn(mac,self.call()["locks"])


if __name__ == "__main__":
    unittest.main()

