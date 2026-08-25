#!/usr/bin/env python3
"""Fail-closed freshness/publication gate for the existing Clay GO metrics collector.

This file does not define a second metrics authority. It runs the existing
``free swarm/go_collective_metrics.py`` collector into temporary outputs, binds the
candidate to one exact input snapshot, and atomically replaces the existing
GO_COLLECTIVE_METRICS outputs only when the bound snapshot is still current and
cannot regress a newer publication.

No provider call or provider credential is used. No runtime/model/training/canonical
truth credit is minted by this gate.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Iterable

RECEIPT_SCHEMA = "COLLECTIVE_METRICS_FRESHNESS_RECEIPT/v1"
SNAPSHOT_SCHEMA = "CLAY_GO_COLLECTIVE_METRICS_INPUT_SNAPSHOT/v1"
LIVE_SNAPSHOT_SCHEMA = "CLAY_GO_COLLECTIVE_METRICS_LIVE_SNAPSHOT/v1"
GATE_SCHEMA = "CLAY_GO_COLLECTIVE_METRICS_FRESHNESS_GATE/v1"

LIVE_PATHS = {
    "swarm": "free swarm/LIVE_METRICS.json",
    "forge": "free swarm/FORGE_LIVE.json",
    "distillery": "free swarm/DISTILLERY_LIVE.json",
}
INBOX_PATH = "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
CONFIG_PATH = "research_entity/continuity/go_metrics/GO_METRICS_CONFIG_V1.json"
DELTA_LEDGER_PATH = "free swarm/architecture_delta_evaluations.jsonl"
COLLECTOR_PATH = "free swarm/go_collective_metrics.py"
OUTPUT_JSON_PATH = "free swarm/GO_COLLECTIVE_METRICS.json"
OUTPUT_MD_PATH = "free swarm/GO_COLLECTIVE_METRICS.md"
RECEIPT_PATH = "free swarm/COLLECTIVE_METRICS_FRESHNESS_RECEIPT.json"
LOCK_PATH = "free swarm/.go_collective_metrics.lock"


class FreshnessError(RuntimeError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def parse_ts(value: Any) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise FreshnessError("TIMESTAMP_REQUIRED")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        raise FreshnessError(f"TIMESTAMP_INVALID:{value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def epoch_key(value: Any) -> tuple[int, ...]:
    text = str(value or "").strip()
    if not text:
        raise FreshnessError("AUTHORITY_EPOCH_REQUIRED")
    try:
        return tuple(int(part) for part in text.split("."))
    except ValueError as exc:
        raise FreshnessError(f"AUTHORITY_EPOCH_INVALID:{text}") from exc


def stable_file_bytes(path: Path, label: str) -> tuple[bytes, dict[str, Any]]:
    try:
        before = path.stat()
        h = hashlib.sha256()
        chunks: list[bytes] = []
        size = 0
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                chunks.append(chunk)
                size += len(chunk)
                h.update(chunk)
        after = path.stat()
    except OSError as exc:
        raise FreshnessError(f"INPUT_REQUIRED:{label}:{type(exc).__name__}") from exc
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
        or size != after.st_size
    ):
        raise FreshnessError(f"INPUT_MOVED_DURING_HASH:{label}")
    return b"".join(chunks), {"path": label, "sha256": h.hexdigest(), "bytes": size}


def stable_file_identity(path: Path, label: str) -> dict[str, Any]:
    _, identity = stable_file_bytes(path, label)
    return identity


def stable_json_input(path: Path, label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    raw, identity = stable_file_bytes(path, label)
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise FreshnessError(f"JSON_REQUIRED:{label}:{type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise FreshnessError(f"JSON_OBJECT_REQUIRED:{label}")
    return value, identity


def read_json(path: Path) -> dict[str, Any]:
    value, _ = stable_json_input(path, path.as_posix())
    return value


def safe_rel(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise FreshnessError("STEERING_PATH_UNSAFE")
    return path.as_posix()


def authority_snapshot(repo: Path) -> dict[str, Any]:
    inbox, inbox_id = stable_json_input(repo / INBOX_PATH, INBOX_PATH)
    epoch = str(inbox.get("schema_version") or "")
    epoch_key(epoch)
    steering_rel = safe_rel(str(inbox.get("steering") or ""))
    steering, steering_id = stable_json_input(repo / steering_rel, steering_rel)
    if str(steering.get("schema_version") or "") != epoch:
        raise FreshnessError("SUPERVISOR_INBOX_STEERING_EPOCH_MISMATCH")
    if inbox.get("active_program") != "ENTITYOS_HCU" or inbox.get("product") != "EntityOS":
        raise FreshnessError("ENTITYOS_PROGRAM_AUTHORITY_MISMATCH")
    if inbox.get("integrated_cognition_compute_architecture") != "HCU":
        raise FreshnessError("HCU_AUTHORITY_MISMATCH")
    authority = steering.get("authority") if isinstance(steering.get("authority"), dict) else {}
    if authority.get("free_only") is not True or authority.get("no_paid_fallback") is not True:
        raise FreshnessError("FREE_ONLY_AUTHORITY_REQUIRED")
    return {
        "authority_epoch": epoch,
        "steering": steering_rel,
        "inputs": [inbox_id, steering_id],
    }


def live_snapshot(repo: Path) -> dict[str, Any]:
    authority = authority_snapshot(repo)
    entries: dict[str, Any] = {}
    values: dict[str, dict[str, Any]] = {}
    times: list[dt.datetime] = []
    for name, rel in LIVE_PATHS.items():
        value, identity = stable_json_input(repo / rel, rel)
        values[name] = value
        ts = parse_ts(value.get("generated_at"))
        times.append(ts)
        entries[name] = {**identity, "generated_at": ts.isoformat()}
    projection = {
        "swarm": {
            "worker_records": ((values["swarm"].get("workers") or {}).get("worker_records")),
            "total_tokens": ((values["swarm"].get("workers") or {}).get("total_tokens")),
        },
        "forge": {
            "evaluations": values["forge"].get("evaluations"),
            "accepted_deltas": values["forge"].get("accepted_deltas"),
        },
        "distillery": {
            "accepted_packets": values["distillery"].get("accepted_packets"),
            "accepted_dataset_tokens": values["distillery"].get("accepted_dataset_tokens"),
        },
    }
    core = {
        "schema": LIVE_SNAPSHOT_SCHEMA,
        "authority_epoch": authority["authority_epoch"],
        "authority_inputs": authority["inputs"],
        "inputs": entries,
        "latest_input_generated_at": max(times).isoformat(),
        "projection": projection,
    }
    return {**core, "live_snapshot_id": sha256_json(core)}


def measured_files(repo: Path, artifacts: Path) -> Iterable[tuple[Path, str]]:
    for rel in (CONFIG_PATH, DELTA_LEDGER_PATH, COLLECTOR_PATH):
        path = repo / rel
        if path.exists() or rel != DELTA_LEDGER_PATH:
            yield path, rel
    records = repo / "research_entity/continuity/go_metrics/worker_records"
    if records.exists():
        for path in sorted(records.rglob("*.json")):
            yield path, path.relative_to(repo).as_posix()
    if artifacts.exists():
        for path in sorted(artifacts.rglob("workers.jsonl")):
            yield path, "artifact://" + path.relative_to(artifacts).as_posix()


def full_snapshot(repo: Path, artifacts: Path) -> dict[str, Any]:
    live = live_snapshot(repo)
    core = {
        "schema": SNAPSHOT_SCHEMA,
        "authority_epoch": live["authority_epoch"],
        "live_snapshot_id": live["live_snapshot_id"],
        "latest_input_generated_at": live["latest_input_generated_at"],
        "live_inputs": live["inputs"],
        "authority_inputs": live["authority_inputs"],
        "measured_inputs": [stable_file_identity(path, label) for path, label in measured_files(repo, artifacts)],
        "projection": live["projection"],
    }
    return {**core, "snapshot_id": sha256_json(core)}


def canonicalize_sources(result: dict[str, Any], repo: Path, artifacts: Path) -> dict[str, Any]:
    result = copy.deepcopy(result)
    for row in result.get("workers") or []:
        if not isinstance(row, dict) or not isinstance(row.get("_source"), str):
            continue
        source = Path(row["_source"])
        try:
            row["_source"] = "artifact://" + source.relative_to(artifacts).as_posix()
            continue
        except (ValueError, OSError):
            pass
        try:
            row["_source"] = "repo://" + source.relative_to(repo).as_posix()
        except (ValueError, OSError):
            pass
    return result


def run_collector(repo: Path, artifacts: Path) -> tuple[dict[str, Any], str]:
    collector = repo / COLLECTOR_PATH
    if not collector.is_file():
        raise FreshnessError("COLLECTOR_REQUIRED")
    with tempfile.TemporaryDirectory(prefix="clay-go-metrics-") as tmp:
        out_json = Path(tmp) / "candidate.json"
        out_md = Path(tmp) / "candidate.md"
        proc = subprocess.run(
            [sys.executable, str(collector), "--repo", str(repo), "--artifacts", str(artifacts),
             "--output-json", str(out_json), "--output-md", str(out_md)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=240,
        )
        if proc.returncode != 0:
            raise FreshnessError(f"COLLECTOR_FAILED:{proc.returncode}")
        result, _ = stable_json_input(out_json, "candidate.json")
        return canonicalize_sources(result, repo, artifacts), out_md.read_text(encoding="utf-8")


def decorate_result(base: dict[str, Any], snapshot: dict[str, Any], generated_at: str | None = None) -> dict[str, Any]:
    stable = copy.deepcopy(base)
    stable.pop("generated_at", None)
    stable.pop("result_digest_sha256", None)
    stable["authority_epoch"] = snapshot["authority_epoch"]
    stable["input_snapshot"] = copy.deepcopy(snapshot)
    stable["live_projection"] = {"snapshot_id": snapshot["snapshot_id"], **copy.deepcopy(snapshot["projection"])}
    stable["freshness"] = {
        "schema": GATE_SCHEMA,
        "status": "CURRENT",
        "authority_epoch": snapshot["authority_epoch"],
        "measured_snapshot_id": snapshot["snapshot_id"],
        "measured_live_snapshot_id": snapshot["live_snapshot_id"],
        "latest_input_generated_at": snapshot["latest_input_generated_at"],
        "runtime_credit_added": 0,
    }
    digest = sha256_json(stable)
    stable["generated_at"] = generated_at or utc_now()
    stable["result_digest_sha256"] = digest
    return stable


def result_order(result: dict[str, Any]) -> tuple[tuple[int, ...], dt.datetime]:
    snapshot = result.get("input_snapshot")
    if not isinstance(snapshot, dict):
        raise FreshnessError("UNBOUND_HISTORICAL_RESULT")
    return (
        epoch_key(result.get("authority_epoch") or snapshot.get("authority_epoch")),
        parse_ts(snapshot.get("latest_input_generated_at")),
    )


def publication_decision(existing: dict[str, Any] | None, candidate: dict[str, Any]) -> tuple[bool, str]:
    if not existing:
        return True, "PUBLISH_NO_EXISTING_RESULT"
    try:
        old_order = result_order(existing)
    except FreshnessError:
        return True, "PUBLISH_SUPERSEDE_HISTORICAL_UNBOUND"
    new_order = result_order(candidate)
    if new_order[0] < old_order[0]:
        return False, "REJECT_OLDER_AUTHORITY_EPOCH"
    if new_order[0] > old_order[0]:
        return True, "PUBLISH_NEWER_AUTHORITY_EPOCH"
    if new_order[1] < old_order[1]:
        return False, "REJECT_OUT_OF_ORDER_OLDER_SNAPSHOT"
    if new_order[1] > old_order[1]:
        return True, "PUBLISH_NEWER_INPUT_SNAPSHOT"
    old_snap = ((existing.get("input_snapshot") or {}).get("snapshot_id"))
    new_snap = ((candidate.get("input_snapshot") or {}).get("snapshot_id"))
    if old_snap != new_snap:
        return False, "REJECT_AMBIGUOUS_SAME_TIME_DIFFERENT_SNAPSHOT"
    if existing.get("result_digest_sha256") != candidate.get("result_digest_sha256"):
        return False, "REJECT_NONDETERMINISTIC_SAME_SNAPSHOT"
    return False, "IDEMPOTENT_SAME_SNAPSHOT"


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with tmp.open("wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def freshness_markdown(candidate: dict[str, Any], base_md: str) -> str:
    f = candidate["freshness"]
    return (
        "<!-- GO_COLLECTIVE_FRESHNESS:BEGIN -->\n"
        "### Publication freshness\n"
        f"- Status: `{f['status']}`\n"
        f"- Authority epoch: `{f['authority_epoch']}`\n"
        f"- Bounded snapshot: `{f['measured_snapshot_id']}`\n"
        f"- Latest bound input: `{f['latest_input_generated_at']}`\n"
        f"- Deterministic result digest: `{candidate['result_digest_sha256']}`\n"
        "<!-- GO_COLLECTIVE_FRESHNESS:END -->\n\n" + base_md
    )


def receipt(status: str, candidate: dict[str, Any] | None, decision: str, published: bool) -> dict[str, Any]:
    return {
        "schema": RECEIPT_SCHEMA,
        "observed_at": utc_now(),
        "status": status,
        "decision": decision,
        "published": published,
        "authority_epoch": candidate.get("authority_epoch") if candidate else None,
        "snapshot_id": ((candidate or {}).get("input_snapshot") or {}).get("snapshot_id"),
        "live_snapshot_id": ((candidate or {}).get("input_snapshot") or {}).get("live_snapshot_id"),
        "result_digest_sha256": (candidate or {}).get("result_digest_sha256"),
        "scope": "GO_COLLECTIVE_METRICS_FRESHNESS_AND_ATOMIC_PUBLICATION_ONLY",
        "provider_runtime_credit_added": 0,
        "entityos_hcu_runtime_credit_added": 0,
        "hcu_full_runtime_credit_added": 0,
        "jspace_model_runtime_credit_added": 0,
        "training_credit_added": 0,
    }


def build_candidate(repo: Path, artifacts: Path) -> tuple[dict[str, Any], str]:
    before = full_snapshot(repo, artifacts)
    base, base_md = run_collector(repo, artifacts)
    after = full_snapshot(repo, artifacts)
    if before["snapshot_id"] != after["snapshot_id"]:
        raise FreshnessError("INPUT_SNAPSHOT_MOVED_DURING_COLLECTION")
    candidate = decorate_result(base, before)
    return candidate, freshness_markdown(candidate, base_md)


def publish_candidate(repo: Path, artifacts: Path, candidate: dict[str, Any], markdown: str) -> tuple[bool, str]:
    lock_path = repo / LOCK_PATH
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        expected = (candidate.get("input_snapshot") or {}).get("snapshot_id")
        if full_snapshot(repo, artifacts)["snapshot_id"] != expected:
            return False, "REJECT_INPUT_MOVED_BEFORE_PUBLICATION"
        output = repo / OUTPUT_JSON_PATH
        existing: dict[str, Any] | None = None
        if output.exists():
            try:
                existing, _ = stable_json_input(output, OUTPUT_JSON_PATH)
            except FreshnessError:
                existing = None
        publish, decision = publication_decision(existing, candidate)
        if not publish:
            return False, decision
        if full_snapshot(repo, artifacts)["snapshot_id"] != expected:
            return False, "REJECT_INPUT_MOVED_AT_PUBLICATION"
        atomic_write(output, json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n")
        atomic_write(repo / OUTPUT_MD_PATH, markdown.encode("utf-8"))
        return True, decision


def mark_stale_if_needed(repo: Path) -> tuple[bool, str]:
    output = repo / OUTPUT_JSON_PATH
    if not output.exists():
        return False, "NO_AGGREGATE_TO_CLASSIFY"
    lock_path = repo / LOCK_PATH
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if not output.exists():
            return False, "NO_AGGREGATE_TO_CLASSIFY"
        try:
            existing, _ = stable_json_input(output, OUTPUT_JSON_PATH)
            current = live_snapshot(repo)
        except FreshnessError as exc:
            return False, f"FRESHNESS_CHECK_BLOCKED:{exc}"
        bound = existing.get("input_snapshot")
        if not isinstance(bound, dict):
            return False, "HISTORICAL_UNBOUND_AGGREGATE"
        bound_epoch = str(existing.get("authority_epoch") or bound.get("authority_epoch") or "")
        if bound_epoch != current["authority_epoch"]:
            reason = "AUTHORITY_EPOCH_CHANGED"
        elif bound.get("live_snapshot_id") != current["live_snapshot_id"]:
            reason = "LIVE_INPUT_MOVED_AFTER_MEASUREMENT"
        else:
            return False, "AGGREGATE_LIVE_SNAPSHOT_CURRENT"
        updated = copy.deepcopy(existing)
        fresh = updated.get("freshness") if isinstance(updated.get("freshness"), dict) else {}
        fresh.update({
            "schema": GATE_SCHEMA,
            "status": "STALE_UNMEASURED",
            "reason": reason,
            "observed_at": utc_now(),
            "current_authority_epoch": current["authority_epoch"],
            "current_live_snapshot_id": current["live_snapshot_id"],
            "current_latest_input_generated_at": current["latest_input_generated_at"],
            "runtime_credit_added": 0,
        })
        updated["freshness"] = fresh
        atomic_write(output, json.dumps(updated, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n")
        return True, reason


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--artifacts", type=Path, default=Path("/artifacts/clay-entityos-swarm"))
    ap.add_argument("--mark-stale-only", action="store_true")
    args = ap.parse_args()
    repo = args.repo.resolve()
    artifacts = args.artifacts.resolve()

    changed, stale_reason = mark_stale_if_needed(repo)
    if args.mark_stale_only:
        print(json.dumps({"changed": changed, "reason": stale_reason}, sort_keys=True))
        return 0

    candidate: dict[str, Any] | None = None
    try:
        candidate, markdown = build_candidate(repo, artifacts)
        published, decision = publish_candidate(repo, artifacts, candidate, markdown)
        status = "PASS_CURRENT" if published or decision == "IDEMPOTENT_SAME_SNAPSHOT" else "BLOCKED_FAIL_CLOSED"
        current_receipt = receipt(status, candidate, decision, published)
        atomic_write(repo / RECEIPT_PATH, json.dumps(current_receipt, indent=2, sort_keys=True).encode("utf-8") + b"\n")
        print(json.dumps(current_receipt, sort_keys=True))
        return 0 if status == "PASS_CURRENT" else 2
    except FreshnessError as exc:
        current_receipt = receipt("BLOCKED_FAIL_CLOSED", candidate, str(exc), False)
        atomic_write(repo / RECEIPT_PATH, json.dumps(current_receipt, indent=2, sort_keys=True).encode("utf-8") + b"\n")
        print(json.dumps(current_receipt, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
