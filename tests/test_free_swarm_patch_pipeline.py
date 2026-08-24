from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import free_swarm_patch_pipeline as pipe  # noqa: E402


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(
        ["git", *args], cwd=repo, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return p.stdout.strip()


def make_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "patch@example.invalid")
    git(repo, "config", "user.name", "patch test")
    (repo / "sample.py").write_text(
        "value = 1\nname = 'old'\nflag = False\n", encoding="utf-8"
    )
    git(repo, "add", "sample.py")
    git(repo, "commit", "-q", "-m", "source")
    return repo, git(repo, "rev-parse", "HEAD")


def test_rehydrate_adapter_binds_exact_source(tmp_path):
    repo, source = make_repo(tmp_path)
    got = pipe.rehydrate_targets(repo, source, ["sample.py"], per_file_chars=5000)
    assert got["ok"] is True
    assert got["source_head"] == source
    assert got["execution_state"] == "EXECUTION_BLOCKED"
    assert got["files"][0]["git_blob"] == git(repo, "rev-parse", f"{source}:sample.py")
    assert "value = 1" in got["files"][0]["content"]


def test_rehydrate_adapter_rejects_path_escape(tmp_path):
    repo, source = make_repo(tmp_path)
    got = pipe.rehydrate_targets(repo, source, ["../secret.txt"])
    assert got["ok"] is False
    assert got["reason"] == "UNSAFE_TARGET_PATH"


def test_valid_patch_passes_without_repair(tmp_path):
    repo, source = make_repo(tmp_path)
    patch = (
        "diff --git a/sample.py b/sample.py\n"
        "--- a/sample.py\n"
        "+++ b/sample.py\n"
        "@@ -1,3 +1,3 @@\n"
        "-value = 1\n"
        "+value = 2\n"
        " name = 'old'\n"
        " flag = False\n"
    )
    got = pipe.normalize_patch_against_source(repo, source, patch, ["sample.py"])
    assert got["ok"] is True
    assert got["repair_mode"] == "NONE"
    assert got["patch"] == patch


def test_bad_hunk_counts_recount_then_standard_recheck(tmp_path):
    repo, source = make_repo(tmp_path)
    patch = (
        "diff --git a/sample.py b/sample.py\n"
        "--- a/sample.py\n"
        "+++ b/sample.py\n"
        "@@ -1,9 +1,9 @@\n"
        "-value = 1\n"
        "+value = 2\n"
        " name = 'old'\n"
        " flag = False\n"
    )
    got = pipe.normalize_patch_against_source(repo, source, patch, ["sample.py"])
    assert got["ok"] is True
    assert got["repair_mode"] == "RECOUNT_NORMALIZED"
    assert "@@ -1,3 +1,3 @@" in got["patch"]
    assert "@@ -1,9 +1,9 @@" not in got["patch"]


def test_context_mismatch_is_not_fuzzy_repaired(tmp_path):
    repo, source = make_repo(tmp_path)
    patch = (
        "diff --git a/sample.py b/sample.py\n"
        "--- a/sample.py\n"
        "+++ b/sample.py\n"
        "@@ -1,3 +1,3 @@\n"
        "-value = 999\n"
        "+value = 2\n"
        " name = 'old'\n"
        " flag = False\n"
    )
    got = pipe.normalize_patch_against_source(repo, source, patch, ["sample.py"])
    assert got["ok"] is False
    assert got["reason"] == "PATCH_APPLY_REJECTED"
    assert got["repair_mode"] == "NONE"


def test_patch_target_set_must_equal_stage1_targets(tmp_path):
    repo, source = make_repo(tmp_path)
    patch = (
        "diff --git a/sample.py b/sample.py\n"
        "--- a/sample.py\n"
        "+++ b/sample.py\n"
        "@@ -1 +1 @@\n"
        "-value = 1\n"
        "+value = 2\n"
    )
    got = pipe.normalize_patch_against_source(
        repo, source, patch, ["sample.py", "other.py"]
    )
    assert got["ok"] is False
    assert got["reason"] == "PATCH_TARGET_SET_MISMATCH"


def test_stage2_prompt_binds_source_and_forces_fail_closed_default(tmp_path):
    repo, source = make_repo(tmp_path)
    proposal = {
        "delta_id": "d",
        "hypothesis": "h",
        "target_files": ["sample.py"],
        "test_commands": ["true"],
        "falsifier": "f",
        "patch_unified_diff": "invented",
        "ready_for_forge": True,
    }
    binding = pipe.rehydrate_targets(repo, source, ["sample.py"])
    prompt = pipe.stage2_prompt("PROTOCOL", proposal, binding)
    assert source in prompt
    assert binding["files"][0]["git_blob"] in prompt
    assert "value = 1" in prompt
    assert '"patch_unified_diff":""' in prompt
    assert '"ready_for_forge":false' in prompt


def test_architecture_delta_canonicalization_can_force_ready_false():
    text = (
        "DEUTSCHE_ZUSAMMENFASSUNG\n"
        'ARCHITECTURE_DELTA_JSON={"delta_id":"d","target_files":["sample.py"],'
        '"patch_unified_diff":"bad","test_commands":["true"],'
        '"falsifier":"fails","ready_for_forge":true}\n'
        'OPEN_RESEARCH_QUESTIONS_JSON=[]\n'
    )
    obj = pipe.architecture_delta(text)
    assert obj is not None
    obj["ready_for_forge"] = False
    obj["patch_pipeline_stage"] = "APPLY_CHECK_BLOCKED"
    updated = pipe.canonicalize_architecture_delta(text, obj)
    reparsed = pipe.architecture_delta(updated)
    assert reparsed is not None
    assert reparsed["ready_for_forge"] is False
    assert reparsed["patch_pipeline_stage"] == "APPLY_CHECK_BLOCKED"
