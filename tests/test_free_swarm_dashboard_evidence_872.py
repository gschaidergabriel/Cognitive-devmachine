#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVALUATE = ROOT / "free swarm" / "evaluate.py"
spec = importlib.util.spec_from_file_location("free_swarm_evaluate", EVALUATE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def nominal_row() -> dict:
    return {
        "schema": "CLAY_FORGE_DELTA_EVALUATION/v1",
        "status": "accepted",
        "source_class": "free_swarm",
        "provider": "test",
        "model": "test-model",
        "delta_id": "delta-1",
        "relative_improvement_pct": 10.0,
        "reproducible_runs": 2,
        "tests_passed": 2,
        "tests_failed": 0,
        "negative_tests_passed": 1,
        "negative_tests_failed": 0,
        "static_checks_passed": 1,
        "static_checks_failed": 0,
        "benchmark_non_regression": True,
    }


def qualified_row() -> dict:
    row = nominal_row()
    source = "1" * 40
    row.update({
        "source_scope": "EXACT_WORKER_PROMPT_HEAD",
        "source_repo_head": source,
        "evaluation_repo_head": "2" * 40,
        "worker_sha": "3" * 64,
        "target_blob_identities": {"tools/demo.py": "4" * 40},
        "execution_admission": {
            "schema": "CLAY_FORGE_EXECUTION_ADMISSION/v1",
            "source_scope": "EXACT_WORKER_PROMPT_HEAD",
            "source_identity_admitted": True,
            "source_head": source,
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
    })
    return row


class FreeSwarmDashboardEvidence872(unittest.TestCase):
    def test_nominal_accept_is_not_evident_accept(self):
        row = nominal_row()
        self.assertTrue(mod.nominal_accept(row))
        self.assertFalse(mod.accepted_delta(row))

    def test_qualified_accept_is_evident_accept(self):
        self.assertTrue(mod.accepted_delta(qualified_row()))

    def test_delta_metrics_keep_nominal_and_qualified_counts_separate(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "evaluations.jsonl"
            ledger.write_text(
                json.dumps(nominal_row(), separators=(",", ":")) + "\n" +
                json.dumps(qualified_row(), separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            got = mod.delta_metrics(ledger)
        self.assertEqual(2, got["nominal_accepted"])
        self.assertEqual(1, got["accepted"])
        self.assertEqual(1, got["legacy_or_unqualified_accepted"])
        self.assertEqual(1, got["qualification_reasons"].get("EVIDENCE_QUALIFIED_ACCEPT"))
        self.assertEqual(1, got["qualification_reasons"].get("SOURCE_SCOPE_NOT_EXACT"))

    def test_visible_metric_label_is_backed_by_qualified_count(self):
        metrics = {
            "generated_at": "2026-08-24T00:00:00+00:00",
            "workers": {"worker_records": 0, "average_concurrency": 0.0, "peak_concurrency": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "exact_usage_rows": 0, "models": []},
            "deltas": {"accepted": 1, "nominal_accepted": 2, "legacy_or_unqualified_accepted": 1, "best_model": None, "innovation_leader": None, "source_classes": {}},
            "corpus": {"approx_tokens_4chars": 0, "output_only_equivalent_usd": 0.0, "text_files": 0, "characters": 0, "sonnet5_output_usd_per_mtok": 10.0},
        }
        rendered = mod.auto_markdown(metrics)
        self.assertIn("Evident akzeptierte Architektur-Deltas | 1", rendered)
        self.assertIn("Nominal/historisch akzeptierte Architektur-Deltas | 2", rendered)
        self.assertIn("Legacy/unqualifizierte nominale Accepts | 1", rendered)


if __name__ == "__main__":
    unittest.main()
