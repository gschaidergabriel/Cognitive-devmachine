import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HCU = ROOT / "the artefact" / "MicroEntity" / "hcu"


class EntityOSHCUIntegrationAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((HCU / "ENTITYOS_HCU_INTEGRATION_CONTRACT.json").read_text(encoding="utf-8"))
        self.index = json.loads((HCU / "HCU_DATA_INDEX.json").read_text(encoding="utf-8"))
        self.readme = (HCU / "README.md").read_text(encoding="utf-8")
        self.arch = (HCU / "HCU_ARCHITECTURE.md").read_text(encoding="utf-8")

    def test_current_product_and_compute_authority(self):
        self.assertEqual(self.contract["status"], "ACTIVE")
        self.assertEqual(self.contract["product"], "EntityOS")
        self.assertEqual(self.contract["compute_architecture"], "HCU")
        self.assertEqual(self.index["product"], "EntityOS")
        self.assertEqual(self.index["compute_architecture"], "HCU")
        self.assertIn("EntityOS", self.readme)
        self.assertIn("EntityOS", self.arch)
        self.assertNotIn("OWNER-DIRECTED MINI ENTITY WORKSTREAM", self.readme)
        self.assertNotIn("Product: Mini Entity / EntityOS", self.arch)

    def test_compatibility_path_cannot_reactivate_mini_entity(self):
        policy = self.contract["compatibility_name_policy"]
        self.assertEqual(policy["MicroEntity"], "HISTORICAL_IMPLEMENTATION_OR_PROVENANCE_ONLY")
        self.assertEqual(policy["Mini Entity"], "HISTORICAL_IMPLEMENTATION_OR_PROVENANCE_ONLY")
        self.assertIn("not a current product identity", self.readme)
        self.assertIn("compatibility", self.arch.lower())

    def test_state_effect_and_execution_authority_fail_closed(self):
        authority = self.contract["authority"]
        execution = self.contract["execution_policy"]
        self.assertEqual(authority["effects"], "EffectGate+EffectJournal")
        self.assertEqual(authority["second_product_identity"], "FORBIDDEN")
        self.assertEqual(authority["second_state_truth_effect_or_recovery_authority"], "FORBIDDEN")
        self.assertEqual(execution["current_credit_surface"], "AUTHORIZED_ISOLATED_SANDBOX_ONLY")
        self.assertEqual(execution["vps_testing"], "FORBIDDEN")
        self.assertEqual(execution["together_api"], "FORBIDDEN")
        self.assertEqual(execution["paid_fallback"], "FORBIDDEN")
        self.assertEqual(self.contract["runtime_credit"], 0)

    def test_entry_route_engine_identity_is_not_self_asserted(self):
        inv = self.contract["entry_route_invariants"]
        self.assertTrue(inv["typed_entry_required_for_new_data"])
        self.assertTrue(inv["replay_stable_event_identity_distinct_from_concrete_admission_identity"])
        self.assertTrue(inv["entry_capability_claim_may_narrow_but_never_self_grant_or_broaden"])
        self.assertTrue(inv["engine_identity_and_artifact_authority_must_come_from_independent_deterministic_control_plane_admission"])
        self.assertTrue(inv["untrusted_causal_event_may_not_mint_engine_provider_class_or_artifact_authority"])
        self.assertEqual(inv["duplicate_router_entry_canonicalizer_or_effect_authority"], "FORBIDDEN")
        self.assertEqual(self.contract["retained_donor"]["pull_request"], 1263)

    def test_canonicalization_must_converge_before_hash_promotion(self):
        canonical = self.contract["canonicalization"]
        self.assertEqual(canonical["status"], "CONVERGENCE_REQUIRED")
        self.assertIn("EXACTLY_ONE_VERSIONED_CURRENT_ENTRY_HCU_CANONICAL_IDENTITY_PATH", canonical["law"])
        self.assertEqual(self.index["duplicate_route_entry_canonicalization_authority"], "FORBIDDEN")
        self.assertIn("ENTITYOS_HCU_INTEGRATION_CONTRACT.json", self.index["generated_release_artifacts"])


if __name__ == "__main__":
    unittest.main()
