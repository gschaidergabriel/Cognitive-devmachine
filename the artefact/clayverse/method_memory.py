from __future__ import annotations

import json
import math
import time
import uuid
from dataclasses import dataclass
from typing import Any, Iterable

from .store import UnifiedDB


METHOD_MEMORY_KINDS = frozenset({
    "framework_candidate",
    "framework",
    "heuristic_candidate",
    "heuristic",
    "failure_pattern",
    "counterexample",
    "method_receipt",
})
RETRIEVABLE_METHOD_KINDS = frozenset({
    "framework",
    "heuristic",
    "failure_pattern",
    "counterexample",
})
CANDIDATE_METHOD_KINDS = frozenset({"framework_candidate", "heuristic_candidate"})
PROMOTED_METHOD_KINDS = frozenset({"framework", "heuristic"})
METHOD_STATUSES = frozenset({"CANDIDATE", "PROMOTED", "DEMOTED", "RETIRED"})
FACT_STATUSES = frozenset({"PRESENT", "UNDERCOVERED", "UNKNOWN"})

_METHOD_FIELDS = frozenset({
    "name",
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
})
_LIST_FIELDS = frozenset({
    "problem_signature",
    "preconditions",
    "method_steps",
    "invariants",
    "expected_observations",
    "falsifiers",
    "failure_modes",
    "scope_limits",
    "source_episode_ids",
    "supporting_memory_ids",
    "counterexample_memory_ids",
})


class MethodMemoryError(ValueError):
    pass


def _text(value: Any, *, field: str, max_chars: int = 512) -> str:
    if not isinstance(value, str):
        raise MethodMemoryError(f"{field} must be a string")
    normalized = " ".join(value.strip().split())
    if not normalized or len(normalized) > max_chars:
        raise MethodMemoryError(f"invalid {field}")
    return normalized


def _items(value: Any, *, field: str, max_items: int = 64, max_chars: int = 512) -> list[str]:
    if not isinstance(value, list) or len(value) > max_items:
        raise MethodMemoryError(f"{field} must be a bounded list")
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        normalized = _text(item, field=field, max_chars=max_chars)
        if normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out


def _canonical_signature(items: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({" ".join(str(item).strip().lower().split()) for item in items if str(item).strip()}))


def validate_method_envelope(kind: str, raw: Any) -> dict[str, Any]:
    if kind not in METHOD_MEMORY_KINDS - {"method_receipt"}:
        raise MethodMemoryError("unsupported method kind")
    if not isinstance(raw, dict):
        raise MethodMemoryError("method envelope must be an object")
    if set(raw) != _METHOD_FIELDS:
        missing = sorted(_METHOD_FIELDS - set(raw))
        extra = sorted(set(raw) - _METHOD_FIELDS)
        raise MethodMemoryError(f"method envelope shape mismatch: missing={missing} extra={extra}")

    value: dict[str, Any] = {}
    value["name"] = _text(raw["name"], field="name", max_chars=256)
    value["goal_shape"] = _text(raw["goal_shape"], field="goal_shape", max_chars=256)
    for field in _LIST_FIELDS:
        value[field] = _items(raw[field], field=field)

    if not value["problem_signature"]:
        raise MethodMemoryError("problem_signature must not be empty")
    if not value["source_episode_ids"]:
        raise MethodMemoryError("source_episode_ids must not be empty")

    for field in ("abstraction_version", "support_count", "success_count", "failure_count"):
        item = raw[field]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise MethodMemoryError(f"{field} must be a non-negative integer")
        value[field] = item
    if value["abstraction_version"] < 1:
        raise MethodMemoryError("abstraction_version must be >= 1")

    calibration = raw["calibration"]
    if isinstance(calibration, bool) or not isinstance(calibration, (int, float)) or not math.isfinite(float(calibration)):
        raise MethodMemoryError("calibration must be finite")
    calibration = float(calibration)
    if not 0.0 <= calibration <= 1.0:
        raise MethodMemoryError("calibration must be within [0,1]")
    value["calibration"] = calibration

    validated_at = raw["last_validated_at"]
    if isinstance(validated_at, bool) or not isinstance(validated_at, (int, float)) or not math.isfinite(float(validated_at)) or float(validated_at) < 0.0:
        raise MethodMemoryError("last_validated_at must be a non-negative finite timestamp")
    value["last_validated_at"] = float(validated_at)

    status = raw["status"]
    if status not in METHOD_STATUSES:
        raise MethodMemoryError("invalid method status")
    value["status"] = status

    if kind in CANDIDATE_METHOD_KINDS and status != "CANDIDATE":
        raise MethodMemoryError("candidate kind requires CANDIDATE status")
    if kind in PROMOTED_METHOD_KINDS and status != "PROMOTED":
        raise MethodMemoryError("promoted kind requires PROMOTED status")
    if kind in {"failure_pattern", "counterexample"} and status not in {"PROMOTED", "DEMOTED", "RETIRED"}:
        raise MethodMemoryError("evidence limiter requires a non-candidate status")

    # A single successful episode is explicitly insufficient for promoted reusable methods.
    if kind in PROMOTED_METHOD_KINDS:
        if value["support_count"] < 2 or len(set(value["source_episode_ids"])) < 2:
            raise MethodMemoryError("promoted method requires evidence from at least two source episodes")
        if not value["falsifiers"]:
            raise MethodMemoryError("promoted method requires at least one falsifier")
        if not value["scope_limits"]:
            raise MethodMemoryError("promoted method requires explicit scope limits")

    # Preserve a stable JSON representation so malformed/non-canonical values cannot
    # become a second interpretation surface across retrieval and receipts.
    json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return value


def should_enter_stage_b(
    fact_status: str,
    *,
    strategy_request: bool = False,
    conflict: bool = False,
    out_of_distribution: bool = False,
) -> bool:
    if fact_status not in FACT_STATUSES:
        raise MethodMemoryError("invalid fact status")
    return bool(
        fact_status in {"UNKNOWN", "UNDERCOVERED"}
        or strategy_request
        or conflict
        or out_of_distribution
    )


@dataclass(frozen=True)
class MethodQuery:
    problem_signature: tuple[str, ...]
    goal_shape: str

    @classmethod
    def build(cls, *, problem_signature: Iterable[str], goal_shape: str) -> "MethodQuery":
        signature = _canonical_signature(problem_signature)
        if not signature or len(signature) > 64:
            raise MethodMemoryError("query problem_signature must be non-empty and bounded")
        goal = _text(goal_shape, field="goal_shape", max_chars=256).lower()
        return cls(signature, goal)


@dataclass(frozen=True)
class _ScoredMethod:
    memory_id: str
    kind: str
    subject: str
    envelope: dict[str, Any]
    score: float
    matched_facets: tuple[str, ...]


class MethodMemoryStore:
    """Validated UnifiedDB-backed method memory and Stage-B structural retrieval.

    This module deliberately does not infer structural signatures from raw user text.
    Signature derivation is a separate future admission problem. Here, the boundary is
    explicit: once a bounded structural signature exists, method selection is based on
    those facets rather than lexical resemblance to the surface prompt.

    Method memory remains accessibility/advice only. It never mutates factual retrieval
    status, provenance, rights, or effect authority.
    """

    ENVELOPE_VERSION = 1

    def __init__(self, db: UnifiedDB):
        self.db = db

    def _assert_refs(self, envelope: dict[str, Any]) -> None:
        episode_ids = tuple(envelope["source_episode_ids"])
        placeholders = ",".join("?" for _ in episode_ids)
        found = {
            str(row[0])
            for row in self.db.db.execute(
                f"SELECT episode_id FROM workspace_episodes WHERE episode_id IN ({placeholders})",
                episode_ids,
            ).fetchall()
        }
        missing = sorted(set(episode_ids) - found)
        if missing:
            raise MethodMemoryError(f"unknown source episodes: {missing}")

        memory_ids = tuple(dict.fromkeys(
            envelope["supporting_memory_ids"] + envelope["counterexample_memory_ids"]
        ))
        if memory_ids:
            placeholders = ",".join("?" for _ in memory_ids)
            found_memories = {
                str(row[0])
                for row in self.db.db.execute(
                    f"SELECT memory_id FROM durable_memory WHERE memory_id IN ({placeholders})",
                    memory_ids,
                ).fetchall()
            }
            missing_memories = sorted(set(memory_ids) - found_memories)
            if missing_memories:
                raise MethodMemoryError(f"unknown supporting/counterexample memories: {missing_memories}")

    def add_method(
        self,
        *,
        kind: str,
        subject: str,
        envelope: dict[str, Any],
        source_turn_id: str | None = None,
        user_id: str | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> str:
        value = validate_method_envelope(kind, envelope)
        subject = _text(subject, field="subject", max_chars=256)
        self._assert_refs(value)
        if source_turn_id is not None:
            if not self.db.db.execute("SELECT 1 FROM turns WHERE turn_id=?", (source_turn_id,)).fetchone():
                raise MethodMemoryError("unknown source_turn_id")
        if user_id is not None:
            if not self.db.db.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone():
                raise MethodMemoryError("unknown user_id")

        receipt = dict(provenance or {})
        receipt.update({
            "memory_class": "method",
            "method_envelope_version": self.ENVELOPE_VERSION,
            "truth_authority": False,
            "effect_authority": False,
        })
        memory_id = str(uuid.uuid4())
        self.db.db.execute(
            "INSERT INTO durable_memory(memory_id,kind,subject,value,source_turn_id,user_id,ts,provenance) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (
                memory_id,
                kind,
                subject,
                json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False),
                source_turn_id,
                user_id,
                time.time(),
                json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False),
            ),
        )
        return memory_id

    @staticmethod
    def _decode(row) -> dict[str, Any]:
        try:
            raw = json.loads(row["value"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise MethodMemoryError(f"malformed method memory {row['memory_id']}") from exc
        return validate_method_envelope(str(row["kind"]), raw)

    @staticmethod
    def _score(query: MethodQuery, envelope: dict[str, Any]) -> tuple[float, tuple[str, ...]]:
        query_facets = set(query.problem_signature)
        method_facets = set(_canonical_signature(envelope["problem_signature"]))
        overlap = tuple(sorted(query_facets.intersection(method_facets)))
        if not overlap:
            return 0.0, ()
        union = query_facets.union(method_facets)
        structural = len(overlap) / max(1, len(union))
        goal = 1.0 if envelope["goal_shape"].strip().lower() == query.goal_shape else 0.0
        score = (0.80 * structural) + (0.15 * goal) + (0.05 * float(envelope["calibration"]))
        return min(1.0, score), overlap

    def _matching_limiters(
        self,
        *,
        method: _ScoredMethod,
        query: MethodQuery,
        user_id: str,
    ) -> list[dict[str, Any]]:
        linked = tuple(method.envelope["counterexample_memory_ids"])
        if not linked:
            return []
        placeholders = ",".join("?" for _ in linked)
        rows = self.db.db.execute(
            f"SELECT * FROM durable_memory WHERE memory_id IN ({placeholders}) "
            "AND kind IN ('counterexample','failure_pattern') AND (user_id IS NULL OR user_id=?)",
            (*linked, user_id),
        ).fetchall()
        matched: list[dict[str, Any]] = []
        for row in rows:
            envelope = self._decode(row)
            score, facets = self._score(query, envelope)
            if score > 0.0:
                matched.append({
                    "memory_id": str(row["memory_id"]),
                    "kind": str(row["kind"]),
                    "name": envelope["name"],
                    "matched_facets": list(facets),
                    "calibration": envelope["calibration"],
                })
        return matched

    def retrieve_stage_b(
        self,
        *,
        query: MethodQuery,
        user_id: str,
        fact_status: str,
        strategy_request: bool = False,
        conflict: bool = False,
        out_of_distribution: bool = False,
        limit: int = 6,
    ) -> dict[str, Any]:
        if fact_status not in FACT_STATUSES:
            raise MethodMemoryError("invalid fact status")
        if limit < 1 or limit > 24:
            raise MethodMemoryError("invalid method retrieval limit")
        if not self.db.db.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,)).fetchone():
            raise MethodMemoryError("unknown user_id")

        entered = should_enter_stage_b(
            fact_status,
            strategy_request=strategy_request,
            conflict=conflict,
            out_of_distribution=out_of_distribution,
        )
        if not entered:
            return {
                "fact_status": fact_status,
                "method_status": "NOT_ENTERED",
                "method_context": [],
                "counterevidence": [],
                "truth_authority": False,
                "effect_authority": False,
            }

        rows = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE kind IN ('framework','heuristic') "
            "AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 2000",
            (user_id,),
        ).fetchall()
        scored: list[_ScoredMethod] = []
        for row in rows:
            envelope = self._decode(row)
            if envelope["status"] != "PROMOTED":
                continue
            score, facets = self._score(query, envelope)
            if score <= 0.0:
                continue
            scored.append(_ScoredMethod(
                memory_id=str(row["memory_id"]),
                kind=str(row["kind"]),
                subject=str(row["subject"]),
                envelope=envelope,
                score=score,
                matched_facets=facets,
            ))
        scored.sort(key=lambda item: (item.score, item.envelope["calibration"], item.memory_id), reverse=True)

        methods: list[dict[str, Any]] = []
        counterevidence: list[dict[str, Any]] = []
        for item in scored:
            limiters = self._matching_limiters(method=item, query=query, user_id=user_id)
            if limiters:
                counterevidence.extend(limiters)
                continue
            methods.append({
                "memory_id": item.memory_id,
                "kind": item.kind,
                "subject": item.subject,
                "name": item.envelope["name"],
                "problem_signature": list(item.envelope["problem_signature"]),
                "goal_shape": item.envelope["goal_shape"],
                "preconditions": list(item.envelope["preconditions"]),
                "method_steps": list(item.envelope["method_steps"]),
                "invariants": list(item.envelope["invariants"]),
                "expected_observations": list(item.envelope["expected_observations"]),
                "falsifiers": list(item.envelope["falsifiers"]),
                "failure_modes": list(item.envelope["failure_modes"]),
                "scope_limits": list(item.envelope["scope_limits"]),
                "matched_facets": list(item.matched_facets),
                "structural_score": item.score,
                "calibration": item.envelope["calibration"],
                "source_episode_ids": list(item.envelope["source_episode_ids"]),
                "supporting_memory_ids": list(item.envelope["supporting_memory_ids"]),
                "counterexample_memory_ids": list(item.envelope["counterexample_memory_ids"]),
            })
            if len(methods) >= limit:
                break

        # This invariant is intentionally explicit in the returned boundary. Method
        # availability cannot upgrade a factual UNKNOWN/UNDERCOVERED state.
        return {
            "fact_status": fact_status,
            "method_status": "PRESENT" if methods else "UNKNOWN",
            "method_context": methods,
            "counterevidence": counterevidence,
            "truth_authority": False,
            "effect_authority": False,
        }
