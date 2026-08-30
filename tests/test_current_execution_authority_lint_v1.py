import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "tools" / "current_execution_authority_lint_v1.py"
spec = importlib.util.spec_from_file_location("lintmod", MOD_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class CurrentExecutionAuthorityLintTests(unittest.TestCase):
    def test_current_repository_projection_is_consistent(self):
        manifest = mod.load(ROOT / "governance" / "CURRENT_EXECUTION_SURFACE_PROJECTIONS_V1.json")
        self.assertEqual(mod.lint(ROOT, manifest), [])

    def _minimal_repo(self, stale=False, historical=False, banner=True):
        td = tempfile.TemporaryDirectory()
        root = pathlib.Path(td.name)
        (root / "governance").mkdir()
        authority = (
            "absence of a direct chat SSH tool is not `NO_EXECUTOR`\n"
            "FREE_ONLY_PROVIDER_POLICY != NO_VPS\n"
            "EXECUTION_SURFACE_RESOLUTION_PROTOCOL_V1.md\n"
        )
        (root / "CLAY_EXECUTION_AUTHORITY.md").write_text(authority)
        (root / "governance" / "EXECUTION_SURFACE_RESOLUTION_PROTOCOL_V1.md").write_text("protocol")
        (root / "governance" / "EXECUTION_SURFACE_REGISTRY_V1.json").write_text("{}")
        role = "SUPERSEDED_HISTORICAL_SNAPSHOT" if historical else "CURRENT_WORKER_ROUTING_SHIM"
        text = "Status: SUPERSEDED HISTORICAL\n" if banner else "Status: CURRENT\n"
        text += "required\n"
        if stale:
            text += "VPS/self-hosted/production-host testing is forbidden under current control\n"
        (root / "projection.md").write_text(text)
        manifest = {
            "canonical_authority": "CLAY_EXECUTION_AUTHORITY.md",
            "resolver_protocol": "governance/EXECUTION_SURFACE_RESOLUTION_PROTOCOL_V1.md",
            "registry": "governance/EXECUTION_SURFACE_REGISTRY_V1.json",
            "projections": [{"path": "projection.md", "role": role, "required_markers": ["required"]}],
            "forbidden_current_claims": ["VPS/self-hosted/production-host testing is forbidden under current control"],
            "historical_roles_may_contain_forbidden_claims_only_when_supersession_marked": ["SUPERSEDED_HISTORICAL_SNAPSHOT"],
        }
        return td, root, manifest

    def test_stale_current_projection_fails(self):
        td, root, manifest = self._minimal_repo(stale=True, historical=False)
        try:
            errors = mod.lint(root, manifest)
            self.assertTrue(any(e.startswith("STALE_CURRENT_CLAIM") for e in errors), errors)
        finally:
            td.cleanup()

    def test_historical_stale_text_requires_top_supersession_banner(self):
        td, root, manifest = self._minimal_repo(stale=True, historical=True, banner=False)
        try:
            errors = mod.lint(root, manifest)
            self.assertTrue(any(e.startswith("HISTORICAL_WITHOUT_TOP_SUPERSESSION") for e in errors), errors)
        finally:
            td.cleanup()

    def test_historical_stale_text_with_banner_is_allowed(self):
        td, root, manifest = self._minimal_repo(stale=True, historical=True, banner=True)
        try:
            self.assertEqual(mod.lint(root, manifest), [])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
