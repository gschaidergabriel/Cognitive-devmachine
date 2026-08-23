from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
BASE_CONTROL = ROOT / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
EXECUTION_ADDENDUM = ROOT / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
PROGRAM_ADDENDUM = ROOT / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"

EXPECTED_PROGRAM = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
EXPECTED_PROGRAM_ID = "mini-entity-pipeline-all-in-one"
EXPECTED_STAGE = "MINI_ENTITY_PIPELINE_CLAY_PLUS_BUNDLED_08B_UNIFIED_JSPACE_GWT"
EXPECTED_OWNER = "research_entity/global/ENTITYOS_FIXED_CLAUDE_ADAPTIVE_INFERENCE_INTEGRATION.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: Path) -> str:
    relative = path.relative_to(ROOT)
    proc = subprocess.run(
        ["git", "hash-object", "--", str(relative)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


class Control43ProgramAuthoritySyncTest(unittest.TestCase):
    def setUp(self) -> None:
        self.bootstrap = load(BOOTSTRAP)
        self.state = load(PROGRAM_STATE)
        self.base = load(BASE_CONTROL)
        self.exec_addendum = load(EXECUTION_ADDENDUM)
        self.program_addendum = load(PROGRAM_ADDENDUM)

    def test_effective_program_identity_follows_bootstrap_and_program_state(self) -> None:
        override = self.program_addendum["program_identity_override"]
        self.assertEqual(self.bootstrap["active_program"], EXPECTED_PROGRAM)
        self.assertEqual(self.bootstrap["active_stage"], EXPECTED_STAGE)
        self.assertEqual(self.state["program_id"], EXPECTED_PROGRAM_ID)
        self.assertEqual(self.state["stage"], EXPECTED_STAGE)
        self.assertEqual(override["active_program"], self.bootstrap["active_program"])
        self.assertEqual(override["target_stage"], self.bootstrap["active_stage"])

    def test_owner_directive_is_cross_bound_across_authorities(self) -> None:
        authority = self.program_addendum["owner_program_authority"]
        self.assertEqual(self.bootstrap["sole_owner_directive"], EXPECTED_OWNER)
        self.assertEqual(self.state["owner_directive"], EXPECTED_OWNER)
        self.assertEqual(authority["owner_directive_path"], EXPECTED_OWNER)
        self.assertEqual(authority["bootstrap_minimal_path"], str(BOOTSTRAP.relative_to(ROOT)))
        self.assertEqual(authority["program_state_path"], str(PROGRAM_STATE.relative_to(ROOT)))
        self.assertEqual(authority["program_state_schema"], self.state["schema_version"])
        self.assertEqual(authority["bootstrap_minimal_blob_sha"], git_blob_sha(BOOTSTRAP))

    def test_composed_control_is_bound_to_exact_4_1_and_4_2_bytes(self) -> None:
        self.assertEqual(
            self.program_addendum["base_control_path"],
            str(BASE_CONTROL.relative_to(ROOT)),
        )
        self.assertEqual(
            self.program_addendum["execution_boundary_addendum_path"],
            str(EXECUTION_ADDENDUM.relative_to(ROOT)),
        )
        self.assertEqual(self.program_addendum["base_control_blob_sha"], git_blob_sha(BASE_CONTROL))
        self.assertEqual(
            self.program_addendum["execution_boundary_addendum_blob_sha"],
            git_blob_sha(EXECUTION_ADDENDUM),
        )
        self.assertEqual(
            self.program_addendum["composition_order"],
            ["4.1", "4.2-execution-boundary-addendum", "4.3-program-authority-addendum"],
        )

    def test_stale_legacy_metadata_is_not_effective_program_selection(self) -> None:
        stale = self.program_addendum["superseded_active_metadata"]
        override = self.program_addendum["program_identity_override"]
        self.assertEqual(stale["classification"], "LEGACY_CONTROL_METADATA_ONLY_NOT_CURRENT_PROGRAM_AUTHORITY")
        self.assertNotEqual(override["active_program"], stale["active_program"])
        self.assertNotEqual(override["target_stage"], stale["target_stage"])
        self.assertNotEqual(override["product_endpoint_definition"], stale["product_endpoint_definition"])
        joined_selection = "\n".join(self.program_addendum["work_selection_override"])
        self.assertIn("MINI_ENTITY", joined_selection)
        self.assertNotIn("PR611", joined_selection)
        self.assertNotIn("PR623", joined_selection)

    def test_free_only_and_authority_fences_survive_composition(self) -> None:
        hard = self.program_addendum["preserved_hard_rules"]
        self.assertEqual(self.program_addendum["mode"], "FREE_ONLY")
        self.assertTrue(hard["free_only"])
        self.assertFalse(hard["paid_fallback"])
        self.assertTrue(hard["together_forbidden_under_current_control"])
        self.assertTrue(hard["model_output_is_candidate_not_truth"])
        self.assertTrue(hard["runtime_credit_requires_exact_admitted_execution"])
        self.assertTrue(hard["canonical_semantics_require_executable_counterevidence_and_review"])
        self.assertTrue(hard["goodman_ancestry_collapse"])
        self.assertEqual(hard["frank_harness_modification"], "FORBIDDEN")
        self.assertEqual(self.base["mode"], "FREE_ONLY")
        self.assertEqual(self.exec_addendum["mode"], "FREE_ONLY")
        self.assertFalse(self.base["cycle_policy"]["paid_fallback"])
        self.assertEqual(self.base["cycle_policy"]["vps_testing"], "FORBIDDEN")
        self.assertEqual(self.base["cycle_policy"]["self_hosted_vps_test_runners"], "FORBIDDEN")
        self.assertEqual(self.base["cycle_policy"]["production_host_testing"], "FORBIDDEN")

    def test_source_only_control_sync_cannot_mint_runtime_credit(self) -> None:
        credit = self.program_addendum["credit"]
        self.assertEqual(credit["source_control_authority_sync"], "PASS_SOURCE_ONLY")
        self.assertEqual(credit["bundled_08b_runtime"], 0)
        self.assertEqual(credit["jspace_runtime"], 0)
        self.assertEqual(credit["whole_gwt"], 0)
        self.assertEqual(credit["claude_adapter_runtime"], 0)
        self.assertEqual(credit["whole_product"], 0)


if __name__ == "__main__":
    unittest.main()
