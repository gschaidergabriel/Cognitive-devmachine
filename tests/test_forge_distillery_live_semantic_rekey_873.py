from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import ingest_forge_accepts_into_distillery as bridge
import promote_forge_distillery_runtime_gate as promotion

SOURCE = "1" * 40
TREE = "2" * 40


def qualified_evaluation() -> dict:
    return {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "delta_id": "live-semantic-rekey-873",
        "source_class": "deterministic_test_fixture",
        "provider": "local_deterministic",
        "model": "none",
        "role": "RUNTIME",
        "worker_sha": "a" * 64,
        "source_repo_head": SOURCE,
        "evaluation_repo_head": SOURCE,
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "evaluated_at": "2026-08-25T00:00:00+00:00",
        "status": "accepted",
        "metric": "deterministic_test_metric",
        "relative_improvement_pct": 100.0,
        "reproducible_runs": 2,
        "tests_passed": 2,
        "tests_failed": 0,
        "negative_tests_passed": 1,
        "negative_tests_failed": 0,
        "static_checks_passed": 1,
        "static_checks_failed": 0,
        "benchmark_non_regression": True,
        "reverted": False,
        "target_blob_identities": {
            "tools/ingest_forge_accepts_into_distillery.py": "b" * 40,
        },
        "requires_rebase_to_evaluation_head": False,
        "execution_admission": {
            "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
            "source_scope": "EXACT_WORKER_PROMPT_HEAD",
            "source_identity_admitted": True,
            "source_head": SOURCE,
            "evaluation_checkout_head": SOURCE,
            "decisions": [
                {
                    "admitted": True,
                    "argv": ["python3", "-m", "unittest"],
                }
            ],
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


def passing_gate(evaluation: dict) -> dict:
    return {
        "schema": promotion.PASS_SCHEMA,
        "pass": True,
        "status": promotion.PASS_STATUS,
        "source_sha": SOURCE,
        "source_tree": TREE,
        "network_used": False,
        "provider_calls": 0,
        "paid_fallback_attempt_count": 0,
        "acceptance_witness": {
            "nominal_without_execution_admission_rejected": True,
            "exact_evidence_qualified_accept": 1,
            "first_new_distillery_packets": 1,
            "accepted_dataset_tokens_after_first": 10,
            "replay_new_packets": 0,
            "replay_duplicates": 1,
            "token_delta_on_replay": 0,
            "accepted_dataset_tokens_after_replay": 10,
        },
        "distillery_first": {
            "admitted": 1,
            "accepted_dataset_tokens_counter": 10,
        },
        "distillery_replay": {
            "admitted": 0,
            "duplicates": 1,
            "accepted_dataset_tokens_counter": 10,
        },
        "forge_evaluation": evaluation,
    }


def context() -> dict:
    return {
        "expected_source_tree": TREE,
        "github_run_id": "87301",
        "github_event_name": "push",
        "source_selection": promotion.CANONICAL_SOURCE_SELECTION,
    }


class LiveSemanticRekey873Tests(unittest.TestCase):
    def test_envelope_rekey_changes_full_evaluation_not_execution_or_measurement_identity(self):
        evaluation = qualified_evaluation()
        replay = promotion.semantic_replay_variant(evaluation)

        self.assertNotEqual(replay["delta_id"], evaluation["delta_id"])
        self.assertNotEqual(replay["evaluated_at"], evaluation["evaluated_at"])
        self.assertNotEqual(bridge.digest_json(replay), bridge.digest_json(evaluation))
        self.assertEqual(
            bridge.execution_replay_identity(replay),
            bridge.execution_replay_identity(evaluation),
        )
        self.assertEqual(
            bridge.measured_evidence_identity(replay),
            bridge.measured_evidence_identity(evaluation),
        )

    def test_live_promotion_semantic_rekey_zero_delta_conflict_fails_closed_and_restart_stays_zero(self):
        evaluation = qualified_evaluation()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            gate_path = root / "gate.json"
            db = root / "distillery.sqlite3"
            gate_path.write_text(json.dumps(passing_gate(evaluation)) + "\n", encoding="utf-8")

            first = promotion.promote(gate_path, SOURCE, db, **context())
            second = promotion.promote(gate_path, SOURCE, db, **context())

        self.assertEqual(first["status"], "PASS")
        self.assertEqual(first["outcome"], "PROMOTED_NEW_PACKET")
        self.assertEqual(first["semantic_replay"]["admitted"], 0)
        self.assertEqual(first["semantic_replay"]["duplicates"], 1)
        self.assertEqual(first["semantic_replay_token_delta"], 0)
        self.assertEqual(first["measured_conflict"]["duplicates"], 0)
        self.assertEqual(
            first["measured_conflict"]["rejected"].get("REPLAY_IDENTITY_CONFLICT"),
            1,
        )
        self.assertEqual(first["measured_conflict_token_delta"], 0)
        self.assertTrue(first["reopen_persistence_exercised"])
        self.assertEqual(
            first["after"]["measured_evidence_sha256"],
            first["measured_evidence_sha256"],
        )

        self.assertEqual(second["status"], "PASS")
        self.assertEqual(second["outcome"], "ALREADY_PROMOTED_IDEMPOTENT")
        self.assertEqual(second["first_token_delta"], 0)
        self.assertEqual(second["semantic_replay_token_delta"], 0)
        self.assertEqual(second["measured_conflict_token_delta"], 0)
        self.assertEqual(
            second["after"]["accepted_dataset_tokens_counter"],
            first["after"]["accepted_dataset_tokens_counter"],
        )


if __name__ == "__main__":
    unittest.main()
