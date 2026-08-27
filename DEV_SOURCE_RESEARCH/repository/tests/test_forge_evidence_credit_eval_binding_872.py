from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools" / "forge_evidence_credit_871.py"
spec = importlib.util.spec_from_file_location("forge_credit_872", MODULE)
forge_credit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(forge_credit)

HEAD = "1" * 40
WORKER = "2" * 64


def exact_row() -> dict:
    return {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "status": "accepted",
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "source_repo_head": HEAD,
        "evaluation_repo_head": HEAD,
        "worker_sha": WORKER,
        "target_blob_identities": {"tools/example.py": "3" * 40},
        "relative_improvement_pct": 5.0,
        "reproducible_runs": 2,
        "tests_passed": 2,
        "tests_failed": 0,
        "negative_tests_passed": 1,
        "negative_tests_failed": 0,
        "static_checks_passed": 1,
        "static_checks_failed": 0,
        "benchmark_non_regression": True,
        "reverted": False,
        "execution_admission": {
            "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
            "source_scope": "EXACT_WORKER_PROMPT_HEAD",
            "source_identity_admitted": True,
            "source_head": HEAD,
            "evaluation_checkout_head": HEAD,
            "decisions": [{"admitted": True, "reason": "ALLOWLISTED", "argv": ["python3", "-m", "unittest"], "class": "TEST"}],
            "all_commands_admitted": True,
            "candidate_is_canonical_truth": False,
            "backend": {
                "admitted": True,
                "backend": "bubblewrap_unshare_all",
                "network_namespace": "ISOLATED",
                "secret_environment_inherited": False,
                "host_secret_paths_exposed": False,
            },
        },
    }


class ForgeEvidenceCheckoutBinding872(unittest.TestCase):
    def test_exact_row_is_creditable(self):
        self.assertEqual((True, "EVIDENCE_QUALIFIED_ACCEPT"), forge_credit.evidence_reason(exact_row()))

    def test_missing_evaluation_checkout_head_fails_closed(self):
        row = exact_row()
        del row["execution_admission"]["evaluation_checkout_head"]
        self.assertEqual((False, "EXECUTION_EVALUATION_HEAD_UNBOUND"), forge_credit.evidence_reason(row))

    def test_mismatched_evaluation_checkout_head_fails_closed(self):
        row = exact_row()
        row["execution_admission"]["evaluation_checkout_head"] = "4" * 40
        self.assertEqual((False, "EXECUTION_EVALUATION_HEAD_MISMATCH"), forge_credit.evidence_reason(row))

    def test_empty_decisions_do_not_pass_vacuously(self):
        row = exact_row()
        row["execution_admission"]["decisions"] = []
        row["execution_admission"]["all_commands_admitted"] = True
        self.assertEqual((False, "EXECUTION_COMMAND_DECISIONS_MISSING"), forge_credit.evidence_reason(row))

    def test_rejected_decision_overrides_aggregate_true(self):
        row = exact_row()
        row["execution_admission"]["decisions"][0]["admitted"] = False
        row["execution_admission"]["all_commands_admitted"] = True
        self.assertEqual((False, "EXECUTION_COMMAND_DECISION_REJECTED"), forge_credit.evidence_reason(row))


if __name__ == "__main__":
    unittest.main()
