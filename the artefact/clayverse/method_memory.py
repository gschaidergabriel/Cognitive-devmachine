from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .memory_classes import METHOD_CANDIDATE_KINDS, METHOD_KINDS, METHOD_SERVABLE_KINDS
from .store import UnifiedDB


class MethodMemoryError(ValueError):
    pass


_REQUIRED_SEQUENCE_FIELDS = (
    "preconditions", "method_steps", "invariants", "expected_observations",
    "falsifiers", "failure_modes", "scope_limits", "source_episode_ids",
    "supporting_memory_ids", "counterexample_memory_ids",
)
_REQUIRED_PROMOTED_FIELDS = (
    "problem_signature", "goal_shape", "abstraction_version", "support_count",
    "success_count", "failure_count", "calibration", "last_validated_at",
    "promotion_receipt_id",
)


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MethodMemoryError("method record must be canonical JSON") from exc


def _string_list(value: Any, field: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise MethodMemoryError(f"{field} must be a list of non-empty strings")
    if not allow_empty and not value:
        raise MethodMemoryError(f"{field} must not be empty")
    return [item.strip() for item in value]


def _normalize_signature(signature: Any) -> dict[str, tuple[str, ...]]:
    if not isinstance(signature, dict) or not signature:
        raise MethodMemoryError("problem_signature must be a non-empty object")
    result: dict[str, tuple[str, ...]] = {}
    for raw_key, raw_value in signature.items():
        if not isinstance(raw_key, str) or not raw_key.strip():
            raise MethodMemoryError("problem_signature keys must be non-empty strings")
        key = raw_key.strip().lower()
        if isinstance(raw_value, bool):
            values = ("true" if raw_value else "false",)
        elif isinstance(raw_value, (str, int)) and not isinstance(raw_value, bool):
            values = (str(raw_value).strip().lower(),)
        elif isinstance(raw_value, list):
            if any(not isinstance(item, (str, int)) or isinstance(item, bool) for item in raw_value):
                raise MethodMemoryError("problem_signature list values must be strings or integers")
            values = tuple(sorted({str(item).strip().lower() for item in raw_value if str(item).strip()}))
        else:
            raise MethodMemoryError("problem_signature values must be scalar or lists")
        if not values or any(not value for value in values):
            raise MethodMemoryError("problem_signature facets must not be empty")
        result[key] = values
    return dict(sorted(result.items()))


def _signature_facets(signature: dict[str, tuple[str, ...]]) -> set[str]:
    return {f"{key}={value}" for key, values in signature.items() for value in values}


def structural_similarity(left: Any, right: Any) -> float:
    a = _signature_facets(_normalize_signature(left))
    b = _signature_facets(_normalize_signature(right))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(frozen=True)
class MethodHit:
    memory_id: str
    kind: str
    name: str
    score: float
    record: dict[str, Any]
    provenance: dict[str, Any]

    def public(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "kind": self.kind,
            "name": self.name,
            "structural_score": round(self.score, 6),
            "problem_signature": self.record["problem_signature"],
            "preconditions": self.record["preconditions"],
            "goal_shape": self.record["goal_shape"],
            "method_steps": self.record["method_steps"],
            "falsifiers": self.record["falsifiers"],
            "failure_modes": self.record["failure_modes"],
            "scope_limits": self.record["scope_limits"],
            "calibration": self.record["calibration"],
            "counterexample_memory_ids": self.record["counterexample_memory_ids"],
            "provenance": self.provenance,
            "truth_authority": False,
            "effect_authority": False,
        }


class MethodMemory:
    """Validated method-memory admission and deterministic structural retrieval.

    This baseline never promotes candidates and never returns method content as
    factual evidence. Promoted frameworks/heuristics require an externally produced
    promotion receipt plus cross-instance support before they are servable.
    """

    CONTRACT_VERSION = 1
    MIN_STRUCTURAL_SCORE = 0.34
    COUNTEREXAMPLE_BLOCK_SCORE = 0.67

    def __init__(self, db: UnifiedDB):
        self.db = db

    @staticmethod
    def validate(kind: str, record: Any) -> dict[str, Any]:
        kind = str(kind)
        if kind not in METHOD_KINDS - {"method_receipt"}:
            raise MethodMemoryError("unsupported method-memory kind")
        if not isinstance(record, dict):
            raise MethodMemoryError("method record must be an object")
        normalized = dict(record)
        normalized["problem_signature"] = {
            key: list(values) if len(values) > 1 else values[0]
            for key, values in _normalize_signature(record.get("problem_signature")).items()
        }
        goal = record.get("goal_shape")
        if not isinstance(goal, str) or not goal.strip():
            raise MethodMemoryError("goal_shape must be a non-empty string")
        normalized["goal_shape"] = goal.strip().lower()
        for field in _REQUIRED_SEQUENCE_FIELDS:
            normalized[field] = _string_list(
                record.get(field), field,
                allow_empty=field not in {"method_steps", "falsifiers", "scope_limits", "source_episode_ids"},
            )
        version = record.get("abstraction_version")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise MethodMemoryError("abstraction_version must be a positive integer")
        normalized["abstraction_version"] = version
        expected_status = "CANDIDATE" if kind in METHOD_CANDIDATE_KINDS else "PROMOTED"
        if record.get("status") != expected_status:
            raise MethodMemoryError(f"{kind} requires status {expected_status}")
        normalized["status"] = expected_status
        for field in ("support_count", "success_count", "failure_count"):
            value = record.get(field, 0)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise MethodMemoryError(f"{field} must be a non-negative integer")
            normalized[field] = value
        calibration = record.get("calibration", 0.0)
        if not isinstance(calibration, (int, float)) or isinstance(calibration, bool) or not math.isfinite(float(calibration)) or not 0.0 <= float(calibration) <= 1.0:
            raise MethodMemoryError("calibration must be finite in [0,1]")
        normalized["calibration"] = float(calibration)
        last_validated = record.get("last_validated_at", 0.0)
        if not isinstance(last_validated, (int, float)) or isinstance(last_validated, bool) or not math.isfinite(float(last_validated)) or float(last_validated) < 0:
            raise MethodMemoryError("last_validated_at must be a non-negative finite number")
        normalized["last_validated_at"] = float(last_validated)

        if kind in {"framework", "heuristic"}:
            for field in _REQUIRED_PROMOTED_FIELDS:
                if field not in record:
                    raise MethodMemoryError(f"promoted method missing {field}")
            if len(set(normalized["source_episode_ids"])) < 2:
                raise MethodMemoryError("promoted method requires at least two source episodes")
            if normalized["support_count"] < 2:
                raise MethodMemoryError("promoted method requires cross-instance support")
            receipt = record.get("promotion_receipt_id")
            if not isinstance(receipt, str) or not receipt.strip():
                raise MethodMemoryError("promoted method requires promotion_receipt_id")
            normalized["promotion_receipt_id"] = receipt.strip()
        else:
            receipt = record.get("promotion_receipt_id")
            if receipt is not None:
                if not isinstance(receipt, str) or not receipt.strip():
                    raise MethodMemoryError("promotion_receipt_id must be non-empty when present")
                normalized["promotion_receipt_id"] = receipt.strip()

        provenance = record.get("provenance")
        if not isinstance(provenance, dict) or not provenance:
            raise MethodMemoryError("method record requires provenance object")
        _canonical_json(provenance)
        normalized["provenance"] = provenance
        _canonical_json(normalized)
        return normalized

    def admit(self, *, kind: str, name: str, record: dict[str, Any], user_id: str | None) -> str:
        if not isinstance(name, str) or not name.strip():
            raise MethodMemoryError("method name must be non-empty")
        normalized = self.validate(kind, record)
        payload = _canonical_json(normalized)
        provenance = {
            "source": "method_memory_admission",
            "contract_version": self.CONTRACT_VERSION,
            "record_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            "method_status": normalized["status"],
            "truth_authority": False,
            "effect_authority": False,
        }
        return self.db.add_memory(kind, name.strip(), payload, None, user_id, provenance)

    @staticmethod
    def _decode_row(row) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            record = json.loads(row["value"])
            provenance = json.loads(row["provenance"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise MethodMemoryError("malformed method row") from exc
        if not isinstance(provenance, dict):
            raise MethodMemoryError("malformed method provenance")
        return MethodMemory.validate(str(row["kind"]), record), provenance

    def retrieve(self, *, problem_signature: dict[str, Any], user_id: str, limit: int = 6) -> dict[str, Any]:
        if not isinstance(user_id, str) or not user_id:
            raise MethodMemoryError("user_id required")
        if limit < 1 or limit > 24:
            raise MethodMemoryError("invalid method retrieval limit")
        normalized_query = _normalize_signature(problem_signature)
        query_public = {k: list(v) if len(v) > 1 else v[0] for k, v in normalized_query.items()}
        placeholders = ",".join("?" for _ in METHOD_SERVABLE_KINDS)
        rows = self.db.db.execute(
            f"SELECT * FROM durable_memory WHERE kind IN ({placeholders}) "
            "AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 1000",
            (*sorted(METHOD_SERVABLE_KINDS), user_id),
        ).fetchall()
        valid: list[MethodHit] = []
        rejected = 0
        for row in rows:
            try:
                record, provenance = self._decode_row(row)
            except MethodMemoryError:
                rejected += 1
                continue
            if record["status"] != "PROMOTED":
                continue
            score = structural_similarity(query_public, record["problem_signature"])
            if score >= self.MIN_STRUCTURAL_SCORE:
                valid.append(MethodHit(str(row["memory_id"]), str(row["kind"]), str(row["subject"]), score, record, provenance))

        counterexamples = [hit for hit in valid if hit.kind in {"counterexample", "failure_pattern"}]
        methods = [hit for hit in valid if hit.kind in {"framework", "heuristic"}]
        blocked: set[str] = set()
        for method in methods:
            referenced = set(method.record.get("counterexample_memory_ids", []))
            for counter in counterexamples:
                if counter.memory_id in referenced and counter.score >= self.COUNTEREXAMPLE_BLOCK_SCORE:
                    blocked.add(method.memory_id)
                    break
        served = [hit for hit in methods if hit.memory_id not in blocked]
        served.sort(key=lambda hit: (hit.score, float(hit.record["calibration"]), hit.memory_id), reverse=True)
        counterexamples.sort(key=lambda hit: (hit.score, hit.memory_id), reverse=True)
        served = served[:limit]
        counterexamples = counterexamples[:limit]
        return {
            "problem_signature": query_public,
            "methods": [hit.public() for hit in served],
            "counterevidence": [hit.public() for hit in counterexamples],
            "receipt": {
                "status": "PRESENT" if served else "UNKNOWN",
                "candidate_count": len(rows),
                "served_count": len(served),
                "counterevidence_count": len(counterexamples),
                "blocked_count": len(blocked),
                "malformed_rejected_count": rejected,
                "truth_authority": False,
                "effect_authority": False,
                "structural_only": True,
            },
        }
