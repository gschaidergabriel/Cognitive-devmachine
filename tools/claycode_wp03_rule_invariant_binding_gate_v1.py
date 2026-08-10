#!/usr/bin/env python3
"""CC-WP-03/WP04 candidate: explicit-binding legality gate for rule/invariant semantics.

V18 intentionally preserves a flat operator-chain grammar. Prior executable research showed
that silently choosing evaluator precedence can change meaning materially. This gate therefore
lowers rule_decl/invariant_decl only when binding is explicit from AST structure or when one
operator/relation repeats at the same expression level and can be represented as an ordered
N-ary chain without inventing cross-operator precedence.

Mixed operator/relation classes on one flat expr level are rejected fail-closed as
AMBIGUOUS_BINDING. Parenthesized source survives frontend normalization as nested expr nodes,
so explicit grouping can resolve these cases without widening grammar or guessing precedence.

This is declarative lowering only. It never executes calls/tools, proves truth, or mints effect
or bearer authority. Candidate only: no WP03/WP04/WP05 promotion is implied.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

SCHEMA = "ClayCodeDeclarativeBindingIR/v1"
DOMAIN = b"ClayCodeDeclarativeBindingIR/v1\x00"
BUNDLE_DOMAIN = b"ClayCodeDeclarativeBindingBundle/v1\x00"
SUPPORTED = {"rule_decl": "RULE", "invariant_decl": "INVARIANT"}
PUNCT = {"(", ")", "[", "]", "{", "}", ","}


class BindingError(ValueError):
    pass


def stable_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def children(node: Any) -> list[Any]:
    if not isinstance(node, dict):
        return []
    value = node.get("children", [])
    if not isinstance(value, list):
        raise BindingError("canonical AST children must be a list")
    return value


def token(node: Any) -> tuple[str, str] | None:
    if not isinstance(node, dict) or "token" not in node:
        return None
    typ = node.get("token")
    value = node.get("value")
    if not isinstance(typ, str) or not isinstance(value, (str, int, float, bool)):
        raise BindingError("canonical token requires scalar value and string token type")
    return typ, str(value)


def kind(node: Any) -> str | None:
    return node.get("kind") if isinstance(node, dict) and isinstance(node.get("kind"), str) else None


def token_values(node: Any) -> list[str]:
    out: list[str] = []
    pending = [node]
    while pending:
        cur = pending.pop()
        t = token(cur)
        if t is not None:
            out.append(t[1])
            continue
        pending.extend(reversed(children(cur)))
    return out


def qid(node: Any) -> str:
    if kind(node) != "qid":
        raise BindingError(f"qid node required, got {kind(node)!r}")
    vals = token_values(node)
    if not vals:
        raise BindingError("empty qid")
    if "." in vals:
        text = "".join(vals)
    else:
        text = ".".join(v for v in vals if v not in PUNCT)
    if not text:
        raise BindingError("empty canonical qid text")
    return text


def relation_name(node: Any) -> str:
    vals = [v for v in token_values(node) if v not in PUNCT]
    if len(vals) != 1:
        raise BindingError(f"relation/operator wrapper must contain one semantic token: {vals!r}")
    return vals[0]


def raw_token_value(node: Any) -> str | None:
    t = token(node)
    return t[1] if t is not None else None


def _literal_from_token(node: dict[str, Any]) -> dict[str, Any]:
    typ, value = token(node) or ("", "")
    if typ == "SIGNED_NUMBER":
        parsed: Any = float(value) if any(ch in value for ch in ".eE") else int(value)
        return {"k": "literal", "type": "Number", "value": parsed}
    if typ == "BOOLEAN":
        return {"k": "literal", "type": "Bool", "value": value == "true"}
    if typ == "STRING":
        return {"k": "literal", "type": "String", "value": value}
    if typ == "REF":
        return {"k": "ref", "value": value}
    if value in PUNCT:
        raise BindingError(f"punctuation token cannot be standalone semantic term: {value!r}")
    return {"k": "symbol", "name": value}


def _semantic_children(node: Any, *, drop: set[str]) -> list[Any]:
    out = []
    for child in children(node):
        value = raw_token_value(child)
        if value in drop:
            continue
        out.append(child)
    return out


def lower_term(node: Any) -> dict[str, Any]:
    t = token(node)
    if t is not None:
        return _literal_from_token(node)

    k = kind(node)
    if k == "qid":
        return {"k": "symbol", "name": qid(node)}
    if k == "call":
        parts = _semantic_children(node, drop={"(", ")", ","})
        if not parts or kind(parts[0]) != "qid":
            raise BindingError("call must start with qid")
        return {"k": "call_descriptor", "name": qid(parts[0]), "args": [lower_term(x) for x in parts[1:]], "execution": "FORBIDDEN"}
    if k in {"list", "set"}:
        parts = _semantic_children(node, drop={"[", "]", "{", "}", ","})
        return {"k": k, "items": [lower_term(x) for x in parts]}
    if k == "postfix_optional":
        parts = _semantic_children(node, drop={"?"})
        if len(parts) != 1 or kind(parts[0]) != "qid":
            raise BindingError("postfix_optional requires exactly one qid")
        return {"k": "optional_symbol", "name": qid(parts[0])}
    if k == "prefix_relation":
        parts = children(node)
        if len(parts) != 2:
            raise BindingError("prefix_relation must have relation and operand")
        rel = relation_name(parts[0]) if kind(parts[0]) == "prefix_relop" else raw_token_value(parts[0])
        if not rel:
            raise BindingError("prefix relation token missing")
        return {"k": "prefix_relation", "relation": rel, "operand": lower_term(parts[1]), "truth_authority": "NONE", "effect_authority": "NONE"}
    if k == "postfix_relation":
        parts = children(node)
        if len(parts) != 2 or kind(parts[1]) != "postfix_relop":
            raise BindingError("postfix_relation must have operand and postfix relation")
        return {"k": "postfix_relation", "relation": relation_name(parts[1]), "operand": lower_term(parts[0]), "truth_authority": "NONE", "effect_authority": "NONE"}
    if k == "expr":
        return lower_expr(node)
    if k is not None and k.startswith("ident_"):
        vals = token_values(node)
        if len(vals) != 1:
            raise BindingError(f"malformed identifier alias {k}: {vals!r}")
        return {"k": "symbol", "name": vals[0]}
    if k == "primary":
        parts = _semantic_children(node, drop={"(", ")"})
        if len(parts) != 1:
            raise BindingError("primary grouping must contain one semantic child")
        return lower_term(parts[0])
    raise BindingError(f"unsupported declarative term kind: {k!r}")


def lower_expr(node: Any) -> dict[str, Any]:
    if kind(node) != "expr":
        return lower_term(node)
    parts = children(node)
    if not parts:
        raise BindingError("empty expr")
    operands = [lower_term(parts[0])]
    operators: list[dict[str, Any]] = []
    i = 1
    while i < len(parts):
        op_node = parts[i]
        op_kind = kind(op_node)
        if op_kind not in {"operator", "infix_relop"}:
            raise BindingError(f"expected operator/relation wrapper at expr index {i}, got {op_kind!r}/{raw_token_value(op_node)!r}")
        op = relation_name(op_node)
        op_class = "INFIX_RELATION" if op_kind == "infix_relop" else "OPERATOR"
        i += 1
        explicit_marker = False
        if op_kind == "infix_relop" and i < len(parts) and raw_token_value(parts[i]) == "=":
            explicit_marker = True
            i += 1
        if i >= len(parts):
            raise BindingError(f"dangling operator/relation {op!r}")
        operators.append({"name": op, "class": op_class, "explicit_equals_marker": explicit_marker})
        operands.append(lower_term(parts[i]))
        i += 1

    if not operators:
        if len(operands) != 1:
            raise BindingError("operator-free expr has multiple operands")
        return operands[0]

    signature = [(op["class"], op["name"], op["explicit_equals_marker"]) for op in operators]
    same_binding = all(item == signature[0] for item in signature)
    if not same_binding:
        return {
            "k": "ambiguous_flat_chain",
            "binding_status": "AMBIGUOUS_BINDING",
            "operands": operands,
            "operators": operators,
            "reason": "mixed operator/relation binding on one V18 flat expr level requires explicit grouping or separately frozen precedence semantics",
        }

    op = operators[0]
    return {
        "k": "nary_chain" if len(operators) > 1 else "binary_relation",
        "binding_status": "EXPLICIT_SINGLE_BINDING_CLASS",
        "operator": op,
        "operands": operands,
        "ordered": True,
    }


def has_ambiguity(plan: Any) -> bool:
    if isinstance(plan, dict):
        if plan.get("binding_status") == "AMBIGUOUS_BINDING":
            return True
        return any(has_ambiguity(v) for v in plan.values())
    if isinstance(plan, list):
        return any(has_ambiguity(v) for v in plan)
    return False


def lower_clause(row: dict[str, Any], *, index: int) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise BindingError("residual clause row must be object")
    k = row.get("kind")
    if k not in SUPPORTED:
        raise BindingError(f"unsupported clause kind: {k!r}")
    ast = row.get("canonical_ast")
    if not isinstance(ast, dict) or ast.get("kind") != k:
        raise BindingError("residual clause/root kind mismatch")
    parts = children(ast)
    if len(parts) != 2:
        raise BindingError(f"{k} must contain keyword and exactly one expression")
    keyword = raw_token_value(parts[0])
    expected = "rule" if k == "rule_decl" else "invariant"
    if keyword != expected:
        raise BindingError(f"{k} keyword mismatch: {keyword!r}")
    plan = lower_term(parts[1])
    ambiguous = has_ambiguity(plan)
    core = {
        "schema": SCHEMA,
        "clause_kind": SUPPORTED[k],
        "plan": plan,
        "source_residual_sha256": sha256(stable_json(row)),
        "binding_status": "REJECTED_AMBIGUOUS_BINDING" if ambiguous else "LOWERED_AND_VALIDATED_EXPLICIT_BINDING",
        "effect_authority": "NONE",
        "truth_authority": "NONE",
        "runtime_call_execution": "FORBIDDEN",
    }
    sem = sha256(DOMAIN + stable_json(core))
    return {"index": index, **core, "binding_semantic_sha256": sem, "binding_id": f"binding:{sem}"}


def lower_bundle(typed_ir: dict[str, Any]) -> dict[str, Any]:
    opaque = typed_ir.get("opaque_unlowered_semantics")
    if not isinstance(opaque, list):
        raise BindingError("TypedIR must expose opaque_unlowered_semantics")
    clauses = []
    for index, row in enumerate(opaque):
        if isinstance(row, dict) and row.get("kind") in SUPPORTED:
            clauses.append(lower_clause(row, index=index))
    accepted = [c for c in clauses if c["binding_status"] == "LOWERED_AND_VALIDATED_EXPLICIT_BINDING"]
    rejected = [c for c in clauses if c["binding_status"] != "LOWERED_AND_VALIDATED_EXPLICIT_BINDING"]
    core = {
        "schema": SCHEMA,
        "source_typed_ir_sha256": typed_ir.get("typed_ir_sha256"),
        "clauses": clauses,
        "summary": {
            "total": len(clauses),
            "accepted": len(accepted),
            "rejected_ambiguous": len(rejected),
            "kind_counts": dict(sorted(Counter(c["clause_kind"] for c in clauses).items())),
            "implicit_execution_count": 0,
            "effect_authority": "NONE",
            "truth_authority": "NONE",
        },
    }
    return {
        **core,
        "bundle_sha256": sha256(BUNDLE_DOMAIN + stable_json(core)),
        "accepted_registry": [
            {
                "binding_id": c["binding_id"],
                "binding_semantic_sha256": c["binding_semantic_sha256"],
                "clause_kind": c["clause_kind"],
                "effect_authority": "NONE",
                "truth_authority": "NONE",
            }
            for c in accepted
        ],
        "rejected": [
            {
                "index": c["index"],
                "binding_id": c["binding_id"],
                "reason": "AMBIGUOUS_BINDING",
            }
            for c in rejected
        ],
        "promotion": "NONE",
        "wp03_status": "OPEN_UNTIL_AMBIGUOUS_BINDINGS_RESOLVED_AND_EXACT_CURRENT_EXECUTION_PASSES",
    }
