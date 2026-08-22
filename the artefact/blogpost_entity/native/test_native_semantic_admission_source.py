#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PART04 = HERE / "mini_entity_part04.inc"
ZERO_PROFILE = ROOT / "blogpost_entity" / "presets" / "zero_blog.json"


class NativeSemanticAdmissionSourceTests(unittest.TestCase):
    def test_shipped_profile_really_requires_canonical_v2_semantics(self) -> None:
        profile = json.loads(ZERO_PROFILE.read_text(encoding="utf-8"))
        self.assertEqual(profile["schema"], "clay-pipeline-profile/v2")
        self.assertTrue(profile["gate"]["require_hash_echo"])
        self.assertTrue(profile["gate"]["require_evidence_per_section"])
        self.assertGreater(len(profile["gate"]["leak_patterns"]), 0)
        self.assertGreater(len(profile["state_metrics"]), 0)
        self.assertGreater(len(profile["canonical_probes"]), 0)
        self.assertGreater(len(profile["sources"]), 0)

    def test_native_run_checks_semantic_admission_before_collection_or_inference(self) -> None:
        text = PART04.read_text(encoding="utf-8")
        run_start = text.index("static void cmd_run")
        run_text = text[run_start:]
        gate_pos = run_text.index("native_semantic_admission_blocker(profile)")
        collect_pos = run_text.index("collect_packet(source_path)")
        infer_pos = run_text.index("model_output(profile")
        commit_pos = run_text.index("commit_run(db")
        self.assertLess(gate_pos, collect_pos)
        self.assertLess(gate_pos, infer_pos)
        self.assertLess(gate_pos, commit_pos)
        self.assertIn("CANONICAL_PROFILE_V2_REQUIRES_PIPELINE_PARITY", run_text[:collect_pos])

    def test_status_exposes_blocked_semantic_admission(self) -> None:
        text = PART04.read_text(encoding="utf-8")
        self.assertIn('"native_semantic_admission"', text)
        self.assertIn("CANONICAL_PROFILE_V2_REQUIRES_PIPELINE_PARITY", text)


if __name__ == "__main__":
    unittest.main()
