from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

from .store import UnifiedDB

METHOD_SCHEMA_VERSION = 1
METHOD_KINDS = frozenset({
    "framework_candidate",
    "framework",
    "heuristic_candidate",
    "heuristic",
    "failure_pattern",
    "counterexample",
    "method_receipt",
})
ROUTABLE_METHOD_KINDS = frozenset({"framework", "heuristic", "failure_pattern", "counterexample"})
CANDIDATE_KINDS = frozenset({"framework_candidate", "heuristic_candidate"})
PROMOTABLE_KINDS = frozenset({"framework", "heuristic"})
VALID_STATUS = frozenset({"CANDIDATE", "PROMOTED", "DEMOTED", "RETIRED"})

_LIST_FIELDS = (
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
)

_GOAL_PATTERNS = {
    "diagnose": ("diagnose", "debug", "root cause", "investigate", "why fail", "failure"),
    "plan": ("plan", "strategy", "architect", "design", "roadmap"),
    "verify": ("verify", "validate", "test", "falsify", "check", "evidence"),
    "compare": ("compare", "versus", "tradeoff", "choose", "select"),
    "recover": ("recover", "restore", "restart", "rollback", "crash", "replay"),
    "optimize": ("optimize", "improve", "latency", "efficient", "budget", "faster"),
}
_MECHANISM_PATTERNS = {
    "concurrency": ("concurrent", "race", "collision", "simultaneous", "parallel"),
    "provenance": ("provenance", "identity", "digest", "sha", "attest", "source binding"),
    "unknown": ("unknown", "insufficient", "uncertain", "missing evidence", "not known"),
    "conflict": ("conflict", "contradict", "disagree", "counterevidence"),
    "privacy": ("privacy", "permission", "cross-session", "cross user", "access boundary"),
    "causal": ("causal", "outcome", "credit", "intervention", "effect"),
    "stateful": ("state", "persistent", "restart", "generation", "recovery", "database"),
    "retrieval": ("retrieval", "memory", "context", "entry point", "recall"),
}
_STRATEGY_PATTERN = re.compile(
    r"(?i)\b(strategy|plan|approach|diagnos|debug|investigat|hypothes|falsif|how should|how do|method)\w*\b"
)


class MethodRecordError(ValueError):
    pass


@dataclass(frozen=True)
class MethodMatch:
    memory_id: str
    kind: str
    subject: str
    score: float
    record: dict[str, Any]
    provenance: dict[str, Any]


def _norm_atom(value: Any) -> str:
    if not isinstance(value, str):
        raise MethodRecordError("signature atoms must be strings")
    atom = " ".join(value.strip().lower().split())
    if not atom or len(atom) > 160:
        raise MethodRecordError("invalid signature atom")
    return atom


def canonical_problem_signature(raw: Any) -> dict[str, list[str]]:
    if not isinstance(raw, dict) or not raw or len(raw) > 24:
        raise MethodRecordError("problem_signature must be a non-empty bounded object")
    result: dict[str, list[str]] = {}
    for key, value in raw.items():
        key = _norm_atom(key)
        values = value if isinstance(value, list) else [value]
        if not values or len(values) > 32:
            raise MethodRecordError("invalid problem_signature facet")
        result[key] = sorted({_norm_atom(v) for v in values})
    return dict(sorted(result.items()))


def infer_problem_signature(text: str, resource_refs: list[str] | None = None) -> dict[str, list[str]]:
    if not isinstance(text, str) or not text.strip():
        raise MethodRecordError("cannot infer signature from empty text")
    lowered = " ".join(text.lower().split())
    goals = sorted({name for name, needles in _GOAL_PATTERNS.items() if any(n in lowered for n in needles)})
    mechanisms = sorted({name for name, needles in _MECHANISM_PATTERNS.items() if any(n in lowered for n in needles)})
    resources = sorted({str(ref).split(":", 1)[0].lower() for ref in (resource_refs or []) if ":" in str(ref)})
    result: dict[str, list[str]] = {}
    if goals:
        result["goal"] = goals
    if mechanisms:
        result["mechanism"] = mechanisms
    if resources:
        result["resource_shape"] = resources[:12]
    if not result:
        result["goal"] = ["general_problem_solving"]
    return result


def _parse_json_object(raw: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except Exception as exc:
        raise MethodRecordError(f"invalid {label} JSON") from exc
    if not isinstance(value, dict):
        raise MethodRecordError(f"{label} must be an object")
    return value


def validate_method_record(kind: str, record: Any) -> dict[str, Any]:
    if kind not in METHOD_KINDS:
        raise MethodRecordError("unrecognized method memory kind")
    if not isinstance(record, dict):
        raise MethodRecordError("method record must be an object")

    required = {
        "problem_signature",
        "goal_shape",
        "abstraction_version",
        "support_count",
        "success_count",
        "failure_count",
        "calibration",
        "last_validated_at",
        "status",
        *_LIST_FIELDS,
    }
    missing = sorted(required.difference(record))
    if missing:
        raise MethodRecordError("missing method fields: " + ",".join(missing))

    normalized = dict(record)
    normalized["problem_signature"] = canonical_problem_signature(record["problem_signature"])
    goal_shape = record["goal_shape"]
    if isinstance(goal_shape, str):
        goal_shape = [goal_shape]
    if not isinstance(goal_shape, list) or not goal_shape or len(goal_shape) > 24:
        raise MethodRecordError("goal_shape must be a non-empty bounded list")
    normalized["goal_shape"] = sorted({_norm_atom(x) for x in goal_shape})

    for field in _LIST_FIELDS:
        value = record[field]
        if not isinstance(value, list) or len(value) > 256:
            raise MethodRecordError(f"{field} must be a bounded list")
        normalized[field] = [str(x) for x in value]

    if not isinstance(record["abstraction_version"], str) or not record["abstraction_version"].strip():
        raise MethodRecordError("invalid abstraction_version")
    normalized["abstraction_version"] = record["abstraction_version"].strip()

    for field in ("support_count", "success_count", "failure_count"):
        value = record[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise MethodRecordError(f"{field} must be a non-negative integer")
        normalized[field] = value
    if record["success_count"] + record["failure_count"] > record["support_count"]:
        raise MethodRecordError("success/failure counts exceed support_count")

    calibration = record["calibration"]
    if isinstance(calibration, bool) or not isinstance(calibration, (int, float)) or not 0.0 <= float(calibration) <= 1.0:
        raise MethodRecordError("calibration must be in [0,1]")
    normalized["calibration"] = float(calibration)

    last_validated_at = record["last_validated_at"]
    if isinstance(last_validated_at, bool) or not isinstance(last_validated_at, (int, float)) or float(last_validated_at) < 0:
        raise MethodRecordError("invalid last_validated_at")
    normalized["last_validated_at"] = float(last_validated_at)

    status = str(record["status"]).upper()
    if status not in VALID_STATUS:
        raise MethodRecordError("invalid method status")
    if kind in CANDIDATE_KINDS and status != "CANDIDATE":
        raise MethodRecordError("candidate kind requires CANDIDATE status")
    if kind in PROMOTABLE_KINDS and status == "CANDIDATE":
        raise MethodRecordError("promoted method kind cannot retain CANDIDATE status")
    if kind in PROMOTABLE_KINDS and status == "PROMOTED":
        if normalized["support_count"] < 2 or len(set(normalized["source_episode_ids"])) < 2:
            raise MethodRecordError("single-episode promotion is forbidden")
        if not normalized["falsifiers"]:
            raise MethodRecordError("promoted method requires explicit falsifier")
    normalized["status"] = status

    limits = record.get("limits_method_ids", [])
    if not isinstance(limits, list) or len(limits) > 128:
        raise MethodRecordError("limits_method_ids must be a bounded list")
    normalized["limits_method_ids"] = [str(x) for x in limits]
    normalized["method_schema_version"] = METHOD_SCHEMA_VERSION
    return normalized


def structural_score(query: dict[str, list[str]], candidate: dict[str, list[str]]) -> float:
    facets = set(query).intersection(candidate)
    if not facets:
        return 0.0
    weighted = 0.0
    total = 0.0
    for facet in sorted(set(query).union(candidate)):
        q = set(query.get(facet, []))
        c = set(candidate.get(facet, []))
        weight = 2.0 if facet in {"goal", "mechanism"} else 1.0
        total += weight
        if q and c:
            weighted += weight * (len(q.intersection(c)) / len(q.union(c)))
    return weighted / max(total, 1.0)


class MethodMemory:
    """Validated method-memory admission and deterministic Stage-B retrieval.

    This layer stores HOW-to-solve knowledge in UnifiedDB without granting factual,
    effect, privacy, or promotion authority to retrieval. Candidate memories are never
    served as active methods. PROMOTED method use remains structurally matched and
    receipt-bounded; malformed active records fail closed.
    """

    def __init__(self, db: UnifiedDB):
        self.db = db

    def _assert_refs(self, record: dict[str, Any]) -> None:
        for episode_id in set(record["source_episode_ids"]):
            if not self.db.db.execute("SELECT 1 FROM workspace_episodes WHERE episode_id=?", (episode_id,)).fetchone():
                raise MethodRecordError("unknown source_episode_id")
        for memory_id in set(record["supporting_memory_ids"] + record["counterexample_memory_ids"] + record["limits_method_ids"]):
            if not self.db.db.execute("SELECT 1 FROM durable_memory WHERE memory_id=?", (memory_id,)).fetchone():
                raise MethodRecordError("unknown referenced memory_id")

    def admit(
        self,
        *,
        kind: str,
        subject: str,
        record: dict[str, Any],
        source_turn_id: str | None,
        user_id: str | None,
        provenance: dict[str, Any],
    ) -> str:
        if not isinstance(subject, str) or not subject.strip() or len(subject) > 300:
            raise MethodRecordError("invalid method subject")
        if not isinstance(provenance, dict) or not provenance:
            raise MethodRecordError("method admission requires provenance")
        normalized = validate_method_record(kind, record)
        self._assert_refs(normalized)
        stored_provenance = dict(provenance)
        stored_provenance.update({
            "method_schema_version": METHOD_SCHEMA_VERSION,
            "admission": "method_memory:v1",
            "truth_authority": False,
            "effect_authority": False,
        })
        return self.db.add_memory(
            kind,
            subject.strip(),
            json.dumps(normalized, sort_keys=True, separators=(",", ":"), allow_nan=False),
            source_turn_id,
            user_id,
            stored_provenance,
        )

    @staticmethod
    def strategy_intent(query: str) -> bool:
        return bool(_STRATEGY_PATTERN.search(query or ""))

    def retrieve(
        self,
        *,
        query: str,
        user_id: str,
        evidence_status: str,
        resource_refs: list[str] | None = None,
        problem_signature: dict[str, list[str]] | None = None,
        limit: int = 6,
        min_score: float = 0.20,
    ) -> dict[str, Any]:
        status = str(evidence_status).upper()
        if status not in {"PRESENT", "UNDERCOVERED", "UNKNOWN"}:
            raise MethodRecordError("invalid evidence status")
        trigger = status in {"UNDERCOVERED", "UNKNOWN"} or self.strategy_intent(query)
        query_signature = canonical_problem_signature(problem_signature) if problem_signature is not None else infer_problem_signature(query, resource_refs)
        if not trigger:
            return {
                "triggered": False,
                "evidence_status": status,
                "problem_signature": query_signature,
                "methods": [],
                "counterevidence": [],
                "factual_status_unchanged": status,
            }

        rows = self.db.db.execute(
            "SELECT * FROM durable_memory WHERE kind IN ('framework','heuristic','failure_pattern','counterexample') "
            "AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 2000",
            (user_id,),
        ).fetchall()
        matches: list[MethodMatch] = []
        for row in rows:
            record = validate_method_record(str(row["kind"]), _parse_json_object(str(row["value"]), "method record"))
            if record["status"] != "PROMOTED":
                continue
            provenance = _parse_json_object(str(row["provenance"]), "method provenance")
            score = structural_score(query_signature, record["problem_signature"])
            if score <= 0.0:
                continue
            matches.append(MethodMatch(str(row["memory_id"]), str(row["kind"]), str(row["subject"]), score, record, provenance))

        limiting = [m for m in matches if m.kind in {"failure_pattern", "counterexample"}]
        methods = [m for m in matches if m.kind in {"framework", "heuristic"}]
        limited_ids = {
            target
            for limiter in limiting
            if limiter.score >= min_score
            for target in limiter.record.get("limits_method_ids", [])
        }
        methods = [m for m in methods if m.memory_id not in limited_ids and m.score >= min_score]
        methods.sort(key=lambda m: (m.score, m.record["calibration"], m.record["last_validated_at"], m.memory_id), reverse=True)
        limiting.sort(key=lambda m: (m.score, m.record["calibration"], m.memory_id), reverse=True)

        def public(match: MethodMatch) -> dict[str, Any]:
            return {
                "memory_id": match.memory_id,
                "kind": match.kind,
                "subject": match.subject,
                "structural_score": round(match.score, 6),
                "problem_signature": match.record["problem_signature"],
                "preconditions": match.record["preconditions"],
                "goal_shape": match.record["goal_shape"],
                "method_steps": match.record["method_steps"],
                "falsifiers": match.record["falsifiers"],
                "failure_modes": match.record["failure_modes"],
                "scope_limits": match.record["scope_limits"],
                "calibration": match.record["calibration"],
                "provenance": match.provenance,
                "truth_authority": False,
                "effect_authority": False,
            }

        return {
            "triggered": True,
            "evidence_status": status,
            "problem_signature": query_signature,
            "methods": [public(m) for m in methods[:limit]],
            "counterevidence": [public(m) for m in limiting[:limit]],
            "factual_status_unchanged": status,
            "generated_at": time.time(),
        }
