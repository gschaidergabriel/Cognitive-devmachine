#!/usr/bin/env python3
"""Read-only control-plane sync guard for clay-direct-dev/VPS execution.

This tool never checks out, resets, pulls, writes Git refs, reads secrets, or contacts any
model/provider endpoint. It performs one read-only GitHub control query (`git ls-remote`)
and proves whether the *existing* checkout is admissible for later non-provider runtime work.

PASS requires:
- clean working tree;
- local HEAD exactly equals current GitHub `main`;
- local tree identity is bound;
- current SUPERVISOR_INBOX and FREE_PROVIDER_ADMISSION are parseable and epoch-coherent;
- current authority is FREE_ONLY/HARD_OFF with all provider routes false and Together forbidden;
- critical downstream source files exist and are SHA-256 bound.

A stale or dirty checkout yields NO_EXECUTION_AUTHORITY. The tool does not repair it; this
prevents a read-only synchronisation check from silently becoming a mutation authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

SCHEMA = "XENO_VPS_CONTROL_SYNC_GUARD/v1"
DEFAULT_REMOTE = "https://github.com/gschaidergabriel/clay-global-research-entity.git"
SUPERVISOR_REL = Path("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
ADMISSION_REL = Path("research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json")
CRITICAL_SOURCES = (
    Path("tools/free_swarm_restart_authority_attribution_v4.py"),
    Path("tools/freepool_fallback_provider_gate_v1.py"),
    Path("tools/system_analysis_current_reader_v1.py"),
    Path("free swarm/update_system_analysis_v6.py"),
    Path("tools/xeno_physical_grid10_fused_acceptance_v1.py"),
    Path("tools/xeno_recursive_physical_scaling_bridge_acceptance_v2.py"),
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if cp.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed rc={cp.returncode}: {cp.stderr.strip()}")
    return cp.stdout.strip()


def remote_main_sha(remote: str) -> str:
    cp = subprocess.run(
        ["git", "ls-remote", remote, "refs/heads/main"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if cp.returncode != 0:
        raise RuntimeError(f"git ls-remote failed rc={cp.returncode}: {cp.stderr.strip()}")
    rows = [line.split() for line in cp.stdout.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) < 2 or rows[0][1] != "refs/heads/main":
        raise RuntimeError("could not resolve exactly one refs/heads/main")
    sha = rows[0][0].lower()
    if len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        raise RuntimeError("remote main SHA is not canonical hex40")
    return sha


def load_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"{path}: expected JSON object")
    return obj


def validate_authority(supervisor: dict[str, Any], admission: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    s_epoch = str(supervisor.get("schema_version", ""))
    a_epoch = str(admission.get("authority_epoch", ""))
    if not s_epoch or s_epoch != a_epoch:
        errors.append(f"authority_epoch_mismatch:{s_epoch!r}!={a_epoch!r}")

    free_only = supervisor.get("free_only")
    if not isinstance(free_only, dict):
        errors.append("supervisor.free_only_missing")
        free_only = {}
    if free_only.get("enabled") is not True:
        errors.append("supervisor.free_only.enabled_not_true")
    if free_only.get("provider_routes_admitted") is not False:
        errors.append("supervisor.provider_routes_admitted_not_false")
    if free_only.get("together_forbidden") is not True:
        errors.append("supervisor.together_forbidden_not_true")
    if free_only.get("no_paid_fallback") is not True:
        errors.append("supervisor.no_paid_fallback_not_true")
    if free_only.get("free_swarm_owner_emergency_stop") is not True:
        errors.append("supervisor.emergency_stop_not_true")

    if admission.get("mode") != "FREE_ONLY":
        errors.append("admission.mode_not_FREE_ONLY")
    state = str(admission.get("execution_state", ""))
    if "HARD_OFF" not in state:
        errors.append("admission.execution_state_not_HARD_OFF")
    providers = admission.get("providers")
    if not isinstance(providers, dict) or not providers:
        errors.append("admission.providers_missing")
    else:
        admitted = [name for name, cfg in providers.items() if isinstance(cfg, dict) and cfg.get("admitted") is True]
        if admitted:
            errors.append("admission.provider_admitted:" + ",".join(sorted(admitted)))
    policy = str(admission.get("default_policy", ""))
    if "TOGETHER_FORBIDDEN" not in policy or "NO_PAID_FALLBACK" not in policy:
        errors.append("admission.default_policy_missing_paid_prohibitions")
    return errors


def evaluate(repo: Path, remote_sha: str) -> dict[str, Any]:
    head = run_git(repo, "rev-parse", "HEAD").lower()
    tree = run_git(repo, "rev-parse", "HEAD^{tree}").lower()
    porcelain = run_git(repo, "status", "--porcelain=v1", "--untracked-files=normal")
    dirty = bool(porcelain.strip())

    errors: list[str] = []
    if dirty:
        errors.append("working_tree_dirty")
    if head != remote_sha:
        errors.append(f"stale_head:{head}!={remote_sha}")

    sup_path = repo / SUPERVISOR_REL
    adm_path = repo / ADMISSION_REL
    missing = [str(p) for p in (SUPERVISOR_REL, ADMISSION_REL, *CRITICAL_SOURCES) if not (repo / p).is_file()]
    if missing:
        errors.extend("missing_source:" + p for p in missing)

    supervisor: dict[str, Any] = {}
    admission: dict[str, Any] = {}
    if sup_path.is_file() and adm_path.is_file():
        try:
            supervisor = load_json(sup_path)
            admission = load_json(adm_path)
            errors.extend(validate_authority(supervisor, admission))
        except Exception as exc:  # fail closed
            errors.append(f"authority_parse_error:{type(exc).__name__}:{exc}")

    hashes: dict[str, str] = {}
    for rel in (SUPERVISOR_REL, ADMISSION_REL, *CRITICAL_SOURCES):
        path = repo / rel
        if path.is_file():
            hashes[str(rel)] = sha256_file(path)

    passed = not errors
    return {
        "schema": SCHEMA,
        "pass": passed,
        "execution_authority": "READONLY_CONTROL_SYNC_PASS" if passed else "NO_EXECUTION_AUTHORITY",
        "repo": str(repo.resolve()),
        "local_head": head,
        "remote_main_head": remote_sha,
        "tree": tree,
        "dirty": dirty,
        "authority_epoch": str(admission.get("authority_epoch", "")) if admission else None,
        "supervisor_schema_version": str(supervisor.get("schema_version", "")) if supervisor else None,
        "source_sha256": hashes,
        "provider_calls": 0,
        "secret_lookups": 0,
        "working_tree_mutations": 0,
        "git_ref_mutations": 0,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--remote", default=DEFAULT_REMOTE)
    p.add_argument("--receipt", default="")
    ns = p.parse_args(argv)
    repo = Path(ns.repo).resolve()

    try:
        remote_sha = remote_main_sha(ns.remote)
        receipt = evaluate(repo, remote_sha)
    except Exception as exc:
        receipt = {
            "schema": SCHEMA,
            "pass": False,
            "execution_authority": "NO_EXECUTION_AUTHORITY",
            "repo": str(repo),
            "provider_calls": 0,
            "secret_lookups": 0,
            "working_tree_mutations": 0,
            "git_ref_mutations": 0,
            "errors": [f"control_sync_error:{type(exc).__name__}:{exc}"],
        }

    encoded = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    sys.stdout.write(encoded)
    if ns.receipt:
        out = Path(ns.receipt)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded, encoding="utf-8")
    return 0 if receipt.get("pass") is True else 77


if __name__ == "__main__":
    raise SystemExit(main())
