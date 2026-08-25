#!/usr/bin/env python3
"""Collective recursive-improvement metrics for Clay `go`.

Offline/local collector. It reads append-only worker evidence plus existing Free Swarm
worker artifacts and architecture-delta adjudications, derives a multi-objective table,
and writes deterministic JSON/Markdown. It performs no provider call, reads no provider
credential, and grants no canonical runtime/model/training credit.

Scores are descriptive proxies behind hard evidence gates. Raw fields stay visible.
UNKNOWN is preferred over invented precision.

Supervisor 8.76/8.77 freshness law is enforced in this existing publisher path: the
canonical Swarm, Forge and Distillery live mirrors are bound into one bounded snapshot,
selected supervisor authority is bound explicitly, result identity is deterministic,
and an advisory file lock plus compare-before-replace gate prevents an older writer
from regressing a newer publication.
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
import tempfile
from typing import Any, Iterable

SCHEMA = "CLAY_GO_COLLECTIVE_METRICS/v1"
WORKER_SCHEMA = "CLAY_GO_WORKER_METRICS/v1"
SOURCE_SNAPSHOT_SCHEMA = "CLAY_GO_COLLECTIVE_METRICS_SOURCE_SNAPSHOT/v1"
FRESHNESS_SCHEMA = "CLAY_GO_COLLECTIVE_METRICS_FRESHNESS/v1"
FRESHNESS_RECEIPT_SCHEMA = "COLLECTIVE_METRICS_FRESHNESS_RECEIPT/v1"
MAX_SOURCE_SKEW_SECONDS = 120.0
AUTO_BEGIN = "<!-- GO_COLLECTIVE_RECURSIVE_METRICS:BEGIN -->"
AUTO_END = "<!-- GO_COLLECTIVE_RECURSIVE_METRICS:END -->"


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


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


def sha256_json(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


def load_config(repo: Path) -> dict[str, Any]:
    return read_json(repo / "research_entity/continuity/go_metrics/GO_METRICS_CONFIG_V1.json")


def epoch_key(value: Any) -> tuple[int, ...] | None:
    if not isinstance(value, (str, int, float)):
        return None
    parts = str(value).strip().split(".")
    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        return None


def current_authority_binding(repo: Path) -> dict[str, Any]:
    """Bind the inbox-selected steering; never self-seed authority from this publisher."""
    inbox_path = repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox = read_json(inbox_path)
    epoch = str(inbox.get("schema_version") or "").strip()
    steering_rel = inbox.get("steering")
    errors: list[str] = []
    if not epoch:
        errors.append("SUPERVISOR_INBOX_EPOCH_MISSING")
    if not isinstance(steering_rel, str) or not steering_rel.strip():
        errors.append("SUPERVISOR_STEERING_POINTER_MISSING")
        steering = {}
    else:
        steering = read_json(repo / steering_rel)
        if not steering:
            errors.append("SUPERVISOR_STEERING_UNREADABLE")
        elif str(steering.get("schema_version") or "").strip() != epoch:
            errors.append("SUPERVISOR_STEERING_EPOCH_MISMATCH")
    binding_payload = {
        "inbox": inbox,
        "selected_steering": steering,
        "selected_steering_path": steering_rel,
    }
    return {
        "authority_epoch": epoch or None,
        "selected_steering_path": steering_rel if isinstance(steering_rel, str) else None,
        "binding_sha256": sha256_json(binding_payload),
        "status": "BOUND" if not errors else "UNMEASURED_FAIL_CLOSED",
        "errors": errors,
    }


def _source_metrics(name: str, doc: dict[str, Any]) -> dict[str, Any]:
    if name == "swarm":
        workers = doc.get("workers") if isinstance(doc.get("workers"), dict) else {}
        return {key: workers.get(key) for key in (
            "worker_records", "exact_usage_rows", "input_tokens", "output_tokens", "total_tokens"
        )}
    if name == "forge":
        return {key: doc.get(key) for key in (
            "discovery_queries", "discovery_hits", "evaluations", "accepted_deltas"
        )}
    return {key: doc.get(key) for key in (
        "collected_source_tokens", "collected_chunks", "accepted_packets", "accepted_dataset_tokens"
    )}


def source_snapshot_from_docs(
    swarm: dict[str, Any],
    forge: dict[str, Any],
    distillery: dict[str, Any],
    authority: dict[str, Any],
    measurement_bindings: dict[str, Any] | None = None,
    max_source_skew_seconds: float = MAX_SOURCE_SKEW_SECONDS,
) -> dict[str, Any]:
    """Create one deterministic identity for Swarm+Forge+Distillery+authority inputs."""
    docs = {"swarm": swarm, "forge": forge, "distillery": distillery}
    errors = list(authority.get("errors") or [])
    sources: dict[str, Any] = {}
    times: list[dt.datetime] = []
    for name, doc in docs.items():
        if not isinstance(doc, dict) or not doc:
            errors.append(f"{name.upper()}_SOURCE_MISSING")
            continue
        generated_at = doc.get("generated_at")
        parsed = parse_ts(generated_at)
        if parsed is None:
            errors.append(f"{name.upper()}_GENERATED_AT_INVALID")
        else:
            times.append(parsed)
        sources[name] = {
            "generated_at": generated_at,
            "sha256": sha256_json(doc),
            "metrics": _source_metrics(name, doc),
        }

    earliest = min(times).isoformat() if len(times) == 3 else None
    latest = max(times).isoformat() if len(times) == 3 else None
    skew = (max(times) - min(times)).total_seconds() if len(times) == 3 else None
    if skew is not None and skew > float(max_source_skew_seconds):
        errors.append("SOURCE_SNAPSHOT_SKEW_EXCEEDED")
    if authority.get("status") != "BOUND" or not authority.get("authority_epoch"):
        if "AUTHORITY_NOT_BOUND" not in errors:
            errors.append("AUTHORITY_NOT_BOUND")

    identity_payload = {
        "schema": SOURCE_SNAPSHOT_SCHEMA,
        "authority_epoch": authority.get("authority_epoch"),
        "authority_binding_sha256": authority.get("binding_sha256"),
        "selected_steering_path": authority.get("selected_steering_path"),
        "max_source_skew_seconds": float(max_source_skew_seconds),
        "sources": sources,
        "measurement_bindings": measurement_bindings or {},
    }
    return {
        **identity_payload,
        "snapshot_id": sha256_json(identity_payload),
        "earliest_input_at": earliest,
        "latest_input_at": latest,
        "source_skew_seconds": skew,
        "status": "FRESH" if not errors else "UNMEASURED_FAIL_CLOSED",
        "errors": errors,
    }


def load_source_snapshot(
    repo: Path,
    authority: dict[str, Any],
    measurement_bindings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return source_snapshot_from_docs(
        read_json(repo / "free swarm/LIVE_METRICS.json"),
        read_json(repo / "free swarm/FORGE_LIVE.json"),
        read_json(repo / "free swarm/DISTILLERY_LIVE.json"),
        authority,
        measurement_bindings=measurement_bindings,
    )


def canonical_measurement_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove executor-local absolute source paths from the deterministic measurement digest."""
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item.pop("_source", None)
        out.append(item)
    return out


def source_metrics_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    sources = snapshot.get("sources") if isinstance(snapshot.get("sources"), dict) else {}
    return {
        name: dict((sources.get(name) or {}).get("metrics") or {})
        for name in ("swarm", "forge", "distillery")
    }


def classify_existing_publication(
    existing: dict[str, Any],
    snapshot: dict[str, Any],
    current_epoch: str,
) -> str:
    if not existing:
        return "MISSING"
    existing_epoch = str(existing.get("authority_epoch") or "").strip()
    if existing_epoch != current_epoch:
        old_key = epoch_key(existing_epoch)
        new_key = epoch_key(current_epoch)
        if old_key is not None and new_key is not None and old_key > new_key:
            return "EXISTING_NEWER_AUTHORITY_FAIL_CLOSED"
        return "HISTORICAL_AUTHORITY_EPOCH"

    current_latest = parse_ts(snapshot.get("latest_input_at"))
    existing_snapshot = existing.get("source_snapshot")
    if not isinstance(existing_snapshot, dict):
        existing_generated = parse_ts(existing.get("generated_at"))
        if existing_generated is not None and current_latest is not None and existing_generated < current_latest:
            return "STALE_UNBOUND_AGGREGATE"
        return "UNMEASURED_UNBOUND_AGGREGATE"

    old_latest = parse_ts(existing_snapshot.get("latest_input_at"))
    if old_latest is None or current_latest is None:
        return "UNMEASURED_SNAPSHOT_TIME"
    old_id = existing_snapshot.get("snapshot_id")
    new_id = snapshot.get("snapshot_id")
    if old_latest > current_latest:
        return "CURRENT_NEWER_SNAPSHOT_EXISTS"
    if old_latest < current_latest:
        return "STALE_SUPERSEDED_INPUT"
    if old_id == new_id:
        return "CURRENT_SAME_SNAPSHOT"
    return "AMBIGUOUS_SAME_TIME_DIFFERENT_SNAPSHOT"


def publication_decision(existing: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    snapshot = result.get("source_snapshot") if isinstance(result.get("source_snapshot"), dict) else {}
    epoch = str(result.get("authority_epoch") or "")
    if snapshot.get("status") != "FRESH":
        return {"publish": False, "reason": "NEW_SNAPSHOT_NOT_FRESH", "classification": "UNMEASURED_FAIL_CLOSED"}
    classification = classify_existing_publication(existing, snapshot, epoch)
    blocked = {
        "EXISTING_NEWER_AUTHORITY_FAIL_CLOSED",
        "CURRENT_NEWER_SNAPSHOT_EXISTS",
        "AMBIGUOUS_SAME_TIME_DIFFERENT_SNAPSHOT",
        "UNMEASURED_SNAPSHOT_TIME",
        "UNMEASURED_UNBOUND_AGGREGATE",
    }
    if classification in blocked:
        return {"publish": False, "reason": classification, "classification": classification}
    if classification == "CURRENT_SAME_SNAPSHOT":
        if existing.get("result_digest") == result.get("result_digest"):
            return {"publish": False, "reason": "IDEMPOTENT_NO_CHANGE", "classification": classification}
        return {"publish": False, "reason": "SAME_SNAPSHOT_RESULT_DIGEST_MISMATCH", "classification": classification}
    return {"publish": True, "reason": "PUBLISH", "classification": classification}


def stable_result_digest(result: dict[str, Any]) -> str:
    """Digest only bounded deterministic fields, never wall-clock writer timing or local paths."""
    keys = (
        "schema", "generated_at", "authority_epoch", "program", "product", "architecture",
        "config_sha256", "source_snapshot", "source_metrics", "worker_record_count", "aggregate",
        "anti_goodhart", "selection_policy", "runtime_credit_added", "note",
    )
    return sha256_json({key: result.get(key) for key in keys})


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as tmp:
        tmp.write(text)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp_path = Path(tmp.name)
    os.replace(temp_path, path)


def publish_guarded(
    result: dict[str, Any],
    md: str,
    out_json: Path,
    out_md: Path,
    readme: Path | None = None,
) -> dict[str, Any]:
    """Serialize writers and re-check the current publication while holding the lock."""
    out_json.parent.mkdir(parents=True, exist_ok=True)
    lock_path = out_json.with_name(f".{out_json.name}.lock")
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        existing = read_json(out_json)
        decision = publication_decision(existing, result)
        if decision["reason"] == "IDEMPOTENT_NO_CHANGE":
            return decision
        if not decision["publish"]:
            raise SystemExit(f"COLLECTIVE_METRICS_PUBLICATION_BLOCKED:{decision['reason']}")

        json_text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        # Markdown is staged first; canonical JSON is the commit point for consumers.
        _atomic_write(out_md, md)
        if readme is not None:
            current = readme.read_text(encoding="utf-8") if readme.exists() else "# Free Swarm\n"
            _atomic_write(readme, replace_block(current, md))
        _atomic_write(out_json, json_text)
        return decision


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
    if not isinstance(inv, dict) or inv.get("verified") is not True:
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
        for candidate in candidates:
            if candidate:
                by_actor[candidate].append(delta)
    for row in workers:
        matches: list[dict[str, Any]] = []
        for candidate in {worker_key(row), str(row.get("organ") or ""), str(row.get("model") or "")}:
            matches.extend(by_actor.get(candidate, []))
        uniq = {}
        for delta in matches:
            key = str(delta.get("delta_id") or delta.get("_source")) + ":" + str(delta.get("_line"))
            uniq[key] = delta
        matches = list(uniq.values())
        total_tokens = inum(row.get("total_tokens"))
        utility = 0.0
        cqs: list[float] = []
        viss: list[float] = []
        for delta in matches:
            cq, _ = code_quality(delta, config)
            if cq is not None:
                cqs.append(cq)
            vis = innovation_score(delta, config)
            if vis is not None:
                viss.append(vis)
            imp = fnum(delta.get("relative_improvement_pct")) or 0.0
            runs = inum(delta.get("reproducible_runs")) or 0
            indep = fnum(delta.get("independence_factor"))
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
        for milestone in milestones:
            probability = fnum(probs.get(milestone))
            if probability is not None and 0 <= probability <= 1:
                per_lineage[lineage][milestone].append(probability)

    milestone_probs: dict[str, float] = {}
    for milestone in milestones:
        lineage_vals = []
        for _, values in per_lineage.items():
            value = robust_median(values.get(milestone, []))
            if value is not None:
                lineage_vals.append(value)
        value = robust_median(lineage_vals)
        if value is not None:
            milestone_probs[milestone] = value

    baseline = hc.get("initial_research_baseline") or {}
    seed = baseline.get("milestone_probabilities") or {}
    used_seed = False
    for milestone in milestones:
        if milestone not in milestone_probs:
            probability = fnum(seed.get(milestone))
            if probability is not None:
                milestone_probs[milestone] = probability
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
    known_tokens = [inum(row.get("total_tokens")) for row in workers]
    total_tokens = sum(x for x in known_tokens if x is not None)
    exact_token_rows = sum(1 for x in known_tokens if x is not None)
    utility = sum(float(row.get("verified_utility_units") or 0.0) for row in workers)
    tqe = 1000.0 * utility / total_tokens if total_tokens > 0 else None
    cqs = [fnum(row.get("code_quality_score")) for row in workers]
    cqs = [x for x in cqs if x is not None]
    viss = [fnum(row.get("verified_innovation_score")) for row in workers]
    viss = [x for x in viss if x is not None]
    lats = [fnum(row.get("information_latency_seconds")) for row in workers]
    lats = sorted(x for x in lats if x is not None)
    pidx = [fnum(row.get("performance_index")) for row in workers]
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
        key=lambda row: (
            -(fnum(row.get("token_quality_efficiency")) or -1),
            str(row.get("worker_id") or row.get("organ") or ""),
        ),
    )
    for row in ranked[:limit]:
        status = str(row.get("status") or row.get("runtime_status") or "OBSERVED")
        lines.append(
            f"| {worker_key(row)} | {fmt(row.get('total_tokens'),0)} | "
            f"{fmt(row.get('token_quality_efficiency'),6)} | {fmt(row.get('code_quality_score'),2)} | "
            f"{fmt(row.get('verified_innovation_score'),2)} | {fmt(row.get('performance_index'),3)} | "
            f"{fmt(row.get('information_latency_seconds'),3)} | "
            f"{fmt(row.get('capability_information_latency_ratio'),3)} | "
            f"`{str(row.get('evidence_lineage_resolved') or 'UNKNOWN')[:80]}` | {status} |"
        )
    if len(workers) > limit:
        lines.append(f"| … | … | … | … | … | … | … | … | … | {len(workers)-limit} additional rows in JSON |")
    return lines


def markdown(result: dict[str, Any]) -> str:
    aggregate_result = result["aggregate"]
    hcu = aggregate_result["hcu_confidence"]
    probability = hcu.get("forecast_probability")
    snapshot = result.get("source_snapshot") or {}
    source_metrics = result.get("source_metrics") or {}
    lines = [
        AUTO_BEGIN,
        "## GO Collective Recursive-Improvement Metrics",
        f"Generated from bounded inputs: `{result['generated_at']}`  ",
        f"Schema: `{SCHEMA}`  ",
        f"Authority epoch: `{result.get('authority_epoch')}`  ",
        f"Freshness: **{snapshot.get('status','UNMEASURED')}** · snapshot `{snapshot.get('snapshot_id','UNKNOWN')}`  ",
        f"Input skew: `{fmt(snapshot.get('source_skew_seconds'),3)} s` · result digest `{result.get('result_digest','UNKNOWN')}`  ",
        "",
        "### Bound source snapshot",
        "| source | generated_at | key measurements |",
        "|---|---|---|",
        f"| Swarm | {((snapshot.get('sources') or {}).get('swarm') or {}).get('generated_at','UNKNOWN')} | total_tokens={((source_metrics.get('swarm') or {}).get('total_tokens'))} |",
        f"| Forge | {((snapshot.get('sources') or {}).get('forge') or {}).get('generated_at','UNKNOWN')} | evaluations={((source_metrics.get('forge') or {}).get('evaluations'))}; accepted={((source_metrics.get('forge') or {}).get('accepted_deltas'))} |",
        f"| Distillery | {((snapshot.get('sources') or {}).get('distillery') or {}).get('generated_at','UNKNOWN')} | packets={((source_metrics.get('distillery') or {}).get('accepted_packets'))}; dataset_tokens={((source_metrics.get('distillery') or {}).get('accepted_dataset_tokens'))} |",
        "",
        "### Aggregate",
        "| Metric | Current | Evidence note |",
        "|---|---:|---|",
        f"| Worker records observed | {aggregate_result['worker_records']} | all explicit records + available Free Swarm rows |",
        f"| Exact-token rows | {aggregate_result['exact_token_rows']} | missing tokens remain UNKNOWN |",
        f"| Total exact tokens | {fmt(aggregate_result['total_tokens'],0)} | per-worker measurement; live source total remains separately bound above |",
        f"| Token Quality Efficiency / 1k tokens | {fmt(aggregate_result['token_quality_efficiency'],6)} | accepted verified utility only |",
        f"| Code Quality Score / 100 | {fmt(aggregate_result['code_quality_score'],2)} | UNKNOWN when evidence coverage is insufficient |",
        f"| Verified Innovation Score / 100 | {fmt(aggregate_result['verified_innovation_score'],2)} | self-reported novelty ignored |",
        f"| Median performance index | {fmt(aggregate_result['performance_index_median'],3)} | same benchmark family only |",
        f"| p95 information latency (s) | {fmt(aggregate_result['p95_information_latency_seconds'],3)} | producer evidence -> first downstream consumption |",
        f"| Capability / latency ratio | {fmt(aggregate_result['capability_information_latency_ratio'],3)} | unbounded; raw perf+latency remain visible |",
        f"| HCU_TARGET_100_GO forecast | {fmt(100*probability,1) if probability is not None else 'UNKNOWN'}% | {hcu.get('calibration_state')} forecast, not completion % |",
        "",
        "### HCU milestone forecast vector",
        "| milestone | p |",
        "|---|---:|",
    ]
    for key, value in hcu.get("milestone_probabilities", {}).items():
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
        "- Stale/unbound/out-of-order aggregate writers fail closed before canonical JSON replacement.",
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--artifacts", type=Path, default=Path("/artifacts/clay-entityos-swarm"))
    ap.add_argument("--output-json", type=Path, default=None)
    ap.add_argument("--output-md", type=Path, default=None)
    ap.add_argument("--update-readme", action="store_true")
    args = ap.parse_args()

    repo = args.repo.resolve()
    config = load_config(repo)
    if config.get("schema") != "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1":
        raise SystemExit("GO_METRICS_CONFIG_REQUIRED")

    authority = current_authority_binding(repo)
    if authority.get("status") != "BOUND":
        raise SystemExit("COLLECTIVE_METRICS_AUTHORITY_UNBOUND:" + ",".join(authority.get("errors") or []))

    workers = explicit_worker_rows(repo)
    workers.extend(free_swarm_rows(args.artifacts))
    deltas = delta_rows(repo)
    attach_delta_metrics(workers, deltas, config)
    measurement_bindings = {
        "config_sha256": sha256_json(config),
        "workers_sha256": sha256_json(canonical_measurement_rows(workers)),
        "deltas_sha256": sha256_json(canonical_measurement_rows(deltas)),
    }
    snapshot = load_source_snapshot(repo, authority, measurement_bindings=measurement_bindings)
    if snapshot.get("status") != "FRESH":
        raise SystemExit("COLLECTIVE_METRICS_SOURCE_SNAPSHOT_UNMEASURED:" + ",".join(snapshot.get("errors") or []))

    result = {
        "schema": SCHEMA,
        # Deterministic: publication identity comes from the latest bounded input, never writer wall-clock time.
        "generated_at": snapshot.get("latest_input_at"),
        "authority_epoch": authority.get("authority_epoch"),
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "config_sha256": sha256_json(config),
        "source_snapshot": snapshot,
        "source_metrics": source_metrics_from_snapshot(snapshot),
        "worker_record_count": len(workers),
        "aggregate": aggregate(workers, config),
        "workers": workers,
        "anti_goodhart": config.get("anti_goodhart"),
        "selection_policy": config.get("selection_policy"),
        "runtime_credit_added": 0,
        "note": "Derived measurement only. It cannot mint canonical truth or runtime/model/training credit.",
    }
    result["result_digest"] = stable_result_digest(result)
    md = markdown(result)

    out_json = args.output_json or (repo / "free swarm/GO_COLLECTIVE_METRICS.json")
    out_md = args.output_md or (repo / "free swarm/GO_COLLECTIVE_METRICS.md")
    readme = (repo / "free swarm/README.md") if args.update_readme else None
    decision = publish_guarded(result, md, out_json, out_md, readme=readme)

    print(out_json)
    print(out_md)
    hcu = result["aggregate"]["hcu_confidence"]
    print(json.dumps({
        "workers": len(workers),
        "tqe": result["aggregate"]["token_quality_efficiency"],
        "cqs": result["aggregate"]["code_quality_score"],
        "vis": result["aggregate"]["verified_innovation_score"],
        "cilr": result["aggregate"]["capability_information_latency_ratio"],
        "hcu_forecast_probability": hcu.get("forecast_probability"),
        "calibration_state": hcu.get("calibration_state"),
        "authority_epoch": result["authority_epoch"],
        "freshness_status": snapshot.get("status"),
        "source_snapshot_id": snapshot.get("snapshot_id"),
        "result_digest": result.get("result_digest"),
        "publication": decision,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
