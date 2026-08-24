import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "the artefact" / "manifest.json"


class ArtefactManifestCurrentAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_current_supervisor_is_872_everywhere_current_facing(self) -> None:
        self.assertEqual(
            self.manifest["authority_correction"],
            "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_72.json",
        )
        self.assertEqual(self.manifest["execution_policy"]["active_supervisor_epoch"], "8.72")
        self.assertEqual(self.manifest["coordination_authority"]["supervisor"], "8.72")

    def test_free_only_and_together_fail_closed(self) -> None:
        policy = self.manifest["execution_policy"]
        self.assertTrue(policy["active_supervisor_free_only"])
        self.assertTrue(policy["together_general_inference_and_fallback_forbidden"])
        self.assertFalse(policy["other_paid_fallback"])

    def test_runtime_credit_boundary_remains_zero(self) -> None:
        credit = self.manifest["runtime_credit"]
        self.assertEqual(credit["entityos_hcu_whole_runtime_credit"], 0)
        self.assertEqual(credit["hcu_full_runtime_credit"], 0)
        self.assertEqual(credit["jspace_model_runtime_credit"], 0)
        self.assertEqual(credit["training_credit"], 0)
        self.assertFalse(credit["whole_product_pass"])

    def test_atomic_lease_remains_required(self) -> None:
        coordination = self.manifest["coordination_authority"]
        self.assertTrue(coordination["atomic_lease_required_before_unusual_intervention"])
        self.assertEqual(
            coordination["no_reproducible_trigger_identity"],
            "COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT",
        )


if __name__ == "__main__":
    unittest.main()
