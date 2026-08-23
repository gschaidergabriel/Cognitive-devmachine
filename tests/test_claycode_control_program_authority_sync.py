from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM_STATE = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
SUPERVISOR_INBOX = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
BASE_CONTROL = ROOT / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
EXECUTION_ADDENDUM = ROOT / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"

EXPECTED_PROGRAM = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
EXPECTED_PROGRAM_ID = "mini-entity-pipeline-all-in-one"
EXPECTED_STAGE = "MINI_ENTITY_PIPELINE_CLAY_PLUS_BUNDLED_08B_UNIFIED_JSPACE_GWT"
EXPECTED_OWNER_DIRECTIVE = "research_entity/global/ENTITYOS_FIXED_CLAUDE_ADAPTIVE_INFERENCE_INTEGRATION.md"
STALE_PROGRAM = "CLAYVERSE_CLAY_MACHINE_ONLY"
STALE_STAGE = "CLAY_MACHINE"
STALE_ENDPOINT = "SINGLE_FILE_CLAY_COMPUTER"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: Path) -> str:
    rel = path.relative_to(ROOT)
    proc = subprocess.run(
        ["git", "hash-object", "--", str(rel)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


class ProgramAuthoritySyncTest(unittest.TestCase):
    def setUp(self) -> None:
        self.bootstrap = load(BOOTSTRAP)
        self.state = load(PROGRAM_STATE)
        self.inbox = load(SUPERVISOR_INBOX)
        self.control = load(BASE_CONTROL)
        self.addendum = load(EXECUTION_ADDENDUM)

    def test_active_program_stage_and_owner_authority_are_cross_bound(self) -> None:
        self.assertEqual(self.bootstrap["active_program"], EXPECTED_PROGRAM)
        self.assertEqual(self.bootstrap["active_stage"], EXPECTED_STAGE)
        self.assertEqual(self.bootstrap["sole_owner_directive"], EXPECTED_OWNER_DIRECTIVE)
        self.assertEqual(self.state["program_id"], EXPECTED_PROGRAM_ID)
        self.assertEqual(self.state["stage"], EXPECTED_STAGE)
        self.assertEqual(self.state["owner_directive"], EXPECTED_OWNER_DIRECTIVE)
        self.assertEqual(self.inbox["active_program"], EXPECTED_PROGRAM)
        self.assertEqual(self.control["active_program"], EXPECTED_PROGRAM)
        self.assertEqual(self.control["target_stage"], EXPECTED_STAGE)
        self.assertEqual(self.control["owner_directive_path"], EXPECTED_OWNER_DIRECTIVE)
        self.assertFalse(self.inbox["control_sync_required_before_research_spend"])

    def test_stale_endpoint_metadata_cannot_be_active_work_selection(self) -> None:
        self.assertNotEqual(self.inbox["active_program"], STALE_PROGRAM)
        self.assertNotEqual(self.control["active_program"], STALE_PROGRAM)
        self.assertNotEqual(self.control["target_stage"], STALE_STAGE)
        self.assertNotEqual(self.control["product_endpoint_definition"], STALE_ENDPOINT)
        for priority in self.control["priority_order"]:
            self.assertNotIn("PR611", priority)
            self.assertNotIn("PR623", priority)
        for priority in self.addendum["priority_order_override"]:
            self.assertNotIn("PR611", priority)
            self.assertNotIn("PR623", priority)

    def test_execution_addendum_is_bound_to_exact_migrated_base_control(self) -> None:
        self.assertEqual(self.addendum["base_control_path"], str(BASE_CONTROL.relative_to(ROOT)))
        self.assertEqual(self.addendum["base_control_blob_sha"], git_blob_sha(BASE_CONTROL))

    def test_hard_execution_and_authority_fences_survive_migration(self) -> None:
        self.assertEqual(self.control["mode"], "FREE_ONLY")
        self.assertFalse(self.control["cycle_policy"]["paid_fallback"])
        self.assertEqual(self.control["cycle_policy"]["vps_testing"], "FORBIDDEN")
        self.assertEqual(self.control["cycle_policy"]["self_hosted_vps_test_runners"], "FORBIDDEN")
        self.assertEqual(self.control["cycle_policy"]["production_host_testing"], "FORBIDDEN")
        self.assertTrue(self.inbox["verified_updates"]["free_only"])
        self.assertFalse(self.inbox["verified_updates"]["together_training_network_execution_allowed_under_free_only"])
        self.assertTrue(self.addendum["preserved_hard_rules"]["free_only"])
        self.assertFalse(self.addendum["preserved_hard_rules"]["paid_fallback"])
        self.assertTrue(self.addendum["preserved_hard_rules"]["together_forbidden"])
        self.assertTrue(self.addendum["preserved_hard_rules"]["goodman_ancestry_collapse"])
        self.assertEqual(self.addendum["preserved_hard_rules"]["frank_harness_modification"], "FORBIDDEN")
        self.assertIn("model_output_is_candidate_not_truth", self.control["authority_rules"])
        self.assertIn("exact_head_credit_requires_explicit_pr_head_fetch_binding_and_tested_sha_equality", self.control["authority_rules"])
        self.assertIn("all_current_build_test_experiment_and_runtime_validation_execution_is_isolated_sandbox_only", self.control["authority_rules"])


if __name__ == "__main__":
    unittest.main()
