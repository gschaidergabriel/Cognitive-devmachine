import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from forge_candidate_execution_boundary import (  # noqa: E402
    command_evidence,
    materialize_patch_context,
    patch_paths_safe,
    safe_target,
    validate_candidate_without_execution,
)


def _git(cwd: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return p.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "forge-test@example.invalid")
    _git(repo, "config", "user.name", "Forge Test")
    (repo / "demo.txt").write_text("alpha\n", encoding="utf-8")
    _git(repo, "add", "demo.txt")
    _git(repo, "commit", "-qm", "base")
    return repo


def _row(proposal: dict):
    return {
        "candidate_hash": "c" * 64,
        "delta_id": "delta-1",
        "provider": "test",
        "model": "test-model",
        "role": "HCU_CAUSAL",
        "worker_sha": "w" * 64,
        "proposal_json": json.dumps(proposal),
    }


def _forge(repo: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    return SimpleNamespace(ROOT=repo, FORGE_ROOT=out, now=lambda: "2026-08-24T00:00:00+00:00")


def _proposal(**overrides):
    obj = {
        "target_files": ["demo.txt"],
        "patch_unified_diff": "",
        "test_commands": ["python3 -m pytest -q tests/test_demo.py"],
        "negative_test_commands": [],
        "benchmark_command": "",
        "hypothesis": "exact source context improves patch apply rate",
    }
    obj.update(overrides)
    return obj


def test_sensitive_and_escape_targets_fail_closed():
    assert safe_target("tools/x.py") is True
    assert safe_target("../x.py") is False
    assert safe_target("research_entity/private/API_TOKENS.env") is False
    assert safe_target("x.env") is False
    assert patch_paths_safe("--- a/demo.txt\n+++ b/../../escape\n", ["demo.txt"]) is False


def test_model_commands_are_evidence_not_authority():
    got = command_evidence(
        ["python3 -c 'print(1)'", "pytest -q; env"],
        "echo x | cat",
    )
    assert got["execution_admitted"] is False
    assert got["inline_interpreter_present"] is True
    assert got["shell_metacharacters_present"] is True


def test_patch_context_binds_exact_head_tree_and_blob(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "forge"
    got = materialize_patch_context(
        root=repo,
        output_root=out,
        candidate_hash="a" * 64,
        targets=["demo.txt"],
    )
    assert got["ok"] is True
    packet = json.loads((out / got["relative_path"]).read_text(encoding="utf-8"))
    assert packet["source"]["commit"] == _git(repo, "rev-parse", "HEAD")
    assert packet["source"]["tree"] == _git(repo, "rev-parse", "HEAD^{tree}")
    assert packet["targets"][0]["blob_sha"] == _git(repo, "rev-parse", "HEAD:demo.txt")
    assert packet["targets"][0]["content_utf8"] == "alpha\n"
    assert packet["canonical_truth"] is False
    assert packet["effect_authority"] is False


def test_stage1_candidate_rehydrates_then_stops_before_execution(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "forge"
    got = validate_candidate_without_execution(_forge(repo, out), None, _row(_proposal()))
    assert got["status"] == "valid_candidate"
    assert got["execution_state"] == "EXECUTION_BLOCKED"
    assert got["next_state"] == "SECOND_STAGE_PATCH_SYNTHESIS"
    assert got["patch_context"]["ok"] is True


def test_apply_clean_patch_still_requires_isolated_executor(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "forge"
    patch = "--- a/demo.txt\n+++ b/demo.txt\n@@ -1 +1 @@\n-alpha\n+beta\n"
    got = validate_candidate_without_execution(
        _forge(repo, out), None, _row(_proposal(patch_unified_diff=patch))
    )
    assert got["status"] == "apply_check_pass"
    assert got["apply_check"]["ok"] is True
    assert got["execution_state"] == "EXECUTION_BLOCKED"
    assert got["execution_admitted"] is False
    assert got["next_state"] == "EXECUTION_ADMISSION"


def test_model_authored_program_is_never_run(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    out = tmp_path / "forge"
    marker = tmp_path / "MUST_NOT_EXIST"
    monkeypatch.setenv("NVIDIA_API_KEY", "SHOULD_NOT_BE_EXPOSED")
    patch = "--- a/demo.txt\n+++ b/demo.txt\n@@ -1 +1 @@\n-alpha\n+beta\n"
    cmd = f"python3 -c \"open({str(marker)!r},'w').write(os.environ.get('NVIDIA_API_KEY',''))\""
    got = validate_candidate_without_execution(
        _forge(repo, out), None, _row(_proposal(patch_unified_diff=patch, test_commands=[cmd]))
    )
    assert got["status"] == "apply_check_pass"
    assert got["execution_state"] == "EXECUTION_BLOCKED"
    assert marker.exists() is False


def test_rejected_patch_gets_regeneration_context_not_execution(tmp_path):
    repo = _repo(tmp_path)
    out = tmp_path / "forge"
    patch = "--- a/demo.txt\n+++ b/demo.txt\n@@ -99 +99 @@\n-nope\n+beta\n"
    got = validate_candidate_without_execution(
        _forge(repo, out), None, _row(_proposal(patch_unified_diff=patch))
    )
    assert got["status"] == "patch_rejected"
    assert got["next_state"] == "SECOND_STAGE_PATCH_SYNTHESIS"
    assert got["execution_state"] == "EXECUTION_BLOCKED"
    assert got["patch_context"]["ok"] is True
