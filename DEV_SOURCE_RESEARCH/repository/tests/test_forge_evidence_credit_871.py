import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "tools" / "forge_evidence_credit_871.py"
spec = importlib.util.spec_from_file_location("guard", MODULE)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def base_row():
    return {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "record_type": "forge_evaluation",
        "status": "accepted",
        "worker_sha": "b" * 64,
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "source_repo_head": "a" * 40,
        "evaluation_repo_head": "c" * 40,
        "target_blob_identities": {"tools/x.py": "d" * 40},
        "relative_improvement_pct": 10.0,
        "reproducible_runs": 2,
        "tests_passed": 2,
        "tests_failed": 0,
        "negative_tests_failed": 0,
        "static_checks_failed": 0,
        "benchmark_non_regression": True,
        "reverted": False,
        "execution_admission": {
            "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
            "source_scope": "EXACT_WORKER_PROMPT_HEAD",
            "source_identity_admitted": True,
            "source_head": "a" * 40,
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


class EvidenceCreditTests(unittest.TestCase):
    def test_fully_bound_acceptance_qualifies(self):
        self.assertEqual(guard.evidence_reason(base_row()), (True, "EVIDENCE_QUALIFIED_ACCEPT"))

    def test_legacy_current_style_accept_is_nominal_but_not_evidence_qualified(self):
        row = base_row()
        for key in ("source_scope", "source_repo_head", "evaluation_repo_head", "target_blob_identities", "execution_admission"):
            row.pop(key)
        self.assertTrue(guard.nominal_accept(row))
        self.assertEqual(guard.evidence_reason(row), (False, "SOURCE_SCOPE_NOT_EXACT"))

    def test_unisolated_backend_fails_closed(self):
        row = base_row()
        row["execution_admission"]["backend"]["network_namespace"] = "UNAVAILABLE"
        self.assertEqual(guard.evidence_reason(row), (False, "ISOLATION_NOT_PROVEN"))

    def test_source_mismatch_fails_closed(self):
        row = base_row()
        row["execution_admission"]["source_head"] = "e" * 40
        self.assertEqual(guard.evidence_reason(row), (False, "EXECUTION_SOURCE_HEAD_MISMATCH"))

    def test_audit_separates_nominal_from_qualified(self):
        legacy = base_row()
        legacy.pop("source_scope")
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ledger.jsonl"
            p.write_text(json.dumps(legacy) + "\n" + json.dumps(base_row()) + "\n", encoding="utf-8")
            out = guard.audit(p)
        self.assertEqual(out["nominal_accepted"], 2)
        self.assertEqual(out["evidence_qualified_accepted"], 1)
        self.assertEqual(out["legacy_or_unqualified_accepted"], 1)


if __name__ == "__main__":
    unittest.main()
