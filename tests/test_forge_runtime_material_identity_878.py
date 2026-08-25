from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from forge_runtime_material_identity_878 import bind_material_sources


class ForgeRuntimeMaterialIdentity878Tests(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> None:
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "Clay Test",
            "GIT_AUTHOR_EMAIL": "clay@example.invalid",
            "GIT_COMMITTER_NAME": "Clay Test",
            "GIT_COMMITTER_EMAIL": "clay@example.invalid",
        }
        subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )

    def _fixture(self, root: Path) -> tuple[Path, Path]:
        self._git(root, "init")
        code = root / "forge.py"
        telemetry = root / "LIVE_METRICS.json"
        code.write_text("VALUE = 1\n", encoding="utf-8")
        telemetry.write_text('{"n": 0}\n', encoding="utf-8")
        self._git(root, "add", "forge.py", "LIVE_METRICS.json")
        self._git(root, "commit", "-m", "fixture")
        return code, telemetry

    def test_exact_material_source_is_admitted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            code, _ = self._fixture(root)
            result = bind_material_sources(root, [code])
            self.assertTrue(result["material_sources_match"])
            self.assertEqual(result["reason"], "MATERIAL_SOURCES_MATCH_HEAD")

    def test_dirty_material_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            code, _ = self._fixture(root)
            code.write_text("VALUE = 2\n", encoding="utf-8")
            result = bind_material_sources(root, [code])
            self.assertFalse(result["material_sources_match"])
            self.assertEqual(result["reason"], "MATERIAL_SOURCE_BLOB_MISMATCH")

    def test_dirty_tracked_nonmaterial_telemetry_does_not_demote_code(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            code, telemetry = self._fixture(root)
            telemetry.write_text('{"n": 1}\n', encoding="utf-8")
            status = subprocess.check_output(
                ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=no"],
                text=True,
            ).strip()
            self.assertTrue(status)
            result = bind_material_sources(root, [code])
            self.assertTrue(result["material_sources_match"])
            self.assertEqual(result["reason"], "MATERIAL_SOURCES_MATCH_HEAD")

    def test_missing_or_outside_material_fails_closed(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as other:
            root = Path(td)
            code, _ = self._fixture(root)
            outside = Path(other) / "outside.py"
            outside.write_text("X = 1\n", encoding="utf-8")
            result = bind_material_sources(root, [code, outside])
            self.assertFalse(result["material_sources_match"])
            self.assertEqual(result["reason"], "MATERIAL_SOURCE_BLOB_MISMATCH")


if __name__ == "__main__":
    unittest.main()
