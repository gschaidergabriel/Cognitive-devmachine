#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_free_evidence_forge_safe_871 as safe


class ForgeDisposableWorktree872(unittest.TestCase):
    def test_only_strict_child_of_forge_root_is_disposable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "forge"
            root.mkdir()
            child = root / "candidate" / "patched"
            child.mkdir(parents=True)
            outside = Path(td) / "outside"
            outside.mkdir()
            with mock.patch.object(safe.base, "FORGE_ROOT", root):
                self.assertTrue(safe._is_disposable_forge_workdir(child))
                self.assertFalse(safe._is_disposable_forge_workdir(root))
                self.assertFalse(safe._is_disposable_forge_workdir(outside))

    def test_disposable_worktree_bind_is_writable_but_root_probe_remains_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "forge"
            root.mkdir()
            child = root / "candidate" / "patched"
            child.mkdir(parents=True)

            def donor(cwd: Path):
                host = str(cwd.resolve())
                return ["bwrap", "--unshare-all", "--ro-bind", host, "/work", "--chdir", "/work", "--"]

            with (
                mock.patch.object(safe.base, "FORGE_ROOT", root),
                mock.patch.object(safe, "_ORIGINAL_BWRAP_PREFIX", side_effect=donor),
            ):
                child_prefix = safe._writable_disposable_bwrap_prefix(child)
                root_prefix = safe._writable_disposable_bwrap_prefix(root)

            child_slices = [child_prefix[i:i + 3] for i in range(len(child_prefix) - 2)]
            root_slices = [root_prefix[i:i + 3] for i in range(len(root_prefix) - 2)]
            self.assertIn(["--bind", str(child.resolve()), "/work"], child_slices)
            self.assertNotIn(["--ro-bind", str(child.resolve()), "/work"], child_slices)
            self.assertIn(["--ro-bind", str(root.resolve()), "/work"], root_slices)

    def test_unknown_namespace_layout_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "forge"
            root.mkdir()
            child = root / "candidate"
            child.mkdir()
            with (
                mock.patch.object(safe.base, "FORGE_ROOT", root),
                mock.patch.object(safe, "_ORIGINAL_BWRAP_PREFIX", return_value=["bwrap", "--unshare-all", "--"]),
            ):
                self.assertIsNone(safe._writable_disposable_bwrap_prefix(child))

    def test_model_command_outside_disposable_root_is_refused_before_executor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "forge"
            root.mkdir()
            outside = Path(td) / "outside"
            outside.mkdir()
            original = mock.Mock(return_value={"rc": 0})
            with (
                mock.patch.object(safe.base, "FORGE_ROOT", root),
                mock.patch.object(safe, "_ORIGINAL_ADMISSION_RUN_CMD", original),
            ):
                got = safe._run_cmd_disposable_only(outside, "pytest -q tests/test_demo.py", 5)
            self.assertEqual(126, got["rc"])
            self.assertIn("WORKDIR_OUTSIDE_DISPOSABLE_FORGE_ROOT", got["stderr"])
            original.assert_not_called()

    def test_model_command_inside_disposable_root_reaches_isolated_executor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "forge"
            root.mkdir()
            child = root / "candidate" / "patched"
            child.mkdir(parents=True)
            original = mock.Mock(return_value={"rc": 0, "stdout": "ok"})
            with (
                mock.patch.object(safe.base, "FORGE_ROOT", root),
                mock.patch.object(safe, "_ORIGINAL_ADMISSION_RUN_CMD", original),
            ):
                got = safe._run_cmd_disposable_only(child, "pytest -q tests/test_demo.py", 5)
            self.assertEqual(0, got["rc"])
            original.assert_called_once_with(child, "pytest -q tests/test_demo.py", 5)


if __name__ == "__main__":
    unittest.main()
