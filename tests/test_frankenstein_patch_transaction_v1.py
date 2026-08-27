from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

MODULE_DIR = Path(__file__).resolve().parents[1] / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from frankenstein_patch_guard_v1 import PatchGuardError, PatchPolicy
from frankenstein_patch_transaction_v1 import PatchTransactionError, apply_verified_patch


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Patch Transaction Test")
    (repo / "x.py").write_text("x = 1\n")
    git(repo, "add", "x.py")
    git(repo, "commit", "-qm", "base")
    return repo


def existing_policy(repo: Path) -> PatchPolicy:
    return PatchPolicy(
        expected_head=git(repo, "rev-parse", "HEAD"),
        allowed_paths=("x.py",),
        expected_base_sha256={"x.py": sha256(repo / "x.py")},
        max_deleted_lines=10,
        max_total_changed_lines=20,
    )


def existing_patch() -> str:
    return """diff --git a/x.py b/x.py
--- a/x.py
+++ b/x.py
@@ -1 +1 @@
-x = 1
+x = 2
"""


def new_file_patch() -> str:
    return """diff --git a/new.py b/new.py
new file mode 100644
--- /dev/null
+++ b/new.py
@@ -0,0 +1 @@
+value = 7
"""


def test_existing_patch_applies_verifies_and_is_not_committed(tmp_path):
    repo = make_repo(tmp_path)
    receipt = apply_verified_patch(
        repo,
        existing_patch(),
        existing_policy(repo),
        verification_argv=[sys.executable, "-c", "from pathlib import Path; assert Path('x.py').read_text() == 'x = 2\\n'"],
    )
    assert (repo / "x.py").read_text() == "x = 2\n"
    assert receipt["status"] == "APPLIED_AND_VERIFIED_NOT_COMMITTED"
    assert receipt["commit_performed"] is False
    assert receipt["git_apply_check_index"] == "PASS"
    assert git(repo, "diff", "--name-only") == "x.py"
    assert git(repo, "diff", "--cached", "--name-only") == ""


def test_verification_failure_restores_exact_existing_bytes_and_unrelated_dirty_file(tmp_path):
    repo = make_repo(tmp_path)
    before = (repo / "x.py").read_bytes()
    (repo / "unrelated.txt").write_text("keep me dirty\n")
    with pytest.raises(PatchTransactionError, match="verification failed"):
        apply_verified_patch(
            repo,
            existing_patch(),
            existing_policy(repo),
            verification_argv=[sys.executable, "-c", "raise SystemExit(9)"],
        )
    assert (repo / "x.py").read_bytes() == before
    assert (repo / "unrelated.txt").read_text() == "keep me dirty\n"


def test_explicit_new_file_applies_and_verifies(tmp_path):
    repo = make_repo(tmp_path)
    policy = PatchPolicy(
        expected_head=git(repo, "rev-parse", "HEAD"),
        allowed_paths=("new.py",),
        expected_base_sha256={"new.py": None},
        max_deleted_lines=0,
    )
    receipt = apply_verified_patch(
        repo,
        new_file_patch(),
        policy,
        verification_argv=[sys.executable, "-c", "import new; assert new.value == 7"],
    )
    assert (repo / "new.py").read_text() == "value = 7\n"
    assert receipt["files"][0]["before_sha256"] is None


def test_failed_new_file_verification_removes_new_file(tmp_path):
    repo = make_repo(tmp_path)
    policy = PatchPolicy(
        expected_head=git(repo, "rev-parse", "HEAD"),
        allowed_paths=("new.py",),
        expected_base_sha256={"new.py": None},
        max_deleted_lines=0,
    )
    with pytest.raises(PatchTransactionError, match="verification failed"):
        apply_verified_patch(
            repo,
            new_file_patch(),
            policy,
            verification_argv=[sys.executable, "-c", "raise SystemExit(3)"],
        )
    assert not (repo / "new.py").exists()


def test_wrong_head_is_rejected_by_canonical_preflight_before_mutation(tmp_path):
    repo = make_repo(tmp_path)
    p = existing_policy(repo)
    wrong = PatchPolicy(
        expected_head="0" * 40,
        allowed_paths=p.allowed_paths,
        expected_base_sha256=p.expected_base_sha256,
    )
    with pytest.raises(PatchGuardError, match="HEAD mismatch"):
        apply_verified_patch(
            repo,
            existing_patch(),
            wrong,
            verification_argv=[sys.executable, "-c", "raise AssertionError('must not run')"],
        )
    assert (repo / "x.py").read_text() == "x = 1\n"


def test_dirty_touched_path_is_rejected_by_canonical_index_preflight(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "x.py").write_text("x = 1\n# dirty\n")
    p = PatchPolicy(
        expected_head=git(repo, "rev-parse", "HEAD"),
        allowed_paths=("x.py",),
        expected_base_sha256={"x.py": sha256(repo / "x.py")},
    )
    with pytest.raises(PatchGuardError, match="git apply --check --index"):
        apply_verified_patch(
            repo,
            existing_patch(),
            p,
            verification_argv=[sys.executable, "-c", "raise AssertionError('must not run')"],
        )


def test_verification_receipt_does_not_copy_raw_output_or_argv(tmp_path):
    repo = make_repo(tmp_path)
    secret_like = "DO_NOT_COPY_THIS_SENTINEL"
    receipt = apply_verified_patch(
        repo,
        existing_patch(),
        existing_policy(repo),
        verification_argv=[sys.executable, "-c", f"print({secret_like!r})"],
    )
    rendered = repr(receipt)
    assert secret_like not in rendered
    assert receipt["verification"]["stdout_bytes"] > 0
    assert len(receipt["verification"]["stdout_sha256"]) == 64
    assert len(receipt["verification"]["argv_sha256"]) == 64


def test_failed_verification_error_does_not_copy_raw_output(tmp_path):
    repo = make_repo(tmp_path)
    secret_like = "DO_NOT_COPY_FAILURE_SENTINEL"
    with pytest.raises(PatchTransactionError) as exc:
        apply_verified_patch(
            repo,
            existing_patch(),
            existing_policy(repo),
            verification_argv=[sys.executable, "-c", f"import sys; print({secret_like!r}, file=sys.stderr); raise SystemExit(4)"],
        )
    assert secret_like not in str(exc.value)
    assert (repo / "x.py").read_text() == "x = 1\n"
