from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GUARD_PATH = (
    REPO_ROOT
    / "research_entity"
    / "topic_packets"
    / "frankenstein-master-cognition-concept"
    / "frankenstein_edit_guard_v2.py"
)
spec = importlib.util.spec_from_file_location("frankenstein_edit_guard_v2", GUARD_PATH)
guard = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = guard
spec.loader.exec_module(guard)


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    return repo


def _track(repo: Path, rel: str, content: str) -> str:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    subprocess.run(["git", "add", rel], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", f"add {rel}"], cwd=repo, check=True)
    return guard.sha256_file(p)


def _head(repo: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def _patch(rel: str, old: str, new: str) -> str:
    import difflib
    body = "".join(difflib.unified_diff(
        old.splitlines(True), new.splitlines(True),
        fromfile=f"a/{rel}", tofile=f"b/{rel}", n=3,
    ))
    return f"diff --git a/{rel} b/{rel}\n" + body


def test_small_exact_base_patch_applies_and_receipts_hashes(tmp_path):
    repo = _repo(tmp_path)
    old = "def f():\n    return 1\n"
    new = "def f():\n    return 2\n\ndef g():\n    return 3\n"
    base = _track(repo, "tools/x.py", old)
    receipt = guard.apply_guarded_patch(
        repo, _patch("tools/x.py", old, new),
        expected_base_sha256={"tools/x.py": base},
        expected_head_sha=_head(repo),
        allowed_paths=["tools/x.py"],
    )
    assert (repo / "tools/x.py").read_text() == new
    assert receipt["status"] == "APPLIED_NOT_YET_VERIFIED"
    assert receipt["files"][0]["before_sha256"] == base
    assert receipt["files"][0]["after_sha256"] == guard.sha256_file(repo / "tools/x.py")


def test_stale_base_hash_fails_before_mutation(tmp_path):
    repo = _repo(tmp_path)
    old = "x = 1\n"
    new = "x = 2\n"
    _track(repo, "x.py", old)
    with pytest.raises(guard.EditGuardError, match="stale base hash"):
        guard.apply_guarded_patch(
            repo, _patch("x.py", old, new),
            expected_base_sha256={"x.py": "0" * 64},
            expected_head_sha=_head(repo),
            allowed_paths=["x.py"],
        )
    assert (repo / "x.py").read_text() == old


def test_stale_repository_head_fails_before_mutation(tmp_path):
    repo = _repo(tmp_path)
    old = "x = 1\n"
    new = "x = 2\n"
    base = _track(repo, "x.py", old)
    with pytest.raises(guard.EditGuardError, match="stale repository HEAD"):
        guard.apply_guarded_patch(
            repo,
            _patch("x.py", old, new),
            expected_base_sha256={"x.py": base},
            expected_head_sha="0" * 40,
            allowed_paths=["x.py"],
        )
    assert (repo / "x.py").read_text() == old


def test_unallowed_file_fails_closed(tmp_path):
    repo = _repo(tmp_path)
    old = "x = 1\n"
    new = "x = 2\n"
    base = _track(repo, "x.py", old)
    with pytest.raises(guard.EditGuardError, match="outside allowlist"):
        guard.apply_guarded_patch(
            repo, _patch("x.py", old, new),
            expected_base_sha256={"x.py": base},
            expected_head_sha=_head(repo),
            allowed_paths=["other.py"],
        )
    assert (repo / "x.py").read_text() == old


def test_traversal_patch_rejected(tmp_path):
    repo = _repo(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("secret = 1\n")
    _track(repo, "seed.txt", "seed\n")
    patch = (
        "diff --git a/../outside.py b/../outside.py\n"
        "--- a/../outside.py\n+++ b/../outside.py\n"
        "@@ -1 +1 @@\n-secret = 1\n+secret = 2\n"
    )
    with pytest.raises(guard.EditGuardError, match="unsafe path"):
        guard.apply_guarded_patch(
            repo, patch,
            expected_base_sha256={"outside.py": "0" * 64},
            expected_head_sha=_head(repo),
            allowed_paths=["outside.py"],
        )
    assert outside.read_text() == "secret = 1\n"


def test_symlink_edit_rejected_before_read_or_write(tmp_path):
    repo = _repo(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("secret = 1\n")
    _track(repo, "seed.txt", "seed\n")
    (repo / "link.py").symlink_to(outside)
    patch = (
        "diff --git a/link.py b/link.py\n--- a/link.py\n+++ b/link.py\n"
        "@@ -1 +1 @@\n-secret = 1\n+secret = 2\n"
    )
    with pytest.raises(guard.EditGuardError, match="symlink edits are forbidden"):
        guard.apply_guarded_patch(
            repo, patch,
            expected_base_sha256={"link.py": guard.sha256_file(outside)},
            expected_head_sha=_head(repo),
            allowed_paths=["link.py"],
        )
    assert outside.read_text() == "secret = 1\n"


def test_large_semantic_replacement_same_size_is_rejected_by_deletion_fraction(tmp_path):
    repo = _repo(tmp_path)
    old = "".join(f"old_{i} = {i}\n" for i in range(100))
    new = "".join(f"new_{i} = {i}\n" for i in range(100))
    base = _track(repo, "big.py", old)
    with pytest.raises(guard.EditGuardError, match="too many deleted lines|deletion fraction too large"):
        guard.apply_guarded_patch(
            repo, _patch("big.py", old, new),
            expected_base_sha256={"big.py": base},
            expected_head_sha=_head(repo),
            allowed_paths=["big.py"],
        )
    assert (repo / "big.py").read_text() == old


def test_rename_mode_and_new_file_operations_rejected(tmp_path):
    repo = _repo(tmp_path)
    base = _track(repo, "x.py", "x = 1\n")
    patches = [
        "diff --git a/x.py b/y.py\nsimilarity index 100%\nrename from x.py\nrename to y.py\n",
        "diff --git a/x.py b/x.py\nold mode 100644\nnew mode 100755\n",
        "diff --git a/new.py b/new.py\nnew file mode 100644\n--- /dev/null\n+++ b/new.py\n@@ -0,0 +1 @@\n+x = 1\n",
    ]
    for patch in patches:
        with pytest.raises(guard.EditGuardError):
            guard.apply_guarded_patch(
                repo, patch,
                expected_base_sha256={"x.py": base},
                expected_head_sha=_head(repo),
                allowed_paths=["x.py"],
            )


def test_verification_failure_restores_exact_bytes_and_unrelated_dirty_file(tmp_path):
    repo = _repo(tmp_path)
    old = "x = 1\n"
    new = "x = 2\n"
    base = _track(repo, "x.py", old)
    (repo / "unrelated.txt").write_text("dirty and must remain\n")
    with pytest.raises(guard.EditGuardError, match="verification failed"):
        guard.apply_and_verify_guarded_patch(
            repo, _patch("x.py", old, new),
            expected_base_sha256={"x.py": base},
            expected_head_sha=_head(repo),
            allowed_paths=["x.py"],
            verification_argv=[sys.executable, "-c", "raise SystemExit(7)"],
        )
    assert (repo / "x.py").read_text() == old
    assert guard.sha256_file(repo / "x.py") == base
    assert (repo / "unrelated.txt").read_text() == "dirty and must remain\n"


def test_verification_success_keeps_patch_and_uses_argv_not_shell(tmp_path):
    repo = _repo(tmp_path)
    old = "x = 1\n"
    new = "x = 2\n"
    base = _track(repo, "x.py", old)
    receipt = guard.apply_and_verify_guarded_patch(
        repo, _patch("x.py", old, new),
        expected_base_sha256={"x.py": base},
        expected_head_sha=_head(repo),
        allowed_paths=["x.py"],
        verification_argv=[sys.executable, "-c", "from pathlib import Path; assert Path('x.py').read_text() == 'x = 2\\n'"],
    )
    assert receipt["status"] == "APPLIED_AND_VERIFIED"
    assert receipt["verification"]["returncode"] == 0
    assert (repo / "x.py").read_text() == new


def test_extract_single_unified_diff_requires_exactly_one_payload():
    patch = "diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-x=1\n+x=2\n"
    assert guard.extract_single_unified_diff(f"```diff\n{patch}```") == patch
    with pytest.raises(guard.EditGuardError):
        guard.extract_single_unified_diff(f"note\n```diff\n{patch}```")
    with pytest.raises(guard.EditGuardError):
        guard.extract_single_unified_diff(f"```diff\n{patch}```\n```diff\n{patch}```")
