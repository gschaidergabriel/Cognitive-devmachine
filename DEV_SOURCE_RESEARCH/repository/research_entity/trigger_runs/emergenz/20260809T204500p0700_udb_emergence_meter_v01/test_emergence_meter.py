import tempfile
import unittest
from pathlib import Path

from emergence_meter import run_calibration


class CalibrationTests(unittest.TestCase):
    def test_controls_separate_interaction_from_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            r = run_calibration(Path(td) / "lab.db", n=2400, seed=41)
        self.assertEqual(r["null"]["status"], "NOT_SUPPORTED")
        self.assertNotEqual(r["additive"]["status"], "CAUSAL_EMERGENCE_CANDIDATE_OPEN")
        self.assertIn("COMMON_DRIVER", r["common_driver"]["controls_failed"])
        self.assertEqual(r["xor_no_reentry"]["status"], "MECHANISM_SUPPORTED_NOT_EMERGENCE")
        self.assertEqual(r["xor_reentry"]["status"], "CAUSAL_EMERGENCE_CANDIDATE_OPEN")

    def test_reproducible(self):
        with tempfile.TemporaryDirectory() as td:
            a = run_calibration(Path(td) / "a.db", n=800, seed=9)
            b = run_calibration(Path(td) / "b.db", n=800, seed=9)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
