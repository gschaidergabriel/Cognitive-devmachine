#!/usr/bin/env python3
"""Collective recursive-improvement metrics for Clay ``go``.

This is the single existing GO collective-metrics publisher.  It remains an
offline/local measurement surface: no provider call, no credential lookup and no
runtime/model/training credit.

Supervisor 8.76/8.77 added a hard metrology requirement that the publisher must
not let a stale aggregate supersede newer live Swarm/Forge/Distillery inputs.
Publication therefore starts from one bounded, digest-bound snapshot of those
three live surfaces plus the current supervisor inbox, then fails closed against
an already-published newer writer.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any, Iterable

SCHEMA = "CLAY_GO_COLLECTIVE_METRICS/v1"
WORKER_SCHEMA = "CLAY_GO_WORKER_METRICS/v1"
FRESHNESS_SCHEMA = "CLAY_GO_COLLECTIVE_METRICS_FRESHNESS/v1"
FRESHNESS_RECEIPT_SCHEMA = "COLLECTIVE_METRICS_FRESHNESS_RECEIPT/v1"
AUTO_BEGIN = "<!-- GO_COLLECTIVE_RECURSIVE_METRICS:BEGIN -->"
AUTO_END = "<!-- GO_COLLECTIVE_RECURSIVE_METRICS:END -->"
LIVE_INPUT_PATHS = {
    "swarm": Path("free swarm/LIVE_METRICS.json"),
    "forge": Path("free swarm/FORGE_LIVE.json"),
    "distillery": Path("free swarm/DISTILLERY_LIVE.json"),
    "authority": Path("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"),
}


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def read_bytes(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError:
        return None


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
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def epoch_key(value: Any) -> tuple[int, ...] | None:
    if value is None:
        return None
    parts = str(value).strip().split(".")
    if not parts or any(not p.isdigit() for p in parts):
        return None
    return tuple(int(p) for p in parts)


def fnum(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def inum(value: Any) -> int | None:
    value = fnum(value)
    return int(value) if value is not None else None


def usage(row: dict[str, Any]) -> tuple[int | None, int | None, int | None]:
    raw = row.get("usage")
    if not isinstance(raw, dict):
        raw = {}
    inp = inum(raw.get("input_tokens", raw.get("prompt_tokens", row.get("input_tokens"))))
    out = inum(raw.get("output_tokens", raw.get("completion_tokens", row.get("output_tokens"))))
    total = inum(raw.get("total_tokens", row.get("total_tokens")))
    if total is None and inp is not None and out is not None:
        total = inp + out
    return inp, out, total


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(raw)


def load_config(repo: Path) -> dict[str, Any]:
    return read_json(repo / "research_entity/continuity/go_metrics/GO_METRICS_CONFIG_V1.json")


def accepted_delta(row: dict[str, Any]) -> bool:
    status = str(row.get("status") or "").lower()
    if status not in {"accepted", "pass", "integrated", "verified"}:
        return False
    imp = fnum(row.get("relative_improvement_pct"))
    runs = inum(row.get("reproducible_runs")) or 0
    hard_failed = sum((inum(row.get(key)) or 0) for key in (
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
    p, f = p or 0, f or 0
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
    coverage = sum(float(weights.get(k, 0.0)) for k, value in components.items() if value is not None)
    min_cov = float((config.get("code_quality") or {}).get("min_evidence_coverage", 0.60))
    if coverage < min_cov:
        return None, coverage
    score = 100.0 * sum(float(weights.get(k, 0.0)) * (value or 0.0) for k, value in components.items())
    return score, coverage


def innovation_score(row: dict[str, Any], config: dict[str, Any]) -> float | None:
    inv = row.get("innovation")
    if not isinstance(inv, dict) or inv.get("verified") is not True:
        return None
    weights = (config.get("innovation") or {}).get("weights") or {}
    mapping = {
        "nonduplicate_mechanism_novelty": "novelty",
        "measured_useful_effect": "measured_effect",
        "transferability_reuse": "transferability",
        "falsifiability_causal_discriminability": "falsifiability",
    }
    values: dict[str, float] = {}
    for target, source in mapping.items():
        value = fnum(inv.get(source))
        if value is None:
            return None
        if value > 1:
            value /= 100.0
        values[target] = max(0.0, min(value, 1.0))
    return 100.0 * sum(float(weights.get(key, 0.0)) * value for key, value in values.items())


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
    baseline, new = fnum(bench.get("baseline")), fnum(bench.get("new"))
    if baseline is None or new is None or baseline <= 0 or new <= 0:
        return None
    return new / baseline if bench.get("higher_is_better", True) else baseline / new


def explicit_worker_rows(repo: Path) -> list[dict[str, Any]]:
    root = repo / "research_entity/continuity/go_metrics/worker_records"
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for path in sorted(root.rglob("*.json")):
        row = read_json(path)
        if row:
            row["_record_path"] = path.relative_to(repo).as_posix()
            rows.append(row)
    return rows


def free_swarm_rows(artifacts: Path | None) -> list[dict[str, Any]]:
    if artifacts is None or not artifacts.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw in iter_jsonl(sorted(artifacts.rglob("workers.jsonl"))):
        inp, out, total = usage(raw)
        provider = str(raw.get("provider") or "unknown")
        model = str(raw.get("model") or "unknown")
        rows.append({
            "schema": WORKER_SCHEMA,
            "macrocycle_id": raw.get("macrocycle_id") or raw.get("go_macrocycle_id") or "MACROCYCLE_ID_UNRESOLVED",
            "worker_id": f"free-swarm-{raw.get('worker_serial') or raw.get('_line')}",
            "organ": f"{provider}/{model}",
            "source_class": "free_swarm",
            "provider": provider,
            "model": model,
            "evidence_lineage": f"free_swarm:{provider}:{model}",
            "started_at": None,
            "finished_at": raw.get("ts"),
            "input_tokens": inp,
            "output_tokens": out,
            "total_tokens": total,
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
        str(row.get("provider") or "unknown"), str(row.get("model") or row.get("organ") or "unknown"),
        str(row.get("prompt_lineage") or "unknown"), str(row.get("orchestration_lineage") or "unknown"),
    ])


def attach_delta_metrics(workers: list[dict[str, Any]], deltas: list[dict[str, Any]], config: dict[str, Any]) -> None:
    by_actor: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for delta in deltas:
        if not accepted_delta(delta):
            continue
        for candidate in {str(delta.get("worker_id") or ""), str(delta.get("organ") or ""), str(delta.get("model") or "")}:
            if candidate:
                by_actor[candidate].append(delta)
    for row in workers:
        matches: dict[str, dict[str, Any]] = {}
        for candidate in {worker_key(row), str(row.get("organ") or ""), str(row.get("model") or "")}:
            for delta in by_actor.get(candidate, []):
                key = str(delta.get("delta_id") or delta.get("_source")) + ":" + str(delta.get("_line"))
                matches[key] = delta
        utility = 0.0
        cqs: list[float] = []
        viss: list[float] = []
        for delta in matches.values():
            cq, _ = code_quality(delta, config)
            if cq is not None:
                cqs.append(cq)
            vis = innovation_score(delta, config)
            if vis is not None:
                viss.append(vis)
            imp = fnum(delta.get("relative_improvement_pct")) or 0.0
            runs = inum(delta.get("reproducible_runs")) or 0
            independence = fnum(delta.get("independence_factor"))
            independence = 1.0 if independence is None else independence
            utility += max(0.0, imp / 100.0) * ((cq or 0.0) / 100.0) * min(runs / 3.0, 1.0) * max(0.0, min(independence, 1.0))
        total = inum(row.get("total_tokens"))
        row["accepted_delta_count"] = len(matches)
        row["verified_utility_units"] = utility
        row["token_quality_efficiency"] = 1000.0 * utility / total if total and total > 0 else None
        row["code_quality_score"] = statistics.fmean(cqs) if cqs else None
        row["verified_innovation_score"] = statistics.fmean(viss) if viss else None
        pidx, latency = performance_index(row), information_latency(row)
        floor = float((config.get("capability_information_latency") or {}).get("measurement_floor_seconds", 0.001))
        row["performance_index"] = pidx
        row["information_latency_seconds"] = latency
        row["capability_information_latency_ratio"] = pidx / max(latency, floor) if pidx is not None and latency is not None else None
        row["evidence_lineage_resolved"] = worker_lineage(row)


def robust_median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def hcu_forecast(workers: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    hcu = config.get("hcu_confidence") or {}
    milestones = list(hcu.get("milestones") or [])
    per_lineage: dict[str, dict[str, list[float]]] = collections.defaultdict(lambda: collections.defaultdict(list))
    for row in workers:
        forecast = row.get("hcu_forecast")
        probs = forecast.get("milestone_probabilities") if isinstance(forecast, dict) else None
        if not isinstance(probs, dict):
            continue
        lineage = worker_lineage(row)
        for milestone in milestones:
            probability = fnum(probs.get(milestone))
            if probability is not None and 0 <= probability <= 1:
                per_lineage[lineage][milestone].append(probability)
    milestone_probs: dict[str, float] = {}
    for milestone in milestones:
        lineage_values = [robust_median(values.get(milestone, [])) for values in per_lineage.values()]
        resolved = robust_median([value for value in lineage_values if value is not None])
        if resolved is not None:
            milestone_probs[milestone] = resolved
    seed = (hcu.get("initial_research_baseline") or {}).get("milestone_probabilities") or {}
    seed_used = False
    for milestone in milestones:
        if milestone not in milestone_probs:
            probability = fnum(seed.get(milestone))
            if probability is not None:
                milestone_probs[milestone] = probability
                seed_used = True
    bounded = [max(0.01, min(float(milestone_probs[m]), 0.99)) for m in milestones if m in milestone_probs]
    probability = math.exp(sum(math.log(x) for x in bounded) / len(bounded)) if bounded else None
    return {
        "event": hcu.get("event"),
        "event_definition": hcu.get("event_definition"),
        "forecast_probability": probability,
        "milestone_probabilities": milestone_probs,
        "milestone_coverage": len(bounded) / len(milestones) if milestones else 0.0,
        "independent_forecast_lineages": len(per_lineage),
        "seed_used": seed_used,
        "calibration_state": "UNCALIBRATED" if seed_used or len(per_lineage) < 3 else "COLLECTING_OUTCOME_CALIBRATION",
        "brier_score": None,
        "log_loss": None,
        "note": "Forecast only; not completion percentage or canonical truth.",
    }


def aggregate(workers: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    known_tokens = [inum(row.get("total_tokens")) for row in workers]
    total_tokens = sum(value for value in known_tokens if value is not None)
    exact_rows = sum(value is not None for value in known_tokens)
    utility = sum(float(row.get("verified_utility_units") or 0.0) for row in workers)
    cqs = [value for value in (fnum(row.get("code_quality_score")) for row in workers) if value is not None]
    viss = [value for value in (fnum(row.get("verified_innovation_score")) for row in workers) if value is not None]
    latencies = sorted(value for value in (fnum(row.get("information_latency_seconds")) for row in workers) if value is not None)
    pidxs = [value for value in (fnum(row.get("performance_index")) for row in workers) if value is not None]
    p95 = None
    if latencies:
        if len(latencies) == 1:
            p95 = latencies[0]
        else:
            k = 0.95 * (len(latencies) - 1); lo, hi = math.floor(k), math.ceil(k)
            p95 = latencies[lo] if lo == hi else latencies[lo] * (hi - k) + latencies[hi] * (k - lo)
    perf = statistics.median(pidxs) if pidxs else None
    floor = float((config.get("capability_information_latency") or {}).get("measurement_floor_seconds", 0.001))
    return {
        "worker_records": len(workers),
        "exact_token_rows": exact_rows,
        "total_tokens": total_tokens if exact_rows else None,
        "verified_utility_units": utility,
        "token_quality_efficiency": 1000.0 * utility / total_tokens if total_tokens > 0 else None,
        "code_quality_score": statistics.fmean(cqs) if cqs else None,
        "verified_innovation_score": statistics.fmean(viss) if viss else None,
        "performance_index_median": perf,
        "p95_information_latency_seconds": p95,
        "capability_information_latency_ratio": perf / max(p95, floor) if perf is not None and p95 is not None else None,
        "missing_token_fraction": 1.0 - exact_rows / len(workers) if workers else None,
        "hcu_confidence": hcu_forecast(workers, config),
    }


def _decode_snapshot(raw: dict[str, bytes]) -> tuple[dict[str, dict[str, Any]], str | None]:
    decoded: dict[str, dict[str, Any]] = {}
    for name, payload in raw.items():
        try:
            value = json.loads(payload.decode("utf-8"))
        except Exception:
            return {}, f"INVALID_JSON:{name}"
        if not isinstance(value, dict):
            return {}, f"INVALID_OBJECT:{name}"
        decoded[name] = value
    return decoded, None


def capture_input_snapshot(repo: Path, attempts: int = 4) -> dict[str, Any]:
    """Read all live input bytes twice; return only an internally stable snapshot."""
    absolute = {name: repo / rel for name, rel in LIVE_INPUT_PATHS.items()}
    last_reason = "SNAPSHOT_UNSTABLE"
    for _ in range(max(1, attempts)):
        first = {name: read_bytes(path) for name, path in absolute.items()}
        if any(payload is None for payload in first.values()):
            missing = sorted(name for name, payload in first.items() if payload is None)
            return {"ok": False, "status": "MISSING_INPUT", "missing": missing}
        second = {name: read_bytes(path) for name, path in absolute.items()}
        if first != second:
            last_reason = "INPUT_CHANGED_DURING_SNAPSHOT"
            continue
        stable = {name: payload for name, payload in first.items() if payload is not None}
        decoded, error = _decode_snapshot(stable)
        if error:
            return {"ok": False, "status": error}
        authority_epoch = decoded["authority"].get("schema_version")
        if epoch_key(authority_epoch) is None:
            return {"ok": False, "status": "AUTHORITY_EPOCH_UNRESOLVED"}
        source_times: dict[str, str] = {}
        parsed_times: list[dt.datetime] = []
        for name in ("swarm", "forge", "distillery"):
            raw_ts = decoded[name].get("generated_at")
            parsed = parse_ts(raw_ts)
            if parsed is None:
                return {"ok": False, "status": f"INPUT_TIMESTAMP_UNRESOLVED:{name}"}
            parsed = parsed.astimezone(dt.timezone.utc)
            parsed_times.append(parsed)
            source_times[name] = parsed.isoformat()
        digests = {name: sha256_bytes(payload) for name, payload in stable.items()}
        identity_material = {
            "authority_epoch": str(authority_epoch),
            "sources": {name: {"sha256": digests[name], "generated_at": source_times.get(name)} for name in sorted(digests)},
        }
        snapshot_id = sha256_json(identity_material)
        return {
            "ok": True,
            "status": "FRESH_BOUNDED_SNAPSHOT",
            "schema": FRESHNESS_SCHEMA,
            "authority_epoch": str(authority_epoch),
            "snapshot_id": snapshot_id,
            "source_sha256": digests,
            "source_generated_at": source_times,
            "input_watermark": max(parsed_times).isoformat(),
            "oldest_input_at": min(parsed_times).isoformat(),
            "max_input_skew_seconds": (max(parsed_times) - min(parsed_times)).total_seconds(),
            "decoded": decoded,
        }
    return {"ok": False, "status": last_reason}


def source_metrics_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    decoded = snapshot["decoded"]
    swarm_workers = decoded["swarm"].get("workers") if isinstance(decoded["swarm"].get("workers"), dict) else {}
    deltas = decoded["swarm"].get("deltas") if isinstance(decoded["swarm"].get("deltas"), dict) else {}
    forge, dist = decoded["forge"], decoded["distillery"]
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "free_swarm_live_metrics_generated_at": snapshot["source_generated_at"]["swarm"],
        "worker_records": inum(swarm_workers.get("worker_records")),
        "exact_usage_rows": inum(swarm_workers.get("exact_usage_rows")),
        "input_tokens": inum(swarm_workers.get("input_tokens")),
        "output_tokens": inum(swarm_workers.get("output_tokens")),
        "total_tokens": inum(swarm_workers.get("total_tokens")),
        "swarm_evident_accepted_deltas": inum(deltas.get("accepted")),
        "forge_generated_at": snapshot["source_generated_at"]["forge"],
        "forge_evaluations": inum(forge.get("evaluations")),
        "forge_accepted_deltas": inum(forge.get("accepted_deltas")),
        "distillery_generated_at": snapshot["source_generated_at"]["distillery"],
        "distillery_collected_source_tokens": inum(dist.get("collected_source_tokens")),
        "distillery_accepted_packets": inum(dist.get("accepted_packets")),
        "distillery_accepted_dataset_tokens": inum(dist.get("accepted_dataset_tokens")),
    }


def stable_measurement_digest(result: dict[str, Any]) -> str:
    """Digest only evidence-bearing deterministic fields, excluding wall-clock publication time."""
    material = {
        "schema": result.get("schema"),
        "authority_epoch": result.get("authority_epoch"),
        "config_sha256": result.get("config_sha256"),
        "snapshot_id": ((result.get("freshness") or {}).get("snapshot_id")),
        "source_metrics": result.get("source_metrics"),
        "aggregate": result.get("aggregate"),
        "anti_goodhart": result.get("anti_goodhart"),
        "selection_policy": result.get("selection_policy"),
        "runtime_credit_added": result.get("runtime_credit_added"),
    }
    return sha256_json(material)


def publication_decision(existing: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    if not existing:
        return {"allow": True, "status": "NO_EXISTING_PUBLICATION"}
    current_epoch = epoch_key(candidate.get("authority_epoch"))
    existing_epoch = epoch_key(existing.get("authority_epoch"))
    if current_epoch is None:
        return {"allow": False, "status": "CANDIDATE_AUTHORITY_UNRESOLVED"}
    if existing_epoch is not None and existing_epoch > current_epoch:
        return {"allow": False, "status": "HISTORICAL_AUTHORITY_EPOCH"}
    if existing_epoch is not None and existing_epoch < current_epoch:
        return {"allow": True, "status": "SUPERSEDE_HISTORICAL_AUTHORITY_EPOCH"}
    existing_fresh = existing.get("freshness") if isinstance(existing.get("freshness"), dict) else {}
    candidate_fresh = candidate.get("freshness") if isinstance(candidate.get("freshness"), dict) else {}
    old_watermark = parse_ts(existing_fresh.get("input_watermark") or existing.get("generated_at"))
    new_watermark = parse_ts(candidate_fresh.get("input_watermark"))
    if new_watermark is None:
        return {"allow": False, "status": "CANDIDATE_WATERMARK_UNRESOLVED"}
    if old_watermark is not None and old_watermark > new_watermark:
        return {"allow": False, "status": "OUT_OF_ORDER_OLDER_WRITER"}
    if old_watermark == new_watermark:
        old_snapshot, new_snapshot = existing_fresh.get("snapshot_id"), candidate_fresh.get("snapshot_id")
        if old_snapshot and new_snapshot and old_snapshot != new_snapshot:
            return {"allow": False, "status": "WATERMARK_COLLISION_DIFFERENT_SNAPSHOT"}
        if existing.get("measurement_digest_sha256") == candidate.get("measurement_digest_sha256"):
            return {"allow": False, "status": "IDEMPOTENT_ALREADY_PUBLISHED", "idempotent": True}
    return {"allow": True, "status": "NEWER_OR_CHANGED_MEASUREMENT"}


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "UNKNOWN"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def worker_table_rows(workers: list[dict[str, Any]], limit: int = 100) -> list[str]:
    lines = ["| worker | tokens | TQE | CQS | VIS | perf idx | info latency s | CILR | lineage | status |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    ranked = sorted(workers, key=lambda row: (-(fnum(row.get("token_quality_efficiency")) or -1), worker_key(row)))
    for row in ranked[:limit]:
        status = str(row.get("status") or row.get("runtime_status") or "OBSERVED")
        lines.append(
            f"| {worker_key(row)} | {fmt(row.get('total_tokens'),0)} | {fmt(row.get('token_quality_efficiency'),6)} | "
            f"{fmt(row.get('code_quality_score'),2)} | {fmt(row.get('verified_innovation_score'),2)} | "
            f"{fmt(row.get('performance_index'),3)} | {fmt(row.get('information_latency_seconds'),3)} | "
            f"{fmt(row.get('capability_information_latency_ratio'),3)} | `{str(row.get('evidence_lineage_resolved') or 'UNKNOWN')[:80]}` | {status} |"
        )
    return lines


def markdown(result: dict[str, Any]) -> str:
    aggregate_value = result["aggregate"]
    hcu = aggregate_value["hcu_confidence"]
    probability = hcu.get("forecast_probability")
    freshness = result["freshness"]
    lines = [
        AUTO_BEGIN, "## GO Collective Recursive-Improvement Metrics",
        f"Generated: `{result['generated_at']}`  ", f"Authority: `{result['authority_epoch']}`  ",
        f"Snapshot: `{freshness['snapshot_id']}`  ", f"Input watermark: `{freshness['input_watermark']}`  ", "",
        "### Aggregate", "| Metric | Current | Evidence note |", "|---|---:|---|",
        f"| Worker records observed | {aggregate_value['worker_records']} | explicit records + available Free Swarm artifact rows |",
        f"| Total exact tokens | {fmt(aggregate_value['total_tokens'],0)} | historical estimates not invented |",
        f"| Token Quality Efficiency / 1k tokens | {fmt(aggregate_value['token_quality_efficiency'],6)} | verified utility only |",
        f"| Code Quality Score / 100 | {fmt(aggregate_value['code_quality_score'],2)} | UNKNOWN under insufficient evidence |",
        f"| Verified Innovation Score / 100 | {fmt(aggregate_value['verified_innovation_score'],2)} | self-report ignored |",
        f"| HCU_TARGET_100_GO forecast | {fmt(100*probability,1) if probability is not None else 'UNKNOWN'}% | {hcu.get('calibration_state')} forecast, not completion |",
        "", "### Bounded live snapshot", "| surface | generated_at | sha256 |", "|---|---|---|",
    ]
    for name in ("swarm", "forge", "distillery"):
        lines.append(f"| {name} | `{freshness['source_generated_at'][name]}` | `{freshness['source_sha256'][name]}` |")
    lines += ["", "### Per-worker view", *worker_table_rows(result["workers"]), "",
              "### Anti-Goodhart health",
              "- Stale aggregate output cannot supersede a newer bounded live snapshot.",
              "- Authority-epoch regressions fail closed; historical snapshots remain evidence but not current state.",
              "- Shared model/source/prompt/orchestration ancestry is correlated evidence and must be collapsed.", AUTO_END, ""]
    return "\n".join(lines)


def replace_block(text: str, block: str) -> str:
    if AUTO_BEGIN in text and AUTO_END in text:
        before = text.split(AUTO_BEGIN, 1)[0]
        after = text.split(AUTO_END, 1)[1]
        return before.rstrip() + "\n\n" + block.rstrip() + "\n" + after.lstrip()
    return text.rstrip() + "\n\n" + block


def make_receipt(candidate: dict[str, Any], decision: dict[str, Any], *, published: bool) -> dict[str, Any]:
    return {
        "schema": FRESHNESS_RECEIPT_SCHEMA,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authority_epoch": candidate.get("authority_epoch"),
        "snapshot_id": ((candidate.get("freshness") or {}).get("snapshot_id")),
        "input_watermark": ((candidate.get("freshness") or {}).get("input_watermark")),
        "measurement_digest_sha256": candidate.get("measurement_digest_sha256"),
        "publication_decision": decision,
        "published": published,
        "tests_or_runtime_credit_added": 0,
        "scope": "COLLECTIVE_METRICS_FRESHNESS_AND_ORDERING_ONLY",
        "whole_entityos_hcu_credit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--artifacts", type=Path, default=Path("/artifacts/clay-entityos-swarm"))
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    parser.add_argument("--receipt-json", type=Path, default=None)
    parser.add_argument("--update-readme", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    snapshot = capture_input_snapshot(repo)
    if not snapshot.get("ok"):
        print(json.dumps({"schema": FRESHNESS_RECEIPT_SCHEMA, "published": False, "status": snapshot.get("status")}, sort_keys=True))
        return 2

    config = load_config(repo)
    if config.get("schema") != "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1":
        raise SystemExit("GO_METRICS_CONFIG_REQUIRED")
    workers = explicit_worker_rows(repo)
    workers.extend(free_swarm_rows(args.artifacts))
    attach_delta_metrics(workers, delta_rows(repo), config)

    freshness = {key: value for key, value in snapshot.items() if key not in {"ok", "decoded"}}
    result = {
        "schema": SCHEMA,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "authority_epoch": snapshot["authority_epoch"],
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "config_sha256": sha256_json(config),
        "worker_record_count": len(workers),
        "source_metrics": source_metrics_from_snapshot(snapshot),
        "freshness": freshness,
        "aggregate": aggregate(workers, config),
        "workers": workers,
        "anti_goodhart": config.get("anti_goodhart"),
        "selection_policy": config.get("selection_policy"),
        "runtime_credit_added": 0,
        "note": "Derived measurement only. It cannot mint canonical truth or runtime/model/training credit.",
    }
    result["measurement_digest_sha256"] = stable_measurement_digest(result)
    out_json = args.output_json or (repo / "free swarm/GO_COLLECTIVE_METRICS.json")
    out_md = args.output_md or (repo / "free swarm/GO_COLLECTIVE_METRICS.md")
    existing = read_json(out_json)
    decision = publication_decision(existing, result)
    published = False
    if decision.get("allow"):
        atomic_write_text(out_json, json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        atomic_write_text(out_md, markdown(result))
        if args.update_readme:
            readme = repo / "free swarm/README.md"
            current = readme.read_text(encoding="utf-8") if readme.exists() else "# Free Swarm\n"
            atomic_write_text(readme, replace_block(current, markdown(result)))
        published = True
    receipt = make_receipt(result, decision, published=published)
    if args.receipt_json:
        target = args.receipt_json if args.receipt_json.is_absolute() else repo / args.receipt_json
        atomic_write_text(target, json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, sort_keys=True, ensure_ascii=False))
    if decision.get("idempotent"):
        return 0
    return 0 if published else 3


if __name__ == "__main__":
    raise SystemExit(main())
