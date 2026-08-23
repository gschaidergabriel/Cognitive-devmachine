from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from check_ucf_terminal_closure import evaluate  # noqa: E402
from claycode_structured_backend import parse  # noqa: E402


class BlogpostEntityTerminalClosureV2Tests(unittest.TestCase):
    @classmethod
    def source(cls) -> str:
        return (ROOT / "the artefact" / "blogpost_entity" / "BLOGPOST_ENTITY.clay").read_text(
            encoding="utf-8"
        )

    def test_canonical_source_passes_terminal_closure_guard(self):
        report = evaluate(self.source())
        self.assertTrue(report["has_two_phase_terminal"])
        self.assertTrue(report["finalize_after_commit"])
        self.assertFalse(report["fatal_post_commit_finalize"])
        self.assertTrue(report["pass"])

    def test_committed_finalization_failure_is_explicit_not_fatal(self):
        source = self.source()
        self.assertNotIn("require finalized.ok", source)
        self.assertIn('"COMMITTED_FINALIZED"', source)
        self.assertIn('"COMMITTED_FINALIZATION_FAILED"', source)
        self.assertIn('map_set(result,"ucf_finalization",finalized)', source)

    def test_modified_clay_source_still_parses(self):
        program = parse(self.source())
        names = {fn.name for fn in program.functions}
        self.assertIn("run", names)
        self.assertIn("phase", names)


if __name__ == "__main__":
    unittest.main()