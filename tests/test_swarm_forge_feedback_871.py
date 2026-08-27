from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_24h_entityos_swarm as swarm


class ForgeFeedback871Tests(unittest.TestCase):
    def _eval_file(self, root: Path) -> Path:
        path = root / "architecture_delta_evaluations.jsonl"
        rows = [
            {"record_type": "schema_marker", "status": "ignored"},
            {"status": "patch_rejected", "reason": "error: No valid patches in input"},
            {"status": "patch_rejected", "reason": "error: corrupt patch at line 4"},
            {
                "status": "needs_implementation",
                "reason": "missing/safety-invalid patch, targets, or tests",
            },
            {"status": "patch_rejected", "reason": "error: x/y: No such file or directory"},
            {"status": "accepted", "relative_improvement_pct": 10.0},
        ]
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        return path

    def test_feedback_compresses_pre_execution_rejections_without_minting_authority(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feedback = swarm.forge_failure_feedback(self._eval_file(Path(td)))
        self.assertEqual(feedback["authority"], "NONCANONICAL_FEEDBACK_ONLY")
        self.assertEqual(feedback["evaluations_sampled"], 5)
        self.assertEqual(feedback["status_counts"]["patch_rejected"], 3)
        self.assertEqual(feedback["status_counts"]["needs_implementation"], 1)
        self.assertEqual(feedback["accepted_count"], 1)
        self.assertEqual(feedback["pre_execution_reject_count"], 4)
        reasons = dict(feedback["top_failure_reasons"])
        self.assertEqual(reasons["NO_VALID_UNIFIED_PATCH"], 1)
        self.assertEqual(reasons["CORRUPT_UNIFIED_PATCH"], 1)
        self.assertEqual(reasons["MISSING_OR_SAFETY_INVALID_PATCH_TARGETS_OR_TESTS"], 1)
        self.assertEqual(reasons["TARGET_PATH_NOT_IN_REPOSITORY"], 1)

    def test_missing_evaluation_file_fails_soft_as_noncanonical_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feedback = swarm.forge_failure_feedback(Path(td) / "missing.jsonl")
        self.assertEqual(
            feedback,
            {"authority": "NONCANONICAL_FEEDBACK_ONLY", "evaluations_sampled": 0},
        )

    def test_live_runtime_truth_carries_forge_status_and_failure_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "forge").mkdir(parents=True)
            (root / "forge/STATUS.json").write_text(
                json.dumps({"accepted_deltas": 0, "candidate_states": {"PATCH_REJECTED": 3}}),
                encoding="utf-8",
            )
            self._eval_file(root / "forge")
            old_root = swarm.ARTIFACT_ROOT
            try:
                swarm.ARTIFACT_ROOT = root
                payload = json.loads(swarm.live_runtime_truth(20000))
            finally:
                swarm.ARTIFACT_ROOT = old_root
        self.assertEqual(payload["forge_status"]["accepted_deltas"], 0)
        self.assertEqual(payload["forge_failure_feedback"]["pre_execution_reject_count"], 4)
        self.assertEqual(payload["forge_failure_feedback"]["authority"], "NONCANONICAL_FEEDBACK_ONLY")

    def test_worker_prompt_fails_closed_before_ready_for_forge_true(self) -> None:
        old = swarm._ORIGINAL_WORKER_PROMPT
        try:
            swarm._ORIGINAL_WORKER_PROMPT = lambda *args: "BASE"
            prompt = swarm.optimized_worker_prompt("P", "R", "T", "{}", 7)
        finally:
            swarm._ORIGINAL_WORKER_PROMPT = old
        self.assertIn("ready_for_forge=true is an executable transport claim", prompt)
        self.assertIn("complete real unified diff", prompt)
        self.assertIn("NO Markdown/code fences", prompt)
        self.assertIn("exact hunk line counts", prompt)
        self.assertIn("negative_test_commands", prompt)
        self.assertIn("ready_for_forge=false", prompt)
        self.assertIn("forge_failure_feedback", prompt)


if __name__ == "__main__":
    unittest.main()
