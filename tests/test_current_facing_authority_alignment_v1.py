from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
MANIFEST = ROOT / "the artefact/manifest.json"
ADMISSION = ROOT / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
INBOX = ROOT / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class CurrentFacingAuthorityAlignmentV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.bootstrap = _load(BOOTSTRAP)
        self.program = _load(PROGRAM)
        self.manifest = _load(MANIFEST)
        self.admission = _load(ADMISSION)
        self.inbox = _load(INBOX)

    def _supervisor_epoch(self) -> tuple[str, str]:
        epoch = str(self.inbox["schema_version"])
        correction = str(self.inbox["steering"])
        supervisor = _load(ROOT / correction)
        self.assertEqual(str(supervisor["schema_version"]), epoch)
        return correction, epoch

    def test_current_facing_mirrors_follow_inbox_supervisor_dynamically(self) -> None:
        correction, epoch = self._supervisor_epoch()

        self.assertEqual(str(self.bootstrap["schema_version"]), epoch)
        self.assertEqual(self.bootstrap["authority_correction"], correction)

        self.assertEqual(str(self.program["schema_version"]), epoch)
        self.assertEqual(self.program["authority_correction"], correction)

        self.assertEqual(self.manifest["authority_correction"], correction)
        self.assertEqual(
            str(self.manifest["execution_policy"]["active_supervisor_epoch"]),
            epoch,
        )
        self.assertEqual(
            str(self.manifest["coordination_authority"]["supervisor"]),
            epoch,
        )

    def test_worker_directive_is_successor_dynamic(self) -> None:
        expected = self.bootstrap["all_worker_protocol"]
        self.assertEqual(self.program["all_worker_protocol"], expected)
        self.assertTrue((ROOT / expected).is_file())

    def test_active_owner_execution_surface_does_not_regress_to_obsolete_vps_ban(self) -> None:
        program_policy = self.program["execution_policy"]
        manifest_policy = self.manifest["execution_policy"]

        self.assertTrue(program_policy["authorized_zero_cost_local_normal_user_execution"])
        self.assertTrue(program_policy["authorized_clay_direct_dev_vps_sandbox_execution"])
        self.assertTrue(manifest_policy["authorized_zero_cost_local_normal_user_execution"])
        self.assertTrue(manifest_policy["authorized_clay_direct_dev_vps_sandbox_execution"])
        self.assertNotIn("vps_testing_forbidden", manifest_policy)
        self.assertNotIn("self_hosted_vps_test_runners_forbidden", manifest_policy)

    def test_provider_authority_epoch_and_allowlist_follow_inbox(self) -> None:
        _, epoch = self._supervisor_epoch()
        self.assertEqual(str(self.admission["authority_epoch"]), epoch)
        self.assertEqual(self.admission["mode"], "FREE_ONLY")

        expected = set(self.bootstrap["free_provider_allowlist_current"])
        self.assertTrue(expected)
        self.assertTrue(expected.issubset(set(self.admission["providers"])))

    def test_provider_economic_provenance_and_zero_credit_remain_current_facing(self) -> None:
        program_policy = self.program["execution_policy"]
        manifest_policy = self.manifest["execution_policy"]
        admission_gate = self.admission["route_level_gate"]

        self.assertEqual(program_policy["current_provider_runtime_credit"], 0)
        self.assertEqual(self.admission["runtime_provider_credit"], 0)
        self.assertEqual(
            self.program["runtime_credit"]["external_provider_worker_runtime_credit"],
            0,
        )
        self.assertEqual(
            self.manifest["runtime_credit"]["external_provider_worker_runtime_credit"],
            0,
        )

        for rule in (
            program_policy["external_provider_admission_rule"],
            manifest_policy["external_provider_admission_rule"],
        ):
            self.assertIn("CONCRETE_CREDENTIAL_MODEL_ROUTE", rule)
            self.assertIn("ZERO_COST", rule)

        self.assertIn("FAIL_CLOSED", admission_gate["unknown_or_unbound_route"])
        self.assertEqual(admission_gate["paid_fallback_attempt_count"], 0)
        self.assertTrue(program_policy["together_general_inference_and_fallback_forbidden"])
        self.assertTrue(manifest_policy["together_general_inference_and_fallback_forbidden"])
        self.assertFalse(program_policy["other_paid_fallback"])
        self.assertFalse(manifest_policy["other_paid_fallback"])


if __name__ == "__main__":
    unittest.main()
