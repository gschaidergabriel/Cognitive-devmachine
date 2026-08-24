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
    def make_tree(self, version="8.68"):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        suffix = version.replace(".", "_")
        authority = f"research_entity/claycode/autonomous/SUPERVISOR_STEERING_{suffix}.json"

        def put_json(rel, obj):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")

        def put_text(rel, text):
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        put_json("research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json", {"entity_id": "entity"})
        put_json(
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
            {
                "entity_id": "entity",
                "identity": {"persistent_research_entity": "Clay", "temporary_worker": "ORGAN_NOT_ENTITY"},
                "active_program": mod.CURRENT_PROGRAM,
                "active_stage": mod.CURRENT_STAGE,
                "product_endpoint": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "authority_correction": authority,
                "effect_authority": "EffectGate+EffectJournal",
                "free_only": True,
                "paid_fallback": "FORBIDDEN",
                "together_api": "FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE",
                "free_provider_allowlist_current": ["groq", "mistral", "nvidia", "openrouter"],
            },
        )
        put_json(
            "research_entity/rooms/PROGRAM_STATE.json",
            {
                "schema_version": version,
                "program_id": "entityos-hcu",
                "status": "ACTIVE",
                "stage": mod.CURRENT_STAGE,
                "current_stage": mod.CURRENT_STAGE,
                "product": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "authority_correction": authority,
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
                    "production_host_testing_forbidden": True,
                    "external_provider_admission_file": mod.CANONICAL_PROVIDER_ADMISSION,
                    "together_general_inference_and_fallback_forbidden": True,
                    "other_paid_fallback": False,
                },
                "runtime_credit": {
                    "entityos_hcu_whole_runtime_credit": 0,
                    "hcu_full_runtime_credit": 0,
                    "jspace_model_runtime_credit": 0,
                    "training_credit": 0,
                    "whole_product_pass": False,
                },
            },
        )
        put_json(
            "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
            {"schema_version": version, "steering": authority},
        )
        put_json(
            "the artefact/manifest.json",
            {
                "artifact": mod.CURRENT_PRODUCT,
                "product_endpoint": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "stage": mod.CURRENT_STAGE,
                "authority_correction": authority,
                "effect_authority": "EffectGate+EffectJournal",
                "execution_policy": {
                    "active_supervisor_free_only": True,
                    "authorized_zero_cost_local_normal_user_execution": True,
                    "authorized_clay_direct_dev_vps_sandbox_execution": True,
                    "external_provider_admission_file": mod.CANONICAL_PROVIDER_ADMISSION,
                    "external_llm_provider_execution": "QUARANTINED_UNTIL_FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT_V1_EXACT_SOURCE_PASS",
                    "together_general_inference_and_fallback_forbidden": True,
                    "other_paid_fallback": False,
                },
                "runtime_credit": {
                    "entityos_hcu_whole_runtime_credit": 0,
                    "hcu_full_runtime_credit": 0,
                    "jspace_model_runtime_credit": 0,
                    "training_credit": 0,
                    "whole_product_pass": False,
                },
            },
        )
        put_json(
            authority,
            {
                "schema_version": version,
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
            },
        )
        put_json(
            mod.CANONICAL_PROVIDER_ADMISSION,
            {
                "schema": "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1",
                "authority_epoch": version,
                "mode": "FREE_ONLY",
                "product": mod.CURRENT_PRODUCT,
                "compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "source": "ENTITYOS_HCU_CONTROL_PLANE",
                "providers": {
                    name: {"admitted": False, "cost_class": "UNKNOWN"}
                    for name in ["groq", "mistral", "nvidia", "openrouter"]
                },
                "runtime_provider_credit": 0,
                "execution_state": "EXTERNAL_LLM_PROVIDER_TRAFFIC_QUARANTINED_UNTIL_EXECUTABLE_TYPED_FREE_ADMISSION_PASS",
            },
        )
        put_text(
            "CLAUDE.md",
            f"AUTONOMOUS_SUPERVISOR=SUPERVISOR_STEERING_{suffix}\n"
            f"SUPERVISOR_STEERING_{suffix}.json\n"
            f"CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE_{suffix}.md\n"
            "clay-direct-dev\nprovider traffic QUARANTINED\n",
        )

        put_json(
            mod.CONTROL41,
            {
                "schema_version": "4.1",
                "mode": "FREE_ONLY",
                "cycle_policy": {"paid_fallback": False},
                "authority_rules": ["model_output_is_candidate_not_truth"],
            },
        )
        put_json(
            mod.CONTROL42,
            {
                "schema_version": "4.2-execution-boundary-addendum",
                "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True},
            },
        )
        put_json(
            mod.CONTROL43,
            {
                "schema_version": "4.3-program-authority-addendum",
                "preserved_hard_rules": {
                    "free_only": True,
                    "paid_fallback": False,
                    "model_output_is_candidate_not_truth": True,
                },
            },
        )
        put_json(
            mod.CONTROL44,
            {
                "schema_version": "4.4-clayverse-product-authority-addendum",
                "program_identity_override": {"product_endpoint": "ClayVerse"},
                "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True},
            },
        )
        return td, root, authority

    def load(self, root, rel):
        return json.loads((root / rel).read_text(encoding="utf-8"))

    def save(self, root, rel, obj):
        (root / rel).write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")

    def assert_error(self, result, code):
        self.assertFalse(result["pass"], result)
        self.assertTrue(any(err == code or err.startswith(code) for err in result["errors"]), result)

    def test_current_868_pointer_consensus_passes(self):
        td, root, authority = self.make_tree()
        self.addCleanup(td.cleanup)
        result = mod.validate(root)
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["resolved_authority"], authority)
        self.assertEqual(result["resolved_authority_epoch"], "8.68")

    def test_successor_869_requires_no_code_constant_bump(self):
        td, root, authority = self.make_tree("8.69")
        self.addCleanup(td.cleanup)
        result = mod.validate(root)
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["resolved_authority_epoch"], "8.69")

    def test_manifest_pointer_lag_fails_split_brain(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        data = self.load(root, "the artefact/manifest.json")
        data["authority_correction"] = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_65.json"
        self.save(root, "the artefact/manifest.json", data)
        self.assert_error(mod.validate(root), "AUTHORITY_POINTER_SPLIT_BRAIN")

    def test_traversal_or_malformed_pointer_fails_closed(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        data = self.load(root, "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
        data["steering"] = "research_entity/claycode/autonomous/../SUPERVISOR_STEERING_8_68.json"
        self.save(root, "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json", data)
        self.assert_error(mod.validate(root), "AUTHORITY_POINTER_INVALID:inbox")

    def test_provider_epoch_mismatch_fails_closed(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        data = self.load(root, mod.CANONICAL_PROVIDER_ADMISSION)
        data["authority_epoch"] = "8.67"
        self.save(root, mod.CANONICAL_PROVIDER_ADMISSION, data)
        self.assert_error(mod.validate(root), "PROVIDER_ADMISSION_EPOCH_MISMATCH")

    def test_provider_self_grant_while_quarantined_fails(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        data = self.load(root, mod.CANONICAL_PROVIDER_ADMISSION)
        data["providers"]["groq"] = {"admitted": True, "cost_class": "FREE"}
        self.save(root, mod.CANONICAL_PROVIDER_ADMISSION, data)
        self.assert_error(mod.validate(root), "PROVIDER_SELF_GRANT_WHILE_QUARANTINED:groq")

    def test_reintroducing_old_blanket_vps_prohibition_is_detected(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        data = self.load(root, "research_entity/rooms/PROGRAM_STATE.json")
        data["execution_policy"]["authorized_clay_direct_dev_vps_sandbox_execution"] = False
        self.save(root, "research_entity/rooms/PROGRAM_STATE.json", data)
        self.assert_error(mod.validate(root), "PROGRAM_CLAY_DIRECT_DEV_EXECUTION_DRIFT")

    def test_provider_admission_path_cannot_be_substituted(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        data = self.load(root, "the artefact/manifest.json")
        data["execution_policy"]["external_provider_admission_file"] = "scratch/forged_free.json"
        self.save(root, "the artefact/manifest.json", data)
        self.assert_error(mod.validate(root), "MANIFEST_PROVIDER_ADMISSION_PATH_DRIFT")

    def test_runtime_credit_inflation_fails(self):
        td, root, _ = self.make_tree()
        self.addCleanup(td.cleanup)
        data = self.load(root, "research_entity/rooms/PROGRAM_STATE.json")
        data["runtime_credit"]["jspace_model_runtime_credit"] = 1
        self.save(root, "research_entity/rooms/PROGRAM_STATE.json", data)
        self.assert_error(mod.validate(root), "PROGRAM_JSPACE_RUNTIME_CREDIT_NONZERO")


if __name__ == "__main__":
    unittest.main()
