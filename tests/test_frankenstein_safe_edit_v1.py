from __future__ import annotations

import hashlib
from pathlib import Path
import sys

import pytest

TOPIC_DIR = (
    Path(__file__).resolve().parents[1]
    / "research_entity"
    / "topic_packets"
    / "frankenstein-master-cognition-concept"
)
sys.path.insert(0, str(TOPIC_DIR))

from frankenstein_safe_edit_v1 import (  # noqa: E402
    EditPolicy,
    PatchSyntaxError,
    PathViolation,
    PolicyViolation,
    SourceChanged,
    commit_plan,
    plan_unified_patch,
    snapshot_sha256,
)


def _write(root: Path, rel: str, text: str) -> Path:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    return target


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def test_valid_patch_preserves_unrelated_regions_and_commits_atomically(tmp_path: Path) -> None:
    original = "alpha\nbeta\ngamma\ndelta\n"
    target = _write(tmp_path, "tools/x.py", original)
    patch = """--- a/tools/x.py
+++ b/tools/x.py
@@ -1,4 +1,5 @@
 alpha
-beta
+BETA
 gamma
 delta
+epsilon
"""
    plan = plan_unified_patch(tmp_path, "tools/x.py", _sha(original), patch)
    assert plan.deleted_old_lines == 1
    assert plan.added_new_lines == 2
    assert plan.preserved_old_lines == 3
    assert target.read_text() == original

    receipt = commit_plan(tmp_path, plan)
    assert receipt["committed"] is True
    assert target.read_text() == "alpha\nBETA\ngamma\ndelta\nepsilon\n"
    assert snapshot_sha256(tmp_path, "tools/x.py") == plan.after_sha256


def test_wrong_preimage_hash_fails_closed(tmp_path: Path) -> None:
    _write(tmp_path, "x.txt", "a\nb\n")
    patch = """--- a/x.txt
+++ b/x.txt
@@ -1,2 +1,2 @@
 a
-b
+B
"""
    with pytest.raises(SourceChanged):
        plan_unified_patch(tmp_path, "x.txt", "0" * 64, patch)


def test_strict_context_mismatch_fails_closed(tmp_path: Path) -> None:
    original = "a\nb\nc\n"
    _write(tmp_path, "x.txt", original)
    patch = """--- a/x.txt
+++ b/x.txt
@@ -1,3 +1,3 @@
 a
-WRONG
+B
 c
"""
    with pytest.raises(PatchSyntaxError, match="context mismatch"):
        plan_unified_patch(tmp_path, "x.txt", _sha(original), patch)


def test_patch_target_must_equal_declared_target(tmp_path: Path) -> None:
    original = "a\nb\n"
    _write(tmp_path, "x.txt", original)
    patch = """--- a/y.txt
+++ b/y.txt
@@ -1,2 +1,2 @@
 a
-b
+B
"""
    with pytest.raises(PolicyViolation, match="target mismatch"):
        plan_unified_patch(tmp_path, "x.txt", _sha(original), patch)


def test_repo_escape_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("x\n")
    patch = """--- a/../outside.txt
+++ b/../outside.txt
@@ -1 +1 @@
-x
+y
"""
    with pytest.raises(PathViolation):
        plan_unified_patch(tmp_path, "../outside.txt", _sha("x\n"), patch)


def test_rename_is_rejected(tmp_path: Path) -> None:
    original = "a\n"
    _write(tmp_path, "x.txt", original)
    patch = """--- a/x.txt
+++ b/y.txt
@@ -1 +1 @@
-a
+A
"""
    with pytest.raises(PolicyViolation, match="renames"):
        plan_unified_patch(tmp_path, "x.txt", _sha(original), patch)


def test_massive_672_to_87_style_rewrite_is_rejected_even_with_correct_hash(tmp_path: Path) -> None:
    old_lines = [f"old_{i}" for i in range(672)]
    new_lines = [f"fabricated_{i}" for i in range(87)]
    original = "\n".join(old_lines) + "\n"
    _write(tmp_path, "tools/grid10_fabric.py", original)
    body = "\n".join([*(f"-{line}" for line in old_lines), *(f"+{line}" for line in new_lines)])
    patch = (
        "--- a/tools/grid10_fabric.py\n"
        "+++ b/tools/grid10_fabric.py\n"
        f"@@ -1,672 +1,87 @@\n{body}\n"
    )
    with pytest.raises(PolicyViolation, match="deletion budget exceeded"):
        plan_unified_patch(
            tmp_path,
            "tools/grid10_fabric.py",
            _sha(original),
            patch,
            policy=EditPolicy(max_deleted_fraction=0.25),
        )


def test_similar_size_whole_file_rewrite_is_also_rejected(tmp_path: Path) -> None:
    old_lines = [f"old_{i:03d}" for i in range(20)]
    new_lines = [f"new_{i:03d}" for i in range(20)]
    original = "\n".join(old_lines) + "\n"
    _write(tmp_path, "x.txt", original)
    body = "\n".join([*(f"-{line}" for line in old_lines), *(f"+{line}" for line in new_lines)])
    patch = f"--- a/x.txt\n+++ b/x.txt\n@@ -1,20 +1,20 @@\n{body}\n"
    with pytest.raises(PolicyViolation, match="deletion budget exceeded"):
        plan_unified_patch(tmp_path, "x.txt", _sha(original), patch)


def test_multiple_hunks_preserve_middle_region(tmp_path: Path) -> None:
    original = "a\nb\nc\nd\ne\nf\n"
    _write(tmp_path, "x.txt", original)
    patch = """--- a/x.txt
+++ b/x.txt
@@ -1,2 +1,2 @@
 a
-b
+B
@@ -5,2 +5,2 @@
 e
-f
+F
"""
    plan = plan_unified_patch(
        tmp_path,
        "x.txt",
        _sha(original),
        patch,
        policy=EditPolicy(max_deleted_fraction=0.40),
    )
    assert plan.untouched_old_lines == 2
    assert plan.context_old_lines == 2
    commit_plan(tmp_path, plan)
    assert (tmp_path / "x.txt").read_text() == "a\nB\nc\nd\ne\nF\n"


def test_plan_is_invalidated_by_toctou_source_change(tmp_path: Path) -> None:
    original = "a\nb\nc\n"
    target = _write(tmp_path, "x.txt", original)
    patch = """--- a/x.txt
+++ b/x.txt
@@ -1,3 +1,3 @@
 a
-b
+B
 c
"""
    plan = plan_unified_patch(
        tmp_path, "x.txt", _sha(original), patch, policy=EditPolicy(max_deleted_fraction=0.50)
    )
    target.write_text("a\nexternal-change\nc\n")
    with pytest.raises(SourceChanged, match="changed after planning"):
        commit_plan(tmp_path, plan)


def test_noop_patch_is_rejected(tmp_path: Path) -> None:
    original = "a\nb\n"
    _write(tmp_path, "x.txt", original)
    patch = """--- a/x.txt
+++ b/x.txt
@@ -1,2 +1,2 @@
 a
 b
"""
    with pytest.raises(PolicyViolation, match="no-op"):
        plan_unified_patch(tmp_path, "x.txt", _sha(original), patch)


def test_hunk_declared_counts_are_verified(tmp_path: Path) -> None:
    original = "a\nb\n"
    _write(tmp_path, "x.txt", original)
    patch = """--- a/x.txt
+++ b/x.txt
@@ -1,2 +1,2 @@
 a
-b
+B
+EXTRA
"""
    with pytest.raises(PatchSyntaxError, match="hunk count mismatch"):
        plan_unified_patch(tmp_path, "x.txt", _sha(original), patch)
