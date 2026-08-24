#!/usr/bin/env python3
"""Trigger-1 intermediate-representation causal steering protocol.

Pure deterministic math/evidence layer. No model loading or network I/O.
It exists to prevent readout/token-preference shortcuts from being promoted as
learned Global J-Space representation evidence.

Required stronger discriminator:
- vector derived only from intermediate calibration activations;
- layer/gain selected only on semantic calibration cases;
- disjoint semantic holdout with positive and negative polarity coverage;
- baseline semantic discrimination before intervention credit;
- six matched controls plus explicit wrong-layer and lesion/rescue evidence;
- counterbalanced label mappings so output-token identity cannot explain transfer;
- nuisance controls scored by absolute effect magnitude.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "TRIGGER1_INTERMEDIATE_CONTRASTIVE_PROTOCOL/v3"
CREDIT_SCOPE = "INTERMEDIATE_REPRESENTATION_CAUSAL_CANDIDATE_ONLY"
REQUIRED_CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)
SEMANTIC_POLARITIES = {"positive", "negative"}


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


def _semantic_case_metadata(
    rows: Sequence[Mapping[str, Any]], *, keyed_by_label_map: bool
) -> dict[tuple[str, ...], dict[str, str]]:
    meta: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        case_id = str(row.get("case_id") or "")
        if not case_id:
            raise IntermediateProtocolError("SEMANTIC_CASE_ID_REQUIRED")
        label_map_id = str(row.get("label_map_id") or "") if keyed_by_label_map else ""
        if keyed_by_label_map and not label_map_id:
            raise IntermediateProtocolError("SEMANTIC_LABEL_MAP_ID_REQUIRED")
        polarity = row.get("stimulus_polarity")
        family_id = row.get("stimulus_family_id")
        stimulus_sha = row.get("stimulus_sha256")
        if polarity not in SEMANTIC_POLARITIES:
            raise IntermediateProtocolError("SEMANTIC_STIMULUS_POLARITY_REQUIRED")
        if not isinstance(family_id, str) or not family_id.strip():
            raise IntermediateProtocolError("SEMANTIC_STIMULUS_FAMILY_REQUIRED")
        if not _sha256(stimulus_sha):
            raise IntermediateProtocolError("SEMANTIC_STIMULUS_SHA256_REQUIRED")
        key = (case_id, label_map_id) if keyed_by_label_map else (case_id,)
        current = {
            "polarity": str(polarity),
            "family_id": family_id.strip(),
            "stimulus_sha256": str(stimulus_sha),
        }
        previous = meta.get(key)
        if previous is not None and previous != current:
            raise IntermediateProtocolError("SEMANTIC_STIMULUS_METADATA_INCONSISTENT_WITHIN_CASE")
        meta[key] = current
    return meta


def _semantic_coverage(
    rows: Sequence[Mapping[str, Any]], *, keyed_by_label_map: bool
) -> tuple[dict[tuple[str, ...], dict[str, str]], set[str], set[str]]:
    meta = _semantic_case_metadata(rows, keyed_by_label_map=keyed_by_label_map)
    polarities = {m["polarity"] for m in meta.values()}
    stimulus_shas = {m["stimulus_sha256"] for m in meta.values()}
    if polarities != SEMANTIC_POLARITIES:
        raise IntermediateProtocolError("SEMANTIC_POLARITY_COVERAGE_REQUIRED")
    if len(stimulus_shas) < 2:
        raise IntermediateProtocolError("DISTINCT_SEMANTIC_STIMULI_REQUIRED")
    return meta, polarities, stimulus_shas


def _calibration_rows(rows: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    out = list(rows)
    if not out or any(r.get("split") != "calibration" for r in out):
        raise IntermediateProtocolError("CALIBRATION_ONLY_ROWS_REQUIRED")
    _semantic_coverage(out, keyed_by_label_map=False)
    return out


def _semantic_baseline_margins(
    by_case: Mapping[tuple[str, ...], Mapping[str, float]],
    meta: Mapping[tuple[str, ...], Mapping[str, str]],
) -> list[float]:
    margins: list[float] = []
    for key, semantic in meta.items():
        vals = by_case.get(key)
        if not vals or "BASELINE" not in vals:
            raise IntermediateProtocolError("SEMANTIC_BASELINE_REQUIRED")
        baseline = _finite(vals["BASELINE"], "baseline_target_score")
        signed = baseline if semantic["polarity"] == "positive" else -baseline
        margins.append(signed)
    return margins


def select_layer_gain(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Choose layer/gain only where calibration carries real semantic discrimination."""
    xs = _calibration_rows(rows)
    semantic_meta, _, stimulus_shas = _semantic_coverage(xs, keyed_by_label_map=False)
    combos = sorted({(int(r["layer"]), float(r["gain"])) for r in xs})
    ranked = []
    semantic_rejections = 0
    for layer, gain in combos:
        subset = [r for r in xs if int(r["layer"]) == layer and float(r["gain"]) == gain]
        by_case: dict[tuple[str, ...], dict[str, float]] = {}
        for r in subset:
            key = (str(r["case_id"]),)
            by_case.setdefault(key, {})[str(r["control"])] = _finite(r["target_score"], "target_score")
        try:
            baseline_margins = _semantic_baseline_margins(by_case, semantic_meta)
        except IntermediateProtocolError:
            semantic_rejections += 1
            continue
        if not baseline_margins or min(baseline_margins) <= 0:
            semantic_rejections += 1
            continue
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
            ranked.append((min(margins), sum(margins) / len(margins), min(baseline_margins), layer, gain))
    ranked.sort(reverse=True)
    if not ranked or ranked[0][0] <= 0:
        return {
            "selected": False,
            "reason": "SEMANTIC_BASELINE_DISCRIMINATION_REQUIRED"
            if semantic_rejections == len(combos) and combos
            else "NO_POSITIVE_CALIBRATION_MARGIN",
        }
    worst, avg, semantic_margin, layer, gain = ranked[0]
    return {
        "selected": True,
        "layer": layer,
        "gain": gain,
        "worst_margin": worst,
        "mean_margin": avg,
        "semantic_baseline_min_signed_margin": semantic_margin,
        "semantic_stimulus_count": len(stimulus_shas),
        "selection_sha256": digest(ranked[0]),
    }


def _counterbalanced_label_maps(rows: Sequence[Mapping[str, Any]]) -> tuple[bool, set[tuple[str, str]]]:
    mappings: set[tuple[str, str]] = set()
    for row in rows:
        positive = row.get("positive_label")
        negative = row.get("negative_label")
        if isinstance(positive, str) and positive and isinstance(negative, str) and negative and positive != negative:
            mappings.add((positive, negative))
    return any((b, a) in mappings for a, b in mappings), mappings


def adjudicate_holdout(
    rows: Iterable[Mapping[str, Any]], *, selected_layer: int, selected_gain: float
) -> dict[str, Any]:
    xs = list(rows)
    if not xs or any(r.get("split") != "holdout" for r in xs):
        raise IntermediateProtocolError("HOLDOUT_ONLY_ROWS_REQUIRED")
    frozen = [
        r for r in xs
        if int(r["layer"]) == int(selected_layer) and float(r["gain"]) == float(selected_gain)
    ]
    if not frozen:
        return {"pass": False, "classification": "FROZEN_LAYER_GAIN_NOT_PRESENT"}

    label_maps = {str(r.get("label_map_id")) for r in frozen if r.get("label_map_id") is not None}
    if len(label_maps) < 2:
        return {"pass": False, "classification": "LABEL_REMAP_HOLDOUT_REQUIRED"}
    mapping_ok, explicit_mappings = _counterbalanced_label_maps(frozen)
    if not mapping_ok:
        return {"pass": False, "classification": "COUNTERBALANCED_LABEL_MAPPING_REQUIRED"}

    try:
        semantic_meta, semantic_polarities, stimulus_shas = _semantic_coverage(
            frozen, keyed_by_label_map=True
        )
    except IntermediateProtocolError as exc:
        return {"pass": False, "classification": str(exc)}

    polarity_by_map: dict[str, set[str]] = {}
    for (_case_id, label_map_id), meta in semantic_meta.items():
        polarity_by_map.setdefault(label_map_id, set()).add(meta["polarity"])
    if any(v != SEMANTIC_POLARITIES for v in polarity_by_map.values()):
        return {"pass": False, "classification": "SEMANTIC_POLARITY_PER_LABEL_MAP_REQUIRED"}

    by_case: dict[tuple[str, str], dict[str, float]] = {}
    wrong_layer_seen: set[tuple[str, str]] = set()
    lesion_rescue_seen: set[tuple[str, str]] = set()
    wrong_layer_ok = True
    lesion_rescue_ok = True
    for r in frozen:
        key = (str(r["case_id"]), str(r["label_map_id"]))
        if str(r.get("control")) in REQUIRED_CONTROLS:
            by_case.setdefault(key, {})[str(r["control"])] = _finite(r["target_score"], "target_score")
        if r.get("wrong_layer_delta") is not None:
            wrong_layer_seen.add(key)
            wrong_layer_ok = wrong_layer_ok and _finite(r["wrong_layer_delta"], "wrong_layer_delta") <= 0
        if r.get("lesion_delta") is not None and r.get("rescue_delta") is not None:
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
        return {"pass": False, "classification": "WRONG_LAYER_EVIDENCE_REQUIRED", "cases_missing_wrong_layer": sorted(case_keys - wrong_layer_seen)}
    if lesion_rescue_seen != case_keys:
        return {"pass": False, "classification": "LESION_RESCUE_EVIDENCE_REQUIRED", "cases_missing_lesion_rescue": sorted(case_keys - lesion_rescue_seen)}

    try:
        semantic_baseline_margins = _semantic_baseline_margins(by_case, semantic_meta)
    except IntermediateProtocolError as exc:
        return {"pass": False, "classification": str(exc)}
    if not semantic_baseline_margins or min(semantic_baseline_margins) <= 0:
        return {
            "pass": False,
            "classification": "SEMANTIC_BASELINE_DISCRIMINATION_REQUIRED",
            "semantic_baseline_min_signed_margin": min(semantic_baseline_margins) if semantic_baseline_margins else None,
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
        margins and min(margins) > 0 and max(null_drifts) <= 1e-6 and wrong_layer_ok and lesion_rescue_ok
    )
    return {
        "pass": passed,
        "classification": "INTERMEDIATE_SEMANTIC_REPRESENTATION_CAUSAL_CANDIDATE" if passed else "INTERMEDIATE_REPRESENTATION_NOT_ESTABLISHED",
        "case_count": len(margins),
        "label_map_count": len(label_maps),
        "explicit_label_mappings": sorted(explicit_mappings),
        "counterbalanced_label_mapping": mapping_ok,
        "semantic_polarities": sorted(semantic_polarities),
        "semantic_stimulus_count": len(stimulus_shas),
        "semantic_baseline_correct_count": sum(x > 0 for x in semantic_baseline_margins),
        "semantic_baseline_case_count": len(semantic_baseline_margins),
        "semantic_baseline_min_signed_margin": min(semantic_baseline_margins),
        "worst_directional_specificity_margin": min(margins) if margins else None,
        "max_same_norm_nuisance_effect": max(nuisance_effects) if nuisance_effects else None,
        "max_null_drift": max(null_drifts) if null_drifts else None,
        "wrong_layer_evidence_complete": wrong_layer_seen == case_keys,
        "lesion_rescue_evidence_complete": lesion_rescue_seen == case_keys,
        "wrong_layer_ok": wrong_layer_ok,
        "lesion_rescue_ok": lesion_rescue_ok,
        "credit_scope": CREDIT_SCOPE,
    }


__all__ = [
    "SCHEMA",
    "CREDIT_SCOPE",
    "REQUIRED_CONTROLS",
    "SEMANTIC_POLARITIES",
    "IntermediateProtocolError",
    "contrastive_direction",
    "control_vectors",
    "lesion",
    "rescue",
    "select_layer_gain",
    "adjudicate_holdout",
    "digest",
]
