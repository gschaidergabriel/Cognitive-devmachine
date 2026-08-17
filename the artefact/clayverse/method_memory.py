from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any

from .memory_classes import METHOD_CANDIDATE_KINDS, METHOD_KINDS, METHOD_SERVABLE_KINDS
from .store import UnifiedDB

_WORD = re.compile(r"[\w.-]{2,}", re.UNICODE)


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
    if not isinstance(value, list) or len(value) > MethodMemory.MAX_SEQUENCE_ITEMS:
        raise MethodMemoryError(f"{field} must be a bounded list")
    if any(not isinstance(item, str) or not item.strip() or len(item) > MethodMemory.MAX_ITEM_CHARS for item in value):
        raise MethodMemoryError(f"{field} must contain bounded non-empty strings")
    if not allow_empty and not value:
        raise MethodMemoryError(f"{field} must not be empty")
    return [item.strip() for item in value]


def _normalize_signature(signature: Any) -> dict[str, tuple[str, ...]]:
    if not isinstance(signature, dict) or not signature or len(signature) > MethodMemory.MAX_SIGNATURE_KEYS:
        raise MethodMemoryError("problem_signature must be a bounded non-empty object")
    result: dict[str, tuple[str, ...]] = {}
    total_facets = 0
    for raw_key, raw_value in signature.items():
        if not isinstance(raw_key, str) or not raw_key.strip() or len(raw_key) > 80:
            raise MethodMemoryError("problem_signature keys must be bounded non-empty strings")
        key = raw_key.strip().lower()
        if isinstance(raw_value, bool):
            values = ("true" if raw_value else "false",)
        elif isinstance(raw_value, (str, int)) and not isinstance(raw_value, bool):
            value = str(raw_value).strip().lower()
            values = (value,)
        elif isinstance(raw_value, list):
            if len(raw_value) > MethodMemory.MAX_SIGNATURE_VALUES:
                raise MethodMemoryError("problem_signature list is too large")
            if any(not isinstance(item, (str, int)) or isinstance(item, bool) for item in raw_value):
                raise MethodMemoryError("problem_signature list values must be strings or integers")
            values = tuple(sorted({str(item).strip().lower() for item in raw_value if str(item).strip()}))
        else:
            raise MethodMemoryError("problem_signature values must be scalar or lists")
        if not values or any(not value or len(value) > 160 for value in values):
            raise MethodMemoryError("problem_signature facets must be bounded and non-empty")
        total_facets += len(values)
        if total_facets > MethodMemory.MAX_SIGNATURE_FACETS:
            raise MethodMemoryError("problem_signature has too many facets")
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

    The baseline never promotes candidates and never returns method content as factual
    evidence. A bounded deterministic problem signature is only a retrieval key; it is
    not a truth claim and contains no topic/entity terms from the prompt.
    """

    CONTRACT_VERSION = 1
    MIN_STRUCTURAL_SCORE = 0.34
    COUNTEREXAMPLE_BLOCK_SCORE = 0.67
    MAX_RECORD_CHARS = 32_768
    MAX_SEQUENCE_ITEMS = 64
    MAX_ITEM_CHARS = 4_096
    MAX_SIGNATURE_KEYS = 16
    MAX_SIGNATURE_VALUES = 16
    MAX_SIGNATURE_FACETS = 32

    _DIAGNOSE = frozenset({"why", "cause", "causes", "diagnose", "diagnosis", "debug", "failure", "failed", "error", "root"})
    _PLAN = frozenset({"plan", "strategy", "approach", "steps", "roadmap"})
    _INVESTIGATE = frozenset({"investigate", "investigation", "test", "verify", "falsify", "experiment", "hypothesis", "hypotheses", "check"})
    _DECIDE = frozenset({"decide", "choose", "compare", "tradeoff", "tradeoffs", "select"})

    def __init__(self, db: UnifiedDB):
        self.db = db

    @classmethod
    def derive_problem_signature(
        cls,
        *,
        query: str,
        evidence_status: str,
        resource_refs: list[str] | tuple[str, ...],
        collision_count: int,
    ) -> dict[str, Any]:
        tokens = {token.lower() for token in _WORD.findall(str(query))[:256]}
        if tokens & cls._DIAGNOSE:
            goal = "diagnose"
        elif tokens & cls._INVESTIGATE:
            goal = "investigate"
        elif tokens & cls._PLAN:
            goal = "plan"
        elif tokens & cls._DECIDE:
            goal = "decide"
        else:
            goal = "solve"
        resource_shape = sorted({str(ref).split(":", 1)[0].lower() for ref in resource_refs if str(ref).strip()})[:8]
        return {
            "goal_shape": goal,
            "evidence_state": str(evidence_status or "UNKNOWN").upper(),
            "resource_shape": resource_shape or ["none"],
            "collision_state": "present" if int(collision_count) > 0 else "absent",
        }

    @classmethod
    def should_activate(cls, *, evidence_status: str, problem_signature: dict[str, Any]) -> bool:
        status = str(evidence_status or "UNKNOWN").upper()
        goal = str(problem_signature.get("goal_shape", "solve"))
        return status in {"UNKNOWN", "UNDERCOVERED"} or goal in {"diagnose", "investigate", "plan", "decide"}

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
        if not isinstance(goal, str) or not goal.strip() or len(goal) > 160:
            raise MethodMemoryError("goal_shape must be a bounded non-empty string")
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

        status = record.get("status")
        if kind in METHOD_CANDIDATE_KINDS:
            allowed_statuses = {"CANDIDATE"}
        elif kind in {"framework", "heuristic"}:
            allowed_statuses = {"PROMOTED", "DEMOTED", "RETIRED"}
        else:
            allowed_statuses = {"PROMOTED", "RETIRED"}
        if status not in allowed_statuses:
            raise MethodMemoryError(f"{kind} has invalid lifecycle status")
        normalized["status"] = status

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
            if not isinstance(receipt, str) or not receipt.strip() or len(receipt) > 512:
                raise MethodMemoryError("promoted method requires bounded promotion_receipt_id")
            normalized["promotion_receipt_id"] = receipt.strip()
        else:
            receipt = record.get("promotion_receipt_id")
            if receipt is not None:
                if not isinstance(receipt, str) or not receipt.strip() or len(receipt) > 512:
                    raise MethodMemoryError("promotion_receipt_id must be bounded when present")
                normalized["promotion_receipt_id"] = receipt.strip()

        provenance = record.get("provenance")
        if not isinstance(provenance, dict) or not provenance:
            raise MethodMemoryError("method record requires provenance object")
        _canonical_json(provenance)
        normalized["provenance"] = provenance
        payload = _canonical_json(normalized)
        if len(payload) > MethodMemory.MAX_RECORD_CHARS:
            raise MethodMemoryError("method record exceeds canonical size bound")
        return normalized

    def admit(self, *, kind: str, name: str, record: dict[str, Any], user_id: str | None) -> str:
        if not isinstance(name, str) or not name.strip() or len(name) > 256:
            raise MethodMemoryError("method name must be bounded and non-empty")
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
        signature_hash = hashlib.sha256(_canonical_json(query_public).encode("utf-8")).hexdigest()
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
                "problem_signature_sha256": signature_hash,
                "truth_authority": False,
                "effect_authority": False,
                "structural_only": True,
            },
        }
