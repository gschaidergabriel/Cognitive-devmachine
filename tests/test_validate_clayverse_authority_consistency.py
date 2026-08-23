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


class AuthorityConsistency861Tests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory(); root = Path(td.name)
        files = {
            "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json": {"entity_id": "entity"},
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json": {
                "entity_id": "entity", "identity": {"persistent_research_entity": "Clay", "temporary_worker": "ORGAN_NOT_ENTITY"},
                "active_program": mod.CURRENT_PROGRAM, "active_stage": mod.CURRENT_STAGE, "product_endpoint": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE, "authority_correction": mod.CURRENT_AUTHORITY,
                "free_only": True, "paid_fallback": "FORBIDDEN", "execution_surface": "AUTHORIZED_ISOLATED_FREE_SANDBOX_ONLY_IN_CURRENT_AUTONOMOUS_SUPERVISOR_MODE",
                "together_api": "FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE; GENERAL_INFERENCE_FORBIDDEN; OWNER_PAID_ONE_SHOT_DIRECTIVE_QUARANTINED_WITH_ZERO_EXECUTION_CREDIT",
                "together_one_shot_training_consumed": False,
                "current_supervisor_together_training": "FORBIDDEN_BEFORE_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION",
            },
            "research_entity/rooms/PROGRAM_STATE.json": {
                "program_id": "entityos-hcu", "status": "ACTIVE", "stage": mod.CURRENT_STAGE, "current_stage": mod.CURRENT_STAGE,
                "product": mod.CURRENT_PRODUCT, "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE, "authority_correction": mod.CURRENT_AUTHORITY,
                "execution_policy": {
                    "free_only": True, "isolated_sandbox_only": True, "vps_testing_forbidden": True, "self_hosted_vps_test_runners_forbidden": True, "production_host_testing_forbidden": True,
                    "together_general_inference_and_fallback_forbidden": True, "owner_paid_one_shot_directive_present_as_provenance": True,
                    "owner_paid_one_shot_directive_file": mod.PAID_DIRECTIVE_PROVENANCE, "owner_paid_one_shot_job_consumed": False,
                    "current_supervisor_together_training_forbidden": True,
                    "paid_or_unknown_provider_admission_boundary": "FAIL_CLOSED_BEFORE_CREDENTIAL_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION",
                    "other_paid_fallback": False,
                },
                "go_required_tracks": {"track_a": "ENTITYOS_EXECUTABLE_CONVERGENCE", "track_b": "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT", "track_c": "GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS"},
                "training_program": {"owner_paid_one_shot_directive_status": "QUARANTINED_FOR_CURRENT_FREE_ONLY_SUPERVISOR", "paid_preflight_or_job_creation_allowed_now": False},
                "runtime_credit": {"entityos_hcu_whole_runtime_credit": 0, "jspace_model_runtime_credit": 0, "training_credit": 0, "whole_product_pass": False},
            },
            mod.CURRENT_AUTHORITY: {
                "schema_version": "8.61", "status": "CURRENT_AUTONOMOUS_SUPERVISOR_STEERING", "program": mod.CURRENT_PROGRAM, "product": mod.CURRENT_PRODUCT, "compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "free_only": {"enabled": True, "no_paid_fallback": True, "together_training": "FORBIDDEN_IN_THIS_SUPERVISOR_MODE", "together_general_inference": "FORBIDDEN", "paid_subscription_unknown_provider_execution": "FAIL_CLOSED", "rule": "PAID, SUBSCRIPTION and UNKNOWN lanes must be rejected before credential/key lookup and before network I/O."},
                "promotion_state": {"entityos_whole_runtime_pass": False, "hcu_runtime_credit_change": False, "canonical_semantics_promotion": False, "training_credit": 0},
            },
            "the artefact/manifest.json": {
                "artifact": mod.CURRENT_PRODUCT, "product_endpoint": mod.CURRENT_PRODUCT, "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "stage": mod.CURRENT_STAGE, "authority_correction": mod.CURRENT_AUTHORITY,
                "execution_policy": {"free_only": True, "isolated_sandbox_only": True, "vps_testing_forbidden": True, "together_general_inference_and_fallback_forbidden": True, "owner_paid_one_shot_directive_present_as_provenance": True, "owner_paid_one_shot_job_consumed": False, "current_supervisor_together_training_forbidden": True, "paid_or_unknown_provider_admission_boundary": "FAIL_CLOSED_BEFORE_CREDENTIAL_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION", "other_paid_fallback": False},
                "runtime_credit": {"entityos_hcu_whole_runtime_credit": 0, "jspace_model_runtime_credit": 0, "training_credit": 0, "whole_product_pass": False},
            },
            mod.CONTROL41: {"schema_version": "4.1", "status": "ACTIVE", "mode": "FREE_ONLY", "cycle_policy": {"paid_fallback": False, "automatic_subscription_upgrade": False, "vps_testing": "FORBIDDEN"}, "authority_rules": ["model_output_is_candidate_not_truth", "autonomous_cycle_may_not_modify_FRANK_harness"]},
            mod.CONTROL42: {"schema_version": "4.2-execution-boundary-addendum", "status": "ACTIVE", "mode": "FREE_ONLY", "base_control_path": mod.CONTROL41, "base_control_blob_sha": "pending", "execution_routing": {"direct_vps_host_candidate_execution": "FORBIDDEN", "persistent_self_hosted_candidate_execution": "FORBIDDEN", "production_host_testing": "FORBIDDEN"}, "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True, "frank_harness_modification": "FORBIDDEN"}},
            mod.CONTROL43: {"schema_version": "4.3-program-authority-addendum", "status": "ACTIVE", "mode": "FREE_ONLY", "base_control_path": mod.CONTROL41, "base_control_blob_sha": "pending", "execution_boundary_addendum_path": mod.CONTROL42, "execution_boundary_addendum_blob_sha": "pending", "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden_under_current_control": True, "runtime_credit_requires_exact_admitted_execution": True}},
            mod.CONTROL44: {"schema_version": "4.4-clayverse-product-authority-addendum", "status": "ACTIVE", "mode": "FREE_ONLY", "prior_program_authority_addendum_blob_sha": "pending", "program_identity_override": {"active_program": "CLAYVERSE_SINGLE_CONTAINER", "product_endpoint": "ClayVerse"}, "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True, "runtime_credit_requires_exact_admitted_isolated_execution": True}},
        }
        texts = {
            "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md": "Program: EntityOS + HCU\nFREE_ONLY\n",
            "the artefact/ARCHITECTURE.md": "# EntityOS HCU architecture\n",
            "the artefact/README.md": "# EntityOS HCU\nSUPERVISOR_STEERING_8_61.json\nFREE_ONLY\n",
            mod.ROOT_CLAUDE: "# Clay\n`PROGRAM=ENTITYOS_HCU`\nSUPERVISOR_STEERING_8_61.json\nFREE_ONLY: Together and paid provider lanes are forbidden.\n",
        }
        for rel, data in files.items():
            p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(data,sort_keys=True),encoding="utf-8")
        for rel, text in texts.items():
            p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding="utf-8")
        p42=root/mod.CONTROL42; d42=json.loads(p42.read_text()); d42["base_control_blob_sha"]=mod.git_blob_sha(root/mod.CONTROL41); p42.write_text(json.dumps(d42,sort_keys=True))
        p43=root/mod.CONTROL43; d43=json.loads(p43.read_text()); d43["base_control_blob_sha"]=mod.git_blob_sha(root/mod.CONTROL41); d43["execution_boundary_addendum_blob_sha"]=mod.git_blob_sha(p42); p43.write_text(json.dumps(d43,sort_keys=True))
        p44=root/mod.CONTROL44; d44=json.loads(p44.read_text()); d44["prior_program_authority_addendum_blob_sha"]=mod.git_blob_sha(p43); p44.write_text(json.dumps(d44,sort_keys=True))
        return td, root

    def test_coherent_861_free_only_authority_passes(self):
        td,root=self.make_tree(); self.addCleanup(td.cleanup); r=mod.validate(root); self.assertTrue(r["pass"],r["errors"])
    def test_successor_rollback_regression_fails_closed(self):
        td,root=self.make_tree(); self.addCleanup(td.cleanup); p=root/"research_entity/continuity/BOOTSTRAP_MINIMAL.json"; d=json.loads(p.read_text()); d["authority_correction"]="research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_53.json"; p.write_text(json.dumps(d)); self.assertIn("BOOTSTRAP_AUTHORITY_POINTER_MISMATCH",mod.validate(root)["errors"])
    def test_paid_preflight_cannot_reenable(self):
        td,root=self.make_tree(); self.addCleanup(td.cleanup); p=root/"research_entity/rooms/PROGRAM_STATE.json"; d=json.loads(p.read_text()); d["training_program"]["paid_preflight_or_job_creation_allowed_now"]=True; p.write_text(json.dumps(d)); self.assertIn("PROGRAM_PAID_PREFLIGHT_NOT_FORBIDDEN",mod.validate(root)["errors"])
    def test_together_training_cannot_reenable(self):
        td,root=self.make_tree(); self.addCleanup(td.cleanup); p=root/mod.CURRENT_AUTHORITY; d=json.loads(p.read_text()); d["free_only"]["together_training"]="ALLOWED"; p.write_text(json.dumps(d)); self.assertIn("STEERING861_TOGETHER_FENCE_WEAKENED",mod.validate(root)["errors"])
    def test_manifest_cannot_lag_to_852(self):
        td,root=self.make_tree(); self.addCleanup(td.cleanup); p=root/"the artefact/manifest.json"; d=json.loads(p.read_text()); d["authority_correction"]="research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"; p.write_text(json.dumps(d)); self.assertIn("MANIFEST_AUTHORITY_POINTER_MISMATCH",mod.validate(root)["errors"])
    def test_manifest_cannot_reenable_paid_one_shot(self):
        td,root=self.make_tree(); self.addCleanup(td.cleanup); p=root/"the artefact/manifest.json"; d=json.loads(p.read_text()); d["execution_policy"]["current_supervisor_together_training_forbidden"]=False; p.write_text(json.dumps(d)); self.assertIn("MANIFEST_TOGETHER_FREE_ONLY_FENCE_MISSING",mod.validate(root)["errors"])
    def test_runtime_credit_cannot_self_promote(self):
        td,root=self.make_tree(); self.addCleanup(td.cleanup); p=root/"research_entity/rooms/PROGRAM_STATE.json"; d=json.loads(p.read_text()); d["runtime_credit"]["training_credit"]=1; p.write_text(json.dumps(d)); self.assertIn("PROGRAM_RUNTIME_CREDIT_PREMATURE",mod.validate(root)["errors"])
    def test_historical_together_ban_stays_bound(self):
        td,root=self.make_tree(); self.addCleanup(td.cleanup); p=root/mod.CONTROL42; d=json.loads(p.read_text()); d["preserved_hard_rules"]["together_forbidden"]=False; p.write_text(json.dumps(d,sort_keys=True)); errors=mod.validate(root)["errors"]; self.assertIn("CONTROL42_TOGETHER_FENCE_WEAKENED",errors); self.assertIn("CONTROL43_ANCESTRY_MISMATCH",errors)


if __name__ == "__main__":
    unittest.main()
