from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

MODULE_DIR = Path(__file__).resolve().parents[1] / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from frankenstein_patch_guard_v1 import PatchGuardError, PatchPolicy, preflight_patch


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)
    return proc.stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Patch Guard Test")
    (repo / "tools").mkdir()
    (repo / "tools" / "grid10_fabric.py").write_text(
        "def keep_a():\n    return 'a'\n\n"
        "def keep_b():\n    return 'b'\n\n"
        "def keep_c():\n    return 'c'\n"
    )
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "base")
    return repo


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def policy(repo: Path, *, allowed=("tools/grid10_fabric.py",), base=None, **kwargs) -> PatchPolicy:
    if base is None:
        base = {p: sha256(repo / p) for p in allowed}
    return PatchPolicy(
        expected_head=git(repo, "rev-parse", "HEAD"),
        allowed_paths=tuple(allowed),
        expected_base_sha256=base,
        **kwargs,
    )


def test_valid_small_patch_passes_without_applying(tmp_path):
    repo = make_repo(tmp_path)
    original = (repo / "tools" / "grid10_fabric.py").read_text()
    patch = """diff --git a/tools/grid10_fabric.py b/tools/grid10_fabric.py
--- a/tools/grid10_fabric.py
+++ b/tools/grid10_fabric.py
@@ -7,2 +7,5 @@ def keep_c():
 def keep_c():
     return 'c'
+
+def added_table():
+    return {'ok': True}
"""
    report = preflight_patch(repo, patch, policy(repo))
    assert report["applied"] is False
    assert report["git_apply_check_index"] == "PASS"
    assert report["totals"]["deleted_lines"] == 0
    assert (repo / "tools" / "grid10_fabric.py").read_text() == original


def test_wrong_head_fails_closed(tmp_path):
    repo = make_repo(tmp_path)
    p = policy(repo)
    bad = PatchPolicy(
        expected_head="0" * 40,
        allowed_paths=p.allowed_paths,
        expected_base_sha256=p.expected_base_sha256,
    )
    with pytest.raises(PatchGuardError, match="HEAD mismatch"):
        preflight_patch(repo, "not even parsed", bad)


def test_base_digest_mismatch_fails_closed(tmp_path):
    repo = make_repo(tmp_path)
    p = policy(repo, base={"tools/grid10_fabric.py": "0" * 64})
    patch = """diff --git a/tools/grid10_fabric.py b/tools/grid10_fabric.py
--- a/tools/grid10_fabric.py
+++ b/tools/grid10_fabric.py
@@ -1,2 +1,2 @@
 def keep_a():
-    return 'a'
+    return 'A'
"""
    with pytest.raises(PatchGuardError, match="base SHA-256 mismatch"):
        preflight_patch(repo, patch, p)


def test_unauthorized_path_fails_closed(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "other.py").write_text("x = 1\n")
    git(repo, "add", "other.py")
    git(repo, "commit", "-qm", "other")
    patch = """diff --git a/other.py b/other.py
--- a/other.py
+++ b/other.py
@@ -1 +1 @@
-x = 1
+x = 2
"""
    with pytest.raises(PatchGuardError, match="unauthorized"):
        preflight_patch(repo, patch, policy(repo))


def test_deletion_budget_blocks_padded_whole_file_rewrite(tmp_path):
    repo = make_repo(tmp_path)
    old = (repo / "tools" / "grid10_fabric.py").read_text().splitlines()
    patch_lines = [
        "diff --git a/tools/grid10_fabric.py b/tools/grid10_fabric.py",
        "--- a/tools/grid10_fabric.py",
        "+++ b/tools/grid10_fabric.py",
        f"@@ -1,{len(old)} +1,20 @@",
    ]
    patch_lines += ["-" + line for line in old]
    patch_lines += ["+padding_%02d = None" % i for i in range(20)]
    patch = "\n".join(patch_lines) + "\n"
    with pytest.raises(PatchGuardError, match="deletion budget exceeded"):
        preflight_patch(repo, patch, policy(repo, max_deleted_lines=2, max_total_changed_lines=100))


def test_dirty_touched_path_fails_git_index_check_even_if_policy_digest_matches_dirty_file(tmp_path):
    repo = make_repo(tmp_path)
    path = repo / "tools" / "grid10_fabric.py"
    path.write_text(path.read_text() + "\n# concurrent local change\n")
    dirty_digest = sha256(path)
    p = policy(repo, base={"tools/grid10_fabric.py": dirty_digest})
    patch = """diff --git a/tools/grid10_fabric.py b/tools/grid10_fabric.py
--- a/tools/grid10_fabric.py
+++ b/tools/grid10_fabric.py
@@ -1,2 +1,2 @@
 def keep_a():
-    return 'a'
+    return 'A'
"""
    with pytest.raises(PatchGuardError, match="git apply --check --index"):
        preflight_patch(repo, patch, p)


def test_new_file_can_be_explicitly_allowed(tmp_path):
    repo = make_repo(tmp_path)
    patch = """diff --git a/tools/new_helper.py b/tools/new_helper.py
new file mode 100644
--- /dev/null
+++ b/tools/new_helper.py
@@ -0,0 +1,2 @@
+def hello():
+    return 'hi'
"""
    p = policy(
        repo,
        allowed=("tools/new_helper.py",),
        base={"tools/new_helper.py": None},
        max_deleted_lines=0,
    )
    report = preflight_patch(repo, patch, p)
    assert report["files"][0]["base"]["exists"] is False
    assert not (repo / "tools" / "new_helper.py").exists()


def test_file_delete_is_forbidden(tmp_path):
    repo = make_repo(tmp_path)
    old = (repo / "tools" / "grid10_fabric.py").read_text().splitlines()
    patch = "\n".join([
        "diff --git a/tools/grid10_fabric.py b/tools/grid10_fabric.py",
        "deleted file mode 100644",
        "--- a/tools/grid10_fabric.py",
        "+++ /dev/null",
        f"@@ -1,{len(old)} +0,0 @@",
        *["-" + line for line in old],
        "",
    ])
    with pytest.raises(PatchGuardError, match="file deletion"):
        preflight_patch(repo, patch, policy(repo, max_deleted_lines=100))


def test_rename_is_forbidden(tmp_path):
    repo = make_repo(tmp_path)
    patch = """diff --git a/tools/grid10_fabric.py b/tools/grid10_fabric_renamed.py
similarity index 100%
rename from tools/grid10_fabric.py
rename to tools/grid10_fabric_renamed.py
"""
    with pytest.raises(PatchGuardError, match="rename/copy"):
        preflight_patch(repo, patch, policy(repo))


def test_existing_file_mode_change_is_forbidden(tmp_path):
    repo = make_repo(tmp_path)
    patch = """diff --git a/tools/grid10_fabric.py b/tools/grid10_fabric.py
old mode 100644
new mode 100755
"""
    with pytest.raises(PatchGuardError, match="mode changes"):
        preflight_patch(repo, patch, policy(repo))


def test_new_symlink_mode_is_forbidden(tmp_path):
    repo = make_repo(tmp_path)
    patch = """diff --git a/tools/new_link b/tools/new_link
new file mode 120000
--- /dev/null
+++ b/tools/new_link
@@ -0,0 +1 @@
+../outside
"""
    p = policy(
        repo,
        allowed=("tools/new_link",),
        base={"tools/new_link": None},
    )
    with pytest.raises(PatchGuardError, match="regular non-executable"):
        preflight_patch(repo, patch, p)


def test_control_character_policy_path_is_forbidden(tmp_path):
    repo = make_repo(tmp_path)
    p = PatchPolicy(
        expected_head=git(repo, "rev-parse", "HEAD"),
        allowed_paths=("tools/bad\nname.py",),
        expected_base_sha256={"tools/bad\nname.py": None},
    )
    with pytest.raises(PatchGuardError, match="unsafe path spelling"):
        preflight_patch(repo, "not parsed yet", p)
