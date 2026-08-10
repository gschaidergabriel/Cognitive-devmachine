#!/usr/bin/env python3
"""CC-WP-03/WP04/WP05 candidate: typed declarative ClauseIR for rule/invariant residuals.

The current receipt-bound WP03 bridge preserves admitted non-declaration semantics in
`opaque_unlowered_semantics`. This candidate lowers only `rule_decl` and `invariant_decl`
into a deterministic declarative ClauseIR, validates their V18 canonical-AST envelope, and
provides a fail-closed consumer boundary.

Scope is deliberately narrow:
- a lowered clause is descriptive/declarative state, never bearer/effect authority;
- rule/invariant admission does not execute tools, mutate external state or prove truth;
- unknown residual classes remain outside this lowerer;
- malformed relation-token tampering fails closed;
- every material receipt is bound to the current repo/control/compiler component revision so
  stale successful executions cannot close current work.

This file is a research/build candidate. It does not itself promote WP03/WP04/WP05.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any, Iterable

SCHEMA = "ClayCodeDeclarativeClauseIR/v1"
DOMAIN = b"ClayCodeDeclarativeClauseIR/v1\x00"
RECEIPT_DOMAIN = b"ClayCodeDeclarativeClauseReceipt/v1\x00"
CONSUMER_DOMAIN = b"ClayCodeDeclarativeClauseConsumer/v1\x00"
SUPPORTED_KINDS = {"rule_decl": "RULE", "invariant_decl": "INVARIANT"}
REQUIRED_WORK_REVISION_FIELDS = (
    "repo_head","supervisor_blob_sha","steering_ref","steering_blob_sha",
    "frontend_blob_sha","grammar_blob_sha","typed_ir_blob_sha","residual_builder_blob_sha",
)
PREFIX_RELATIONS = {"4B_emits", "4B_need_not_learn"}
DOTTED_PREFIX_RELATIONS = {"Needle.lowers", "Needle.owns"}
POSTFIX_RELATIONS = {
    "cannot_be_silently_averaged_away","is_explanation_of_derivation","roles_are_typed",
    "outside_stable_prefix","must_be_preserved_unless_counterevidence",
    "personalizes_for_Andreas_when_FRANK_target","preserves_general_transfer_variants",
}
INFIX_RELATIONS = {
    "preserves","required_before","never_implies","never_requires","may_reference",
    "never_confers","returns","loads","cannot_authorize","distinct_from","lowers","owns",
    "lifecycle","consumes","writes","includes",
}
CORE_OPERATORS = {
    ">=","<=","!=","==","->","=>",">","<","=","|","+","-","*","/",
    "&&","||","or","iff","requires","in","subset_of",
}
RELATION_TOKEN_TYPES = {"PREFIX_REL","DOTTED_PREFIX_REL","POSTFIX_REL","INFIX_REL"}
KNOWN_RELATIONS = PREFIX_RELATIONS | DOTTED_PREFIX_RELATIONS | POSTFIX_RELATIONS | INFIX_RELATIONS
PUNCTUATION = {"(",")","[","]","{","}",",",":","?",";"}
REF_RE = re.compile(r"^@[A-Za-z0-9_./-]+$")
NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")

class ClauseIRError(ValueError):
    pass

def stable_json(value: Any) -> bytes:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def validate_work_revision_shape(work_revision: dict[str,str]) -> None:
    if not isinstance(work_revision,dict) or not work_revision:
        raise ClauseIRError("current-work revision binding is required")
    missing=[f for f in REQUIRED_WORK_REVISION_FIELDS if not isinstance(work_revision.get(f),str) or not work_revision[f]]
    if missing:
        raise ClauseIRError(f"current-work revision missing exact bindings: {missing!r}")

def _children(node: Any) -> list[Any]:
    if not isinstance(node,dict): return []
    value=node.get("children",[])
    if not isinstance(value,list): raise ClauseIRError("canonical AST children must be a list")
    return value

def _walk(node: Any) -> Iterable[Any]:
    yield node
    for child in _children(node): yield from _walk(child)

def _token(node: Any) -> tuple[str,str] | None:
    if not isinstance(node,dict) or "token" not in node: return None
    typ=node.get("token"); value=node.get("value")
    if not isinstance(typ,str) or not isinstance(value,(str,int,float,bool)):
        raise ClauseIRError("canonical token requires string token type and scalar value")
    return typ,str(value)

def _validate_relation_token(typ: str,value: str) -> None:
    if typ=="PREFIX_REL" and value not in PREFIX_RELATIONS: raise ClauseIRError(f"unknown PREFIX_REL value: {value!r}")
    if typ=="DOTTED_PREFIX_REL" and value not in DOTTED_PREFIX_RELATIONS: raise ClauseIRError(f"unknown DOTTED_PREFIX_REL value: {value!r}")
    if typ=="POSTFIX_REL" and value not in POSTFIX_RELATIONS: raise ClauseIRError(f"unknown POSTFIX_REL value: {value!r}")
    if typ=="INFIX_REL" and value not in INFIX_RELATIONS: raise ClauseIRError(f"unknown INFIX_REL value: {value!r}")

def _validate_ast_node(node: Any) -> None:
    if not isinstance(node,dict): raise ClauseIRError(f"canonical AST node must be object, got {type(node).__name__}")
    has_kind="kind" in node; has_token="token" in node
    if has_kind==has_token: raise ClauseIRError("canonical AST node must contain exactly one of kind/token")
    if has_kind:
        kind=node.get("kind")
        if not isinstance(kind,str) or not kind: raise ClauseIRError("canonical AST kind must be non-empty string")
        extra=set(node)-{"kind","children"}
        if extra: raise ClauseIRError(f"unexpected canonical tree fields: {sorted(extra)!r}")
        for child in _children(node): _validate_ast_node(child)
        return
    extra=set(node)-{"token","value"}
    if extra: raise ClauseIRError(f"unexpected canonical token fields: {sorted(extra)!r}")
    typ,value=_token(node) or ("","")
    if typ in RELATION_TOKEN_TYPES: _validate_relation_token(typ,value)

def _token_rows(node: Any) -> list[dict[str,str]]:
    out=[]
    for part in _walk(node):
        t=_token(part)
        if t is not None: out.append({"token":t[0],"value":t[1]})
    return out

def _is_keyword_token(value: str,kind: str) -> bool:
    return value == ("rule" if kind=="rule_decl" else "invariant")

def _validate_clause_root(kind: str,ast: Any) -> tuple[list[Any],list[dict[str,str]]]:
    _validate_ast_node(ast)
    if ast.get("kind")!=kind: raise ClauseIRError(f"residual kind/root mismatch: row={kind!r}, ast={ast.get('kind')!r}")
    children=_children(ast)
    if len(children)<2: raise ClauseIRError(f"{kind} must contain declaration keyword and expression payload")
    first_token=_token(children[0])
    if first_token is None or not _is_keyword_token(first_token[1],kind):
        raise ClauseIRError(f"{kind} first child must be its declaration keyword")
    expr_children=children[1:]; tokens=_token_rows(ast)
    if not tokens: raise ClauseIRError(f"{kind} contains no canonical tokens")
    return expr_children,tokens

def _semantic_token_class(token_type: str,value: str) -> str:
    if token_type in RELATION_TOKEN_TYPES or value in KNOWN_RELATIONS: return "RELATION"
    if value in CORE_OPERATORS: return "OPERATOR"
    if value in PUNCTUATION: return "PUNCTUATION"
    if value in {"true","false"}: return "BOOLEAN"
    if REF_RE.fullmatch(value): return "REF"
    if NUMBER_RE.fullmatch(value): return "NUMBER"
    if token_type=="STRING": return "STRING"
    return "SYMBOL"

def _symbol_inventory(tokens: list[dict[str,str]]) -> list[str]:
    return sorted({r["value"] for r in tokens[1:] if _semantic_token_class(r["token"],r["value"])=="SYMBOL"})

def _relation_inventory(tokens: list[dict[str,str]]) -> list[str]:
    return sorted({r["value"] for r in tokens if _semantic_token_class(r["token"],r["value"])=="RELATION"})

def lower_clause(residual: dict[str,Any],*,index: int,work_revision: dict[str,str]) -> dict[str,Any]:
    if not isinstance(residual,dict): raise ClauseIRError("residual row must be object")
    kind=residual.get("kind")
    if kind not in SUPPORTED_KINDS: raise ClauseIRError(f"unsupported residual class for declarative ClauseIR: {kind!r}")
    expr_children,tokens=_validate_clause_root(kind,residual.get("canonical_ast"))
    validate_work_revision_shape(work_revision)
    semantic_core={
        "schema":SCHEMA,"clause_kind":SUPPORTED_KINDS[kind],"expression_ast":expr_children,
        "token_stream":tokens[1:],"symbols":_symbol_inventory(tokens),"relations":_relation_inventory(tokens),
        "effect_class":"DECLARATIVE_CONSTRAINT_ONLY","effect_authority":"NONE","truth_authority":"NONE",
    }
    clause_hash=sha256(DOMAIN+stable_json(semantic_core))
    return {"index":index,**semantic_core,"clause_semantic_sha256":clause_hash,"clause_id":f"clause:{clause_hash}",
            "source_residual_sha256":sha256(stable_json(residual)),"work_revision":dict(work_revision),
            "legality":"LOWERED_AND_VALIDATED_FOR_DECLARATIVE_CLAUSE_IR","runtime_execution":"NOT_GRANTED_BY_WP03_CLAUSE_IR"}

def lower_bundle(typed_ir: dict[str,Any],*,work_revision: dict[str,str]) -> dict[str,Any]:
    validate_work_revision_shape(work_revision)
    opaque=typed_ir.get("opaque_unlowered_semantics")
    if not isinstance(opaque,list): raise ClauseIRError("TypedIR must contain opaque_unlowered_semantics list")
    clauses=[]; deferred=[]
    for index,row in enumerate(opaque):
        kind=row.get("kind") if isinstance(row,dict) else None
        if kind in SUPPORTED_KINDS: clauses.append(lower_clause(row,index=index,work_revision=work_revision))
        else: deferred.append({"index":index,"kind":kind,"status":"EXPLICITLY_DEFERRED_FAIL_CLOSED","effect_authority":"NONE"})
    core={"schema":SCHEMA,"source_typed_ir_sha256":typed_ir.get("typed_ir_sha256"),"work_revision":dict(work_revision),
          "clauses":clauses,"deferred":deferred,"summary":{"clause_count":len(clauses),
          "clause_kind_counts":dict(sorted(Counter(c["clause_kind"] for c in clauses).items())),"deferred_count":len(deferred),
          "effect_authority":"NONE","runtime_execution_authority":"NONE"}}
    receipt_hash=sha256(RECEIPT_DOMAIN+stable_json(core))
    return {**core,"clause_receipt_sha256":receipt_hash,"invariants":{"presence_implies_truth":"FORBIDDEN",
            "clause_ir_mints_effect_authority":"FORBIDDEN","clause_ir_mints_runtime_execution_authority":"FORBIDDEN",
            "unsupported_residual_implicit_execution":"FORBIDDEN","stale_work_revision_credit":"FORBIDDEN",
            "receipt_reuse_across_component_hash_change":"FORBIDDEN"},"promotion":"NONE","wp03_status":"OPEN","wp04_status":"OPEN","wp05_status":"OPEN"}

def validate_bundle(receipt: dict[str,Any],*,expected_work_revision: dict[str,str]) -> None:
    validate_work_revision_shape(expected_work_revision)
    if receipt.get("schema")!=SCHEMA: raise ClauseIRError("unexpected ClauseIR receipt schema")
    if receipt.get("work_revision")!=expected_work_revision: raise ClauseIRError("STALE_EXECUTION_RECEIPT: work/component revision mismatch")
    clauses=receipt.get("clauses"); deferred=receipt.get("deferred")
    if not isinstance(clauses,list) or not isinstance(deferred,list): raise ClauseIRError("ClauseIR receipt lists missing")
    for item in clauses:
        if item.get("effect_authority")!="NONE" or item.get("truth_authority")!="NONE": raise ClauseIRError("declarative clause attempted to mint authority")
        if item.get("legality")!="LOWERED_AND_VALIDATED_FOR_DECLARATIVE_CLAUSE_IR": raise ClauseIRError("clause missing legality receipt")
        if item.get("work_revision")!=expected_work_revision: raise ClauseIRError("clause bound to stale work/component revision")
    for row in deferred:
        if row.get("status")!="EXPLICITLY_DEFERRED_FAIL_CLOSED" or row.get("effect_authority")!="NONE": raise ClauseIRError("non-clause residual did not remain fail closed")

def consume_declarative_clauses(receipt: dict[str,Any],*,expected_work_revision: dict[str,str]) -> dict[str,Any]:
    validate_bundle(receipt,expected_work_revision=expected_work_revision)
    registry=[{"clause_id":item["clause_id"],"clause_kind":item["clause_kind"],"clause_semantic_sha256":item["clause_semantic_sha256"],
               "evaluation_boundary":"RUNTIME_PREDICATE_ENVIRONMENT_REQUIRED","effect_authority":"NONE","truth_authority":"NONE"}
              for item in receipt["clauses"]]
    core={"schema":"ClayCodeDeclarativeClauseConsumer/v1","source_clause_receipt_sha256":receipt["clause_receipt_sha256"],
          "work_revision":dict(expected_work_revision),"registry":registry,"deferred_residual_count":len(receipt["deferred"]),
          "implicit_execution_count":0,"effect_authority":"NONE"}
    return {**core,"consumer_receipt_sha256":sha256(CONSUMER_DOMAIN+stable_json(core)),"status":"PASS_CONSUMPTION_BOUNDARY_ONLY","promotion":"NONE"}
