from __future__ import annotations

import json
import math
import os
import re
import time
import uuid
from pathlib import Path
from typing import Protocol

TIER2_EXIT_CODE = 86
TIER2_SCHEMA = "clayverse.tier2-replacement/v1"
TIER2_ACTION = "replace_pod_sandbox"
_PENDING_META_KEY = "tier2_replacement_pending"
_LAST_META_KEY = "tier2_replacement_last"
_REASON = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")


class Tier2ReplacementIntegrityError(RuntimeError):
    pass


class Tier2ReplacementPending(RuntimeError):
    def __init__(self, receipt: dict[str, object]):
        super().__init__("full pod/microVM replacement required before ingress may reopen")
        self.receipt = receipt


class _CanonicalDB(Protocol):
    db: object

    def tx(self): ...
    def entity_generation(self) -> int: ...
    def checkpoint(self, note: str) -> tuple[str, str]: ...


def _pod_uid(raw: object, *, required: bool) -> str | None:
    if raw is None:
        if required:
            raise Tier2ReplacementIntegrityError("CLAYVERSE_POD_UID is required for Tier-2 fencing")
        return None
    if not isinstance(raw, str):
        raise Tier2ReplacementIntegrityError("pod UID must be text")
    value = raw.strip()
    if not value:
        if required:
            raise Tier2ReplacementIntegrityError("CLAYVERSE_POD_UID is required for Tier-2 fencing")
        return None
    if len(value) > 160 or any(ord(ch) < 0x21 or ord(ch) > 0x7E for ch in value):
        raise Tier2ReplacementIntegrityError("pod UID has invalid shape")
    return value


def current_pod_uid(*, required: bool = False) -> str | None:
    return _pod_uid(os.environ.get("CLAYVERSE_POD_UID"), required=required)


def _reason_code(reason: object) -> str:
    if not isinstance(reason, str) or _REASON.fullmatch(reason) is None:
        raise Tier2ReplacementIntegrityError("Tier-2 reason must be a bounded machine-readable code")
    return reason


def _receipt_json(receipt: dict[str, object]) -> str:
    payload = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
    if len(payload.encode("utf-8")) > 3072:
        raise Tier2ReplacementIntegrityError("Tier-2 receipt exceeds bounded termination-message envelope")
    return payload


def _decode_receipt(raw: object) -> dict[str, object]:
    if not isinstance(raw, str) or not raw:
        raise Tier2ReplacementIntegrityError("Tier-2 pending receipt is missing")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise Tier2ReplacementIntegrityError("Tier-2 pending receipt is invalid JSON") from exc
    required = {
        "schema",
        "action",
        "request_id",
        "old_pod_uid",
        "generation",
        "reason",
        "requested_at",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise Tier2ReplacementIntegrityError("Tier-2 pending receipt has invalid fields")
    if value["schema"] != TIER2_SCHEMA or value["action"] != TIER2_ACTION:
        raise Tier2ReplacementIntegrityError("Tier-2 pending receipt has invalid protocol identity")
    try:
        uuid.UUID(str(value["request_id"]))
    except (ValueError, TypeError, AttributeError) as exc:
        raise Tier2ReplacementIntegrityError("Tier-2 request id is invalid") from exc
    _pod_uid(value["old_pod_uid"], required=True)
    generation = value["generation"]
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
        raise Tier2ReplacementIntegrityError("Tier-2 generation is invalid")
    _reason_code(value["reason"])
    requested_at = value["requested_at"]
    if isinstance(requested_at, bool) or not isinstance(requested_at, (int, float)):
        raise Tier2ReplacementIntegrityError("Tier-2 timestamp is invalid")
    if not math.isfinite(float(requested_at)) or float(requested_at) <= 0:
        raise Tier2ReplacementIntegrityError("Tier-2 timestamp is invalid")
    return value


def _meta_value(db: _CanonicalDB, key: str) -> str | None:
    row = db.db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return str(row[0]) if row else None


def _upsert_meta(tx, key: str, value: str) -> None:
    tx.execute(
        "INSERT INTO meta(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def write_termination_receipt(
    receipt: dict[str, object],
    *,
    path: str | os.PathLike[str] | None = None,
) -> None:
    target = Path(path or os.environ.get("CLAYVERSE_TIER2_TERMINATION_PATH", "/dev/termination-log"))
    payload = _receipt_json(receipt)
    with target.open("w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.write("\n")
        handle.flush()


def request_tier2_replacement(
    db: _CanonicalDB,
    reason: str,
    *,
    pod_uid: str | None = None,
    termination_path: str | os.PathLike[str] | None = None,
    now: float | None = None,
) -> dict[str, object]:
    """Persist one canonical Tier-2 request and surface it through the termination message.

    This function deliberately does not delete a Kubernetes Pod and does not require a
    Kubernetes credential. The ClayVerse container owns only the canonical recovery
    request; an external deployment orchestrator owns sandbox replacement.
    """
    uid = _pod_uid(pod_uid if pod_uid is not None else current_pod_uid(required=True), required=True)
    reason = _reason_code(reason)
    existing_raw = _meta_value(db, _PENDING_META_KEY)
    if existing_raw is not None:
        receipt = _decode_receipt(existing_raw)
        if receipt["old_pod_uid"] != uid:
            raise Tier2ReplacementIntegrityError(
                "cannot overwrite an unresolved Tier-2 request from a different Pod UID"
            )
    else:
        timestamp = time.time() if now is None else float(now)
        if not math.isfinite(timestamp) or timestamp <= 0:
            raise Tier2ReplacementIntegrityError("Tier-2 request time is invalid")
        receipt = {
            "schema": TIER2_SCHEMA,
            "action": TIER2_ACTION,
            "request_id": str(uuid.uuid4()),
            "old_pod_uid": uid,
            "generation": int(db.entity_generation()),
            "reason": reason,
            "requested_at": timestamp,
        }
        encoded = _receipt_json(receipt)
        with db.tx() as tx:
            _upsert_meta(tx, _PENDING_META_KEY, encoded)
        db.checkpoint(f"tier2-request:{receipt['request_id']}")
    write_termination_receipt(receipt, path=termination_path)
    return receipt


def reconcile_tier2_replacement(
    db: _CanonicalDB,
    *,
    pod_uid: str | None = None,
    termination_path: str | os.PathLike[str] | None = None,
    now: float | None = None,
) -> dict[str, object]:
    """Fence same-Pod restarts and admit recovery only after the Pod UID changes."""
    raw = _meta_value(db, _PENDING_META_KEY)
    if raw is None:
        return {"status": "clear", "pod_uid": current_pod_uid(required=False)}

    receipt = _decode_receipt(raw)
    uid = _pod_uid(pod_uid if pod_uid is not None else current_pod_uid(required=True), required=True)
    if uid == receipt["old_pod_uid"]:
        # Re-emit on every kubelet same-Pod container restart so the external
        # orchestrator cannot lose the Tier-2 trigger when lastState rotates.
        write_termination_receipt(receipt, path=termination_path)
        raise Tier2ReplacementPending(receipt)

    timestamp = time.time() if now is None else float(now)
    if not math.isfinite(timestamp) or timestamp <= 0:
        raise Tier2ReplacementIntegrityError("Tier-2 replacement observation time is invalid")
    resolved = {
        **receipt,
        "new_pod_uid": uid,
        "resolved_at": timestamp,
    }
    with db.tx() as tx:
        _upsert_meta(tx, _LAST_META_KEY, json.dumps(resolved, sort_keys=True, separators=(",", ":")))
        tx.execute("DELETE FROM meta WHERE key=?", (_PENDING_META_KEY,))
    db.checkpoint(f"tier2-replaced:{receipt['request_id']}")
    return {
        "status": "replacement_observed",
        "request_id": receipt["request_id"],
        "old_pod_uid": receipt["old_pod_uid"],
        "new_pod_uid": uid,
    }
