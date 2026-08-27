import unittest

import research_interconnect_preflight as rip


class ResearchInterconnectQ23RegressionTests(unittest.TestCase):
    def test_q23_is_registered_peer(self):
        self.assertIn("q23", rip.BRANCHES)

    def test_every_priority_exactly_covers_current_registry(self):
        expected = set(rip.BRANCHES)
        for trigger, order in rip.PRIORITY.items():
            with self.subTest(trigger=trigger):
                self.assertEqual(set(order), expected)
                self.assertEqual(len(order), len(expected))

    def test_q23_has_direct_preflight_route(self):
        self.assertIn("q23", rip.PRIORITY)
        self.assertIn("harness", rip.PRIORITY["q23"])
        self.assertIn("frank", rip.PRIORITY["q23"])

    def test_harness_ingests_q23(self):
        self.assertIn("q23", rip.PRIORITY["harness"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
