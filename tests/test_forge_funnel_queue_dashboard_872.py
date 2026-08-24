import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

SAFE_PATH = TOOLS / "run_free_evidence_forge_safe_871.py"
_safe_spec = importlib.util.spec_from_file_location("safe_forge_872", SAFE_PATH)
safe = importlib.util.module_from_spec(_safe_spec)
assert _safe_spec.loader is not None
_safe_spec.loader.exec_module(safe)

DASH_PATH = REPO / "free swarm" / "update_forge_readme.py"
_dash_spec = importlib.util.spec_from_file_location("forge_dashboard_872", DASH_PATH)
dash = importlib.util.module_from_spec(_dash_spec)
assert _dash_spec.loader is not None
_dash_spec.loader.exec_module(dash)


def evidence_row():
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


class BacklogFirstTests(unittest.TestCase):
    def test_ready_backlog_is_evaluated_before_discovery_phase(self):
        events = []
        old_ingest = safe.base.ingest_worker_candidates
        old_eval = safe._evaluate_ready_backlog
        old_cycle = safe._ORIGINAL_CYCLE
        try:
            safe.base.ingest_worker_candidates = lambda con: events.append("ingest")

            async def fake_eval(con, args):
                events.append(("evaluate", args.candidates_per_cycle))
                return 3

            async def fake_cycle(con, args):
                events.append(("base_cycle", args.candidates_per_cycle))
                return 5

            safe._evaluate_ready_backlog = fake_eval
            safe._ORIGINAL_CYCLE = fake_cycle
            args = SimpleNamespace(candidates_per_cycle=8, local_parallel=4)
            total = asyncio.run(safe._backlog_first_cycle(object(), args))
        finally:
            safe.base.ingest_worker_candidates = old_ingest
            safe._evaluate_ready_backlog = old_eval
            safe._ORIGINAL_CYCLE = old_cycle

        self.assertEqual(total, 8)
        self.assertEqual(events, ["ingest", ("evaluate", 8), ("base_cycle", 0)])

    def test_empty_backlog_preserves_normal_cycle(self):
        events = []
        old_ingest = safe.base.ingest_worker_candidates
        old_eval = safe._evaluate_ready_backlog
        old_cycle = safe._ORIGINAL_CYCLE
        try:
            safe.base.ingest_worker_candidates = lambda con: events.append("ingest")

            async def fake_eval(con, args):
                events.append("evaluate")
                return 0

            async def fake_cycle(con, args):
                events.append(("base_cycle", args.candidates_per_cycle))
                return 7

            safe._evaluate_ready_backlog = fake_eval
            safe._ORIGINAL_CYCLE = fake_cycle
            args = SimpleNamespace(candidates_per_cycle=8, local_parallel=4)
            total = asyncio.run(safe._backlog_first_cycle(object(), args))
        finally:
            safe.base.ingest_worker_candidates = old_ingest
            safe._evaluate_ready_backlog = old_eval
            safe._ORIGINAL_CYCLE = old_cycle

        self.assertEqual(total, 7)
        self.assertEqual(events, ["ingest", "evaluate", ("base_cycle", 8)])


class EvidenceDashboardTests(unittest.TestCase):
    def test_nominal_and_evidence_qualified_counts_are_separate(self):
        qualified = evidence_row()
        nominal_only = evidence_row()
        nominal_only.pop("execution_admission")
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "evaluations.jsonl"
            ledger.write_text(
                json.dumps(nominal_only) + "\n" + json.dumps(qualified) + "\n",
                encoding="utf-8",
            )
            out = dash.evidence_counts(ledger, REPO)

        self.assertEqual(out["nominal_accepted_deltas"], 2)
        self.assertEqual(out["evidence_qualified_accepted_deltas"], 1)
        self.assertEqual(out["legacy_or_unqualified_accepted_deltas"], 1)
        self.assertEqual(out["unqualified_nominal_reasons"].get("EXECUTION_ADMISSION_MISSING"), 1)
        self.assertEqual(out["acceptance_semantics"], "EVIDENCE_QUALIFIED_ONLY")

    def test_markdown_uses_only_evidence_qualified_count_for_conversion(self):
        m = {
            "generated_at": "2026-08-24T00:00:00Z",
            "evaluations": 2,
            "nominal_accepted_deltas": 2,
            "evidence_qualified_accepted_deltas": 1,
            "unqualified_nominal_reasons": {"EXECUTION_ADMISSION_MISSING": 1},
        }
        free = {"workers": {"total_tokens": 1_000_000}}
        text = dash.md(m, free, {})
        self.assertIn("nominell/historisch `accepted` | 2", text)
        self.assertIn("evidence-qualified akzeptierte Forge-Deltas** | **1", text)
        self.assertIn("1.000 evidence-qualified Deltas / 1 Mio.", text)


if __name__ == "__main__":
    unittest.main()
