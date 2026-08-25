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
import datetime as dt
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
        return tuple(int(part) for part in text.split("."))
    except ValueError as exc:
        raise FreshnessError("AUTHORITY_EPOCH_INVALID") from exc


@dataclass(frozen=True)
class Surface:
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
    if steering.get("program") != "ENTITYOS_HCU" or steering.get("product") != "EntityOS":
        raise FreshnessError("AUTHORITY_PROGRAM_PRODUCT_MISMATCH")
    return {
        "authority_epoch": epoch,
        "inbox_path": inbox_path.relative_to(repo).as_posix(),
        "inbox_sha256": sha256_bytes(inbox_raw),
        "steering_path": steering_rel,
        "steering_sha256": sha256_bytes(steering_raw),
    }


def build_snapshot(repo: Path) -> dict[str, Any]:
    authority = resolve_authority(repo)
    surfaces = [
        _read_surface("swarm", repo / "free swarm/LIVE_METRICS.json", repo),
        _read_surface("forge", repo / "free swarm/FORGE_LIVE.json", repo),
        _read_surface("distillery", repo / "free swarm/DISTILLERY_LIVE.json", repo),
    ]
    timestamps = [parse_ts(s.generated_at) for s in surfaces]
    identity_core = {
        "schema": SNAPSHOT_SCHEMA,
        "authority": authority,
        "surfaces": [s.identity() for s in surfaces],
    }
    snapshot_id = sha256_json(identity_core)
    surface_rows = []
    for surface in surfaces:
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
    }


def candidate_digest(candidate: dict[str, Any], snapshot: dict[str, Any]) -> str:
    payload = dict(candidate)
    payload.pop("generated_at", None)
    payload.pop("freshness", None)
    return sha256_json({"candidate": payload, "snapshot_id": snapshot["snapshot_id"]})


def publication_decision(
    candidate: dict[str, Any],
    snapshot: dict[str, Any],
    current: dict[str, Any] | None,
) -> dict[str, Any]:
    candidate_epoch = str(candidate.get("authority_epoch") or snapshot["authority"]["authority_epoch"])
    if epoch_key(candidate_epoch) != epoch_key(snapshot["authority"]["authority_epoch"]):
        raise FreshnessError("CANDIDATE_AUTHORITY_EPOCH_MISMATCH")

    digest = candidate_digest(candidate, snapshot)
    if not current:
        return {"action": "PUBLISH", "reason": "NO_CURRENT_PUBLICATION", "result_digest_sha256": digest}

    cur_fresh = current.get("freshness") if isinstance(current.get("freshness"), dict) else {}
    cur_epoch = current.get("authority_epoch")
    if cur_epoch:
        if epoch_key(cur_epoch) > epoch_key(candidate_epoch):
            raise FreshnessError("OUT_OF_ORDER_AUTHORITY_REGRESSION")

    cur_snapshot = cur_fresh.get("snapshot") if isinstance(cur_fresh.get("snapshot"), dict) else {}
    cur_max_raw = cur_snapshot.get("max_input_generated_at")
    if cur_max_raw:
        cur_max = parse_ts(cur_max_raw)
        new_max = parse_ts(snapshot["max_input_generated_at"])
        if new_max < cur_max:
            raise FreshnessError("OUT_OF_ORDER_INPUT_SNAPSHOT")

    if cur_snapshot.get("snapshot_id") == snapshot["snapshot_id"]:
        cur_digest = cur_fresh.get("result_digest_sha256")
        if cur_digest == digest:
            return {"action": "NO_CHANGE", "reason": "IDEMPOTENT_REPLAY", "result_digest_sha256": digest}
        raise FreshnessError("SAME_SNAPSHOT_DIFFERENT_RESULT")

    return {"action": "PUBLISH", "reason": "FRESHER_OR_DIFFERENT_BOUND_SNAPSHOT", "result_digest_sha256": digest}


def attach_freshness(candidate: dict[str, Any], snapshot: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    out = dict(candidate)
    out["authority_epoch"] = snapshot["authority"]["authority_epoch"]
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
    tmp.write_bytes(data)
    os.replace(tmp, path)


def publish(repo: Path, candidate_path: Path, output_path: Path, receipt_path: Path) -> dict[str, Any]:
    snapshot_before = build_snapshot(repo)
    try:
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FreshnessError("CANDIDATE_UNREADABLE") from exc
    if not isinstance(candidate, dict):
        raise FreshnessError("CANDIDATE_NOT_OBJECT")
    current = None
    if output_path.exists():
        try:
            parsed = json.loads(output_path.read_text(encoding="utf-8"))
            current = parsed if isinstance(parsed, dict) else None
        except Exception:
            raise FreshnessError("CURRENT_PUBLICATION_UNREADABLE")

    decision = publication_decision(candidate, snapshot_before, current)
    snapshot_after = build_snapshot(repo)
    if snapshot_after["snapshot_id"] != snapshot_before["snapshot_id"]:
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
        atomic_write(output_path, json.dumps(published, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n")
    atomic_write(receipt_path, json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n")
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
    receipt = args.receipt or (repo / "research_entity/continuity/receipts/COLLECTIVE_METRICS_FRESHNESS_LATEST.json")
    result = publish(repo, args.candidate_json, output, receipt)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
