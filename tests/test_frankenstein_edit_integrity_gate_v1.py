from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from frankenstein_edit_integrity_gate_v1 import (  # noqa: E402
    EditIntegrityError,
    EditPolicy,
    apply_existing_file_patch,
)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)


def _repo(tmp_path: Path, content: str = "alpha\nbeta\ngamma\n") -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    assert _git(root, "init", "-q").returncode == 0
    assert _git(root, "config", "user.email", "test@example.invalid").returncode == 0
    assert _git(root, "config", "user.name", "test").returncode == 0
    (root / "mod.txt").write_text(content)
    assert _git(root, "add", "mod.txt").returncode == 0
    assert _git(root, "commit", "-qm", "init").returncode == 0
    return root


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _patch(root: Path, new_content: str, path: str = "mod.txt") -> bytes:
    p = root / path
    old = p.read_bytes() if p.exists() else None
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(new_content)
    cp = subprocess.run(["git", "diff", "--", path], cwd=root, capture_output=True, check=True)
    if old is None:
        p.unlink()
    else:
        p.write_bytes(old)
    return cp.stdout


def test_valid_patch_applies_and_receipt_binds_pre_and_post_hashes(tmp_path):
    root = _repo(tmp_path)
    before = _sha(root / "mod.txt")
    patch = _patch(root, "alpha\nBETA\ngamma\n")
    receipt = apply_existing_file_patch(root, patch, {"mod.txt": before})
    assert (root / "mod.txt").read_text() == "alpha\nBETA\ngamma\n"
    assert receipt.preimage_sha256["mod.txt"] == before
    assert receipt.postimage_sha256["mod.txt"] == _sha(root / "mod.txt")
    assert receipt.patch_sha256 == hashlib.sha256(patch).hexdigest()
    assert receipt.git_diff_check == "PASS"
    assert receipt.reverse_apply_check == "PASS"
    assert receipt.scope == "EXISTING_FILE_PATCH_INTEGRITY_ONLY"


def test_stale_preimage_hash_fails_before_mutation(tmp_path):
    root = _repo(tmp_path)
    original = (root / "mod.txt").read_bytes()
    patch = _patch(root, "alpha\nBETA\ngamma\n")
    with pytest.raises(EditIntegrityError, match="preimage SHA-256 mismatch"):
        apply_existing_file_patch(root, patch, {"mod.txt": "0" * 64})
    assert (root / "mod.txt").read_bytes() == original


def test_context_mismatch_patch_fails_before_mutation(tmp_path):
    root = _repo(tmp_path)
    before = _sha(root / "mod.txt")
    patch = _patch(root, "alpha\nBETA\ngamma\n").replace(b"-beta", b"-not-beta")
    original = (root / "mod.txt").read_bytes()
    with pytest.raises(EditIntegrityError, match="git apply --check failed|cannot inspect patch"):
        apply_existing_file_patch(root, patch, {"mod.txt": before})
    assert (root / "mod.txt").read_bytes() == original


def test_undeclared_second_file_is_rejected(tmp_path):
    root = _repo(tmp_path)
    (root / "other.txt").write_text("one\ntwo\n")
    assert _git(root, "add", "other.txt").returncode == 0
    assert _git(root, "commit", "-qm", "other").returncode == 0
    before = _sha(root / "mod.txt")
    mod_old = (root / "mod.txt").read_bytes()
    other_old = (root / "other.txt").read_bytes()
    (root / "mod.txt").write_text("alpha\nBETA\ngamma\n")
    (root / "other.txt").write_text("one\nTWO\n")
    patch = subprocess.run(["git", "diff"], cwd=root, capture_output=True, check=True).stdout
    (root / "mod.txt").write_bytes(mod_old)
    (root / "other.txt").write_bytes(other_old)
    with pytest.raises(EditIntegrityError, match="path mismatch"):
        apply_existing_file_patch(root, patch, {"mod.txt": before})
    assert (root / "mod.txt").read_bytes() == mod_old
    assert (root / "other.txt").read_bytes() == other_old


def test_path_escape_declaration_is_rejected(tmp_path):
    root = _repo(tmp_path)
    patch = _patch(root, "alpha\nBETA\ngamma\n")
    with pytest.raises(EditIntegrityError, match="unsafe declared path"):
        apply_existing_file_patch(root, patch, {"../outside.txt": "0" * 64})


def test_new_file_patch_is_rejected(tmp_path):
    root = _repo(tmp_path)
    (root / "new.txt").write_text("new\n")
    patch = subprocess.run(["git", "diff", "--no-index", "/dev/null", "new.txt"], cwd=root, capture_output=True).stdout
    (root / "new.txt").unlink()
    with pytest.raises(EditIntegrityError):
        apply_existing_file_patch(root, patch, {"mod.txt": _sha(root / "mod.txt")})


def test_large_deletion_is_rejected_even_when_patch_is_valid(tmp_path):
    content = "".join(f"line-{i}\n" for i in range(100))
    root = _repo(tmp_path, content)
    before = _sha(root / "mod.txt")
    patch = _patch(root, "".join(f"line-{i}\n" for i in range(40)))
    with pytest.raises(EditIntegrityError, match="deletion fraction exceeded"):
        apply_existing_file_patch(root, patch, {"mod.txt": before})
    assert (root / "mod.txt").read_text() == content


def test_explicit_stricter_deletion_budget_is_enforced(tmp_path):
    content = "".join(f"line-{i}\n" for i in range(20))
    root = _repo(tmp_path, content)
    before = _sha(root / "mod.txt")
    patch = _patch(root, "".join(f"line-{i}\n" for i in range(16)))
    policy = EditPolicy(max_deleted_fraction_per_file=1.0, max_deleted_lines_per_file=2)
    with pytest.raises(EditIntegrityError, match="deletion budget exceeded"):
        apply_existing_file_patch(root, patch, {"mod.txt": before}, policy=policy)


def test_whitespace_error_fails_preflight_and_preserves_original(tmp_path):
    root = _repo(tmp_path)
    before = _sha(root / "mod.txt")
    original = (root / "mod.txt").read_bytes()
    patch = _patch(root, "alpha\nbeta   \ngamma\n")
    with pytest.raises(EditIntegrityError, match="git apply --check failed"):
        apply_existing_file_patch(root, patch, {"mod.txt": before})
    assert (root / "mod.txt").read_bytes() == original


def test_672_line_file_small_patch_preserves_all_unrelated_lines(tmp_path):
    content = "".join(f"line-{i:03d}\n" for i in range(672))
    root = _repo(tmp_path, content)
    before = _sha(root / "mod.txt")
    lines = content.splitlines()
    lines[336] = "line-336-CHANGED"
    patch = _patch(root, "\n".join(lines) + "\n")
    apply_existing_file_patch(root, patch, {"mod.txt": before})
    result = (root / "mod.txt").read_text().splitlines()
    assert len(result) == 672
    assert result[335] == "line-335"
    assert result[336] == "line-336-CHANGED"
    assert result[337] == "line-337"


def test_symlink_parent_escape_is_rejected_before_mutation(tmp_path):
    root = _repo(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "victim.txt"
    victim.write_text("outside-data\n")
    (root / "linked").symlink_to(outside, target_is_directory=True)

    # The declaration is lexically repo-relative but resolves through a
    # symlink parent outside the worktree. It must never be admitted.
    patch = (
        b"diff --git a/linked/victim.txt b/linked/victim.txt\n"
        b"--- a/linked/victim.txt\n"
        b"+++ b/linked/victim.txt\n"
        b"@@ -1 +1 @@\n"
        b"-outside-data\n"
        b"+tampered\n"
    )
    before = hashlib.sha256(victim.read_bytes()).hexdigest()
    with pytest.raises(EditIntegrityError, match="symlink path component forbidden"):
        apply_existing_file_patch(root, patch, {"linked/victim.txt": before})
    assert victim.read_text() == "outside-data\n"
