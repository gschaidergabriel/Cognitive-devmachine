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
                "entity_display_name": "Clay",
                "identity": {
                    "persistent_research_entity": "Clay",
                    "temporary_worker": "ORGAN_NOT_ENTITY",
                },
                "active_program": mod.EXPECTED_PROGRAM,
                "active_stage": mod.EXPECTED_STAGE,
                "product_endpoint": mod.EXPECTED_PRODUCT,
                "integrated_cognition_compute_architecture": mod.EXPECTED_COMPUTE,
                "authority_correction": mod.STEERING852,
                "canonical_repository": mod.EXPECTED_REPO,
                "canonical_branch": "main",
                "canonical_workspace": mod.EXPECTED_WORKSPACE,
                "execution_surface": "AUTHORIZED_ISOLATED_SANDBOX_ONLY",
                "together_api": "FORBIDDEN",
                "paid_fallback": "FORBIDDEN",
                "final_paid_model_training": "OWNER_AUTHORIZATION_REQUIRED",
                "go_required_tracks": [
                    mod.EXPECTED_GO_TRACK,
                    "HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT_OR_HCU_NO_CHANGE_WITH_REASON",
                ],
                "compatibility_names": {
                    "xeno": "TRANSITIONAL_IMPLEMENTATION_COMPATIBILITY_CODENAME_ONLY",
                    "xcu": "TRANSITIONAL_RESEARCH_ALIAS_FOR_HCU_ONLY",
                    "clayverse_frank": "HISTORICAL_DONOR_PROVENANCE_ONLY",
                },
            },
            "research_entity/rooms/PROGRAM_STATE.json": {
                "program_id": "entityos-hcu",
                "stage": mod.EXPECTED_STAGE,
                "current_stage": mod.EXPECTED_STAGE,
                "product": mod.EXPECTED_PRODUCT,
                "integrated_cognition_compute_architecture": mod.EXPECTED_COMPUTE,
                "canonical_repository": mod.EXPECTED_REPO,
                "canonical_branch": "main",
                "canonical_workspace": mod.EXPECTED_WORKSPACE,
                "go_required_tracks": {
                    "track_a": mod.EXPECTED_GO_TRACK,
                    "track_b": mod.EXPECTED_ENTRY_TRACK,
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
            },
            mod.STEERING852: {
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
            },
            "the artefact/manifest.json": {
                "schema_version": "ENTITYOS_HCU_MANIFEST/v1",
                "artifact": mod.EXPECTED_PRODUCT,
                "product_endpoint": mod.EXPECTED_PRODUCT,
                "program": mod.EXPECTED_PROGRAM,
                "stage": mod.EXPECTED_STAGE,
                "integrated_cognition_compute_architecture": mod.EXPECTED_COMPUTE,
                "canonical_repository": mod.EXPECTED_REPO,
                "canonical_branch": "main",
                "canonical_workspace": mod.EXPECTED_WORKSPACE,
                "authority": {
                    "external_effects": "EffectGate+EffectJournal",
                    "second_truth_effect_or_recovery_authority": "FORBIDDEN",
                },
                "execution_policy": {
                    "free_only": True,
                    "authorized_isolated_sandbox_only_for_current_runtime_credit": True,
                    "vps_testing_forbidden": True,
                    "self_hosted_vps_test_runners_forbidden": True,
                    "production_host_testing_forbidden": True,
                    "together_forbidden": True,
                    "paid_fallback": False,
                },
                "legacy_manifest_provenance": {
                    "prior_manifest_git_blob_sha1": mod.LEGACY_MANIFEST_BLOB,
                    "classification": "HISTORICAL_DONOR_PROVENANCE_ONLY",
                },
                "acceptance": {
                    "entityos_hcu_whole_runtime_credit": 0,
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
                "authority_rules": ["model_output_is_candidate_not_truth"],
            },
            mod.CONTROL42: {
                "schema_version": "4.2-execution-boundary-addendum",
                "base_control_path": mod.CONTROL41,
                "base_control_blob_sha": "pending",
                "preserved_hard_rules": {
                    "free_only": True,
                    "paid_fallback": False,
                    "together_forbidden": True,
                },
                "execution_routing": {
                    "direct_vps_host_candidate_execution": "FORBIDDEN",
                    "persistent_self_hosted_candidate_execution": "FORBIDDEN",
                    "production_host_testing": "FORBIDDEN",
                },
            },
            mod.CONTROL43: {
                "schema_version": "4.3-program-authority-addendum",
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
                },
            },
            mod.CONTROL44: {
                "schema_version": "4.4-clayverse-product-authority-addendum",
                "prior_program_authority_addendum_path": mod.CONTROL43,
                "prior_program_authority_addendum_blob_sha": "pending",
                "preserved_hard_rules": {
                    "free_only": True,
                    "paid_fallback": False,
                    "together_forbidden": True,
                    "vps_testing": False,
                    "runtime_credit_requires_exact_admitted_isolated_execution": True,
                    "model_output_is_candidate_not_truth": True,
                },
            },
        }
        text = {
            mod.WORKER_DIRECTIVE: (
                "Current product/system: **EntityOS**\n"
                "Current integrated cognition/compute architecture: **HCU**\n"
                + mod.EXPECTED_GO_TRACK + "\n" + mod.EXPECTED_ENTRY_TRACK + "\n"
            ),
            "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md": (
                "Program: EntityOS + HCU\n"
                "Stage: ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP\n"
                "Product: EntityOS\n"
                "Compute architecture: HCU\n"
            ),
            "the artefact/README.md": (
                "# the artefact — EntityOS + HCU cognitive computer\n"
                "- **EntityOS** = sole current product/system identity.\n"
                "- **HCU** = sole current integrated cognition/compute architecture.\n"
            ),
            "CLAUDE.md": (
                "PROGRAM=ENTITYOS_HCU\n"
                "PRODUCT=EntityOS\n"
                "COMPUTE_ARCHITECTURE=HCU\n"
                "ClayVerse and Frank = historical donor/provenance only\n"
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

        c42 = root / mod.CONTROL42
        d42 = json.loads(c42.read_text(encoding="utf-8"))
        d42["base_control_blob_sha"] = mod.git_blob_sha(root / mod.CONTROL41)
        c42.write_text(json.dumps(d42, sort_keys=True), encoding="utf-8")

        c43 = root / mod.CONTROL43
        d43 = json.loads(c43.read_text(encoding="utf-8"))
        d43["base_control_blob_sha"] = mod.git_blob_sha(root / mod.CONTROL41)
        d43["execution_boundary_addendum_blob_sha"] = mod.git_blob_sha(c42)
        c43.write_text(json.dumps(d43, sort_keys=True), encoding="utf-8")

        c44 = root / mod.CONTROL44
        d44 = json.loads(c44.read_text(encoding="utf-8"))
        d44["prior_program_authority_addendum_blob_sha"] = mod.git_blob_sha(c43)
        c44.write_text(json.dumps(d44, sort_keys=True), encoding="utf-8")
        return td, root

    def test_coherent_entityos_hcu_authority_passes(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        self.assertTrue(mod.validate(root)["pass"])

    def test_clayverse_product_regression_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "the artefact/manifest.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["product_endpoint"] = "ClayVerse"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("MANIFEST_PRODUCT_MISMATCH", mod.validate(root)["errors"])

    def test_xeno_product_regression_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["product_endpoint"] = "Xeno"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("BOOTSTRAP_PRODUCT_MISMATCH", mod.validate(root)["errors"])

    def test_second_compute_architecture_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["integrated_cognition_compute_architecture"] = "XCU"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("PROGRAM_COMPUTE_ARCHITECTURE_MISMATCH", mod.validate(root)["errors"])

    def test_paid_fallback_weakening_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.CONTROL41
        data = json.loads(path.read_text(encoding="utf-8"))
        data["cycle_policy"]["paid_fallback"] = True
        path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        errors = mod.validate(root)["errors"]
        self.assertIn("CONTROL41_PAID_FALLBACK_WEAKENED", errors)
        self.assertIn("CONTROL42_BASE_BLOB_MISMATCH", errors)
        self.assertIn("CONTROL43_BASE_BLOB_MISMATCH", errors)

    def test_together_weakening_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.CONTROL42
        data = json.loads(path.read_text(encoding="utf-8"))
        data["preserved_hard_rules"]["together_forbidden"] = False
        path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        errors = mod.validate(root)["errors"]
        self.assertIn("CONTROL42_TOGETHER_FENCE_WEAKENED", errors)
        self.assertIn("CONTROL43_EXEC_BLOB_MISMATCH", errors)

    def test_control43_mutation_breaks_control44_ancestry(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.CONTROL43
        data = json.loads(path.read_text(encoding="utf-8"))
        data["tamper"] = True
        path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        self.assertIn("CONTROL44_PRIOR_BLOB_MISMATCH", mod.validate(root)["errors"])

    def test_legacy_manifest_provenance_is_pinned(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "the artefact/manifest.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["legacy_manifest_provenance"]["prior_manifest_git_blob_sha1"] = "0" * 40
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("MANIFEST_LEGACY_BLOB_PROVENANCE_MISMATCH", mod.validate(root)["errors"])

    def test_runtime_credit_inflation_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "the artefact/manifest.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["acceptance"]["entityos_hcu_whole_runtime_credit"] = 1
        data["acceptance"]["whole_product_pass"] = True
        path.write_text(json.dumps(data), encoding="utf-8")
        errors = mod.validate(root)["errors"]
        self.assertIn("MANIFEST_RUNTIME_CREDIT_NONZERO", errors)
        self.assertIn("MANIFEST_WHOLE_PRODUCT_PASS_UNJUSTIFIED", errors)


if __name__ == "__main__":
    unittest.main()
