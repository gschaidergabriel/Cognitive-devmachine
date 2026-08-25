#!/usr/bin/env python3
"""Exact-vector nuisance-subspace successor to cross-task abstract-control gate v4.

V4 requires strict causal-cell/topology matching plus rank-complete nuisance coverage for every declared nuisance axis but binds those axes only by
IDs and hashes.  V5 additionally binds the actual frozen calibration vectors, verifies that
the declared nuisance basis is genuinely orthonormal, and recomputes how much of every
post-residualization semantic control vector lies inside that nuisance span.

This closes two source-level promotion gaps: duplicate/non-orthogonal axes cannot masquerade
as a higher-rank nuisance basis, and per-axis causal weakness cannot substitute for an exact
linear-subspace deconfound.  V5 still delegates the causal/runtime requirements to v4 and
mints no canonical, J-Space, HCU, EntityOS or training credit.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from typing import Any

from tools import trigger1_cross_task_abstract_control_gate_v4 as v4

SCHEMA = "CLAY_TRIGGER1_CROSS_TASK_ABSTRACT_CONTROL_GATE/v5"
ATTESTATION_SCHEMA = "CLAY_TRIGGER1_CROSS_TASK_ABSTRACT_CONTROL_EVIDENCE/v5"
NUISANCE_SCHEMA = "CLAY_TRIGGER1_FROZEN_NUISANCE_SUBSPACE_BINDING/v2"
SEMANTIC_SCHEMA = "CLAY_TRIGGER1_POST_NUISANCE_SEMANTIC_VECTOR_BINDING/v1"
STATES = ("S0", "S1", "S2")
ORTHONORMAL_TOL = 1e-5
MAX_NUISANCE_PROJECTION_FRACTION = 1e-4
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.fullmatch(value))


def _vector(value: Any) -> list[float] | None:
    if not isinstance(value, list) or len(value) < 2:
        return None
    out: list[float] = []
    for item in value:
        if not isinstance(item, (int, float)) or isinstance(item, bool) or not math.isfinite(float(item)):
            return None
        out.append(float(item))
    return out


def vector_sha256(vector: list[float]) -> str:
    canonical = [float(x) for x in vector]
    payload = json.dumps(canonical, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _dot(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("VECTOR_DIMENSION_MISMATCH")
    return sum(x * y for x, y in zip(a, b))


def _norm(a: list[float]) -> float:
    return math.sqrt(_dot(a, a))


def _validate_vector_bindings(candidate: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    nuisance = candidate.get("nuisance_subspace")
    axes: list[tuple[str, list[float], str]] = []
    if not isinstance(nuisance, dict):
        failures.append("V5_NUISANCE_SUBSPACE_BINDING_REQUIRED")
        return {"basis_dimension": None, "axis_count": 0, "max_axis_dot_abs": None, "semantic_projection_fraction": {}}
    if nuisance.get("schema") != NUISANCE_SCHEMA:
        failures.append("V5_NUISANCE_SUBSPACE_SCHEMA_MISMATCH")
    if nuisance.get("fit_split") != "CALIBRATION":
        failures.append("V5_NUISANCE_SUBSPACE_MUST_BE_CALIBRATION_ONLY")
    if nuisance.get("frozen_before_holdout") is not True:
        failures.append("V5_NUISANCE_SUBSPACE_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if not _sha256(nuisance.get("receipt_sha256")):
        failures.append("V5_NUISANCE_SUBSPACE_RECEIPT_SHA256_REQUIRED")
    rank = nuisance.get("rank")
    if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
        failures.append("V5_NUISANCE_SUBSPACE_RANK_INVALID")
        rank = None
    raw_axes = nuisance.get("axes")
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    if not isinstance(raw_axes, list) or not raw_axes:
        failures.append("V5_NUISANCE_SUBSPACE_AXES_REQUIRED")
    else:
        for i, raw in enumerate(raw_axes):
            p = f"V5_NUISANCE_AXIS_{i}"
            if not isinstance(raw, dict):
                failures.append(p + "_OBJECT_REQUIRED")
                continue
            axis_id = raw.get("axis_id")
            vec = _vector(raw.get("vector"))
            digest = raw.get("vector_sha256")
            if not isinstance(axis_id, str) or not axis_id:
                failures.append(p + "_ID_INVALID")
                continue
            if axis_id in seen_ids:
                failures.append(p + "_DUPLICATE_ID")
                continue
            seen_ids.add(axis_id)
            if vec is None:
                failures.append(p + "_VECTOR_INVALID")
                continue
            if not _sha256(digest) or digest != vector_sha256(vec):
                failures.append(p + "_VECTOR_SHA256_MISMATCH")
                continue
            if digest in seen_hashes:
                failures.append(p + "_DUPLICATE_VECTOR_SHA256")
                continue
            seen_hashes.add(digest)
            n = _norm(vec)
            if not math.isclose(n, 1.0, rel_tol=0.0, abs_tol=ORTHONORMAL_TOL):
                failures.append(p + "_NOT_UNIT_NORM")
            axes.append((axis_id, vec, digest))
    if rank is not None and len(axes) != rank:
        failures.append("V5_NUISANCE_SUBSPACE_AXIS_COUNT_RANK_MISMATCH")
    dims = {len(v) for _, v, _ in axes}
    if len(dims) > 1:
        failures.append("V5_NUISANCE_AXIS_DIMENSION_MISMATCH")
    max_dot = 0.0
    if len(dims) == 1:
        for i in range(len(axes)):
            for j in range(i + 1, len(axes)):
                d = abs(_dot(axes[i][1], axes[j][1]))
                max_dot = max(max_dot, d)
                if d > ORTHONORMAL_TOL:
                    failures.append(f"V5_NUISANCE_AXES_NOT_ORTHOGONAL:{axes[i][0]}:{axes[j][0]}")

    semantic = candidate.get("semantic_control_vectors")
    projections: dict[str, float | None] = {}
    if not isinstance(semantic, dict):
        failures.append("V5_SEMANTIC_VECTOR_BINDING_REQUIRED")
    else:
        if semantic.get("schema") != SEMANTIC_SCHEMA:
            failures.append("V5_SEMANTIC_VECTOR_SCHEMA_MISMATCH")
        if semantic.get("fit_split") != "CALIBRATION":
            failures.append("V5_SEMANTIC_VECTORS_MUST_BE_CALIBRATION_ONLY")
        if semantic.get("frozen_before_holdout") is not True:
            failures.append("V5_SEMANTIC_VECTORS_MUST_BE_FROZEN_BEFORE_HOLDOUT")
        if semantic.get("vectors_are_post_nuisance_residualization") is not True:
            failures.append("V5_POST_NUISANCE_RESIDUALIZATION_REQUIRED")
        if semantic.get("residualization_method") != "ORTHOGONAL_PROJECTION_CALIBRATION_FROZEN":
            failures.append("V5_RESIDUALIZATION_METHOD_MISMATCH")
        if not _sha256(semantic.get("receipt_sha256")):
            failures.append("V5_SEMANTIC_VECTOR_RECEIPT_SHA256_REQUIRED")
        raw_vectors = semantic.get("vectors")
        if not isinstance(raw_vectors, dict) or set(raw_vectors) != set(STATES):
            failures.append("V5_EXACT_THREE_SEMANTIC_VECTORS_REQUIRED")
        elif len(dims) == 1 and axes:
            dim = next(iter(dims))
            for state in STATES:
                item = raw_vectors.get(state)
                if not isinstance(item, dict):
                    failures.append(f"V5_SEMANTIC_VECTOR_{state}_OBJECT_REQUIRED")
                    projections[state] = None
                    continue
                vec = _vector(item.get("vector"))
                digest = item.get("vector_sha256")
                if vec is None or len(vec) != dim:
                    failures.append(f"V5_SEMANTIC_VECTOR_{state}_INVALID_OR_DIMENSION_MISMATCH")
                    projections[state] = None
                    continue
                if not _sha256(digest) or digest != vector_sha256(vec):
                    failures.append(f"V5_SEMANTIC_VECTOR_{state}_SHA256_MISMATCH")
                energy = _dot(vec, vec)
                if energy <= 0:
                    failures.append(f"V5_SEMANTIC_VECTOR_{state}_ZERO_NORM")
                    projections[state] = None
                    continue
                projected_energy = sum(_dot(vec, q) ** 2 for _, q, _ in axes)
                fraction = projected_energy / energy
                projections[state] = fraction
                if fraction > MAX_NUISANCE_PROJECTION_FRACTION:
                    failures.append(f"V5_SEMANTIC_VECTOR_{state}_NUISANCE_PROJECTION_TOO_LARGE")

    return {
        "basis_dimension": next(iter(dims)) if len(dims) == 1 else None,
        "axis_count": len(axes),
        "declared_rank": rank,
        "max_axis_dot_abs": max_dot if axes else None,
        "orthonormal_tolerance": ORTHONORMAL_TOL,
        "semantic_projection_fraction": projections,
        "max_nuisance_projection_fraction": MAX_NUISANCE_PROJECTION_FRACTION,
    }


def _delegate_to_v4(candidate: dict[str, Any]) -> dict[str, Any]:
    delegated = copy.deepcopy(candidate)
    delegated["schema"] = v4.ATTESTATION_SCHEMA
    nuisance = delegated.get("nuisance_subspace")
    if isinstance(nuisance, dict):
        nuisance["schema"] = v4.NUISANCE_SCHEMA
    delegated.pop("semantic_control_vectors", None)
    return delegated


def adjudicate(candidate: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(candidate, dict):
        candidate = {}
        failures.append("ATTESTATION_OBJECT_REQUIRED")
    if candidate.get("schema") != ATTESTATION_SCHEMA:
        failures.append("ATTESTATION_SCHEMA_MISMATCH")
    vector_binding = _validate_vector_bindings(candidate, failures)
    base = v4.adjudicate(_delegate_to_v4(candidate))
    failures.extend(base.get("failures") or [])
    passed = not failures and base.get("cross_task_abstract_native_control_pass") is True
    return {
        "schema": SCHEMA,
        "cross_task_abstract_native_control_pass": passed,
        "failures": sorted(set(failures)),
        "exact_nuisance_vector_binding": vector_binding,
        "delegated_v4": base,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "claim_scope_if_pass": "QWEN3_0_6B_EXACT_ORTHONORMAL_NUISANCE_RESIDUALIZED_CONTROL_MATCHED_CROSS_TASK_NATIVE_CONTROL_COMPONENT_ONLY",
        "evidence_boundary": "V5 verifies exact frozen nuisance basis bytes, orthonormality and post-residualization semantic-vector projection before delegating all v4 causal/runtime requirements. It does not prove arbitrary nonlinear nuisance-span causal equivalence, execute a model, or mint canonical/global J-Space credit.",
    }
