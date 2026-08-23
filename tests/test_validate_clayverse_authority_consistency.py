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
            "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json": {"entity_id": "entity", "entity_version": "V1", "revision": 2, "state_hash": "state"},
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json": {
                "entity_id": "entity", "expected_entity_version": "V1", "expected_revision": 2, "expected_state_hash": "state",
                "identity": {"every_turn_guard": mod.IDENTITY_GUARD},
                "per_turn": {"identity_injection": "every substantive prompt_run_id refreshes identity"},
                "mandatory_invariants": ["every substantive prompt_run_id refreshes the Research Entity identity injection"],
                "active_program": mod.EXPECTED_PROGRAM, "active_stage": mod.EXPECTED_STAGE,
                "sole_owner_directive": mod.OWNER_DIRECTIVE, "product_endpoint": "ClayVerse",
                "release_form": mod.EXPECTED_RELEASE, "together_api": "FORBIDDEN", "vps_testing": "FORBIDDEN",
            },
            "research_entity/rooms/PROGRAM_STATE.json": {
                "program_id": "clayverse-single-container", "stage": mod.EXPECTED_STAGE, "current_stage": mod.EXPECTED_STAGE,
                "current_stage_goal": "Converge the complete one-container ClayVerse product.",
                "dynamic_targets": {"primary": mod.EXPECTED_DYNAMIC_PRIMARY},
                "current_frontier": "Run the next exact-current ClayVerse acceptance gate.",
                "go_contract": "Every go advances the same whole-ClayVerse product.",
                "owner_directive": mod.OWNER_DIRECTIVE, "product_endpoint": "ClayVerse", "release_form": mod.EXPECTED_RELEASE,
                "execution_policy": {"free_only": True, "isolated_sandbox_only": True, "vps_testing_forbidden": True, "together_forbidden": True},
            },
            "the artefact/manifest.json": {"artifact": "ClayVerse", "product_endpoint": "ClayVerse", "release_form": mod.EXPECTED_RELEASE, "canonical_workspace": "the artefact/"},
            mod.BASE41: {
                "schema_version": "4.1", "status": "ACTIVE", "mode": "FREE_ONLY",
                "cycle_policy": {"paid_fallback": False, "automatic_subscription_upgrade": False, "vps_testing": "FORBIDDEN", "self_hosted_vps_test_runners": "FORBIDDEN", "production_host_testing": "FORBIDDEN"},
            },
            mod.EXEC42: {
                "schema_version": "4.2-execution-boundary-addendum", "status": "ACTIVE", "mode": "FREE_ONLY",
                "base_control_path": mod.BASE41, "base_control_version": "4.1",
                "execution_routing": {"direct_vps_host_candidate_execution": "FORBIDDEN", "persistent_self_hosted_candidate_execution": "FORBIDDEN", "production_host_testing": "FORBIDDEN"},
                "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True, "frank_harness_modification": "FORBIDDEN"},
            },
            mod.PROGRAM43: {
                "schema_version": "4.3-program-authority-addendum", "status": "ACTIVE", "mode": "FREE_ONLY",
                "base_control_path": mod.BASE41, "execution_boundary_addendum_path": mod.EXEC42,
                "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden_under_current_control": True, "runtime_credit_requires_exact_admitted_execution": True, "frank_harness_modification": "FORBIDDEN"},
            },
            mod.CONTROL44: {
                "schema_version": "4.4-clayverse-product-authority-addendum", "status": "ACTIVE", "mode": "FREE_ONLY",
                "base_control_path": mod.BASE41, "execution_boundary_addendum_path": mod.EXEC42, "prior_program_authority_addendum_path": mod.PROGRAM43,
                "composition_order": ["4.1", "4.2-execution-boundary-addendum", "4.3-program-authority-addendum", "4.4-clayverse-product-authority-addendum"],
                "effective_control_version": mod.EXPECTED_EFFECTIVE_CONTROL,
                "program_identity_override": {"active_program": mod.EXPECTED_PROGRAM, "target_stage": mod.EXPECTED_STAGE, "product_endpoint": "ClayVerse", "release_form": mod.EXPECTED_RELEASE},
                "preserved_hard_rules": {"free_only": True, "paid_fallback": False, "together_forbidden": True, "vps_testing": False, "runtime_credit_requires_exact_admitted_isolated_execution": True, "frank_harness_modification": "FORBIDDEN"},
            },
            mod.STEERING844: {"program": mod.EXPECTED_PROGRAM, "stage": mod.EXPECTED_STAGE, "effective_control": mod.EXPECTED_EFFECTIVE_CONTROL, "adjudication": {"free_only": True, "together_forbidden": True, "vps_testing": False}},
        }
        text = {
            mod.OWNER_DIRECTIVE: "# ClayVerse\nStatus: CURRENT OWNER DIRECTIVE\n",
            "research_entity/continuity/CLAYVERSE_FAST_BOOTSTRAP_SOURCE_CURRENT.md": "CURRENT FAST CACHE\nactive ClayVerse program\n",
            "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md": "Program: ClayVerse single-container\nStage: CLAYVERSE_ARTIFACT\n",
            "the artefact/ARCHITECTURE.md": "ClayVerse is the product endpoint.\n",
            "the artefact/README.md": "# the artefact — ClayVerse single-container product\nThe active release endpoint is one OCI/Docker-compatible ClayVerse container image.\n",
            mod.ROOT_CLAUDE: "# CLAY — CURRENT CLAYVERSE REPO ORGAN\n`PROGRAM=CLAYVERSE_SINGLE_CONTAINER`\n`STAGE=CLAYVERSE_ARTIFACT`\nRead research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md first.\n",
        }
        for rel, data in files.items():
            path = root / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data), encoding="utf-8")
        for rel, data in text.items():
            path = root / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(data, encoding="utf-8")
        return td, root

    def mutate(self, root, rel, fn):
        path = root / rel
        data = json.loads(path.read_text(encoding="utf-8")); fn(data); path.write_text(json.dumps(data), encoding="utf-8")
        return mod.validate(root)["errors"]

    def test_coherent_clayverse_authority_passes(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup); self.assertTrue(mod.validate(root)["pass"])

    def test_old_mini_entity_bootstrap_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.assertIn("BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH", self.mutate(root, "research_entity/continuity/BOOTSTRAP_MINIMAL.json", lambda d: d.__setitem__("active_program", "MINI_ENTITY_PIPELINE_ALL_IN_ONE")))

    def test_identity_guard_loss_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.assertIn("BOOTSTRAP_IDENTITY_GUARD_POINTER_MISSING", self.mutate(root, "research_entity/continuity/BOOTSTRAP_MINIMAL.json", lambda d: d.__setitem__("identity", {})))

    def test_control44_mini_entity_regression_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.assertIn("CONTROL44_PROGRAM_MISMATCH", self.mutate(root, mod.CONTROL44, lambda d: d["program_identity_override"].__setitem__("active_program", "MINI_ENTITY_PIPELINE_ALL_IN_ONE")))

    def test_control44_safety_weakening_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.assertIn("CONTROL44_FREE_ONLY_WEAKENED", self.mutate(root, mod.CONTROL44, lambda d: d["preserved_hard_rules"].__setitem__("free_only", False)))

    def test_nested_work_selector_poison_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.assertIn("PROGRAM_DYNAMIC_PRIMARY_MISMATCH", self.mutate(root, "research_entity/rooms/PROGRAM_STATE.json", lambda d: d["dynamic_targets"].__setitem__("primary", "MINI_ENTITY_PIPELINE_ALL_IN_ONE")))

    def test_non_clayverse_frontier_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.assertIn("PROGRAM_FRONTIER_NOT_CLAYVERSE", self.mutate(root, "research_entity/rooms/PROGRAM_STATE.json", lambda d: d.__setitem__("current_frontier", "Continue Mini Entity work selection.")))

    def test_base41_paid_fallback_weakening_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.assertIn("BASE41_PAID_FALLBACK_WEAKENED", self.mutate(root, mod.BASE41, lambda d: d["cycle_policy"].__setitem__("paid_fallback", True)))

    def test_exec42_direct_vps_weakening_fails_closed_even_if_44_claims_preserved(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.assertIn("EXEC42_DIRECT_VPS_WEAKENED", self.mutate(root, mod.EXEC42, lambda d: d["execution_routing"].__setitem__("direct_vps_host_candidate_execution", "ALLOWED")))

    def test_program43_runtime_evidence_weakening_fails_closed_even_if_44_claims_preserved(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        self.assertIn("PROGRAM43_RUNTIME_EVIDENCE_WEAKENED", self.mutate(root, mod.PROGRAM43, lambda d: d["preserved_hard_rules"].__setitem__("runtime_credit_requires_exact_admitted_execution", False)))

    def test_superseded_directive_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.OWNER_DIRECTIVE; path.write_text("# SUPERSEDED — compatibility redirect\n", encoding="utf-8")
        errors = mod.validate(root)["errors"]
        self.assertIn("DIRECTIVE_NOT_CURRENT", errors); self.assertIn("DIRECTIVE_MARKED_SUPERSEDED", errors)

    def test_root_claude_mini_entity_program_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.ROOT_CLAUDE
        path.write_text("# stale repo organ\n`PROGRAM=MINI_ENTITY_PIPELINE_ALL_IN_ONE`\n`STAGE=CLAYVERSE_ARTIFACT`\nresearch_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md\n", encoding="utf-8")
        errors = mod.validate(root)["errors"]
        self.assertIn("ROOT_CLAUDE_PROGRAM_MISMATCH", errors); self.assertIn("ROOT_CLAUDE_MINI_ENTITY_PROGRAM_ACTIVE", errors)

    def test_root_claude_stale_blogpost_directive_fails_closed(self):
        td, root = self.make_tree(); self.addCleanup(td.cleanup)
        path = root / mod.ROOT_CLAUDE
        path.write_text("# stale first-read redirect\n`PROGRAM=CLAYVERSE_SINGLE_CONTAINER`\n`STAGE=CLAYVERSE_ARTIFACT`\nresearch_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md\nresearch_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md\n", encoding="utf-8")
        self.assertIn("ROOT_CLAUDE_STALE_BLOGPOST_DIRECTIVE", mod.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
