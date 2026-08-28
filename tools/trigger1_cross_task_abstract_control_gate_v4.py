#!/usr/bin/env python3
"""Strict causal-cell matching successor for cross-task abstract control.

V4 composes the rank-complete nuisance coverage of v3 with two additional
fail-closed invariants that v2/v3 do not enforce directly:

* every intervention/control row within one causal cell must use the same task
  grammar, proof topology, demo context, prompt length, probe length and final
  token position as that cell's TARGET row; and
* proof topology must be fully crossed over target x opaque code x query
  polarity, rather than merely appearing balanced after pooling those factors.

This is an execution-free evidence gate. It cannot mint canonical, J-Space,
HCU, EntityOS or training credit.
"""
from __future__ import annotations

import copy
from typing import Any

from tools import trigger1_cross_task_abstract_control_gate_v2 as v2
from tools import trigger1_cross_task_abstract_control_gate_v3 as v3

SCHEMA = "CLAY_TRIGGER1_CROSS_TASK_ABSTRACT_CONTROL_GATE/v4"
ATTESTATION_SCHEMA = "CLAY_TRIGGER1_CROSS_TASK_ABSTRACT_CONTROL_EVIDENCE/v4"

STATES = v2.STATES
CODES = v2.CODES
POLARITIES = v2.POLARITIES
CONTROLS = v2.CONTROLS
PINNED_GGUF_SHA256 = v2.PINNED_GGUF_SHA256
PINNED_LLAMA_CPP_COMMIT = v2.PINNED_LLAMA_CPP_COMMIT
PRIMARY_GAIN = v2.PRIMARY_GAIN
PRIMARY_LAYER = v2.PRIMARY_LAYER
NUISANCE_SCHEMA = v3.NUISANCE_SCHEMA

MATCH_FIELDS = (
    "task_grammar_id",
    "proof_topology_id",
    "demo_context_id",
    "prompt_tokens",
    "probe_tokens",
    "last_token_index",
)


def _cell_key(row: dict[str, Any]) -> tuple[str, str, str, str, str] | None:
    vals = (
        row.get("family_id"),
        row.get("vector_state_id"),
        row.get("requested_code"),
        row.get("probe_polarity"),
        row.get("replicate_id"),
    )
    if not all(isinstance(x, str) and x for x in vals):
        return None
    return vals  # type: ignore[return-value]


def _signature(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(row.get(field) for field in MATCH_FIELDS)


def _strict_cell_matching(candidate: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    rows = candidate.get("holdout_causal_rows")
    if not isinstance(rows, list):
        return {}

    cells: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    family_topologies: dict[str, set[str]] = {}
    topology_counts: dict[tuple[str, str, str, str, str], int] = {}

    for raw in rows:
        if not isinstance(raw, dict):
            continue
        key = _cell_key(raw)
        if key is None:
            continue
        cells.setdefault(key, []).append(raw)
        if raw.get("control") == "TARGET":
            fam, target, code, polarity, _rep = key
            topology = raw.get("proof_topology_id")
            if isinstance(topology, str) and topology:
                family_topologies.setdefault(fam, set()).add(topology)
                tkey = (fam, target, code, polarity, topology)
                topology_counts[tkey] = topology_counts.get(tkey, 0) + 1

    exactly_matched_cells = 0
    for key, cell_rows in cells.items():
        target_rows = [r for r in cell_rows if r.get("control") == "TARGET"]
        if len(target_rows) != 1:
            # V2/V3 own generic missing/duplicate-control failures.
            continue
        target_signature = _signature(target_rows[0])
        cell_ok = True
        for row in cell_rows:
            sig = _signature(row)
            for idx, field in enumerate(MATCH_FIELDS):
                if sig[idx] != target_signature[idx]:
                    ctrl = str(row.get("control"))
                    axis = row.get("nuisance_axis_id")
                    suffix = ctrl if axis is None else f"{ctrl}@{axis}"
                    failures.append(
                        "CAUSAL_CONTROL_MATCH_FAIL:"
                        + field
                        + ":"
                        + ":".join(key)
                        + ":"
                        + suffix
                    )
                    cell_ok = False
        if cell_ok:
            exactly_matched_cells += 1

    factorial_cells_checked = 0
    for fam, topologies in sorted(family_topologies.items()):
        if len(topologies) < 2:
            # V2 already rejects insufficient topology diversity.
            continue
        for topology in sorted(topologies):
            counts: list[int] = []
            for target in STATES:
                for code in CODES:
                    for polarity in POLARITIES:
                        n = topology_counts.get((fam, target, code, polarity, topology), 0)
                        counts.append(n)
                        factorial_cells_checked += 1
                        if n < 1:
                            failures.append(
                                f"PROOF_TOPOLOGY_FULL_FACTORIAL_CELL_MISSING:{fam}:{target}:{code}:{polarity}:{topology}"
                            )
            if counts and len(set(counts)) != 1:
                failures.append(f"PROOF_TOPOLOGY_FULL_FACTORIAL_IMBALANCE:{fam}:{topology}")

    return {
        "cells_observed": len(cells),
        "cells_exactly_matched": exactly_matched_cells,
        "match_fields": list(MATCH_FIELDS),
        "topology_factorial": "PROOF_TOPOLOGY_X_TARGET_3_X_CODE_3_X_POLARITY_2",
        "topology_factorial_cells_checked": factorial_cells_checked,
    }


def adjudicate(candidate: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(candidate, dict):
        candidate = {}
        failures.append("ATTESTATION_OBJECT_REQUIRED")
    if candidate.get("schema") != ATTESTATION_SCHEMA:
        failures.append("ATTESTATION_SCHEMA_MISMATCH")

    strict = _strict_cell_matching(candidate, failures)

    delegated = copy.deepcopy(candidate)
    delegated["schema"] = v3.ATTESTATION_SCHEMA
    base = v3.adjudicate(delegated)
    failures.extend(base.get("failures") or [])
    passed = not failures

    return {
        "schema": SCHEMA,
        "cross_task_abstract_native_control_pass": passed,
        "failures": sorted(set(failures)),
        "strict_causal_cell_matching": strict,
        "delegated_v3": base,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "claim_scope_if_pass": "QWEN3_0_6B_RANK_CONSISTENT_CONTROL_MATCHED_TOPOLOGY_FACTORIAL_RANK_COMPLETE_NUISANCE_CROSS_TASK_NATIVE_CONTROL_COMPONENT_ONLY",
        "evidence_boundary": "V4 adds exact within-cell topology/context/token-position matching and topology x target x code x polarity factoriality on top of v3 rank-complete nuisance adjudication. It executes no model and mints no canonical/global J-Space credit.",
    }
