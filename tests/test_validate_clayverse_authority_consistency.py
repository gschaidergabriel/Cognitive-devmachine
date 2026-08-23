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
                "entity_version": "V1",
                "revision": 2,
                "state_hash": "state",
            },
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json": {
                "entity_id": "entity",
                "expected_entity_version": "V1",
                "expected_revision": 2,
                "expected_state_hash": "state",
                "identity": {"every_turn_guard": mod.IDENTITY_GUARD},
                "per_turn": {"identity_injection": "every substantive prompt_run_id refreshes identity"},
                "mandatory_invariants": ["every substantive prompt_run_id refreshes the Research Entity identity injection"],
                "active_program": mod.EXPECTED_PROGRAM,
                "active_stage": mod.EXPECTED_STAGE,
                "sole_owner_directive": mod.OWNER_DIRECTIVE,
                "product_endpoint": "ClayVerse",
                "release_form": mod.EXPECTED_RELEASE,
                "together_api": "FORBIDDEN",
                "vps_testing": "FORBIDDEN",
            },
            "research_entity/rooms/PROGRAM_STATE.json": {
                "program_id": "clayverse-single-container",
                "stage": mod.EXPECTED_STAGE,
                "current_stage": mod.EXPECTED_STAGE,
                "owner_directive": mod.OWNER_DIRECTIVE,
                "product_endpoint": "ClayVerse",
                "release_form": mod.EXPECTED_RELEASE,
                "execution_policy": {
                    "free_only": True,
                    "isolated_sandbox_only": True,
                    "vps_testing_forbidden": True,
                    "together_forbidden": True,
                },
            },
            "the artefact/manifest.json": {
                "artifact": "ClayVerse",
                "product_endpoint": "ClayVerse",
                "release_form": mod.EXPECTED_RELEASE,
                "canonical_workspace": "the artefact/",
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
                "effective_control_version": mod.EXPECTED_EFFECTIVE_CONTROL,
                "program_identity_override": {
                    "active_program": mod.EXPECTED_PROGRAM,
                    "target_stage": mod.EXPECTED_STAGE,
                    "product_endpoint": "ClayVerse",
                    "release_form": mod.EXPECTED_RELEASE,
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
            mod.STEERING844: {
                "program": mod.EXPECTED_PROGRAM,
                "stage": mod.EXPECTED_STAGE,
                "effective_control": mod.EXPECTED_EFFECTIVE_CONTROL,
                "adjudication": {"free_only": True, "together_forbidden": True, "vps_testing": False},
            },
        }
        text = {
            mod.OWNER_DIRECTIVE: "# ClayVerse\nStatus: CURRENT OWNER DIRECTIVE\n",
            "research_entity/continuity/CLAYVERSE_FAST_BOOTSTRAP_SOURCE_CURRENT.md": "CURRENT FAST CACHE\nactive ClayVerse program\n",
            "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md": "Program: ClayVerse single-container\nStage: CLAYVERSE_ARTIFACT\n",
            "the artefact/ARCHITECTURE.md": "ClayVerse is the product endpoint.\n",
            "the artefact/README.md": "# the artefact — ClayVerse single-container product\nThe active release endpoint is one OCI/Docker-compatible ClayVerse container image.\n",
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

    def test_coherent_clayverse_authority_passes(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        self.assertTrue(mod.validate(root)["pass"])

    def test_old_mini_entity_bootstrap_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["active_program"] = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH", mod.validate(root)["errors"])

    def test_identity_guard_loss_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["identity"] = {}
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("BOOTSTRAP_IDENTITY_GUARD_POINTER_MISSING", mod.validate(root)["errors"])

    def test_control41_paid_fallback_weakening_fails_closed(self):
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

    def test_control42_together_weakening_fails_closed(self):
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
        data["credit"] = {"tampered": True}
        path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        self.assertIn("CONTROL44_PRIOR_BLOB_MISMATCH", mod.validate(root)["errors"])

    def test_control44_mini_entity_regression_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.CONTROL44
        data = json.loads(path.read_text(encoding="utf-8"))
        data["program_identity_override"]["active_program"] = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("CONTROL44_PROGRAM_MISMATCH", mod.validate(root)["errors"])

    def test_control44_safety_weakening_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.CONTROL44
        data = json.loads(path.read_text(encoding="utf-8"))
        data["preserved_hard_rules"]["free_only"] = False
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("CONTROL44_FREE_ONLY_WEAKENED", mod.validate(root)["errors"])

    def test_superseded_directive_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.OWNER_DIRECTIVE
        path.write_text("# SUPERSEDED — compatibility redirect\n", encoding="utf-8")
        errors = mod.validate(root)["errors"]
        self.assertIn("DIRECTIVE_NOT_CURRENT", errors)
        self.assertIn("DIRECTIVE_MARKED_SUPERSEDED", errors)


if __name__ == "__main__":
    unittest.main()
