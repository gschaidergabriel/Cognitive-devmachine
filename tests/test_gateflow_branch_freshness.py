import importlib.util
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "gateflow_branch_freshness.py"
spec = importlib.util.spec_from_file_location("gateflow_branch_freshness", TOOL)
m = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(m)


class BranchFreshnessTests(unittest.TestCase):
    def test_behind_alone_never_red_for_receipt(self):
        row = m.classify({
            "id": "receipt",
            "branch": "research/x",
            "base_branch": "main",
            "ahead_by": 1,
            "behind_by": 500,
            "head_files": ["research_entity/trigger_runs/go/x/RESEARCH_RECEIPT.json"],
            "main_since_base_files": ["tools/compiler.py", "research_entity/runtime/core.py"],
            "dependency_cone": [],
        })
        self.assertEqual(row["freshness"], "GREEN")
        self.assertEqual(row["disposition"], "EVIDENCE_ONLY_APPEND")

    def test_direct_overlap_is_red(self):
        row = m.classify({
            "id": "runtime",
            "branch": "feature/runtime",
            "base_branch": "main",
            "ahead_by": 2,
            "behind_by": 1,
            "head_files": ["research_entity/runtime/provider.py"],
            "main_since_base_files": ["research_entity/runtime/provider.py"],
            "dependency_cone": [],
        })
        self.assertEqual(row["freshness"], "RED")
        self.assertEqual(row["recommendation"], "REBASE_AND_RERUN")

    def test_dependency_cone_hit_is_red_without_file_overlap(self):
        row = m.classify({
            "id": "compiler",
            "branch": "feature/compiler",
            "base_branch": "main",
            "ahead_by": 3,
            "behind_by": 70,
            "head_files": ["tools/new_lowering.py"],
            "main_since_base_files": ["research_entity/claycode/TYPE_EFFECT_CONTRACT.clay"],
            "dependency_cone": ["research_entity/claycode/**"],
        })
        self.assertEqual(row["freshness"], "RED")
        self.assertIn("TYPE_EFFECT_CONTRACT", row["evidence"]["dependency_cone_hits"][0])

    def test_sensitive_without_proven_overlap_is_amber(self):
        row = m.classify({
            "id": "tool",
            "branch": "feature/tool",
            "base_branch": "main",
            "ahead_by": 1,
            "behind_by": 100,
            "head_files": ["tools/new_gate.py"],
            "main_since_base_files": ["research_entity/trigger_runs/go/y/receipt.json"],
            "dependency_cone": [],
        })
        self.assertEqual(row["freshness"], "AMBER")
        self.assertEqual(row["recommendation"], "RERUN_CHEAP_GATES")

    def test_stacked_follows_parent(self):
        row = m.classify({
            "id": "stacked",
            "branch": "feature/child",
            "base_branch": "feature/parent",
            "ahead_by": 1,
            "behind_by": 200,
            "head_files": ["tools/child.py"],
            "main_since_base_files": ["tools/other.py"],
            "dependency_cone": [],
        })
        self.assertEqual(row["disposition"], "STACKED")
        self.assertEqual(row["recommendation"], "FOLLOW_STACKED_PARENT")

    def test_superseded_is_close_candidate_but_not_auto_closed(self):
        row = m.classify({
            "id": "old",
            "branch": "feature/old",
            "base_branch": "main",
            "ahead_by": 1,
            "behind_by": 1000,
            "head_files": ["tools/old.py"],
            "main_since_base_files": ["tools/old.py"],
            "dependency_cone": [],
            "superseded_by": "PR#999",
        })
        self.assertEqual(row["disposition"], "SUPERSEDED")
        self.assertFalse(row["invariants"]["destructive_action_performed"])

    def test_invalid_snapshot_fails_closed(self):
        out = m.compile_snapshot({"schema_version": "9", "candidates": "nope"})
        self.assertFalse(out["ok"])
        self.assertTrue(out["errors"])

    def test_compile_summary(self):
        out = m.compile_snapshot({
            "schema_version": "1.0",
            "main_head": "abc",
            "candidates": [{
                "id": "r",
                "branch": "r",
                "base_branch": "main",
                "ahead_by": 1,
                "behind_by": 99,
                "head_files": ["research_entity/trigger_runs/x/a.json"],
                "main_since_base_files": [],
                "dependency_cone": [],
            }]
        })
        self.assertTrue(out["ok"])
        self.assertEqual(out["summary"]["candidate_count"], 1)
        self.assertEqual(out["summary"]["freshness_counts"]["GREEN"], 1)


if __name__ == "__main__":
    unittest.main()
