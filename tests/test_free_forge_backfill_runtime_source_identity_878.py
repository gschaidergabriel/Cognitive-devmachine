from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_free_evidence_forge_backfill as forge  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def _fixture_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    tools = repo / "tools"
    tools.mkdir(parents=True)
    entrypoint = tools / "run_free_evidence_forge_backfill.py"
    dependency = tools / "dependency.py"
    entrypoint.write_text("print('clean')\n", encoding="utf-8")
    dependency.write_text("VALUE = 1\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Clay Test")
    _git(repo, "config", "user.email", "clay-test@example.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "fixture")
    return entrypoint, dependency


def _observe(monkeypatch, entrypoint: Path) -> dict[str, object]:
    monkeypatch.setattr(forge, "__file__", str(entrypoint))
    monkeypatch.setattr(forge, "_ENTRYPOINT", entrypoint)
    return forge._source_identity()


def test_clean_tracked_tree_is_admitted(monkeypatch, tmp_path: Path) -> None:
    entrypoint, _ = _fixture_repo(tmp_path)
    observed = _observe(monkeypatch, entrypoint)

    assert observed["tracked_worktree_dirty"] is False
    assert observed["entrypoint_matches_source_tree"] is True
    assert observed["source_entrypoint_blob"] == observed["runtime_entrypoint_git_blob"]
    assert observed["source_identity_admitted"] is True
    assert observed["source_identity_reason"] == "CLEAN_TRACKED_TREE_AND_ENTRYPOINT_MATCH_HEAD"


def test_dirty_entrypoint_fails_closed(monkeypatch, tmp_path: Path) -> None:
    entrypoint, _ = _fixture_repo(tmp_path)
    entrypoint.write_text("print('locally modified')\n", encoding="utf-8")
    observed = _observe(monkeypatch, entrypoint)

    assert observed["tracked_worktree_dirty"] is True
    assert observed["entrypoint_matches_source_tree"] is False
    assert observed["source_identity_admitted"] is False
    assert observed["source_identity_reason"] == "TRACKED_WORKTREE_DIRTY"


def test_dirty_tracked_dependency_fails_closed_even_when_entrypoint_matches(monkeypatch, tmp_path: Path) -> None:
    entrypoint, dependency = _fixture_repo(tmp_path)
    dependency.write_text("VALUE = 2\n", encoding="utf-8")
    observed = _observe(monkeypatch, entrypoint)

    assert observed["tracked_worktree_dirty"] is True
    assert observed["entrypoint_matches_source_tree"] is True
    assert observed["source_identity_admitted"] is False
    assert observed["source_identity_reason"] == "TRACKED_WORKTREE_DIRTY"
