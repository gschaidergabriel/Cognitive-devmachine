from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "git_source_identity_v1.py"
SPEC = importlib.util.spec_from_file_location("git_source_identity_v1", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class GitSourceIdentityV1Tests(unittest.TestCase):
    def git(self, repo: Path, *args: str) -> None:
        subprocess.run(["git", "-C", str(repo), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def make_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir()
        self.git(repo, "init", "-q")
        (repo / "tracked.txt").write_text("initial\n", encoding="utf-8")
        self.git(repo, "add", "tracked.txt")
        subprocess.run(
            [
                "git", "-C", str(repo),
                "-c", "user.name=Clay Test",
                "-c", "user.email=clay-test@example.invalid",
                "commit", "-qm", "init",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return repo

    def test_clean_checkout_is_stable_and_clean(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td))
            first = mod.source_identity(repo)
            second = mod.source_identity(repo)
            self.assertFalse(first["dirty_state"]["dirty"])
            self.assertEqual(first, second)

    def test_same_porcelain_shape_different_tracked_bytes_change_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td))
            tracked = repo / "tracked.txt"
            tracked.write_text("version-two\n", encoding="utf-8")
            first = mod.source_identity(repo)
            tracked.write_text("version-six\n", encoding="utf-8")
            second = mod.source_identity(repo)
            self.assertTrue(first["dirty_state"]["dirty"])
            self.assertNotEqual(first["dirty_state_sha256"], second["dirty_state_sha256"])
            self.assertNotEqual(first["source_identity_sha256"], second["source_identity_sha256"])

    def test_untracked_content_change_changes_identity_without_persisting_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self.make_repo(Path(td))
            untracked = repo / "private-looking-name.txt"
            untracked.write_text("alpha\n", encoding="utf-8")
            first = mod.source_identity(repo)
            untracked.write_text("bravo\n", encoding="utf-8")
            second = mod.source_identity(repo)
            self.assertEqual(first["dirty_state"]["untracked_count"], 1)
            entry = first["dirty_state"]["untracked_entries"][0]
            self.assertNotIn("path", entry)
            self.assertIn("path_sha256", entry)
            self.assertNotEqual(first["dirty_state_sha256"], second["dirty_state_sha256"])


if __name__ == "__main__":
    unittest.main()
