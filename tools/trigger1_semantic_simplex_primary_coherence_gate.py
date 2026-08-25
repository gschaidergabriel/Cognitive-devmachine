#!/usr/bin/env python3
"""Monotonic primary-axis coherence guard for Trigger-1 simplex rank metrology.

This companion does not define a second dimensionality statistic and never upgrades the
canonical calibration rank analyzer. It binds to that analyzer's exact input receipt and
can only preserve its verdict or reduce it to UNRESOLVED when the primary semantic
contrast h1 = A - .5*(N+U) is not directionally coherent across matched calibration
families. It runs no model, opens no holdout, and mints no runtime/promotion credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

INPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_CALIBRATION_ACTIVATIONS/v1"
RANK_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_RANK_ANALYSIS/v1"
OUTPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_PRIMARY_COHERENCE_GUARD/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
VERDICTS = {"ONE_DIMENSIONAL_SUPPORTED", "TWO_DIMENSIONAL_REQUIRED", "UNRESOLVED"}


def canonical_sha(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(a: list[float]) -> float:
    return math.sqrt(max(0.0, _dot(a, a)))


def _cos(a: list[float], b: list[float]) -> float | None:
    na, nb = _norm(a), _norm(b)
    if na <= 1e-12 or nb <= 1e-12:
        return None
    return _dot(a, b) / (na * nb)


def _h1(rows: dict[str, list[float]]) -> list[float]:
    a, n, u = (rows[key] for key in CLASSES)
    return [a[i] - 0.5 * (n[i] + u[i]) for i in range(len(a))]


def _group(payload: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, list[float]]], float]:
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError("INPUT_SCHEMA_INVALID")
    config = payload.get("decision_config")
    if not isinstance(config, dict):
        raise ValueError("DECISION_CONFIG_REQUIRED")
    threshold = config.get("primary_axis_min_family_cosine")
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not math.isfinite(float(threshold))
        or not 0.0 <= float(threshold) <= 1.0
    ):
        raise ValueError("PRIMARY_AXIS_MIN_FAMILY_COSINE_REQUIRED_0_TO_1")

    records = payload.get("rows")
    if not isinstance(records, list) or not records:
        raise ValueError("ROWS_REQUIRED")
    grouped: dict[str, dict[str, list[float]]] = {}
    dimension: int | None = None
    for index, row in enumerate(records):
        if not isinstance(row, dict):
            raise ValueError(f"ROW_OBJECT_REQUIRED:{index}")
        family = str(row.get("family_group_id") or "").strip()
        semantic = str(row.get("semantic_class") or "").strip().upper()
        vector = row.get("activation")
        if not family:
            raise ValueError(f"FAMILY_REQUIRED:{index}")
        if semantic not in CLASSES:
            raise ValueError(f"SEMANTIC_CLASS_INVALID:{index}")
        if not isinstance(vector, list) or not vector:
            raise ValueError(f"ACTIVATION_REQUIRED:{index}")
        parsed: list[float] = []
        for value in vector:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
            ):
                raise ValueError(f"FINITE_ACTIVATION_REQUIRED:{index}")
            parsed.append(float(value))
        if dimension is None:
            dimension = len(parsed)
        if len(parsed) != dimension:
            raise ValueError("VECTOR_DIMENSION_MISMATCH")
        slot = grouped.setdefault(family, {})
        if semantic in slot:
            raise ValueError(f"DUPLICATE_CLASS:{family}:{semantic}")
        slot[semantic] = parsed

    for family, rows in grouped.items():
        if set(rows) != set(CLASSES):
            raise ValueError(f"MATCHED_TRIPLET_REQUIRED:{family}")
    if len(grouped) < 3:
        raise ValueError("AT_LEAST_THREE_MATCHED_FAMILIES_REQUIRED")
    return sorted(grouped), grouped, float(threshold)


def adjudicate(payload: dict[str, Any], rank_result: dict[str, Any]) -> dict[str, Any]:
    families, grouped, threshold = _group(payload)
    input_sha = canonical_sha(payload)
    failures: list[str] = []
    if rank_result.get("schema") != RANK_SCHEMA:
        failures.append("RANK_SCHEMA_INVALID")
    if rank_result.get("input_sha256") != input_sha:
        failures.append("RANK_RESULT_INPUT_SHA_MISMATCH")
    prior = rank_result.get("verdict")
    if prior not in VERDICTS:
        failures.append("RANK_VERDICT_INVALID")

    h1s = {family: _h1(grouped[family]) for family in families}
    dimension = len(next(iter(h1s.values())))
    global_h1 = [
        sum(h1s[family][i] for family in families) / len(families)
        for i in range(dimension)
    ]
    if _norm(global_h1) <= 1e-12:
        failures.append("GLOBAL_PRIMARY_H1_DEGENERATE")
        rows: list[dict[str, Any]] = []
        min_cosine = None
    else:
        rows = []
        for family in families:
            cosine = _cos(h1s[family], global_h1)
            rows.append(
                {
                    "family_group_id": family,
                    "h1_norm": _norm(h1s[family]),
                    "cosine_to_full_primary_h1": cosine,
                }
            )
        cosines = [
            row["cosine_to_full_primary_h1"]
            for row in rows
            if row["cosine_to_full_primary_h1"] is not None
        ]
        min_cosine = min(cosines) if len(cosines) == len(rows) else None
        if min_cosine is None:
            failures.append("FAMILY_PRIMARY_H1_DEGENERATE")

    coherent = bool(not failures and min_cosine is not None and min_cosine >= threshold)
    final_verdict = prior if coherent else "UNRESOLVED"
    reasons: list[str] = []
    if failures:
        reasons.extend(failures)
    elif not coherent:
        reasons.append("PRIMARY_H1_CROSS_FAMILY_DIRECTION_INCOHERENT")
    elif prior == "UNRESOLVED":
        reasons.append("PRIMARY_H1_COHERENT_BUT_BASE_RANK_ANALYZER_UNRESOLVED")
    else:
        reasons.append("PRIMARY_H1_COHERENCE_PRESERVES_BASE_RANK_VERDICT")

    core = {
        "schema": OUTPUT_SCHEMA,
        "input_schema": INPUT_SCHEMA,
        "rank_schema": RANK_SCHEMA,
        "input_sha256": input_sha,
        "rank_analysis_receipt_sha256": rank_result.get("analysis_receipt_sha256"),
        "prior_verdict": prior,
        "verdict": final_verdict,
        "primary_axis_min_family_cosine_threshold": threshold,
        "min_primary_family_cosine_to_full": min_cosine,
        "family_diagnostics": rows,
        "primary_axis_coherent": coherent,
        "reasons": reasons,
        "monotonicity": "PRESERVE_OR_REDUCE_TO_UNRESOLVED_ONLY",
        "promotion_boundary": {
            "runs_model": False,
            "opens_holdout": False,
            "new_runtime_credit": 0,
            "jspace_model_runtime_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
            "training_credit": 0,
            "canonical_semantics_promotion": False,
        },
    }
    return {**core, "guard_receipt_sha256": canonical_sha(core)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--rank-result", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rank_result = json.loads(Path(args.rank_result).read_text(encoding="utf-8"))
    result = adjudicate(payload, rank_result)
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
