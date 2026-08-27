from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

MODULE = TOOLS / "ingest_forge_accepts_into_distillery.py"
spec = importlib.util.spec_from_file_location("bridge", MODULE)
bridge = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bridge)


def exact_row() -> dict:
    head = "1" * 40
    worker = "2" * 64
    return {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "status": "accepted",
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "source_repo_head": head,
        "evaluation_repo_head": head,
        "worker_sha": worker,
        "target_blob_identities": {"tools/example.py": "3" * 40},
        "relative_improvement_pct": 10.0,
        "reproducible_runs": 2,
        "tests_passed": 2,
        "tests_failed": 0,
        "negative_tests_passed": 1,
        "negative_tests_failed": 0,
        "static_checks_passed": 1,
        "static_checks_failed": 0,
        "benchmark_non_regression": True,
        "reverted": False,
        "execution_admission": None,
    }


class ForgeDistilleryEvidenceAdmission871(unittest.TestCase):
    def test_exact_nominal_accept_without_execution_admission_is_rejected(self):
        ok, reason = bridge.admission_reason(exact_row())
        self.assertFalse(ok)
        self.assertEqual("EXECUTION_ADMISSION_MISSING", reason)


if __name__ == "__main__":
    unittest.main()
