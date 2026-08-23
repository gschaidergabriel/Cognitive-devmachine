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
                "mandatory_invariants": [
                    "EntityOS is the sole current product/system identity",
                    "HCU is the sole current integrated cognition/compute architecture",
                    "FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT",
                ],
                "execution_surface": "AUTHORIZED_ISOLATED_SANDBOX_ONLY",
                "together_api": "GENERAL_INFERENCE_AND_FALLBACK_FORBIDDEN; EXACTLY_ONE_OWNER_AUTHORIZED_APPROX_08B_JSPACE_GWT_FINETUNE_ALLOWED_UNTIL_CONSUMED",
                "together_training_authority": mod.TRAINING_AUTHORITY,
                "together_one_shot_training_consumed": False,
                "paid_fallback": "FORBIDDEN_EXCEPT_COST_INHERENT_TO_THE_ONE_OWNER_AUTHORIZED_TRAINING_JOB",
                "final_paid_model_training": "ONE_SHOT_APPROX_08B_JSPACE_GWT_TRAINING_AUTHORIZED; SECOND_JOB_REQUIRES_NEW_OWNER_AUTHORIZATION",
                "effect_authority": "EffectGate+EffectJournal",
            },
            "research_entity/rooms/PROGRAM_STATE.json": {
                "program_id": "entityos-hcu", "status": "ACTIVE", "stage": mod.CURRENT_STAGE, "current_stage": mod.CURRENT_STAGE,
                "product": mod.CURRENT_PRODUCT, "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "authority_correction": mod.CURRENT_AUTHORITY,
                "identity": {"persistent_research_entity": "Clay", "temporary_workers": "ORGANS_NOT_ENTITIES"},
                "authority": {"external_effects": "EffectGate+EffectJournal", "second_persistent_identity": "FORBIDDEN", "second_truth_effect_or_recovery_authority": "FORBIDDEN"},
                "execution_policy": {
                    "free_only_default": True, "isolated_sandbox_only": True, "vps_testing_forbidden": True,
                    "self_hosted_vps_test_runners_forbidden": True, "production_host_testing_forbidden": True,
                    "together_general_inference_and_fallback_forbidden": True,
                    "together_one_shot_08b_jspace_gwt_finetune_authorized": True,
                    "together_one_shot_08b_jspace_gwt_finetune_consumed": False,
                    "together_training_authority_file": mod.TRAINING_AUTHORITY,
                    "second_together_training_requires_new_owner_authorization": True, "other_paid_fallback": False,
                },
                "go_required_tracks": {"track_a": "ENTITYOS_EXECUTABLE_CONVERGENCE", "track_b": "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT", "track_c": "GLOBAL_JSPACE_GWT_PROTOTYPE_AND_ONE_SHOT_08B_TRAINING_READINESS"},
                "training_program": {"one_shot_job_authorized": True, "one_shot_job_consumed": False, "required_precondition": "FUNCTIONAL_INSTRUMENTED_GLOBAL_JSPACE_GWT_PROTOTYPE_WITH_REAL_TRACES"},
                "runtime_credit": {"entityos_hcu_whole_runtime_credit": 0, "whole_product_pass": False},
            },
            mod.CURRENT_AUTHORITY: {
                "schema_version": "8.53", "status": "CURRENT_EXPLICIT_OWNER_STEERING", "program": mod.CURRENT_PROGRAM,
                "product": mod.CURRENT_PRODUCT, "compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "sandbox_pass_directive": {"law": "discover execution surfaces", "vps_self_hosted_production_fallback_for_test_credit": "FORBIDDEN", "false_pass": "FORBIDDEN"},
                "together_policy": {"general_inference_fallback": "FORBIDDEN", "recurring_training": "FORBIDDEN", "one_shot_approx_08b_jspace_gwt_finetune": "OWNER_AUTHORIZED_UNTIL_ONE_JOB_IS_CREATED", "one_shot_consumed": False, "second_job": "REQUIRES_NEW_EXPLICIT_OWNER_AUTHORIZATION", "training_contract": mod.TRAINING_AUTHORITY},
                "current_implementation_delta": {"runtime_credit": 0, "training_job_started": False},
            },
            "the artefact/manifest.json": {
                "artifact": mod.CURRENT_PRODUCT, "product_endpoint": mod.CURRENT_PRODUCT, "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "stage": mod.CURRENT_STAGE, "canonical_workspace": "the artefact/", "authority_correction": mod.CURRENT_AUTHORITY,
                "effect_authority": "EffectGate+EffectJournal",
                "execution_policy": {"free_only_default": True, "isolated_sandbox_only": True, "vps_testing_forbidden": True, "together_general_inference_and_fallback_forbidden": True, "together_one_shot_08b_jspace_gwt_finetune_authorized": True, "together_one_shot_08b_jspace_gwt_finetune_consumed": False, "together_training_authority": mod.TRAINING_AUTHORITY, "other_paid_fallback": False, "second_paid_training_requires_owner_authorization": True},
                "runtime_credit": {"entityos_hcu_whole_runtime_credit": 0, "whole_product_pass": False},
            },
            mod.CONTROL41: {"schema_version": "4.1", "status": "ACTIVE", "mode": "FREE_ONLY", "cycle_policy": {"paid_fallback": False, "automatic_subscription_upgrade": False, "vps_testing": "FORBIDDEN"}, "authority_rules": ["model_output_is_candidate_not_truth", "autonomous_cycle_may_not_modify_FRANK_harness"]},
            mod.CONTROL42: {"schema_version": "4.2-execution-boundary-addendum", "status": "ACTIVE", "mode": "FREE_ONLY", "base_control_path": mod.CONTROL41, "base_control_blob_sha": "pending", "execution_routing": {"direct_vps_host_candidate_execution": "FORBIDDEN", "persistent_self_hosted_candidate_execution": "FORBIDDEN", "production_host_testing": "FORBIDDEN"}, "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True, "frank_harness_modification": "FORBIDDEN"}},
            mod.CONTROL43: {"schema_version": "4.3-program-authority-addendum", "status": "ACTIVE", "mode": "FREE_ONLY", "base_control_path": mod.CONTROL41, "base_control_blob_sha": "pending", "execution_boundary_addendum_path": mod.CONTROL42, "execution_boundary_addendum_blob_sha": "pending", "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden_under_current_control": True, "model_output_is_candidate_not_truth": True, "runtime_credit_requires_exact_admitted_execution": True, "frank_harness_modification": "FORBIDDEN"}},
            mod.CONTROL44: {"schema_version": "4.4-clayverse-product-authority-addendum", "status": "ACTIVE", "mode": "FREE_ONLY", "base_control_path": mod.CONTROL41, "execution_boundary_addendum_path": mod.CONTROL42, "prior_program_authority_addendum_path": mod.CONTROL43, "prior_program_authority_addendum_blob_sha": "pending", "effective_control_version": mod.LEGACY_EXPECTED_CONTROL, "program_identity_override": {"active_program": "CLAYVERSE_SINGLE_CONTAINER", "target_stage": "CLAYVERSE_ARTIFACT", "product_endpoint": "ClayVerse"}, "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True, "vps_testing": False, "runtime_credit_requires_exact_admitted_isolated_execution": True, "model_output_is_candidate_not_truth": True, "frank_harness_modification": "FORBIDDEN"}},
        }
        texts = {
            mod.TRAINING_AUTHORITY: "Owner authorizes one Together full fine-tuning job for the exact intended ~0.8B J-Space/GWT HCU model.\n",
            "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md": "Program: EntityOS + HCU\nTogether API: GENERAL_INFERENCE_AND_FALLBACK_FORBIDDEN; one-shot training scoped.\n",
            "the artefact/ARCHITECTURE.md": "# EntityOS + HCU architecture\nEntityOS is current product. HCU is current compute architecture.\n",
            "the artefact/README.md": "# EntityOS + HCU\nCurrent authority: SUPERVISOR_STEERING_8_53.json\nOne-shot ~0.8B J-Space/GWT training is owner-authorized after gates.\n",
            mod.ROOT_CLAUDE: "# CLAY current EntityOS/HCU\n`PROGRAM=ENTITYOS_HCU`\n`STAGE=ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP`\n`PRODUCT=EntityOS`\n`COMPUTE_ARCHITECTURE=HCU`\nRead SUPERVISOR_STEERING_8_53.json.\nGeneral Together inference/fallback is forbidden. One owner-authorized ~0.8B J-Space/GWT fine-tune is admitted after required gates.\n",
            mod.WORKER_DIRECTIVE: "Newest explicit owner correction. SUPERVISOR_STEERING_8_53.json.\nOne serious Together fine-tuning job is authorized. Together remains forbidden for ordinary inference/fallback.\n",
        }
        for rel, data in files.items():
            p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        for rel, text in texts.items():
            p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")
        p42=root/mod.CONTROL42; d42=json.loads(p42.read_text()); d42["base_control_blob_sha"]=mod.git_blob_sha(root/mod.CONTROL41); p42.write_text(json.dumps(d42,sort_keys=True))
        p43=root/mod.CONTROL43; d43=json.loads(p43.read_text()); d43["base_control_blob_sha"]=mod.git_blob_sha(root/mod.CONTROL41); d43["execution_boundary_addendum_blob_sha"]=mod.git_blob_sha(p42); p43.write_text(json.dumps(d43,sort_keys=True))
        p44=root/mod.CONTROL44; d44=json.loads(p44.read_text()); d44["prior_program_authority_addendum_blob_sha"]=mod.git_blob_sha(p43); p44.write_text(json.dumps(d44,sort_keys=True))
        return td, root

    def test_current_853_authority_passes(self):
        td, root=self.make_tree(); self.addCleanup(td.cleanup); result=mod.validate(root); self.assertTrue(result["pass"], result["errors"])
    def test_authority_successor_rollback_poison_fails_closed(self):
        td, root=self.make_tree(); self.addCleanup(td.cleanup); p=root/"research_entity/continuity/BOOTSTRAP_MINIMAL.json"; data=json.loads(p.read_text()); data["authority_correction"]="research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"; p.write_text(json.dumps(data)); self.assertIn("BOOTSTRAP_AUTHORITY_POINTER_MISMATCH", mod.validate(root)["errors"])
    def test_general_together_fallback_cannot_be_enabled(self):
        td, root=self.make_tree(); self.addCleanup(td.cleanup); p=root/"research_entity/rooms/PROGRAM_STATE.json"; data=json.loads(p.read_text()); data["execution_policy"]["together_general_inference_and_fallback_forbidden"]=False; p.write_text(json.dumps(data)); self.assertIn("PROGRAM_TOGETHER_GENERAL_FALLBACK_FENCE_MISSING",mod.validate(root)["errors"])
    def test_one_shot_training_authority_cannot_disappear(self):
        td, root=self.make_tree(); self.addCleanup(td.cleanup); p=root/"the artefact/manifest.json"; data=json.loads(p.read_text()); data["execution_policy"]["together_one_shot_08b_jspace_gwt_finetune_authorized"]=False; p.write_text(json.dumps(data)); self.assertIn("MANIFEST_ONE_SHOT_TRAINING_STATE_MISMATCH",mod.validate(root)["errors"])
    def test_second_training_cannot_self_authorize(self):
        td, root=self.make_tree(); self.addCleanup(td.cleanup); p=root/mod.CURRENT_AUTHORITY; data=json.loads(p.read_text()); data["together_policy"]["second_job"]="AUTHORIZED"; p.write_text(json.dumps(data)); self.assertIn("STEERING853_SECOND_JOB_GATE_MISSING",mod.validate(root)["errors"])
    def test_runtime_credit_cannot_self_promote(self):
        td, root=self.make_tree(); self.addCleanup(td.cleanup); p=root/"research_entity/rooms/PROGRAM_STATE.json"; data=json.loads(p.read_text()); data["runtime_credit"]["entityos_hcu_whole_runtime_credit"]=1; p.write_text(json.dumps(data)); self.assertIn("PROGRAM_RUNTIME_CREDIT_PREMATURE",mod.validate(root)["errors"])
    def test_historical_together_ban_remains_provenance_bound(self):
        td, root=self.make_tree(); self.addCleanup(td.cleanup); p=root/mod.CONTROL42; data=json.loads(p.read_text()); data["preserved_hard_rules"]["together_forbidden"]=False; p.write_text(json.dumps(data,sort_keys=True)); errors=mod.validate(root)["errors"]; self.assertIn("CONTROL42_TOGETHER_FENCE_WEAKENED",errors); self.assertIn("CONTROL43_ANCESTRY_MISMATCH",errors)
    def test_root_cannot_pin_852_as_current(self):
        td, root=self.make_tree(); self.addCleanup(td.cleanup); p=root/mod.ROOT_CLAUDE; p.write_text(p.read_text().replace("SUPERVISOR_STEERING_8_53.json","SUPERVISOR_STEERING_8_52.json")); self.assertIn("ROOT_CLAUDE_CURRENT_AUTHORITY_MISSING",mod.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
