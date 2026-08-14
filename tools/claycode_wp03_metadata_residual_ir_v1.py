#!/usr/bin/env python3
"""WP03 candidate for non-control residual declarations in the exact V18 surface.

Seven residual classes are lowered as non-authoritative metadata/state declarations:
module, version, status, parent, import, dialect and tensor. `cycle_decl` is deliberately
not lowered here because V18 gives it executable control-flow structure; it remains
fail-closed for the WP05 evaluator.

This candidate preserves canonical AST identity, never grants truth/effect/execution
authority, and requires exact current-work/component bindings. It is not a WP03 promotion.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any, Iterable

SCHEMA="ClayCodeMetadataResidualIR/v1"
DOMAIN=b"ClayCodeMetadataResidualIR/v1\x00"
RECEIPT_DOMAIN=b"ClayCodeMetadataResidualReceipt/v1\x00"
CONSUMER_DOMAIN=b"ClayCodeMetadataResidualConsumer/v1\x00"
SUPPORTED={
    "module_decl":"MODULE_IDENTITY",
    "version_decl":"VERSION_LITERAL",
    "status_decl":"STATUS_MARKER",
    "parent_decl":"PARENT_SET",
    "import_decl":"IMPORT_BINDING",
    "dialect_decl":"DIALECT_DEFINITION",
    "tensor_decl":"TENSOR_LITERAL",
}
CONTROL_DEFER={"cycle_decl":"OWNED_BY_WP05_CONTROL_FLOW_EVALUATOR"}
REQUIRED_WORK_REVISION_FIELDS=(
    "repo_head","supervisor_blob_sha","steering_ref","steering_blob_sha",
    "frontend_blob_sha","grammar_blob_sha","typed_ir_blob_sha","residual_builder_blob_sha",
)
REF_RE=re.compile(r"^@[A-Za-z0-9_./-]+$")

class MetadataIRError(ValueError): pass

def stable_json(v:Any)->bytes:
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()

def sha256(v:bytes)->str: return hashlib.sha256(v).hexdigest()

def validate_work_revision_shape(w:dict[str,str])->None:
    if not isinstance(w,dict): raise MetadataIRError("current-work revision binding required")
    missing=[k for k in REQUIRED_WORK_REVISION_FIELDS if not isinstance(w.get(k),str) or not w[k]]
    if missing: raise MetadataIRError(f"current-work revision missing exact bindings: {missing!r}")

def children(n:Any)->list[Any]:
    if not isinstance(n,dict): return []
    c=n.get("children",[])
    if not isinstance(c,list): raise MetadataIRError("canonical AST children must be list")
    return c

def walk(n:Any)->Iterable[Any]:
    yield n
    for c in children(n): yield from walk(c)

def token(n:Any)->tuple[str,str]|None:
    if not isinstance(n,dict) or "token" not in n: return None
    t=n.get("token"); v=n.get("value")
    if not isinstance(t,str) or not isinstance(v,(str,int,float,bool)):
        raise MetadataIRError("canonical token requires string type and scalar value")
    return t,str(v)

def validate_ast(n:Any)->None:
    if not isinstance(n,dict): raise MetadataIRError("canonical AST node must be object")
    hk="kind" in n; ht="token" in n
    if hk==ht: raise MetadataIRError("canonical AST node must contain exactly one of kind/token")
    if hk:
        if not isinstance(n.get("kind"),str) or not n["kind"]: raise MetadataIRError("empty AST kind")
        extra=set(n)-{"kind","children"}
        if extra: raise MetadataIRError(f"unexpected canonical tree fields: {sorted(extra)!r}")
        for c in children(n): validate_ast(c)
    else:
        extra=set(n)-{"token","value"}
        if extra: raise MetadataIRError(f"unexpected canonical token fields: {sorted(extra)!r}")
        token(n)

def tokens(n:Any)->list[dict[str,str]]:
    out=[]
    for x in walk(n):
        tv=token(x)
        if tv: out.append({"token":tv[0],"value":tv[1]})
    return out

def direct_kinds(n:Any)->list[str]:
    return [c.get("kind") for c in children(n) if isinstance(c,dict) and isinstance(c.get("kind"),str)]

def direct_tokens(n:Any)->list[tuple[str,str]]:
    return [t for c in children(n) if (t:=token(c)) is not None]

def require_root(row:dict[str,Any],kind:str)->tuple[dict[str,Any],list[dict[str,str]]]:
    ast=row.get("canonical_ast"); validate_ast(ast)
    if ast.get("kind")!=kind: raise MetadataIRError(f"residual kind/root mismatch {kind!r}/{ast.get('kind')!r}")
    ts=tokens(ast)
    keyword=kind.removesuffix("_decl")
    if not ts or ts[0]["value"]!=keyword: raise MetadataIRError(f"{kind} missing declaration keyword")
    return ast,ts

def validate_class_shape(kind:str,ast:dict[str,Any],ts:list[dict[str,str]])->dict[str,Any]:
    vals=[x["value"] for x in ts]
    dks=direct_kinds(ast)
    if kind=="module_decl":
        if len(vals)<2 or "qid" not in dks: raise MetadataIRError("module_decl requires qid")
        return {"module_qid_tokens":vals[1:]}
    if kind=="version_decl":
        strings=[x["value"] for x in ts[1:] if x["token"]=="STRING"]
        if len(strings)!=1: raise MetadataIRError("version_decl requires exactly one STRING")
        return {"version_literal":strings[0]}
    if kind=="status_decl":
        if len(vals)<2 or "qid" not in dks: raise MetadataIRError("status_decl requires qid")
        return {"status_qid_tokens":vals[1:]}
    if kind=="parent_decl":
        if "list" not in dks: raise MetadataIRError("parent_decl requires list")
        return {"parent_tokens":vals[1:]}
    if kind=="import_decl":
        refs=[x["value"] for x in ts if x["token"]=="REF"]
        if len(refs)!=1 or not REF_RE.fullmatch(refs[0]): raise MetadataIRError("import_decl requires one valid REF")
        if "=" not in vals: raise MetadataIRError("import_decl requires binding operator")
        return {"import_ref":refs[0],"binding_tokens":vals[1:]}
    if kind=="dialect_decl":
        if "dialect_block" not in dks: raise MetadataIRError("dialect_decl requires dialect_block")
        if len(vals)<2: raise MetadataIRError("dialect_decl requires name")
        nested_invariants=sum(1 for x in walk(ast) if isinstance(x,dict) and x.get("kind")=="invariant_decl")
        return {"dialect_name_token":vals[1],"nested_invariant_count":nested_invariants}
    if kind=="tensor_decl":
        if "list" not in dks: raise MetadataIRError("tensor_decl requires list")
        if len(vals)<2 or "=" not in vals: raise MetadataIRError("tensor_decl requires name and list binding")
        return {"tensor_name_token":vals[1],"literal_tokens":vals[2:]}
    raise MetadataIRError(f"unsupported metadata class {kind!r}")

def lower_metadata(row:dict[str,Any],*,index:int,work_revision:dict[str,str])->dict[str,Any]:
    if not isinstance(row,dict): raise MetadataIRError("residual row must be object")
    kind=row.get("kind")
    if kind not in SUPPORTED: raise MetadataIRError(f"unsupported metadata residual class: {kind!r}")
    validate_work_revision_shape(work_revision)
    ast,ts=require_root(row,kind); fields=validate_class_shape(kind,ast,ts)
    core={"schema":SCHEMA,"metadata_kind":SUPPORTED[kind],"canonical_ast":ast,"token_stream":ts[1:],
          "typed_fields":fields,"semantic_type":SUPPORTED[kind],"effect_authority":"NONE","truth_authority":"NONE",
          "runtime_execution_authority":"NONE"}
    h=sha256(DOMAIN+stable_json(core))
    return {"index":index,**core,"metadata_semantic_sha256":h,"metadata_id":f"meta:{h}",
            "source_residual_sha256":sha256(stable_json(row)),"work_revision":dict(work_revision),
            "legality":"LOWERED_AND_VALIDATED_FOR_METADATA_IR","promotion":"NONE"}

def lower_bundle(typed_ir:dict[str,Any],*,work_revision:dict[str,str])->dict[str,Any]:
    validate_work_revision_shape(work_revision)
    opaque=typed_ir.get("opaque_unlowered_semantics")
    if not isinstance(opaque,list): raise MetadataIRError("TypedIR opaque_unlowered_semantics missing")
    lowered=[]; deferred=[]; rejected=[]
    for i,row in enumerate(opaque):
        kind=row.get("kind") if isinstance(row,dict) else None
        if kind in SUPPORTED: lowered.append(lower_metadata(row,index=i,work_revision=work_revision))
        elif kind in CONTROL_DEFER:
            deferred.append({"index":i,"kind":kind,"status":"EXPLICITLY_DEFERRED_FAIL_CLOSED","reason":CONTROL_DEFER[kind],
                             "effect_authority":"NONE","runtime_execution_authority":"NONE"})
        elif kind in {"rule_decl","invariant_decl"}:
            deferred.append({"index":i,"kind":kind,"status":"OWNED_BY_SEPARATE_RULE_INVARIANT_CLAUSE_IR",
                             "effect_authority":"NONE","runtime_execution_authority":"NONE"})
        else:
            rejected.append({"index":i,"kind":kind,"status":"REJECTED_WITH_REASON","reason":"UNRECOGNIZED_RESIDUAL_CLASS",
                             "effect_authority":"NONE"})
    core={"schema":SCHEMA,"source_typed_ir_sha256":typed_ir.get("typed_ir_sha256"),"work_revision":dict(work_revision),
          "lowered":lowered,"deferred":deferred,"rejected":rejected,
          "summary":{"lowered_count":len(lowered),"lowered_kind_counts":dict(sorted(Counter(x["metadata_kind"] for x in lowered).items())),
                     "deferred_count":len(deferred),"rejected_count":len(rejected),"effect_authority":"NONE",
                     "runtime_execution_authority":"NONE"}}
    return {**core,"metadata_receipt_sha256":sha256(RECEIPT_DOMAIN+stable_json(core)),"promotion":"NONE","wp03_status":"OPEN"}

def validate_bundle(receipt:dict[str,Any],*,expected_work_revision:dict[str,str])->None:
    validate_work_revision_shape(expected_work_revision)
    if receipt.get("schema")!=SCHEMA: raise MetadataIRError("unexpected metadata receipt schema")
    if receipt.get("work_revision")!=expected_work_revision: raise MetadataIRError("STALE_EXECUTION_RECEIPT: work/component revision mismatch")
    for x in receipt.get("lowered",[]):
        if x.get("effect_authority")!="NONE" or x.get("truth_authority")!="NONE" or x.get("runtime_execution_authority")!="NONE":
            raise MetadataIRError("metadata attempted to mint authority")
        if x.get("work_revision")!=expected_work_revision: raise MetadataIRError("metadata bound to stale work revision")
    for x in receipt.get("deferred",[]):
        if x.get("effect_authority")!="NONE" or x.get("runtime_execution_authority")!="NONE": raise MetadataIRError("deferred residual gained authority")

def consume_metadata(receipt:dict[str,Any],*,expected_work_revision:dict[str,str])->dict[str,Any]:
    validate_bundle(receipt,expected_work_revision=expected_work_revision)
    registry=[{"metadata_id":x["metadata_id"],"semantic_type":x["semantic_type"],"metadata_semantic_sha256":x["metadata_semantic_sha256"],
               "consumer_boundary":"READ_ONLY_COMPILER_RUNTIME_METADATA","effect_authority":"NONE","runtime_execution_authority":"NONE"}
              for x in receipt["lowered"]]
    control=[x for x in receipt["deferred"] if x.get("kind")=="cycle_decl"]
    core={"schema":"ClayCodeMetadataResidualConsumer/v1","source_metadata_receipt_sha256":receipt["metadata_receipt_sha256"],
          "work_revision":dict(expected_work_revision),"registry":registry,"control_flow_deferred":control,
          "implicit_execution_count":0,"effect_authority":"NONE","runtime_execution_authority":"NONE"}
    return {**core,"consumer_receipt_sha256":sha256(CONSUMER_DOMAIN+stable_json(core)),"status":"PASS_CONSUMPTION_BOUNDARY_ONLY","promotion":"NONE"}
