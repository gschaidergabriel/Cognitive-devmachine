#!/usr/bin/env python3
"""Fail-closed proof capsule for Free-Swarm runtime quiescence.

This tool performs no provider/model/network execution. It only observes:
  * canonical FREE_PROVIDER_ADMISSION hard-off state,
  * local /proc command lines for forbidden legacy Free-Swarm process classes,
  * derived provider-usage counters in free swarm/LIVE_METRICS.json,
  * the shared provider-budget SQLite gate's direct cumulative counters/leases,
  * repository HEAD/tree/dirty identity.

A PASS means only that the sampled host showed no forbidden process classes, no
movement in either observed provider-counter surface, and no unexpired shared-budget
leases during the declared observation window while canonical provider admission was
hard-off. It does not grant model, GRID10, training, or product credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from typing import Any, Iterable

SCHEMA = "CLAY_FREE_SWARM_RUNTIME_QUIESCENCE_RECEIPT/v1"
REQUIRED_EXECUTION_STATE = "OWNER_EMERGENCY_STOP_FREE_SWARM_HARD_OFF"
DEFAULT_PROVIDER_BUDGET_DB = os.getenv(
    "CLAY_FREE_PROVIDER_BUDGET_DB",
    "/artifacts/clay-entityos-swarm/provider_budget.sqlite3",
)
DEFAULT_FORBIDDEN = (
    "run_6000_free_swarm_supervisor.sh",
    "run_24h_entityos_swarm_supervisor.sh",
    "run_24h_entityos_swarm.py",
    "run_free_go_swarm.py",
    "run_free_evidence_forge.py",
    "run_research_distillery_local.py",
    "run_research_distillery_entry.py",
    "free swarm/evaluate.py",
)


class ProbeError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ProbeError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(obj, dict):
        raise ProbeError(f"JSON root is not an object: {path}")
    return obj


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except Exception as exc:
        raise ProbeError(f"cannot hash {path}: {exc}") from exc


def canonical_sha256(obj: Any) -> str:
    data = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(data)


def admission_state(path: Path) -> dict[str, Any]:
    obj = _read_json(path)
    providers = obj.get("providers")
    if not isinstance(providers, dict) or not providers:
        raise ProbeError("provider admission has no non-empty providers object")
    provider_states: dict[str, bool] = {}
    for name, entry in sorted(providers.items()):
        if not isinstance(entry, dict) or "admitted" not in entry:
            raise ProbeError(f"provider {name!r} lacks explicit admitted field")
        provider_states[str(name)] = bool(entry.get("admitted"))
    execution_state = obj.get("execution_state")
    hard_off = execution_state == REQUIRED_EXECUTION_STATE and all(v is False for v in provider_states.values())
    return {
        "path": str(path),
        "sha256": file_sha256(path),
        "authority_epoch": obj.get("authority_epoch"),
        "mode": obj.get("mode"),
        "execution_state": execution_state,
        "provider_admitted": provider_states,
        "hard_off": hard_off,
    }


def _model_usage_rows(workers: dict[str, Any]) -> list[dict[str, Any]]:
    models = workers.get("models")
    if not isinstance(models, list):
        raise ProbeError("LIVE_METRICS workers.models is not a list")
    out: list[dict[str, Any]] = []
    fields = (
        "provider", "model", "requests", "success", "rate_limits", "errors",
        "input_tokens", "output_tokens", "total_tokens",
    )
    for idx, row in enumerate(models):
        if not isinstance(row, dict):
            raise ProbeError(f"LIVE_METRICS workers.models[{idx}] is not an object")
        out.append({k: row.get(k) for k in fields})
    out.sort(key=lambda r: (str(r.get("provider")), str(r.get("model"))))
    return out


def provider_usage_snapshot(path: Path) -> dict[str, Any]:
    obj = _read_json(path)
    workers = obj.get("workers")
    if not isinstance(workers, dict):
        raise ProbeError("LIVE_METRICS lacks workers object")
    core = {
        "exact_usage_rows": workers.get("exact_usage_rows"),
        "input_tokens": workers.get("input_tokens"),
        "output_tokens": workers.get("output_tokens"),
        "total_tokens": workers.get("total_tokens"),
        "models": _model_usage_rows(workers),
    }
    for field in ("exact_usage_rows", "input_tokens", "output_tokens", "total_tokens"):
        if not isinstance(core[field], int) or core[field] < 0:
            raise ProbeError(f"LIVE_METRICS workers.{field} must be a non-negative integer")
    return {
        "path": str(path),
        "file_sha256": file_sha256(path),
        "generated_at": obj.get("generated_at"),
        "usage": core,
        "usage_sha256": canonical_sha256(core),
    }


def provider_budget_snapshot(
    path: Path,
    *,
    now: float | None = None,
    providers: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Read the shared quota gate directly without mutating/expiring any rows.

    ``total_requests`` is incremented by free_swarm_quota.acquire() before a provider
    request can proceed, so this is a stronger attempt counter than a derived worker
    dashboard. The snapshot intentionally keeps the derived LIVE_METRICS check as an
    independent surface rather than replacing it.
    """
    path = path.resolve()
    if not path.exists() or not path.is_file():
        raise ProbeError(f"shared provider budget DB unavailable: {path}")
    current = time.time() if now is None else float(now)
    provider_filter = tuple(sorted({str(x) for x in providers or () if str(x)}))
    provider_filter_set = set(provider_filter)
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=2)
        try:
            rows = con.execute(
                "SELECT provider,total_requests,total_success,total_429,total_errors "
                "FROM provider_state ORDER BY provider"
            ).fetchall()
            if not rows:
                raise ProbeError("shared provider budget DB has no provider_state rows")
            provider_counters: dict[str, dict[str, int]] = {}
            for provider, requests, success, rate, errors in rows:
                provider_name = str(provider)
                if provider_filter_set and provider_name not in provider_filter_set:
                    continue
                values = {
                    "total_requests": requests,
                    "total_success": success,
                    "total_429": rate,
                    "total_errors": errors,
                }
                if any(not isinstance(v, int) or v < 0 for v in values.values()):
                    raise ProbeError(f"shared provider budget has invalid counters for {provider!r}")
                provider_counters[provider_name] = values
            if provider_filter_set and not provider_counters:
                raise ProbeError("shared provider budget DB has no rows for canonical provider set")
            lease_rows = con.execute(
                "SELECT lease_id,provider,owner,acquired_at,expires_at "
                "FROM leases WHERE expires_at > ? ORDER BY provider,lease_id",
                (current,),
            ).fetchall()
        finally:
            con.close()
    except ProbeError:
        raise
    except Exception as exc:
        raise ProbeError(f"cannot read shared provider budget DB {path}: {exc}") from exc

    counters = {"providers": provider_counters}
    unexpired = [
        {
            "lease_id": str(lease_id),
            "provider": str(provider),
            "owner": str(owner),
            "acquired_at": float(acquired_at),
            "expires_at": float(expires_at),
        }
        for lease_id, provider, owner, acquired_at, expires_at in lease_rows
        if not provider_filter_set or str(provider) in provider_filter_set
    ]
    return {
        "path": str(path),
        "provider_filter": list(provider_filter),
        "counter_sha256": canonical_sha256(counters),
        "counters": counters,
        "unexpired_leases": unexpired,
        "zero_unexpired_leases": not unexpired,
    }


def scan_processes(proc_root: Path, forbidden: Iterable[str], ignore_pids: Iterable[int] = ()) -> dict[str, Any]:
    if not proc_root.exists() or not proc_root.is_dir():
        raise ProbeError(f"proc root unavailable: {proc_root}")
    forbidden = tuple(str(x) for x in forbidden if str(x))
    ignored = {int(x) for x in ignore_pids}
    scanned = 0
    matches: list[dict[str, Any]] = []
    for p in sorted(proc_root.glob("[0-9]*/cmdline"), key=lambda q: int(q.parent.name)):
        pid = int(p.parent.name)
        if pid in ignored:
            continue
        try:
            raw = p.read_bytes()
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        scanned += 1
        cmd = raw.replace(b"\0", b" ").decode("utf-8", errors="replace").strip()
        if not cmd:
            continue
        hit = [needle for needle in forbidden if needle in cmd]
        if hit:
            matches.append({"pid": pid, "cmdline": cmd, "matched": hit})
    return {"scanned_processes": scanned, "matches": matches, "zero_forbidden": not matches}


def git_identity(repo: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        try:
            cp = subprocess.run(
                ["git", "-C", str(repo), *args],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as exc:
            raise ProbeError(f"git identity failed for {args}: {exc}") from exc
        return cp.stdout.strip()

    head = run("rev-parse", "HEAD")
    tree = run("rev-parse", "HEAD^{tree}")
    status = run("status", "--porcelain=v1")
    return {"repo": str(repo.resolve()), "head": head, "tree": tree, "dirty": bool(status), "status_porcelain": status}


def evaluate(
    admission: dict[str, Any],
    usage_before: dict[str, Any],
    usage_after: dict[str, Any],
    process_samples: list[dict[str, Any]],
    provider_budget_before: dict[str, Any] | None = None,
    provider_budget_after: dict[str, Any] | None = None,
) -> dict[str, Any]:
    hard_off = admission.get("hard_off") is True
    usage_stable = usage_before.get("usage_sha256") == usage_after.get("usage_sha256")
    process_evidence_present = bool(process_samples)
    process_quiet = process_evidence_present and all(s.get("zero_forbidden") is True for s in process_samples)
    budget_evidence_present = provider_budget_before is not None and provider_budget_after is not None
    budget_stable = bool(
        budget_evidence_present
        and provider_budget_before.get("counter_sha256") == provider_budget_after.get("counter_sha256")
    )
    no_budget_leases = bool(
        budget_evidence_present
        and provider_budget_before.get("zero_unexpired_leases") is True
        and provider_budget_after.get("zero_unexpired_leases") is True
    )
    passed = hard_off and usage_stable and process_quiet and budget_stable and no_budget_leases
    reasons: list[str] = []
    if not hard_off:
        reasons.append("CANONICAL_PROVIDER_ADMISSION_NOT_HARD_OFF")
    if not usage_stable:
        reasons.append("PROVIDER_USAGE_CHANGED_DURING_WINDOW")
    if not process_evidence_present:
        reasons.append("NO_PROCESS_SAMPLES")
    elif not process_quiet:
        reasons.append("FORBIDDEN_FREE_SWARM_PROCESS_OBSERVED")
    if not budget_evidence_present:
        reasons.append("NO_SHARED_PROVIDER_BUDGET_EVIDENCE")
    else:
        if not budget_stable:
            reasons.append("SHARED_PROVIDER_BUDGET_COUNTER_CHANGED_DURING_WINDOW")
        if not no_budget_leases:
            reasons.append("UNEXPIRED_SHARED_PROVIDER_BUDGET_LEASE_OBSERVED")
    return {
        "hard_off": hard_off,
        "provider_usage_stable": usage_stable,
        "process_samples_present": process_evidence_present,
        "zero_forbidden_processes_all_samples": process_quiet,
        "shared_provider_budget_evidence_present": budget_evidence_present,
        "shared_provider_budget_counter_stable": budget_stable,
        "zero_unexpired_shared_provider_budget_leases": no_budget_leases,
        "status": "PASS_COMPONENT_ONLY" if passed else "FAIL_CLOSED",
        "failure_reasons": reasons,
    }


def build_receipt(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo).resolve()
    admission_path = (repo / args.admission).resolve()
    metrics_path = (repo / args.metrics).resolve()
    provider_budget_db = Path(args.provider_budget_db).expanduser().resolve()
    proc_root = Path(args.proc_root).resolve()
    forbidden = tuple(DEFAULT_FORBIDDEN) + tuple(args.forbid or ())

    identity = git_identity(repo)
    admission = admission_state(admission_path)
    start_wall = time.time()
    usage_before = provider_usage_snapshot(metrics_path)
    canonical_provider_names = tuple(sorted(admission.get("provider_admitted", {}).keys()))
    budget_before = provider_budget_snapshot(
        provider_budget_db, now=start_wall, providers=canonical_provider_names
    )
    samples: list[dict[str, Any]] = []

    end_at = time.monotonic() + args.window_seconds
    sample_idx = 0
    while True:
        now_wall = time.time()
        proc = scan_processes(proc_root, forbidden, ignore_pids=(os.getpid(), os.getppid()))
        samples.append({"sample": sample_idx, "wall_time_unix": now_wall, **proc})
        sample_idx += 1
        remaining = end_at - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(args.sample_interval_seconds, remaining))

    usage_after = provider_usage_snapshot(metrics_path)
    end_wall = time.time()
    budget_after = provider_budget_snapshot(
        provider_budget_db, now=end_wall, providers=canonical_provider_names
    )
    decision = evaluate(
        admission,
        usage_before,
        usage_after,
        samples,
        provider_budget_before=budget_before,
        provider_budget_after=budget_after,
    )

    try:
        source_hash = file_sha256(Path(__file__).resolve())
    except ProbeError:
        source_hash = None

    return {
        "schema": SCHEMA,
        "source": {"path": str(Path(__file__).resolve()), "sha256": source_hash},
        "repository": identity,
        "authority": admission,
        "observation": {
            "start_unix": start_wall,
            "end_unix": end_wall,
            "duration_seconds": max(0.0, end_wall - start_wall),
            "requested_window_seconds": args.window_seconds,
            "sample_interval_seconds": args.sample_interval_seconds,
            "proc_root": str(proc_root),
            "forbidden_needles": list(forbidden),
            "process_samples": samples,
            "provider_usage_before": usage_before,
            "provider_usage_after": usage_after,
            "shared_provider_budget_before": budget_before,
            "shared_provider_budget_after": budget_after,
        },
        "decision": decision,
        "credit_boundary": "RUNTIME_QUIESCENCE_COMPONENT_ONLY; NO_MODEL_GRID10_TRAINING_HCU_ENTITYOS_CREDIT",
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    p.add_argument("--admission", default="research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json")
    p.add_argument("--metrics", default="free swarm/LIVE_METRICS.json")
    p.add_argument("--provider-budget-db", default=DEFAULT_PROVIDER_BUDGET_DB)
    p.add_argument("--proc-root", default="/proc")
    p.add_argument("--window-seconds", type=float, default=60.0)
    p.add_argument("--sample-interval-seconds", type=float, default=1.0)
    p.add_argument("--forbid", action="append", default=[])
    p.add_argument("--output")
    ns = p.parse_args(argv)
    if ns.window_seconds <= 0:
        p.error("--window-seconds must be > 0")
    if ns.sample_interval_seconds <= 0:
        p.error("--sample-interval-seconds must be > 0")
    return ns


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        receipt = build_receipt(args)
    except ProbeError as exc:
        receipt = {
            "schema": SCHEMA,
            "decision": {"status": "FAIL_CLOSED", "failure_reasons": ["PROBE_ERROR"]},
            "error": str(exc),
            "credit_boundary": "NO_RUNTIME_QUIESCENCE_CREDIT",
        }
    text = json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0 if receipt.get("decision", {}).get("status") == "PASS_COMPONENT_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
