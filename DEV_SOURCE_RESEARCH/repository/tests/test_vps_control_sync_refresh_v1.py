from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "tools" / "vps_control_sync_refresh_v1.py"


def load_mod():
    spec = importlib.util.spec_from_file_location("vps_refresh", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def run(*args: str, cwd: Path | None = None) -> str:
    cp = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert cp.returncode == 0, (args, cp.stdout, cp.stderr)
    return cp.stdout.strip()


def write_tree(repo: Path, epoch: str = "9.13", provider_true: bool = False, together_forbidden: bool = True):
    sup = {
        "schema_version": epoch,
        "free_only": {
            "enabled": True,
            "provider_routes_admitted": False,
            "together_forbidden": together_forbidden,
            "no_paid_fallback": True,
            "free_swarm_owner_emergency_stop": True,
        },
    }
    adm = {
        "authority_epoch": epoch,
        "mode": "FREE_ONLY",
        "execution_state": "OWNER_EMERGENCY_STOP_FREE_SWARM_HARD_OFF",
        "default_policy": "FREE_ONLY_NO_PAID_FALLBACK_TOGETHER_FORBIDDEN",
        "providers": {
            "openrouter": {"admitted": provider_true},
            "groq": {"admitted": False},
        },
    }
    files = {
        "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json": json.dumps(sup),
        "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json": json.dumps(adm),
        "tools/free_swarm_restart_authority_attribution_v4.py": "# v4\n",
        "tools/freepool_fallback_provider_gate_v1.py": "# gate\n",
        "tools/system_analysis_current_reader_v1.py": "# reader\n",
        "free swarm/update_system_analysis_v6.py": "# monitor\n",
        "tools/xeno_physical_grid10_fused_acceptance_v1.py": "# grid\n",
        "tools/xeno_recursive_physical_scaling_bridge_acceptance_v2.py": "# bridge\n",
    }
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def init_remote(tmp_path: Path):
    bare = tmp_path / "remote.git"
    seed = tmp_path / "seed"
    run("git", "init", "--bare", str(bare))
    run("git", "init", "-b", "main", str(seed))
    run("git", "config", "user.email", "test@example.invalid", cwd=seed)
    run("git", "config", "user.name", "test", cwd=seed)
    write_tree(seed)
    run("git", "add", ".", cwd=seed)
    run("git", "commit", "-m", "base", cwd=seed)
    run("git", "remote", "add", "origin", str(bare), cwd=seed)
    run("git", "push", "-u", "origin", "main", cwd=seed)
    clone = tmp_path / "clone"
    run("git", "clone", "-b", "main", str(bare), str(clone))
    run("git", "config", "user.email", "test@example.invalid", cwd=clone)
    run("git", "config", "user.name", "test", cwd=clone)
    return bare, seed, clone


def commit_and_push(seed: Path, msg: str, **kwargs) -> str:
    write_tree(seed, **kwargs)
    marker = seed / "marker.txt"
    marker.write_text(msg, encoding="utf-8")
    run("git", "add", ".", cwd=seed)
    run("git", "commit", "-m", msg, cwd=seed)
    run("git", "push", "origin", "main", cwd=seed)
    return run("git", "rev-parse", "HEAD", cwd=seed)


def call(mod, clone: Path, bare: Path, apply: bool = False):
    out = clone / "receipt.json"
    argv = ["--repo", str(clone), "--remote", str(bare), "--receipt", str(out)]
    if apply:
        argv.append("--apply")
    rc = mod.main(argv)
    return rc, json.loads(out.read_text(encoding="utf-8"))


def test_dirty_checkout_never_mutates(tmp_path):
    mod = load_mod(); bare, seed, clone = init_remote(tmp_path)
    remote = commit_and_push(seed, "remote-1")
    before = run("git", "rev-parse", "HEAD", cwd=clone)
    (clone / "dirty.txt").write_text("dirty", encoding="utf-8")
    rc, receipt = call(mod, clone, bare, apply=True)
    assert rc == 77 and receipt["pass"] is False
    assert "working_tree_dirty" in receipt["errors"][0]
    assert run("git", "rev-parse", "HEAD", cwd=clone) == before != remote


def test_stale_clean_without_apply_is_read_only(tmp_path):
    mod = load_mod(); bare, seed, clone = init_remote(tmp_path)
    remote = commit_and_push(seed, "remote-2")
    before = run("git", "rev-parse", "HEAD", cwd=clone)
    rc, receipt = call(mod, clone, bare, apply=False)
    assert rc == 77
    assert receipt["execution_authority"] == "REFRESH_REQUIRED_APPLY_NOT_REQUESTED"
    assert receipt.get("git_worktree_fast_forward_applied") is not True
    assert run("git", "rev-parse", "HEAD", cwd=clone) == before != remote


def test_safe_fast_forward_apply_reaches_exact_remote(tmp_path):
    mod = load_mod(); bare, seed, clone = init_remote(tmp_path)
    remote = commit_and_push(seed, "remote-3")
    rc, receipt = call(mod, clone, bare, apply=True)
    assert rc == 0 and receipt["pass"] is True
    assert receipt["execution_authority"] == "CONTROL_SYNC_REFRESH_PASS"
    assert receipt["dirty_after"] is False
    assert receipt["remote_main_head_initial"] == receipt["remote_main_head_final"] == remote
    assert run("git", "rev-parse", "HEAD", cwd=clone) == remote


def test_diverged_checkout_rejected_without_reset(tmp_path):
    mod = load_mod(); bare, seed, clone = init_remote(tmp_path)
    commit_and_push(seed, "remote-4")
    (clone / "local.txt").write_text("local", encoding="utf-8")
    run("git", "add", ".", cwd=clone); run("git", "commit", "-m", "local", cwd=clone)
    before = run("git", "rev-parse", "HEAD", cwd=clone)
    rc, receipt = call(mod, clone, bare, apply=True)
    assert rc == 77 and "local_head_not_ancestor_of_remote_main" in receipt["errors"][0]
    assert run("git", "rev-parse", "HEAD", cwd=clone) == before


@pytest.mark.parametrize(
    "kwargs,needle",
    [
        ({"epoch": "9.14"}, "authority_epoch_mismatch"),
        ({"provider_true": True}, "provider_not_false:openrouter"),
        ({"together_forbidden": False}, "together_forbidden"),
    ],
)
def test_remote_authority_violation_blocks_apply(tmp_path, kwargs, needle):
    mod = load_mod(); bare, seed, clone = init_remote(tmp_path)
    if kwargs.get("epoch"):
        write_tree(seed, epoch="9.14")
        adm_p = seed / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
        adm = json.loads(adm_p.read_text()); adm["authority_epoch"] = "9.13"; adm_p.write_text(json.dumps(adm))
        (seed / "marker.txt").write_text("bad-epoch")
        run("git", "add", ".", cwd=seed); run("git", "commit", "-m", "bad-epoch", cwd=seed); run("git", "push", "origin", "main", cwd=seed)
    else:
        commit_and_push(seed, "bad-auth", **kwargs)
    before = run("git", "rev-parse", "HEAD", cwd=clone)
    rc, receipt = call(mod, clone, bare, apply=True)
    assert rc == 77 and needle in receipt["errors"][0]
    assert run("git", "rev-parse", "HEAD", cwd=clone) == before


def test_remote_race_after_resolution_cannot_mint_pass(tmp_path, monkeypatch):
    mod = load_mod(); bare, seed, clone = init_remote(tmp_path)
    first = commit_and_push(seed, "remote-first")
    original = mod.validate_commit
    raced = {"done": False}

    def validate_then_advance(repo, commit):
        result = original(repo, commit)
        if not raced["done"]:
            commit_and_push(seed, "remote-raced")
            raced["done"] = True
        return result

    monkeypatch.setattr(mod, "validate_commit", validate_then_advance)
    rc, receipt = call(mod, clone, bare, apply=True)
    assert rc == 77
    assert receipt["pass"] is False
    assert "remote_main_moved_during_refresh" in receipt["errors"][0]
    assert receipt["remote_main_head_initial"] == first
    assert receipt["remote_main_head_final"] != first


def test_post_reset_validation_failure_does_not_mint_pass(tmp_path, monkeypatch):
    mod = load_mod(); bare, seed, clone = init_remote(tmp_path)
    commit_and_push(seed, "remote-post-fail")
    original = mod.validate_commit
    calls = {"n": 0}

    def fail_second(repo, commit):
        calls["n"] += 1
        result = original(repo, commit)
        if calls["n"] >= 2:
            authority, hashes, errors = result
            errors = list(errors) + ["injected_post_reset_failure"]
            return authority, hashes, errors
        return result

    monkeypatch.setattr(mod, "validate_commit", fail_second)
    rc, receipt = call(mod, clone, bare, apply=True)
    assert rc == 77
    assert receipt["pass"] is False
    assert "post_refresh_validation_failed" in receipt["errors"][0]
