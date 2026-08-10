#!/usr/bin/env python3
"""WP04 research candidate: rank exact signature work by symbolic type-anchor leverage.

Input is a CallConstraintGraph/v1. This planner never invents a concrete type and never upgrades
an unresolved call. It asks a narrower planning question: if an exact, independently justified
signature for target/arity were later added, which currently-equal symbolic type variables would
be anchored by that contract? This makes the remaining signature work measurable and lets the
compiler/research loop prioritize high-leverage declarations rather than fill 27 rows arbitrarily.

A call contract anchors one symbolic return node and one symbolic parameter node per argument.
Connected equality components define propagation. The planner reports per-call component
coverage and a deterministic greedy set cover over call-associated components. This is planning
evidence only; it grants no execution, truth or effect authority.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "ClayCodeCallAnchorPlan/v1-research"
DOMAIN = b"ClayCodeCallAnchorPlan/v1-research\x00"


class AnchorPlanError(ValueError):
    pass


def stable_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(DOMAIN + stable_json(value)).hexdigest()


def _components(graph: dict[str, Any]) -> tuple[list[list[str]], dict[str, int]]:
    rows = graph.get("type_equality_components")
    if not isinstance(rows, list):
        raise AnchorPlanError("constraint graph missing type_equality_components")
    components: list[list[str]] = []
    owner: dict[str, int] = {}
    for idx, raw in enumerate(rows):
        if not isinstance(raw, list) or not raw or not all(isinstance(x, str) for x in raw):
            raise AnchorPlanError(f"invalid type equality component at {idx}")
        comp = sorted(set(raw))
        if len(comp) != len(raw):
            raise AnchorPlanError(f"duplicate node inside component {idx}")
        for node in comp:
            if node in owner:
                raise AnchorPlanError(f"node appears in multiple components: {node}")
            owner[node] = idx
        components.append(comp)
    return components, owner


def _contract_nodes(target: str, arity: int) -> list[str]:
    return [f"ret:{target}/{arity}", *[f"param:{target}/{arity}#{i}" for i in range(arity)]]


def build_anchor_plan(graph: dict[str, Any]) -> dict[str, Any]:
    if graph.get("schema") != "ClayCodeCallConstraintGraph/v1-research":
        raise AnchorPlanError(f"unsupported constraint graph schema: {graph.get('schema')!r}")
    components, owner = _components(graph)
    obligations = graph.get("obligations")
    if not isinstance(obligations, list) or not obligations:
        raise AnchorPlanError("constraint graph missing obligations")

    rows = []
    call_components: set[int] = set()
    for obligation in obligations:
        if not isinstance(obligation, dict):
            raise AnchorPlanError("obligation must be object")
        identity = obligation.get("identity") or {}
        target = identity.get("target")
        arity = identity.get("arity")
        if not isinstance(target, str) or not isinstance(arity, int) or arity < 0:
            raise AnchorPlanError(f"invalid call identity: {identity!r}")
        nodes = _contract_nodes(target, arity)
        covered = sorted({owner[node] for node in nodes if node in owner})
        call_components.update(covered)
        covered_nodes = sorted({node for cid in covered for node in components[cid]})
        rows.append({
            "target": target,
            "arity": arity,
            "target_arity_key": f"{target}/{arity}",
            "resolution_state": obligation.get("resolution_state"),
            "effect_boundary": bool(obligation.get("effect_boundary")),
            "signature_nodes": nodes,
            "covered_component_ids": covered,
            "covered_component_count": len(covered),
            "covered_symbolic_node_count": len(covered_nodes),
            "covered_symbolic_nodes": covered_nodes,
            "execution_admitted": False,
            "effect_authority": "NONE",
            "truth_authority": "NONE",
        })

    # Deterministic greedy set cover over only components reachable from call signature nodes.
    uncovered = set(call_components)
    selected = []
    by_key = {row["target_arity_key"]: row for row in rows}
    while uncovered:
        candidates = []
        for row in rows:
            gain = sorted(uncovered & set(row["covered_component_ids"]))
            if gain:
                candidates.append((
                    -len(gain),
                    -sum(len(components[cid]) for cid in gain),
                    row["target_arity_key"],
                    gain,
                ))
        if not candidates:
            raise AnchorPlanError(f"uncoverable call-associated components: {sorted(uncovered)}")
        candidates.sort()
        _, _, key, gain = candidates[0]
        selected.append({
            "target_arity_key": key,
            "newly_covered_component_ids": gain,
            "newly_covered_symbolic_node_count": sum(len(components[cid]) for cid in gain),
        })
        uncovered -= set(gain)

    ranked = sorted(
        rows,
        key=lambda row: (
            -row["covered_component_count"],
            -row["covered_symbolic_node_count"],
            row["target_arity_key"],
        ),
    )
    core = {
        "schema": SCHEMA,
        "source_constraint_graph_sha256": graph.get("constraint_graph_sha256"),
        "component_count": len(components),
        "call_associated_component_ids": sorted(call_components),
        "call_associated_component_count": len(call_components),
        "ranked_signature_anchor_leverage": ranked,
        "greedy_signature_set_cover": selected,
        "invariants": {
            "concrete_type_invention": "FORBIDDEN",
            "anchor_plan_promotes_signature": "FORBIDDEN",
            "anchor_plan_admits_execution": "FORBIDDEN",
            "type_name_resemblance_is_anchor": "FORBIDDEN",
            "effect_boundary_requires_separate_sealed_runtime_binding": "REQUIRED",
        },
    }
    return {
        **core,
        "anchor_plan_sha256": digest(core),
        "summary": {
            "type_equality_components": len(components),
            "call_associated_components": len(call_components),
            "greedy_signature_contracts_for_call_component_cover": len(selected),
            "max_components_covered_by_one_signature": max(row["covered_component_count"] for row in rows),
            "max_symbolic_nodes_covered_by_one_signature": max(row["covered_symbolic_node_count"] for row in rows),
            "execution_admitted_calls": 0,
            "effect_authority": "NONE",
            "truth_authority": "NONE",
        },
        "promotion": "NONE",
    }
