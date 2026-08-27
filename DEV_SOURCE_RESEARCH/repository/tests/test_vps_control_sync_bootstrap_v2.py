from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "tools" / "vps_control_sync_bootstrap_v2.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("bootstrap_v2", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def run(*args: str, cwd: Path | None = None) -> str:
    cp = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert cp.returncode == 0, (args, cp.stdout, cp.stderr)
    return cp.stdout.strip()


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    run("git", "init", "-b", "main", str(repo))
    run("git", "config", "user.email", "test@example.invalid", cwd=repo)
    run("git", "config", "user.name", "test", cwd=repo)
    (repo / "a.txt").write_text("a", encoding="utf-8")
    run("git", "add", ".", cwd=repo)
    run("git", "commit", "-m", "base", cwd=repo)
    return repo


def test_receipt_inside_owning_checkout_is_rejected_without_dirtying(tmp_path, monkeypatch):
    mod = load_mod()
    repo = init_repo(tmp_path)
    before = run("git", "status", "--porcelain=v1", cwd=repo)
    receipt = repo / "receipt.json"
    rc = mod.main(["--repo", str(repo), "--receipt", str(receipt)])
    assert rc == 77
    assert not receipt.exists()
    assert run("git", "status", "--porcelain=v1", cwd=repo) == before == ""


def test_capsule_inside_owning_checkout_is_rejected_before_write(tmp_path):
    mod = load_mod()
    repo = init_repo(tmp_path)
    capsule = repo / "capsule"
    rc = mod.main(["--repo", str(repo), "--capsule-dir", str(capsule)])
    assert rc == 77
    assert not capsule.exists()
    assert run("git", "status", "--porcelain=v1", cwd=repo) == ""


def test_path_containment_rejects_nested_but_not_sibling(tmp_path):
    mod = load_mod()
    repo = init_repo(tmp_path)
    assert mod.is_within(repo / "x" / "y", repo) is True
    assert mod.is_within(tmp_path / "repo-sibling", repo) is False


def test_non_git_owning_checkout_fails_closed(tmp_path):
    mod = load_mod()
    repo = tmp_path / "notgit"
    repo.mkdir()
    rc = mod.main(["--repo", str(repo)])
    assert rc == 77


def test_output_guard_is_checked_before_remote_transport(tmp_path, monkeypatch):
    mod = load_mod()
    repo = init_repo(tmp_path)
    called = {"remote": False}

    def forbidden_remote(_remote: str):
        called["remote"] = True
        raise AssertionError("remote transport must not run")

    monkeypatch.setattr(mod, "remote_main", forbidden_remote)
    rc = mod.main(["--repo", str(repo), "--receipt", str(repo / "r.json")])
    assert rc == 77
    assert called["remote"] is False
