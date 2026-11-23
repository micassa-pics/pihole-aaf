import json
import unittest

from worker import update, unique_pairs


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
