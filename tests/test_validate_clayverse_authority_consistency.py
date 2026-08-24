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

AUTH = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_68.json"
OWNER = "governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md"
DIRECTIVE = "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE_8_68.md"
PROVIDERS = ("groq", "mistral", "nvidia", "openrouter")


class AuthorityConsistencyTests(unittest.TestCase):
    def make_tree(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)

        def put_json(rel, obj):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")

        def put_text(rel, text):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        put_json("research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json", {"entity_id": "entity"})
        put_json("research_entity/continuity/BOOTSTRAP_MINIMAL.json", {
            "schema_version": "8.68",
            "entity_id": "entity",
            "identity": {"persistent_research_entity": "Clay", "temporary_worker": "ORGAN_NOT_ENTITY"},
            "active_program": mod.CURRENT_PROGRAM,
            "active_stage": mod.CURRENT_STAGE,
            "product_endpoint": mod.CURRENT_PRODUCT,
            "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
            "authority_correction": AUTH,
            "active_owner_authority": OWNER,
            "execution_surface": "FREE_ONLY; LOCAL_AND_CLAY_DIRECT_DEV_ALLOWED; EXTERNAL_LLM_PROVIDER_TRAFFIC_QUARANTINED_UNTIL_EXECUTABLE_TYPED_FREE_ADMISSION_PASS",
            "free_provider_allowlist_current": list(PROVIDERS),
            "all_worker_protocol": DIRECTIVE,
            "free_only": True,
            "paid_fallback": "FORBIDDEN",
            "together_api": "FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE",
            "effect_authority": "EffectGate+EffectJournal",
        })
        put_json("research_entity/rooms/PROGRAM_STATE.json", {
            "schema_version": "8.68",
            "program_id": "entityos-hcu",
            "status": "ACTIVE",
            "stage": mod.CURRENT_STAGE,
            "current_stage": mod.CURRENT_STAGE,
            "product": mod.CURRENT_PRODUCT,
            "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
            "authority_correction": AUTH,
            "active_owner_authority": OWNER,
            "authority": {
                "external_effects": "EffectGate+EffectJournal",
                "second_persistent_identity": "FORBIDDEN",
                "second_truth_effect_or_recovery_authority": "FORBIDDEN",
            },
            "execution_policy": {
                "free_only": True,
                "authorized_zero_cost_local_normal_user_execution": True,
                "authorized_clay_direct_dev_vps_sandbox_execution": True,
                "local_root_or_sudo_new_authority_implied": False,
                "unrelated_vps_host_changes_allowed": False,
                "new_external_production_effects_separately_gated": True,
                "production_host_testing_forbidden": True,
                "together_general_inference_and_fallback_forbidden": True,
                "current_supervisor_together_training_forbidden": True,
                "other_paid_fallback": False,
                "current_provider_runtime_credit": 0,
                "current_provider_runtime_inventory": "HISTORICAL_UNADMITTED_EXTERNAL_PROVIDER_TRAFFIC_OBSERVED; ALL_CURRENT_EXTERNAL_LLM_PROVIDER_TRAFFIC_QUARANTINED_PER_SUPERVISOR_8_68",
                "environment_attestation_is_authority": False,
            },
            "runtime_credit": {
                "external_provider_worker_runtime_credit": 0,
                "entityos_hcu_whole_runtime_credit": 0,
                "hcu_full_runtime_credit": 0,
                "jspace_model_runtime_credit": 0,
                "training_credit": 0,
                "whole_product_pass": False,
            },
        })
        put_json("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", {
            "schema_version": "8.68",
            "steering": AUTH,
        })
        put_json(AUTH, {
            "schema_version": "8.68",
            "active_program": mod.CURRENT_PROGRAM,
            "product": mod.CURRENT_PRODUCT,
            "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
            "free_only": {
                "enabled": True,
                "no_paid_fallback": True,
                "together_forbidden": True,
                "external_llm_provider_execution": "QUARANTINED_UNTIL_EXECUTABLE_TYPED_FREE_ADMISSION_PASS",
            },
            "promotion": {
                "entityos_whole_runtime_pass": False,
                "hcu_full_runtime_pass": False,
                "provider_runtime_credit": 0,
                "training_credit": 0,
            },
        })
        put_json("the artefact/manifest.json", {
            "artifact": mod.CURRENT_PRODUCT,
            "product_endpoint": mod.CURRENT_PRODUCT,
            "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
            "stage": mod.CURRENT_STAGE,
            "authority_correction": AUTH,
            "effect_authority": "EffectGate+EffectJournal",
            "execution_policy": {
                "active_supervisor_free_only": True,
                "active_supervisor_epoch": "8.68",
                "authorized_zero_cost_local_normal_user_execution": True,
                "authorized_clay_direct_dev_vps_sandbox_execution": True,
                "local_root_or_sudo_new_authority_implied": False,
                "unrelated_vps_host_changes_allowed": False,
                "new_external_production_effects_separately_gated": True,
                "production_host_testing_forbidden": True,
                "together_general_inference_and_fallback_forbidden": True,
                "current_supervisor_together_training": "FORBIDDEN_BEFORE_CREDENTIAL_KEY_LOOKUP_PREFLIGHT_NETWORK_IO_OR_JOB_CREATION",
                "other_paid_fallback": False,
                "external_llm_provider_execution": "QUARANTINED_UNTIL_FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT_V1_EXACT_SOURCE_PASS",
            },
            "runtime_credit": {
                "external_provider_worker_runtime_credit": 0,
                "entityos_hcu_whole_runtime_credit": 0,
                "hcu_full_runtime_credit": 0,
                "jspace_model_runtime_credit": 0,
                "training_credit": 0,
                "whole_product_pass": False,
            },
        })
        put_json(mod.PROVIDER_ADMISSION, {
            "schema": mod.PROVIDER_SCHEMA,
            "authority_epoch": "8.68",
            "mode": "FREE_ONLY",
            "product": mod.CURRENT_PRODUCT,
            "compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
            "runtime_provider_credit": 0,
            "execution_state": "EXTERNAL_LLM_PROVIDER_TRAFFIC_QUARANTINED_UNTIL_EXECUTABLE_TYPED_FREE_ADMISSION_PASS",
            "providers": {
                name: {"admitted": False, "cost_class": "UNKNOWN", "evidence_ref": f"test:{name}"}
                for name in PROVIDERS
            },
        })
        put_text("the artefact/ARCHITECTURE.md", "# EntityOS + HCU architecture\n")
        put_text("the artefact/README.md", "# EntityOS + HCU\n")
        put_text(mod.ROOT_CLAUDE, f"EntityOS HCU\nRead {AUTH}.\nRead {DIRECTIVE}.\n")
        put_text(DIRECTIVE, "EntityOS + HCU current worker directive\n")

        put_json(mod.CONTROL41, {
            "schema_version": "4.1",
            "status": "ACTIVE",
            "mode": "FREE_ONLY",
            "cycle_policy": {"paid_fallback": False, "automatic_subscription_upgrade": False, "vps_testing": "FORBIDDEN"},
            "authority_rules": ["model_output_is_candidate_not_truth", "autonomous_cycle_may_not_modify_FRANK_harness"],
        })
        put_json(mod.CONTROL42, {
            "schema_version": "4.2-execution-boundary-addendum",
            "base_control_path": mod.CONTROL41,
            "base_control_blob_sha": mod.git_blob_sha(root / mod.CONTROL41),
            "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True},
        })
        put_json(mod.CONTROL43, {
            "schema_version": "4.3-program-authority-addendum",
            "base_control_blob_sha": mod.git_blob_sha(root / mod.CONTROL41),
            "execution_boundary_addendum_path": mod.CONTROL42,
            "execution_boundary_addendum_blob_sha": mod.git_blob_sha(root / mod.CONTROL42),
            "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden_under_current_control": True},
        })
        put_json(mod.CONTROL44, {
            "schema_version": "4.4-clayverse-product-authority-addendum",
            "prior_program_authority_addendum_path": mod.CONTROL43,
            "prior_program_authority_addendum_blob_sha": mod.git_blob_sha(root / mod.CONTROL43),
            "effective_control_version": mod.LEGACY_EXPECTED_CONTROL,
            "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True, "vps_testing": False},
        })
        return td, root

    def test_current_868_passes(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        result = mod.validate(root)
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["resolved_authority"], AUTH)
        self.assertEqual(result["provider_admission_epoch"], "8.68")

    def test_successor_869_passes_without_validator_code_change(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        new = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_69.json"
        old = root / AUTH
        supervisor = json.loads(old.read_text()); supervisor["schema_version"] = "8.69"
        new_path = root / new; new_path.parent.mkdir(parents=True, exist_ok=True); new_path.write_text(json.dumps(supervisor)); old.unlink()
        for rel, key in [
            ("research_entity/continuity/BOOTSTRAP_MINIMAL.json", "authority_correction"),
            ("research_entity/rooms/PROGRAM_STATE.json", "authority_correction"),
            ("the artefact/manifest.json", "authority_correction"),
            ("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", "steering"),
        ]:
            path = root / rel; obj = json.loads(path.read_text()); obj[key] = new; path.write_text(json.dumps(obj))
        program = root / "research_entity/rooms/PROGRAM_STATE.json"; obj = json.loads(program.read_text()); obj["schema_version"] = "8.69"; program.write_text(json.dumps(obj))
        inbox = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"; obj = json.loads(inbox.read_text()); obj["schema_version"] = "8.69"; inbox.write_text(json.dumps(obj))
        manifest = root / "the artefact/manifest.json"; obj = json.loads(manifest.read_text()); obj["execution_policy"]["active_supervisor_epoch"] = "8.69"; manifest.write_text(json.dumps(obj))
        admission = root / mod.PROVIDER_ADMISSION; obj = json.loads(admission.read_text()); obj["authority_epoch"] = "8.69"; admission.write_text(json.dumps(obj))
        (root / mod.ROOT_CLAUDE).write_text(f"EntityOS HCU\nRead {new}.\nRead {DIRECTIVE}.\n")
        result = mod.validate(root)
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["resolved_authority_schema"], "8.69")

    def test_authority_pointer_split_brain_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "the artefact/manifest.json"; obj = json.loads(path.read_text()); obj["authority_correction"] = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_67.json"; path.write_text(json.dumps(obj))
        self.assertIn("AUTHORITY_POINTER_SPLIT_BRAIN", mod.validate(root)["errors"])

    def test_owner_pointer_split_brain_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"; obj = json.loads(path.read_text()); obj["active_owner_authority"] = "governance/OTHER.md"; path.write_text(json.dumps(obj))
        self.assertIn("OWNER_AUTHORITY_POINTER_SPLIT_BRAIN", mod.validate(root)["errors"])

    def test_provider_epoch_mismatch_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.PROVIDER_ADMISSION; obj = json.loads(path.read_text()); obj["authority_epoch"] = "8.67"; path.write_text(json.dumps(obj))
        self.assertIn("PROVIDER_ADMISSION_EPOCH_MISMATCH", mod.validate(root)["errors"])

    def test_nonfree_provider_cannot_self_admit(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.PROVIDER_ADMISSION; obj = json.loads(path.read_text()); obj["providers"]["groq"] = {"admitted": True, "cost_class": "PAID", "evidence_ref": "forged"}; path.write_text(json.dumps(obj))
        self.assertIn("PROVIDER_ADMISSION_NONFREE_SELF_ADMIT:groq", mod.validate(root)["errors"])

    def test_provider_quarantine_cannot_be_removed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / AUTH; obj = json.loads(path.read_text()); obj["free_only"]["external_llm_provider_execution"] = "ALLOWED"; path.write_text(json.dumps(obj))
        self.assertIn("SUPERVISOR_PROVIDER_QUARANTINE_MISSING", mod.validate(root)["errors"])

    def test_stale_root_routing_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        (root / mod.ROOT_CLAUDE).write_text("EntityOS HCU\nRead SUPERVISOR_STEERING_8_65.json\n")
        errors = mod.validate(root)["errors"]
        self.assertIn("ROOT_CLAUDE_CURRENT_AUTHORITY_MISSING", errors)
        self.assertIn("ROOT_CLAUDE_CURRENT_WORKER_DIRECTIVE_MISSING", errors)

    def test_current_owner_local_vps_authority_survives_legacy_ancestry(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        result = mod.validate(root)
        self.assertTrue(result["pass"], result)
        program = json.loads((root / "research_entity/rooms/PROGRAM_STATE.json").read_text())
        self.assertTrue(program["execution_policy"]["authorized_clay_direct_dev_vps_sandbox_execution"])

    def test_runtime_credit_cannot_self_promote(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "the artefact/manifest.json"; obj = json.loads(path.read_text()); obj["runtime_credit"]["jspace_model_runtime_credit"] = 1; path.write_text(json.dumps(obj))
        self.assertIn("MANIFEST_JSPACE_RUNTIME_CREDIT_NONZERO", mod.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
