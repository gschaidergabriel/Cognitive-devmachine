import unittest

from v031_conditioning_depth_addendum import run


class ConditioningDepthAddendumTests(unittest.TestCase):
    def test_omitted_history_link_collapses_more_than_direct_link(self):
        result = run(seeds=4, samples=5000, max_depth=2)
        self.assertLess(
            result["depth1_retention_fraction_omitted_path"],
            result["depth1_retention_fraction_true_path"],
        )
        self.assertLess(result["depth1_retention_fraction_omitted_path"], 0.25)

    def test_nonclaim_boundary_is_explicit(self):
        result = run(seeds=2, samples=3000, max_depth=1)
        self.assertFalse(result["live_frank_validated"])
        self.assertIn("NEVER_TREAT_STABILITY_AS_CAUSAL_PROOF", result["adjudication"])


if __name__ == "__main__":
    unittest.main()
