from __future__ import annotations

import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BLOGPOST = HERE.parent
CONTRACT_PATH = HERE / "NATIVE_PROFILE_V2_PARITY_CONTRACT.json"
PIPELINE_PATH = BLOGPOST / "BLOGPOST_ENTITY.clay"
REFERENCE_RUNTIME_PATH = ROOT / "tools" / "clay_profile_pipeline_runtime.py"


class ReferenceRuntimeFreshMainFusionGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.pipeline = PIPELINE_PATH.read_text(encoding="utf-8")
        cls.runtime = REFERENCE_RUNTIME_PATH.read_text(encoding="utf-8")

    def test_only_narrow_fresh_main_extraction_is_admitted_from_stale_donors(self) -> None:
        fusion = self.contract["reference_runtime_fresh_main_fusion"]
        self.assertEqual(fusion["status"], "NARROW_FRESH_MAIN_EXTRACTION_REQUIRED")
        donors = {int(item["pull_request"]): item for item in fusion["donors"]}
        self.assertEqual(set(donors), {727, 728})
        for donor in donors.values():
            self.assertTrue(str(donor["whole_branch_merge"]).startswith("FORBIDDEN"))
        self.assertEqual(donors[727]["role"], "PREFERRED_MECHANISM_DONOR_ONLY")
        self.assertIn("parent environment", donors[728]["known_regression_if_copied_verbatim"])

    def test_fusion_contract_preserves_current_security_and_state_fences(self) -> None:
        required = set(self.contract["reference_runtime_fresh_main_fusion"]["must_preserve_or_strengthen"])
        self.assertTrue(
            {
                "recursive_persisted_string_leak_gate",
                "active_secret_rejection",
                "db_profile_integrity_hash",
                "embedded_profile_secret_value_rejection",
                "read_only_evidence_queries",
                "local_exec_parent_environment_isolation",
                "exactly_once_consumption",
                "generation_cas",
                "atomic_commit",
                "canonical_three_argument_run_boundary",
                "one_current_effect_surface_only",
                "fail_closed_native_v2_admission_until_exact_runtime_receipt",
            }.issubset(required)
        )

        # These are already-landed current-main protections and must not disappear while
        # the stale effect surface is being repaired.
        self.assertIn("def _iter_persisted_string_leaves", self.runtime)
        self.assertIn("for text in self._iter_persisted_string_leaves(payload)", self.runtime)
        self.assertIn('"SECRET_LEAK"', self.runtime)
        self.assertIn('"STALE_GENERATION"', self.runtime)
        self.assertIn('"STALE_GENERATION_FINAL"', self.runtime)

    def test_canonical_run_boundary_stays_db_resident_and_three_argument(self) -> None:
        self.assertIn(
            "fn run(entity_db:String, source_db:String, secret_file:String)->Map",
            self.pipeline,
        )
        self.assertNotIn("profile_path", self.pipeline)
        self.assertIn('effect("pipeline_profile_read"', self.pipeline)
        self.assertIn('effect("inference_generate"', self.pipeline)
        self.assertNotIn('effect("profile_load"', self.pipeline)
        self.assertNotIn('effect("provider_chat_json"', self.pipeline)

    def test_reference_remains_fail_closed_until_real_effect_surface_converges(self) -> None:
        gap = self.contract["reference_runtime_effect_surface"]
        missing = [
            name
            for name in self.contract["required_reference_effect_surface"]
            if f'"{name}"' not in self.runtime
        ]
        stale = [
            name
            for name in self.contract["legacy_reference_effects_to_deauthorize"]
            if f'"{name}"' in self.runtime
        ]
        self.assertEqual(gap["missing_current_effects"], missing)
        self.assertEqual(gap["stale_current_effects"], stale)
        if missing or stale:
            self.assertEqual(gap["status"], "FAIL_CLOSED_MISMATCH")
            self.assertEqual(self.contract["admission"]["status"], "FAIL_CLOSED_UNTIL_EXACT_PARITY")
            self.assertIsNone(self.contract["admission"]["runtime_receipt"])


if __name__ == "__main__":
    unittest.main()
