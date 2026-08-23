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
            "CLAUDE.md": (
                "# CLAY — CLAYVERSE RESEARCH / BUILD ORGAN\n"
                "`PROGRAM=CLAYVERSE_SINGLE_CONTAINER`\n"
                "`STAGE=CLAYVERSE_ARTIFACT`\n"
                "`PRODUCT=one OCI/Docker-compatible ClayVerse container image`\n"
                f"Current owner directive: `{mod.OWNER_DIRECTIVE}`\n"
                "This root `CLAUDE.md` is repository-worker instruction only.\n"
                "UnifiedDB remains the sole durable canonical cognition/state/memory/data authority.\n"
                "Together API/service: **forbidden**.\n"
            ),
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

    def test_superseded_directive_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.OWNER_DIRECTIVE
        path.write_text("# SUPERSEDED — compatibility redirect\n", encoding="utf-8")
        errors = mod.validate(root)["errors"]
        self.assertIn("DIRECTIVE_NOT_CURRENT", errors)
        self.assertIn("DIRECTIVE_MARKED_SUPERSEDED", errors)

    def test_root_claude_mini_entity_regression_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "CLAUDE.md"
        path.write_text(
            "# CLAY — MULTI-USE MINI ENTITY BUILD ORGAN\n"
            "`PROGRAM=MINI_ENTITY_PIPELINE_ALL_IN_ONE`\n",
            encoding="utf-8",
        )
        errors = mod.validate(root)["errors"]
        self.assertIn("CLAUDE_ROOT_PROGRAM_MISMATCH", errors)
        self.assertIn("CLAUDE_ROOT_STALE_MINI_ENTITY_AUTHORITY", errors)

    def test_root_claude_cannot_be_runtime_memory_authority(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "CLAUDE.md"
        text = path.read_text(encoding="utf-8").replace("repository-worker instruction only", "product runtime memory authority")
        path.write_text(text, encoding="utf-8")
        self.assertIn("CLAUDE_ROOT_RUNTIME_MEMORY_SCOPE_MISSING", mod.validate(root)["errors"])


if __name__ == "__main__":
    unittest.main()
