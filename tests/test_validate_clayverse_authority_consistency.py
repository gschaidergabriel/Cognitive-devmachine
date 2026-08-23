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


class AuthorityConsistencyTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        files = {
            "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json": {"entity_id": "entity"},
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json": {
                "entity_id": "entity",
                "identity": {"persistent_research_entity": "Clay", "temporary_worker": "ORGAN_NOT_ENTITY"},
                "active_program": mod.CURRENT_PROGRAM,
                "active_stage": mod.CURRENT_STAGE,
                "product_endpoint": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "authority_correction": mod.CURRENT_AUTHORITY,
                "execution_surface": "AUTHORIZED_ISOLATED_FREE_SANDBOX_ONLY_IN_CURRENT_AUTONOMOUS_SUPERVISOR_MODE",
                "free_only": True,
                "paid_fallback": "FORBIDDEN",
                "together_api": "FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE",
                "together_training_authority_provenance": mod.TRAINING_PROVENANCE,
                "together_one_shot_training_consumed": False,
                "current_supervisor_together_training": "FORBIDDEN_BEFORE_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION",
                "effect_authority": "EffectGate+EffectJournal",
                "mandatory_invariants": [
                    "EntityOS is the sole current product/system identity",
                    "HCU is the sole current integrated cognition/compute architecture",
                    "FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT",
                ],
            },
            "research_entity/rooms/PROGRAM_STATE.json": {
                "program_id": "entityos-hcu", "status": "ACTIVE",
                "stage": mod.CURRENT_STAGE, "current_stage": mod.CURRENT_STAGE,
                "product": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "authority_correction": mod.CURRENT_AUTHORITY,
                "authority": {
                    "external_effects": "EffectGate+EffectJournal",
                    "second_persistent_identity": "FORBIDDEN",
                    "second_truth_effect_or_recovery_authority": "FORBIDDEN",
                },
                "execution_policy": {
                    "free_only": True,
                    "isolated_sandbox_only": True,
                    "vps_testing_forbidden": True,
                    "self_hosted_vps_test_runners_forbidden": True,
                    "production_host_testing_forbidden": True,
                    "together_general_inference_and_fallback_forbidden": True,
                    "owner_paid_one_shot_directive_present_as_provenance": True,
                    "owner_paid_one_shot_directive_file": mod.TRAINING_PROVENANCE,
                    "owner_paid_one_shot_job_consumed": False,
                    "current_supervisor_together_training_forbidden": True,
                    "paid_or_unknown_provider_admission_boundary": "FAIL_CLOSED_BEFORE_CREDENTIAL_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION",
                    "other_paid_fallback": False,
                },
                "go_required_tracks": {
                    "track_a": "ENTITYOS_EXECUTABLE_CONVERGENCE",
                    "track_b": "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT",
                    "track_c": "GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS",
                },
                "runtime_credit": {
                    "entityos_hcu_whole_runtime_credit": 0,
                    "jspace_model_runtime_credit": 0,
                    "training_credit": 0,
                    "whole_product_pass": False,
                },
            },
            mod.CURRENT_AUTHORITY: {
                "schema_version": "8.61",
                "status": "CURRENT_AUTONOMOUS_SUPERVISOR_STEERING",
                "program": mod.CURRENT_PROGRAM,
                "product": mod.CURRENT_PRODUCT,
                "compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "free_only": {
                    "enabled": True,
                    "no_paid_fallback": True,
                    "together_training": "FORBIDDEN_IN_THIS_SUPERVISOR_MODE",
                    "together_general_inference": "FORBIDDEN",
                    "paid_subscription_unknown_provider_execution": "FAIL_CLOSED",
                },
                "evidence": {"together_job_created": False},
                "promotion_state": {"entityos_whole_runtime_pass": False, "training_credit": 0},
            },
            "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json": {
                "steering": mod.CURRENT_AUTHORITY,
                "free_only": {"enabled": True, "no_paid_fallback": True},
            },
            "the artefact/manifest.json": {
                "artifact": mod.CURRENT_PRODUCT,
                "product_endpoint": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "stage": mod.CURRENT_STAGE,
                "authority_correction": mod.CURRENT_AUTHORITY,
                "effect_authority": "EffectGate+EffectJournal",
                "execution_policy": {
                    "free_only": True,
                    "isolated_sandbox_only": True,
                    "vps_testing_forbidden": True,
                    "self_hosted_vps_test_runners_forbidden": True,
                    "production_host_testing_forbidden": True,
                    "together_general_inference_and_fallback_forbidden": True,
                    "owner_paid_one_shot_directive_present_as_provenance": True,
                    "owner_paid_one_shot_directive_file": mod.TRAINING_PROVENANCE,
                    "current_supervisor_together_training_forbidden": True,
                    "paid_or_unknown_provider_admission_boundary": "FAIL_CLOSED_BEFORE_CREDENTIAL_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION",
                    "other_paid_fallback": False,
                },
                "runtime_credit": {
                    "entityos_hcu_whole_runtime_credit": 0,
                    "jspace_model_runtime_credit": 0,
                    "training_credit": 0,
                    "whole_product_pass": False,
                },
            },
            mod.CONTROL41: {
                "schema_version": "4.1", "status": "ACTIVE", "mode": "FREE_ONLY",
                "cycle_policy": {"paid_fallback": False, "automatic_subscription_upgrade": False, "vps_testing": "FORBIDDEN"},
                "authority_rules": ["model_output_is_candidate_not_truth", "autonomous_cycle_may_not_modify_FRANK_harness"],
            },
            mod.CONTROL42: {
                "schema_version": "4.2-execution-boundary-addendum",
                "base_control_path": mod.CONTROL41, "base_control_blob_sha": "pending",
                "execution_routing": {
                    "direct_vps_host_candidate_execution": "FORBIDDEN",
                    "persistent_self_hosted_candidate_execution": "FORBIDDEN",
                    "production_host_testing": "FORBIDDEN",
                },
                "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True},
            },
            mod.CONTROL43: {
                "schema_version": "4.3-program-authority-addendum",
                "base_control_blob_sha": "pending",
                "execution_boundary_addendum_path": mod.CONTROL42,
                "execution_boundary_addendum_blob_sha": "pending",
                "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden_under_current_control": True, "runtime_credit_requires_exact_admitted_execution": True},
            },
            mod.CONTROL44: {
                "schema_version": "4.4-clayverse-product-authority-addendum",
                "prior_program_authority_addendum_path": mod.CONTROL43,
                "prior_program_authority_addendum_blob_sha": "pending",
                "effective_control_version": mod.LEGACY_EXPECTED_CONTROL,
                "program_identity_override": {"active_program": "CLAYVERSE_SINGLE_CONTAINER", "target_stage": "CLAYVERSE_ARTIFACT", "product_endpoint": "ClayVerse"},
                "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True, "vps_testing": False, "runtime_credit_requires_exact_admitted_isolated_execution": True},
            },
        }
        texts = {
            mod.TRAINING_PROVENANCE: "# Owner one-shot provenance\n",
            "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md": "Program: EntityOS + HCU\nTogether API: FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE\n",
            "the artefact/ARCHITECTURE.md": "# EntityOS + HCU architecture\n",
            "the artefact/README.md": "# EntityOS + HCU\nSUPERVISOR_STEERING_8_61.json\n",
            mod.ROOT_CLAUDE: "`PROGRAM=ENTITYOS_HCU`\nSUPERVISOR_STEERING_8_61.json\nFREE_ONLY\n",
        }
        for rel, data in files.items():
            p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        for rel, text in texts.items():
            p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")

        c42p = root / mod.CONTROL42
        c42 = json.loads(c42p.read_text()); c42["base_control_blob_sha"] = mod.git_blob_sha(root / mod.CONTROL41); c42p.write_text(json.dumps(c42, sort_keys=True))
        c43p = root / mod.CONTROL43
        c43 = json.loads(c43p.read_text()); c43["base_control_blob_sha"] = mod.git_blob_sha(root / mod.CONTROL41); c43["execution_boundary_addendum_blob_sha"] = mod.git_blob_sha(c42p); c43p.write_text(json.dumps(c43, sort_keys=True))
        c44p = root / mod.CONTROL44
        c44 = json.loads(c44p.read_text()); c44["prior_program_authority_addendum_blob_sha"] = mod.git_blob_sha(c43p); c44p.write_text(json.dumps(c44, sort_keys=True))
        return td, root

    def mutate(self, root, rel, fn):
        p = root / rel
        data = json.loads(p.read_text())
        fn(data)
        p.write_text(json.dumps(data, sort_keys=True))

    def test_current_861_free_only_tree_passes(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        result = mod.validate(root)
        self.assertTrue(result["pass"], result["errors"])

    def test_bootstrap_stale_852_pointer_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(root, "research_entity/continuity/BOOTSTRAP_MINIMAL.json", lambda d: d.__setitem__("authority_correction", "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"))
        self.assertIn("BOOTSTRAP_AUTHORITY_POINTER_MISMATCH", mod.validate(root)["errors"])

    def test_program_paid_lane_cannot_cross_admission_boundary(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(root, "research_entity/rooms/PROGRAM_STATE.json", lambda d: d["execution_policy"].__setitem__("paid_or_unknown_provider_admission_boundary", "ALLOW"))
        self.assertIn("PROGRAM_PAID_ADMISSION_FENCE_MISSING", mod.validate(root)["errors"])

    def test_supervisor_cannot_enable_together_training(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(root, mod.CURRENT_AUTHORITY, lambda d: d["free_only"].__setitem__("together_training", "ALLOWED"))
        self.assertIn("SUPERVISOR861_TOGETHER_TRAINING_FENCE_MISSING", mod.validate(root)["errors"])

    def test_manifest_cannot_retain_stale_852_authority(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(root, "the artefact/manifest.json", lambda d: d.__setitem__("authority_correction", "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"))
        self.assertIn("MANIFEST_AUTHORITY_POINTER_MISMATCH", mod.validate(root)["errors"])

    def test_training_credit_cannot_self_promote(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(root, "the artefact/manifest.json", lambda d: d["runtime_credit"].__setitem__("training_credit", 1))
        self.assertIn("MANIFEST_TRAINING_CREDIT_NONZERO", mod.validate(root)["errors"])

    def test_effect_authority_cannot_move_to_hcu(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(root, "research_entity/rooms/PROGRAM_STATE.json", lambda d: d["authority"].__setitem__("external_effects", "HCU"))
        self.assertIn("PROGRAM_EFFECT_AUTHORITY_MISMATCH", mod.validate(root)["errors"])

    def test_legacy_together_fence_remains_hash_bound(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.mutate(root, mod.CONTROL42, lambda d: d["preserved_hard_rules"].__setitem__("together_forbidden", False))
        errors = mod.validate(root)["errors"]
        self.assertIn("CONTROL42_TOGETHER_FENCE_WEAKENED", errors)
        self.assertIn("CONTROL43_EXEC_BLOB_MISMATCH", errors)

    def test_root_routing_requires_861(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        (root / mod.ROOT_CLAUDE).write_text("`PROGRAM=ENTITYOS_HCU`\nSUPERVISOR_STEERING_8_52.json\nFREE_ONLY\n")
        self.assertIn("ROOT_CLAUDE_CURRENT_AUTHORITY_MISSING", mod.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
