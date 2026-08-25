#!/usr/bin/env python3
"""Fail-closed publication gate for Clay GO collective metrics.

This module does not create a second metrics authority. It guards publication to the
existing ``free swarm/GO_COLLECTIVE_METRICS.*`` surfaces by binding one bounded input
snapshot across Swarm, Forge and Distillery plus the inbox-selected supervisor authority.

It performs no provider calls, reads no credentials and grants no runtime/model/training
credit. A successful gate proves only publication freshness/coherence at the bound files.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterator, NamedTuple

SNAPSHOT_SCHEMA = "CLAY_GO_COLLECTIVE_INPUT_SNAPSHOT/v1"
RECEIPT_SCHEMA = "COLLECTIVE_METRICS_FRESHNESS_RECEIPT/v1"
PUBLISH_SCHEMA = "CLAY_GO_COLLECTIVE_FRESHNESS_PUBLICATION/v1"


class FreshnessError(RuntimeError):
    """Fail-closed publication error."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(_canonical_json(value))


def parse_ts(value: Any) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise FreshnessError("INPUT_GENERATED_AT_MISSING")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FreshnessError("INPUT_GENERATED_AT_INVALID") from exc
    if parsed.tzinfo is None:
        raise FreshnessError("INPUT_GENERATED_AT_NAIVE")
    return parsed.astimezone(dt.timezone.utc)


def iso(ts: dt.datetime) -> str:
    return ts.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def epoch_key(value: Any) -> tuple[int, ...]:
    text = str(value or "").strip()
    if not text:
        raise FreshnessError("AUTHORITY_EPOCH_MISSING")
    try:
        parts = tuple(int(part) for part in text.split("."))
    except ValueError as exc:
        raise FreshnessError("AUTHORITY_EPOCH_INVALID") from exc
    if not parts:
        raise FreshnessError("AUTHORITY_EPOCH_INVALID")
    return parts


class Surface(NamedTuple):
    name: str
    path: str
    generated_at: str
    sha256: str
    payload: dict[str, Any]

    def identity(self) -> dict[str, str]:
        return {
            "name": self.name,
            "path": self.path,
            "generated_at": self.generated_at,
            "sha256": self.sha256,
        }


def _read_surface(name: str, path: Path, repo: Path) -> Surface:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise FreshnessError(f"INPUT_MISSING:{name}") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise FreshnessError(f"INPUT_JSON_INVALID:{name}") from exc
    if not isinstance(payload, dict):
        raise FreshnessError(f"INPUT_JSON_NOT_OBJECT:{name}")
    generated_at = iso(parse_ts(payload.get("generated_at")))
    try:
        rel = path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        rel = str(path.resolve())
    return Surface(name, rel, generated_at, sha256_bytes(raw), payload)


def resolve_authority(repo: Path) -> dict[str, Any]:
    inbox_path = repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    try:
        inbox_raw = inbox_path.read_bytes()
        inbox = json.loads(inbox_raw.decode("utf-8"))
    except Exception as exc:
        raise FreshnessError("SUPERVISOR_INBOX_UNREADABLE") from exc
    if not isinstance(inbox, dict):
        raise FreshnessError("SUPERVISOR_INBOX_NOT_OBJECT")
    epoch = str(inbox.get("schema_version") or "").strip()
    epoch_key(epoch)
    steering_rel = inbox.get("steering")
    if not isinstance(steering_rel, str) or not steering_rel.strip():
        raise FreshnessError("SUPERVISOR_STEERING_POINTER_MISSING")
    steering_path = repo / steering_rel
    try:
        steering_raw = steering_path.read_bytes()
        steering = json.loads(steering_raw.decode("utf-8"))
    except Exception as exc:
        raise FreshnessError("SUPERVISOR_STEERING_UNREADABLE") from exc
    if not isinstance(steering, dict):
        raise FreshnessError("SUPERVISOR_STEERING_NOT_OBJECT")
    if str(steering.get("schema_version") or "").strip() != epoch:
        raise FreshnessError("AUTHORITY_EPOCH_MISMATCH")
    program = steering.get("program", steering.get("active_program"))
    if program != "ENTITYOS_HCU" or steering.get("product") != "EntityOS":
        raise FreshnessError("AUTHORITY_PROGRAM_PRODUCT_MISMATCH")
    return {
        "authority_epoch": epoch,
        "inbox_path": inbox_path.relative_to(repo).as_posix(),
        "inbox_sha256": sha256_bytes(inbox_raw),
        "steering_path": steering_rel,
        "steering_sha256": sha256_bytes(steering_raw),
    }


def _bounded_source_metrics(surfaces: dict[str, Surface], snapshot_id: str) -> dict[str, Any]:
    swarm = surfaces["swarm"]
    forge = surfaces["forge"]
    dist = surfaces["distillery"]
    workers = swarm.payload.get("workers") if isinstance(swarm.payload.get("workers"), dict) else {}
    return {
        "bounded_snapshot_id": snapshot_id,
        "swarm_snapshot_id": snapshot_id,
        "forge_snapshot_id": snapshot_id,
        "distillery_snapshot_id": snapshot_id,
        "free_swarm_live_metrics_generated_at": swarm.generated_at,
        "worker_records": workers.get("worker_records"),
        "exact_usage_rows": workers.get("exact_usage_rows"),
        "input_tokens": workers.get("input_tokens"),
        "output_tokens": workers.get("output_tokens"),
        "total_tokens": workers.get("total_tokens"),
        "forge_generated_at": forge.generated_at,
        "forge_discovery_hits": forge.payload.get("discovery_hits"),
        "forge_evaluations": forge.payload.get("evaluations"),
        "forge_accepted_deltas": forge.payload.get("accepted_deltas"),
        "distillery_generated_at": dist.generated_at,
        "distillery_collected_source_tokens": dist.payload.get("collected_source_tokens"),
        "distillery_collected_chunks": dist.payload.get("collected_chunks"),
        "distillery_accepted_packets": dist.payload.get("accepted_packets"),
        "distillery_accepted_dataset_tokens": dist.payload.get("accepted_dataset_tokens"),
    }


def build_snapshot(repo: Path) -> dict[str, Any]:
    authority = resolve_authority(repo)
    ordered = [
        _read_surface("swarm", repo / "free swarm/LIVE_METRICS.json", repo),
        _read_surface("forge", repo / "free swarm/FORGE_LIVE.json", repo),
        _read_surface("distillery", repo / "free swarm/DISTILLERY_LIVE.json", repo),
    ]
    surfaces = {surface.name: surface for surface in ordered}
    timestamps = [parse_ts(surface.generated_at) for surface in ordered]
    identity_core = {
        "schema": SNAPSHOT_SCHEMA,
        "authority": authority,
        "surfaces": [surface.identity() for surface in ordered],
    }
    snapshot_id = sha256_json(identity_core)
    surface_rows = []
    for surface in ordered:
        row = surface.identity()
        row["snapshot_id"] = snapshot_id
        surface_rows.append(row)
    return {
        "schema": SNAPSHOT_SCHEMA,
        "snapshot_id": snapshot_id,
        "authority": authority,
        "min_input_generated_at": iso(min(timestamps)),
        "max_input_generated_at": iso(max(timestamps)),
        "surfaces": surface_rows,
        "source_metrics": _bounded_source_metrics(surfaces, snapshot_id),
    }


def _materialize_candidate(candidate: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    out = dict(candidate)
    out["authority_epoch"] = snapshot["authority"]["authority_epoch"]
    out["source_metrics"] = snapshot["source_metrics"]
    return out


def candidate_digest(candidate: dict[str, Any], snapshot: dict[str, Any]) -> str:
    payload = _materialize_candidate(candidate, snapshot)
    payload.pop("generated_at", None)
    payload.pop("freshness", None)
    return sha256_json({"candidate": payload, "snapshot_id": snapshot["snapshot_id"]})


def publication_decision(
    candidate: dict[str, Any],
    snapshot: dict[str, Any],
    current: dict[str, Any] | None,
) -> dict[str, Any]:
    candidate_epoch = str(candidate.get("authority_epoch") or snapshot["authority"]["authority_epoch"])
    current_epoch = snapshot["authority"]["authority_epoch"]
    if epoch_key(candidate_epoch) != epoch_key(current_epoch):
        raise FreshnessError("CANDIDATE_AUTHORITY_EPOCH_MISMATCH")

    digest = candidate_digest(candidate, snapshot)
    if not current:
        return {
            "action": "PUBLISH",
            "reason": "NO_CURRENT_PUBLICATION",
            "current_state": "UNMEASURED",
            "result_digest_sha256": digest,
        }

    cur_fresh = current.get("freshness") if isinstance(current.get("freshness"), dict) else {}
    cur_epoch_raw = current.get("authority_epoch")
    current_state = "UNMEASURED"
    if cur_epoch_raw:
        cur_epoch = epoch_key(cur_epoch_raw)
        new_epoch = epoch_key(candidate_epoch)
        if cur_epoch > new_epoch:
            raise FreshnessError("OUT_OF_ORDER_AUTHORITY_REGRESSION")
        if cur_epoch < new_epoch:
            current_state = "HISTORICAL_AUTHORITY"

    cur_snapshot = cur_fresh.get("snapshot") if isinstance(cur_fresh.get("snapshot"), dict) else {}
    cur_snapshot_id = cur_snapshot.get("snapshot_id")
    cur_max_raw = cur_snapshot.get("max_input_generated_at")
    if current_state != "HISTORICAL_AUTHORITY" and cur_max_raw:
        cur_max = parse_ts(cur_max_raw)
        new_max = parse_ts(snapshot["max_input_generated_at"])
        if new_max < cur_max:
            raise FreshnessError("OUT_OF_ORDER_INPUT_SNAPSHOT")
        if new_max > cur_max:
            current_state = "STALE_INPUT_SNAPSHOT"
        elif cur_snapshot_id and cur_snapshot_id != snapshot["snapshot_id"]:
            raise FreshnessError("AMBIGUOUS_EQUAL_TIME_DIFFERENT_SNAPSHOT")

    if cur_snapshot_id == snapshot["snapshot_id"]:
        cur_digest = cur_fresh.get("result_digest_sha256")
        if cur_digest == digest:
            return {
                "action": "NO_CHANGE",
                "reason": "IDEMPOTENT_REPLAY",
                "current_state": "CURRENT",
                "result_digest_sha256": digest,
            }
        raise FreshnessError("SAME_SNAPSHOT_DIFFERENT_RESULT")

    reason = {
        "HISTORICAL_AUTHORITY": "CURRENT_PUBLICATION_HISTORICAL_AUTHORITY",
        "STALE_INPUT_SNAPSHOT": "CURRENT_PUBLICATION_STALE_INPUT",
        "UNMEASURED": "CURRENT_PUBLICATION_UNMEASURED",
    }.get(current_state, "FRESHER_BOUND_SNAPSHOT")
    return {
        "action": "PUBLISH",
        "reason": reason,
        "current_state": current_state,
        "result_digest_sha256": digest,
    }


def attach_freshness(candidate: dict[str, Any], snapshot: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    out = _materialize_candidate(candidate, snapshot)
    out["freshness"] = {
        "schema": PUBLISH_SCHEMA,
        "state": "FRESH_BOUND_SNAPSHOT",
        "snapshot": snapshot,
        "result_digest_sha256": decision["result_digest_sha256"],
        "runtime_credit_added": 0,
    }
    return out


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    with tmp.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    try:
        dir_fd = os.open(path.parent, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


@contextmanager
def publication_lock(output_path: Path) -> Iterator[None]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = output_path.with_name(output_path.name + ".lock")
    with lock_path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _load_current(output_path: Path) -> dict[str, Any] | None:
    if not output_path.exists():
        return None
    try:
        parsed = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FreshnessError("CURRENT_PUBLICATION_UNREADABLE") from exc
    if not isinstance(parsed, dict):
        raise FreshnessError("CURRENT_PUBLICATION_NOT_OBJECT")
    return parsed


def publish(repo: Path, candidate_path: Path, output_path: Path, receipt_path: Path) -> dict[str, Any]:
    snapshot_before = build_snapshot(repo)
    try:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FreshnessError("CANDIDATE_UNREADABLE") from exc
    if not isinstance(candidate, dict):
        raise FreshnessError("CANDIDATE_NOT_OBJECT")

    with publication_lock(output_path):
        snapshot_locked = build_snapshot(repo)
        if snapshot_locked["snapshot_id"] != snapshot_before["snapshot_id"]:
            raise FreshnessError("INPUT_CHANGED_BEFORE_LOCKED_PUBLICATION")

        current = _load_current(output_path)
        decision = publication_decision(candidate, snapshot_locked, current)

        snapshot_after = build_snapshot(repo)
        if snapshot_after["snapshot_id"] != snapshot_locked["snapshot_id"]:
            raise FreshnessError("INPUT_CHANGED_DURING_PUBLICATION")

        receipt = {
            "schema": RECEIPT_SCHEMA,
            "generated_at": iso(dt.datetime.now(dt.timezone.utc)),
            "status": "PASS" if decision["action"] in {"PUBLISH", "NO_CHANGE"} else "FAIL",
            "decision": decision,
            "snapshot": snapshot_after,
            "candidate_path": str(candidate_path),
            "output_path": str(output_path),
            "scope": "COLLECTIVE_METRICS_FRESHNESS_AND_BOUND_SNAPSHOT_PUBLICATION_ONLY",
            "runtime_credit_added": 0,
        }

        if decision["action"] == "PUBLISH":
            published = attach_freshness(candidate, snapshot_after, decision)
            atomic_write(
                output_path,
                json.dumps(published, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n",
            )
        atomic_write(
            receipt_path,
            json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n",
        )
        return receipt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--candidate-json", type=Path, required=True)
    ap.add_argument("--output-json", type=Path, default=None)
    ap.add_argument("--receipt", type=Path, default=None)
    args = ap.parse_args()
    repo = args.repo.resolve()
    output = args.output_json or (repo / "free swarm/GO_COLLECTIVE_METRICS.json")
    receipt = args.receipt or (
        repo / "research_entity/continuity/receipts/COLLECTIVE_METRICS_FRESHNESS_LATEST.json"
    )
    result = publish(repo, args.candidate_json, output, receipt)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
