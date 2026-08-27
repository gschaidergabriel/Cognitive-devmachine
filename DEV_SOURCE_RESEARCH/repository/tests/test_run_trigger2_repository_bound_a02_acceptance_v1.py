from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

from tools import run_trigger2_repository_bound_a02_acceptance_v1 as runner


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def _write_commit(repo: Path, rel: str, content: bytes, message: str) -> str:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    _git(repo, "add", rel)
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _authority(commit: str, content: bytes) -> dict:
    return {
        "producer": {
            "repo_path": "tools/producer.py",
            "source_sha256": hashlib.sha256(content).hexdigest(),
            "source_lineage": {
                "repository": runner.EXPECTED_REPOSITORY,
                "branch": "main",
                "source_path": "tools/producer.py",
                "source_commit_sha": commit,
            },
        }
    }


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.check_call(["git", "init", "-b", "main"], cwd=repo)
    _git(repo, "config", "user.email", "trigger2-test@example.invalid")
    _git(repo, "config", "user.name", "Trigger2 Test")
    return repo


def test_remote_identity_accepts_only_exact_secret_free_forms():
    assert runner._normalize_remote(
        "https://github.com/gschaidergabriel/clay-global-research-entity.git"
    ) == runner.EXPECTED_REPOSITORY
    assert runner._normalize_remote(
        "git@github.com:gschaidergabriel/clay-global-research-entity.git"
    ) == runner.EXPECTED_REPOSITORY
    assert runner._normalize_remote(
        "ssh://git@github.com/gschaidergabriel/clay-global-research-entity"
    ) == runner.EXPECTED_REPOSITORY

    # Credential-bearing and attacker-controlled suffix lookalikes must fail closed.
    assert runner._normalize_remote(
        "https://token@github.com/gschaidergabriel/clay-global-research-entity.git"
    ) is None
    assert runner._normalize_remote(
        "https://attacker.invalid/github.com/gschaidergabriel/clay-global-research-entity.git"
    ) is None
    assert runner._normalize_remote(
        "https://github.com/gschaidergabriel/other-repo.git"
    ) is None


def test_lineage_accepts_real_ancestor_commit_path_blob_and_current_bytes(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    content = b"print('authority-pinned')\n"
    source_commit = _write_commit(repo, "tools/producer.py", content, "source")
    _write_commit(repo, "README.md", b"successor\n", "successor")
    head = _git(repo, "rev-parse", "HEAD")

    monkeypatch.setattr(runner, "ROOT", repo)
    result = runner._lineage_binding(_authority(source_commit, content), head)
    assert result["pass"] is True
    assert result["commit_exists"] is True
    assert result["commit_is_ancestor_of_executed_head"] is True
    assert result["all_three_byte_identities_match"] is True


def test_lineage_rejects_well_formed_nonexistent_commit(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    content = b"print('authority-pinned')\n"
    _write_commit(repo, "tools/producer.py", content, "source")
    head = _git(repo, "rev-parse", "HEAD")

    monkeypatch.setattr(runner, "ROOT", repo)
    authority = _authority("0" * 40, content)
    result = runner._lineage_binding(authority, head)
    assert result["pass"] is False
    assert result["commit_exists"] is False


def test_lineage_rejects_real_nonancestor_even_with_identical_source_bytes(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    content = b"print('authority-pinned')\n"
    _write_commit(repo, "tools/producer.py", content, "main source")
    main_head = _git(repo, "rev-parse", "HEAD")

    _git(repo, "checkout", "--orphan", "unrelated")
    for child in list(repo.iterdir()):
        if child.name == ".git":
            continue
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            import shutil
            shutil.rmtree(child)
    _git(repo, "rm", "-rf", "--cached", ".")
    unrelated_commit = _write_commit(repo, "tools/producer.py", content, "unrelated source")
    _git(repo, "checkout", "main")

    monkeypatch.setattr(runner, "ROOT", repo)
    result = runner._lineage_binding(_authority(unrelated_commit, content), main_head)
    assert result["commit_exists"] is True
    assert result["all_three_byte_identities_match"] is True
    assert result["commit_is_ancestor_of_executed_head"] is False
    assert result["pass"] is False


def test_lineage_rejects_post_checkout_worktree_mutation(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    content = b"print('authority-pinned')\n"
    source_commit = _write_commit(repo, "tools/producer.py", content, "source")
    head = _git(repo, "rev-parse", "HEAD")
    (repo / "tools/producer.py").write_bytes(b"print('mutated')\n")

    monkeypatch.setattr(runner, "ROOT", repo)
    result = runner._lineage_binding(_authority(source_commit, content), head)
    assert result["commit_exists"] is True
    assert result["commit_is_ancestor_of_executed_head"] is True
    assert result["all_three_byte_identities_match"] is False
    assert result["pass"] is False
