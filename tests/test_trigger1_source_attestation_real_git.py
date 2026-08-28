#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from trigger1_source_attestation import exact_source_identity, require_clean_source


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class Trigger1SourceAttestationRealGitTests(unittest.TestCase):
    def make_repo(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        git(root, "init", "-q")
        git(root, "config", "user.email", "test@example.invalid")
        git(root, "config", "user.name", "test")
        (root / "tracked.txt").write_text("base\n", encoding="utf-8")
        git(root, "add", "tracked.txt")
        git(root, "commit", "-qm", "init")
        return td, root

    def test_real_clean_repo_is_explicitly_clean_and_stable(self):
        td, root = self.make_repo()
        try:
            a = require_clean_source(root)
            b = require_clean_source(root)
            self.assertFalse(a["repo_dirty"])
            self.assertEqual(hashlib.sha256(b"").hexdigest(), a["repo_status_sha256"])
            self.assertEqual(a, b)
        finally:
            td.cleanup()

    def test_real_tracked_modification_fails_closed(self):
        td, root = self.make_repo()
        try:
            clean = exact_source_identity(root)
            (root / "tracked.txt").write_text("modified\n", encoding="utf-8")
            dirty = exact_source_identity(root)
            self.assertTrue(dirty["repo_dirty"])
            self.assertNotEqual(clean["repo_status_sha256"], dirty["repo_status_sha256"])
            with self.assertRaisesRegex(RuntimeError, "DIRTY_SOURCE_TREE_FAIL_CLOSED"):
                require_clean_source(root)
        finally:
            td.cleanup()

    def test_same_porcelain_shape_different_bytes_get_distinct_exact_identity(self):
        td, root = self.make_repo()
        try:
            tracked = root / "tracked.txt"
            tracked.write_text("version-two\n", encoding="utf-8")
            first = exact_source_identity(root)
            tracked.write_text("version-six\n", encoding="utf-8")
            second = exact_source_identity(root)
            # Both worktrees report the same path/status shape, which is why the
            # compatibility Porcelain digest alone cannot be the evidence identity.
            self.assertEqual(first["repo_status_sha256"], second["repo_status_sha256"])
            self.assertNotEqual(first["repo_dirty_state_sha256"], second["repo_dirty_state_sha256"])
            self.assertNotEqual(first["source_identity_sha256"], second["source_identity_sha256"])
        finally:
            td.cleanup()

    def test_real_staged_modification_fails_closed(self):
        td, root = self.make_repo()
        try:
            (root / "tracked.txt").write_text("staged\n", encoding="utf-8")
            git(root, "add", "tracked.txt")
            self.assertTrue(exact_source_identity(root)["repo_dirty"])
            with self.assertRaisesRegex(RuntimeError, "DIRTY_SOURCE_TREE_FAIL_CLOSED"):
                require_clean_source(root)
        finally:
            td.cleanup()

    def test_real_untracked_file_fails_closed(self):
        td, root = self.make_repo()
        try:
            (root / "untracked.bin").write_bytes(b"candidate bytes")
            self.assertTrue(exact_source_identity(root)["repo_dirty"])
            with self.assertRaisesRegex(RuntimeError, "DIRTY_SOURCE_TREE_FAIL_CLOSED"):
                require_clean_source(root)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
