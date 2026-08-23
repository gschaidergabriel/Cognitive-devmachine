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
            "research_entity/continuity/BOOTSTRAP_MINIMAL.json": {
                "active_program": "CLAYVERSE_SINGLE_CONTAINER",
                "active_stage": "CLAYVERSE_ARTIFACT",
                "sole_owner_directive": mod.OWNER_DIRECTIVE,
                "product_endpoint": "ClayVerse",
                "release_form": mod.EXPECTED_RELEASE,
            },
            "research_entity/rooms/PROGRAM_STATE.json": {
                "program_id": "clayverse-single-container",
                "stage": "CLAYVERSE_ARTIFACT",
                "owner_directive": mod.OWNER_DIRECTIVE,
                "product_endpoint": "ClayVerse",
                "release_form": mod.EXPECTED_RELEASE,
            },
            "the artefact/manifest.json": {
                "artifact": "ClayVerse",
                "product_endpoint": "ClayVerse",
                "release_form": mod.EXPECTED_RELEASE,
                "canonical_workspace": "the artefact/",
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
        result = mod.validate(root)
        self.assertTrue(result["pass"], result)

    def test_old_mini_entity_bootstrap_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["active_program"] = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
        path.write_text(json.dumps(data), encoding="utf-8")
        result = mod.validate(root)
        self.assertFalse(result["pass"])
        self.assertIn("BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH", result["errors"])

    def test_superseded_directive_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / mod.OWNER_DIRECTIVE
        path.write_text("# SUPERSEDED — compatibility redirect\n", encoding="utf-8")
        result = mod.validate(root)
        self.assertFalse(result["pass"])
        self.assertIn("DIRECTIVE_NOT_CURRENT", result["errors"])
        self.assertIn("DIRECTIVE_MARKED_SUPERSEDED", result["errors"])

    def test_readme_claiming_clayverse_superseded_fails_closed(self):
        td, root = self.make_tree()
        self.addCleanup(td.cleanup)
        path = root / "the artefact/README.md"
        path.write_text(
            "# the artefact — ClayVerse single-container product\n"
            "The active release endpoint is one OCI/Docker-compatible ClayVerse container image.\n"
            "The previous ClayVerse single-container endpoint is superseded.\n",
            encoding="utf-8",
        )
        result = mod.validate(root)
        self.assertFalse(result["pass"])
        self.assertIn("README_CLAYVERSE_SUPERSEDED", result["errors"])


if __name__ == "__main__":
    unittest.main()
