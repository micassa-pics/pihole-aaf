import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from worker import KEEP, snapshot, update, unique_pairs


class HandoffTest(unittest.TestCase):
    def test_promotion_expiry_restart_and_address_reuse(self):
        s = {}
        def sample(t, leases, reservations):
            return [v for line in update(s, t, leases, reservations).splitlines()
                    if not line.startswith(("T ", "R ")) for v in line.split()]
        sample(100, {"a": "old"}, {})
        self.assertEqual(sample(115, {"a": "old"}, {"a": "new"}), [])
        self.assertEqual(s["pending"], {"a": "new"})
        s = json.loads(json.dumps(s))
        sample(130, {}, {"a": "new"})
        sample(145, {"b": "old", "a": "new"}, {"a": "new"})
        self.assertEqual(sample(160, {"b": "old", "a": "new"}, {"a": "new"}),
                         ["new", "old", "100", "115", "new", "new", "145", "160"])
        self.assertEqual(sample(175, {"a": "new"}, {}), [])

    def test_same_ip_and_offline_gap(self):
        s = {}
        self.assertEqual(update(s, 100, {"a": "x"}, {"a": "x"}).splitlines(), ["T 100", "R a x ready"])
        update(s, 200, {"a": "x"}, {"a": "x"})
        self.assertEqual(s["windows"]["a"], [["x", 100, 100], ["x", 200, 200]])

    def test_ambiguous_leases(self):
        self.assertEqual(unique_pairs([("a","x"),("b","x"),("c","y"),("c","z")]), {})

    def test_conflict_then_same_address_reuse(self):
        state = {}
        update(state, 100, {"previous":"x"}, {})
        pending = update(state, 115, {"previous":"x"}, {"new":"x"})
        self.assertIn("R new x pending", pending)
        ready = update(state, 130, {"new":"x"}, {"new":"x"})
        self.assertEqual(ready.splitlines(), ["T 130", "R new x ready", "x x 130 130"])

    def test_pending_reservation_retargeted_outside_ui(self):
        state = {}
        update(state, 100, {"a":"x"}, {"a":"y"})
        self.assertIn("pending", update(state, 115, {"a":"x"}, {"a":"z"}))
        self.assertIn("pending", update(state, 130, {}, {"a":"z"}))
        self.assertIn("z x 100 115", update(state, 145, {"a":"z"}, {"a":"z"}))

    def test_clock_rollback_and_retention(self):
        s = {}
        update(s, 100, {"a":"x"}, {})
        before = json.dumps(s)
        with self.assertRaises(ValueError):
            update(s, 99, {"a":"y"}, {})
        self.assertEqual(before, json.dumps(s))
        update(s, 101 + KEEP, {}, {})
        self.assertEqual(s["windows"], {})

    def test_files_exclude_expired_and_conflicting_leases(self):
        with TemporaryDirectory() as directory:
            config = Path(directory)
            mac = "02:00:00:00:00:01"
            other = "02:00:00:00:00:02"
            (config / "pihole.toml").write_text(f'[dhcp]\nactive=true\nhosts=["{mac},192.0.2.2,printer"]')
            (config / "dhcp.leases").write_text(
                f"100 {mac} 192.0.2.1 expired *\n200 {mac} 192.0.2.2 printer *\n"
                f"0 {other} 192.0.2.2 other *\n")
            leases, reservations, macs, ips = snapshot(config, 100)
            self.assertEqual(leases, {})
            self.assertEqual(reservations, {mac:"192.0.2.2"})
            self.assertEqual(macs, {mac, other})
            self.assertEqual(ips, {"192.0.2.2"})

    def test_two_static_moves_keep_all_observed_addresses(self):
        s = {}
        update(s, 100, {"a":"x"}, {"a":"x"})
        update(s, 115, {}, {"a":"x"})
        first = update(s, 130, {}, {"a":"y"})
        self.assertIn("R a y ready", first)
        self.assertIn("y x 100 115", first)
        update(s, 145, {}, {"a":"y"})
        second = update(s, 160, {"other":"x"}, {"a":"z"})
        self.assertIn("z x 100 115", second)
        self.assertIn("z y 130 145", second)


if __name__ == "__main__":
    unittest.main()
