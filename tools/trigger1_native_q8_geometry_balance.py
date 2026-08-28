#!/usr/bin/env python3
"""Deterministic family-energy-balanced semantic geometry finalizer for Trigger-1.

The native Q8 basis lane already uses a rank analyzer that requires raw and
family-energy-balanced rank classifications to agree.  Rank agreement does not imply
that the raw mean direction is stable: one high-energy scenario can preserve rank while
rotating the actual controller axes toward itself.

This execution-free primitive closes that metrology gap.  It consumes matched
AFFIRMATIVE/NEGATIVE/NEUTRAL calibration activations and an already-admitted rank verdict,
scales all three centered class vectors from a family by the same inverse contrast-pair
energy, then constructs the 1D/2D semantic basis from those equal-energy families.  The
same scalar is applied to both within-family contrasts, so each family's internal simplex
shape is preserved while cross-family magnitude domination is removed.

It also reports raw-vs-balanced axis cosines as a diagnostic.  It does not choose a gain,
run a model, open holdout data, or mint runtime/J-Space/HCU/EntityOS/training/canonical
credit.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import numpy as np

SCHEMA = "CLAY_TRIGGER1_NATIVE_Q8_FAMILY_ENERGY_BALANCED_GEOMETRY/v1"
INPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_SIMPLEX_CALIBRATION_ACTIVATIONS/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
RANK_VERDICTS = {"ONE_DIMENSIONAL_SUPPORTED": 1, "TWO_DIMENSIONAL_REQUIRED": 2}


class GeometryError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def vector_sha_f64(vector: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(vector, dtype="<f8").tobytes()).hexdigest()


def _norm(vector: np.ndarray) -> float:
    return float(np.linalg.norm(vector))


def _unit(vector: np.ndarray, name: str) -> np.ndarray:
    n = _norm(vector)
    if not math.isfinite(n) or n <= 1e-12:
        raise GeometryError(f"{name}_DEGENERATE")
    return vector / n


def _cosine(a: np.ndarray | None, b: np.ndarray | None) -> float | None:
    if a is None or b is None:
        return None
    na, nb = _norm(a), _norm(b)
    if na <= 1e-12 or nb <= 1e-12:
        return None
    return float(np.dot(a, b) / (na * nb))


def _parse(payload: Any) -> tuple[list[str], dict[str, dict[str, np.ndarray]], int]:
    if not isinstance(payload, dict) or payload.get("schema") != INPUT_SCHEMA:
        raise GeometryError("INPUT_SCHEMA_INVALID")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise GeometryError("ROWS_REQUIRED")
    dimension = payload.get("dimension")
    if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension < 2:
        raise GeometryError("DIMENSION_AT_LEAST_TWO_REQUIRED")

    grouped: dict[str, dict[str, np.ndarray]] = {}
    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise GeometryError(f"ROW_{index}_OBJECT_REQUIRED")
        row_id = str(row.get("row_id") or "").strip()
        family = str(row.get("family_group_id") or "").strip()
        semantic = str(row.get("semantic_class") or "").strip().upper()
        if not row_id or row_id in seen_ids:
            raise GeometryError(f"ROW_{index}_UNIQUE_ROW_ID_REQUIRED")
        if not family:
            raise GeometryError(f"ROW_{index}_FAMILY_REQUIRED")
        if semantic not in CLASSES:
            raise GeometryError(f"ROW_{index}_SEMANTIC_CLASS_INVALID")
        try:
            activation = np.asarray(row.get("activation"), dtype=np.float64)
        except Exception as exc:
            raise GeometryError(f"ROW_{index}_NUMERIC_ACTIVATION_REQUIRED") from exc
        if activation.shape != (dimension,):
            raise GeometryError(f"ROW_{index}_DIMENSION_MISMATCH")
        if not np.all(np.isfinite(activation)):
            raise GeometryError(f"ROW_{index}_NONFINITE_ACTIVATION")
        slot = grouped.setdefault(family, {})
        if semantic in slot:
            raise GeometryError(f"FAMILY_DUPLICATE_CLASS:{family}:{semantic}")
        slot[semantic] = activation
        seen_ids.add(row_id)

    families = sorted(grouped)
    if len(families) < 3:
        raise GeometryError("AT_LEAST_THREE_MATCHED_FAMILIES_REQUIRED")
    for family in families:
        if set(grouped[family]) != set(CLASSES):
            raise GeometryError(f"FAMILY_MUST_CONTAIN_EXACT_TRIAD:{family}")
    return families, grouped, dimension


def _geometry_from_family_rows(
    families: list[str],
    grouped: dict[str, dict[str, np.ndarray]],
    *,
    energy_balance: bool,
    rank: int,
) -> dict[str, Any]:
    h1_rows: list[np.ndarray] = []
    d2_rows: list[np.ndarray] = []
    centered_rows: dict[str, list[np.ndarray]] = {name: [] for name in CLASSES}
    energies: list[float] = []

    for family in families:
        a = grouped[family]["AFFIRMATIVE"]
        n = grouped[family]["NEGATIVE"]
        u = grouped[family]["NEUTRAL"]
        grand = (a + n + u) / 3.0
        centered = {
            "AFFIRMATIVE": a - grand,
            "NEGATIVE": n - grand,
            "NEUTRAL": u - grand,
        }
        h1 = a - 0.5 * (n + u)
        d2 = n - u
        energy = math.sqrt(_norm(h1) ** 2 + _norm(d2) ** 2)
        if not math.isfinite(energy) or energy <= 1e-12:
            raise GeometryError(f"DEGENERATE_MATCHED_CONTRAST_PAIR:{family}")
        energies.append(energy)
        factor = 1.0 / energy if energy_balance else 1.0
        h1_rows.append(h1 * factor)
        d2_rows.append(d2 * factor)
        for semantic in CLASSES:
            centered_rows[semantic].append(centered[semantic] * factor)

    h1_mean = np.mean(np.stack(h1_rows, axis=0), axis=0)
    axis1 = _unit(h1_mean, "H1")
    d2_mean = np.mean(np.stack(d2_rows, axis=0), axis=0)
    h2 = d2_mean - float(np.dot(d2_mean, axis1)) * axis1
    if rank == 2:
        axis2 = _unit(h2, "H2")
        axes = np.stack([axis1, axis2], axis=0)
    else:
        axis2 = None
        axes = np.stack([axis1], axis=0)

    centroids = {
        semantic: np.mean(np.stack(centered_rows[semantic], axis=0), axis=0)
        for semantic in CLASSES
    }
    coordinates: dict[str, list[float]] = {}
    projected: dict[str, np.ndarray] = {}
    for semantic in CLASSES:
        coords = axes @ centroids[semantic]
        projected[semantic] = np.asarray(coords @ axes, dtype=np.float64)
        coordinates[semantic] = [float(value) for value in coords]

    nonzero_norms = [
        _norm(projected[semantic])
        for semantic in CLASSES
        if _norm(projected[semantic]) > 1e-12
    ]
    if len(nonzero_norms) < 2:
        raise GeometryError("TARGET_GEOMETRY_DEGENERATE")
    shared_scale = float(sum(nonzero_norms) / len(nonzero_norms))
    vectors = {semantic: projected[semantic] / shared_scale for semantic in CLASSES}
    mean_vector = sum(vectors.values()) / 3.0
    vectors = {semantic: vector - mean_vector for semantic, vector in vectors.items()}

    return {
        "axis1": axis1,
        "axis2": axis2,
        "coordinates": coordinates,
        "vectors": vectors,
        "shared_scale": shared_scale,
        "family_pair_energies": energies,
    }


def finalize(payload: dict[str, Any], rank_result: dict[str, Any]) -> dict[str, Any]:
    families, _, dimension = _parse(payload)
    verdict = str(rank_result.get("verdict") or "") if isinstance(rank_result, dict) else ""
    rank = RANK_VERDICTS.get(verdict)
    if rank is None:
        raise GeometryError(f"ADMITTED_RANK_VERDICT_REQUIRED:{verdict or 'MISSING'}")
    receipt = rank_result.get("analysis_receipt_sha256")
    if not isinstance(receipt, str) or len(receipt) != 64:
        raise GeometryError("RANK_ANALYSIS_RECEIPT_SHA256_REQUIRED")

    families, grouped, dimension = _parse(payload)
    raw = _geometry_from_family_rows(families, grouped, energy_balance=False, rank=rank)
    balanced = _geometry_from_family_rows(families, grouped, energy_balance=True, rank=rank)

    axis1_cos = _cosine(raw["axis1"], balanced["axis1"])
    axis2_cos = _cosine(raw["axis2"], balanced["axis2"])
    packet_core = {
        "schema": SCHEMA,
        "rank": rank,
        "rank_verdict": verdict,
        "rank_analysis_receipt_sha256": receipt,
        "input_payload_sha256": canonical_sha(payload),
        "dimension": dimension,
        "families": families,
        "family_weighting": "INVERSE_WITHIN_FAMILY_CONTRAST_PAIR_ENERGY",
        "family_pair_energy_definition": "sqrt(||A-0.5*(N+U)||^2 + ||N-U||^2)",
        "internal_simplex_shape_preserved_within_family": True,
        "balanced_axis_h1_sha256_f64le": vector_sha_f64(balanced["axis1"]),
        "balanced_axis_h2_sha256_f64le": vector_sha_f64(balanced["axis2"]) if balanced["axis2"] is not None else None,
        "balanced_semantic_coordinates": balanced["coordinates"],
        "balanced_shared_geometry_scale": balanced["shared_scale"],
        "balanced_target_vectors": {
            semantic: {
                "vector_sha256_f64le": vector_sha_f64(balanced["vectors"][semantic]),
                "vector_l2": _norm(balanced["vectors"][semantic]),
            }
            for semantic in CLASSES
        },
        "zero_sum_target_vector_residual_l2": _norm(sum(balanced["vectors"].values())),
        "raw_vs_balanced_diagnostic": {
            "axis_h1_cosine": axis1_cos,
            "axis_h2_cosine": axis2_cos,
            "minimum_family_pair_energy": min(balanced["family_pair_energies"]),
            "maximum_family_pair_energy": max(balanced["family_pair_energies"]),
            "energy_dynamic_range": max(balanced["family_pair_energies"]) / min(balanced["family_pair_energies"]),
        },
        "gain_selected": False,
        "holdout_opened": False,
        "model_executed": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "whole_entityos_hcu_credit": False,
        "evidence_boundary": "Calibration representation geometry only. Rank must already be admitted. Family-energy balancing prevents one scenario magnitude from dominating controller direction but does not establish causal steerability or semantic truth.",
    }
    return {**packet_core, "geometry_receipt_sha256": canonical_sha(packet_core)}
