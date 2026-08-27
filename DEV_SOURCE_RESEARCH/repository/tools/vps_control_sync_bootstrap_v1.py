#!/usr/bin/env python3
"""Read-only bootstrap for delivering the current VPS refresh tool to a stale checkout.

This file is intended to be supplied by the control plane itself (for example from the current
GitHub workflow/connector), not discovered from the stale owning checkout. It does not mutate
the owning checkout. It resolves current remote main, fetches that exact commit into Git object
storage, extracts the refresh tool and its adversarial test from that commit into a temporary
capsule, records SHA-256 identities, and optionally runs the test from an isolated temporary
worktree at that exact commit.

Only after this bootstrap reports PASS may a separate authority invoke the extracted refresh tool
against the owning checkout. This bootstrap never uses --apply, never resets the owning checkout,
never starts/stops runtime processes, and never touches provider credentials/endpoints.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

SCHEMA = "XENO_VPS_CONTROL_SYNC_BOOTSTRAP/v1"
DEFAULT_REMOTE = "https://github.com/gschaidergabriel/clay-global-research-entity.git"
REFRESH = "tools/vps_control_sync_refresh_v1.py"
TEST = "tests/test_vps_control_sync_refresh_v1.py"
FETCH_REF = "refs/xeno-control-bootstrap/main"


def cp(args: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)
    if check and p.returncode != 0:
        raise RuntimeError(f"command_failed:{args!r}:rc={p.returncode}:{p.stderr.decode(errors='replace').strip()}")
    return p


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def remote_main(remote: str) -> str:
    p = cp(["git", "ls-remote", remote, "refs/heads/main"])
    rows = [line.split() for line in p.stdout.decode().splitlines() if line.strip()]
    if len(rows) != 1 or rows[0][1] != "refs/heads/main":
        raise RuntimeError("remote_main_not_unique")
    value = rows[0][0].lower()
    if len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise RuntimeError("remote_main_not_hex40")
    return value


def git_show(repo: Path, commit: str, rel: str) -> bytes:
    p = cp(["git", "-C", str(repo), "show", f"{commit}:{rel}"])
    return p.stdout


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Owning stale/possibly-current git checkout; object store only may be updated by fetch")
    ap.add_argument("--remote", default=DEFAULT_REMOTE)
    ap.add_argument("--capsule-dir", default="")
    ap.add_argument("--run-tests", action="store_true")
    ap.add_argument("--receipt", default="")
    ns = ap.parse_args(argv)

    repo = Path(ns.repo).resolve()
    receipt = {
        "schema": SCHEMA,
        "pass": False,
        "execution_authority": "BOOTSTRAP_ONLY_NO_APPLY_AUTHORITY",
        "owning_checkout_worktree_mutations": 0,
        "runtime_process_mutations": 0,
        "provider_calls": 0,
        "secret_lookups": 0,
        "errors": [],
    }
    capsule_created = None
    temp_worktree = None
    try:
        before_head = cp(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.decode().strip().lower()
        before_tree = cp(["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"]).stdout.decode().strip().lower()
        before_status = cp(["git", "-C", str(repo), "status", "--porcelain=v1", "--untracked-files=normal"]).stdout.decode()
        receipt.update(owning_head_before=before_head, owning_tree_before=before_tree, owning_dirty_before=bool(before_status.strip()))

        rsha = remote_main(ns.remote)
        receipt["remote_main_head"] = rsha
        # Fetches objects/ref only; does not alter HEAD/index/worktree.
        cp(["git", "-C", str(repo), "fetch", "--no-tags", ns.remote, f"refs/heads/main:{FETCH_REF}"])
        fetched = cp(["git", "-C", str(repo), "rev-parse", FETCH_REF]).stdout.decode().strip().lower()
        if fetched != rsha:
            raise RuntimeError(f"fetched_ref_mismatch:{fetched}!={rsha}")

        refresh_bytes = git_show(repo, rsha, REFRESH)
        test_bytes = git_show(repo, rsha, TEST)
        capsule = Path(ns.capsule_dir).resolve() if ns.capsule_dir else Path(tempfile.mkdtemp(prefix="xeno-control-bootstrap-"))
        if not ns.capsule_dir:
            capsule_created = capsule
        capsule.mkdir(parents=True, exist_ok=True)
        refresh_out = capsule / "vps_control_sync_refresh_v1.py"
        test_out = capsule / "test_vps_control_sync_refresh_v1.py"
        refresh_out.write_bytes(refresh_bytes)
        test_out.write_bytes(test_bytes)
        receipt["capsule"] = {
            "dir": str(capsule),
            "remote_commit": rsha,
            "refresh_path_in_commit": REFRESH,
            "refresh_sha256": sha256(refresh_bytes),
            "test_path_in_commit": TEST,
            "test_sha256": sha256(test_bytes),
        }

        # Prove fetch/extraction did not alter owning HEAD/index/worktree.
        after_head = cp(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.decode().strip().lower()
        after_tree = cp(["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"]).stdout.decode().strip().lower()
        after_status = cp(["git", "-C", str(repo), "status", "--porcelain=v1", "--untracked-files=normal"]).stdout.decode()
        if (after_head, after_tree, after_status) != (before_head, before_tree, before_status):
            raise RuntimeError("owning_checkout_changed_during_bootstrap")
        receipt.update(owning_head_after=after_head, owning_tree_after=after_tree, owning_dirty_after=bool(after_status.strip()))

        if ns.run_tests:
            work_root = Path(tempfile.mkdtemp(prefix="xeno-control-test-worktree-"))
            temp_worktree = work_root
            cp(["git", "-C", str(repo), "worktree", "add", "--detach", str(work_root), rsha])
            p = cp([sys.executable, "-m", "pytest", "-q", TEST], cwd=work_root, check=False)
            receipt["test_execution"] = {
                "returncode": p.returncode,
                "stdout_sha256": sha256(p.stdout),
                "stderr_sha256": sha256(p.stderr),
                "stdout_tail": p.stdout.decode(errors="replace")[-4000:],
                "stderr_tail": p.stderr.decode(errors="replace")[-4000:],
            }
            if p.returncode != 0:
                raise RuntimeError(f"refresh_regression_tests_failed:rc={p.returncode}")

        # Re-resolve current remote after extraction/tests; moving main cannot mint bootstrap PASS.
        rsha2 = remote_main(ns.remote)
        receipt["remote_main_head_final"] = rsha2
        if rsha2 != rsha:
            raise RuntimeError(f"remote_main_moved_during_bootstrap:{rsha}->{rsha2}")
        receipt["pass"] = True
        receipt["execution_authority"] = "BOOTSTRAP_CAPSULE_PASS_NO_APPLY_AUTHORITY"
    except Exception as exc:
        receipt["errors"] = [f"{type(exc).__name__}:{exc}"]
    finally:
        if temp_worktree is not None:
            cp(["git", "-C", str(repo), "worktree", "remove", "--force", str(temp_worktree)], check=False)
            shutil.rmtree(temp_worktree, ignore_errors=True)

    encoded = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    sys.stdout.write(encoded)
    if ns.receipt:
        out = Path(ns.receipt)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded, encoding="utf-8")
    return 0 if receipt["pass"] else 77


if __name__ == "__main__":
    raise SystemExit(main())
