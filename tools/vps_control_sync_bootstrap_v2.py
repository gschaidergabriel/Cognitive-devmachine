#!/usr/bin/env python3
"""Read-only bootstrap for delivering the current VPS refresh tool to a stale checkout.

v2 closes an output-path mutation gap in v1: user-supplied capsule/receipt paths are rejected
when they resolve inside the owning checkout. A bootstrap that claims to leave the owning
checkout unchanged must not be able to dirty it via its own output arguments.

The bootstrap only fetches Git objects/a namespaced ref, extracts the exact current refresh tool
and its adversarial test into a capsule outside the owning checkout, optionally executes that
exact test in a detached temporary worktree, and re-resolves remote main before granting a
BOOTSTRAP_CAPSULE_PASS_NO_APPLY_AUTHORITY result.

It never applies the refresh, resets the owning checkout, starts/stops runtime processes, or
reads/calls provider credentials/endpoints.
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

SCHEMA = "XENO_VPS_CONTROL_SYNC_BOOTSTRAP/v2"
DEFAULT_REMOTE = "https://github.com/gschaidergabriel/clay-global-research-entity.git"
REFRESH = "tools/vps_control_sync_refresh_v1.py"
TEST = "tests/test_vps_control_sync_refresh_v1.py"
FETCH_REF = "refs/xeno-control-bootstrap/main-v2"


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


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def reject_owning_output_path(value: str, repo: Path, label: str) -> None:
    if not value:
        return
    if is_within(Path(value), repo):
        raise RuntimeError(f"{label}_inside_owning_checkout_forbidden")


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
    temp_worktree = None
    try:
        if not (repo / ".git").exists():
            raise RuntimeError("owning_checkout_not_git_worktree")
        reject_owning_output_path(ns.capsule_dir, repo, "capsule_dir")
        reject_owning_output_path(ns.receipt, repo, "receipt")

        before_head = cp(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.decode().strip().lower()
        before_tree = cp(["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"]).stdout.decode().strip().lower()
        before_status = cp(["git", "-C", str(repo), "status", "--porcelain=v1", "--untracked-files=normal"]).stdout.decode()
        receipt.update(owning_head_before=before_head, owning_tree_before=before_tree, owning_status_sha256_before=sha256(before_status.encode()), owning_dirty_before=bool(before_status.strip()))

        rsha = remote_main(ns.remote)
        receipt["remote_main_head"] = rsha
        cp(["git", "-C", str(repo), "fetch", "--no-tags", ns.remote, f"refs/heads/main:{FETCH_REF}"])
        fetched = cp(["git", "-C", str(repo), "rev-parse", FETCH_REF]).stdout.decode().strip().lower()
        if fetched != rsha:
            raise RuntimeError(f"fetched_ref_mismatch:{fetched}!={rsha}")

        refresh_bytes = git_show(repo, rsha, REFRESH)
        test_bytes = git_show(repo, rsha, TEST)
        capsule = Path(ns.capsule_dir).resolve() if ns.capsule_dir else Path(tempfile.mkdtemp(prefix="xeno-control-bootstrap-v2-"))
        capsule.mkdir(parents=True, exist_ok=True)
        refresh_out = capsule / "vps_control_sync_refresh_v1.py"
        test_out = capsule / "test_vps_control_sync_refresh_v1.py"
        refresh_out.write_bytes(refresh_bytes)
        test_out.write_bytes(test_bytes)
        receipt["capsule"] = {
            "dir": str(capsule),
            "outside_owning_checkout": not is_within(capsule, repo),
            "remote_commit": rsha,
            "refresh_path_in_commit": REFRESH,
            "refresh_sha256": sha256(refresh_bytes),
            "test_path_in_commit": TEST,
            "test_sha256": sha256(test_bytes),
        }
        if not receipt["capsule"]["outside_owning_checkout"]:
            raise RuntimeError("capsule_containment_check_failed")

        after_head = cp(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.decode().strip().lower()
        after_tree = cp(["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"]).stdout.decode().strip().lower()
        after_status = cp(["git", "-C", str(repo), "status", "--porcelain=v1", "--untracked-files=normal"]).stdout.decode()
        if (after_head, after_tree, after_status) != (before_head, before_tree, before_status):
            raise RuntimeError("owning_checkout_changed_during_bootstrap")
        receipt.update(owning_head_after=after_head, owning_tree_after=after_tree, owning_status_sha256_after=sha256(after_status.encode()), owning_dirty_after=bool(after_status.strip()))

        if ns.run_tests:
            work_root = Path(tempfile.mkdtemp(prefix="xeno-control-test-worktree-v2-"))
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

        rsha2 = remote_main(ns.remote)
        receipt["remote_main_head_final"] = rsha2
        if rsha2 != rsha:
            raise RuntimeError(f"remote_main_moved_during_bootstrap:{rsha}->{rsha2}")

        final_head = cp(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.decode().strip().lower()
        final_tree = cp(["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"]).stdout.decode().strip().lower()
        final_status = cp(["git", "-C", str(repo), "status", "--porcelain=v1", "--untracked-files=normal"]).stdout.decode()
        if (final_head, final_tree, final_status) != (before_head, before_tree, before_status):
            raise RuntimeError("owning_checkout_changed_before_bootstrap_pass")
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
        out = Path(ns.receipt).resolve()
        if not is_within(out, repo):
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(encoded, encoding="utf-8")
    return 0 if receipt["pass"] else 77


if __name__ == "__main__":
    raise SystemExit(main())
