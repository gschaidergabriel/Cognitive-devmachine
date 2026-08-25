#!/usr/bin/env python3
"""Fail-closed freshness/publication primitives for GO collective metrics.

This module is a guard for the existing ``free swarm/GO_COLLECTIVE_METRICS``
publisher, not a second metrics authority.  It binds one coherent Swarm/Forge/
Distillery live snapshot to the inbox-selected supervisor authority, rejects stale
or mixed inputs, serializes competing writers, and emits a publication receipt.

No provider call, credential access, model/training credit, or canonical-semantic
promotion occurs here.
"""
from __future__ import annotations

import copy
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

SNAPSHOT_SCHEMA = "CLAY_GO_COLLECTIVE_INPUT_SNAPSHOT/v1"
FRESHNESS_SCHEMA = "CLAY_GO_COLLECTIVE_METRICS_FRESHNESS/v1"
RECEIPT_SCHEMA = "COLLECTIVE_METRICS_FRESHNESS_RECEIPT/v1"

LIVE_INPUTS = {
    "swarm": {
        "path": "free swarm/LIVE_METRICS.json",
        "schema": "CLAY_FREE_SWARM_METRICS/v1",
    },
    "forge": {
        "path": "free swarm/FORGE_LIVE.json",
        "schema": "CLAY_FREE_EVIDENCE_FORGE_STATUS/v1",
    },
    "distillery": {
        "path": "free swarm/DISTILLERY_LIVE.json",
        "state": "LIVE",
    },
}


class FreshnessError(RuntimeError):
    pass


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value))


def _parse_ts(value: Any) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise FreshnessError("GENERATED_AT_REQUIRED")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FreshnessError("GENERATED_AT_INVALID") from exc
    if parsed.tzinfo is None:
        raise FreshnessError("GENERATED_AT_TIMEZONE_REQUIRED")
    return parsed.astimezone(dt.timezone.utc)


def _epoch_key(value: Any) -> tuple[int, ...]:
    text = str(value or "").strip()
    if not text:
        raise FreshnessError("AUTHORITY_EPOCH_REQUIRED")
    try:
        parts = tuple(int(part) for part in text.split("."))
    except ValueError as exc:
        raise FreshnessError("AUTHORITY_EPOCH_INVALID") from exc
    if not parts:
        raise FreshnessError("AUTHORITY_EPOCH_INVALID")
    return parts


def _stable_read(path: Path) -> tuple[dict[str, Any], bytes, tuple[int, int, int]]:
    try:
        before = path.stat()
        raw = path.read_bytes()
        after = path.stat()
    except OSError as exc:
        raise FreshnessError(f"INPUT_UNREADABLE:{path}") from exc
    before_token = (before.st_mtime_ns, before.st_size, before.st_ino)
    after_token = (after.st_mtime_ns, after.st_size, after.st_ino)
    if before_token != after_token or len(raw) != after.st_size:
        raise FreshnessError(f"INPUT_CHANGED_DURING_READ:{path}")
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise FreshnessError(f"INPUT_JSON_INVALID:{path}") from exc
    if not isinstance(value, dict):
        raise FreshnessError(f"INPUT_NOT_OBJECT:{path}")
    return value, raw, after_token


def resolve_current_authority(repo: Path) -> dict[str, str]:
    inbox_path = repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox, inbox_raw, _ = _stable_read(inbox_path)
    epoch = str(inbox.get("schema_version") or "").strip()
    _epoch_key(epoch)
    steering_rel = str(inbox.get("steering") or "").strip()
    if not steering_rel:
        raise FreshnessError("SUPERVISOR_STEERING_POINTER_REQUIRED")
    steering_path = repo / steering_rel
    steering, steering_raw, _ = _stable_read(steering_path)
    if _epoch_key(steering.get("schema_version")) != _epoch_key(epoch):
        raise FreshnessError("SUPERVISOR_INBOX_STEERING_EPOCH_MISMATCH")
    if steering.get("program") != "ENTITYOS_HCU" or steering.get("product") != "EntityOS":
        raise FreshnessError("SUPERVISOR_PROGRAM_PRODUCT_MISMATCH")
    return {
        "authority_epoch": epoch,
        "inbox_path": inbox_path.relative_to(repo).as_posix(),
        "inbox_sha256": _sha256_bytes(inbox_raw),
        "steering_path": steering_rel,
        "steering_sha256": _sha256_bytes(steering_raw),
    }


def _nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise FreshnessError(f"LIVE_FIELD_INVALID:{label}")
    return value


def _extract_fields(name: str, doc: dict[str, Any]) -> dict[str, int]:
    if name == "swarm":
        workers = doc.get("workers") if isinstance(doc.get("workers"), dict) else {}
        return {
            "free_swarm_total_tokens": _nonnegative_int(workers.get("total_tokens"), "swarm.total_tokens"),
            "free_swarm_worker_records": _nonnegative_int(workers.get("worker_records"), "swarm.worker_records"),
        }
    if name == "forge":
        return {
            "forge_evaluations": _nonnegative_int(doc.get("evaluations"), "forge.evaluations"),
            "forge_accepted_deltas": _nonnegative_int(doc.get("accepted_deltas"), "forge.accepted_deltas"),
        }
    if name == "distillery":
        return {
            "distillery_accepted_packets": _nonnegative_int(doc.get("accepted_packets"), "distillery.accepted_packets"),
            "distillery_accepted_dataset_tokens": _nonnegative_int(doc.get("accepted_dataset_tokens"), "distillery.accepted_dataset_tokens"),
        }
    raise FreshnessError(f"UNKNOWN_LIVE_INPUT:{name}")


def build_live_snapshot(
    repo: Path,
    *,
    now: dt.datetime | None = None,
    max_age_seconds: float = 3600.0,
    max_snapshot_skew_seconds: float = 30.0,
    max_future_skew_seconds: float = 60.0,
) -> dict[str, Any]:
    """Capture one coherent current snapshot or fail closed.

    Freshness is a property of the *inputs at publication time*, not of a writer's
    wall-clock timestamp.  Every source must be recent, near the other sources, and
    unchanged from its read until the snapshot identity is sealed.
    """
    repo = repo.resolve()
    authority = resolve_current_authority(repo)
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    inputs: dict[str, dict[str, Any]] = {}
    fields: dict[str, dict[str, Any]] = {}
    times: list[dt.datetime] = []
    stat_tokens: dict[str, tuple[int, int, int]] = {}

    for name, spec in LIVE_INPUTS.items():
        rel = str(spec["path"])
        path = repo / rel
        doc, raw, stat_token = _stable_read(path)
        if "schema" in spec and doc.get("schema") != spec["schema"]:
            raise FreshnessError(f"LIVE_SCHEMA_MISMATCH:{name}")
        if "state" in spec and doc.get("state") != spec["state"]:
            raise FreshnessError(f"LIVE_STATE_MISMATCH:{name}")
        ts = _parse_ts(doc.get("generated_at"))
        age = (now - ts).total_seconds()
        if age > max_age_seconds:
            raise FreshnessError(f"STALE_LIVE_INPUT:{name}")
        if age < -max_future_skew_seconds:
            raise FreshnessError(f"FUTURE_LIVE_INPUT:{name}")
        times.append(ts)
        stat_tokens[rel] = stat_token
        inputs[name] = {
            "path": rel,
            "sha256": _sha256_bytes(raw),
            "generated_at": ts.isoformat(),
            "age_seconds": age,
        }
        for field, value in _extract_fields(name, doc).items():
            fields[field] = {"value": value, "source": name}

    skew = (max(times) - min(times)).total_seconds()
    if skew > max_snapshot_skew_seconds:
        raise FreshnessError("SHARED_SNAPSHOT_SKEW_EXCEEDED")

    # Detect cross-file tearing: no input may change after it was read while the
    # remaining members of the shared snapshot are being captured.
    for rel, expected in stat_tokens.items():
        path = repo / rel
        try:
            current = path.stat()
        except OSError as exc:
            raise FreshnessError(f"INPUT_DISAPPEARED:{rel}") from exc
        actual = (current.st_mtime_ns, current.st_size, current.st_ino)
        if actual != expected:
            raise FreshnessError(f"INPUT_CHANGED_DURING_SNAPSHOT:{rel}")

    preimage = {
        "schema": SNAPSHOT_SCHEMA,
        "authority": authority,
        "inputs": inputs,
        "min_input_generated_at": min(times).isoformat(),
        "max_input_generated_at": max(times).isoformat(),
        "max_age_seconds": max_age_seconds,
        "max_snapshot_skew_seconds": max_snapshot_skew_seconds,
    }
    snapshot_id = _sha256_json(preimage)
    for item in fields.values():
        item["snapshot_id"] = snapshot_id
    return {
        **preimage,
        "snapshot_id": snapshot_id,
        "observed_at": now.isoformat(),
        "snapshot_skew_seconds": skew,
        "fields": dict(sorted(fields.items())),
    }


def deterministic_result_digest(result: dict[str, Any]) -> str:
    payload = copy.deepcopy(result)
    payload.pop("generated_at", None)
    payload.pop("result_digest_sha256", None)
    freshness = payload.get("freshness")
    if isinstance(freshness, dict):
        freshness.pop("assessed_at", None)
    return _sha256_json(payload)


def publication_decision(existing: dict[str, Any], candidate: dict[str, Any]) -> str:
    if not existing:
        return "PUBLISH_NO_EXISTING"
    old_epoch = _epoch_key(existing.get("authority_epoch"))
    new_epoch = _epoch_key(candidate.get("authority_epoch"))
    if old_epoch > new_epoch:
        return "REJECT_OLDER_AUTHORITY_WRITER"
    if old_epoch < new_epoch:
        return "PUBLISH_SUPERSEDES_HISTORICAL_AUTHORITY"

    old_snapshot = existing.get("bounded_live_snapshot")
    new_snapshot = candidate.get("bounded_live_snapshot")
    if not isinstance(new_snapshot, dict):
        return "REJECT_CANDIDATE_SNAPSHOT_UNRESOLVED"
    if not isinstance(old_snapshot, dict):
        return "PUBLISH_SUPERSEDES_UNMEASURED_SNAPSHOT"
    old_max = _parse_ts(old_snapshot.get("max_input_generated_at"))
    new_max = _parse_ts(new_snapshot.get("max_input_generated_at"))
    if new_max < old_max:
        return "REJECT_OUT_OF_ORDER_OLDER_SNAPSHOT"
    if new_max > old_max:
        return "PUBLISH_NEWER_SNAPSHOT"
    if old_snapshot.get("snapshot_id") != new_snapshot.get("snapshot_id"):
        return "REJECT_EQUAL_TIME_SNAPSHOT_CONFLICT"
    if existing.get("result_digest_sha256") != candidate.get("result_digest_sha256"):
        return "REJECT_NONDETERMINISTIC_SAME_SNAPSHOT"
    return "IDEMPOTENT_IDENTICAL_RESULT"


def assess_published_freshness(published: dict[str, Any], current_snapshot: dict[str, Any]) -> dict[str, Any]:
    current_epoch = current_snapshot["authority"]["authority_epoch"]
    if _epoch_key(published.get("authority_epoch")) != _epoch_key(current_epoch):
        return {"schema": FRESHNESS_SCHEMA, "status": "HISTORICAL_AUTHORITY_EPOCH"}
    prior = published.get("bounded_live_snapshot")
    if not isinstance(prior, dict):
        return {"schema": FRESHNESS_SCHEMA, "status": "UNMEASURED_SNAPSHOT_IDENTITY"}
    if prior.get("snapshot_id") == current_snapshot.get("snapshot_id"):
        return {"schema": FRESHNESS_SCHEMA, "status": "FRESH"}
    if _parse_ts(prior.get("max_input_generated_at")) < _parse_ts(current_snapshot.get("max_input_generated_at")):
        return {"schema": FRESHNESS_SCHEMA, "status": "STALE_NEWER_CANONICAL_INPUT"}
    return {"schema": FRESHNESS_SCHEMA, "status": "SNAPSHOT_MISMATCH_FAIL_CLOSED"}


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if tmp.exists():
            tmp.unlink()


def publish_bundle(
    *,
    out_json: Path,
    out_md: Path,
    result: dict[str, Any],
    markdown: str,
    receipt_path: Path,
    readme_path: Path | None = None,
    readme_text: str | None = None,
) -> dict[str, Any]:
    """Serialize writers, reject regressions, and commit a receipt last."""
    lock_path = out_json.with_name(out_json.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            try:
                existing = json.loads(out_json.read_text(encoding="utf-8")) if out_json.exists() else {}
                if not isinstance(existing, dict):
                    raise FreshnessError("CURRENT_PUBLICATION_NOT_OBJECT")
            except FreshnessError:
                raise
            except Exception as exc:
                raise FreshnessError("CURRENT_PUBLICATION_UNREADABLE") from exc
            decision = publication_decision(existing, result)
            if decision.startswith("REJECT_"):
                raise FreshnessError(decision)
            receipt = {
                "schema": RECEIPT_SCHEMA,
                "authority_epoch": result["authority_epoch"],
                "snapshot_id": result["bounded_live_snapshot"]["snapshot_id"],
                "max_input_generated_at": result["bounded_live_snapshot"]["max_input_generated_at"],
                "result_digest_sha256": result["result_digest_sha256"],
                "decision": decision,
                "scope": "COLLECTIVE_METRICS_FRESHNESS_AND_SHARED_SNAPSHOT_PUBLICATION_ONLY",
                "runtime_credit_added": 0,
                "model_credit_added": 0,
                "training_credit_added": 0,
            }
            if decision == "IDEMPOTENT_IDENTICAL_RESULT":
                return receipt
            _atomic_write_text(out_json, json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
            _atomic_write_text(out_md, markdown)
            if readme_path is not None and readme_text is not None:
                _atomic_write_text(readme_path, readme_text)
            # Receipt is the commit marker and is emitted only after the bound outputs.
            _atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
            return receipt
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
