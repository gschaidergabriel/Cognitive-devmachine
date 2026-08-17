from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

METHOD_SCHEMA = "clayverse.method/v1"
METHOD_KINDS = frozenset({"framework", "heuristic"})
CANDIDATE_KINDS = frozenset({"framework_candidate", "heuristic_candidate"})
COUNTER_KINDS = frozenset({"failure_pattern", "counterexample"})
ALL_METHOD_KINDS = METHOD_KINDS | CANDIDATE_KINDS | COUNTER_KINDS

_MAX_METHODS = 4
_MAX_COUNTER = 4
_MAX_SIGNATURE_VALUES = 32
_MAX_FIELD_ITEMS = 64
_REQUIRED_PROMOTED_FIELDS = (
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
    "status",
)

_FACET_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("diagnose", ("why", "cause", "root cause", "mechanism", "diagnose", "debug", "troubleshoot",
                  "ursache", "warum", "mechanismus", "diagnose", "fehler", "debuggen")),
    ("plan", ("plan", "strategy", "approach", "roadmap", "steps", "how should", "how do",
              "strategie", "vorgehen", "fahrplan", "schritte", "wie soll", "wie kann")),
    ("compare", ("compare", "choose", "tradeoff", "versus", " vs ", "alternative",
                 "vergleichen", "wählen", "abwägen", "gegenüber")),
    ("optimize", ("optimize", "improve", "reduce", "increase", "faster", "efficient",
                  "optimieren", "verbessern", "reduzieren", "steigern", "schneller", "effizient")),
    ("generate_hypotheses", ("hypothesis", "hypotheses", "possibilities", "explanations", "brainstorm",
                             "hypothese", "hypothesen", "möglichkeiten", "erklärungen")),
    ("validate", ("test", "verify", "validate", "falsify", "experiment", "measure",
                  "testen", "prüfen", "validieren", "falsifizieren", "experiment", "messen")),
    ("unknown", ("unknown", "novel", "unfamiliar", "new problem", "not know", "uncertain",
                 "unbekannt", "neuartig", "neu", "weiß nicht", "unsicher")),
    ("conflict", ("conflict", "contradiction", "disagree", "inconsistent",
                  "konflikt", "widerspruch", "uneinig", "inkonsistent")),
    ("fail_closed", ("fail closed", "deny by default", "reject unknown", "safety gate",
                     "fail-closed", "standardmäßig verweigern", "unbekannt ablehnen")),
    ("privacy_bound", ("privacy", "private", "cross-user", "cross session", "data leak",
                       "privat", "datenschutz", "sitzungsübergreifend", "datenleck")),
    ("budget_bound", ("budget", "limit", "bounded", "token limit", "memory limit",
                      "budget", "grenze", "begrenzt", "limit")),
    ("recovery", ("restart", "recover", "resume", "crash", "replay",
                  "neustart", "wiederherstellen", "fortsetzen", "absturz", "wiederholung")),
)

_STRATEGY_MARKERS = (
    "how", "strategy", "approach", "plan", "diagnose", "debug", "investigate", "hypothesis",
    "method", "roadmap", "why", "cause", "mechanism",
    "wie", "strategie", "vorgehen", "diagnose", "untersuchen", "hypothese",
    "methode", "fahrplan", "warum", "ursache", "mechanismus",
)


def _bounded_string_list(value: Any, *, field: str, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    if len(value) > _MAX_FIELD_ITEMS:
        raise ValueError(f"{field} exceeds bound")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip() or len(item) > 2000:
            raise ValueError(f"{field} contains invalid item")
        out.append(item.strip())
    if not allow_empty and not out:
        raise ValueError(f"{field} must not be empty")
    return out


def _normalize_signature(raw: Any) -> dict[str, list[str]]:
    if not isinstance(raw, dict) or not raw:
        raise ValueError("problem_signature must be a non-empty object")
    if len(raw) > 16:
        raise ValueError("problem_signature exceeds facet bound")
    out: dict[str, list[str]] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not key.strip() or len(key) > 80:
            raise ValueError("problem_signature has invalid facet key")
        values = _bounded_string_list(value, field=f"problem_signature.{key}", allow_empty=False)
        if len(values) > _MAX_SIGNATURE_VALUES:
            raise ValueError("problem_signature facet exceeds bound")
        out[key.strip().lower()] = sorted({x.strip().lower() for x in values})
    return out


def validate_method_payload(kind: str, raw_value: str) -> dict[str, Any]:
    if kind not in ALL_METHOD_KINDS:
        raise ValueError("not a method-memory kind")
    try:
        payload = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("method memory must be canonical JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("method memory must be an object")
    if payload.get("schema") != METHOD_SCHEMA:
        raise ValueError("method memory schema mismatch")

    status = payload.get("status")
    if kind in CANDIDATE_KINDS:
        if status != "CANDIDATE":
            raise ValueError("candidate method must remain CANDIDATE")
        payload["problem_signature"] = _normalize_signature(payload.get("problem_signature"))
        return payload

    if kind in COUNTER_KINDS:
        if status not in {"PROMOTED", "CANDIDATE"}:
            raise ValueError("counterevidence status invalid")
        payload["problem_signature"] = _normalize_signature(payload.get("problem_signature"))
        payload["blocks_method_ids"] = _bounded_string_list(payload.get("blocks_method_ids", []), field="blocks_method_ids")
        return payload

    missing = [field for field in _REQUIRED_PROMOTED_FIELDS if field not in payload]
    if missing:
        raise ValueError("promoted method missing fields: " + ",".join(missing))
    if status != "PROMOTED":
        raise ValueError("servable method must be PROMOTED")
    payload["problem_signature"] = _normalize_signature(payload["problem_signature"])
    for field in (
        "preconditions", "goal_shape", "method_steps", "invariants", "expected_observations",
        "falsifiers", "failure_modes", "scope_limits", "source_episode_ids",
        "supporting_memory_ids", "counterexample_memory_ids",
    ):
        payload[field] = _bounded_string_list(
            payload[field], field=field, allow_empty=(field not in {"method_steps", "falsifiers", "source_episode_ids"})
        )
    if len(set(payload["source_episode_ids"])) < 2:
        raise ValueError("promoted method requires at least two distinct source episodes")
    if not isinstance(payload["abstraction_version"], int) or payload["abstraction_version"] < 1:
        raise ValueError("abstraction_version invalid")
    for field in ("support_count", "success_count", "failure_count"):
        if not isinstance(payload[field], int) or payload[field] < 0:
            raise ValueError(f"{field} invalid")
    if payload["support_count"] < 2:
        raise ValueError("promoted method requires support_count >= 2")
    calibration = payload["calibration"]
    if not isinstance(calibration, (int, float)) or not math.isfinite(float(calibration)):
        raise ValueError("calibration invalid")
    if not 0.0 <= float(calibration) <= 1.0:
        raise ValueError("calibration out of range")
    return payload


def derive_problem_signature(query: str) -> set[str]:
    text = f" {str(query).lower()} "
    facets: set[str] = set()
    for facet, markers in _FACET_PATTERNS:
        if any(marker in text for marker in markers):
            facets.add(facet)
    return facets


def method_triggered(query: str, fact_status: str) -> bool:
    if str(fact_status).upper() != "PRESENT":
        return True
    text = str(query).lower()
    return any(marker in text for marker in _STRATEGY_MARKERS)


def _method_facets(payload: dict[str, Any]) -> set[str]:
    sig = payload["problem_signature"]
    facets: set[str] = set()
    for key, values in sig.items():
        facets.add(key)
        facets.update(values)
    facets.update(x.lower() for x in payload.get("goal_shape", []))
    return facets


def _score(query_facets: set[str], payload: dict[str, Any]) -> float:
    if not query_facets:
        return 0.0
    method_facets = _method_facets(payload)
    overlap = len(query_facets.intersection(method_facets))
    if overlap == 0:
        return 0.0
    coverage = overlap / len(query_facets)
    precision = overlap / max(1, len(method_facets))
    calibration = float(payload.get("calibration", 0.0))
    support = min(1.0, math.log2(1 + int(payload.get("support_count", 0))) / 4.0)
    return (0.72 * coverage) + (0.12 * precision) + (0.10 * calibration) + (0.06 * support)


@dataclass(frozen=True)
class MethodContext:
    memory_id: str
    kind: str
    subject: str
    score: float
    payload: dict[str, Any]
    provenance: dict[str, Any]

    def public(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "kind": self.kind,
            "subject": self.subject,
            "context_class": "method_context",
            "method_score": self.score,
            "method": self.payload,
            "provenance": self.provenance,
            "truth_authority": False,
            "effect_authority": False,
        }


class MethodMemoryRetriever:
    """Stage-B structural method retrieval. It proposes methods, never factual truth."""

    POLICY_MODE = "SHADOW"

    def __init__(self, db):
        self.db = db

    @staticmethod
    def _provenance(raw: str) -> dict[str, Any]:
        try:
            value = json.loads(raw)
            return value if isinstance(value, dict) else {"raw_type": type(value).__name__}
        except Exception:
            return {"parse_error": True}

    def retrieve(self, *, query: str, user_id: str, fact_status: str) -> dict[str, Any]:
        triggered = method_triggered(query, fact_status)
        if not triggered:
            return {
                "triggered": False,
                "fact_status": str(fact_status).upper(),
                "method_status": "NOT_TRIGGERED",
                "items": [],
                "counterevidence": [],
                "invalid_method_ids": [],
                "policy_mode": self.POLICY_MODE,
            }

        query_facets = derive_problem_signature(query)
        rows = self.db.db.execute(
            "SELECT * FROM method_memory "
            "WHERE kind IN ('framework','heuristic','framework_candidate','heuristic_candidate',"
            "'failure_pattern','counterexample') "
            "AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 1000",
            (user_id,),
        ).fetchall()

        methods: list[MethodContext] = []
        counters: list[tuple[str, float, dict[str, Any], dict[str, Any], str]] = []
        invalid: list[str] = []
        for row in rows:
            kind = str(row["kind"])
            memory_id = str(row["memory_id"])
            try:
                payload = validate_method_payload(kind, str(row["value"]))
            except ValueError:
                invalid.append(memory_id)
                continue
            score = _score(query_facets, payload)
            if score <= 0.0:
                continue
            provenance = self._provenance(str(row["provenance"]))
            if kind in METHOD_KINDS:
                methods.append(MethodContext(memory_id, kind, str(row["subject"]), score, payload, provenance))
            elif kind in COUNTER_KINDS:
                counters.append((memory_id, score, payload, provenance, str(row["subject"])))

        blocked_ids: set[str] = set()
        for _, score, payload, _, _ in counters:
            if score > 0.0:
                blocked_ids.update(str(x) for x in payload.get("blocks_method_ids", []))
        methods = [item for item in methods if item.memory_id not in blocked_ids]
        methods.sort(key=lambda item: (item.score, float(item.payload.get("calibration", 0.0)), item.memory_id), reverse=True)
        counters.sort(key=lambda item: (item[1], item[0]), reverse=True)

        selected = methods[:_MAX_METHODS]
        counter_public = [
            {
                "memory_id": memory_id,
                "kind": "counterevidence",
                "subject": subject,
                "context_class": "counterevidence",
                "counter_score": score,
                "counter": payload,
                "provenance": provenance,
                "truth_authority": False,
                "effect_authority": False,
            }
            for memory_id, score, payload, provenance, subject in counters[:_MAX_COUNTER]
        ]
        return {
            "triggered": True,
            "fact_status": str(fact_status).upper(),
            "method_status": "PRESENT" if selected else "UNKNOWN",
            "items": [item.public() for item in selected],
            "counterevidence": counter_public,
            "invalid_method_ids": sorted(invalid)[:32],
            "policy_mode": self.POLICY_MODE,
            "query_facets": sorted(query_facets),
        }
