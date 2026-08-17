from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from .store import UnifiedDB

METHOD_SCHEMA = "clayverse.method/v1"
CANDIDATE_KINDS = frozenset({"framework_candidate", "heuristic_candidate"})
ACTIVE_METHOD_KINDS = frozenset({"framework", "heuristic"})
COUNTER_METHOD_KINDS = frozenset({"failure_pattern", "counterexample"})
METHOD_KINDS = CANDIDATE_KINDS | ACTIVE_METHOD_KINDS | COUNTER_METHOD_KINDS | frozenset({"method_receipt"})
METHOD_STATUSES = frozenset({"CANDIDATE", "PROMOTED", "DEMOTED", "RETIRED"})
STAGE_B_TRIGGERS = frozenset({"UNKNOWN", "UNDERCOVERED", "OOD", "CONFLICT", "STRATEGY"})
_ACTIVE_SERVE_STATUS = "PROMOTED"
_WS = re.compile(r"\s+")


class MethodRecordError(ValueError):
    pass


def _bounded_string(value: Any, field: str, *, max_len: int = 4096, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise MethodRecordError(f"{field} must be a string")
    normalized = _WS.sub(" ", value.strip())
    if not allow_empty and not normalized:
        raise MethodRecordError(f"{field} must not be empty")
    if len(normalized) > max_len:
        raise MethodRecordError(f"{field} too large")
    return normalized


def _string_list(value: Any, field: str, *, min_items: int = 0, max_items: int = 64, item_max: int = 1000) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise MethodRecordError(f"{field} must be a list")
    if len(value) < min_items or len(value) > max_items:
        raise MethodRecordError(f"{field} item count invalid")
    items = tuple(_bounded_string(item, field, max_len=item_max) for item in value)
    if len(set(items)) != len(items):
        raise MethodRecordError(f"{field} contains duplicates")
    return items


def canonical_problem_signature(value: Any) -> dict[str, tuple[str, ...]]:
    """Validate an explicit structural signature.

    Values are abstract structural tags/facets, not free-form query text. Stage-B matching
    operates on these explicit facets so surface lexical overlap cannot silently become
    analogical authority.
    """
    if not isinstance(value, dict):
        raise MethodRecordError("problem_signature must be an object")
    if not 2 <= len(value) <= 24:
        raise MethodRecordError("problem_signature requires 2..24 facets")
    out: dict[str, tuple[str, ...]] = {}
    for raw_key, raw_values in value.items():
        key = _bounded_string(raw_key, "problem_signature facet", max_len=80).lower()
        if key in out:
            raise MethodRecordError("duplicate normalized problem_signature facet")
        values = _string_list(raw_values, f"problem_signature.{key}", min_items=1, max_items=16, item_max=160)
        normalized = tuple(sorted({_WS.sub(" ", item.strip().lower()) for item in values}))
        if not normalized:
            raise MethodRecordError(f"problem_signature.{key} empty")
        if len(normalized) != len(values):
            raise MethodRecordError(f"problem_signature.{key} contains normalized duplicates")
        out[key] = normalized
    return dict(sorted(out.items()))


def structural_similarity(query: dict[str, tuple[str, ...]], candidate: dict[str, tuple[str, ...]]) -> float:
    """Symmetric facet-aware overlap with no free-text lexical fallback.

    Missing facets on either side count against the match. Matching values in the wrong
    facet do not count. This prevents a candidate from hiding contradictory or unrelated
    structure behind a perfect match on only the query's named facets.
    """
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
            "problem_signature": {k: list(v) for k, v in self.problem_signature.items()},
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
        result["method_authority"] = False
        result["truth_authority"] = False
        result["effect_authority"] = False
        if score is not None:
            result["structural_score"] = round(float(score), 6)
        return result


_REQUIRED_FIELDS = frozenset({
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
    if keys != _REQUIRED_FIELDS:
        missing = sorted(_REQUIRED_FIELDS - keys)
        extra = sorted(keys - _REQUIRED_FIELDS)
        raise MethodRecordError(f"method payload fields mismatch missing={missing} extra={extra}")
    if payload["schema"] != METHOD_SCHEMA:
        raise MethodRecordError("unsupported method schema")

    status = _bounded_string(payload["status"], "status", max_len=20).upper()
    if status not in METHOD_STATUSES:
        raise MethodRecordError("invalid method status")
    if kind in CANDIDATE_KINDS and status != "CANDIDATE":
        raise MethodRecordError("candidate kind must remain CANDIDATE")
    if kind in ACTIVE_METHOD_KINDS | COUNTER_METHOD_KINDS and status not in {"PROMOTED", "DEMOTED", "RETIRED"}:
        raise MethodRecordError("active/counter method kind requires terminalized promotion state")

    source_episode_ids = _string_list(payload["source_episode_ids"], "source_episode_ids", min_items=1, max_items=128, item_max=200)
    support_count = payload["support_count"]
    success_count = payload["success_count"]
    failure_count = payload["failure_count"]
    for field, value in (("support_count", support_count), ("success_count", success_count), ("failure_count", failure_count)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 1_000_000:
            raise MethodRecordError(f"{field} invalid")
    if support_count < len(source_episode_ids):
        raise MethodRecordError("support_count smaller than source episode count")
    if success_count + failure_count > support_count:
        raise MethodRecordError("success/failure counts exceed support_count")

    if kind in ACTIVE_METHOD_KINDS and status == _ACTIVE_SERVE_STATUS:
        if len(source_episode_ids) < 2 or support_count < 2:
            raise MethodRecordError("single episode cannot promote reusable method")

    calibration = payload["calibration"]
    if not isinstance(calibration, (int, float)) or isinstance(calibration, bool) or not 0.0 <= float(calibration) <= 1.0:
        raise MethodRecordError("calibration must be within [0,1]")
    last_validated_at = payload["last_validated_at"]
    if not isinstance(last_validated_at, (int, float)) or isinstance(last_validated_at, bool) or float(last_validated_at) < 0:
        raise MethodRecordError("last_validated_at invalid")
    abstraction_version = payload["abstraction_version"]
    if not isinstance(abstraction_version, int) or isinstance(abstraction_version, bool) or abstraction_version < 1 or abstraction_version > 1_000_000:
        raise MethodRecordError("abstraction_version invalid")

    return MethodRecord(
        memory_id=memory_id,
        kind=kind,
        name=_bounded_string(payload["name"], "name", max_len=300),
        problem_signature=canonical_problem_signature(payload["problem_signature"]),
        preconditions=_string_list(payload["preconditions"], "preconditions", max_items=64),
        goal_shape=_bounded_string(payload["goal_shape"], "goal_shape", max_len=1000),
        method_steps=_string_list(payload["method_steps"], "method_steps", min_items=1, max_items=128),
        invariants=_string_list(payload["invariants"], "invariants", max_items=64),
        expected_observations=_string_list(payload["expected_observations"], "expected_observations", max_items=64),
        falsifiers=_string_list(payload["falsifiers"], "falsifiers", min_items=1, max_items=64),
        failure_modes=_string_list(payload["failure_modes"], "failure_modes", max_items=64),
        scope_limits=_string_list(payload["scope_limits"], "scope_limits", min_items=1, max_items=64),
        source_episode_ids=source_episode_ids,
        supporting_memory_ids=_string_list(payload["supporting_memory_ids"], "supporting_memory_ids", max_items=256, item_max=200),
        counterexample_memory_ids=_string_list(payload["counterexample_memory_ids"], "counterexample_memory_ids", max_items=256, item_max=200),
        abstraction_version=abstraction_version,
        support_count=support_count,
        success_count=success_count,
        failure_count=failure_count,
        calibration=float(calibration),
        last_validated_at=float(last_validated_at),
        status=status,
    )


class MethodMemory:
    """Strict UnifiedDB admission plus SHADOW-only Stage-B structural retrieval.

    This intentionally does not alter MicroClay ACTIVE serving. It provides a fail-closed
    method-memory substrate and structural discriminator that can later be fused into the
    full MicroClay Stage-B policy after held-out evidence.
    """

    MIN_STRUCTURAL_SCORE = 0.50
    COUNTEREXAMPLE_BLOCK_SCORE = 0.75
    MAX_SCAN = 2000

    def __init__(self, db: UnifiedDB):
        self.db = db

    def _assert_references(self, record: MethodRecord, *, user_id: str | None) -> None:
        episode_ids = tuple(record.source_episode_ids)
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
            raise MethodRecordError(f"unknown source_episode_ids: {missing}")
        unterminated = sorted(
            episode_id for episode_id, row in found.items()
            if str(row["state"]) not in {"COMPLETED", "ABORTED"} or not int(row["reentered"])
        )
        if unterminated:
            raise MethodRecordError(
                f"source episodes are not terminal causally re-entered episodes: {unterminated}"
            )
        if user_id is not None:
            expected_session = f"session:{user_id}"
            wrong_scope = sorted(
                episode_id for episode_id, row in found.items()
                if str(row["session_id"]) != expected_session
            )
            if wrong_scope:
                raise MethodRecordError(f"source episodes cross user/session scope: {wrong_scope}")

        referenced_memory_ids = tuple(dict.fromkeys(record.supporting_memory_ids + record.counterexample_memory_ids))
        if not referenced_memory_ids:
            return
        placeholders = ",".join("?" for _ in referenced_memory_ids)
        memory_rows = self.db.db.execute(
            f"SELECT memory_id,kind,user_id FROM durable_memory WHERE memory_id IN ({placeholders})",
            referenced_memory_ids,
        ).fetchall()
        by_id = {str(row["memory_id"]): row for row in memory_rows}
        missing_memory = sorted(set(referenced_memory_ids) - set(by_id))
        if missing_memory:
            raise MethodRecordError(f"unknown supporting/counterexample memory ids: {missing_memory}")
        if user_id is not None:
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

    def admit(self, *, kind: str, payload: dict[str, Any], source_turn_id: str | None, user_id: str | None, provenance: dict[str, Any]) -> str:
        record = validate_method_record(kind, payload)
        self._assert_references(record, user_id=user_id)
        prov = dict(provenance or {})
        prov.update({
            "method_schema": METHOD_SCHEMA,
            "method_status": record.status,
            "truth_authority": False,
            "effect_authority": False,
        })
        canonical = json.dumps(record.payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        return self.db.add_memory(record.kind, record.name, canonical, source_turn_id, user_id, prov)

    @staticmethod
    def _decode_row(row) -> MethodRecord:
        try:
            payload = json.loads(str(row["value"]))
        except Exception as exc:
            raise MethodRecordError(f"invalid method JSON for {row['memory_id']}") from exc
        return validate_method_record(str(row["kind"]), payload, memory_id=str(row["memory_id"]))

    def _active_rows(self, user_id: str):
        placeholders = ",".join("?" for _ in sorted(ACTIVE_METHOD_KINDS | COUNTER_METHOD_KINDS))
        return self.db.db.execute(
            f"SELECT * FROM durable_memory WHERE kind IN ({placeholders}) "
            "AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT ?",
            (*sorted(ACTIVE_METHOD_KINDS | COUNTER_METHOD_KINDS), user_id, self.MAX_SCAN),
        ).fetchall()

    def retrieve_stage_b(
        self,
        *,
        evidence_status: str,
        problem_signature: dict[str, Any],
        user_id: str,
        trigger: str | None = None,
        limit: int = 4,
    ) -> dict[str, Any]:
        evidence_status = _bounded_string(evidence_status, "evidence_status", max_len=20).upper()
        if evidence_status not in {"PRESENT", "UNDERCOVERED", "UNKNOWN"}:
            raise ValueError("invalid evidence status")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 16:
            raise ValueError("invalid Stage-B limit")
        if trigger is None:
            trigger = evidence_status if evidence_status in {"UNKNOWN", "UNDERCOVERED"} else None
        trigger = trigger.upper() if isinstance(trigger, str) else None
        if trigger is not None and trigger not in STAGE_B_TRIGGERS:
            raise ValueError("invalid Stage-B trigger")

        signature = canonical_problem_signature(problem_signature)
        signature_bytes = json.dumps({k: list(v) for k, v in signature.items()}, sort_keys=True, separators=(",", ":")).encode()
        signature_hash = hashlib.sha256(signature_bytes).hexdigest()

        if trigger not in STAGE_B_TRIGGERS:
            return {
                "fact_status": evidence_status,
                "method_context": [],
                "counterevidence": [],
                "receipt": {
                    "mode": "SHADOW_METHOD_V1",
                    "trigger": None,
                    "problem_signature_sha256": signature_hash,
                    "truth_authority": False,
                    "effect_authority": False,
                    "served": False,
                },
            }

        methods: list[tuple[float, MethodRecord]] = []
        counters: list[tuple[float, MethodRecord]] = []
        for row in self._active_rows(user_id):
            record = self._decode_row(row)
            self._assert_references(record, user_id=user_id)
            if record.status != _ACTIVE_SERVE_STATUS:
                continue
            score = structural_similarity(signature, record.problem_signature)
            if score < self.MIN_STRUCTURAL_SCORE:
                continue
            if record.kind in ACTIVE_METHOD_KINDS:
                methods.append((score, record))
            else:
                counters.append((score, record))

        methods.sort(key=lambda item: (item[0], item[1].calibration, item[1].support_count, item[1].memory_id or ""), reverse=True)
        counters.sort(key=lambda item: (item[0], item[1].calibration, item[1].support_count, item[1].memory_id or ""), reverse=True)
        counters_by_id = {record.memory_id: (score, record) for score, record in counters}

        selected: list[tuple[float, MethodRecord]] = []
        blocking: list[tuple[float, MethodRecord]] = []
        for score, record in methods:
            linked = [counters_by_id[mid] for mid in record.counterexample_memory_ids if mid in counters_by_id]
            linked_blockers = [pair for pair in linked if pair[0] >= self.COUNTEREXAMPLE_BLOCK_SCORE]
            if linked_blockers:
                blocking.extend(linked_blockers)
                continue
            selected.append((score, record))
            if len(selected) >= limit:
                break

        all_counter = {(record.memory_id, score): record for score, record in counters[:limit]}
        for score, record in blocking:
            all_counter[(record.memory_id, score)] = record
        counter_items = [
            record.public(score=score)
            for (memory_id, score), record in sorted(
                all_counter.items(), key=lambda item: (item[0][1], item[0][0] or ""), reverse=True
            )[:limit]
        ]

        return {
            "fact_status": evidence_status,
            "method_context": [record.public(score=score) for score, record in selected],
            "counterevidence": counter_items,
            "receipt": {
                "mode": "SHADOW_METHOD_V1",
                "trigger": trigger,
                "problem_signature_sha256": signature_hash,
                "candidate_method_count": len(methods),
                "counterevidence_count": len(counters),
                "selected_count": len(selected),
                "truth_authority": False,
                "effect_authority": False,
                "served": False,
            },
        }
