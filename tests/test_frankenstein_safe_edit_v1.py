import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept" / "frankenstein_safe_edit_v1.py"
spec = importlib.util.spec_from_file_location("frankenstein_safe_edit_v1", MODULE_PATH)
safe = importlib.util.module_from_spec(spec)
sys.modules["frankenstein_safe_edit_v1"] = safe
spec.loader.exec_module(safe)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def test_parse_edit_and_new_file_blocks():
    response = """EDIT: tools/a.py
<<<<<<< SEARCH
x = 1
=======
x = 2
>>>>>>> REPLACE

NEW_FILE: tests/test_a.py
```python
assert True
```
"""
    edits, new_files = safe.parse_safe_edit_response(response)
    assert edits == [safe.EditBlock("tools/a.py", "x = 1", "x = 2")]
    assert new_files == [safe.NewFileBlock("tests/test_a.py", "assert True")]


def test_exact_edit_preserves_everything_outside_declared_span(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "mod.py"
    original = "header\nalpha = 1\nmiddle\nbeta = 2\nfooter\n"
    target.write_text(original)
    block = safe.EditBlock("mod.py", "beta = 2", "beta = 3\nextra = 4")
    plan = safe.plan_safe_edits(repo, [block])
    receipt = safe.apply_safe_edit_plan(plan)
    result = target.read_text()
    assert result == "header\nalpha = 1\nmiddle\nbeta = 3\nextra = 4\nfooter\n"
    row = receipt["existing_file_edits"][0]
    assert row["original_sha256"] == sha(original)
    assert row["result_sha256"] == sha(result)
    assert row["unchanged_chars"] == len(original) - len("beta = 2")
    assert receipt["scope"] == "EXACT_LOCAL_TEXT_TRANSFORM_ONLY"


def test_search_must_be_unique_in_original(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("same\nsame\n")
    with pytest.raises(safe.SafeEditError, match="exactly once"):
        safe.plan_safe_edits(repo, [safe.EditBlock("a.py", "same", "changed")])


def test_overlapping_search_spans_are_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("abcdefghi\n")
    edits = [
        safe.EditBlock("a.py", "cdef", "X"),
        safe.EditBlock("a.py", "efgh", "Y"),
    ]
    with pytest.raises(safe.SafeEditError, match="overlapping"):
        safe.plan_safe_edits(repo, edits, policy=safe.SafeEditPolicy(max_replaced_fraction=0.9))


def test_default_policy_rejects_rewriting_most_of_existing_file(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    original = "A" * 100 + "B" * 100
    (repo / "big.txt").write_text(original)
    with pytest.raises(safe.SafeEditError, match="budget exceeded"):
        safe.plan_safe_edits(repo, [safe.EditBlock("big.txt", "A" * 100 + "B" * 20, "tiny")])


def test_minimal_change_to_small_file_is_allowed(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("x=1\n")
    plan = safe.plan_safe_edits(repo, [safe.EditBlock("a.py", "1", "2")])
    safe.apply_safe_edit_plan(plan)
    assert (repo / "a.py").read_text() == "x=2\n"


def test_full_file_replacement_is_rejected_by_default_budget(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("x=1\n")
    with pytest.raises(safe.SafeEditError, match="budget exceeded"):
        safe.plan_safe_edits(repo, [safe.EditBlock("a.py", "x=1\n", "totally different\n")])


def test_path_escape_is_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("secret\n")
    with pytest.raises(safe.SafeEditError, match="escapes repo_root"):
        safe.plan_safe_edits(repo, [safe.EditBlock("../outside.py", "secret", "oops")])


def test_symlink_escape_is_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("secret\n")
    (repo / "link.py").symlink_to(outside)
    with pytest.raises(safe.SafeEditError, match="escapes repo_root"):
        safe.plan_safe_edits(repo, [safe.EditBlock("link.py", "secret", "oops")])


def test_new_file_must_not_already_exist(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "a.py").write_text("old\n")
    with pytest.raises(safe.SafeEditError, match="already exists"):
        safe.plan_safe_edits(repo, [], [safe.NewFileBlock("a.py", "new")])


def test_new_file_is_created_and_receipted(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    plan = safe.plan_safe_edits(repo, [], [safe.NewFileBlock("new.py", "x = 1")])
    receipt = safe.apply_safe_edit_plan(plan)
    assert (repo / "new.py").read_text() == "x = 1"
    assert receipt["new_files"][0]["result_sha256"] == sha("x = 1")


def test_stale_preimage_fails_closed_before_write(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "a.py"
    target.write_text("x=1\ny=2\n")
    plan = safe.plan_safe_edits(repo, [safe.EditBlock("a.py", "1", "9")])
    target.write_text("x=7\ny=2\n")
    with pytest.raises(safe.StalePreimageError, match="changed after planning"):
        safe.apply_safe_edit_plan(plan)
    assert target.read_text() == "x=7\ny=2\n"


def test_multiple_nonoverlapping_edits_use_original_offsets(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    target = repo / "a.txt"
    target.write_text("aa 11 bb 22 cc 33 dd")
    edits = [
        safe.EditBlock("a.txt", "11", "ONE-LONG"),
        safe.EditBlock("a.txt", "33", "THREE"),
    ]
    plan = safe.plan_safe_edits(repo, edits)
    safe.apply_safe_edit_plan(plan)
    assert target.read_text() == "aa ONE-LONG bb 22 cc THREE dd"


def test_no_blocks_is_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(safe.SafeEditError, match="no EDIT or NEW_FILE"):
        safe.plan_safe_edits(repo, [], [])
