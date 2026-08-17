#!/usr/bin/env python3
"""ClayCode CC-WP-03/04 rule_decl + invariant_decl class-specific legality candidate.

Consumes preserved canonical residual AST; never reparses source. It lowers the two dominant
residual classes into an explicit symbolic constraint IR. The IR is descriptive/pure and can
be consumed only by the paired symbolic constraint evaluator; it never carries effect
authority. Unsupported/malformed constructs fail closed and remain non-executable.

Candidate evidence only: target-VPS execution and current-component binding are required
before any package promotion.
"""
from __future__ import annotations
import hashlib, json
from typing import Any

SCHEMA = "ClayCodeRuleInvariantLegality/v1"
DOMAIN = b"ClayCodeRuleInvariantLegality/v1\x00"
LOWERED = "LOWERED_AND_VALIDATED"
DEFERRED = "EXPLICITLY_DEFERRED_FAIL_CLOSED"
REJECTED = "REJECTED_WITH_REASON"
SUPPORTED_CLASSES = {"rule_decl", "invariant_decl"}

ALLOWED_NODE_KINDS = {
    "rule_decl", "invariant_decl", "expr", "operator", "infix_relop", "prefix_relop",
    "postfix_relop", "prefix_relation", "postfix_relation", "qid", "call", "list", "set",
    "postfix_optional", "primary",
}
ALLOWED_CONNECTORS = {
    ">=", "<=", "!=", "==", "->", "=>", ">", "<", "=", "|", "+", "-", "*", "/",
    "&&", "||", "or", "iff", "requires", "in", "subset_of",
    "preserves", "required_before", "never_implies", "never_requires", "may_reference",
    "never_confers", "returns", "loads", "cannot_authorize", "distinct_from", "lowers",
    "owns", "lifecycle", "consumes", "writes", "includes",
    "cannot_be_silently_averaged_away", "is_explanation_of_derivation", "roles_are_typed",
    "outside_stable_prefix", "must_be_preserved_unless_counterevidence",
    "personalizes_for_Andreas_when_FRANK_target", "preserves_general_transfer_variants",
    "4B_emits", "4B_need_not_learn", "Needle.lowers", "Needle.owns",
}
PUNCT = {".", "(", ")", "[", "]", "{", "}", ",", "?", "="}
SCALAR_TOKEN_TYPES = {"NAME", "REF", "SIGNED_NUMBER", "STRING", "BOOLEAN"}

class LegalityError(ValueError):
    pass

def stable_json(v: Any) -> bytes:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def kind(n: Any) -> str | None:
    return n.get("kind") if isinstance(n, dict) else None

def children(n: Any) -> list[Any]:
    if not isinstance(n, dict) or not isinstance(n.get("children"), list):
        raise LegalityError("AST node missing children list")
    return n["children"]

def token(n: Any) -> tuple[str, str] | None:
    if isinstance(n, dict) and "token" in n:
        return str(n["token"]), str(n.get("value", ""))
    return None

def walk(n: Any):
    yield n
    if isinstance(n, dict) and isinstance(n.get("children"), list):
        for c in n["children"]:
            yield from walk(c)

def _connector_values(n: Any) -> list[str]:
    vals=[]
    for x in walk(n):
        k=kind(x)
        if k in {"operator","infix_relop","prefix_relop","postfix_relop"}:
            for c in children(x):
                t=token(c)
                if t: vals.append(t[1])
        elif k in {"prefix_relation", "postfix_relation"}:
            for c in children(x):
                t=token(c)
                if t and ("REL" in t[0] or t[1] in ALLOWED_CONNECTORS): vals.append(t[1])
    return vals

def _validate_ast(n: Any) -> None:
    for x in walk(n):
        t=token(x)
        if t is not None:
            typ,val=t
            if typ in SCALAR_TOKEN_TYPES or val in PUNCT or val in ALLOWED_CONNECTORS or typ in {"RULE","INVARIANT","DOT","LPAR","RPAR","LSQB","RSQB","LBRACE","RBRACE","COMMA","QMARK"}:
                continue
            if val in {"rule","invariant"}:
                continue
            raise LegalityError(f"unsupported token in rule/invariant AST: {typ}:{val}")
        k=kind(x)
        if k is not None and k not in ALLOWED_NODE_KINDS:
            raise LegalityError(f"unsupported AST node kind: {k}")
    bad=[v for v in _connector_values(n) if v not in ALLOWED_CONNECTORS]
    if bad:
        raise LegalityError(f"unsupported connector(s): {bad}")

def lower_residual(residual: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(residual, dict):
        raise LegalityError("residual must be object")
    cls=residual.get("kind")
    if cls not in SUPPORTED_CLASSES:
        return {"kind": cls, "status": DEFERRED, "evaluator_lowering": "DENY", "effect_authority": "NONE", "reason": "class not handled by rule/invariant legality v1"}
    ast=residual.get("canonical_ast")
    if not isinstance(ast, dict) or kind(ast)!=cls:
        raise LegalityError(f"{cls} residual canonical_ast must have matching root kind")
    payload=[c for c in children(ast) if kind(c) in {"expr","qid","call","prefix_relation","postfix_relation"}]
    if len(payload)!=1:
        raise LegalityError(f"{cls} requires exactly one semantic payload, got {len(payload)}")
    _validate_ast(ast)
    constraint_core={
        "constraint_schema": "ClayCodeSymbolicConstraint/v1",
        "source_class": cls,
        "payload_ast": payload[0],
        "connectors": _connector_values(payload[0]),
        "effect_class": "PURE_DECLARATIVE_CONSTRAINT",
        "effect_authority": "NONE",
        "execution_authority": "NONE",
    }
    h=sha256(b"ClayCodeSymbolicConstraint/v1\x00"+stable_json(constraint_core))
    return {
        "kind": cls,
        "status": LOWERED,
        "checker": SCHEMA,
        "evaluator_lowering": "ALLOW_SYMBOLIC_CONSTRAINT_ONLY",
        "effect_authority": "NONE",
        "constraint": constraint_core,
        "constraint_sha256": h,
    }

def lower_rows(residuals: list[dict[str, Any]]) -> dict[str, Any]:
    rows=[]
    for i,r in enumerate(residuals):
        try:
            out=lower_residual(r)
            rows.append({"index":i, **out})
        except LegalityError as exc:
            rows.append({"index":i,"kind": r.get("kind") if isinstance(r,dict) else None,"status":REJECTED,"checker":SCHEMA,"evaluator_lowering":"DENY","effect_authority":"NONE","reason":str(exc)})
    counts={s:sum(1 for r in rows if r["status"]==s) for s in (LOWERED,DEFERRED,REJECTED)}
    core={"schema":SCHEMA,"rows":rows,"summary":{**counts,"total":len(rows),"effect_authority":"NONE"}}
    return {**core,"receipt_sha256":sha256(DOMAIN+stable_json(core)),"promotion":"NONE"}

def validate_receipt(receipt: dict[str, Any]) -> None:
    rows=receipt.get("rows")
    if not isinstance(rows,list): raise LegalityError("rows missing")
    for r in rows:
        if r.get("effect_authority")!="NONE": raise LegalityError("rule/invariant checker minted effect authority")
        st=r.get("status")
        if st==LOWERED:
            if r.get("evaluator_lowering")!="ALLOW_SYMBOLIC_CONSTRAINT_ONLY": raise LegalityError("lowered row has wrong evaluator gate")
            c=r.get("constraint")
            if not isinstance(c,dict) or c.get("effect_authority")!="NONE" or c.get("execution_authority")!="NONE": raise LegalityError("lowered constraint authority violation")
            expected=sha256(b"ClayCodeSymbolicConstraint/v1\x00"+stable_json(c))
            if r.get("constraint_sha256")!=expected: raise LegalityError("constraint hash tamper")
        elif st in {DEFERRED,REJECTED}:
            if r.get("evaluator_lowering")!="DENY": raise LegalityError("non-lowered row admitted to evaluator")
        else: raise LegalityError(f"unknown status {st!r}")

def symbolic_consume(row: dict[str, Any]) -> dict[str, Any]:
    """WP05-facing consumption boundary: produces a data-only plan, never an effect."""
    if row.get("status")!=LOWERED or row.get("evaluator_lowering")!="ALLOW_SYMBOLIC_CONSTRAINT_ONLY":
        raise LegalityError("symbolic evaluator rejects non-lowered residual")
    if row.get("effect_authority")!="NONE": raise LegalityError("authority violation")
    c=row.get("constraint")
    if not isinstance(c,dict): raise LegalityError("constraint missing")
    expected=sha256(b"ClayCodeSymbolicConstraint/v1\x00"+stable_json(c))
    if row.get("constraint_sha256")!=expected: raise LegalityError("constraint hash mismatch")
    plan={"plan_schema":"ClayCodeSymbolicConstraintPlan/v1","constraint_sha256":expected,"mode":"DATA_ONLY_SYMBOLIC_CONSUMPTION","effect_authority":"NONE","execution_authority":"NONE"}
    return {**plan,"plan_sha256":sha256(b"ClayCodeSymbolicConstraintPlan/v1\x00"+stable_json(plan))}
