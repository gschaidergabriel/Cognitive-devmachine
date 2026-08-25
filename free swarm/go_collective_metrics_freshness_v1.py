#!/usr/bin/env python3
"""Freshness guard for the canonical Clay GO collective-metrics publisher.

The public go_collective_metrics.py remains the single entrypoint. The pre-8.77
calculation is preserved only as an internal donor; publication here binds one
Swarm/Forge/Distillery snapshot, current supervisor epoch, deterministic result
identity, serialized compare-before-commit, and atomic file replacement.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from typing import Any

_CORE_PATH = Path(__file__).parent / "_internal" / "go_collective_metrics_core_v1.py"
_SPEC = importlib.util.spec_from_file_location("clay_go_collective_metrics_core_v1", _CORE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("GO_COLLECTIVE_METRICS_CORE_V1_UNAVAILABLE")
_core = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_core)

for _name in dir(_core):
    if not _name.startswith("_") and _name not in globals():
        globals()[_name] = getattr(_core, _name)

FRESHNESS_SCHEMA = "COLLECTIVE_METRICS_FRESHNESS/v1"
SNAPSHOT_SCHEMA = "CLAY_GO_COLLECTIVE_INPUT_SNAPSHOT/v1"
DEFAULT_MAX_SOURCE_AGE_SECONDS = 3600.0
DEFAULT_MAX_SNAPSHOT_SKEW_SECONDS = 300.0
FUTURE_TOLERANCE_SECONDS = 30.0


class FreshnessError(RuntimeError):
    pass


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_json(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _utc(value: dt.datetime | None = None) -> dt.datetime:
    value = value or dt.datetime.now(dt.timezone.utc)
    return value.astimezone(dt.timezone.utc) if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


def _parse_ts(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return _utc(dt.datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        return None


def _epoch_key(value: Any) -> tuple[int, ...] | None:
    try:
        parts = tuple(int(x) for x in str(value or "").strip().split("."))
    except ValueError:
        return None
    return parts if parts and all(x >= 0 for x in parts) else None


def _stable_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: v for k, v in row.items() if k != "_source"} for row in rows]


def make_shared_snapshot(*, authority_epoch: str, sources: dict[str, dict[str, Any]],
                         collector_payload_sha256: str, now: dt.datetime | None = None,
                         max_source_age_seconds: float = DEFAULT_MAX_SOURCE_AGE_SECONDS,
                         max_snapshot_skew_seconds: float = DEFAULT_MAX_SNAPSHOT_SKEW_SECONDS) -> dict[str, Any]:
    if set(sources) != {"free_swarm", "forge", "distillery"}:
        raise FreshnessError("SHARED_SNAPSHOT_REQUIRES_SWARM_FORGE_DISTILLERY")
    if _epoch_key(authority_epoch) is None:
        raise FreshnessError("AUTHORITY_EPOCH_INVALID")
    if len(collector_payload_sha256) != 64:
        raise FreshnessError("COLLECTOR_PAYLOAD_DIGEST_INVALID")
    now_utc = _utc(now)
    normalized: dict[str, dict[str, Any]] = {}
    times: list[dt.datetime] = []
    for name in ("free_swarm", "forge", "distillery"):
        src = sources[name]
        stamp = _parse_ts(src.get("generated_at"))
        digest = str(src.get("sha256") or "")
        logical_path = str(src.get("logical_path") or "")
        if stamp is None or len(digest) != 64 or not logical_path:
            raise FreshnessError(f"SOURCE_IDENTITY_INVALID:{name}")
        age = (now_utc - stamp).total_seconds()
        if age > max_source_age_seconds:
            raise FreshnessError(f"STALE_INPUT:{name}:{age:.3f}s")
        if age < -FUTURE_TOLERANCE_SECONDS:
            raise FreshnessError(f"FUTURE_INPUT:{name}:{-age:.3f}s")
        times.append(stamp)
        normalized[name] = {"logical_path": logical_path, "generated_at": stamp.isoformat(), "sha256": digest}
    skew = (max(times) - min(times)).total_seconds()
    if skew > max_snapshot_skew_seconds:
        raise FreshnessError(f"SNAPSHOT_SKEW_EXCEEDED:{skew:.3f}s")
    basis = {"schema": SNAPSHOT_SCHEMA, "authority_epoch": authority_epoch,
             "sources": normalized, "collector_payload_sha256": collector_payload_sha256}
    return {**basis, "snapshot_id": _sha_json(basis),
            "earliest_input_at": min(times).isoformat(), "latest_input_at": max(times).isoformat(),
            "snapshot_skew_seconds": skew, "freshness_status": "FRESH"}


def _read_source(path: Path, logical_path: str) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        raw = path.read_bytes()
        doc = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise FreshnessError(f"SOURCE_READ_FAILED:{logical_path}:{type(exc).__name__}") from exc
    if not isinstance(doc, dict):
        raise FreshnessError(f"SOURCE_NOT_OBJECT:{logical_path}")
    return doc, {"logical_path": logical_path, "generated_at": doc.get("generated_at"), "sha256": _sha_bytes(raw)}


def _prefer(primary: Path, fallback: Path, primary_label: str, fallback_label: str):
    if primary.exists():
        return _read_source(primary, primary_label)
    if fallback.exists():
        return _read_source(fallback, fallback_label)
    raise FreshnessError(f"CANONICAL_LIVE_SOURCE_MISSING:{primary_label}|{fallback_label}")


def _current_authority_epoch(repo: Path) -> str:
    doc = _core.read_json(repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
    epoch = str(doc.get("schema_version") or "").strip()
    if _epoch_key(epoch) is None:
        raise FreshnessError("CURRENT_AUTHORITY_EPOCH_UNRESOLVED")
    if doc.get("active_program") != "ENTITYOS_HCU":
        raise FreshnessError("CURRENT_PROGRAM_MISMATCH")
    return epoch


def _capture_sources(repo: Path, artifacts: Path):
    swarm_doc, swarm_meta = _read_source(repo / "free swarm/LIVE_METRICS.json", "free swarm/LIVE_METRICS.json")
    forge_doc, forge_meta = _prefer(artifacts / "forge/STATUS.json", repo / "free swarm/FORGE_LIVE.json",
                                    "artifacts/forge/STATUS.json", "free swarm/FORGE_LIVE.json")
    dist_doc, dist_meta = _prefer(artifacts / "distillery/STATUS.json", repo / "free swarm/DISTILLERY_LIVE.json",
                                  "artifacts/distillery/STATUS.json", "free swarm/DISTILLERY_LIVE.json")
    return ({"free_swarm": swarm_doc, "forge": forge_doc, "distillery": dist_doc},
            {"free_swarm": swarm_meta, "forge": forge_meta, "distillery": dist_meta})


def source_metrics_from_snapshot(snapshot: dict[str, Any], docs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    sid = snapshot["snapshot_id"]
    workers = docs["free_swarm"].get("workers") or {}
    forge = docs["forge"]
    dist = docs["distillery"]
    return {
        "free_swarm": {"snapshot_id": sid, "generated_at": snapshot["sources"]["free_swarm"]["generated_at"],
                       "worker_records": workers.get("worker_records"), "exact_usage_rows": workers.get("exact_usage_rows"),
                       "input_tokens": workers.get("input_tokens"), "output_tokens": workers.get("output_tokens"),
                       "total_tokens": workers.get("total_tokens")},
        "forge": {"snapshot_id": sid, "generated_at": snapshot["sources"]["forge"]["generated_at"],
                  "discovery_hits": forge.get("discovery_hits"),
                  "evaluations": forge.get("evaluations", forge.get("evaluations_written")),
                  "accepted_deltas": forge.get("accepted_deltas", forge.get("verified_deltas"))},
        "distillery": {"snapshot_id": sid, "generated_at": snapshot["sources"]["distillery"]["generated_at"],
                       "collected_source_tokens": dist.get("collected_source_tokens"),
                       "accepted_packets": dist.get("accepted_packets"),
                       "accepted_dataset_tokens": dist.get("accepted_dataset_tokens")},
    }


def deterministic_result_digest(result: dict[str, Any]) -> str:
    keys = ("schema", "authority_epoch", "snapshot", "config_sha256", "worker_record_count", "aggregate",
            "source_metrics", "anti_goodhart", "selection_policy", "runtime_credit_added")
    return _sha_json({key: result.get(key) for key in keys})


def classify_existing_freshness(existing: dict[str, Any], current_snapshot: dict[str, Any], current_authority_epoch: str) -> str:
    if not existing:
        return "MISSING"
    if str(existing.get("authority_epoch") or "") != current_authority_epoch:
        return "HISTORICAL_AUTHORITY_EPOCH"
    old = existing.get("snapshot") or {}
    if old.get("snapshot_id") == current_snapshot.get("snapshot_id"):
        return "CURRENT"
    old_ts = _parse_ts(old.get("latest_input_at") or existing.get("generated_at"))
    new_ts = _parse_ts(current_snapshot.get("latest_input_at"))
    if old_ts is None or new_ts is None:
        return "UNMEASURED"
    if old_ts < new_ts:
        return "STALE"
    if old_ts > new_ts:
        return "NEWER_THAN_CANDIDATE"
    return "CONFLICT_SAME_TIME_DIFFERENT_SNAPSHOT"


def publication_decision(existing: dict[str, Any], candidate: dict[str, Any], current_authority_epoch: str) -> str:
    candidate_epoch = str(candidate.get("authority_epoch") or "")
    if candidate_epoch != current_authority_epoch:
        return "REJECT_AUTHORITY_EPOCH_MISMATCH"
    if not existing:
        return "PUBLISH"
    old_epoch = str(existing.get("authority_epoch") or "")
    old_key, new_key = _epoch_key(old_epoch), _epoch_key(candidate_epoch)
    if old_key is not None and new_key is not None:
        if old_key > new_key:
            return "REJECT_NEWER_AUTHORITY_ALREADY_PUBLISHED"
        if old_key < new_key:
            return "PUBLISH_SUCCESSOR_AUTHORITY"
    elif old_epoch and old_epoch != candidate_epoch:
        return "REJECT_UNORDERABLE_AUTHORITY_EPOCH"
    old_snap, new_snap = existing.get("snapshot") or {}, candidate.get("snapshot") or {}
    old_ts = _parse_ts(old_snap.get("latest_input_at") or existing.get("generated_at"))
    new_ts = _parse_ts(new_snap.get("latest_input_at") or candidate.get("generated_at"))
    if old_ts is None or new_ts is None:
        return "REJECT_UNMEASURED_PUBLICATION_ORDER"
    if new_ts < old_ts:
        return "REJECT_OUT_OF_ORDER_WRITER"
    if new_ts > old_ts:
        return "PUBLISH"
    if old_snap.get("snapshot_id") != new_snap.get("snapshot_id"):
        return "REJECT_SAME_TIME_SNAPSHOT_CONFLICT"
    if existing.get("result_digest_sha256") == candidate.get("result_digest_sha256"):
        return "IDEMPOTENT"
    return "REJECT_SAME_SNAPSHOT_DIFFERENT_RESULT"


def _freshness_markdown(result: dict[str, Any]) -> str:
    md = _core.markdown(result)
    snap, src = result["snapshot"], result["source_metrics"]
    lines = [f"Authority epoch: `{result['authority_epoch']}`  ", f"Shared snapshot: `{snap['snapshot_id']}`  ",
             f"Snapshot window: `{snap['earliest_input_at']}` → `{snap['latest_input_at']}` ({snap['snapshot_skew_seconds']:.3f}s skew)  ",
             f"Result digest: `{result['result_digest_sha256']}`  ", "", "### Fresh bounded conversion snapshot",
             "| plane | snapshot | metric | value |", "|---|---|---|---:|",
             f"| Free Swarm | `{snap['snapshot_id'][:12]}` | total tokens | {src['free_swarm'].get('total_tokens')} |",
             f"| Forge | `{snap['snapshot_id'][:12]}` | accepted deltas | {src['forge'].get('accepted_deltas')} |",
             f"| Distillery | `{snap['snapshot_id'][:12]}` | accepted dataset tokens | {src['distillery'].get('accepted_dataset_tokens')} |", ""]
    marker = "\n### Aggregate\n"
    if marker not in md:
        raise FreshnessError("MARKDOWN_AGGREGATE_MARKER_MISSING")
    return md.replace(marker, "\n" + "\n".join(lines) + marker, 1)


def build_candidate(repo: Path, artifacts: Path, *, now: dt.datetime | None = None,
                    max_source_age_seconds: float = DEFAULT_MAX_SOURCE_AGE_SECONDS,
                    max_snapshot_skew_seconds: float = DEFAULT_MAX_SNAPSHOT_SKEW_SECONDS):
    config = _core.load_config(repo)
    if config.get("schema") != "CLAY_GO_COLLECTIVE_METRICS_CONFIG/v1":
        raise FreshnessError("GO_METRICS_CONFIG_REQUIRED")
    epoch = _current_authority_epoch(repo)
    docs, source_meta = _capture_sources(repo, artifacts)
    workers = _core.explicit_worker_rows(repo)
    workers.extend(_core.free_swarm_rows(artifacts))
    deltas = _core.delta_rows(repo)
    _core.attach_delta_metrics(workers, deltas, config)
    payload = {"workers": _stable_rows(workers), "deltas": _stable_rows(deltas), "config_sha256": _core.sha256_json(config)}
    snap = make_shared_snapshot(authority_epoch=epoch, sources=source_meta, collector_payload_sha256=_sha_json(payload),
                                now=now, max_source_age_seconds=max_source_age_seconds,
                                max_snapshot_skew_seconds=max_snapshot_skew_seconds)
    result = {"schema": _core.SCHEMA, "generated_at": _utc(now).isoformat(),
              "generation_class": "EXECUTABLE_FRESHNESS_GUARDED_PUBLISHER_SNAPSHOT",
              "authority_epoch": epoch, "program": "ENTITYOS_HCU", "product": "EntityOS", "architecture": "HCU",
              "config_sha256": _core.sha256_json(config), "worker_record_count": len(workers), "snapshot": snap,
              "source_metrics": source_metrics_from_snapshot(snap, docs),
              "freshness": {"schema": FRESHNESS_SCHEMA, "status": "FRESH", "consumer_state_before_publish": None,
                            "max_source_age_seconds": max_source_age_seconds,
                            "max_snapshot_skew_seconds": max_snapshot_skew_seconds},
              "aggregate": _core.aggregate(workers, config), "workers": workers,
              "anti_goodhart": config.get("anti_goodhart"), "selection_policy": config.get("selection_policy"),
              "runtime_credit_added": 0,
              "note": "Derived measurement only. It cannot mint canonical truth or runtime/model/training credit."}
    result["result_digest_sha256"] = deterministic_result_digest(result)
    return result, _freshness_markdown(result)


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp, path)
        try:
            dfd = os.open(path.parent, os.O_RDONLY); os.fsync(dfd); os.close(dfd)
        except OSError:
            pass
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def publish_guarded(result: dict[str, Any], md: str, *, out_json: Path, out_md: Path, repo: Path, update_readme: bool) -> str:
    lock_path = out_json.with_suffix(out_json.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        epoch = _current_authority_epoch(repo)
        existing = _core.read_json(out_json) if out_json.exists() else {}
        result["freshness"]["consumer_state_before_publish"] = classify_existing_freshness(existing, result["snapshot"], epoch)
        result["result_digest_sha256"] = deterministic_result_digest(result)
        decision = publication_decision(existing, result, epoch)
        if decision.startswith("REJECT_"):
            raise FreshnessError(decision)
        if decision == "IDEMPOTENT":
            return decision
        _atomic_write(out_json, json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        _atomic_write(out_md, md)
        if update_readme:
            readme = repo / "free swarm/README.md"
            current = readme.read_text(encoding="utf-8") if readme.exists() else "# Free Swarm\n"
            _atomic_write(readme, _core.replace_block(current, md))
        return decision


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--artifacts", type=Path, default=Path("/artifacts/clay-entityos-swarm"))
    ap.add_argument("--output-json", type=Path, default=None)
    ap.add_argument("--output-md", type=Path, default=None)
    ap.add_argument("--update-readme", action="store_true")
    ap.add_argument("--max-source-age-seconds", type=float, default=DEFAULT_MAX_SOURCE_AGE_SECONDS)
    ap.add_argument("--max-snapshot-skew-seconds", type=float, default=DEFAULT_MAX_SNAPSHOT_SKEW_SECONDS)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    repo, artifacts = args.repo.resolve(), args.artifacts.resolve()
    result, md = build_candidate(repo, artifacts, max_source_age_seconds=args.max_source_age_seconds,
                                 max_snapshot_skew_seconds=args.max_snapshot_skew_seconds)
    out_json = args.output_json or (repo / "free swarm/GO_COLLECTIVE_METRICS.json")
    out_md = args.output_md or (repo / "free swarm/GO_COLLECTIVE_METRICS.md")
    decision = "DRY_RUN" if args.dry_run else publish_guarded(result, md, out_json=out_json, out_md=out_md,
                                                               repo=repo, update_readme=args.update_readme)
    print(json.dumps({"publication": decision, "authority_epoch": result["authority_epoch"],
                      "snapshot_id": result["snapshot"]["snapshot_id"],
                      "result_digest_sha256": result["result_digest_sha256"],
                      "workers": len(result["workers"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
