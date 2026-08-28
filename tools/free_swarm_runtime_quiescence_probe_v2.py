#!/usr/bin/env python3
"""Repository/current-authority-bound 90s runtime quiescence proof.

This is a strict wrapper around the existing v1 observer.  A PASS requires BOTH:
1) vps_control_sync_guard_v1 PASS immediately before observation,
2) >=90 seconds of v1 quiescence evidence,
3) vps_control_sync_guard_v1 PASS again after observation with the SAME remote main,
   local HEAD/tree and dual-authority epoch/hashes.

The wrapper performs no provider/model calls, no secret lookup, no process mutation and no
checkout/ref mutation.  GitHub access is limited to the read-only `git ls-remote` used by the
control-sync guard.  Zombie/defunct entries with empty cmdline are not promoted to live workers;
the underlying v1 process scan is authoritative only for live forbidden command lines.

A PASS is scoped to runtime-quiescence evidence only. It grants no GRID10/HCU/training credit.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

SCHEMA = "CLAY_FREE_SWARM_RUNTIME_QUIESCENCE_RECEIPT/v2"
MIN_WINDOW_SECONDS = 90.0


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _stable_binding(pre: dict[str, Any], post: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for label, obj in (("pre", pre), ("post", post)):
        if obj.get("pass") is not True:
            errors.append(f"{label}_control_sync_not_pass")
        if obj.get("dirty") is not False:
            errors.append(f"{label}_working_tree_not_clean")
        if obj.get("provider_calls") != 0 or obj.get("secret_lookups") != 0:
            errors.append(f"{label}_unexpected_provider_or_secret_boundary")
    for field in ("local_head", "remote_main_head", "tree", "authority_epoch", "supervisor_schema_version"):
        if pre.get(field) != post.get(field):
            errors.append(f"binding_changed:{field}")
    if pre.get("source_sha256") != post.get("source_sha256"):
        errors.append("binding_changed:source_sha256")
    if pre.get("local_head") != pre.get("remote_main_head"):
        errors.append("pre_local_not_current_remote")
    if post.get("local_head") != post.get("remote_main_head"):
        errors.append("post_local_not_current_remote")
    return (not errors, errors)


def evaluate(pre: dict[str, Any], inner: dict[str, Any], post: dict[str, Any], requested_window: float) -> dict[str, Any]:
    stable, errors = _stable_binding(pre, post)
    duration = float(inner.get("observation", {}).get("duration_seconds", 0.0) or 0.0)
    inner_pass = inner.get("decision", {}).get("status") == "PASS_COMPONENT_ONLY"
    if requested_window < MIN_WINDOW_SECONDS:
        errors.append("requested_window_below_90s")
    if duration < MIN_WINDOW_SECONDS:
        errors.append("observed_duration_below_90s")
    if not inner_pass:
        errors.append("v1_quiescence_not_pass")
    passed = stable and inner_pass and requested_window >= MIN_WINDOW_SECONDS and duration >= MIN_WINDOW_SECONDS
    return {
        "schema": SCHEMA,
        "pass": passed,
        "status": "PASS_SCOPED_RUNTIME_QUIESCENCE" if passed else "FAIL_CLOSED",
        "control_binding_pre": pre,
        "quiescence_v1": inner,
        "control_binding_post": post,
        "minimum_window_seconds": MIN_WINDOW_SECONDS,
        "requested_window_seconds": requested_window,
        "observed_duration_seconds": duration,
        "provider_calls": 0,
        "secret_lookups": 0,
        "process_mutations": 0,
        "git_ref_mutations": 0,
        "credit_boundary": "RUNTIME_QUIESCENCE_ONLY; NO_GRID10_HCU_TRAINING_ENTITYOS_PROMOTION",
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--remote", default="https://github.com/gschaidergabriel/clay-global-research-entity.git")
    p.add_argument("--window-seconds", type=float, default=90.0)
    p.add_argument("--sample-interval-seconds", type=float, default=2.0)
    p.add_argument("--provider-budget-db", default="/artifacts/clay-entityos-swarm/provider_budget.sqlite3")
    p.add_argument("--receipt", default="")
    ns = p.parse_args(argv)
    repo = Path(ns.repo).resolve()
    tools = repo / "tools"
    try:
        guard = _load(tools / "vps_control_sync_guard_v1.py", "go_sync_guard")
        qv1 = _load(tools / "free_swarm_runtime_quiescence_probe_v1.py", "go_quiescence_v1")
        remote_pre = guard.remote_main_sha(ns.remote)
        pre = guard.evaluate(repo, remote_pre)
        if pre.get("pass") is not True:
            inner = {"decision": {"status": "NOT_RUN_CONTROL_SYNC_FAILED"}, "observation": {"duration_seconds": 0.0}}
            post = pre
        elif ns.window_seconds < MIN_WINDOW_SECONDS:
            inner = {"decision": {"status": "NOT_RUN_WINDOW_TOO_SHORT"}, "observation": {"duration_seconds": 0.0}}
            post = pre
        else:
            inner_ns = argparse.Namespace(
                repo=str(repo),
                admission="research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json",
                metrics="free swarm/LIVE_METRICS.json",
                provider_budget_db=ns.provider_budget_db,
                proc_root="/proc",
                forbid=[],
                window_seconds=float(ns.window_seconds),
                sample_interval_seconds=float(ns.sample_interval_seconds),
                receipt="",
            )
            inner = qv1.build_receipt(inner_ns)
            remote_post = guard.remote_main_sha(ns.remote)
            post = guard.evaluate(repo, remote_post)
        receipt = evaluate(pre, inner, post, float(ns.window_seconds))
    except Exception as exc:
        receipt = {
            "schema": SCHEMA,
            "pass": False,
            "status": "FAIL_CLOSED",
            "provider_calls": 0,
            "secret_lookups": 0,
            "process_mutations": 0,
            "git_ref_mutations": 0,
            "errors": [f"{type(exc).__name__}:{exc}"],
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
