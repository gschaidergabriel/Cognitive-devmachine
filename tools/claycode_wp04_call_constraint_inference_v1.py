#!/usr/bin/env python3
"""WP04 research candidate: exact call-site constraints without invented signatures.

The real G9 cycle currently contains calls but V18 does not provide declared typed function
signatures for them. This extractor preserves that negative result instead of guessing return
or parameter types. It derives only evidence available in the canonical CycleRegionIR:
exact target+arity identity, argument shape, nesting, assignment/dataflow use and explicit
constructor-name resemblance. Those observations become symbolic unification constraints.

A target that merely resembles a record/type name is NOT promoted to a constructor contract;
unqualified/suffix/basename matches are never signatures. `Needle.execute/1` is kept as the
separate source-observed effect-boundary obligation but receives no authority. No call is
execution-admitted by this layer.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Any

import claycode_wp03_cycle_ir_v1 as cycle_ir

SCHEMA = "ClayCodeCallConstraintGraph/v1-research"
DOMAIN = b"ClayCodeCallConstraintGraph/v1-research\x00"
OCC_DOMAIN = b"ClayCodeCallOccurrence/v1\x00"
CONSTRAINT_DOMAIN = b"ClayCodeCallTypeConstraint/v1\x00"
CONDITION_PATH_SENTINEL = -1
THEN_REGION_PATH_SENTINEL = -2


class CallConstraintError(ValueError):
    pass


def stable_json(v: Any) -> bytes:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(domain: bytes, v: Any) -> str:
    return hashlib.sha256(domain + stable_json(v)).hexdigest()


def semantic_children(node: Any) -> list[dict[str, Any]]:
    if not isinstance(node, dict):
        return []
    return [c for c in node.get("children", []) if isinstance(c, dict) and (c.get("kind") or c.get("token"))]


def node_kind(node: Any) -> str | None:
    return node.get("kind") if isinstance(node, dict) and isinstance(node.get("kind"), str) else None


def qid_text(node: dict[str, Any]) -> str:
    return cycle_ir.qid(node)


def call_parts(node: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    if node_kind(node) != "call":
        raise CallConstraintError("call node required")
    kids = [c for c in semantic_children(node) if c.get("kind")]
    if not kids or node_kind(kids[0]) != "qid":
        raise CallConstraintError("call must begin with qid")
    return qid_text(kids[0]), kids[1:]


def unwrap_single_expr(node: dict[str, Any]) -> dict[str, Any]:
    cur = node
    while node_kind(cur) == "expr":
        kids = [c for c in semantic_children(cur) if c.get("kind")]
        if len(kids) != 1:
            return cur
        cur = kids[0]
    return cur


def arg_shape(node: dict[str, Any]) -> dict[str, Any]:
    unwrapped = unwrap_single_expr(node)
    k = node_kind(unwrapped)
    if k == "qid":
        return {"kind": "SYMBOL", "symbol": qid_text(unwrapped)}
    if k == "call":
        target, args = call_parts(unwrapped)
        return {"kind": "CALL_RESULT", "target": target, "arity": len(args)}
    if k == "postfix_optional":
        return {"kind": "OPTIONAL_EXPR", "tokens": cycle_ir.tokens(unwrapped)}
    if k == "expr":
        return {"kind": "EXPR", "tokens": cycle_ir.tokens(unwrapped)}
    if k in {"list", "set"}:
        return {"kind": k.upper(), "tokens": cycle_ir.tokens(unwrapped)}
    if "token" in unwrapped:
        return {"kind": "LITERAL_OR_TOKEN", "token": unwrapped.get("token"), "value": unwrapped.get("value")}
    return {"kind": "OTHER", "ast_kind": k, "tokens": cycle_ir.tokens(unwrapped)}


def declared_function_keys(typed_ir: dict[str, Any]) -> set[tuple[str, int]]:
    """Return only exact declaration identities. No suffix/basename matching."""
    out: set[tuple[str, int]] = set()
    for decl in typed_ir.get("declarations", []):
        if not isinstance(decl, dict):
            continue
        if decl.get("kind") == "function" and isinstance(decl.get("name"), str):
            out.add((decl["name"], len(decl.get("params", []))))
        if decl.get("kind") == "interface" and isinstance(decl.get("name"), str):
            iface = decl["name"]
            for method in decl.get("methods", []):
                if isinstance(method, dict) and isinstance(method.get("name"), str):
                    out.add((f"{iface}.{method['name']}", len(method.get("params", []))))
    return out


def declared_type_names(typed_ir: dict[str, Any]) -> set[str]:
    names = set()
    for row in typed_ir.get("types", []):
        if isinstance(row, dict) and isinstance(row.get("name"), str):
            names.add(row["name"])
    for row in typed_ir.get("declarations", []):
        if isinstance(row, dict) and isinstance(row.get("name"), str) and row.get("kind") in {"record", "sum_type"}:
            names.add(row["name"])
    return names


def iter_cycle_ops(region: dict[str, Any], *, prefix: tuple[int, ...] = ()):
    """Yield each op with an ancestor-preserving structural path.

    Paths are stable semantic location evidence, not execution authority. `-2` marks descent
    into an IF then-region; `-1` is reserved by the caller for the IF condition. Keeping the
    ancestor path prevents nested regions from reusing top-level `(0,)`, `(1,)`, ... paths.
    """
    for op_index, op in enumerate(region.get("ops", [])):
        if not isinstance(op, dict):
            continue
        op_path = prefix + (op_index,)
        yield op_path, op
        if op.get("kind") == "IF":
            then_region = op.get("then_region")
            if not isinstance(then_region, dict):
                raise CallConstraintError("IF op missing then_region")
            yield from iter_cycle_ops(then_region, prefix=op_path + (THEN_REGION_PATH_SENTINEL,))


def collect_calls(cycle: dict[str, Any], typed_ir: dict[str, Any]) -> dict[str, Any]:
    exact_declared = declared_function_keys(typed_ir)
    type_names = declared_type_names(typed_ir)
    occurrences: list[dict[str, Any]] = []
    constraints: list[dict[str, Any]] = []
    symbol_sources: dict[str, str] = {}

    def add_constraint(lhs: str, rhs: str, reason: str, evidence: dict[str, Any]) -> None:
        core = {"lhs": lhs, "rhs": rhs, "relation": "TYPE_EQUALITY", "reason": reason, "evidence": evidence}
        constraints.append({**core, "constraint_sha256": sha256(CONSTRAINT_DOMAIN, core)})

    def visit(node: dict[str, Any], *, op: dict[str, Any], path: tuple[int, ...], parent_call: tuple[str, int] | None, assigned_root: bool) -> None:
        k = node_kind(node)
        if k == "call":
            target, args = call_parts(node)
            identity = (target, len(args))
            occ_index = len(occurrences)
            return_var = f"ret:{target}/{len(args)}"
            arg_shapes = [arg_shape(arg) for arg in args]
            assignment_target = op.get("target") if assigned_root and op.get("kind") == "ASSIGN" else None
            exact_match = identity in exact_declared
            resemblance = target if target in type_names else None
            effect_boundary = target == "Needle.execute" and len(args) == 1
            resolution = (
                "DECLARED_SIGNATURE_EXACT_NONEXECUTABLE_UNTIL_BINDING"
                if exact_match else
                "EFFECT_BOUNDARY_SIGNATURE_MISSING"
                if effect_boundary else
                "UNRESOLVED_SIGNATURE"
            )
            core = {
                "occurrence_index": occ_index,
                "target": target,
                "arity": len(args),
                "target_arity_key": f"{target}/{len(args)}",
                "op_semantic_id": op.get("op_semantic_id"),
                "path": list(path),
                "parent_call": None if parent_call is None else {"target": parent_call[0], "arity": parent_call[1]},
                "assignment_target": assignment_target,
                "argument_shapes": arg_shapes,
                "resolution_state": resolution,
                "exact_declared_match": exact_match,
                "type_name_resemblance": resemblance,
                "effect_boundary": effect_boundary,
                "execution_admitted": False,
                "effect_authority": "NONE",
                "truth_authority": "NONE",
            }
            occ_hash = sha256(OCC_DOMAIN, core)
            occurrences.append({**core, "occurrence_sha256": occ_hash})

            if assignment_target:
                symbol_sources[assignment_target] = return_var
                add_constraint(return_var, f"var:{assignment_target}", "ASSIGNMENT_RESULT", {"occurrence_sha256": occ_hash})

            for arg_index, (arg, shape) in enumerate(zip(args, arg_shapes)):
                param_var = f"param:{target}/{len(args)}#{arg_index}"
                unwrapped = unwrap_single_expr(arg)
                if shape["kind"] == "SYMBOL":
                    add_constraint(f"var:{shape['symbol']}", param_var, "DIRECT_SYMBOL_ARGUMENT", {"occurrence_sha256": occ_hash, "arg_index": arg_index})
                elif shape["kind"] == "CALL_RESULT":
                    add_constraint(f"ret:{shape['target']}/{shape['arity']}", param_var, "DIRECT_NESTED_CALL_RESULT", {"occurrence_sha256": occ_hash, "arg_index": arg_index})
                else:
                    add_constraint(f"expr:{occ_hash}#{arg_index}", param_var, "STRUCTURAL_EXPRESSION_ARGUMENT", {"occurrence_sha256": occ_hash, "arg_index": arg_index, "shape": shape["kind"]})
                visit(unwrapped, op=op, path=path + (arg_index,), parent_call=identity, assigned_root=False)
            return

        for child_index, child in enumerate(semantic_children(node)):
            if child.get("kind"):
                visit(child, op=op, path=path + (child_index,), parent_call=parent_call, assigned_root=False)

    for op_path, op in iter_cycle_ops(cycle["region"]):
        if op.get("kind") == "ASSIGN":
            rhs = unwrap_single_expr(op["rhs_ast"])
            visit(rhs, op=op, path=op_path, parent_call=None, assigned_root=node_kind(rhs) == "call")
        elif op.get("kind") == "EXPR":
            expr = unwrap_single_expr(op["expr_ast"])
            visit(expr, op=op, path=op_path, parent_call=None, assigned_root=False)
        elif op.get("kind") == "IF":
            # Calls in conditions are inventoried too; current G9 conditions contain none.
            visit(
                op["condition_ast"],
                op=op,
                path=op_path + (CONDITION_PATH_SENTINEL,),
                parent_call=None,
                assigned_root=False,
            )

    # Deduplicate constraints by semantic content while preserving deterministic order.
    unique = {row["constraint_sha256"]: row for row in constraints}
    constraints = [unique[key] for key in sorted(unique)]

    # Deterministic connected components of symbolic type-equality constraints.
    graph: dict[str, set[str]] = defaultdict(set)
    for row in constraints:
        a, b = row["lhs"], row["rhs"]
        graph[a].add(b); graph[b].add(a)
    seen: set[str] = set(); components = []
    for start in sorted(graph):
        if start in seen:
            continue
        stack = [start]; comp = []
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur); comp.append(cur)
            stack.extend(sorted(graph[cur] - seen, reverse=True))
        components.append(sorted(comp))

    pair_counts = Counter((x["target"], x["arity"]) for x in occurrences)
    obligations = []
    for target, arity in sorted(pair_counts):
        rows = [x for x in occurrences if x["target"] == target and x["arity"] == arity]
        if len({x["resolution_state"] for x in rows}) != 1:
            raise CallConstraintError(f"non-deterministic resolution state for {target}/{arity}")
        obligations.append({
            "identity": {"target": target, "arity": arity},
            "occurrences": pair_counts[(target, arity)],
            "resolution_state": rows[0]["resolution_state"],
            "type_name_resemblance": rows[0]["type_name_resemblance"],
            "effect_boundary": rows[0]["effect_boundary"],
            "execution_admitted": False,
        })

    core = {
        "schema": SCHEMA,
        "cycle_semantic_id": cycle.get("cycle_semantic_id"),
        "source_typed_ir_sha256": typed_ir.get("typed_ir_sha256"),
        "occurrences": occurrences,
        "obligations": obligations,
        "constraints": constraints,
        "type_equality_components": components,
        "invariants": {
            "fuzzy_or_suffix_signature_resolution": "FORBIDDEN",
            "type_name_resemblance_promotes_constructor": "FORBIDDEN",
            "unresolved_call_executes": "FORBIDDEN",
            "constraint_graph_mints_effect_authority": "FORBIDDEN",
            "constraint_graph_mints_truth_authority": "FORBIDDEN",
            "nested_region_path_collision": "FORBIDDEN",
        },
    }
    graph_hash = sha256(DOMAIN, core)
    return {
        **core,
        "constraint_graph_sha256": graph_hash,
        "summary": {
            "call_site_occurrences": len(occurrences),
            "unique_target_arities": len(obligations),
            "exact_declared_matches": sum(1 for x in obligations if x["resolution_state"] == "DECLARED_SIGNATURE_EXACT_NONEXECUTABLE_UNTIL_BINDING"),
            "unresolved_signatures": sum(1 for x in obligations if x["resolution_state"] == "UNRESOLVED_SIGNATURE"),
            "effect_boundary_missing_signatures": sum(1 for x in obligations if x["resolution_state"] == "EFFECT_BOUNDARY_SIGNATURE_MISSING"),
            "type_name_resemblance_only": sum(1 for x in obligations if x["type_name_resemblance"] is not None),
            "type_equality_constraints": len(constraints),
            "type_equality_components": len(components),
            "execution_admitted_calls": 0,
            "effect_authority": "NONE",
            "truth_authority": "NONE",
        },
        "promotion": "NONE",
        "wp03_status": "OPEN",
    }
