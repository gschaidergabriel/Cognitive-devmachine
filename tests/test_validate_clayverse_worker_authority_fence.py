from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "validate_clayverse_authority_consistency.py"
spec = importlib.util.spec_from_file_location("authority_validator_worker_fence", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


GOOD_WORKER = f"""# ClayCode All-Workers Execution Directive — ClayVerse
Status: **CURRENT PROJECT OWNER WORKER DIRECTIVE**
Current product authority: `{mod.OWNER_DIRECTIVE}`
Active product: **ClayVerse**

```text
{mod.CLAYVERSE_WORKER_MARKER}
- Current build/test/experiment/runtime validation is isolated-sandbox-only.
- VPS/self-hosted/production-host test evidence is forbidden.
- Together API/service is forbidden.
```
"""


class ClayVerseWorkerAuthorityFenceTests(unittest.TestCase):
    def make_root(self, text: str = GOOD_WORKER):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        path = root / mod.WORKER_DIRECTIVE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        bootstrap = {
            "schema_version": "8.2",
            "all_worker_protocol": mod.WORKER_DIRECTIVE,
        }
        return td, root, bootstrap

    def test_current_clayverse_worker_protocol_passes(self):
        td, root, bootstrap = self.make_root()
        self.addCleanup(td.cleanup)
        errors: list[str] = []
        mod.validate_worker_authority(root, bootstrap, errors)
        self.assertEqual(errors, [])

    def test_bootstrap_pointer_drift_fails_closed(self):
        td, root, bootstrap = self.make_root()
        self.addCleanup(td.cleanup)
        bootstrap["all_worker_protocol"] = "research_entity/claycode/stale-mini-worker.md"
        errors: list[str] = []
        mod.validate_worker_authority(root, bootstrap, errors)
        self.assertIn("BOOTSTRAP_WORKER_DIRECTIVE_POINTER_MISMATCH", errors)

    def test_legacy_mini_entity_prompt_marker_fails_closed(self):
        td, root, bootstrap = self.make_root(
            GOOD_WORKER.replace(mod.CLAYVERSE_WORKER_MARKER, mod.LEGACY_WORKER_MARKER)
        )
        self.addCleanup(td.cleanup)
        errors: list[str] = []
        mod.validate_worker_authority(root, bootstrap, errors)
        self.assertIn("WORKER_CLAYVERSE_MARKER_MISSING", errors)
        self.assertIn("WORKER_LEGACY_MINI_ENTITY_MARKER_ACTIVE", errors)

    def test_active_mini_entity_program_token_fails_closed(self):
        td, root, bootstrap = self.make_root(
            GOOD_WORKER + "\nActive program: MINI_ENTITY_PIPELINE_ALL_IN_ONE\n"
        )
        self.addCleanup(td.cleanup)
        errors: list[str] = []
        mod.validate_worker_authority(root, bootstrap, errors)
        self.assertIn("WORKER_MINI_ENTITY_PROGRAM_ACTIVE", errors)

    def test_execution_fence_weakening_fails_closed(self):
        poisoned = GOOD_WORKER.replace(
            "VPS/self-hosted/production-host test evidence is forbidden.",
            "VPS testing may be used when convenient.",
        ).replace(
            "Together API/service is forbidden.",
            "Together API/service may be used.",
        )
        td, root, bootstrap = self.make_root(poisoned)
        self.addCleanup(td.cleanup)
        errors: list[str] = []
        mod.validate_worker_authority(root, bootstrap, errors)
        self.assertIn("WORKER_VPS_FENCE_MISSING", errors)
        self.assertIn("WORKER_TOGETHER_FENCE_MISSING", errors)

    def test_current_schema_requires_worker_file(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        errors: list[str] = []
        mod.validate_worker_authority(
            root,
            {"schema_version": "8.2", "all_worker_protocol": mod.WORKER_DIRECTIVE},
            errors,
        )
        self.assertTrue(any(item.startswith("MISSING:worker_directive:") for item in errors))


if __name__ == "__main__":
    unittest.main()
