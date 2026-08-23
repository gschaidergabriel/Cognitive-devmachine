import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import validate_jspace_gwt_runtime_admission_v1 as runtime_admission
from test_validate_jspace_gwt_boot_binding_v1 import D6, manifest_bytes, valid_manifest, valid_receipt


def git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if cp.returncode != 0:
        raise AssertionError(cp.stdout + cp.stderr)
    return cp.stdout.strip()


def make_repo(root: Path) -> tuple[Path, str, str]:
    repo = root / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "JSpace Fixture")
    (repo / "tracked.txt").write_text("exact source fixture\n", encoding="utf-8")
    git(repo, "add", "tracked.txt")
    git(repo, "commit", "-qm", "fixture")
    return repo, git(repo, "rev-parse", "HEAD"), git(repo, "rev-parse", "HEAD^{tree}")


def exact_receipt(head: str, tree: str) -> dict:
    manifest = valid_manifest()
    receipt = valid_receipt(manifest, manifest_bytes(manifest))
    receipt["source"] = {"main_sha": head, "tree_sha": tree, "dirty": False}
    return receipt


class RuntimeSourceAdmissionTests(unittest.TestCase):
    def test_exact_clean_checkout_passes(self):
        with tempfile.TemporaryDirectory() as td:
            repo, head, tree = make_repo(Path(td))
            bound = runtime_admission.validate_checkout_binding(exact_receipt(head, tree), repo)
            self.assertEqual(bound, {"main_sha": head, "tree_sha": tree})

    def test_forged_valid_head_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            repo, head, tree = make_repo(Path(td))
            receipt = exact_receipt(head, tree)
            receipt["source"]["main_sha"] = "b" * 40
            with self.assertRaisesRegex(runtime_admission.RuntimeAdmissionError, "SOURCE_HEAD_MISMATCH"):
                runtime_admission.validate_checkout_binding(receipt, repo)

    def test_forged_valid_tree_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            repo, head, tree = make_repo(Path(td))
            receipt = exact_receipt(head, tree)
            receipt["source"]["tree_sha"] = "c" * 40
            with self.assertRaisesRegex(runtime_admission.RuntimeAdmissionError, "SOURCE_TREE_MISMATCH"):
                runtime_admission.validate_checkout_binding(receipt, repo)

    def test_dirty_checkout_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            repo, head, tree = make_repo(Path(td))
            (repo / "tracked.txt").write_text("mutated source fixture\n", encoding="utf-8")
            with self.assertRaisesRegex(runtime_admission.RuntimeAdmissionError, "SOURCE_CHECKOUT_DIRTY"):
                runtime_admission.validate_checkout_binding(exact_receipt(head, tree), repo)

    def test_dirty_receipt_cannot_receive_runtime_admission(self):
        with tempfile.TemporaryDirectory() as td:
            repo, head, tree = make_repo(Path(td))
            receipt = exact_receipt(head, tree)
            receipt["source"]["dirty"] = True
            receipt["source"]["dirty_diff_sha256"] = D6
            with self.assertRaisesRegex(
                runtime_admission.RuntimeAdmissionError,
                "SOURCE_RECEIPT_DIRTY_NOT_RUNTIME_ADMISSIBLE",
            ):
                runtime_admission.validate_checkout_binding(receipt, repo)

    def test_subdirectory_cannot_masquerade_as_source_root(self):
        with tempfile.TemporaryDirectory() as td:
            repo, head, tree = make_repo(Path(td))
            subdir = repo / "nested"
            subdir.mkdir()
            with self.assertRaisesRegex(runtime_admission.RuntimeAdmissionError, "SOURCE_ROOT_NOT_GIT_TOPLEVEL"):
                runtime_admission.validate_checkout_binding(exact_receipt(head, tree), subdir)


if __name__ == "__main__":
    unittest.main()
