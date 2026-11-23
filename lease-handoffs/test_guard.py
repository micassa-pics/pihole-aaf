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
        self.leases = []

    def read(self):
        return self.rows[:]

    def write(self, rows):
        self.writes += 1
        self.rows = rows[:]

    def active_leases(self):
        return self.leases[:]


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

    def test_repair_conflicting_rules_after_monitor_reads_them(self):
        self.api.rows=[row(MAC,1),row(OTHER,1)]
        self.j.db.execute("DELETE FROM journal")
        base=self.call()
        self.monitor.update(reservations={},host_rules=base["hosts"][:])
        v=self.call(self.save([row(MAC,2),row(OTHER,1)],base))
        self.assertIn(MAC,v["locks"])
        self.assertEqual(self.api.writes,1)

    def test_disabled_dhcp_requires_matching_config_checkpoint(self):
        self.monitor.update(dhcp_enabled=False,reservations={},host_rules=self.api.rows[:])
        self.call(self.save([row(MAC,2),row(OTHER,8)]))
        self.monitor["last"]=101
        self.assertIn(MAC,self.call()["locks"])
        self.monitor["host_rules"]=self.api.rows[:]
        self.assertNotIn(MAC,self.call()["locks"])

    def test_outage_cannot_bypass_a_monitor_only_lock(self):
        self.monitor=None
        with self.assertRaises(Problem):
            self.call(self.save([row(OTHER,8)]))
        self.assertEqual(self.api.writes,0)

    def test_monitor_only_move_can_be_reviewed_but_never_cancelled(self):
        self.monitor["pending"][MAC] = "192.0.2.1"
        view = self.call()
        self.assertEqual(view["locks"][MAC]["kind"], "review")
        request = {"action": "cancel", "key": MAC, "id": "b" * 32, "versions": view["versions"]}
        with self.assertRaises(Problem):
            self.call(request)
        view = self.call({**request, "action": "review"})
        self.assertTrue(view["locks"][MAC]["waitOnly"])
        with self.assertRaises(Problem):
            self.call({**request, "id": "c" * 32, "versions": view["versions"]})
        self.assertEqual(self.api.rows, self.base["hosts"])
        self.assertEqual(self.api.writes, 0)

    def test_active_or_ambiguous_lease_blocks_target(self):
        request = self.save([row(MAC,2), row(OTHER,8)])
        self.monitor["active_leases"] = {OTHER: "192.0.2.2"}
        with self.assertRaisesRegex(Problem, "leased to another device"):
            self.call(request)
        self.monitor["active_leases"] = {}
        self.monitor["ambiguous_ips"] = ["192.0.2.2"]
        with self.assertRaisesRegex(Problem, "ambiguous"):
            self.call(request)
        self.assertEqual(self.api.writes, 0)

    def test_external_edit_before_write_is_detected(self):
        request = self.save([row(MAC,2), row(OTHER,8)])
        external = [row(MAC,1), row(OTHER,9)]
        with patch.object(self.api, "read", side_effect=[self.api.rows, external]):
            with self.assertRaisesRegex(Problem, "changed before the save"):
                self.call(request)
        self.assertEqual(self.api.writes, 0)
        self.assertIsNone(self.j.load()["intent"])

    def test_live_lease_arriving_after_checkpoint_blocks_write(self):
        self.api.leases = [{"ip": "192.0.2.2", "hwaddr": OTHER, "expires": 101}]
        with self.assertRaisesRegex(Problem, "leased to another device"):
            self.call(self.save([row(MAC,2), row(OTHER,8)]))
        self.assertEqual(self.api.writes, 0)

    def test_denied_api_write_does_not_leave_intent(self):
        with patch.object(self.api,"write",side_effect=Problem("Denied",403)), self.assertRaises(Problem):
            self.call(self.save([row(MAC,2),row(OTHER,8)]))
        self.assertIsNone(self.j.load()["intent"])
        self.assertEqual(self.call()["locks"],{})


if __name__ == "__main__":
    unittest.main()

