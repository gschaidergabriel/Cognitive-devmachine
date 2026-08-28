from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import forge_source_rehydration as fsr  # noqa: E402


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(
        ["git", *args], cwd=repo, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return p.stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "r"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "test")
    (repo / "tools").mkdir()
    (repo / "tools" / "x.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "base")
    return repo


def proposal(**overrides):
    obj = {
        "delta_id": "d1",
        "hypothesis": "h",
        "mechanism": "m",
        "target_files": ["tools/x.py"],
        "test_commands": ["python3 -m pytest -q tests/test_x.py"],
        "patch_unified_diff": "",
        "falsifier": "f",
    }
    obj.update(overrides)
    return obj


def test_rehydrates_exact_committed_blob_and_blocks_execution(tmp_path):
    repo = make_repo(tmp_path)
    got = fsr.rehydrate_candidate(repo, proposal())
    assert got["schema"] == fsr.SCHEMA
    assert got["context_state"] == "CONTEXT_READY"
    assert got["execution_state"] == "EXECUTION_BLOCKED"
    assert got["model_commands_executed"] == 0
    assert got["files"][0]["content"] == "VALUE = 1\n"
    assert got["files"][0]["blob_sha"] == git(repo, "rev-parse", "HEAD:tools/x.py")


def test_worktree_mutation_does_not_change_rehydrated_source(tmp_path):
    repo = make_repo(tmp_path)
    first = fsr.rehydrate_candidate(repo, proposal())
    (repo / "tools" / "x.py").write_text("VALUE = 999\n", encoding="utf-8")
    second = fsr.rehydrate_candidate(repo, proposal())
    assert second["files"][0]["content"] == "VALUE = 1\n"
    assert second["binding_sha256"] == first["binding_sha256"]


def test_explicit_source_commit_survives_head_movement(tmp_path):
    repo = make_repo(tmp_path)
    old = git(repo, "rev-parse", "HEAD")
    old_blob = git(repo, "rev-parse", f"{old}:tools/x.py")
    (repo / "tools" / "x.py").write_text("VALUE = 2\n", encoding="utf-8")
    git(repo, "add", "tools/x.py")
    git(repo, "commit", "-q", "-m", "move head")
    assert git(repo, "rev-parse", "HEAD") != old

    got = fsr.rehydrate_candidate(repo, proposal(), source_commit=old)
    assert got["source"]["commit"] == old
    assert got["files"][0]["blob_sha"] == old_blob
    assert got["files"][0]["content"] == "VALUE = 1\n"


def test_rejects_non_exact_source_commit(tmp_path):
    repo = make_repo(tmp_path)
    with pytest.raises(fsr.RehydrationError):
        fsr.rehydrate_candidate(repo, proposal(), source_commit="HEAD")


def test_rejects_path_escape_and_duplicates(tmp_path):
    repo = make_repo(tmp_path)
    with pytest.raises(fsr.RehydrationError):
        fsr.rehydrate_candidate(repo, proposal(target_files=["../secret"]))
    with pytest.raises(fsr.RehydrationError):
        fsr.rehydrate_candidate(repo, proposal(target_files=["README.md", "README.md"]))


def test_packet_binds_candidate_source_and_blob(tmp_path):
    repo = make_repo(tmp_path)
    p = proposal()
    rh = fsr.rehydrate_candidate(repo, p)
    packet = fsr.build_patch_synthesis_packet(rh, p)
    assert packet["candidate_sha256"] == rh["candidate_sha256"]
    assert packet["source_commit"] == git(repo, "rev-parse", "HEAD")
    assert packet["targets"][0]["blob_sha"] == git(repo, "rev-parse", "HEAD:tools/x.py")
    assert packet["execution_authority"] == "NONE"
    assert len(packet["packet_sha256"]) == 64


def test_candidate_mutation_breaks_packet_binding(tmp_path):
    repo = make_repo(tmp_path)
    p = proposal()
    rh = fsr.rehydrate_candidate(repo, p)
    with pytest.raises(fsr.RehydrationError):
        fsr.build_patch_synthesis_packet(rh, proposal(hypothesis="changed"))


def test_large_context_is_bounded_and_not_patch_ready(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "large.txt").write_text("x" * 200, encoding="utf-8")
    git(repo, "add", "large.txt")
    git(repo, "commit", "-q", "-m", "large")
    p = proposal(target_files=["large.txt"])
    rh = fsr.rehydrate_candidate(repo, p, max_file_bytes=32, max_total_bytes=32)
    assert rh["files"][0]["truncated"] is True
    assert rh["files"][0]["context_bytes"] == 32
    assert rh["context_state"] == "CONTEXT_BOUNDED_NOT_PATCH_READY"
    with pytest.raises(fsr.RehydrationError):
        fsr.build_patch_synthesis_packet(rh, p)
