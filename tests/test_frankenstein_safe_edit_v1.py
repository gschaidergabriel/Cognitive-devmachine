from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys

import pytest

PKG_DIR = Path(__file__).resolve().parents[1] / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(PKG_DIR))
import frankenstein_safe_edit_v1 as safe  # noqa: E402


def _git_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.test"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    (root / "src").mkdir()
    (root / "src" / "a.py").write_text("x = 1\ny = 2\n")
    (root / "src" / "b.py").write_text("left = 1\nright = 2\n")
    (root / "untouched.txt").write_bytes(b"DO-NOT-TOUCH\x00RAW\n")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "baseline"], cwd=root, check=True, capture_output=True)
    return root


def _patch_a(new_y: int = 3) -> str:
    return (
        "--- a/src/a.py\n"
        "+++ b/src/a.py\n"
        "@@ -1,2 +1,2 @@\n"
        " x = 1\n"
        "-y = 2\n"
        f"+y = {new_y}\n"
    )


def _patch_b(new_right: int = 4) -> str:
    return (
        "--- a/src/b.py\n"
        "+++ b/src/b.py\n"
        "@@ -1,2 +1,2 @@\n"
        " left = 1\n"
        "-right = 2\n"
        f"+right = {new_right}\n"
    )


def test_snapshot_binds_exact_sha_and_size(tmp_path):
    root = _git_repo(tmp_path)
    snap = safe.snapshot_existing_files(root, ["src/a.py"])
    data = (root / "src" / "a.py").read_bytes()
    assert snap["src/a.py"].sha256 == hashlib.sha256(data).hexdigest()
    assert snap["src/a.py"].size_bytes == len(data)


def test_valid_patch_set_changes_only_targets_and_preserves_unrelated_bytes(tmp_path):
    root = _git_repo(tmp_path)
    untouched_before = (root / "untouched.txt").read_bytes()
    snap = safe.snapshot_existing_files(root, ["src/a.py", "src/b.py"])
    receipt = safe.transactional_apply_patch_set(
        root,
        {"src/a.py": _patch_a(), "src/b.py": _patch_b()},
        {k: v.sha256 for k, v in snap.items()},
        verifier=lambda: "y = 3" in (root / "src" / "a.py").read_text()
        and "right = 4" in (root / "src" / "b.py").read_text(),
    )
    assert (root / "src" / "a.py").read_text() == "x = 1\ny = 3\n"
    assert (root / "src" / "b.py").read_text() == "left = 1\nright = 4\n"
    assert (root / "untouched.txt").read_bytes() == untouched_before
    assert receipt.schema == "FRANKENSTEIN_SAFE_EDIT_RECEIPT/v1"
    assert receipt.verifier_ran and receipt.verifier_passed


def test_wrong_preimage_hash_fails_closed_without_change(tmp_path):
    root = _git_repo(tmp_path)
    before = (root / "src" / "a.py").read_bytes()
    with pytest.raises(safe.PreimageMismatch):
        safe.transactional_apply_patch_set(root, {"src/a.py": _patch_a()}, {"src/a.py": "0" * 64})
    assert (root / "src" / "a.py").read_bytes() == before


def test_toctou_change_after_snapshot_is_rejected(tmp_path):
    root = _git_repo(tmp_path)
    snap = safe.snapshot_existing_files(root, ["src/a.py"])
    (root / "src" / "a.py").write_text("x = 999\ny = 2\n")
    mutated = (root / "src" / "a.py").read_bytes()
    with pytest.raises(safe.PreimageMismatch):
        safe.transactional_apply_patch_set(root, {"src/a.py": _patch_a()}, {"src/a.py": snap["src/a.py"].sha256})
    assert (root / "src" / "a.py").read_bytes() == mutated


@pytest.mark.parametrize("bad", ["../x.py", "/tmp/x.py", "src/../a.py", ".git/config", r"src\\a.py"])
def test_unsafe_paths_are_rejected(tmp_path, bad):
    root = _git_repo(tmp_path)
    with pytest.raises(safe.UnsafePath):
        safe.snapshot_existing_files(root, [bad])


def test_full_file_response_is_not_a_patch(tmp_path):
    root = _git_repo(tmp_path)
    snap = safe.snapshot_existing_files(root, ["src/a.py"])
    with pytest.raises(safe.InvalidPatch):
        safe.transactional_apply_patch_set(
            root,
            {"src/a.py": "FILE: src/a.py\n```python\nx = 9\n```\n"},
            {"src/a.py": snap["src/a.py"].sha256},
        )


def test_patch_header_must_match_target_exactly(tmp_path):
    root = _git_repo(tmp_path)
    snap = safe.snapshot_existing_files(root, ["src/a.py"])
    wrong = _patch_a().replace("a/src/a.py", "a/src/b.py").replace("b/src/a.py", "b/src/b.py")
    with pytest.raises(safe.InvalidPatch):
        safe.transactional_apply_patch_set(root, {"src/a.py": wrong}, {"src/a.py": snap["src/a.py"].sha256})


@pytest.mark.parametrize(
    "marker",
    ["rename from src/a.py", "new file mode 100644", "deleted file mode 100644", "GIT binary patch", "--- /dev/null"],
)
def test_rename_create_delete_binary_and_mode_changes_are_rejected(tmp_path, marker):
    root = _git_repo(tmp_path)
    snap = safe.snapshot_existing_files(root, ["src/a.py"])
    patch = marker + "\n" + _patch_a()
    with pytest.raises(safe.InvalidPatch):
        safe.transactional_apply_patch_set(root, {"src/a.py": patch}, {"src/a.py": snap["src/a.py"].sha256})


def test_verifier_false_rolls_back_byte_identical_preimage(tmp_path):
    root = _git_repo(tmp_path)
    before = (root / "src" / "a.py").read_bytes()
    snap = safe.snapshot_existing_files(root, ["src/a.py"])
    with pytest.raises(safe.VerificationFailed):
        safe.transactional_apply_patch_set(
            root, {"src/a.py": _patch_a()}, {"src/a.py": snap["src/a.py"].sha256}, verifier=lambda: False
        )
    assert (root / "src" / "a.py").read_bytes() == before


def test_verifier_exception_rolls_back_byte_identical_preimage(tmp_path):
    root = _git_repo(tmp_path)
    before = (root / "src" / "a.py").read_bytes()
    snap = safe.snapshot_existing_files(root, ["src/a.py"])

    def boom():
        raise RuntimeError("verification exploded")

    with pytest.raises(RuntimeError, match="verification exploded"):
        safe.transactional_apply_patch_set(
            root, {"src/a.py": _patch_a()}, {"src/a.py": snap["src/a.py"].sha256}, verifier=boom
        )
    assert (root / "src" / "a.py").read_bytes() == before


def test_multi_file_validation_failure_changes_neither_file(tmp_path):
    root = _git_repo(tmp_path)
    before_a = (root / "src" / "a.py").read_bytes()
    before_b = (root / "src" / "b.py").read_bytes()
    snap = safe.snapshot_existing_files(root, ["src/a.py", "src/b.py"])
    bad_b = _patch_b().replace("+++ b/src/b.py", "+++ b/src/not-b.py")
    with pytest.raises(safe.InvalidPatch):
        safe.transactional_apply_patch_set(
            root,
            {"src/a.py": _patch_a(), "src/b.py": bad_b},
            {k: v.sha256 for k, v in snap.items()},
        )
    assert (root / "src" / "a.py").read_bytes() == before_a
    assert (root / "src" / "b.py").read_bytes() == before_b


def test_git_apply_check_failure_changes_nothing(tmp_path):
    root = _git_repo(tmp_path)
    before = (root / "src" / "a.py").read_bytes()
    snap = safe.snapshot_existing_files(root, ["src/a.py"])
    context_wrong = _patch_a().replace(" x = 1", " x = 777")
    with pytest.raises(safe.PatchCheckFailed):
        safe.transactional_apply_patch_set(root, {"src/a.py": context_wrong}, {"src/a.py": snap["src/a.py"].sha256})
    assert (root / "src" / "a.py").read_bytes() == before


def test_expected_hash_keyset_must_exactly_match_patch_targets(tmp_path):
    root = _git_repo(tmp_path)
    snap = safe.snapshot_existing_files(root, ["src/a.py", "src/b.py"])
    with pytest.raises(safe.PreimageMismatch):
        safe.transactional_apply_patch_set(
            root,
            {"src/a.py": _patch_a()},
            {"src/a.py": snap["src/a.py"].sha256, "src/b.py": snap["src/b.py"].sha256},
        )


def test_symlink_target_is_rejected_when_supported(tmp_path):
    root = _git_repo(tmp_path)
    link = root / "src" / "link.py"
    try:
        link.symlink_to(root / "src" / "a.py")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(safe.UnsafePath):
        safe.snapshot_existing_files(root, ["src/link.py"])
