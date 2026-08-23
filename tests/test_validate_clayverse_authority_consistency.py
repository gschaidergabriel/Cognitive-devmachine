import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "validate_clayverse_authority_consistency.py"
spec = importlib.util.spec_from_file_location("authority_validator", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class EntityOSHCUAuthorityConsistencyTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)

        def write_json(rel, value):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
            return path

        def write_text(rel, value):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding="utf-8")
            return path

        write_json(
            "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
            {"entity_id": "entity"},
        )
        write_json(
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
            {
                "entity_id": "entity",
                "entity_display_name": "Clay",
                "identity": {"persistent_research_entity": "Clay", "temporary_worker": "ORGAN_NOT_ENTITY"},
                "active_program": mod.EXPECTED_PROGRAM,
                "active_stage": mod.EXPECTED_STAGE,
                "product_endpoint": mod.EXPECTED_PRODUCT,
                "integrated_cognition_compute_architecture": mod.EXPECTED_COMPUTE,
                "authority_correction": mod.STEERING852,
                "compatibility_names": {
                    "xeno": "TRANSITIONAL_IMPLEMENTATION_COMPATIBILITY_CODENAME_ONLY",
                    "xcu": "TRANSITIONAL_RESEARCH_ALIAS_FOR_HCU_ONLY",
                    "clayverse_frank": "HISTORICAL_DONOR_PROVENANCE_ONLY",
                },
                "go_required_tracks": [
                    "ENTITYOS_EXECUTABLE_CONVERGENCE",
                    "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT_OR_HCU_NO_CHANGE_WITH_REASON",
                ],
                "execution_surface": "AUTHORIZED_ISOLATED_SANDBOX_ONLY",
                "together_api": "FORBIDDEN",
                "paid_fallback": "FORBIDDEN",
                "final_paid_model_training": "OWNER_AUTHORIZATION_REQUIRED",
                "effect_authority": "EffectGate+EffectJournal",
            },
        )
        write_json(
            "research_entity/rooms/PROGRAM_STATE.json",
            {
                "program_id": "entityos-hcu",
                "status": "ACTIVE",
                "stage": mod.EXPECTED_STAGE,
                "current_stage": mod.EXPECTED_STAGE,
                "product": mod.EXPECTED_PRODUCT,
                "integrated_cognition_compute_architecture": mod.EXPECTED_COMPUTE,
                "authority_correction": mod.STEERING852,
                "execution_policy": {
                    "free_only": True,
                    "isolated_sandbox_only": True,
                    "vps_testing_forbidden": True,
                    "self_hosted_vps_test_runners_forbidden": True,
                    "production_host_testing_forbidden": True,
                    "together_forbidden": True,
                    "paid_fallback": False,
                    "final_paid_or_model_training_requires_owner_authorization": True,
                },
                "authority": {
                    "external_effects": "EffectGate+EffectJournal",
                    "second_persistent_identity": "FORBIDDEN",
                    "second_truth_effect_or_recovery_authority": "FORBIDDEN",
                },
            },
        )
        write_json(
            mod.STEERING852,
            {
                "schema_version": "8.52",
                "status": "CURRENT_OWNER_AUTHORITY_CORRECTION",
                "program": mod.EXPECTED_PROGRAM,
                "product": mod.EXPECTED_PRODUCT,
                "integrated_cognition_compute_architecture": mod.EXPECTED_COMPUTE,
                "adjudication": {
                    "entityos": "SOLE_CURRENT_PRODUCT_SYSTEM_IDENTITY",
                    "hcu": "SOLE_CURRENT_INTEGRATED_COGNITION_COMPUTE_ARCHITECTURE",
                    "clayverse": "HISTORICAL_DONOR_PROVENANCE_ONLY",
                },
                "routing_law": [
                    "DO_NOT_CREATE_A_SECOND_IDENTITY_STATE_AUTHORITY_EFFECT_PATH_RECOVERY_LEDGER_OR_PRODUCT_TRACK",
                    "FREE_ONLY_REMAINS_FAIL_CLOSED_WITH_NO_PAID_FALLBACK",
                ],
            },
        )
        write_json(
            "the artefact/manifest.json",
            {
                "schema_version": "ENTITYOS_HCU_ARTIFACT_MANIFEST/v1",
                "artifact": mod.EXPECTED_PRODUCT,
                "product_endpoint": mod.EXPECTED_PRODUCT,
                "integrated_cognition_compute_architecture": mod.EXPECTED_COMPUTE,
                "stage": mod.EXPECTED_STAGE,
                "current_authority": mod.STEERING852,
                "current_architecture": "ENTITYOS_HCU_ARCHITECTURE.md",
                "effect_authority": "EffectGate+EffectJournal",
                "execution_policy": {
                    "authorized_isolated_sandbox_only": True,
                    "vps_testing_forbidden": True,
                    "self_hosted_vps_test_runners_forbidden": True,
                    "production_host_testing_forbidden": True,
                    "free_only": True,
                    "together_forbidden": True,
                    "paid_fallback": False,
                },
                "legacy_clayverse_material": {
                    "status": "SUPERSEDED_AS_CURRENT_PRODUCT_AUTHORITY_HISTORICAL_DONOR_PROVENANCE_ONLY"
                },
            },
        )
        write_text(
            "the artefact/ENTITYOS_HCU_ARCHITECTURE.md",
            "EntityOS is the sole current product/system identity. HCU is the sole current compute architecture.\n",
        )
        write_text("the artefact/README.md", "Current product: EntityOS. Current compute architecture: HCU.\n")
        write_text(
            "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md",
            f"Program: EntityOS + HCU\nStage: {mod.EXPECTED_STAGE}\n",
        )

        c41 = {
            "mode": "FREE_ONLY",
            "cycle_policy": {
                "paid_fallback": False,
                "automatic_subscription_upgrade": False,
                "vps_testing": "FORBIDDEN",
                "self_hosted_vps_test_runners": "FORBIDDEN",
                "production_host_testing": "FORBIDDEN",
            },
            "authority_rules": [
                "model_output_is_candidate_not_truth",
                "autonomous_cycle_may_not_modify_FRANK_harness",
            ],
        }
        c41p = write_json(mod.CONTROL41, c41)
        c42 = {
            "base_control_blob_sha": mod.git_blob_sha(c41p),
            "execution_routing": {
                "direct_vps_host_candidate_execution": "FORBIDDEN",
                "persistent_self_hosted_candidate_execution": "FORBIDDEN",
                "production_host_testing": "FORBIDDEN",
            },
            "preserved_hard_rules": {
                "free_only": True,
                "paid_fallback": False,
                "together_forbidden": True,
                "frank_harness_modification": "FORBIDDEN",
            },
        }
        c42p = write_json(mod.CONTROL42, c42)
        c43 = {
            "base_control_blob_sha": mod.git_blob_sha(c41p),
            "execution_boundary_addendum_blob_sha": mod.git_blob_sha(c42p),
            "program_identity_override": {"active_program": "MINI_ENTITY_PIPELINE_ALL_IN_ONE"},
            "preserved_hard_rules": {
                "free_only": True,
                "paid_fallback": False,
                "together_forbidden_under_current_control": True,
                "model_output_is_candidate_not_truth": True,
                "runtime_credit_requires_exact_admitted_execution": True,
                "frank_harness_modification": "FORBIDDEN",
            },
        }
        c43p = write_json(mod.CONTROL43, c43)
        c44 = {
            "prior_program_authority_addendum_blob_sha": mod.git_blob_sha(c43p),
            "program_identity_override": {
                "active_program": "CLAYVERSE_SINGLE_CONTAINER",
                "product_endpoint": "ClayVerse",
            },
            "preserved_hard_rules": {
                "free_only": True,
                "paid_fallback": False,
                "together_forbidden": True,
                "authorized_isolated_sandbox_only": True,
                "vps_testing": False,
                "self_hosted_vps_test_runners": False,
                "production_host_testing": False,
                "runtime_credit_requires_exact_admitted_isolated_execution": True,
                "model_output_is_candidate_not_truth": True,
                "frank_harness_modification": "FORBIDDEN",
            },
        }
        write_json(mod.CONTROL44, c44)
        return td, root

    def test_current_entityos_hcu_authority_passes_while_historical_controls_remain(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        result = mod.validate(root)
        self.assertTrue(result["pass"], result["errors"])
        self.assertFalse(result["historical_control_product_metadata_used_for_current_authority"])
        self.assertTrue(result["inherited_control_ancestry_checked"])

    def test_bootstrap_clayverse_regression_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
        data = json.loads(path.read_text())
        data["product_endpoint"] = "ClayVerse"
        path.write_text(json.dumps(data))
        self.assertIn("BOOTSTRAP_PRODUCT_MISMATCH", mod.validate(root)["errors"])

    def test_manifest_clayverse_regression_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "the artefact/manifest.json"
        data = json.loads(path.read_text())
        data["artifact"] = "ClayVerse"
        data["product_endpoint"] = "ClayVerse"
        path.write_text(json.dumps(data))
        self.assertIn("MANIFEST_PRODUCT_MISMATCH", mod.validate(root)["errors"])

    def test_program_together_weakening_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        data = json.loads(path.read_text())
        data["execution_policy"]["together_forbidden"] = False
        path.write_text(json.dumps(data))
        self.assertIn("PROGRAM_TOGETHER_FENCE_WEAKENED", mod.validate(root)["errors"])

    def test_control41_mutation_breaks_inherited_ancestry(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.CONTROL41
        data = json.loads(path.read_text())
        data["cycle_policy"]["paid_fallback"] = True
        path.write_text(json.dumps(data, sort_keys=True))
        errors = mod.validate(root)["errors"]
        self.assertIn("CONTROL41_PAID_FALLBACK_WEAKENED", errors)
        self.assertIn("CONTROL42_BASE_BLOB_MISMATCH", errors)
        self.assertIn("CONTROL43_BASE_BLOB_MISMATCH", errors)

    def test_control44_safety_weakening_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.CONTROL44
        data = json.loads(path.read_text())
        data["preserved_hard_rules"]["free_only"] = False
        path.write_text(json.dumps(data, sort_keys=True))
        self.assertIn("CONTROL44_FREE_ONLY_FENCE_WEAKENED", mod.validate(root)["errors"])

    def test_steering_must_keep_clayverse_historical(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.STEERING852
        data = json.loads(path.read_text())
        data["adjudication"]["clayverse"] = "CURRENT_PRODUCT"
        path.write_text(json.dumps(data))
        self.assertIn("STEERING852_CLAYVERSE_NOT_HISTORICAL", mod.validate(root)["errors"])

    def test_current_architecture_is_required(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        (root / "the artefact/ENTITYOS_HCU_ARCHITECTURE.md").unlink()
        self.assertTrue(any(x.startswith("MISSING:architecture:") for x in mod.validate(root)["errors"]))


if __name__ == "__main__":
    unittest.main()
