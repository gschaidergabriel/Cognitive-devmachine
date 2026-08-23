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
                "current_stage_goal": "Converge the complete one-container ClayVerse product.",
                "dynamic_targets": {"primary": mod.EXPECTED_DYNAMIC_PRIMARY},
                "current_frontier": "Run the next exact-current ClayVerse acceptance gate.",
                "go_contract": "Every go advances the same whole-ClayVerse product.",
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
            mod.CONTROL44: {
                "status": "ACTIVE",
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
                },
            },
            mod.STEERING844: {
                "program": mod.EXPECTED_PROGRAM,
                "stage": mod.EXPECTED_STAGE,
                "effective_control": "4.1+4.2+4.3+4.4-clayverse-product-authority-addendum",
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
            path.write_text(json.dumps(data), encoding="utf-8")
        for rel, data in text.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data, encoding="utf-8")
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

    def test_nested_work_selector_poison_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["dynamic_targets"]["primary"] = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("PROGRAM_DYNAMIC_PRIMARY_MISMATCH", mod.validate(root)["errors"])

    def test_non_clayverse_frontier_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "research_entity/rooms/PROGRAM_STATE.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["current_frontier"] = "Continue Mini Entity work selection."
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("PROGRAM_FRONTIER_NOT_CLAYVERSE", mod.validate(root)["errors"])

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
