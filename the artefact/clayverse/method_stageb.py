from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any

from .method_memory import (
    METHOD_SCHEMA_VERSION,
    MethodMemoryManager,
    MethodMemoryValidationError,
    signature_facets,
)

QUERY_SCHEMA = "clayverse.problem_signature/v1"
QUERY_ADMISSION_VERSION = 1
_MAX_METHODS = 4
_MAX_COUNTEREVIDENCE = 4
_STRUCTURAL_TOKEN = re.compile(r"^[a-z][a-z0-9_.:-]{0,63}$")
_QUERY_FIELDS = {"schema", "problem_signature", "goal_shape", "provenance"}
_PROVENANCE_FIELDS = {
    "source",
    "turn_id",
    "episode_id",
    "causal_id",
    "generation",
    "admission_version",
}


class ProblemSignatureAdmissionError(ValueError):
    pass


@dataclass(frozen=True)
class AdmittedProblemQuery:
    problem_signature: dict[str, tuple[str, ...]]
    goal_shape: str
    provenance: dict[str, Any]

    @property
    def facets(self) -> tuple[str, ...]:
        record = {"problem_signature": {k: list(v) for k, v in self.problem_signature.items()}}
        return signature_facets(record)

    def receipt(self) -> dict[str, Any]:
        return {
            "schema": QUERY_SCHEMA,
            "admission_version": QUERY_ADMISSION_VERSION,
            "facet_count": len(self.facets),
            "goal_shape": self.goal_shape,
            "source": self.provenance["source"],
            "truth_authority": False,
            "effect_authority": False,
        }


def _structural_token(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ProblemSignatureAdmissionError(f"{field} must be a structural token")
    token = value.strip().lower()
    if not _STRUCTURAL_TOKEN.fullmatch(token):
        raise ProblemSignatureAdmissionError(
            f"{field} must be a bounded structural token, not free-form prompt text"
        )
    return token


def admit_problem_query(value: Any) -> AdmittedProblemQuery:
    """Admit an explicit structural query object.

    Raw prompt/query text is intentionally not accepted by this boundary. Signature
    derivation is a separate subsystem and must cross this validator before Stage B can
    retrieve reusable methods.
    """
    if not isinstance(value, dict):
        raise ProblemSignatureAdmissionError("problem query must be an object")
    unknown = set(value) - _QUERY_FIELDS
    missing = _QUERY_FIELDS - set(value)
    if unknown:
        raise ProblemSignatureAdmissionError(
            "unknown problem-query fields: " + ",".join(sorted(unknown))
        )
    if missing:
        raise ProblemSignatureAdmissionError(
            "missing problem-query fields: " + ",".join(sorted(missing))
        )
    if value["schema"] != QUERY_SCHEMA:
        raise ProblemSignatureAdmissionError("problem-query schema mismatch")

    raw_signature = value["problem_signature"]
    if not isinstance(raw_signature, dict) or not raw_signature or len(raw_signature) > 64:
        raise ProblemSignatureAdmissionError("problem_signature must be a bounded non-empty object")
    signature: dict[str, tuple[str, ...]] = {}
    for raw_key, raw_values in raw_signature.items():
        key = _structural_token(raw_key, "problem_signature key")
        if isinstance(raw_values, str):
            values = [raw_values]
        elif isinstance(raw_values, list):
            values = raw_values
        else:
            raise ProblemSignatureAdmissionError(
                f"problem_signature.{key} must be a token or token list"
            )
        if not values or len(values) > 64:
            raise ProblemSignatureAdmissionError(
                f"problem_signature.{key} has invalid item count"
            )
        normalized = tuple(sorted({_structural_token(item, f"problem_signature.{key}") for item in values}))
        signature[key] = normalized

    goal_shape = _structural_token(value["goal_shape"], "goal_shape")
    provenance = value["provenance"]
    if not isinstance(provenance, dict):
        raise ProblemSignatureAdmissionError("problem-query provenance must be an object")
    unknown_provenance = set(provenance) - _PROVENANCE_FIELDS
    missing_provenance = _PROVENANCE_FIELDS - set(provenance)
    if unknown_provenance:
        raise ProblemSignatureAdmissionError(
            "unknown problem-query provenance fields: " + ",".join(sorted(unknown_provenance))
        )
    if missing_provenance:
        raise ProblemSignatureAdmissionError(
            "missing problem-query provenance fields: " + ",".join(sorted(missing_provenance))
        )
    source = _structural_token(provenance["source"], "provenance.source")
    if source in {"raw_prompt", "raw_query", "lexical_prompt", "lexical_query"}:
        raise ProblemSignatureAdmissionError("raw-prompt lexical derivation is not an admitted Stage-B source")
    if provenance["admission_version"] != QUERY_ADMISSION_VERSION:
        raise ProblemSignatureAdmissionError("problem-query admission version mismatch")
    for field in ("turn_id", "episode_id", "causal_id"):
        item = provenance[field]
        if not isinstance(item, str) or not item.strip() or len(item) > 256:
            raise ProblemSignatureAdmissionError(f"provenance.{field} is invalid")
    generation = provenance["generation"]
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
        raise ProblemSignatureAdmissionError("provenance.generation is invalid")

    admitted_provenance = {
        "source": source,
        "turn_id": provenance["turn_id"],
        "episode_id": provenance["episode_id"],
        "causal_id": provenance["causal_id"],
        "generation": generation,
        "admission_version": QUERY_ADMISSION_VERSION,
    }
    return AdmittedProblemQuery(signature, goal_shape, admitted_provenance)


def _normalized_method_facets(record: dict[str, Any]) -> set[str]:
    return {facet.lower() for facet in signature_facets(record)}


def _method_score(query: AdmittedProblemQuery, record: dict[str, Any]) -> float:
    query_facets = set(query.facets)
    method_facets = _normalized_method_facets(record)
    if not query_facets or not method_facets:
        return 0.0
    overlap = len(query_facets & method_facets)
    if overlap == 0:
        return 0.0
    coverage = overlap / len(query_facets)
    precision = overlap / len(method_facets)
    method_goal = str(record.get("goal_shape", "")).strip().lower()
    goal_match = 1.0 if method_goal == query.goal_shape else 0.0
    calibration = float(record.get("calibration", 0.0))
    if not math.isfinite(calibration):
        return 0.0
    return (0.68 * coverage) + (0.12 * precision) + (0.12 * goal_match) + (0.08 * calibration)


class AdmittedMethodRetriever:
    """Stage B over validated method memory and admitted structural signatures only."""

    POLICY_MODE = "SHADOW"

    def __init__(self, db):
        self.db = db
        self.manager = MethodMemoryManager(db)

    def _rows(self, user_id: str):
        return self.db.db.execute(
            "SELECT * FROM durable_memory "
            "WHERE kind IN ('framework','heuristic','failure_pattern','counterexample') "
            "AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 1000",
            (user_id,),
        ).fetchall()

    def retrieve(
        self,
        *,
        problem_query: Any,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        fact_status: str,
    ) -> dict[str, Any]:
        admitted = admit_problem_query(problem_query)
        self.db.assert_session_owner(session_id, user_id)
        self.db.assert_live_generation(session_id, generation)
        if admitted.provenance["turn_id"] != turn_id:
            raise ProblemSignatureAdmissionError("problem-query turn identity mismatch")
        if admitted.provenance["episode_id"] != episode_id:
            raise ProblemSignatureAdmissionError("problem-query episode identity mismatch")
        if admitted.provenance["causal_id"] != causal_id:
            raise ProblemSignatureAdmissionError("problem-query causal identity mismatch")
        if int(admitted.provenance["generation"]) != int(generation):
            raise ProblemSignatureAdmissionError("problem-query generation mismatch")

        methods: list[dict[str, Any]] = []
        negatives: list[dict[str, Any]] = []
        invalid_ids: list[str] = []
        for row in self._rows(user_id):
            try:
                decoded = self.manager.decode_row(row)
            except MethodMemoryValidationError:
                invalid_ids.append(str(row["memory_id"]))
                continue
            record = decoded["value"]
            if record.get("status") != "PROMOTED":
                continue
            score = _method_score(admitted, record)
            if score <= 0.0:
                continue
            public = {
                "memory_id": decoded["memory_id"],
                "kind": decoded["kind"],
                "subject": decoded["subject"],
                "method": record,
                "method_score": score,
                "context_class": "method_context",
                "truth_authority": False,
                "effect_authority": False,
                "provenance": decoded["provenance"],
            }
            if decoded["kind"] in {"framework", "heuristic"}:
                methods.append(public)
            else:
                public["context_class"] = "counterevidence"
                negatives.append(public)

        negative_ids = {item["memory_id"] for item in negatives}
        filtered: list[dict[str, Any]] = []
        for method in methods:
            counter_ids = set(method["method"].get("counterexample_memory_ids", []))
            if counter_ids & negative_ids:
                continue
            filtered.append(method)

        filtered.sort(
            key=lambda item: (
                float(item["method_score"]),
                float(item["method"].get("calibration", 0.0)),
                item["memory_id"],
            ),
            reverse=True,
        )
        negatives.sort(key=lambda item: (float(item["method_score"]), item["memory_id"]), reverse=True)
        selected = filtered[:_MAX_METHODS]
        selected_negatives = negatives[:_MAX_COUNTEREVIDENCE]
        fact_status = str(fact_status).upper()
        return {
            "items": selected,
            "counterevidence": selected_negatives,
            "receipt": {
                "route": "method_structural_admitted",
                "policy_mode": self.POLICY_MODE,
                "schema_version": METHOD_SCHEMA_VERSION,
                "query_schema": QUERY_SCHEMA,
                "fact_status": fact_status,
                "method_status": "PRESENT" if selected else "UNKNOWN",
                "selected_count": len(selected),
                "counterevidence_count": len(selected_negatives),
                "invalid_count": len(invalid_ids),
                "fact_status_unchanged": True,
                "truth_authority": False,
                "effect_authority": False,
            },
            "query_receipt": admitted.receipt(),
        }
