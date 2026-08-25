#!/usr/bin/env python3
"""Rank-complete nuisance wrapper for the cross-task abstract native-control gate.

V3 closes a promotion-control gap in v2: calibration may identify a nuisance
subspace with rank r>1, while v2 admits only one literal NUISANCE control per
causal cell. V3 binds the frozen calibration nuisance subspace, requires one
causal NUISANCE row for every admitted orthonormal axis in every holdout cell,
and delegates to v2 using the worst (largest target-margin) nuisance effect.

This module is an execution-free evidence gate. It cannot mint canonical,
J-Space, HCU, EntityOS or training credit.
"""
from __future__ import annotations

import copy
import re
from typing import Any

from tools import trigger1_cross_task_abstract_control_gate_v2 as v2

SCHEMA = "CLAY_TRIGGER1_CROSS_TASK_ABSTRACT_CONTROL_GATE/v3"
ATTESTATION_SCHEMA = "CLAY_TRIGGER1_CROSS_TASK_ABSTRACT_CONTROL_EVIDENCE/v3"
NUISANCE_SCHEMA = "CLAY_TRIGGER1_FROZEN_NUISANCE_SUBSPACE_BINDING/v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.fullmatch(value))


def _cell_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("family_id"),
        row.get("vector_state_id"),
        row.get("requested_code"),
        row.get("probe_polarity"),
        row.get("replicate_id"),
    )


def _nuisance_binding(candidate: dict[str, Any], failures: list[str]) -> tuple[int | None, tuple[str, ...]]:
    binding = candidate.get("nuisance_subspace")
    if not isinstance(binding, dict):
        failures.append("NUISANCE_SUBSPACE_BINDING_REQUIRED")
        return None, ()
    if binding.get("schema") != NUISANCE_SCHEMA:
        failures.append("NUISANCE_SUBSPACE_SCHEMA_MISMATCH")
    if binding.get("fit_split") != "CALIBRATION":
        failures.append("NUISANCE_SUBSPACE_MUST_BE_CALIBRATION_ONLY")
    if binding.get("frozen_before_holdout") is not True:
        failures.append("NUISANCE_SUBSPACE_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if not _sha256(binding.get("receipt_sha256")):
        failures.append("NUISANCE_SUBSPACE_RECEIPT_SHA256_REQUIRED")

    rank = binding.get("rank")
    if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
        failures.append("NUISANCE_SUBSPACE_RANK_INVALID")
        rank = None

    axes = binding.get("axes")
    axis_ids: list[str] = []
    if not isinstance(axes, list) or not axes:
        failures.append("NUISANCE_SUBSPACE_AXES_REQUIRED")
    else:
        seen: set[str] = set()
        for i, axis in enumerate(axes):
            p = f"NUISANCE_AXIS_{i}"
            if not isinstance(axis, dict):
                failures.append(p + "_OBJECT_REQUIRED")
                continue
            axis_id = axis.get("axis_id")
            vector_sha = axis.get("vector_sha256")
            if not isinstance(axis_id, str) or not axis_id:
                failures.append(p + "_ID_INVALID")
                continue
            if axis_id in seen:
                failures.append(p + "_DUPLICATE_ID")
                continue
            if not _sha256(vector_sha):
                failures.append(p + "_VECTOR_SHA256_REQUIRED")
                continue
            seen.add(axis_id)
            axis_ids.append(axis_id)
    if rank is not None and len(axis_ids) != rank:
        failures.append("NUISANCE_SUBSPACE_AXIS_COUNT_RANK_MISMATCH")
    return rank, tuple(axis_ids)


def _prepare_rank_complete_nuisance(candidate: dict[str, Any], failures: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate all nuisance axes and collapse them to v2's worst-axis control.

    Larger target_margin means a stronger nuisance control for the requested
    output. Because v2 requires TARGET - NUISANCE > MIN_EFFECT, the maximum
    nuisance target_margin is the conservative/worst axis to delegate.
    """
    rank, axis_ids = _nuisance_binding(candidate, failures)
    rows = candidate.get("holdout_causal_rows")
    if not isinstance(rows, list) or not rows:
        failures.append("HOLDOUT_CAUSAL_ROWS_REQUIRED_FOR_NUISANCE_BINDING")
        return copy.deepcopy(candidate), {
            "nuisance_rank": rank,
            "axis_ids": list(axis_ids),
            "cells": 0,
            "rank_complete": False,
        }

    non_nuisance: list[dict[str, Any]] = []
    nuisance_by_cell: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    all_cells: set[tuple[Any, ...]] = set()

    for i, raw in enumerate(rows):
        if not isinstance(raw, dict):
            # v2 will report the generic row error; do not mask it here.
            non_nuisance.append(raw)
            continue
        row = copy.deepcopy(raw)
        cell = _cell_key(row)
        all_cells.add(cell)
        ctrl = row.get("control")
        axis_id = row.get("nuisance_axis_id")
        if ctrl == "NUISANCE":
            if not isinstance(axis_id, str) or not axis_id:
                failures.append(f"CAUSAL_{i}_NUISANCE_AXIS_ID_REQUIRED")
                continue
            if axis_id not in axis_ids:
                failures.append(f"CAUSAL_{i}_NUISANCE_AXIS_UNBOUND:{axis_id}")
                continue
            bucket = nuisance_by_cell.setdefault(cell, {})
            if axis_id in bucket:
                failures.append(f"CAUSAL_{i}_DUPLICATE_NUISANCE_AXIS:{axis_id}")
                continue
            bucket[axis_id] = row
        else:
            if axis_id is not None:
                failures.append(f"CAUSAL_{i}_NON_NUISANCE_AXIS_ID_FORBIDDEN")
            non_nuisance.append(row)

    expected = set(axis_ids)
    collapsed: list[dict[str, Any]] = []
    complete_cells = 0
    for cell in sorted(all_cells, key=lambda x: tuple(str(v) for v in x)):
        bucket = nuisance_by_cell.get(cell, {})
        got = set(bucket)
        if got != expected:
            missing = sorted(expected - got)
            extra = sorted(got - expected)
            suffix = ":".join(str(v) for v in cell)
            if missing:
                failures.append("NUISANCE_AXIS_COVERAGE_INCOMPLETE:" + suffix + ":missing=" + ",".join(missing))
            if extra:
                failures.append("NUISANCE_AXIS_COVERAGE_EXTRA:" + suffix + ":extra=" + ",".join(extra))
            continue
        if not bucket:
            failures.append("NUISANCE_AXIS_COVERAGE_EMPTY:" + ":".join(str(v) for v in cell))
            continue
        margins = []
        valid = True
        for axis_id in axis_ids:
            margin = bucket[axis_id].get("target_margin")
            if not v2._num(margin):
                failures.append("NUISANCE_AXIS_MARGIN_INVALID:" + axis_id + ":" + ":".join(str(v) for v in cell))
                valid = False
            else:
                margins.append((float(margin), axis_id, bucket[axis_id]))
        if not valid:
            continue
        worst_margin, worst_axis_id, worst_row = max(margins, key=lambda x: x[0])
        representative = copy.deepcopy(worst_row)
        representative.pop("nuisance_axis_id", None)
        representative["target_margin"] = worst_margin
        representative["rank_complete_worst_nuisance_axis_id"] = worst_axis_id
        representative["rank_complete_nuisance_axis_count"] = len(axis_ids)
        collapsed.append(representative)
        complete_cells += 1

    delegated = copy.deepcopy(candidate)
    delegated["schema"] = v2.ATTESTATION_SCHEMA
    delegated["holdout_causal_rows"] = non_nuisance + collapsed
    return delegated, {
        "nuisance_rank": rank,
        "axis_ids": list(axis_ids),
        "cells": len(all_cells),
        "complete_cells": complete_cells,
        "rank_complete": bool(axis_ids) and complete_cells == len(all_cells) and not any(
            f.startswith("NUISANCE_") or "NUISANCE_AXIS" in f for f in failures
        ),
        "delegation_rule": "MAX_TARGET_MARGIN_OVER_ALL_BOUND_NUISANCE_AXES_PER_CAUSAL_CELL",
    }


def adjudicate(candidate: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(candidate, dict):
        candidate = {}
        failures.append("ATTESTATION_OBJECT_REQUIRED")
    if candidate.get("schema") != ATTESTATION_SCHEMA:
        failures.append("ATTESTATION_SCHEMA_MISMATCH")

    delegated, nuisance = _prepare_rank_complete_nuisance(candidate, failures)
    base = v2.adjudicate(delegated)
    failures.extend(base.get("failures") or [])
    passed = not failures

    return {
        "schema": SCHEMA,
        "cross_task_abstract_native_control_pass": passed,
        "failures": sorted(set(failures)),
        "rank_complete_nuisance_control": nuisance,
        "delegated_v2": base,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "claim_scope_if_pass": "QWEN3_0_6B_RANK_CONSISTENT_PROOF_TOPOLOGY_POSITION_MATCHED_RANK_COMPLETE_NUISANCE_CROSS_TASK_NATIVE_CONTROL_COMPONENT_ONLY",
        "evidence_boundary": "V3 requires calibration-bound rank-complete nuisance causal coverage and delegates the worst nuisance axis per cell into strict v2 cross-task/fixed-gain/rank/topology/position/bidirectional/off-target adjudication. It executes no model and mints no canonical/global J-Space credit.",
    }
