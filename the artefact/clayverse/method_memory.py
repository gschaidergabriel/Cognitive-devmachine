from __future__ import annotations

import hashlib
import json
import math
import re
import time
from dataclasses import dataclass
from typing import Any

from .store import UnifiedDB

METHOD_SCHEMA = "clayverse.method/v1"
METHOD_RECEIPT_SCHEMA = "clayverse.method_receipt/v1"
CANDIDATE_KINDS = frozenset({"framework_candidate", "heuristic_candidate"})
ACTIVE_METHOD_KINDS = frozenset({"framework", "heuristic"})
COUNTER_METHOD_KINDS = frozenset({"failure_pattern", "counterexample"})
METHOD_KINDS = CANDIDATE_KINDS | ACTIVE_METHOD_KINDS | COUNTER_METHOD_KINDS | frozenset({"method_receipt"})
METHOD_STATUSES = frozenset({"CANDIDATE", "PROMOTED", "DEMOTED", "RETIRED"})
PROMOTION_EVALUATION_FIELDS = frozenset({
    "held_out_episode_ids",
    "counterexample_search_performed",
    "memorization_only_rejected",
    "contamination_detected",
    "stale_state_detected",
    "privacy_leakage_detected",
    "authority_leakage_detected",
    "evaluator",
    "evaluated_at",
})
_WS = re.compile(r"\s+")


class MethodRecordError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MethodRecordError("method memory must be finite canonical JSON") from exc


def _bounded_string(value: Any, field: str, *, max_len: int = 4096, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise MethodRecordError(f"{field} must be a string")
    result = _WS.sub(" ", value.strip())
    if not allow_empty and not result:
        raise MethodRecordError(f"{field} must not be empty")
    if len(result) > max_len:
        raise MethodRecordError(f"{field} too large")
    return result


def _string_list(value: Any, field: str, *, min_items: int = 0, max_items: int = 256, item_max: int = 1024) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise MethodRecordError(f"{field} must be a list")
    if len(value) < min_items or len(value) > max_items:
        raise MethodRecordError(f"{field} item count invalid")
    result = tuple(_bounded_string(item, field, max_len=item_max) for item in value)
    if len(set(result)) != len(result):
        raise MethodRecordError(f"{field} contains duplicates")
    return result


def _finite_float(value: Any, field: str, *, minimum: float | None = None, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MethodRecordError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise MethodRecordError(f"{field} must be finite")
    if minimum is not None and result < minimum:
        raise MethodRecordError(f"{field} below minimum")
    if maximum is not None and result > maximum:
        raise MethodRecordError(f"{field} above maximum")
    return result


def _count(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 1_000_000:
        raise MethodRecordError(f"{field} must be a bounded non-negative integer")
    return value


def canonical_problem_signature(value: Any) -> dict[str, tuple[str, ...]]:
    """Validate an admitted structural signature; never derive it from free text here."""
    if not isinstance(value, dict) or not 2 <= len(value) <= 24:
        raise MethodRecordError("problem_signature requires 2..24 explicit facets")
    out: dict[str, tuple[str, ...]] = {}
    for raw_key, raw_values in value.items():
        key = _bounded_string(raw_key, "problem_signature facet", max_len=80).lower()
        if key in out:
            raise MethodRecordError("duplicate normalized problem_signature facet")
        values = _string_list(raw_values, f"problem_signature.{key}", min_items=1, max_items=16, item_max=160)
        normalized = tuple(sorted(_WS.sub(" ", item.strip().lower()) for item in values))
        if len(set(normalized)) != len(normalized):
            raise MethodRecordError(f"problem_signature.{key} contains normalized duplicates")
        out[key] = normalized
    return dict(sorted(out.items()))


def structural_similarity(query: dict[str, tuple[str, ...]], candidate: dict[str, tuple[str, ...]]) -> float:
    """Symmetric facet-aware overlap; missing/extra structure is penalized."""
    scores: list[float] = []
    for facet in sorted(set(query) | set(candidate)):
        q_values = query.get(facet)
        c_values = candidate.get(facet)
        if not q_values or not c_values:
            scores.append(0.0)
            continue
        q = set(q_values)
        c = set(c_values)
        scores.append(len(q & c) / max(1, len(q | c)))
    return sum(scores) / max(1, len(scores))


@dataclass(frozen=True)
class MethodRecord:
    memory_id: str | None
    kind: str
    name: str
    problem_signature: dict[str, tuple[str, ...]]
    preconditions: tuple[str, ...]
    goal_shape: str
    method_steps: tuple[str, ...]
    invariants: tuple[str, ...]
    expected_observations: tuple[str, ...]
    falsifiers: tuple[str, ...]
    failure_modes: tuple[str, ...]
    scope_limits: tuple[str, ...]
    source_episode_ids: tuple[str, ...]
    supporting_memory_ids: tuple[str, ...]
    counterexample_memory_ids: tuple[str, ...]
    abstraction_version: int
    support_count: int
    success_count: int
    failure_count: int
    calibration: float
    last_validated_at: float
    status: str

    def payload(self) -> dict[str, Any]:
        return {
            "schema": METHOD_SCHEMA,
            "name": self.name,
            "problem_signature": {key: list(values) for key, values in self.problem_signature.items()},
            "preconditions": list(self.preconditions),
            "goal_shape": self.goal_shape,
            "method_steps": list(self.method_steps),
            "invariants": list(self.invariants),
            "expected_observations": list(self.expected_observations),
            "falsifiers": list(self.falsifiers),
            "failure_modes": list(self.failure_modes),
            "scope_limits": list(self.scope_limits),
            "source_episode_ids": list(self.source_episode_ids),
            "supporting_memory_ids": list(self.supporting_memory_ids),
            "counterexample_memory_ids": list(self.counterexample_memory_ids),
            "abstraction_version": self.abstraction_version,
            "support_count": self.support_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "calibration": self.calibration,
            "last_validated_at": self.last_validated_at,
            "status": self.status,
        }

    def public(self, *, score: float | None = None) -> dict[str, Any]:
        result = self.payload()
        result["memory_id"] = self.memory_id
        result["truth_authority"] = False
        result["effect_authority"] = False
        if score is not None:
            result["structural_score"] = round(float(score), 6)
        return result


_REQUIRED_METHOD_FIELDS = frozenset({
    "schema", "name", "problem_signature", "preconditions", "goal_shape", "method_steps",
    "invariants", "expected_observations", "falsifiers", "failure_modes", "scope_limits",
    "source_episode_ids", "supporting_memory_ids", "counterexample_memory_ids",
    "abstraction_version", "support_count", "success_count", "failure_count", "calibration",
    "last_validated_at", "status",
})


def validate_method_record(kind: str, payload: Any, *, memory_id: str | None = None) -> MethodRecord:
    kind = _bounded_string(kind, "kind", max_len=80).lower()
    if kind not in METHOD_KINDS - {"method_receipt"}:
        raise MethodRecordError("unsupported method kind")
    if not isinstance(payload, dict):
        raise MethodRecordError("method payload must be an object")
    keys = set(payload)
    if keys != _REQUIRED_METHOD_FIELDS:
        raise MethodRecordError(
            f"method payload fields mismatch missing={sorted(_REQUIRED_METHOD_FIELDS-keys)} extra={sorted(keys-_REQUIRED_METHOD_FIELDS)}"
        )
    if payload["schema"] != METHOD_SCHEMA:
        raise MethodRecordError("unsupported method schema")

    status = _bounded_string(payload["status"], "status", max_len=20).upper()
    if status not in METHOD_STATUSES:
        raise MethodRecordError("invalid method status")
    if kind in CANDIDATE_KINDS and status != "CANDIDATE":
        raise MethodRecordError("candidate kind must remain CANDIDATE")
    if kind in ACTIVE_METHOD_KINDS | COUNTER_METHOD_KINDS and status not in {"PROMOTED", "DEMOTED", "RETIRED"}:
        raise MethodRecordError("active/counter kind requires promotion-state status")

    source_episode_ids = _string_list(payload["source_episode_ids"], "source_episode_ids", min_items=1, max_items=128, item_max=200)
    support_count = _count(payload["support_count"], "support_count")
    success_count = _count(payload["success_count"], "success_count")
    failure_count = _count(payload["failure_count"], "failure_count")
    if support_count < len(source_episode_ids):
        raise MethodRecordError("support_count smaller than source episode count")
    if success_count + failure_count > support_count:
        raise MethodRecordError("success/failure counts exceed support_count")
    if kind in ACTIVE_METHOD_KINDS and status == "PROMOTED":
        if len(source_episode_ids) < 2 or support_count < 2 or success_count < 1:
            raise MethodRecordError("single episode cannot promote reusable method")

    abstraction_version = payload["abstraction_version"]
    if isinstance(abstraction_version, bool) or not isinstance(abstraction_version, int) or not 1 <= abstraction_version <= 1_000_000:
        raise MethodRecordError("abstraction_version invalid")

    return MethodRecord(
        memory_id=memory_id,
        kind=kind,
        name=_bounded_string(payload["name"], "name", max_len=300),
        problem_signature=canonical_problem_signature(payload["problem_signature"]),
        preconditions=_string_list(payload["preconditions"], "preconditions", min_items=1, max_items=64),
        goal_shape=_bounded_string(payload["goal_shape"], "goal_shape", max_len=1000),
        method_steps=_string_list(payload["method_steps"], "method_steps", min_items=1, max_items=128),
        invariants=_string_list(payload["invariants"], "invariants", min_items=1, max_items=64),
        expected_observations=_string_list(payload["expected_observations"], "expected_observations", min_items=1, max_items=64),
        falsifiers=_string_list(payload["falsifiers"], "falsifiers", min_items=1, max_items=64),
        failure_modes=_string_list(payload["failure_modes"], "failure_modes", min_items=1, max_items=64),
        scope_limits=_string_list(payload["scope_limits"], "scope_limits", min_items=1, max_items=64),
        source_episode_ids=source_episode_ids,
        supporting_memory_ids=_string_list(payload["supporting_memory_ids"], "supporting_memory_ids", max_items=256, item_max=200),
        counterexample_memory_ids=_string_list(payload["counterexample_memory_ids"], "counterexample_memory_ids", max_items=256, item_max=200),
        abstraction_version=abstraction_version,
        support_count=support_count,
        success_count=success_count,
        failure_count=failure_count,
        calibration=_finite_float(payload["calibration"], "calibration", minimum=0.0, maximum=1.0),
        last_validated_at=_finite_float(payload["last_validated_at"], "last_validated_at", minimum=0.0),
        status=status,
    )


def _parse_json_object(raw: Any, field: str) -> dict[str, Any]:
    if isinstance(raw, dict):
        value = raw
    elif isinstance(raw, str):
        try:
            value = json.loads(raw, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
        except Exception as exc:
            raise MethodRecordError(f"{field} is invalid JSON") from exc
    else:
        raise MethodRecordError(f"{field} must be an object")
    if not isinstance(value, dict):
        raise MethodRecordError(f"{field} must be an object")
    _canonical_json(value)
    return value


def validate_promotion_evaluation(value: Any) -> dict[str, Any]:
    evaluation = _parse_json_object(value, "promotion evaluation")
    if set(evaluation) != PROMOTION_EVALUATION_FIELDS:
        raise MethodRecordError(
            f"promotion evaluation fields mismatch missing={sorted(PROMOTION_EVALUATION_FIELDS-set(evaluation))} extra={sorted(set(evaluation)-PROMOTION_EVALUATION_FIELDS)}"
        )
    held_out = _string_list(evaluation["held_out_episode_ids"], "held_out_episode_ids", min_items=1, max_items=64, item_max=200)
    safe_true = ("counterexample_search_performed", "memorization_only_rejected")
    safe_false = ("contamination_detected", "stale_state_detected", "privacy_leakage_detected", "authority_leakage_detected")
    for field in safe_true:
        if evaluation[field] is not True:
            raise MethodRecordError(f"promotion blocked: {field} must be true")
    for field in safe_false:
        if evaluation[field] is not False:
            raise MethodRecordError(f"promotion blocked: {field} must be false")
    return {
        "held_out_episode_ids": list(held_out),
        "counterexample_search_performed": True,
        "memorization_only_rejected": True,
        "contamination_detected": False,
        "stale_state_detected": False,
        "privacy_leakage_detected": False,
        "authority_leakage_detected": False,
        "evaluator": _bounded_string(evaluation["evaluator"], "evaluator", max_len=300),
        "evaluated_at": _finite_float(evaluation["evaluated_at"], "evaluated_at", minimum=1.0),
    }


def validate_method_receipt(payload: Any) -> dict[str, Any]:
    receipt = _parse_json_object(payload, "method receipt")
    if receipt.get("schema") != METHOD_RECEIPT_SCHEMA:
        raise MethodRecordError("unsupported method receipt schema")
    receipt_type = receipt.get("receipt_type")
    common = {"schema", "receipt_type", "user_id", "ts", "truth_authority", "effect_authority"}
    if receipt_type == "PROMOTION":
        expected = common | {
            "candidate_memory_id", "target_kind", "source_episode_ids", "held_out_episode_ids",
            "evaluation_sha256",
        }
        if set(receipt) != expected:
            raise MethodRecordError("promotion receipt fields mismatch")
        _bounded_string(receipt["candidate_memory_id"], "candidate_memory_id", max_len=200)
        if receipt["target_kind"] not in ACTIVE_METHOD_KINDS:
            raise MethodRecordError("promotion receipt target kind invalid")
        _string_list(receipt["source_episode_ids"], "source_episode_ids", min_items=2, max_items=128, item_max=200)
        _string_list(receipt["held_out_episode_ids"], "held_out_episode_ids", min_items=1, max_items=64, item_max=200)
        digest = _bounded_string(receipt["evaluation_sha256"], "evaluation_sha256", max_len=64)
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise MethodRecordError("evaluation_sha256 invalid")
    elif receipt_type == "USE":
        expected = common | {
            "session_id", "turn_id", "episode_id", "causal_id", "generation", "evidence_status",
            "trigger", "problem_signature_sha256", "request_identity_sha256", "selected_method_ids",
            "counterexample_memory_ids", "limit", "budget_chars", "served",
        }
        if set(receipt) != expected:
            raise MethodRecordError("method-use receipt fields mismatch")
        for field in ("session_id", "turn_id", "episode_id", "causal_id"):
            _bounded_string(receipt[field], field, max_len=300)
        _count(receipt["generation"], "generation")
        if receipt["evidence_status"] not in {"UNKNOWN", "UNDERCOVERED", "PRESENT"}:
            raise MethodRecordError("use receipt evidence_status invalid")
        if receipt["trigger"] not in {"UNKNOWN", "UNDERCOVERED", "OOD", "CONFLICT", "STRATEGY"}:
            raise MethodRecordError("use receipt trigger invalid")
        for field in ("problem_signature_sha256", "request_identity_sha256"):
            digest = _bounded_string(receipt[field], field, max_len=64)
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise MethodRecordError(f"{field} invalid")
        _string_list(receipt["selected_method_ids"], "selected_method_ids", max_items=32, item_max=200)
        _string_list(receipt["counterexample_memory_ids"], "counterexample_memory_ids", max_items=32, item_max=200)
        if not isinstance(receipt["limit"], int) or isinstance(receipt["limit"], bool) or not 1 <= receipt["limit"] <= 16:
            raise MethodRecordError("use receipt limit invalid")
        if not isinstance(receipt["budget_chars"], int) or isinstance(receipt["budget_chars"], bool) or not 256 <= receipt["budget_chars"] <= 100_000:
            raise MethodRecordError("use receipt budget invalid")
        if receipt["served"] is not False:
            raise MethodRecordError("v1 method-use receipt must remain SHADOW/not served")
    else:
        raise MethodRecordError("unknown method receipt type")
    if receipt["user_id"] not in {"gabriel", "andreas"}:
        raise MethodRecordError("method receipt user invalid")
    _finite_float(receipt["ts"], "receipt ts", minimum=1.0)
    if receipt["truth_authority"] is not False or receipt["effect_authority"] is not False:
        raise MethodRecordError("method receipt cannot carry truth/effect authority")
    return json.loads(_canonical_json(receipt))


class MethodMemoryManager:
    """Canonical method-memory admission/read/promotion boundary inside UnifiedDB."""

    def __init__(self, db: UnifiedDB):
        self.db = db

    def _episode_rows(self, episode_ids: tuple[str, ...], user_id: str) -> dict[str, Any]:
        if not episode_ids:
            raise MethodRecordError("method evidence requires source episodes")
        placeholders = ",".join("?" for _ in episode_ids)
        rows = self.db.db.execute(
            f"SELECT w.episode_id,w.session_id,w.state,"
            "EXISTS(SELECT 1 FROM causal_episodes c WHERE c.episode_id=w.episode_id AND c.reentered=1) AS reentered "
            f"FROM workspace_episodes w WHERE w.episode_id IN ({placeholders})",
            episode_ids,
        ).fetchall()
        found = {str(row["episode_id"]): row for row in rows}
        missing = sorted(set(episode_ids) - set(found))
        if missing:
            raise MethodRecordError(f"unknown source episodes: {missing}")
        wrong = sorted(
            episode_id for episode_id, row in found.items()
            if str(row["session_id"]) != f"session:{user_id}"
            or str(row["state"]) not in {"COMPLETED", "ABORTED"}
            or not int(row["reentered"])
        )
        if wrong:
            raise MethodRecordError(f"source episodes are not same-user terminal causal evidence: {wrong}")
        return found

    def _assert_references(self, record: MethodRecord, user_id: str) -> None:
        self._episode_rows(record.source_episode_ids, user_id)
        referenced = tuple(dict.fromkeys(record.supporting_memory_ids + record.counterexample_memory_ids))
        if not referenced:
            return
        placeholders = ",".join("?" for _ in referenced)
        rows = self.db.db.execute(
            f"SELECT memory_id,kind,user_id FROM durable_memory WHERE memory_id IN ({placeholders})",
            referenced,
        ).fetchall()
        by_id = {str(row["memory_id"]): row for row in rows}
        missing = sorted(set(referenced) - set(by_id))
        if missing:
            raise MethodRecordError(f"unknown referenced memories: {missing}")
        hidden = sorted(
            memory_id for memory_id, row in by_id.items()
            if row["user_id"] is not None and str(row["user_id"]) != user_id
        )
        if hidden:
            raise MethodRecordError(f"referenced memory crosses user scope: {hidden}")
        wrong_counter_kind = sorted(
            memory_id for memory_id in record.counterexample_memory_ids
            if str(by_id[memory_id]["kind"]) not in COUNTER_METHOD_KINDS
        )
        if wrong_counter_kind:
            raise MethodRecordError(f"counterexample link has wrong kind: {wrong_counter_kind}")

    def _assert_source_turn(self, source_turn_id: str | None, user_id: str) -> None:
        if source_turn_id is None:
            return
        row = self.db.db.execute("SELECT user_id FROM turns WHERE turn_id=?", (source_turn_id,)).fetchone()
        if row is None or str(row["user_id"]) != user_id:
            raise MethodRecordError("source turn missing or cross-user")

    def admit(
        self,
        *,
        kind: str,
        payload: dict[str, Any],
        source_turn_id: str | None,
        user_id: str,
        provenance: dict[str, Any],
    ) -> str:
        """Normal admission can never mint a reusable promoted framework/heuristic."""
        if user_id not in {"gabriel", "andreas"}:
            raise MethodRecordError("method admission requires canonical user scope")
        if kind in ACTIVE_METHOD_KINDS or kind == "method_receipt":
            raise MethodRecordError("active methods/receipts require dedicated lifecycle functions")
        record = validate_method_record(kind, payload)
        self._assert_references(record, user_id)
        self._assert_source_turn(source_turn_id, user_id)
        prov = _parse_json_object(provenance, "method provenance")
        forbidden = {"truth_authority", "effect_authority", "promotion_receipt_id"}.intersection(prov)
        if forbidden:
            raise MethodRecordError(f"ordinary admission cannot set authority/promotion fields: {sorted(forbidden)}")
        prov = {**prov, "method_schema": METHOD_SCHEMA, "user_scope": user_id, "truth_authority": False, "effect_authority": False}
        return self.db.add_memory(
            record.kind,
            record.name,
            _canonical_json(record.payload()),
            source_turn_id,
            user_id,
            prov,
        )

    def decode_row(self, row) -> MethodRecord:
        kind = str(row["kind"])
        if kind == "method_receipt":
            raise MethodRecordError("method receipt is not a method record")
        payload = _parse_json_object(str(row["value"]), "stored method")
        record = validate_method_record(kind, payload, memory_id=str(row["memory_id"]))
        provenance = _parse_json_object(str(row["provenance"]), "stored method provenance")
        if provenance.get("method_schema") != METHOD_SCHEMA:
            raise MethodRecordError("stored method has unknown admission schema")
        if row["user_id"] not in {"gabriel", "andreas"} or provenance.get("user_scope") != row["user_id"]:
            raise MethodRecordError("stored method user scope diverged")
        if provenance.get("truth_authority") is not False or provenance.get("effect_authority") is not False:
            raise MethodRecordError("stored method authority fields diverged")
        if record.kind in ACTIVE_METHOD_KINDS and record.status == "PROMOTED":
            receipt_id = provenance.get("promotion_receipt_id")
            if not isinstance(receipt_id, str) or not receipt_id:
                raise MethodRecordError("promoted method lacks promotion receipt")
            receipt_row = self.db.db.execute(
                "SELECT * FROM durable_memory WHERE memory_id=? AND kind='method_receipt' AND user_id=?",
                (receipt_id, row["user_id"]),
            ).fetchone()
            if receipt_row is None:
                raise MethodRecordError("promotion receipt missing")
            receipt = validate_method_receipt(str(receipt_row["value"]))
            if receipt["receipt_type"] != "PROMOTION" or receipt["target_kind"] != record.kind:
                raise MethodRecordError("promotion receipt does not authorize method kind")
        return record

    def row_by_id(self, memory_id: str, user_id: str):
        row = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=? AND user_id=?",
            (memory_id, user_id),
        ).fetchone()
        if row is None:
            raise MethodRecordError("method memory missing or outside user scope")
        return row

    def promote(
        self,
        *,
        candidate_memory_id: str,
        target_kind: str,
        promoted_payload: dict[str, Any],
        evaluation: dict[str, Any],
        user_id: str,
        provenance: dict[str, Any],
    ) -> dict[str, str]:
        """Atomically promote a candidate only after explicit held-out/safety evidence."""
        if self.db.db.in_transaction:
            raise MethodRecordError("method promotion requires an independent atomic transaction")
        if user_id not in {"gabriel", "andreas"} or target_kind not in ACTIVE_METHOD_KINDS:
            raise MethodRecordError("invalid promotion scope/target")
        candidate_row = self.row_by_id(candidate_memory_id, user_id)
        candidate = self.decode_row(candidate_row)
        expected_candidate = "framework_candidate" if target_kind == "framework" else "heuristic_candidate"
        if candidate.kind != expected_candidate or candidate.status != "CANDIDATE":
            raise MethodRecordError("promotion candidate kind/status mismatch")
        promoted = validate_method_record(target_kind, promoted_payload)
        if promoted.status != "PROMOTED":
            raise MethodRecordError("promotion target must be PROMOTED")
        self._assert_references(promoted, user_id)
        evidence = validate_promotion_evaluation(evaluation)
        held_out = tuple(evidence["held_out_episode_ids"])
        self._episode_rows(held_out, user_id)
        if set(held_out).intersection(candidate.source_episode_ids):
            raise MethodRecordError("held-out promotion evidence overlaps candidate source episodes")
        if not set(candidate.source_episode_ids).issubset(set(promoted.source_episode_ids)):
            raise MethodRecordError("promoted record dropped candidate source evidence")
        if not set(held_out).issubset(set(promoted.source_episode_ids)):
            raise MethodRecordError("promoted record omits held-out transfer episodes")
        prov = _parse_json_object(provenance, "promotion provenance")
        forbidden = {"truth_authority", "effect_authority", "promotion_receipt_id"}.intersection(prov)
        if forbidden:
            raise MethodRecordError(f"promotion caller cannot forge authority fields: {sorted(forbidden)}")
        evaluation_json = _canonical_json(evidence)
        receipt_payload = {
            "schema": METHOD_RECEIPT_SCHEMA,
            "receipt_type": "PROMOTION",
            "user_id": user_id,
            "candidate_memory_id": candidate_memory_id,
            "target_kind": target_kind,
            "source_episode_ids": list(promoted.source_episode_ids),
            "held_out_episode_ids": list(held_out),
            "evaluation_sha256": hashlib.sha256(evaluation_json.encode("utf-8")).hexdigest(),
            "ts": time.time(),
            "truth_authority": False,
            "effect_authority": False,
        }
        validate_method_receipt(receipt_payload)
        with self.db.tx():
            receipt_id = self.db.add_memory(
                "method_receipt",
                f"promotion:{candidate_memory_id}",
                _canonical_json(receipt_payload),
                candidate_row["source_turn_id"],
                user_id,
                {"method_receipt_schema": METHOD_RECEIPT_SCHEMA, "receipt_type": "PROMOTION", "evaluation": evidence},
            )
            promoted_id = self.db.add_memory(
                target_kind,
                promoted.name,
                _canonical_json(promoted.payload()),
                candidate_row["source_turn_id"],
                user_id,
                {
                    **prov,
                    "method_schema": METHOD_SCHEMA,
                    "user_scope": user_id,
                    "promotion_receipt_id": receipt_id,
                    "candidate_memory_id": candidate_memory_id,
                    "truth_authority": False,
                    "effect_authority": False,
                },
            )
        return {"candidate_memory_id": candidate_memory_id, "promotion_receipt_id": receipt_id, "promoted_memory_id": promoted_id}

    def write_use_receipt(self, payload: dict[str, Any], *, source_turn_id: str, user_id: str, subject: str) -> str:
        receipt = validate_method_receipt(payload)
        if receipt["receipt_type"] != "USE" or receipt["user_id"] != user_id or receipt["turn_id"] != source_turn_id:
            raise MethodRecordError("method-use receipt identity mismatch")
        return self.db.add_memory(
            "method_receipt",
            subject,
            _canonical_json(receipt),
            source_turn_id,
            user_id,
            {"method_receipt_schema": METHOD_RECEIPT_SCHEMA, "receipt_type": "USE", "truth_authority": False, "effect_authority": False},
        )

    def read_use_receipt(self, *, subject: str, user_id: str) -> tuple[str, dict[str, Any]] | None:
        row = self.db.db.execute(
            "SELECT memory_id,value FROM durable_memory WHERE kind='method_receipt' AND subject=? AND user_id=? ORDER BY ts LIMIT 2",
            (subject, user_id),
        ).fetchall()
        if not row:
            return None
        if len(row) != 1:
            raise MethodRecordError("duplicate method-use receipts fail closed")
        receipt = validate_method_receipt(str(row[0]["value"]))
        if receipt["receipt_type"] != "USE":
            raise MethodRecordError("method-use subject bound to wrong receipt type")
        return str(row[0]["memory_id"]), receipt
