from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import forge_runtime_identity as fri


def _repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "test"], check=True)
    entrypoint = repo / "tools" / "forge.py"
    entrypoint.parent.mkdir()
    entrypoint.write_text("print('forge')\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "tools/forge.py"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True)
    return repo, entrypoint


def test_linux_process_generation_binds_pid_reuse() -> None:
    identity = fri.process_generation_identity(os.getpid())
    assert identity is not None
    assert fri.process_generation_is_live(identity)
    assert not fri.process_generation_is_live(identity + "0")


def test_runtime_identity_binds_exact_committed_entrypoint(tmp_path: Path) -> None:
    repo, entrypoint = _repo(tmp_path)
    identity = fri.runtime_identity(entrypoint, root=repo)
    assert identity["schema"] == fri.RUNTIME_IDENTITY_SCHEMA
    assert identity["runtime_entrypoint_path"] == "tools/forge.py"
    assert identity["runtime_entrypoint_matches_source_commit"] is True
    assert identity["source_commit"]
    assert identity["source_tree"]
    assert identity["process_start_identity"]
    assert identity["supervisor_generation_or_start_nonce"]
    assert identity["status_writer_schema_version"] == fri.STATUS_WRITER_SCHEMA
    assert identity["runtime_identity_state"] == "VERIFIED"


def test_mutated_entrypoint_fails_closed(tmp_path: Path) -> None:
    repo, entrypoint = _repo(tmp_path)
    entrypoint.write_text("print('mutated')\n", encoding="utf-8")
    identity = fri.runtime_identity(entrypoint, root=repo)
    assert identity["runtime_entrypoint_matches_source_commit"] is False
    assert identity["runtime_identity_state"] == "RUNTIME_IDENTITY_UNVERIFIED"


def test_status_validator_rejects_missing_identity(tmp_path: Path) -> None:
    repo, entrypoint = _repo(tmp_path)
    ok, reasons = fri.validate_status_identity({"state": "LIVE"}, entrypoint, root=repo)
    assert not ok
    assert reasons == ["RUNTIME_IDENTITY_MISSING"]


def test_status_validator_accepts_exact_live_identity(tmp_path: Path) -> None:
    repo, entrypoint = _repo(tmp_path)
    identity = fri.runtime_identity(entrypoint, root=repo)
    ok, reasons = fri.validate_status_identity(
        {"state": "LIVE", "runtime_identity": identity}, entrypoint, root=repo
    )
    assert ok
    assert reasons == []
