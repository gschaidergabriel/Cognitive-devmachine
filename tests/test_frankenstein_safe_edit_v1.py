import hashlib
import json
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = REPO_ROOT / "research_entity" / "topic_packets" / "frankenstein-master-cognition-concept"
sys.path.insert(0, str(PKG_DIR))

import frankenstein_safe_edit_v1 as safe


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def edit_plan(path: str, before: str, old: str, new: str):
    return {
        "schema": safe.SCHEMA,
        "files": [{
            "path": path,
            "operation": "edit",
            "base_sha256": sha(before),
            "replacements": [{"old_text": old, "new_text": new}],
        }],
    }


def test_parse_plan_accepts_plain_and_outer_json_fence():
    raw = {"schema": safe.SCHEMA, "files": [{"path": "new.py", "operation": "create", "content": "x=1\n"}]}
    text = json.dumps(raw)
    assert safe.parse_plan_json(text) == raw
    assert safe.parse_plan_json(f"```json\n{text}\n```") == raw


def test_plan_rejects_unknown_fields_and_operations():
    with pytest.raises(safe.SafeEditError):
        safe.validate_plan_shape({"schema": safe.SCHEMA, "files": [], "authority": "self-granted"})
    with pytest.raises(safe.SafeEditError):
        safe.validate_plan_shape({"schema": safe.SCHEMA, "files": [{"path": "x", "operation": "delete"}]})


def test_edit_is_hash_bound_and_preserves_untouched_regions(tmp_path):
    before = "HEADER\n" + "keep-a\n" * 20 + "TARGET = 1\n" + "keep-b\n" * 20 + "FOOTER\n"
    path = tmp_path / "mod.py"
    path.write_text(before)
    plan = edit_plan("mod.py", before, "TARGET = 1\n", "TARGET = 2\n")

    receipt = safe.apply_plan(tmp_path, plan)
    after = path.read_text()
    assert after.startswith("HEADER\n" + "keep-a\n" * 20)
    assert after.endswith("keep-b\n" * 20 + "FOOTER\n")
    assert "TARGET = 2\n" in after
    assert receipt["files"][0]["before_sha256"] == sha(before)
    assert receipt["files"][0]["after_sha256"] == sha(after)


def test_edit_rejects_stale_base_hash_without_writing(tmp_path):
    before = "a\n" * 100
    path = tmp_path / "mod.py"
    path.write_text(before)
    plan = edit_plan("mod.py", before, "a\n", "b\n")
    path.write_text(before + "concurrent-change\n")
    with pytest.raises(safe.SafeEditError, match="stale base hash"):
        safe.apply_plan(tmp_path, plan)
    assert path.read_text() == before + "concurrent-change\n"


def test_edit_rejects_ambiguous_old_text(tmp_path):
    before = "same\nsame\n" + "padding\n" * 20
    (tmp_path / "mod.py").write_text(before)
    plan = edit_plan("mod.py", before, "same\n", "changed\n")
    with pytest.raises(safe.SafeEditError, match="exactly once"):
        safe.stage_plan(tmp_path, plan)
    assert (tmp_path / "mod.py").read_text() == before


def test_edit_rejects_missing_old_text(tmp_path):
    before = "alpha\n" + "padding\n" * 30
    (tmp_path / "mod.py").write_text(before)
    plan = edit_plan("mod.py", before, "not-present\n", "changed\n")
    with pytest.raises(safe.SafeEditError, match="observed 0"):
        safe.stage_plan(tmp_path, plan)


def test_surgical_path_rejects_broad_replacement_even_if_hash_matches(tmp_path):
    before = "L" * 300 + "M" * 700
    (tmp_path / "mod.py").write_text(before)
    plan = edit_plan("mod.py", before, "L" * 300, "B" * 300)
    with pytest.raises(safe.SafeEditError, match="edit span too broad"):
        safe.stage_plan(tmp_path, plan)
    assert (tmp_path / "mod.py").read_text() == before


def test_create_refuses_existing_file(tmp_path):
    (tmp_path / "existing.py").write_text("old\n")
    plan = {"schema": safe.SCHEMA, "files": [{"path": "existing.py", "operation": "create", "content": "new\n"}]}
    with pytest.raises(safe.SafeEditError, match="already exists"):
        safe.stage_plan(tmp_path, plan)
    assert (tmp_path / "existing.py").read_text() == "old\n"


def test_paths_fail_closed_on_traversal_absolute_and_symlink(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "x.py").write_text("x\n")

    for bad in ("../outside/x.py", str(outside / "x.py"), "a/../b.py"):
        plan = {"schema": safe.SCHEMA, "files": [{"path": bad, "operation": "create", "content": "x\n"}]}
        with pytest.raises(safe.SafeEditError):
            safe.stage_plan(repo, plan)

    link = repo / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    plan = {"schema": safe.SCHEMA, "files": [{"path": "link/new.py", "operation": "create", "content": "x\n"}]}
    with pytest.raises(safe.SafeEditError, match="symlink"):
        safe.stage_plan(repo, plan)


def test_entire_plan_stages_before_first_write(tmp_path):
    first_before = "needle\n" + "keep\n" * 100
    second_before = "other\n" + "keep\n" * 100
    (tmp_path / "first.py").write_text(first_before)
    (tmp_path / "second.py").write_text(second_before)
    plan = {
        "schema": safe.SCHEMA,
        "files": [
            {
                "path": "first.py", "operation": "edit", "base_sha256": sha(first_before),
                "replacements": [{"old_text": "needle\n", "new_text": "needle2\n"}],
            },
            {
                "path": "second.py", "operation": "edit", "base_sha256": "0" * 64,
                "replacements": [{"old_text": "other\n", "new_text": "other2\n"}],
            },
        ],
    }
    with pytest.raises(safe.SafeEditError, match="stale base hash"):
        safe.apply_plan(tmp_path, plan)
    assert (tmp_path / "first.py").read_text() == first_before
    assert (tmp_path / "second.py").read_text() == second_before


def test_apply_rolls_back_already_written_files_if_later_write_fails(tmp_path, monkeypatch):
    first_before = "needle\n" + "keep\n" * 100
    (tmp_path / "first.py").write_text(first_before)
    plan = {
        "schema": safe.SCHEMA,
        "files": [
            {
                "path": "first.py", "operation": "edit", "base_sha256": sha(first_before),
                "replacements": [{"old_text": "needle\n", "new_text": "needle2\n"}],
            },
            {"path": "second.py", "operation": "create", "content": "created\n"},
        ],
    }
    real = safe._atomic_write_text
    calls = {"n": 0}

    def flaky(path: Path, content: str):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("synthetic write failure")
        return real(path, content)

    monkeypatch.setattr(safe, "_atomic_write_text", flaky)
    with pytest.raises(safe.SafeEditError, match="rollback attempted"):
        safe.apply_plan(tmp_path, plan)
    assert (tmp_path / "first.py").read_text() == first_before
    assert not (tmp_path / "second.py").exists()


def test_snapshot_for_prompt_binds_content_to_hash(tmp_path):
    content = "line1\nline2\n"
    (tmp_path / "x.py").write_text(content)
    snap = safe.snapshot_for_prompt(tmp_path, ["x.py"])
    assert snap == [{"path": "x.py", "sha256": sha(content), "content": content}]
