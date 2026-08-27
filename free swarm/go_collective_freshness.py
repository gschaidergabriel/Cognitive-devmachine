#!/usr/bin/env python3
"""Fail-closed freshness and publication primitives for GO collective metrics.

This module does not create a second metrics authority. It binds the existing
GO_COLLECTIVE_METRICS publisher to one exact repository snapshot of Swarm,
Forge and Distillery live surfaces, the inbox-selected supervisor epoch, and a
serialized monotonic publication lock. The freshness receipt is written last
and acts as the commit marker for the accepted JSON/Markdown pair.
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
LIVE_INPUT_PATHS = {
    "swarm": "free swarm/LIVE_METRICS.json",
    "forge": "free swarm/FORGE_LIVE.json",
    "distillery": "free swarm/DISTILLERY_LIVE.json",
}


def _parse_ts(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _sha256_bytes(encoded)


def _read_json_bytes(path: Path) -> tuple[dict[str, Any], bytes]:
    data = path.read_bytes()
    value = json.loads(data)
    if not isinstance(value, dict):
        raise RuntimeError(f"BOUNDED_INPUT_NOT_OBJECT:{path}")
    return value, data


def _epoch_key(value: Any) -> tuple[int, ...] | None:
    text = str(value or "").strip()
    if not text:
        return None
    parts = text.split(".")
    if not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def selected_authority_epoch(repo: Path) -> str:
    """Resolve the inbox-selected supervisor epoch and fail closed on drift."""
    inbox_path = repo / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    inbox, _ = _read_json_bytes(inbox_path)
    epoch = str(inbox.get("schema_version") or "").strip()
    steering_rel = str(inbox.get("steering") or "").strip()
    if _epoch_key(epoch) is None or not steering_rel:
        raise RuntimeError("SUPERVISOR_INBOX_SELECTION_UNRESOLVED")
    steering_path = repo / steering_rel
    steering, _ = _read_json_bytes(steering_path)
    if str(steering.get("schema_version") or "").strip() != epoch:
        raise RuntimeError("SUPERVISOR_INBOX_STEERING_EPOCH_MISMATCH")
    if steering.get("program") != "ENTITYOS_HCU":
        raise RuntimeError("SUPERVISOR_STEERING_PROGRAM_MISMATCH")
    return epoch


def _extract_fields(name: str, doc: dict[str, Any]) -> dict[str, Any]:
    if name == "swarm":
        workers = doc.get("workers") if isinstance(doc.get("workers"), dict) else {}
        return {
            "free_swarm_total_tokens": workers.get("total_tokens"),
            "free_swarm_worker_records": workers.get("worker_records"),
        }
    if name == "forge":
        return {
            "forge_evaluations": doc.get("evaluations"),
            "forge_accepted_deltas": doc.get("accepted_deltas"),
        }
    if name == "distillery":
        return {
            "distillery_accepted_packets": doc.get("accepted_packets"),
            "distillery_accepted_dataset_tokens": doc.get("accepted_dataset_tokens"),
        }
    raise RuntimeError(f"UNKNOWN_LIVE_INPUT:{name}")


def build_live_snapshot(repo: Path) -> dict[str, Any]:
    """Read each canonical live surface once and bind all exposed fields to one identity."""
    epoch = selected_authority_epoch(repo)
    raw_inputs: dict[str, dict[str, Any]] = {}
    extracted: dict[str, tuple[str, Any]] = {}
    times: list[dt.datetime] = []

    for name, rel in LIVE_INPUT_PATHS.items():
        path = repo / rel
        doc, raw = _read_json_bytes(path)
        generated_at = doc.get("generated_at")
        parsed = _parse_ts(generated_at)
        if parsed is None:
            raise RuntimeError(f"LIVE_INPUT_GENERATED_AT_UNRESOLVED:{name}")
        times.append(parsed)
        raw_inputs[name] = {
            "path": rel,
            "sha256": _sha256_bytes(raw),
            "generated_at": generated_at,
            "schema": doc.get("schema") or doc.get("state") or "UNKNOWN",
        }
        for field, value in _extract_fields(name, doc).items():
            extracted[field] = (name, value)

    identity_preimage = {
        "schema": SNAPSHOT_SCHEMA,
        "authority_epoch": epoch,
        "inputs": raw_inputs,
    }
    snapshot_id = _sha256_json(identity_preimage)
    fields = {
        field: {"value": value, "source": source, "snapshot_id": snapshot_id}
        for field, (source, value) in sorted(extracted.items())
    }
    return {
        **identity_preimage,
        "snapshot_id": snapshot_id,
        "min_input_generated_at": min(times).astimezone(dt.timezone.utc).isoformat(),
        "max_input_generated_at": max(times).astimezone(dt.timezone.utc).isoformat(),
        "fields": fields,
    }


def assess_published_freshness(
    published: dict[str, Any], current_snapshot: dict[str, Any], current_epoch: str
) -> dict[str, Any]:
    """Classify an existing aggregate against current canonical inputs."""
    published_epoch = str(published.get("authority_epoch") or "").strip()
    if published_epoch != current_epoch:
        return {
            "schema": FRESHNESS_SCHEMA,
            "status": "HISTORICAL_AUTHORITY_EPOCH",
            "published_authority_epoch": published_epoch or None,
            "current_authority_epoch": current_epoch,
        }
    previous = published.get("bounded_live_snapshot")
    if not isinstance(previous, dict):
        return {"schema": FRESHNESS_SCHEMA, "status": "UNMEASURED_SNAPSHOT_IDENTITY"}
    if previous.get("snapshot_id") == current_snapshot.get("snapshot_id"):
        return {"schema": FRESHNESS_SCHEMA, "status": "FRESH"}
    prev_max = _parse_ts(previous.get("max_input_generated_at"))
    cur_max = _parse_ts(current_snapshot.get("max_input_generated_at"))
    if prev_max is not None and cur_max is not None and prev_max < cur_max:
        return {
            "schema": FRESHNESS_SCHEMA,
            "status": "STALE_NEWER_CANONICAL_INPUT",
            "published_max_input_generated_at": prev_max.isoformat(),
            "current_max_input_generated_at": cur_max.isoformat(),
        }
    return {"schema": FRESHNESS_SCHEMA, "status": "UNMEASURED_SNAPSHOT_MISMATCH"}


def deterministic_result_digest(result: dict[str, Any]) -> str:
    """Stable digest for identical bounded measurement inputs, excluding wall-clock narration."""
    payload = copy.deepcopy(result)
    payload.pop("generated_at", None)
    payload.pop("result_digest_sha256", None)
    freshness = payload.get("freshness")
    if isinstance(freshness, dict):
        freshness.pop("assessed_at", None)
    return _sha256_json(payload)


def publication_decision(existing: dict[str, Any], candidate: dict[str, Any]) -> str:
    """Prevent a slower/older writer from regressing the latest published snapshot."""
    if not existing:
        return "PUBLISH_NO_EXISTING"
    old_epoch = _epoch_key(existing.get("authority_epoch"))
    new_epoch = _epoch_key(candidate.get("authority_epoch"))
    if new_epoch is None:
        return "REJECT_CANDIDATE_AUTHORITY_UNRESOLVED"
    if old_epoch is None or old_epoch < new_epoch:
        return "PUBLISH_SUPERSEDES_HISTORICAL_AUTHORITY"
    if old_epoch > new_epoch:
        return "REJECT_OLDER_AUTHORITY_WRITER"

    old_snapshot = existing.get("bounded_live_snapshot")
    new_snapshot = candidate.get("bounded_live_snapshot")
    if not isinstance(new_snapshot, dict):
        return "REJECT_CANDIDATE_SNAPSHOT_UNRESOLVED"
    if not isinstance(old_snapshot, dict):
        return "PUBLISH_SUPERSEDES_UNMEASURED_SNAPSHOT"

    old_max = _parse_ts(old_snapshot.get("max_input_generated_at"))
    new_max = _parse_ts(new_snapshot.get("max_input_generated_at"))
    if old_max is None or new_max is None:
        return "REJECT_PUBLICATION_ORDER_UNRESOLVED"
    if new_max < old_max:
        return "REJECT_OUT_OF_ORDER_OLDER_SNAPSHOT"
    if new_max > old_max:
        return "PUBLISH_NEWER_SNAPSHOT"

    if old_snapshot.get("snapshot_id") == new_snapshot.get("snapshot_id"):
        if existing.get("result_digest_sha256") == candidate.get("result_digest_sha256"):
            return "IDEMPOTENT_IDENTICAL_RESULT"
        return "REJECT_SAME_SNAPSHOT_RESULT_DIVERGENCE"
    return "REJECT_EQUAL_TIME_SNAPSHOT_CONFLICT"


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


def _receipt_path(out_json: Path) -> Path:
    return out_json.with_name("COLLECTIVE_METRICS_FRESHNESS_RECEIPT.json")


def validate_bundle(out_json: Path, out_md: Path, receipt_path: Path | None = None) -> dict[str, Any]:
    receipt_path = receipt_path or _receipt_path(out_json)
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError("COLLECTIVE_METRICS_FRESHNESS_RECEIPT_REQUIRED") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != RECEIPT_SCHEMA:
        raise RuntimeError("COLLECTIVE_METRICS_FRESHNESS_RECEIPT_INVALID")
    if _sha256_bytes(out_json.read_bytes()) != receipt.get("json_sha256"):
        raise RuntimeError("COLLECTIVE_METRICS_JSON_RECEIPT_MISMATCH")
    if _sha256_bytes(out_md.read_bytes()) != receipt.get("markdown_sha256"):
        raise RuntimeError("COLLECTIVE_METRICS_MD_RECEIPT_MISMATCH")
    return receipt


def publish_bundle(
    *,
    out_json: Path,
    out_md: Path,
    result: dict[str, Any],
    markdown: str,
    readme_path: Path | None = None,
    readme_text: str | None = None,
    receipt_path: Path | None = None,
) -> str:
    """Serialize publication, reject regressions, then write receipt commit marker last."""
    lock_path = out_json.with_name(out_json.name + ".lock")
    receipt_path = receipt_path or _receipt_path(out_json)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            try:
                existing = json.loads(out_json.read_text(encoding="utf-8"))
                if not isinstance(existing, dict):
                    existing = {}
            except Exception:
                existing = {}
            decision = publication_decision(existing, result)
            if decision.startswith("REJECT_"):
                raise RuntimeError(decision)
            if decision == "IDEMPOTENT_IDENTICAL_RESULT":
                validate_bundle(out_json, out_md, receipt_path)
                return decision

            json_text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
            _atomic_write_text(out_json, json_text)
            _atomic_write_text(out_md, markdown)
            if readme_path is not None and readme_text is not None:
                _atomic_write_text(readme_path, readme_text)
            receipt = {
                "schema": RECEIPT_SCHEMA,
                "authority_epoch": result.get("authority_epoch"),
                "snapshot_id": (result.get("bounded_live_snapshot") or {}).get("snapshot_id"),
                "source_observed_at": (result.get("bounded_live_snapshot") or {}).get("max_input_generated_at"),
                "result_digest_sha256": result.get("result_digest_sha256"),
                "collector_sha256": result.get("collector_sha256"),
                "config_sha256": result.get("config_sha256"),
                "json_sha256": _sha256_bytes(out_json.read_bytes()),
                "markdown_sha256": _sha256_bytes(out_md.read_bytes()),
                "publication_decision": decision,
                "published_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "runtime_credit_added": 0,
                "model_credit_added": 0,
                "training_credit_added": 0,
            }
            _atomic_write_text(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
            validate_bundle(out_json, out_md, receipt_path)
            return decision
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
