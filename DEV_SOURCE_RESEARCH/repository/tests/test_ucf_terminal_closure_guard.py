from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from check_ucf_terminal_closure import evaluate  # noqa: E402


class UcfTerminalClosureGuardTests(unittest.TestCase):
    def test_current_one_phase_source_is_not_false_failed(self):
        source = 'let admitted = phase("pipeline_cognitive_fabric_admit",a,b,c,d,e)\n'
        self.assertTrue(evaluate(source)["pass"])

    def test_finalize_before_commit_is_rejected(self):
        source = (
            'let finalized = phase("pipeline_cognitive_fabric_finalize",a,b,c,d,e)\n'
            'let committed = phase("pipeline_commit",a,b,c,d,e)\n'
        )
        report = evaluate(source)
        self.assertFalse(report["pass"])
        self.assertTrue(report["legacy_finalize_before_commit"])

    def test_post_commit_fatal_finalize_is_rejected(self):
        source = (
            'let committed = phase("pipeline_commit",a,b,c,d,e)\n'
            'require committed.ok\n'
            'let finalized = phase("pipeline_cognitive_fabric_finalize",a,b,c,d,e)\n'
            'require finalized.ok\n'
        )
        report = evaluate(source)
        self.assertFalse(report["pass"])
        self.assertTrue(report["finalize_after_commit"])
        self.assertTrue(report["fatal_post_commit_finalize"])

    def test_post_commit_nonfatal_finalize_is_allowed_by_this_narrow_guard(self):
        source = (
            'let committed = phase("pipeline_commit",a,b,c,d,e)\n'
            'require committed.ok\n'
            'let finalized = phase("pipeline_cognitive_fabric_finalize",a,b,c,d,e)\n'
            'map_set(result,"finalization",finalized)\n'
        )
        report = evaluate(source)
        self.assertTrue(report["pass"])
        self.assertTrue(report["finalize_after_commit"])
        self.assertFalse(report["fatal_post_commit_finalize"])


if __name__ == "__main__":
    unittest.main()
