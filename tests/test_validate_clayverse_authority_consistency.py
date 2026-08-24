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

AUTHORITY = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_68.json"


class AuthorityConsistencyV4Tests(unittest.TestCase):
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
                "authority_correction": AUTHORITY,
                "mandatory_invariants": [
                    "EntityOS is the sole current product/system identity",
                    "HCU is the sole current integrated cognition/compute architecture",
                    "FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT",
                ],
                "free_only": True,
                "paid_fallback": "FORBIDDEN",
                "together_api": "FORBIDDEN_IN_CURRENT_FREE_ONLY_SUPERVISOR_MODE",
                "effect_authority": "EffectGate+EffectJournal",
                "execution_surface": "FREE_ONLY; ZERO_COST_LOCAL_NORMAL_USER_AND_CLAY_DIRECT_DEV_VPS_SANDBOX_ALLOWED; EXTERNAL_LLM_PROVIDER_TRAFFIC_QUARANTINED_UNTIL_EXECUTABLE_TYPED_FREE_ADMISSION_PASS; PAID_SUBSCRIPTION_UNKNOWN_COST FAIL_CLOSED",
            },
            "research_entity/rooms/PROGRAM_STATE.json": {
                "schema_version": "8.68",
                "program_id": "entityos-hcu",
                "status": "ACTIVE",
                "stage": mod.CURRENT_STAGE,
                "current_stage": mod.CURRENT_STAGE,
                "product": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "authority_correction": AUTHORITY,
                "identity": {
                    "persistent_research_entity": "Clay",
                    "temporary_workers": "ORGANS_NOT_ENTITIES",
                },
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
                    "current_provider_runtime_credit": 0,
                    "current_provider_runtime_inventory": "HISTORICAL_UNADMITTED_EXTERNAL_PROVIDER_TRAFFIC_OBSERVED; ALL_CURRENT_EXTERNAL_LLM_PROVIDER_TRAFFIC_QUARANTINED_PER_SUPERVISOR_8_68",
                },
                "runtime_credit": {
                    "free_swarm_provider_admission_runtime_credit": 0,
                    "external_provider_worker_runtime_credit": 0,
                    "entityos_hcu_whole_runtime_credit": 0,
                    "hcu_full_runtime_credit": 0,
                    "jspace_model_runtime_credit": 0,
                    "training_credit": 0,
                    "whole_product_pass": False,
                },
            },
            "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json": {
                "schema_version": "8.68",
                "steering": AUTHORITY,
            },
            AUTHORITY: {
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
            },
            "the artefact/manifest.json": {
                "schema": "ENTITYOS_HCU_ARTIFACT_MANIFEST/v2",
                "artifact": mod.CURRENT_PRODUCT,
                "product_endpoint": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "stage": mod.CURRENT_STAGE,
                "canonical_workspace": "the artefact/",
                "authority_correction": AUTHORITY,
                "effect_authority": "EffectGate+EffectJournal",
                "legacy_donor": {
                    "prior_product": "ClayVerse",
                    "scope": "HISTORICAL_DONOR_PROVENANCE_ONLY",
                },
                "execution_policy": {
                    "free_only_default": True,
                    "active_supervisor_free_only": True,
                    "authorized_zero_cost_local_normal_user_execution": True,
                    "authorized_clay_direct_dev_vps_sandbox_execution": True,
                    "external_llm_provider_execution": "QUARANTINED_UNTIL_FREE_SWARM_ADMISSION_BOUNDARY_RECEIPT_V1_EXACT_SOURCE_PASS",
                    "together_general_inference_and_fallback_forbidden": True,
                    "other_paid_fallback": False,
                },
                "runtime_credit": {
                    "free_swarm_provider_admission_runtime_credit": 0,
                    "external_provider_worker_runtime_credit": 0,
                    "entityos_hcu_whole_runtime_credit": 0,
                    "hcu_full_runtime_credit": 0,
                    "jspace_model_runtime_credit": 0,
                    "training_credit": 0,
                    "whole_product_pass": False,
                },
            },
            mod.CONTROL41: {
                "schema_version": "4.1",
                "status": "ACTIVE",
                "mode": "FREE_ONLY",
                "cycle_policy": {
                    "paid_fallback": False,
                    "automatic_subscription_upgrade": False,
                    "vps_testing": "FORBIDDEN",
                },
                "authority_rules": [
                    "model_output_is_candidate_not_truth",
                    "autonomous_cycle_may_not_modify_FRANK_harness",
                ],
            },
            mod.CONTROL42: {
                "schema_version": "4.2-execution-boundary-addendum",
                "status": "ACTIVE",
                "mode": "FREE_ONLY",
                "base_control_path": mod.CONTROL41,
                "base_control_blob_sha": "pending",
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
            },
            mod.CONTROL43: {
                "schema_version": "4.3-program-authority-addendum",
                "status": "ACTIVE",
                "mode": "FREE_ONLY",
                "base_control_path": mod.CONTROL41,
                "base_control_blob_sha": "pending",
                "execution_boundary_addendum_path": mod.CONTROL42,
                "execution_boundary_addendum_blob_sha": "pending",
                "preserved_hard_rules": {
                    "free_only": True,
                    "paid_fallback": False,
                    "together_forbidden_under_current_control": True,
                    "model_output_is_candidate_not_truth": True,
                    "runtime_credit_requires_exact_admitted_execution": True,
                    "frank_harness_modification": "FORBIDDEN",
                },
            },
            mod.CONTROL44: {
                "schema_version": "4.4-clayverse-product-authority-addendum",
                "status": "ACTIVE",
                "mode": "FREE_ONLY",
                "base_control_path": mod.CONTROL41,
                "execution_boundary_addendum_path": mod.CONTROL42,
                "prior_program_authority_addendum_path": mod.CONTROL43,
                "prior_program_authority_addendum_blob_sha": "pending",
                "composition_order": [
                    "4.1",
                    "4.2-execution-boundary-addendum",
                    "4.3-program-authority-addendum",
                    "4.4-clayverse-product-authority-addendum",
                ],
                "effective_control_version": mod.LEGACY_EXPECTED_CONTROL,
                "program_identity_override": {
                    "active_program": "CLAYVERSE_SINGLE_CONTAINER",
                    "target_stage": "CLAYVERSE_ARTIFACT",
                    "product_endpoint": "ClayVerse",
                },
                "preserved_hard_rules": {
                    "free_only": True,
                    "paid_fallback": False,
                    "together_forbidden": True,
                    "vps_testing": False,
                    "runtime_credit_requires_exact_admitted_isolated_execution": True,
                    "model_output_is_candidate_not_truth": True,
                    "frank_harness_modification": "FORBIDDEN",
                },
            },
        }
        text = {
            "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md": (
                "Program: EntityOS + HCU\n"
                "Stage: ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP\n"
                "Product: EntityOS\n"
                "Compute architecture: HCU\n"
            ),
            "the artefact/ARCHITECTURE.md": (
                "# EntityOS + HCU architecture\n"
                "EntityOS is the sole current product/system. HCU is the integrated cognition/compute architecture.\n"
            ),
            "the artefact/README.md": "# the artefact — EntityOS + HCU\n",
            mod.ROOT_CLAUDE: (
                "# CLAY — CURRENT ENTITYOS / HCU REPO ORGAN\n"
                "`PROGRAM=ENTITYOS_HCU`\n"
                "`STAGE=ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP`\n"
                "`PRODUCT=EntityOS`\n"
                "`COMPUTE_ARCHITECTURE=HCU`\n"
                "`AUTONOMOUS_SUPERVISOR=RESOLVE_FROM_SUPERVISOR_INBOX`\n"
                "Read research_entity/claycode/autonomous/SUPERVISOR_INBOX.json and resolve its steering pointer.\n"
            ),
        }
        for rel, data in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        for rel, data in text.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data, encoding="utf-8")

        c42p = root / mod.CONTROL42
        c42 = json.loads(c42p.read_text())
        c42["base_control_blob_sha"] = mod.git_blob_sha(root / mod.CONTROL41)
        c42p.write_text(json.dumps(c42, sort_keys=True))
        c43p = root / mod.CONTROL43
        c43 = json.loads(c43p.read_text())
        c43["base_control_blob_sha"] = mod.git_blob_sha(root / mod.CONTROL41)
        c43["execution_boundary_addendum_blob_sha"] = mod.git_blob_sha(c42p)
        c43p.write_text(json.dumps(c43, sort_keys=True))
        c44p = root / mod.CONTROL44
        c44 = json.loads(c44p.read_text())
        c44["prior_program_authority_addendum_blob_sha"] = mod.git_blob_sha(c43p)
        c44p.write_text(json.dumps(c44, sort_keys=True))
        return td, root

    def result(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        return root, mod.validate(root)

    def test_current_successor_dynamic_authority_passes(self):
        _, result = self.result()
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["resolved_authority"], AUTHORITY)
        self.assertEqual(result["resolved_authority_schema"], "8.68")

    def test_pointer_split_brain_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "the artefact/manifest.json"
        data = json.loads(path.read_text()); data["authority_correction"] = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_67.json"
        path.write_text(json.dumps(data))
        self.assertIn("AUTHORITY_POINTER_SPLIT_BRAIN", mod.validate(root)["errors"])

    def test_pointer_path_traversal_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
        data = json.loads(path.read_text()); data["steering"] = "../SUPERVISOR_STEERING_8_68.json"
        path.write_text(json.dumps(data))
        self.assertIn("AUTHORITY_POINTER_INVALID:inbox", mod.validate(root)["errors"])

    def test_filename_schema_mismatch_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / AUTHORITY
        data = json.loads(path.read_text()); data["schema_version"] = "8.67"
        path.write_text(json.dumps(data))
        self.assertIn("AUTHORITY_FILENAME_SCHEMA_MISMATCH", mod.validate(root)["errors"])

    def test_provider_quarantine_cannot_disappear(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / AUTHORITY
        data = json.loads(path.read_text()); data["free_only"]["external_llm_provider_execution"] = "ENABLED"
        path.write_text(json.dumps(data))
        self.assertIn("SUPERVISOR_PROVIDER_QUARANTINE_MISSING", mod.validate(root)["errors"])

    def test_together_cannot_reenable(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / AUTHORITY
        data = json.loads(path.read_text()); data["free_only"]["together_forbidden"] = False
        path.write_text(json.dumps(data))
        self.assertIn("SUPERVISOR_TOGETHER_FENCE_MISSING", mod.validate(root)["errors"])

    def test_program_provider_credit_cannot_self_promote(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        data = json.loads(path.read_text()); data["execution_policy"]["current_provider_runtime_credit"] = 1
        path.write_text(json.dumps(data))
        self.assertIn("PROGRAM_PROVIDER_RUNTIME_CREDIT_NONZERO", mod.validate(root)["errors"])

    def test_whole_runtime_credit_cannot_self_promote(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "the artefact/manifest.json"
        data = json.loads(path.read_text()); data["runtime_credit"]["entityos_hcu_whole_runtime_credit"] = 1
        path.write_text(json.dumps(data))
        self.assertIn("MANIFEST_RUNTIME_CREDIT_NONZERO", mod.validate(root)["errors"])

    def test_root_fixed_minor_pin_is_forbidden(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.ROOT_CLAUDE
        path.write_text(
            "`PROGRAM=ENTITYOS_HCU`\n"
            "`STAGE=ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP`\n"
            "`PRODUCT=EntityOS`\n"
            "`COMPUTE_ARCHITECTURE=HCU`\n"
            "AUTONOMOUS_SUPERVISOR=SUPERVISOR_STEERING_8_68\n"
            "SUPERVISOR_INBOX.json resolve steering\n"
        )
        self.assertIn("ROOT_CLAUDE_FIXED_SUPERVISOR_PIN_FORBIDDEN", mod.validate(root)["errors"])

    def test_legacy_paid_fallback_weakening_still_fails(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.CONTROL41
        data = json.loads(path.read_text()); data["cycle_policy"]["paid_fallback"] = True
        path.write_text(json.dumps(data, sort_keys=True))
        errors = mod.validate(root)["errors"]
        self.assertIn("CONTROL41_PAID_FALLBACK_WEAKENED", errors)
        self.assertIn("CONTROL42_BASE_BLOB_MISMATCH", errors)
        self.assertIn("CONTROL43_BASE_BLOB_MISMATCH", errors)

    def test_legacy_direct_vps_boundary_weakening_still_fails(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.CONTROL42
        data = json.loads(path.read_text()); data["execution_routing"]["direct_vps_host_candidate_execution"] = "ALLOWED"
        path.write_text(json.dumps(data, sort_keys=True))
        errors = mod.validate(root)["errors"]
        self.assertIn("CONTROL42_DIRECT_VPS_FENCE_WEAKENED", errors)
        self.assertIn("CONTROL43_EXEC_BLOB_MISMATCH", errors)

    def test_legacy_frank_harness_fence_still_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.CONTROL44
        data = json.loads(path.read_text()); data["preserved_hard_rules"]["frank_harness_modification"] = "ALLOWED"
        path.write_text(json.dumps(data, sort_keys=True))
        self.assertIn("CONTROL44_FRANK_HARNESS_FENCE_WEAKENED", mod.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
