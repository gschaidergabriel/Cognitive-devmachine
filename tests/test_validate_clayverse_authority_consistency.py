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
            "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json": {
                "entity_id": "entity",
            },
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json": {
                "entity_id": "entity",
                "identity": {
                    "persistent_research_entity": "Clay",
                    "temporary_worker": "ORGAN_NOT_ENTITY",
                },
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
                "together_api": "FORBIDDEN",
                "paid_fallback": "FORBIDDEN",
                "final_paid_model_training": "OWNER_AUTHORIZATION_REQUIRED",
                "effect_authority": "EffectGate+EffectJournal",
            },
            "research_entity/rooms/PROGRAM_STATE.json": {
                "program_id": "entityos-hcu",
                "status": "ACTIVE",
                "stage": mod.CURRENT_STAGE,
                "current_stage": mod.CURRENT_STAGE,
                "product": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
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
                    "isolated_sandbox_only": True,
                    "vps_testing_forbidden": True,
                    "self_hosted_vps_test_runners_forbidden": True,
                    "production_host_testing_forbidden": True,
                    "together_forbidden": True,
                    "paid_fallback": False,
                },
                "go_required_tracks": {
                    "track_a": "ENTITYOS_EXECUTABLE_CONVERGENCE",
                    "track_b": "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT",
                },
                "runtime_credit": {
                    "entityos_hcu_whole_runtime_credit": 0,
                    "whole_product_pass": False,
                },
            },
            mod.CURRENT_AUTHORITY: {
                "schema_version": "8.52",
                "status": "CURRENT_OWNER_AUTHORITY_CORRECTION",
                "program": mod.CURRENT_PROGRAM,
                "product": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "adjudication": {
                    "entityos": "SOLE_CURRENT_PRODUCT_SYSTEM_IDENTITY",
                    "hcu": "SOLE_CURRENT_INTEGRATED_COGNITION_COMPUTE_ARCHITECTURE",
                    "clayverse": "HISTORICAL_DONOR_PROVENANCE_ONLY",
                },
                "routing_law": [
                    "FREE_ONLY_REMAINS_FAIL_CLOSED_WITH_NO_PAID_FALLBACK",
                    "EXECUTABLE_EVIDENCE_OUTRANKS_MODEL_CONSENSUS",
                ],
                "current_runtime_evidence": {
                    "entityos_hcu_whole_runtime_credit": 0,
                    "whole_product_pass": False,
                },
            },
            "the artefact/manifest.json": {
                "schema": "ENTITYOS_HCU_ARTIFACT_MANIFEST/v1",
                "artifact": mod.CURRENT_PRODUCT,
                "product_endpoint": mod.CURRENT_PRODUCT,
                "integrated_cognition_compute_architecture": mod.CURRENT_COMPUTE_ARCHITECTURE,
                "stage": mod.CURRENT_STAGE,
                "canonical_workspace": "the artefact/",
                "authority_correction": mod.CURRENT_AUTHORITY,
                "effect_authority": "EffectGate+EffectJournal",
                "execution_policy": {
                    "free_only": True,
                    "isolated_sandbox_only": True,
                    "vps_testing_forbidden": True,
                    "together_forbidden": True,
                    "paid_fallback": False,
                },
                "runtime_credit": {
                    "entityos_hcu_whole_runtime_credit": 0,
                    "whole_product_pass": False,
                },
                "legacy_donor": {
                    "prior_product": "ClayVerse",
                    "scope": "HISTORICAL_DONOR_PROVENANCE_ONLY",
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
                    "release_form": "ONE_OCI_DOCKER_COMPATIBLE_CONTAINER_IMAGE",
                },
                "preserved_hard_rules": {
                    "free_only": True,
                    "paid_fallback": False,
                    "together_forbidden": True,
                    "vps_testing": False,
                    "runtime_credit_requires_exact_admitted_isolated_execution": True,
                    "model_output_is_candidate_not_truth": True,
                    "frank_harness_modification": "FORBIDDEN",
                    "legacy_mini_entity_swarm_controller": "FORBIDDEN_UNTIL_CLAYVERSE_PROMPT_AND_AUTHORITY_MIGRATION",
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
            "the artefact/README.md": "# the artefact — EntityOS + HCU cognitive computer\n",
            mod.ROOT_CLAUDE: (
                "# CLAY — CURRENT ENTITYOS / HCU REPO ORGAN\n"
                "`PROGRAM=ENTITYOS_HCU`\n"
                "`STAGE=ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP`\n"
                "`PRODUCT=EntityOS`\n"
                "`COMPUTE_ARCHITECTURE=HCU`\n"
                "Read research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json.\n"
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

        control42_path = root / mod.CONTROL42
        control42 = json.loads(control42_path.read_text(encoding="utf-8"))
        control42["base_control_blob_sha"] = mod.git_blob_sha(root / mod.CONTROL41)
        control42_path.write_text(json.dumps(control42, sort_keys=True), encoding="utf-8")

        control43_path = root / mod.CONTROL43
        control43 = json.loads(control43_path.read_text(encoding="utf-8"))
        control43["base_control_blob_sha"] = mod.git_blob_sha(root / mod.CONTROL41)
        control43["execution_boundary_addendum_blob_sha"] = mod.git_blob_sha(control42_path)
        control43_path.write_text(json.dumps(control43, sort_keys=True), encoding="utf-8")

        control44_path = root / mod.CONTROL44
        control44 = json.loads(control44_path.read_text(encoding="utf-8"))
        control44["prior_program_authority_addendum_blob_sha"] = mod.git_blob_sha(control43_path)
        control44_path.write_text(json.dumps(control44, sort_keys=True), encoding="utf-8")
        return td, root

    def test_coherent_entityos_hcu_authority_passes(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        result = mod.validate(root)
        self.assertTrue(result["pass"], result["errors"])

    def test_clayverse_bootstrap_regression_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
        data = json.loads(path.read_text()); data["active_program"] = "CLAYVERSE_SINGLE_CONTAINER"
        path.write_text(json.dumps(data))
        self.assertIn("BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH", mod.validate(root)["errors"])

    def test_hcu_architecture_regression_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        data = json.loads(path.read_text()); data["integrated_cognition_compute_architecture"] = "XCU"
        path.write_text(json.dumps(data))
        self.assertIn("PROGRAM_COMPUTE_ARCHITECTURE_MISMATCH", mod.validate(root)["errors"])

    def test_manifest_cannot_reactivate_clayverse(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "the artefact/manifest.json"
        data = json.loads(path.read_text()); data["artifact"] = "ClayVerse"; data["product_endpoint"] = "ClayVerse"
        path.write_text(json.dumps(data))
        errors = mod.validate(root)["errors"]
        self.assertIn("MANIFEST_ARTIFACT_MISMATCH", errors)
        self.assertIn("MANIFEST_PRODUCT_ENDPOINT_MISMATCH", errors)

    def test_steering852_free_only_fence_is_required(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.CURRENT_AUTHORITY
        data = json.loads(path.read_text()); data["routing_law"] = ["EXECUTABLE_EVIDENCE_OUTRANKS_MODEL_CONSENSUS"]
        path.write_text(json.dumps(data))
        self.assertIn("STEERING852_FREE_ONLY_FENCE_MISSING", mod.validate(root)["errors"])

    def test_program_paid_fallback_weakening_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        data = json.loads(path.read_text()); data["execution_policy"]["paid_fallback"] = True
        path.write_text(json.dumps(data))
        self.assertIn("PROGRAM_PAID_FALLBACK_WEAKENED", mod.validate(root)["errors"])

    def test_program_effect_authority_weakening_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        data = json.loads(path.read_text()); data["authority"]["external_effects"] = "HCU"
        path.write_text(json.dumps(data))
        self.assertIn("PROGRAM_EFFECT_AUTHORITY_MISMATCH", mod.validate(root)["errors"])

    def test_program_runtime_credit_cannot_self_promote(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        data = json.loads(path.read_text()); data["runtime_credit"]["entityos_hcu_whole_runtime_credit"] = 1
        path.write_text(json.dumps(data))
        self.assertIn("PROGRAM_RUNTIME_CREDIT_NONZERO", mod.validate(root)["errors"])

    def test_control41_paid_fallback_mutation_breaks_ancestry(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.CONTROL41
        data = json.loads(path.read_text()); data["cycle_policy"]["paid_fallback"] = True
        path.write_text(json.dumps(data, sort_keys=True))
        errors = mod.validate(root)["errors"]
        self.assertIn("CONTROL41_PAID_FALLBACK_WEAKENED", errors)
        self.assertIn("CONTROL42_BASE_BLOB_MISMATCH", errors)
        self.assertIn("CONTROL43_BASE_BLOB_MISMATCH", errors)

    def test_control42_together_mutation_breaks_ancestry(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.CONTROL42
        data = json.loads(path.read_text()); data["preserved_hard_rules"]["together_forbidden"] = False
        path.write_text(json.dumps(data, sort_keys=True))
        errors = mod.validate(root)["errors"]
        self.assertIn("CONTROL42_TOGETHER_FENCE_WEAKENED", errors)
        self.assertIn("CONTROL43_EXEC_BLOB_MISMATCH", errors)

    def test_control43_mutation_breaks_control44_blob_ancestry(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.CONTROL43
        data = json.loads(path.read_text()); data["tampered"] = True
        path.write_text(json.dumps(data, sort_keys=True))
        self.assertIn("CONTROL44_PRIOR_BLOB_MISMATCH", mod.validate(root)["errors"])

    def test_control44_safety_weakening_still_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.CONTROL44
        data = json.loads(path.read_text()); data["preserved_hard_rules"]["free_only"] = False
        path.write_text(json.dumps(data))
        self.assertIn("CONTROL44_FREE_ONLY_WEAKENED", mod.validate(root)["errors"])

    def test_control44_historical_product_bytes_remain_provenance_bound(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.CONTROL44
        data = json.loads(path.read_text()); data["program_identity_override"]["product_endpoint"] = "EntityOS"
        path.write_text(json.dumps(data))
        self.assertIn("CONTROL44_HISTORICAL_PRODUCT_ANCESTRY_MISMATCH", mod.validate(root)["errors"])

    def test_root_claude_stale_clayverse_program_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.ROOT_CLAUDE
        path.write_text(
            "`PROGRAM=CLAYVERSE_SINGLE_CONTAINER`\n"
            "`STAGE=ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP`\n"
            "`PRODUCT=EntityOS`\n"
            "`COMPUTE_ARCHITECTURE=HCU`\n"
            "SUPERVISOR_STEERING_8_52.json\n"
        )
        errors = mod.validate(root)["errors"]
        self.assertIn("ROOT_CLAUDE_PROGRAM_MISMATCH", errors)
        self.assertIn("ROOT_CLAUDE_STALE_CLAYVERSE_PROGRAM_ACTIVE", errors)

    def test_architecture_stale_clayverse_product_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / "the artefact/ARCHITECTURE.md"
        path.write_text("# EntityOS HCU\nClayVerse is the product endpoint.\n")
        self.assertIn("ARCHITECTURE_STALE_CLAYVERSE_PRODUCT_AUTHORITY", mod.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
