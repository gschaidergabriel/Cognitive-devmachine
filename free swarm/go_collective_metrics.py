#!/usr/bin/env python3
"""Collective recursive-improvement metrics for Clay `go`.

Offline/local collector. It reads append-only worker evidence plus existing Free Swarm
worker artifacts and architecture-delta adjudications, derives a multi-objective table,
and writes deterministic JSON/Markdown. It performs no provider call, reads no provider
credential, and grants no canonical runtime/model/training credit.

Supervisor 8.76+ freshness law is enforced in this same publisher path: the live Swarm,
Forge and Distillery surfaces are read as one bounded byte snapshot, bound to the current
SUPERVISOR_INBOX authority epoch, and publication fails closed on out-of-order/stale input.
The result digest is deterministic for identical bounded inputs.

Scores are descriptive proxies behind hard evidence gates. Raw fields stay visible.
UNKNOWN is preferred over invented precision.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
from typing import Any, Iterable

SCHEMA = "CLAY_GO_COLLECTIVE_METRICS/v1"
WORKER_SCHEMA = "CLAY_GO_WORKER_METRICS/v1"
SNAPSHOT_SCHEMA = "CLAY_COLLECTIVE_METRICS_INPUT_SNAPSHOT/v1"
FRESHNESS_RECEIPT_SCHEMA = "COLLECTIVE_METRICS_FRESHNESS_RECEIPT/v1"
AUTO_BEGIN = "<!-- GO_COLLECTIVE_RECURSIVE_METRICS:BEGIN -->"
AUTO_END = "<!-- GO_COLLECTIVE_RECURSIVE_METRICS:END -->"
LIVE_SOURCE_PATHS = {
    "swarm": "free swarm/LIVE_METRICS.json",
    "forge": "free swarm/FORGE_LIVE.json",
    "distillery": "free swarm/DISTILLERY_LIVE.json",
}


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def read_bytes_stable(path: Path, attempts: int = 4) -> bytes:
    """Read one file without silently accepting an in-place mutation during the read."""
    for _ in range(max(1, attempts)):
        before = path.stat()
        data = path.read_bytes()
        after = path.stat()
        if (
            before.st_dev == after.st_dev
            and before.st_ino == after.st_ino
            and before.st_size == after.st_size == len(data)
            and before.st_mtime_ns == after.st_mtime_ns
        ):
            return data
    raise RuntimeError(f"UNSTABLE_INPUT:{path}")


def decode_json_bytes(data: bytes, path: Path) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"INVALID_JSON_INPUT:{path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"NON_OBJECT_JSON_INPUT:{path}")
    return value


def iter_jsonl(paths: Iterable[Path]):
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except Exception:
                continue
            if isinstance(value, dict):
                value.setdefault("_source", str(path))
                value.setdefault("_line", line_no)
                yield value


def parse_ts(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        x = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return x if x.tzinfo else x.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def canonical_ts(value: Any) -> str:
    parsed = parse_ts(value)
    if parsed is None:
        raise RuntimeError(f"INVALID_GENERATED_AT:{value!r}")
    return parsed.astimezone(dt.timezone.utc).isoformat()


def fnum(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def inum(value: Any) -> int | None:
    x = fnum(value)
    return int(x) if x is not None else None


def usage(row: dict[str, Any]) -> tuple[int | None, int | None, int | None]:
    u = row.get("usage")
    if not isinstance(u, dict):
        u = {}
    i = inum(u.get("input_tokens", u.get("prompt_tokens", row.get("input_tokens"))))
    o = inum(u.get("output_tokens", u.get("completion_tokens", row.get("output_tokens"))))
    t = inum(u.get("total_tokens", row.get("total_tokens")))
    if t is None and i is not None and o is not None:
        t = i + o
    return i, o, t


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


def load_config(repo: Path) -> dict[str, Any]:
    return read_json(repo / "research_entity/continuity/go_metrics/GO_METRICS_CONFIG_V1.json")


def current_authority_epoch(repo: Path) -> str:
    inbox = read_json(repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
    epoch = inbox.get("schema_version")
    if not isinstance(epoch, str) or not epoch.strip():
        raise RuntimeError("SUPERVISOR_INBOX_AUTHORITY_EPOCH_REQUIRED")
    steering = inbox.get("steering")
    if not isinstance(steering, str) or not steering.strip():
        raise RuntimeError("SUPERVISOR_INBOX_STEERING_POINTER_REQUIRED")
    steering_doc = read_json(repo / steering)
    if str(steering_doc.get("schema_version") or "") != epoch:
        raise RuntimeError("SUPERVISOR_INBOX_STEERING_EPOCH_MISMATCH")
    return epoch


def accepted_delta(row: dict[str, Any]) -> bool:
    status = str(row.get("status") or "").lower()
    if status not in {"accepted", "pass", "integrated", "verified"}:
        return False
    imp = fnum(row.get("relative_improvement_pct"))
    runs = inum(row.get("reproducible_runs")) or 0
    hard_failed = sum((inum(row.get(k)) or 0) for k in (
        "tests_failed", "negative_tests_failed", "static_checks_failed"
    ))
    return bool(
        imp is not None and imp > 0 and runs >= 2 and hard_failed == 0
        and row.get("benchmark_non_regression") is True
        and not bool(row.get("reverted"))
    )


def test_ratio(row: dict[str, Any], passed: str, failed: str) -> float | None:
    p = inum(row.get(passed))
    f = inum(row.get(failed))
    if p is None and f is None:
        return None
    p = p or 0
    f = f or 0
    return p / (p + f) if p + f else None


def code_quality(row: dict[str, Any], config: dict[str, Any]) -> tuple[float | None, float]:
    weights = (config.get("code_quality") or {}).get("weights") or {}
    components: dict[str, float | None] = {
        "functional_correctness": test_ratio(row, "tests_passed", "tests_failed"),
        "negative_fail_closed": test_ratio(row, "negative_tests_passed", "negative_tests_failed"),
        "static_build_checks": test_ratio(row, "static_checks_passed", "static_checks_failed"),
        "benchmark_non_regression": 1.0 if row.get("benchmark_non_regression") is True else (
            0.0 if row.get("benchmark_non_regression") is False else None
        ),
        "reproducibility": min((inum(row.get("reproducible_runs")) or 0) / 3.0, 1.0)
            if row.get("reproducible_runs") is not None else None,
        "maintainability_complexity": fnum(row.get("maintainability_score")),
        "provenance_causal_identity": fnum(row.get("provenance_score")),
        "cross_mode_reuse": fnum(row.get("cross_mode_reuse_score")),
    }
    for key, value in list(components.items()):
        if value is not None and value > 1.0:
            components[key] = max(0.0, min(value / 100.0, 1.0))
    coverage = sum(float(weights.get(k, 0.0)) for k, v in components.items() if v is not None)
    min_cov = float((config.get("code_quality") or {}).get("min_evidence_coverage", 0.60))
    if coverage < min_cov:
        return None, coverage
    score = 100.0 * sum(float(weights.get(k, 0.0)) * (v or 0.0) for k, v in components.items())
    return score, coverage


def innovation_score(row: dict[str, Any], config: dict[str, Any]) -> float | None:
    inv = row.get("innovation")
    if not isinstance(inv, dict):
        return None
    if inv.get("verified") is not True:
        return None
    weights = (config.get("innovation") or {}).get("weights") or {}
    keys = {
        "nonduplicate_mechanism_novelty": "novelty",
        "measured_useful_effect": "measured_effect",
        "transferability_reuse": "transferability",
        "falsifiability_causal_discriminability": "falsifiability",
    }
    vals: dict[str, float] = {}
    for target, source in keys.items():
        x = fnum(inv.get(source))
        if x is None:
            return None
        if x > 1:
            x /= 100.0
        vals[target] = max(0.0, min(x, 1.0))
    return 100.0 * sum(float(weights.get(k, 0.0)) * v for k, v in vals.items())


def information_latency(row: dict[str, Any]) -> float | None:
    emitted = parse_ts(row.get("evidence_emitted_at"))
    consumed = parse_ts(row.get("first_downstream_consumed_at"))
    if emitted is None or consumed is None or consumed < emitted:
        return None
    return (consumed - emitted).total_seconds()


def performance_index(row: dict[str, Any]) -> float | None:
    direct = fnum(row.get("performance_index"))
    if direct is not None and direct > 0:
        return direct
    bench = row.get("benchmark")
    if not isinstance(bench, dict):
        return None
    baseline = fnum(bench.get("baseline"))
    new = fnum(bench.get("new"))
    higher = bench.get("higher_is_better", True)
    if baseline is None or new is None or baseline <= 0 or new <= 0:
        return None
    return (new / baseline) if higher else (baseline / new)


def explicit_worker_rows(repo: Path) -> list[dict[str, Any]]:
    root = repo / "research_entity/continuity/go_metrics/worker_records"
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for path in sorted(root.rglob("*.json")):
        row = read_json(path)
        if not row:
            continue
        row["_record_path"] = path.relative_to(repo).as_posix()
        rows.append(row)
    return rows


def free_swarm_rows(artifacts: Path | None) -> list[dict[str, Any]]:
    if artifacts is None or not artifacts.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in iter_jsonl(sorted(artifacts.rglob("workers.jsonl"))):
        i, o, t = usage(raw)
        ts = raw.get("ts")
        serial = raw.get("worker_serial")
        provider = str(raw.get("provider") or "unknown")
        model = str(raw.get("model") or "unknown")
        lineage = f"free_swarm:{provider}:{model}"
        rows.append({
            "schema": WORKER_SCHEMA,
            "macrocycle_id": raw.get("macrocycle_id") or raw.get("go_macrocycle_id") or "MACROCYCLE_ID_UNRESOLVED",
            "worker_id": f"free-swarm-{serial or raw.get('_line')}",
            "organ": f"{provider}/{model}",
            "source_class": "free_swarm",
            "provider": provider,
            "model": model,
            "evidence_lineage": lineage,
            "started_at": None,
            "finished_at": ts,
            "input_tokens": i,
            "output_tokens": o,
            "total_tokens": t,
            "runtime_status": raw.get("http_status"),
            "_source": raw.get("_source"),
            "_line": raw.get("_line"),
        })
    return rows


def delta_rows(repo: Path) -> list[dict[str, Any]]:
    path = repo / "free swarm/architecture_delta_evaluations.jsonl"
    return list(iter_jsonl([path])) if path.exists() else []


def worker_key(row: dict[str, Any]) -> str:
    return str(row.get("worker_id") or row.get("organ") or row.get("model") or "unknown")


def worker_lineage(row: dict[str, Any]) -> str:
    value = row.get("evidence_lineage")
    if isinstance(value, list):
        return "|".join(sorted(str(x) for x in value))
    if value:
        return str(value)
    return ":".join([
        str(row.get("provider") or "unknown"),
        str(row.get("model") or row.get("organ") or "unknown"),
        str(row.get("prompt_lineage") or "unknown"),
        str(row.get("orchestration_lineage") or "unknown"),
    ])


def attach_delta_metrics(workers: list[dict[str, Any]], deltas: list[dict[str, Any]], config: dict[str, Any]) -> None:
    by_actor: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for delta in deltas:
        if not accepted_delta(delta):
            continue
        candidates = {
            str(delta.get("worker_id") or ""),
            str(delta.get("organ") or ""),
            str(delta.get("model") or ""),
        }
        for c in candidates:
            if c:
                by_actor[c].append(delta)
    for row in workers:
        matches: list[dict[str, Any]] = []
        for c in {worker_key(row), str(row.get("organ") or ""), str(row.get("model") or "")}:
            matches.extend(by_actor.get(c, []))
        uniq = {}
        for d in matches:
            key = str(d.get("delta_id") or d.get("_source")) + ":" + str(d.get("_line"))
            uniq[key] = d
        matches = list(uniq.values())
        total_tokens = inum(row.get("total_tokens"))
        utility = 0.0
        cqs: list[float] = []
        viss: list[float] = []
        for d in matches:
            cq, _ = code_quality(d, config)
            if cq is not None:
                cqs.append(cq)
            vis = innovation_score(d, config)
            if vis is not None:
                viss.append(vis)
            imp = fnum(d.get("relative_improvement_pct")) or 0.0
            runs = inum(d.get("reproducible_runs")) or 0
            indep = fnum(d.get("independence_factor"))
            if indep is None:
                indep = 1.0
            cqf = (cq / 100.0) if cq is not None else 0.0
            utility += max(0.0, imp / 100.0) * cqf * min(runs / 3.0, 1.0) * max(0.0, min(indep, 1.0))
        row["accepted_delta_count"] = len(matches)
        row["verified_utility_units"] = utility
        row["token_quality_efficiency"] = (
            1000.0 * utility / total_tokens if total_tokens is not None and total_tokens > 0 else None
        )
        row["code_quality_score"] = statistics.fmean(cqs) if cqs else None
        row["verified_innovation_score"] = statistics.fmean(viss) if viss else None
        pidx = performance_index(row)
        lat = information_latency(row)
        floor = float((config.get("capability_information_latency") or {}).get("measurement_floor_seconds", 0.001))
        row["performance_index"] = pidx
        row["information_latency_seconds"] = lat
        row["capability_information_latency_ratio"] = (
            pidx / max(lat, floor) if pidx is not None and lat is not None else None
        )
        row["evidence_lineage_resolved"] = worker_lineage(row)


def robust_median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def hcu_forecast(workers: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    hc = config.get("hcu_confidence") or {}
    milestones = list(hc.get("milestones") or [])
    per_lineage: dict[str, dict[str, list[float]]] = collections.defaultdict(lambda: collections.defaultdict(list))
    for row in workers:
        forecast = row.get("hcu_forecast")
        if not isinstance(forecast, dict):
            continue
        lineage = worker_lineage(row)
        probs = forecast.get("milestone_probabilities")
        if not isinstance(probs, dict):
            continue
        for m in milestones:
            p = fnum(probs.get(m))
            if p is not None and 0 <= p <= 1:
                per_lineage[lineage][m].append(p)

    milestone_probs: dict[str, float] = {}
    for m in milestones:
        lineage_vals = []
        for _, values in per_lineage.items():
            x = robust_median(values.get(m, []))
            if x is not None:
                lineage_vals.append(x)
        x = robust_median(lineage_vals)
        if x is not None:
            milestone_probs[m] = x

    baseline = hc.get("initial_research_baseline") or {}
    seed = baseline.get("milestone_probabilities") or {}
    used_seed = False
    for m in milestones:
        if m not in milestone_probs:
            p = fnum(seed.get(m))
            if p is not None:
                milestone_probs[m] = p
                used_seed = True

    values = [max(0.01, min(float(milestone_probs[m]), 0.99)) for m in milestones if m in milestone_probs]
    probability = math.exp(sum(math.log(x) for x in values) / len(values)) if values else None
    coverage = len(values) / len(milestones) if milestones else 0.0
    lineages = len(per_lineage)
    calibration_state = "UNCALIBRATED" if used_seed or lineages < 3 else "COLLECTING_OUTCOME_CALIBRATION"
    return {
        "event": hc.get("event"),
        "event_definition": hc.get("event_definition"),
        "forecast_probability": probability,
        "milestone_probabilities": milestone_probs,
        "milestone_coverage": coverage,
        "independent_forecast_lineages": lineages,
        "seed_used": used_seed,
        "calibration_state": calibration_state,
        "brier_score": None,
        "log_loss": None,
        "note": "Forecast only; not completion percentage or canonical truth. Resolve future milestones and calibrate.",
    }


def aggregate(workers: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    known_tokens = [inum(r.get("total_tokens")) for r in workers]
    total_tokens = sum(x for x in known_tokens if x is not None)
    exact_token_rows = sum(1 for x in known_tokens if x is not None)
    utility = sum(float(r.get("verified_utility_units") or 0.0) for r in workers)
    tqe = 1000.0 * utility / total_tokens if total_tokens > 0 else None
    cqs = [fnum(r.get("code_quality_score")) for r in workers]
    cqs = [x for x in cqs if x is not None]
    viss = [fnum(r.get("verified_innovation_score")) for r in workers]
    viss = [x for x in viss if x is not None]
    lats = [fnum(r.get("information_latency_seconds")) for r in workers]
    lats = sorted(x for x in lats if x is not None)
    pidx = [fnum(r.get("performance_index")) for r in workers]
    pidx = [x for x in pidx if x is not None]

    def percentile95(xs: list[float]) -> float | None:
        if not xs:
            return None
        if len(xs) == 1:
            return xs[0]
        k = 0.95 * (len(xs) - 1)
        lo = math.floor(k)
        hi = math.ceil(k)
        if lo == hi:
            return xs[lo]
        return xs[lo] * (hi - k) + xs[hi] * (k - lo)

    p95 = percentile95(lats)
    perf = statistics.median(pidx) if pidx else None
    floor = float((config.get("capability_information_latency") or {}).get("measurement_floor_seconds", 0.001))
    cilr = perf / max(p95, floor) if perf is not None and p95 is not None else None
    return {
        "worker_records": len(workers),
        "exact_token_rows": exact_token_rows,
        "total_tokens": total_tokens if exact_token_rows else None,
        "verified_utility_units": utility,
        "token_quality_efficiency": tqe,
        "code_quality_score": statistics.fmean(cqs) if cqs else None,
        "verified_innovation_score": statistics.fmean(viss) if viss else None,
        "performance_index_median": perf,
        "p95_information_latency_seconds": p95,
        "capability_information_latency_ratio": cilr,
        "missing_token_fraction": 1.0 - (exact_token_rows / len(workers)) if workers else None,
        "hcu_confidence": hcu_forecast(workers, config),
    }


def _source_summary(name: str, data: dict[str, Any], raw: bytes, path: str) -> dict[str, Any]:
    generated_at = canonical_ts(data.get("generated_at"))
    out: dict[str, Any] = {
        "name": name,
        "path": path,
        "generated_at": generated_at,
        "sha256": sha256_bytes(raw),
    }
    if name == "swarm":
        workers = data.get("workers") if isinstance(data.get("workers"), dict) else {}
        out["worker_records"] = inum(workers.get("worker_records"))
        out["exact_usage_rows"] = inum(workers.get("exact_usage_rows"))
        out["total_tokens"] = inum(workers.get("total_tokens"))
    elif name == "forge":
        out["evaluations"] = inum(data.get("evaluations"))
        out["accepted_deltas"] = inum(data.get("accepted_deltas"))
    elif name == "distillery":
        out["accepted_packets"] = inum(data.get("accepted_packets"))
        out["accepted_dataset_tokens"] = inum(data.get("accepted_dataset_tokens"))
    return out


def read_live_snapshot(repo: Path, authority_epoch: str) -> dict[str, Any]:
    sources: dict[str, dict[str, Any]] = {}
    times: list[dt.datetime] = []
    preimage_sources: dict[str, Any] = {}
    for name, rel in LIVE_SOURCE_PATHS.items():
        path = repo / rel
        raw = read_bytes_stable(path)
        data = decode_json_bytes(raw, path)
        summary = _source_summary(name, data, raw, rel)
        parsed = parse_ts(summary["generated_at"])
        assert parsed is not None
        times.append(parsed)
        sources[name] = summary
        preimage_sources[name] = {
            "path": rel,
            "generated_at": summary["generated_at"],
            "sha256": summary["sha256"],
        }
    preimage = {
        "schema": SNAPSHOT_SCHEMA,
        "authority_epoch": authority_epoch,
        "sources": preimage_sources,
    }
    snapshot_id = sha256_json(preimage)
    for summary in sources.values():
        summary["snapshot_id"] = snapshot_id
    return {
        "schema": SNAPSHOT_SCHEMA,
        "authority_epoch": authority_epoch,
        "snapshot_id": snapshot_id,
        "observed_from": min(times).astimezone(dt.timezone.utc).isoformat(),
        "observed_through": max(times).astimezone(dt.timezone.utc).isoformat(),
        "sources": sources,
    }


def _snapshot_times(snapshot: dict[str, Any]) -> dict[str, dt.datetime] | None:
    sources = snapshot.get("sources")
    if not isinstance(sources, dict):
        return None
    out: dict[str, dt.datetime] = {}
    for name in LIVE_SOURCE_PATHS:
        row = sources.get(name)
        if not isinstance(row, dict):
            return None
        ts = parse_ts(row.get("generated_at"))
        if ts is None:
            return None
        out[name] = ts
    return out


def publication_decision(previous: dict[str, Any], current_snapshot: dict[str, Any]) -> dict[str, Any]:
    """Fail closed against a late writer regressing a newer published snapshot."""
    if not previous:
        return {"allowed": True, "classification": "FRESH_INITIAL_PUBLICATION"}
    current_epoch = str(current_snapshot.get("authority_epoch") or "")
    previous_epoch = str(previous.get("authority_epoch") or "")
    if previous_epoch and previous_epoch != current_epoch:
        return {
            "allowed": True,
            "classification": "FRESH_AUTHORITY_SUCCESSOR_REPLACES_HISTORICAL",
            "previous_authority_epoch": previous_epoch,
        }
    prev_snapshot = previous.get("input_snapshot")
    if not isinstance(prev_snapshot, dict):
        prev_generated = parse_ts(previous.get("generated_at"))
        current_from = parse_ts(current_snapshot.get("observed_from"))
        current_through = parse_ts(current_snapshot.get("observed_through"))
        if prev_generated is not None and current_through is not None and prev_generated > current_through:
            return {"allowed": False, "classification": "OUT_OF_ORDER_LEGACY_NEWER_UNRESOLVED"}
        if prev_generated is not None and current_from is not None and prev_generated >= current_from:
            return {"allowed": False, "classification": "LEGACY_OVERLAP_UNMEASURED_FAIL_CLOSED"}
        return {"allowed": True, "classification": "FRESH_REPLACES_LEGACY_UNMEASURED"}
    if prev_snapshot.get("snapshot_id") == current_snapshot.get("snapshot_id"):
        return {"allowed": True, "classification": "SAME_SNAPSHOT_IDEMPOTENT_REPLAY"}
    prev_times = _snapshot_times(prev_snapshot)
    cur_times = _snapshot_times(current_snapshot)
    if prev_times is None or cur_times is None:
        return {"allowed": False, "classification": "SNAPSHOT_ORDER_UNMEASURED_FAIL_CLOSED"}
    older = [name for name in LIVE_SOURCE_PATHS if cur_times[name] < prev_times[name]]
    equal = [name for name in LIVE_SOURCE_PATHS if cur_times[name] == prev_times[name]]
    if older:
        return {
            "allowed": False,
            "classification": "OUT_OF_ORDER_INPUT_FAIL_CLOSED",
            "regressed_sources": older,
        }
    if len(equal) == len(LIVE_SOURCE_PATHS):
        return {"allowed": False, "classification": "SAME_TIMESTAMPS_DIFFERENT_BYTES_CONFLICT"}
    return {"allowed": True, "classification": "FRESH_SUCCESSOR_SNAPSHOT"}


def consumer_freshness(published: dict[str, Any], current_snapshot: dict[str, Any]) -> str:
    """Classify a published aggregate against the now-current live input snapshot."""
    if not published:
        return "UNMEASURED_NO_PUBLISHED_AGGREGATE"
    if str(published.get("authority_epoch") or "") != str(current_snapshot.get("authority_epoch") or ""):
        return "HISTORICAL_AUTHORITY_EPOCH"
    prior = published.get("input_snapshot")
    if not isinstance(prior, dict):
        return "UNMEASURED_LEGACY_NO_SNAPSHOT_IDENTITY"
    if prior.get("snapshot_id") == current_snapshot.get("snapshot_id"):
        return "FRESH"
    prev_times = _snapshot_times(prior)
    cur_times = _snapshot_times(current_snapshot)
    if prev_times is None or cur_times is None:
        return "UNMEASURED_SNAPSHOT_ORDER"
    newer = [name for name in LIVE_SOURCE_PATHS if cur_times[name] > prev_times[name]]
    older = [name for name in LIVE_SOURCE_PATHS if cur_times[name] < prev_times[name]]
    if newer and not older:
        return "STALE_NEWER_LIVE_INPUT"
    if older and not newer:
        return "UNMEASURED_PUBLISHED_NEWER_THAN_OBSERVED_INPUT"
    return "UNMEASURED_PARTIAL_ORDER_MIXED_SNAPSHOT"


def bind_snapshot_inputs(snapshot: dict[str, Any], config: dict[str, Any], workers: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> dict[str, Any]:
    """Extend the live snapshot with every input family that can change the result digest."""
    live_preimage = {
        name: {
            "path": row["path"],
            "generated_at": row["generated_at"],
            "sha256": row["sha256"],
        }
        for name, row in snapshot["sources"].items()
    }
    full_preimage = {
        "schema": SNAPSHOT_SCHEMA,
        "authority_epoch": snapshot["authority_epoch"],
        "live_sources": live_preimage,
        "config_sha256": sha256_json(config),
        "workers_sha256": sha256_json(workers),
        "deltas_sha256": sha256_json(deltas),
    }
    full_id = sha256_json(full_preimage)
    out = json.loads(json.dumps(snapshot))
    out["live_snapshot_id"] = snapshot["snapshot_id"]
    out["snapshot_id"] = full_id
    out["config_sha256"] = full_preimage["config_sha256"]
    out["workers_sha256"] = full_preimage["workers_sha256"]
    out["deltas_sha256"] = full_preimage["deltas_sha256"]
    for row in out["sources"].values():
        row["snapshot_id"] = full_id
    return out


def live_source_metrics(snapshot: dict[str, Any]) -> dict[str, Any]:
    s = snapshot["sources"]
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "swarm_generated_at": s["swarm"]["generated_at"],
        "swarm_worker_records": s["swarm"].get("worker_records"),
        "swarm_exact_usage_rows": s["swarm"].get("exact_usage_rows"),
        "swarm_total_tokens": s["swarm"].get("total_tokens"),
        "forge_generated_at": s["forge"]["generated_at"],
        "forge_evaluations": s["forge"].get("evaluations"),
        "forge_accepted_deltas": s["forge"].get("accepted_deltas"),
        "distillery_generated_at": s["distillery"]["generated_at"],
        "distillery_accepted_packets": s["distillery"].get("accepted_packets"),
        "distillery_accepted_dataset_tokens": s["distillery"].get("accepted_dataset_tokens"),
    }


def build_result(config: dict[str, Any], workers: list[dict[str, Any]], deltas: list[dict[str, Any]], snapshot: dict[str, Any]) -> dict[str, Any]:
    workers_copy = json.loads(json.dumps(workers))
    deltas_copy = json.loads(json.dumps(deltas))
    attach_delta_metrics(workers_copy, deltas_copy, config)
    bound_snapshot = bind_snapshot_inputs(snapshot, config, workers, deltas)
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_at": bound_snapshot["observed_through"],
        "generation_class": "BOUNDED_INPUT_SNAPSHOT_DETERMINISTIC_PUBLISHER",
        "authority_epoch": bound_snapshot["authority_epoch"],
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "config_sha256": sha256_json(config),
        "input_snapshot": bound_snapshot,
        "live_source_metrics": live_source_metrics(bound_snapshot),
        "freshness": {
            "status": "CURRENT_AT_BUILD",
            "consumer_rule": "NEWER_LIVE_INPUT_OR_AUTHORITY_MISMATCH_MUST_NOT_BE_PRESENTED_AS_CURRENT",
            "out_of_order_writer_rule": "OLDER_OR_PARTIALLY_OLDER_SNAPSHOT_CANNOT_REPLACE_NEWER_PUBLICATION",
        },
        "worker_record_count": len(workers_copy),
        "aggregate": aggregate(workers_copy, config),
        "workers": workers_copy,
        "anti_goodhart": config.get("anti_goodhart"),
        "selection_policy": config.get("selection_policy"),
        "runtime_credit_added": 0,
        "note": "Derived measurement only. It cannot mint canonical truth or runtime/model/training credit.",
    }
    result["result_digest_sha256"] = sha256_json(result)
    return result


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "UNKNOWN"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def worker_table_rows(workers: list[dict[str, Any]], limit: int = 100) -> list[str]:
    lines = [
        "| worker | tokens | TQE | CQS | VIS | perf idx | info latency s | CILR | lineage | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    ranked = sorted(
        workers,
        key=lambda r: (
            -(fnum(r.get("token_quality_efficiency")) or -1),
            str(r.get("worker_id") or r.get("organ") or ""),
        ),
    )
    for r in ranked[:limit]:
        status = str(r.get("status") or r.get("runtime_status") or "OBSERVED")
        lines.append(
            f"| {worker_key(r)} | {fmt(r.get('total_tokens'),0)} | "
            f"{fmt(r.get('token_quality_efficiency'),6)} | {fmt(r.get('code_quality_score'),2)} | "
            f"{fmt(r.get('verified_innovation_score'),2)} | {fmt(r.get('performance_index'),3)} | "
            f"{fmt(r.get('information_latency_seconds'),3)} | "
            f"{fmt(r.get('capability_information_latency_ratio'),3)} | "
            f"`{str(r.get('evidence_lineage_resolved') or 'UNKNOWN')[:80]}` | {status} |"
        )
    if len(workers) > limit:
        lines.append(f"| … | … | … | … | … | … | … | … | … | {len(workers)-limit} additional rows in JSON |")
    return lines


def markdown(result: dict[str, Any]) -> str:
    a = result["aggregate"]
    h = a["hcu_confidence"]
    p = h.get("forecast_probability")
    live = result["live_source_metrics"]
    lines = [
        AUTO_BEGIN,
        "## GO Collective Recursive-Improvement Metrics",
        f"Generated from bounded live snapshot through: `{result['generated_at']}`  ",
        f"Schema: `{SCHEMA}`  ",
        f"Authority epoch: `{result['authority_epoch']}`  ",
        f"Input snapshot: `{result['input_snapshot']['snapshot_id']}`  ",
        f"Result digest: `{result['result_digest_sha256']}`  ",
        "",
        "### Live bounded source snapshot",
        "| Metric | Current |",
        "|---|---:|",
        f"| Swarm total tokens | {fmt(live.get('swarm_total_tokens'),0)} |",
        f"| Forge evaluations | {fmt(live.get('forge_evaluations'),0)} |",
        f"| Forge accepted deltas | {fmt(live.get('forge_accepted_deltas'),0)} |",
        f"| Distillery accepted packets | {fmt(live.get('distillery_accepted_packets'),0)} |",
        f"| Distillery accepted dataset tokens | {fmt(live.get('distillery_accepted_dataset_tokens'),0)} |",
        "",
        "### Aggregate",
        "| Metric | Current | Evidence note |",
        "|---|---:|---|",
        f"| Worker records observed | {a['worker_records']} | all explicit records + available Free Swarm rows |",
        f"| Exact-token rows | {a['exact_token_rows']} | missing tokens remain UNKNOWN |",
        f"| Total exact tokens | {fmt(a['total_tokens'],0)} | no historical estimate added |",
        f"| Token Quality Efficiency / 1k tokens | {fmt(a['token_quality_efficiency'],6)} | accepted verified utility only |",
        f"| Code Quality Score / 100 | {fmt(a['code_quality_score'],2)} | UNKNOWN when evidence coverage is insufficient |",
        f"| Verified Innovation Score / 100 | {fmt(a['verified_innovation_score'],2)} | self-reported novelty ignored |",
        f"| Median performance index | {fmt(a['performance_index_median'],3)} | same benchmark family only |",
        f"| p95 information latency (s) | {fmt(a['p95_information_latency_seconds'],3)} | producer evidence -> first downstream consumption |",
        f"| Capability / latency ratio | {fmt(a['capability_information_latency_ratio'],3)} | unbounded; raw perf+latency remain visible |",
        f"| HCU_TARGET_100_GO forecast | {fmt(100*p,1) if p is not None else 'UNKNOWN'}% | {h.get('calibration_state')} forecast, not completion % |",
        "",
        "### HCU milestone forecast vector",
        "| milestone | p |",
        "|---|---:|",
    ]
    for key, value in h.get("milestone_probabilities", {}).items():
        lines.append(f"| `{key}` | {100*float(value):.1f}% |")
    lines += [
        "",
        "### Per-worker view",
        *worker_table_rows(result["workers"]),
        "",
        "### Anti-Goodhart health",
        "- No single scalar selects winners; use Pareto comparison plus hard correctness/provenance/security/effect gates.",
        "- Scores may decrease after stronger measurement or counterevidence.",
        "- Shared model/source/prompt/orchestration ancestry is correlated evidence and must be collapsed.",
        "- Metric-definition changes are versioned, shadow-run, and do not rewrite raw history.",
        "- Confidence forecasts are calibrated on resolved outcomes using Brier/log loss when enough observations exist.",
        "- Any newer live source snapshot makes this aggregate STALE until the same publisher emits a successor.",
        AUTO_END,
        "",
    ]
    return "\n".join(lines)


def replace_block(text: str, block: str) -> str:
    if AUTO_BEGIN in text and AUTO_END in text:
        before = text.split(AUTO_BEGIN, 1)[0]
        after = text.split(AUTO_END, 1)[1]
        return before.rstrip() + "\n\n" + block.rstrip() + "\n" + after.lstrip()
    return text.rstrip() + "\n\n" + block


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def freshness_receipt(result: dict[str, Any], decision: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": FRESHNESS_RECEIPT_SCHEMA,
        "authority_epoch": result["authority_epoch"],
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "input_snapshot_id": result["input_snapshot"]["snapshot_id"],
        "live_snapshot_id": result["input_snapshot"].get("live_snapshot_id"),
        "source_snapshot": result["input_snapshot"]["sources"],
        "publication_decision": decision,
        "result_digest_sha256": result["result_digest_sha256"],
        "previous_result_digest_sha256": previous.get("result_digest_sha256") if previous else None,
        "same_bounded_inputs_are_digest_stable": True,
        "forge_distillery_swarm_share_snapshot_identity": all(
            row.get("snapshot_id") == result["input_snapshot"]["snapshot_id"]
            for row in result["input_snapshot"]["sources"].values()
        ),
        "runtime_credit_added": 0,
        "scope": "COLLECTIVE_METRICS_FRESHNESS_AND_PUBLICATION_ORDER_ONLY",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--artifacts", type=Path, default=Path("/artifacts/clay-entityos-swarm"))
    ap.add_argument("--output-json", type=Path, default=None)
    ap.add_argument("--output-md", type=Path, default=None)
    ap.add_argument("--freshness-receipt", type=Path, default=None)
    ap.add_argument("--update-readme", action="store_true")
    ap.add_argument("--check-current", action="store_true", help="fail unless the published aggregate is current against live inputs")
    args = ap.parse_args()

    repo = args.repo.resolve()
    out_json = args.output_json or (repo / "free swarm/GO_COLLECTIVE_METRICS.json")
    out_md = args.output_md or (repo / "free swarm/GO_COLLECTIVE_METRICS.md")
    receipt_path = args.freshness_receipt or (repo / "research_entity/continuity/go_metrics/COLLECTIVE_METRICS_FRESHNESS_RECEIPT_V1.json")
    lock_path = repo / "free swarm/.go_collective_metrics.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        authority_epoch = current_authority_epoch(repo)
        live_snapshot = read_live_snapshot(repo, authority_epoch)
        previous = read_json(out_json)

        if args.check_current:
            status = consumer_freshness(previous, live_snapshot)
            print(status)
            return 0 if status == "FRESH" else 3

        config = load_config(repo)
        if config.get("schema") != "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1":
            raise SystemExit("GO_METRICS_CONFIG_REQUIRED")
        workers = explicit_worker_rows(repo)
        workers.extend(free_swarm_rows(args.artifacts))
        deltas = delta_rows(repo)
        result = build_result(config, workers, deltas, live_snapshot)
        decision = publication_decision(previous, result["input_snapshot"])
        if not decision.get("allowed"):
            print(json.dumps({
                "status": "PUBLICATION_BLOCKED",
                "decision": decision,
                "current_snapshot_id": result["input_snapshot"]["snapshot_id"],
            }, sort_keys=True))
            return 4

        md = markdown(result)
        atomic_write_text(out_json, json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        atomic_write_text(out_md, md)
        atomic_write_text(
            receipt_path,
            json.dumps(freshness_receipt(result, decision, previous), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        )

        if args.update_readme:
            readme = repo / "free swarm/README.md"
            current = readme.read_text(encoding="utf-8") if readme.exists() else "# Free Swarm\n"
            atomic_write_text(readme, replace_block(current, md))

        print(out_json)
        print(out_md)
        print(receipt_path)
        h = result["aggregate"]["hcu_confidence"]
        print(json.dumps({
            "workers": len(result["workers"]),
            "tqe": result["aggregate"]["token_quality_efficiency"],
            "cqs": result["aggregate"]["code_quality_score"],
            "vis": result["aggregate"]["verified_innovation_score"],
            "cilr": result["aggregate"]["capability_information_latency_ratio"],
            "hcu_forecast_probability": h.get("forecast_probability"),
            "calibration_state": h.get("calibration_state"),
            "authority_epoch": result["authority_epoch"],
            "snapshot_id": result["input_snapshot"]["snapshot_id"],
            "result_digest_sha256": result["result_digest_sha256"],
            "publication_decision": decision["classification"],
        }, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
