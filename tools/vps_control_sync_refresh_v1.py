#!/usr/bin/env python3
"""Fail-closed read/refresh guard for a stale VPS checkout.

Purpose: recover the GO runtime-control transport without using provider/model APIs.
The tool uses an explicit HTTPS GitHub remote, never the checkout's configured SSH remote.
It may update only Git object/ref/worktree state, and only by clean fast-forward to remote main.
It never starts/stops runtime processes, reads provider secrets, or invokes provider endpoints.

Algorithm:
1. Require existing git checkout and clean worktree.
2. Resolve remote main over explicit HTTPS.
3. If already current: validate current FREE_ONLY/HARD_OFF authority and exit PASS.
4. If stale: require local HEAD is ancestor of remote main (no divergence).
5. Fetch remote main into a temporary namespaced ref.
6. Read SUPERVISOR_INBOX + FREE_PROVIDER_ADMISSION directly from fetched commit BEFORE checkout.
7. Require coherent FREE_ONLY/HARD_OFF, all providers false, Together forbidden.
8. Fast-forward checkout with `git reset --hard <remote_sha>` only after all checks pass.
9. Re-validate clean HEAD/tree/authority and critical source hashes.

Any ambiguity yields NO_EXECUTION_AUTHORITY and no runtime mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

SCHEMA = "XENO_VPS_CONTROL_SYNC_REFRESH/v1"
DEFAULT_REMOTE = "https://github.com/gschaidergabriel/clay-global-research-entity.git"
FETCH_REF = "refs/xeno-control-sync/main"
SUP = "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
ADM = "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
CRITICAL = (
    "tools/free_swarm_restart_authority_attribution_v4.py",
    "tools/freepool_fallback_provider_gate_v1.py",
    "tools/system_analysis_current_reader_v1.py",
    "free swarm/update_system_analysis_v6.py",
    "tools/xeno_physical_grid10_fused_acceptance_v1.py",
    "tools/xeno_recursive_physical_scaling_bridge_acceptance_v2.py",
)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(["git", "-C", str(repo), *args], text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and cp.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} rc={cp.returncode}: {cp.stderr.strip()}")
    return cp


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def remote_sha(remote: str) -> str:
    cp = subprocess.run(["git", "ls-remote", remote, "refs/heads/main"], text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if cp.returncode != 0:
        raise RuntimeError(f"https_control_transport_failed:{cp.stderr.strip()}")
    rows = [x.split() for x in cp.stdout.splitlines() if x.strip()]
    if len(rows) != 1 or rows[0][1] != "refs/heads/main":
        raise RuntimeError("remote_main_not_unique")
    value = rows[0][0].lower()
    if len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise RuntimeError("remote_main_not_hex40")
    return value


def show_bytes(repo: Path, commit: str, path: str) -> bytes:
    cp = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if cp.returncode != 0:
        raise RuntimeError(f"missing_at_commit:{path}:{cp.stderr.decode(errors='replace').strip()}")
    return cp.stdout


def parse_json(data: bytes, label: str) -> dict[str, Any]:
    obj = json.loads(data.decode("utf-8"))
    if not isinstance(obj, dict):
        raise RuntimeError(f"{label}_not_object")
    return obj


def authority_errors(sup: dict[str, Any], adm: dict[str, Any]) -> list[str]:
    e: list[str] = []
    se = str(sup.get("schema_version", ""))
    ae = str(adm.get("authority_epoch", ""))
    if not se or se != ae:
        e.append(f"authority_epoch_mismatch:{se}!={ae}")
    f = sup.get("free_only") if isinstance(sup.get("free_only"), dict) else {}
    checks = {
        "free_only_enabled": f.get("enabled") is True,
        "routes_false": f.get("provider_routes_admitted") is False,
        "together_forbidden": f.get("together_forbidden") is True,
        "no_paid_fallback": f.get("no_paid_fallback") is True,
        "emergency_stop": f.get("free_swarm_owner_emergency_stop") is True,
        "admission_free_only": adm.get("mode") == "FREE_ONLY",
        "hard_off": "HARD_OFF" in str(adm.get("execution_state", "")),
        "policy_together_forbidden": "TOGETHER_FORBIDDEN" in str(adm.get("default_policy", "")),
        "policy_no_paid_fallback": "NO_PAID_FALLBACK" in str(adm.get("default_policy", "")),
    }
    e.extend(k for k, ok in checks.items() if not ok)
    providers = adm.get("providers")
    if not isinstance(providers, dict) or not providers:
        e.append("providers_missing")
    else:
        for name, cfg in providers.items():
            if not isinstance(cfg, dict) or cfg.get("admitted") is not False:
                e.append(f"provider_not_false:{name}")
    return e


def validate_commit(repo: Path, commit: str) -> tuple[dict[str, Any], dict[str, str], list[str]]:
    sup_b = show_bytes(repo, commit, SUP)
    adm_b = show_bytes(repo, commit, ADM)
    sup = parse_json(sup_b, "supervisor")
    adm = parse_json(adm_b, "admission")
    errors = authority_errors(sup, adm)
    hashes = {SUP: sha256_bytes(sup_b), ADM: sha256_bytes(adm_b)}
    for rel in CRITICAL:
        data = show_bytes(repo, commit, rel)
        hashes[rel] = sha256_bytes(data)
    return {"supervisor": sup, "admission": adm}, hashes, errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--remote", default=DEFAULT_REMOTE)
    ap.add_argument("--receipt", default="")
    ap.add_argument("--apply", action="store_true", help="Allow clean fast-forward after all remote authority checks pass")
    ns = ap.parse_args(argv)
    repo = Path(ns.repo).resolve()
    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "pass": False,
        "execution_authority": "NO_EXECUTION_AUTHORITY",
        "provider_calls": 0,
        "secret_lookups": 0,
        "runtime_process_mutations": 0,
        "remote_transport": "HTTPS_GIT_ONLY",
        "apply_requested": bool(ns.apply),
        "errors": [],
    }
    try:
        head = git(repo, "rev-parse", "HEAD").stdout.strip().lower()
        tree_before = git(repo, "rev-parse", "HEAD^{tree}").stdout.strip().lower()
        dirty = bool(git(repo, "status", "--porcelain=v1", "--untracked-files=normal").stdout.strip())
        receipt.update(local_head_before=head, tree_before=tree_before, dirty_before=dirty)
        if dirty:
            raise RuntimeError("working_tree_dirty")

        rsha = remote_sha(ns.remote)
        receipt["remote_main_head"] = rsha
        if head != rsha:
            anc = git(repo, "merge-base", "--is-ancestor", head, rsha, check=False)
            if anc.returncode != 0:
                # Remote object may not exist locally yet. Fetch only into namespaced ref, then retry ancestry.
                git(repo, "fetch", "--no-tags", ns.remote, f"refs/heads/main:{FETCH_REF}")
                anc = git(repo, "merge-base", "--is-ancestor", head, rsha, check=False)
            else:
                # Still fetch so remote authority is read from the exact remote object, not a stale local object.
                git(repo, "fetch", "--no-tags", ns.remote, f"refs/heads/main:{FETCH_REF}")
            if anc.returncode != 0:
                raise RuntimeError("local_head_not_ancestor_of_remote_main")
        else:
            # Ensure validation reads the exact current commit; no fetch needed.
            pass

        authority, hashes, errors = validate_commit(repo, rsha)
        receipt["authority_epoch_remote"] = str(authority["admission"].get("authority_epoch", ""))
        receipt["supervisor_epoch_remote"] = str(authority["supervisor"].get("schema_version", ""))
        receipt["source_sha256_remote"] = hashes
        if errors:
            raise RuntimeError("remote_authority_invalid:" + ",".join(errors))

        if head != rsha:
            if not ns.apply:
                receipt["execution_authority"] = "REFRESH_REQUIRED_APPLY_NOT_REQUESTED"
                receipt["errors"] = ["stale_clean_checkout_safe_fast_forward_available"]
                encoded = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
                sys.stdout.write(encoded)
                if ns.receipt:
                    Path(ns.receipt).write_text(encoded, encoding="utf-8")
                return 77
            git(repo, "reset", "--hard", rsha)
            receipt["git_worktree_fast_forward_applied"] = True
        else:
            receipt["git_worktree_fast_forward_applied"] = False

        head2 = git(repo, "rev-parse", "HEAD").stdout.strip().lower()
        tree2 = git(repo, "rev-parse", "HEAD^{tree}").stdout.strip().lower()
        dirty2 = bool(git(repo, "status", "--porcelain=v1", "--untracked-files=normal").stdout.strip())
        authority2, hashes2, errors2 = validate_commit(repo, head2)
        if head2 != rsha or dirty2 or errors2 or hashes2 != hashes:
            raise RuntimeError("post_refresh_validation_failed")
        receipt.update(
            pass=True,
            execution_authority="CONTROL_SYNC_REFRESH_PASS",
            local_head_after=head2,
            tree_after=tree2,
            dirty_after=dirty2,
            source_sha256_after=hashes2,
            authority_epoch_after=str(authority2["admission"].get("authority_epoch", "")),
            errors=[],
        )
    except Exception as exc:
        receipt["errors"] = [f"{type(exc).__name__}:{exc}"]

    encoded = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    sys.stdout.write(encoded)
    if ns.receipt:
        out = Path(ns.receipt); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(encoded, encoding="utf-8")
    return 0 if receipt.get("pass") is True else 77


if __name__ == "__main__":
    raise SystemExit(main())
