from __future__ import annotations

import json
import math
import re
import time
from typing import Any

METHOD_SCHEMA_VERSION = 1
METHOD_KINDS = {
    "framework_candidate",
    "framework",
    "heuristic_candidate",
    "heuristic",
    "failure_pattern",
    "counterexample",
    "method_receipt",
}
CANDIDATE_KINDS = {"framework_candidate", "heuristic_candidate"}
PROMOTABLE_KINDS = {"framework", "heuristic"}
NEGATIVE_METHOD_KINDS = {"failure_pattern", "counterexample"}
LIFECYCLE = {"CANDIDATE", "PROMOTED", "DEMOTED", "RETIRED"}
_SIGNATURE_KEY = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

_METHOD_FIELDS = {
    "problem_signature",
    "preconditions",
    "goal_shape",
    "method_steps",
    "invariants",
    "expected_observations",
    "falsifiers",
    "failure_modes",
    "scope_limits",
    "source_episode_ids",
    "supporting_memory_ids",
    "counterexample_memory_ids",
    "abstraction_version",
    "support_count",
    "success_count",
    "failure_count",
    "calibration",
    "last_validated_at",
    "status",
}
_RECEIPT_FIELDS = {
    "method_memory_id",
    "action",
    "source_episode_ids",
    "supporting_memory_ids",
    "counterexample_memory_ids",
    "evaluation",
    "ts",
}
_RECEIPT_ACTIONS = {"ABSTRACT", "PROMOTE", "DEMOTE", "RETIRE", "USE", "REJECT"}


class MethodMemoryValidationError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MethodMemoryValidationError("method memory must be canonical JSON") from exc


def _as_object(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            parsed = json.loads(value, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MethodMemoryValidationError("method memory value must be valid finite JSON") from exc
    else:
        parsed = value
    if not isinstance(parsed, dict):
        raise MethodMemoryValidationError("method memory value must be an object")
    _canonical_json(parsed)
    return parsed


def _str(value: Any, field: str, *, allow_empty: bool = False, max_len: int = 4096) -> str:
    if not isinstance(value, str):
        raise MethodMemoryValidationError(f"{field} must be a string")
    if not allow_empty and not value.strip():
        raise MethodMemoryValidationError(f"{field} must be non-empty")
    if len(value) > max_len:
        raise MethodMemoryValidationError(f"{field} exceeds maximum length")
    return value


def _str_list(value: Any, field: str, *, min_items: int = 0, max_items: int = 256) -> list[str]:
    if not isinstance(value, list):
        raise MethodMemoryValidationError(f"{field} must be a list")
    if len(value) < min_items or len(value) > max_items:
        raise MethodMemoryValidationError(f"{field} has invalid item count")
    result = []
    for item in value:
        result.append(_str(item, field, max_len=1024))
    if len(set(result)) != len(result):
        raise MethodMemoryValidationError(f"{field} contains duplicate identifiers/items")
    return result


def _count(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MethodMemoryValidationError(f"{field} must be a non-negative integer")
    return value


def _calibration(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MethodMemoryValidationError("calibration must be numeric")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise MethodMemoryValidationError("calibration must be finite and in [0,1]")
    return result


def _timestamp(value: Any, field: str, *, nullable: bool = False) -> float | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MethodMemoryValidationError(f"{field} must be a unix timestamp")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise MethodMemoryValidationError(f"{field} must be a positive finite unix timestamp")
    return result


def _problem_signature(value: Any) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict) or not value:
        raise MethodMemoryValidationError("problem_signature must be a non-empty object")
    if len(value) > 64:
        raise MethodMemoryValidationError("problem_signature has too many facets")
    normalized: dict[str, tuple[str, ...]] = {}
    for key, raw in value.items():
        if not isinstance(key, str) or not _SIGNATURE_KEY.fullmatch(key):
            raise MethodMemoryValidationError("problem_signature keys must be bounded snake_case identifiers")
        if isinstance(raw, str):
            items = [_str(raw, f"problem_signature.{key}", max_len=512)]
        else:
            items = _str_list(raw, f"problem_signature.{key}", min_items=1, max_items=64)
        normalized[key] = tuple(sorted(set(items)))
    return normalized


def signature_facets(record: dict[str, Any]) -> tuple[str, ...]:
    """Return deterministic structural facets for the future Stage-B baseline."""
    signature = _problem_signature(record.get("problem_signature"))
    facets = []
    for key in sorted(signature):
        normalized_values = sorted({value.strip().lower() for value in signature[key]})
        for value in normalized_values:
            facets.append(f"{key}={value}")
    return tuple(facets)


def _validate_provenance(provenance: Any, *, promoted: bool = False) -> dict[str, Any]:
    if not isinstance(provenance, dict) or not provenance:
        raise MethodMemoryValidationError("method memory provenance must be a non-empty object")
    canonical = json.loads(_canonical_json(provenance))
    if promoted:
        receipt = canonical.get("promotion_receipt_id")
        if not isinstance(receipt, str) or not receipt.strip():
            raise MethodMemoryValidationError("promoted method requires promotion_receipt_id provenance")
    return canonical


def validate_method_record(kind: str, value: Any, provenance: Any) -> dict[str, Any]:
    """Validate one method-memory record and return its canonical object form."""
    if kind not in METHOD_KINDS - {"method_receipt"}:
        raise MethodMemoryValidationError("unsupported method memory kind")
    record = _as_object(value)
    unknown = set(record) - _METHOD_FIELDS
    missing = _METHOD_FIELDS - set(record)
    if unknown:
        raise MethodMemoryValidationError(f"unknown method fields: {','.join(sorted(unknown))}")
    if missing:
        raise MethodMemoryValidationError(f"missing method fields: {','.join(sorted(missing))}")

    _problem_signature(record["problem_signature"])
    _str_list(record["preconditions"], "preconditions", min_items=1)
    _str(record["goal_shape"], "goal_shape")
    _str_list(record["method_steps"], "method_steps", min_items=1)
    _str_list(record["invariants"], "invariants", min_items=1)
    _str_list(record["expected_observations"], "expected_observations", min_items=1)
    _str_list(record["falsifiers"], "falsifiers", min_items=1)
    _str_list(record["failure_modes"], "failure_modes", min_items=1)
    _str_list(record["scope_limits"], "scope_limits", min_items=1)
    source_episode_ids = _str_list(record["source_episode_ids"], "source_episode_ids", min_items=1)
    _str_list(record["supporting_memory_ids"], "supporting_memory_ids")
    _str_list(record["counterexample_memory_ids"], "counterexample_memory_ids")
    _str(record["abstraction_version"], "abstraction_version", max_len=128)
    support_count = _count(record["support_count"], "support_count")
    success_count = _count(record["success_count"], "success_count")
    failure_count = _count(record["failure_count"], "failure_count")
    calibration = _calibration(record["calibration"])
    status = _str(record["status"], "status", max_len=32)
    if status not in LIFECYCLE:
        raise MethodMemoryValidationError("invalid method lifecycle status")
    if support_count < success_count + failure_count:
        raise MethodMemoryValidationError("support_count cannot be smaller than success_count + failure_count")

    if kind in CANDIDATE_KINDS:
        if status != "CANDIDATE":
            raise MethodMemoryValidationError("candidate kind must remain CANDIDATE")
        _timestamp(record["last_validated_at"], "last_validated_at", nullable=True)
        _validate_provenance(provenance, promoted=False)
    elif kind in PROMOTABLE_KINDS:
        if status == "CANDIDATE":
            raise MethodMemoryValidationError("promoted kind cannot use CANDIDATE status")
        _timestamp(record["last_validated_at"], "last_validated_at")
        promoted = status == "PROMOTED"
        _validate_provenance(provenance, promoted=promoted)
        if promoted:
            if support_count < 2 or success_count < 1:
                raise MethodMemoryValidationError("single success cannot promote a reusable method")
            if len(source_episode_ids) < 2:
                raise MethodMemoryValidationError("promoted method requires transfer evidence from multiple episodes")
            if calibration <= 0.0:
                raise MethodMemoryValidationError("promoted method requires non-zero calibration")
    else:
        if status == "CANDIDATE":
            raise MethodMemoryValidationError("negative method evidence cannot be CANDIDATE")
        _timestamp(record["last_validated_at"], "last_validated_at")
        _validate_provenance(provenance, promoted=False)

    return json.loads(_canonical_json(record))


def validate_method_receipt(value: Any, provenance: Any) -> dict[str, Any]:
    receipt = _as_object(value)
    unknown = set(receipt) - _RECEIPT_FIELDS
    missing = _RECEIPT_FIELDS - set(receipt)
    if unknown:
        raise MethodMemoryValidationError(f"unknown method receipt fields: {','.join(sorted(unknown))}")
    if missing:
        raise MethodMemoryValidationError(f"missing method receipt fields: {','.join(sorted(missing))}")
    _str(receipt["method_memory_id"], "method_memory_id", max_len=256)
    action = _str(receipt["action"], "action", max_len=32)
    if action not in _RECEIPT_ACTIONS:
        raise MethodMemoryValidationError("invalid method receipt action")
    _str_list(receipt["source_episode_ids"], "source_episode_ids", min_items=1)
    _str_list(receipt["supporting_memory_ids"], "supporting_memory_ids")
    _str_list(receipt["counterexample_memory_ids"], "counterexample_memory_ids")
    _str(receipt["evaluation"], "evaluation", max_len=8192)
    _timestamp(receipt["ts"], "ts")
    _validate_provenance(provenance, promoted=False)
    return json.loads(_canonical_json(receipt))


def canonical_method_value(kind: str, value: Any, provenance: Any) -> str:
    if kind == "method_receipt":
        canonical = validate_method_receipt(value, provenance)
    else:
        canonical = validate_method_record(kind, value, provenance)
    return _canonical_json(canonical)


class MethodMemoryManager:
    """Fail-closed admission/read boundary for canonical method memory in UnifiedDB."""

    def __init__(self, db):
        self.db = db

    def _write_memory(self, kind, subject, value, source_turn_id, user_id, provenance):
        writer = getattr(self.db, "_insert_method_memory", None)
        if callable(writer):
            return writer(kind, subject, value, source_turn_id, user_id, provenance)
        return self.db.add_memory(kind, subject, value, source_turn_id, user_id, provenance)

    def admit(
        self,
        kind: str,
        subject: str,
        value: Any,
        source_turn_id: str | None,
        user_id: str | None,
        provenance: dict[str, Any],
    ) -> str:
        if kind not in METHOD_KINDS:
            raise MethodMemoryValidationError("kind is not method memory")
        if kind in PROMOTABLE_KINDS:
            raise MethodMemoryValidationError(
                "framework/heuristic admission requires the dedicated promotion lifecycle transaction"
            )
        _str(subject, "subject", max_len=1024)
        canonical_provenance = _validate_provenance(provenance, promoted=False)
        canonical_provenance = {
            **canonical_provenance,
            "method_schema_version": METHOD_SCHEMA_VERSION,
        }
        canonical_value = canonical_method_value(kind, value, canonical_provenance)
        return self._write_memory(
            kind,
            subject,
            canonical_value,
            source_turn_id,
            user_id,
            canonical_provenance,
        )

    def _validate_source_evidence(self, record: dict[str, Any], user_id: str | None) -> None:
        if not isinstance(user_id, str) or not user_id:
            raise MethodMemoryValidationError("promotion requires an explicit user-bound candidate")
        source_episode_ids = list(record["source_episode_ids"])
        placeholders = ",".join("?" for _ in source_episode_ids)
        try:
            episode_rows = self.db.db.execute(
                f"SELECT w.episode_id,w.session_id,w.state,s.user_id,"
                "EXISTS(SELECT 1 FROM causal_episodes c WHERE c.episode_id=w.episode_id AND c.reentered=1) AS reentered "
                "FROM workspace_episodes w JOIN sessions s ON s.session_id=w.session_id "
                f"WHERE w.episode_id IN ({placeholders})",
                tuple(source_episode_ids),
            ).fetchall()
        except Exception as exc:
            raise MethodMemoryValidationError("promotion requires canonical workspace/causal episode authority") from exc
        found = {str(row["episode_id"]): row for row in episode_rows}
        if set(found) != set(source_episode_ids):
            raise MethodMemoryValidationError("promotion source episode evidence is incomplete")
        sessions = set()
        for episode_id in source_episode_ids:
            row = found[episode_id]
            if str(row["user_id"]) != user_id:
                raise MethodMemoryValidationError("promotion source episode crosses user boundary")
            sessions.add(str(row["session_id"]))
            if str(row["state"]) not in {"COMPLETED", "ABORTED"}:
                raise MethodMemoryValidationError("promotion source episode must be terminal")
            if not int(row["reentered"]):
                raise MethodMemoryValidationError("promotion source episode must be causally re-entered")
        if len(sessions) != 1:
            raise MethodMemoryValidationError("promotion source episodes must share one canonical user session")

        supporting_ids = list(record["supporting_memory_ids"])
        counter_ids = list(record["counterexample_memory_ids"])
        evidence_ids = supporting_ids + counter_ids
        if evidence_ids:
            placeholders = ",".join("?" for _ in evidence_ids)
            evidence_rows = self.db.db.execute(
                f"SELECT memory_id,kind,user_id FROM durable_memory WHERE memory_id IN ({placeholders})",
                tuple(evidence_ids),
            ).fetchall()
            evidence = {str(row["memory_id"]): row for row in evidence_rows}
            if set(evidence) != set(evidence_ids):
                raise MethodMemoryValidationError("promotion referenced memory evidence is incomplete")
            for memory_id in evidence_ids:
                row = evidence[memory_id]
                owner = row["user_id"]
                if owner is not None and str(owner) != user_id:
                    raise MethodMemoryValidationError("promotion referenced memory crosses user boundary")
            for memory_id in supporting_ids:
                if str(evidence[memory_id]["kind"]) in METHOD_KINDS:
                    raise MethodMemoryValidationError("promotion support cannot recursively use method memory as evidence")
            for memory_id in counter_ids:
                if str(evidence[memory_id]["kind"]) not in NEGATIVE_METHOD_KINDS:
                    raise MethodMemoryValidationError("promotion counterexample reference has wrong kind")

    def promote(
        self,
        candidate_memory_id: str,
        *,
        evaluation: str,
        provenance: dict[str, Any],
        source_turn_id: str | None = None,
    ) -> dict[str, str]:
        """Atomically promote a validated candidate from terminal causal transfer evidence."""
        _str(candidate_memory_id, "candidate_memory_id", max_len=256)
        _str(evaluation, "evaluation", max_len=8192)
        lifecycle_provenance = _validate_provenance(provenance, promoted=False)
        if not hasattr(self.db, "db") or not callable(getattr(self.db, "tx", None)):
            raise MethodMemoryValidationError("promotion requires transactional UnifiedDB access")

        with self.db.tx():
            candidate_row = self.db.db.execute(
                "SELECT * FROM durable_memory WHERE memory_id=? LIMIT 1",
                (candidate_memory_id,),
            ).fetchone()
            if candidate_row is None:
                raise MethodMemoryValidationError("promotion candidate does not exist")
            candidate = self.decode_row(candidate_row)
            if candidate["kind"] not in CANDIDATE_KINDS:
                raise MethodMemoryValidationError("promotion source must be a method candidate")
            record = candidate["value"]
            self._validate_source_evidence(record, candidate["user_id"])

            prior_receipts = self.db.db.execute(
                "SELECT * FROM durable_memory WHERE kind='method_receipt' AND subject=? ORDER BY ts",
                (candidate_memory_id,),
            ).fetchall()
            for row in prior_receipts:
                receipt = self.decode_row(row)
                if receipt["value"]["action"] == "PROMOTE":
                    raise MethodMemoryValidationError("candidate already has a promotion receipt")

            now = time.time()
            receipt_value = {
                "method_memory_id": candidate_memory_id,
                "action": "PROMOTE",
                "source_episode_ids": list(record["source_episode_ids"]),
                "supporting_memory_ids": list(record["supporting_memory_ids"]),
                "counterexample_memory_ids": list(record["counterexample_memory_ids"]),
                "evaluation": evaluation,
                "ts": now,
            }
            receipt_provenance = {
                **lifecycle_provenance,
                "promotion_source_memory_id": candidate_memory_id,
                "promotion_transaction_version": 2,
            }
            receipt_id = self.admit(
                "method_receipt",
                candidate_memory_id,
                receipt_value,
                source_turn_id if source_turn_id is not None else candidate["source_turn_id"],
                candidate["user_id"],
                receipt_provenance,
            )

            promoted_kind = "framework" if candidate["kind"] == "framework_candidate" else "heuristic"
            promoted_record = {
                **record,
                "status": "PROMOTED",
                "last_validated_at": now,
            }
            promoted_provenance = {
                **{k: v for k, v in candidate["provenance"].items() if k != "method_schema_version"},
                **lifecycle_provenance,
                "promotion_source_memory_id": candidate_memory_id,
                "promotion_receipt_id": receipt_id,
                "promotion_transaction_version": 2,
                "method_schema_version": METHOD_SCHEMA_VERSION,
            }
            promoted_value = canonical_method_value(promoted_kind, promoted_record, promoted_provenance)
            promoted_id = self._write_memory(
                promoted_kind,
                candidate["subject"],
                promoted_value,
                source_turn_id if source_turn_id is not None else candidate["source_turn_id"],
                candidate["user_id"],
                promoted_provenance,
            )
            return {
                "candidate_memory_id": candidate_memory_id,
                "receipt_memory_id": receipt_id,
                "promoted_memory_id": promoted_id,
            }

    def validate_promotion_lineage(self, row) -> bool:
        decoded = self.decode_row(row)
        if decoded["kind"] not in PROMOTABLE_KINDS or decoded["value"].get("status") != "PROMOTED":
            return True
        provenance = decoded["provenance"]
        candidate_id = provenance.get("promotion_source_memory_id")
        receipt_id = provenance.get("promotion_receipt_id")
        if not isinstance(candidate_id, str) or not candidate_id or not isinstance(receipt_id, str) or not receipt_id:
            raise MethodMemoryValidationError("promoted method lacks canonical promotion lineage")
        candidate_row = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=? LIMIT 1", (candidate_id,)
        ).fetchone()
        receipt_row = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=? AND kind='method_receipt' LIMIT 1", (receipt_id,)
        ).fetchone()
        if candidate_row is None or receipt_row is None:
            raise MethodMemoryValidationError("promoted method lineage reference is missing")
        candidate = self.decode_row(candidate_row)
        receipt = self.decode_row(receipt_row)
        expected_candidate_kind = "framework_candidate" if decoded["kind"] == "framework" else "heuristic_candidate"
        if candidate["kind"] != expected_candidate_kind:
            raise MethodMemoryValidationError("promoted method lineage candidate kind mismatch")
        if candidate["user_id"] != decoded["user_id"] or receipt["user_id"] != decoded["user_id"]:
            raise MethodMemoryValidationError("promoted method lineage crosses user boundary")
        receipt_value = receipt["value"]
        if receipt_value["action"] != "PROMOTE" or receipt_value["method_memory_id"] != candidate_id:
            raise MethodMemoryValidationError("promoted method receipt does not authorize this lineage")
        if str(receipt_row["subject"]) != candidate_id:
            raise MethodMemoryValidationError("promoted method receipt subject mismatch")
        record = decoded["value"]
        for field in ("source_episode_ids", "supporting_memory_ids", "counterexample_memory_ids"):
            if list(receipt_value[field]) != list(record[field]):
                raise MethodMemoryValidationError(f"promoted method receipt {field} mismatch")
        self._validate_source_evidence(record, decoded["user_id"])
        return True

    def decode_row(self, row) -> dict[str, Any]:
        kind = str(row["kind"])
        if kind not in METHOD_KINDS:
            raise MethodMemoryValidationError("row is not method memory")
        try:
            provenance = json.loads(row["provenance"], parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MethodMemoryValidationError("stored method provenance is invalid JSON") from exc
        if not isinstance(provenance, dict) or provenance.get("method_schema_version") != METHOD_SCHEMA_VERSION:
            raise MethodMemoryValidationError("stored method memory has unknown schema version")
        canonical_value = canonical_method_value(kind, row["value"], provenance)
        return {
            "memory_id": str(row["memory_id"]),
            "kind": kind,
            "subject": str(row["subject"]),
            "value": json.loads(canonical_value),
            "source_turn_id": row["source_turn_id"],
            "user_id": row["user_id"],
            "ts": float(row["ts"]),
            "provenance": provenance,
        }
