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
            "entity_id": "entity",
            "identity": {"persistent_research_entity": "Clay", "temporary_worker": "ORGAN_NOT_ENTITY"},
            "active_program": mod.CURRENT_PROGRAM,
            "active_stage": mod.CURRENT_STAGE,
            "product_endpoint": mod.CURRENT_PRODUCT,
            "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
            "authority_correction": AUTH,
            "active_owner_authority": OWNER,
            "free_only": True,
            "paid_fallback": "FORBIDDEN",
            "together_api": "FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE",
            "effect_authority": "EffectGate+EffectJournal",
        })
        put_json("research_entity/rooms/PROGRAM_STATE.json", {
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
                "production_host_testing_forbidden": True,
                "together_general_inference_and_fallback_forbidden": True,
                "current_supervisor_together_training_forbidden": True,
                "other_paid_fallback": False,
                "external_llm_provider_execution": "QUARANTINED_UNTIL_EXECUTABLE_TYPED_FREE_ADMISSION_PASS",
                "environment_attestation_is_authority": False,
            },
            "runtime_credit": {
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
            "active_owner_authority": OWNER,
            "effect_authority": "EffectGate+EffectJournal",
            "execution_policy": {
                "active_supervisor_free_only": True,
                "owner_authorized_zero_cost_local_normal_user_execution": True,
                "owner_authorized_clay_direct_dev_vps_sandbox_execution": True,
                "production_host_testing_forbidden": True,
                "together_general_inference_and_fallback_forbidden": True,
                "other_paid_fallback": False,
                "external_llm_provider_execution": "QUARANTINED_UNTIL_EXECUTABLE_TYPED_FREE_ADMISSION_PASS",
            },
            "runtime_credit": {
                "entityos_hcu_whole_runtime_credit": 0,
                "hcu_full_runtime_credit": 0,
                "jspace_model_runtime_credit": 0,
                "training_credit": 0,
                "whole_product_pass": False,
            },
        })
        put_text("the artefact/ARCHITECTURE.md", "# EntityOS + HCU architecture\n")
        put_text("the artefact/README.md", "# EntityOS + HCU\n")
        put_text(mod.ROOT_CLAUDE, f"EntityOS HCU\nRead {AUTH}.\n")

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
        self.assertEqual(result["resolved_owner_authority"], OWNER)

    def test_successor_869_passes_without_validator_code_change(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        new = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_69.json"
        old = root / AUTH
        data = json.loads(old.read_text())
        data["schema_version"] = "8.69"
        new_path = root / new
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.write_text(json.dumps(data))
        old.unlink()
        for rel, key in [
            ("research_entity/continuity/BOOTSTRAP_MINIMAL.json", "authority_correction"),
            ("research_entity/rooms/PROGRAM_STATE.json", "authority_correction"),
            ("the artefact/manifest.json", "authority_correction"),
            ("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", "steering"),
        ]:
            path = root / rel
            obj = json.loads(path.read_text())
            obj[key] = new
            path.write_text(json.dumps(obj))
        (root / mod.ROOT_CLAUDE).write_text(f"EntityOS HCU\nRead {new}.\n")
        result = mod.validate(root)
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["resolved_authority_schema"], "8.69")

    def test_authority_pointer_split_brain_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "the artefact/manifest.json"
        obj = json.loads(path.read_text())
        obj["authority_correction"] = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_67.json"
        path.write_text(json.dumps(obj))
        self.assertIn("AUTHORITY_POINTER_SPLIT_BRAIN", mod.validate(root)["errors"])

    def test_owner_pointer_split_brain_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "the artefact/manifest.json"
        obj = json.loads(path.read_text())
        obj["active_owner_authority"] = "governance/OTHER.md"
        path.write_text(json.dumps(obj))
        self.assertIn("OWNER_AUTHORITY_POINTER_SPLIT_BRAIN", mod.validate(root)["errors"])

    def test_filename_schema_mismatch_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / AUTH
        obj = json.loads(path.read_text())
        obj["schema_version"] = "8.67"
        path.write_text(json.dumps(obj))
        self.assertIn("AUTHORITY_FILENAME_SCHEMA_MISMATCH", mod.validate(root)["errors"])

    def test_provider_quarantine_cannot_be_removed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / AUTH
        obj = json.loads(path.read_text())
        obj["free_only"]["external_llm_provider_execution"] = "ALLOWED"
        path.write_text(json.dumps(obj))
        self.assertIn("SUPERVISOR_PROVIDER_QUARANTINE_MISSING", mod.validate(root)["errors"])

    def test_current_owner_local_vps_authority_is_not_reverted_by_legacy_ancestry(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        result = mod.validate(root)
        self.assertTrue(result["pass"], result)
        program = json.loads((root / "research_entity/rooms/PROGRAM_STATE.json").read_text())
        self.assertTrue(program["execution_policy"]["authorized_clay_direct_dev_vps_sandbox_execution"])

    def test_program_runtime_credit_cannot_self_promote(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        obj = json.loads(path.read_text())
        obj["runtime_credit"]["entityos_hcu_whole_runtime_credit"] = 1
        path.write_text(json.dumps(obj))
        self.assertIn("PROGRAM_RUNTIME_CREDIT_NONZERO", mod.validate(root)["errors"])

    def test_manifest_cannot_reactivate_clayverse(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "the artefact/manifest.json"
        obj = json.loads(path.read_text())
        obj["artifact"] = "ClayVerse"
        obj["product_endpoint"] = "ClayVerse"
        path.write_text(json.dumps(obj))
        errors = mod.validate(root)["errors"]
        self.assertIn("MANIFEST_ARTIFACT_MISMATCH", errors)
        self.assertIn("MANIFEST_PRODUCT_ENDPOINT_MISMATCH", errors)


if __name__ == "__main__":
    unittest.main()
