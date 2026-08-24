#!/usr/bin/env python3
"""Trigger-1 intermediate-representation causal steering protocol.

Pure deterministic math/evidence layer. No model loading or network I/O.
It exists to prevent the final-norm/lm-head readout-positive-control from being
misclassified as a learned Global J-Space representation. A model executor feeds
calibration activation rows and holdout observations into this module.

Required stronger discriminator:
- vector derived only from intermediate calibration activations;
- layer/gain selected only on calibration rows;
- disjoint holdout;
- six matched controls plus explicit wrong-layer and lesion/rescue evidence;
- wrong-layer evidence must reuse the exact selected vector at a different layer;
- wrong-layer effect must be strictly weaker than the selected-layer effect; a tie is not localization evidence;
- counterbalanced label-remap holdout families so output-token identity cannot explain transfer;
- nuisance controls are scored by absolute effect magnitude, not only target-positive drift;
- matched-control families bind exact prompt/seed/label identity;
- each required control occurs exactly once per family, so contradictory duplicates cannot be resolved by list order;
- wrong-layer and lesion/rescue auxiliary evidence is bound to the canonical +VECTOR row.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "TRIGGER1_INTERMEDIATE_CONTRASTIVE_PROTOCOL/v2"
CREDIT_SCOPE = "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE_ONLY"
REQUIRED_CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)


class IntermediateProtocolError(ValueError):
    pass


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _finite(x: Any, name: str) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise IntermediateProtocolError(f"{name}:FINITE_NUMBER_REQUIRED")
    y = float(x)
    if not math.isfinite(y):
        raise IntermediateProtocolError(f"{name}:FINITE_NUMBER_REQUIRED")
    return 0.0 if y == 0.0 else y


def _vec(values: Sequence[Any], name: str) -> tuple[float, ...]:
    if isinstance(values, (str, bytes, bytearray)) or len(values) < 2:
        raise IntermediateProtocolError(f"{name}:VECTOR_DIMENSION_REQUIRED")
    return tuple(_finite(x, name) for x in values)


def _nonempty_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise IntermediateProtocolError(f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value


def _seed(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise IntermediateProtocolError("seed:INTEGER_REQUIRED")
    return value


def _family_key(row: Mapping[str, Any], *, holdout: bool) -> tuple[Any, ...]:
    case_id = _nonempty_text(row.get("case_id"), "case_id")
    prompt_sha = row.get("prompt_sha256")
    if not _sha256(prompt_sha):
        raise IntermediateProtocolError("prompt_sha256:SHA256_REQUIRED")
    seed = _seed(row.get("seed"))
    positive = _nonempty_text(row.get("positive_label"), "positive_label")
    negative = _nonempty_text(row.get("negative_label"), "negative_label")
    if positive == negative:
        raise IntermediateProtocolError("label_identity:DISTINCT_LABELS_REQUIRED")
    common = (case_id, str(prompt_sha).lower(), seed, positive, negative)
    if not holdout:
        return common
    label_map_id = _nonempty_text(row.get("label_map_id"), "label_map_id")
    return (case_id, label_map_id, str(prompt_sha).lower(), seed, positive, negative)


def _control_families(
    rows: Iterable[Mapping[str, Any]],
    *,
    holdout: bool,
) -> dict[tuple[Any, ...], dict[str, float]]:
    families: dict[tuple[Any, ...], dict[str, float]] = {}
    for row in rows:
        control = str(row.get("control"))
        if control not in REQUIRED_CONTROLS:
            continue
        key = _family_key(row, holdout=holdout)
        family = families.setdefault(key, {})
        if control in family:
            raise IntermediateProtocolError(f"DUPLICATE_CONTROL_ROW:{control}")
        family[control] = _finite(row.get("target_score"), "target_score")
    return families


def norm(v: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def normalize(v: Sequence[float]) -> tuple[float, ...]:
    n = norm(v)
    if n <= 1e-15:
        raise IntermediateProtocolError("DEGENERATE_DIRECTION")
    return tuple(x / n for x in v)


def mean(rows: Sequence[Sequence[float]]) -> tuple[float, ...]:
    if not rows:
        raise IntermediateProtocolError("NONEMPTY_ROWS_REQUIRED")
    parsed = [_vec(r, "activation") for r in rows]
    dim = len(parsed[0])
    if any(len(r) != dim for r in parsed):
        raise IntermediateProtocolError("ACTIVATION_DIMENSION_MISMATCH")
    return tuple(sum(r[i] for r in parsed) / len(parsed) for i in range(dim))


def contrastive_direction(
    positive_rows: Sequence[Sequence[float]],
    negative_rows: Sequence[Sequence[float]],
) -> tuple[float, ...]:
    p = mean(positive_rows)
    n = mean(negative_rows)
    if len(p) != len(n):
        raise IntermediateProtocolError("CONTRASTIVE_DIMENSION_MISMATCH")
    return normalize(tuple(a - b for a, b in zip(p, n)))


def orthogonal_same_norm(v: Sequence[float]) -> tuple[float, ...]:
    x = _vec(v, "primary")
    n2 = sum(a * a for a in x)
    if n2 <= 1e-15:
        raise IntermediateProtocolError("NONZERO_PRIMARY_REQUIRED")
    axis = min(range(len(x)), key=lambda i: (abs(x[i]), i))
    proj = x[axis] / n2
    y = [-proj * a for a in x]
    y[axis] += 1.0
    return tuple(a * (norm(x) / norm(y)) for a in y)


def control_vectors(direction: Sequence[float], gain: float) -> dict[str, tuple[float, ...]]:
    unit = normalize(_vec(direction, "direction"))
    g = _finite(gain, "gain")
    if g <= 0:
        raise IntermediateProtocolError("POSITIVE_GAIN_REQUIRED")
    plus = tuple(g * x for x in unit)
    perm = tuple(plus[1:]) + (plus[0],)
    if perm == plus:
        raise IntermediateProtocolError("PERMUTED_CONTROL_NOT_DISTINCT")
    return {
        "BASELINE": tuple(0.0 for _ in plus),
        "+VECTOR": plus,
        "SIGN_FLIP": tuple(-x for x in plus),
        "NULL_VECTOR": tuple(0.0 for _ in plus),
        "ORTHOGONAL_SAME_NORM": orthogonal_same_norm(plus),
        "PERMUTED_SAME_NORM": perm,
    }


def lesion(hidden: Sequence[float], direction: Sequence[float]) -> tuple[float, ...]:
    h = _vec(hidden, "hidden")
    d = normalize(_vec(direction, "direction"))
    if len(h) != len(d):
        raise IntermediateProtocolError("LESION_DIMENSION_MISMATCH")
    projection = sum(a * b for a, b in zip(h, d))
    return tuple(a - projection * b for a, b in zip(h, d))


def rescue(hidden: Sequence[float], direction: Sequence[float], gain: float) -> tuple[float, ...]:
    base = lesion(hidden, direction)
    d = normalize(direction)
    g = _finite(gain, "gain")
    return tuple(a + g * b for a, b in zip(base, d))


def _calibration_rows(rows: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    out = list(rows)
    if not out or any(r.get("split") != "calibration" for r in out):
        raise IntermediateProtocolError("CALIBRATION_ONLY_ROWS_REQUIRED")
    return out


def select_layer_gain(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Choose layer/gain only from complete, uniquely keyed calibration control families."""
    xs = _calibration_rows(rows)
    combos = sorted({(int(r["layer"]), float(r["gain"])) for r in xs})
    ranked = []
    for layer, gain in combos:
        subset = [
            r for r in xs
            if int(r["layer"]) == layer and float(r["gain"]) == gain
        ]
        by_case = _control_families(subset, holdout=False)
        margins = []
        for vals in by_case.values():
            if not all(k in vals for k in REQUIRED_CONTROLS):
                continue
            directional = min(
                vals["+VECTOR"] - vals["BASELINE"],
                vals["BASELINE"] - vals["SIGN_FLIP"],
            )
            nuisance = max(
                abs(vals["ORTHOGONAL_SAME_NORM"] - vals["BASELINE"]),
                abs(vals["PERMUTED_SAME_NORM"] - vals["BASELINE"]),
                abs(vals["NULL_VECTOR"] - vals["BASELINE"]),
            )
            margins.append(directional - nuisance)
        if margins:
            ranked.append((min(margins), sum(margins) / len(margins), layer, gain))
    ranked.sort(reverse=True)
    if not ranked or ranked[0][0] <= 0:
        return {"selected": False, "reason": "NO_POSITIVE_CALIBRATION_MARGIN"}
    worst, avg, layer, gain = ranked[0]
    return {
        "selected": True,
        "layer": layer,
        "gain": gain,
        "worst_margin": worst,
        "mean_margin": avg,
        "selection_sha256": digest(ranked[0]),
    }


def _counterbalanced_label_maps(rows: Sequence[Mapping[str, Any]]) -> tuple[bool, set[tuple[str, str]]]:
    mappings: set[tuple[str, str]] = set()
    for row in rows:
        positive = row.get("positive_label")
        negative = row.get("negative_label")
        if isinstance(positive, str) and positive and isinstance(negative, str) and negative and positive != negative:
            mappings.add((positive, negative))
    counterbalanced = any((b, a) in mappings for a, b in mappings)
    return counterbalanced, mappings


def adjudicate_holdout(
    rows: Iterable[Mapping[str, Any]],
    *,
    selected_layer: int,
    selected_gain: float,
) -> dict[str, Any]:
    xs = list(rows)
    if not xs or any(r.get("split") != "holdout" for r in xs):
        raise IntermediateProtocolError("HOLDOUT_ONLY_ROWS_REQUIRED")
    frozen = [
        r for r in xs
        if int(r["layer"]) == int(selected_layer)
        and float(r["gain"]) == float(selected_gain)
    ]
    if not frozen:
        return {"pass": False, "classification": "FROZEN_LAYER_GAIN_NOT_PRESENT"}

    label_maps = {
        str(r.get("label_map_id"))
        for r in frozen
        if r.get("label_map_id") is not None
    }
    if len(label_maps) < 2:
        return {"pass": False, "classification": "LABEL_REMAP_HOLDOUT_REQUIRED"}
    mapping_ok, explicit_mappings = _counterbalanced_label_maps(frozen)
    if not mapping_ok:
        return {"pass": False, "classification": "COUNTERBALANCED_LABEL_MAPPING_REQUIRED"}

    by_case = _control_families(frozen, holdout=True)
    wrong_layer_seen: set[tuple[Any, ...]] = set()
    lesion_rescue_seen: set[tuple[Any, ...]] = set()
    wrong_layer_ok = True
    lesion_rescue_ok = True
    wrong_layer_provenance_failures: list[dict[str, Any]] = []

    for r in frozen:
        key = _family_key(r, holdout=True)
        control = str(r.get("control"))
        has_wrong = r.get("wrong_layer_delta") is not None
        has_lesion_or_rescue = r.get("lesion_delta") is not None or r.get("rescue_delta") is not None
        if (has_wrong or has_lesion_or_rescue) and control != "+VECTOR":
            raise IntermediateProtocolError("AUXILIARY_CAUSAL_EVIDENCE_MUST_BIND_PLUS_VECTOR_ROW")
        if has_wrong:
            wrong_layer_seen.add(key)
            wrong_layer_ok = wrong_layer_ok and _finite(
                r["wrong_layer_delta"], "wrong_layer_delta"
            ) < 0
            wrong_layer = r.get("wrong_layer")
            vector_source_layer = r.get("wrong_layer_vector_source_layer")
            same_selected_vector = r.get("wrong_layer_same_selected_vector")
            receipt_sha = r.get("wrong_layer_receipt_sha256")
            provenance_ok = bool(
                isinstance(wrong_layer, int)
                and not isinstance(wrong_layer, bool)
                and wrong_layer != int(selected_layer)
                and isinstance(vector_source_layer, int)
                and not isinstance(vector_source_layer, bool)
                and vector_source_layer == int(selected_layer)
                and same_selected_vector is True
                and _sha256(receipt_sha)
            )
            if not provenance_ok:
                wrong_layer_provenance_failures.append({
                    "case": key,
                    "wrong_layer": wrong_layer,
                    "wrong_layer_vector_source_layer": vector_source_layer,
                    "wrong_layer_same_selected_vector": same_selected_vector,
                    "wrong_layer_receipt_sha256": receipt_sha,
                })
        if has_lesion_or_rescue:
            if r.get("lesion_delta") is None or r.get("rescue_delta") is None:
                raise IntermediateProtocolError("LESION_RESCUE_PAIR_REQUIRED")
            lesion_rescue_seen.add(key)
            lesion_rescue_ok = (
                lesion_rescue_ok
                and _finite(r["lesion_delta"], "lesion_delta") <= 0
                and _finite(r["rescue_delta"], "rescue_delta") > 0
            )

    case_keys = set(by_case)
    if not case_keys:
        return {"pass": False, "classification": "MATCHED_CONTROL_CASES_REQUIRED"}
    if wrong_layer_seen != case_keys:
        return {
            "pass": False,
            "classification": "WRONG_LAYER_EVIDENCE_REQUIRED",
            "cases_missing_wrong_layer": sorted(case_keys - wrong_layer_seen, key=str),
        }
    if wrong_layer_provenance_failures:
        return {
            "pass": False,
            "classification": "WRONG_LAYER_SELECTED_VECTOR_PROVENANCE_REQUIRED",
            "wrong_layer_provenance_failures": wrong_layer_provenance_failures,
        }
    if lesion_rescue_seen != case_keys:
        return {
            "pass": False,
            "classification": "LESION_RESCUE_EVIDENCE_REQUIRED",
            "cases_missing_lesion_rescue": sorted(case_keys - lesion_rescue_seen, key=str),
        }

    margins = []
    null_drifts = []
    nuisance_effects = []
    for vals in by_case.values():
        if not all(k in vals for k in REQUIRED_CONTROLS):
            return {"pass": False, "classification": "INCOMPLETE_MATCHED_CONTROL_FAMILY"}
        directional = min(
            vals["+VECTOR"] - vals["BASELINE"],
            vals["BASELINE"] - vals["SIGN_FLIP"],
        )
        nuisance = max(
            abs(vals["ORTHOGONAL_SAME_NORM"] - vals["BASELINE"]),
            abs(vals["PERMUTED_SAME_NORM"] - vals["BASELINE"]),
        )
        margins.append(directional - nuisance)
        nuisance_effects.append(nuisance)
        null_drifts.append(abs(vals["NULL_VECTOR"] - vals["BASELINE"]))

    passed = bool(
        margins
        and min(margins) > 0
        and max(null_drifts) <= 1e-6
        and wrong_layer_ok
        and lesion_rescue_ok
    )
    return {
        "pass": passed,
        "classification": (
            "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE"
            if passed
            else "INTERMEDIATE_REPRESENTATION_NOT_ESTABLISHED"
        ),
        "case_count": len(margins),
        "label_map_count": len(label_maps),
        "explicit_label_mappings": sorted(explicit_mappings),
        "counterbalanced_label_mapping": mapping_ok,
        "worst_directional_specificity_margin": min(margins) if margins else None,
        "max_same_norm_nuisance_effect": max(nuisance_effects) if nuisance_effects else None,
        "max_null_drift": max(null_drifts) if null_drifts else None,
        "wrong_layer_evidence_complete": wrong_layer_seen == case_keys,
        "wrong_layer_selected_vector_provenance": not wrong_layer_provenance_failures,
        "lesion_rescue_evidence_complete": lesion_rescue_seen == case_keys,
        "wrong_layer_ok": wrong_layer_ok,
        "lesion_rescue_ok": lesion_rescue_ok,
        "credit_scope": CREDIT_SCOPE,
    }


__all__ = [
    "SCHEMA",
    "CREDIT_SCOPE",
    "REQUIRED_CONTROLS",
    "IntermediateProtocolError",
    "contrastive_direction",
    "control_vectors",
    "lesion",
    "rescue",
    "select_layer_gain",
    "adjudicate_holdout",
    "digest",
]
