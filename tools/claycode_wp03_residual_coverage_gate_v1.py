#!/usr/bin/env python3
"""Integrated exact-once disposition gate for the measured WP03 residual frontier.

Inputs are the exact current TypedIR plus independently validated Rule/Invariant ClauseIR and
MetadataIR receipts/consumer receipts. The gate proves disposition coverage only:
- 81 rule/invariant residuals are owned exactly once by declarative ClauseIR;
- 18 non-control declarations are owned exactly once by MetadataIR;
- 1 cycle_decl remains explicitly fail-closed for WP05 control-flow evaluation;
- no gaps, overlaps, rejections, authority minting or implicit execution are allowed.

This gate does not type-check every expression operand, execute cycle control flow, or promote
WP03/BASE. It is an adjudication input, not release authority.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA="ClayCodeWP03ResidualCoverage/v1"
DOMAIN=b"ClayCodeWP03ResidualCoverage/v1\x00"
CLAUSE_KINDS={"rule_decl","invariant_decl"}
METADATA_KINDS={"module_decl","version_decl","status_decl","parent_decl","import_decl","dialect_decl","tensor_decl"}
CONTROL_KIND="cycle_decl"
EXPECTED_TOTAL=100
EXPECTED_COUNTS={
    "rule_decl":67,"invariant_decl":14,"dialect_decl":9,"import_decl":2,"module_decl":2,
    "version_decl":2,"cycle_decl":1,"status_decl":1,"parent_decl":1,"tensor_decl":1,
}

class CoverageError(ValueError): pass

def stable_json(v:Any)->bytes:
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")

def sha256(v:bytes)->str: return hashlib.sha256(v).hexdigest()

def require_none(row:dict[str,Any],fields:tuple[str,...],label:str)->None:
    for field in fields:
        if row.get(field)!="NONE": raise CoverageError(f"{label} minted {field}: {row.get(field)!r}")

def verify(
    typed_ir:dict[str,Any],
    clause_receipt:dict[str,Any],
    clause_consumer:dict[str,Any],
    metadata_receipt:dict[str,Any],
    metadata_consumer:dict[str,Any],
    *,
    expected_work_revision:dict[str,str],
)->dict[str,Any]:
    opaque=typed_ir.get("opaque_unlowered_semantics")
    if not isinstance(opaque,list): raise CoverageError("TypedIR opaque_unlowered_semantics missing")
    if len(opaque)!=EXPECTED_TOTAL: raise CoverageError(f"measured frontier changed: expected {EXPECTED_TOTAL}, got {len(opaque)}")
    observed={}
    for index,row in enumerate(opaque):
        if not isinstance(row,dict) or not isinstance(row.get("kind"),str): raise CoverageError(f"invalid residual row {index}")
        observed[row["kind"]]=observed.get(row["kind"],0)+1
    if observed!=EXPECTED_COUNTS: raise CoverageError(f"residual class census changed: {observed!r}")

    typed_hash=typed_ir.get("typed_ir_sha256")
    if not isinstance(typed_hash,str) or not typed_hash: raise CoverageError("TypedIR semantic hash missing")
    for label,receipt in (("clause",clause_receipt),("metadata",metadata_receipt)):
        if receipt.get("source_typed_ir_sha256")!=typed_hash: raise CoverageError(f"{label} receipt bound to different TypedIR")
        if receipt.get("work_revision")!=expected_work_revision: raise CoverageError(f"{label} STALE_EXECUTION_RECEIPT")
    for label,consumer in (("clause_consumer",clause_consumer),("metadata_consumer",metadata_consumer)):
        if consumer.get("work_revision")!=expected_work_revision: raise CoverageError(f"{label} STALE_EXECUTION_RECEIPT")
        if consumer.get("implicit_execution_count")!=0: raise CoverageError(f"{label} implicit execution observed")
        require_none(consumer,("effect_authority",),label)

    clause_by_index={}
    for row in clause_receipt.get("clauses",[]):
        idx=row.get("index")
        if not isinstance(idx,int) or idx in clause_by_index: raise CoverageError("duplicate/invalid ClauseIR index")
        if idx<0 or idx>=len(opaque): raise CoverageError("ClauseIR index outside frontier")
        if opaque[idx].get("kind") not in CLAUSE_KINDS: raise CoverageError(f"ClauseIR claimed non-clause index {idx}")
        require_none(row,("effect_authority","truth_authority"),f"clause[{idx}]")
        if row.get("legality")!="LOWERED_AND_VALIDATED_FOR_DECLARATIVE_CLAUSE_IR": raise CoverageError(f"clause[{idx}] not validated")
        clause_by_index[idx]=row

    metadata_by_index={}
    for row in metadata_receipt.get("lowered",[]):
        idx=row.get("index")
        if not isinstance(idx,int) or idx in metadata_by_index: raise CoverageError("duplicate/invalid MetadataIR index")
        if idx<0 or idx>=len(opaque): raise CoverageError("MetadataIR index outside frontier")
        if opaque[idx].get("kind") not in METADATA_KINDS: raise CoverageError(f"MetadataIR claimed non-metadata index {idx}")
        require_none(row,("effect_authority","truth_authority","runtime_execution_authority"),f"metadata[{idx}]")
        if row.get("legality")!="LOWERED_AND_VALIDATED_FOR_METADATA_IR": raise CoverageError(f"metadata[{idx}] not validated")
        metadata_by_index[idx]=row

    if metadata_receipt.get("rejected") not in ([],None): raise CoverageError("current frontier contains rejected metadata residuals")
    cycle_rows=[row for row in metadata_receipt.get("deferred",[]) if row.get("kind")==CONTROL_KIND]
    if len(cycle_rows)!=1: raise CoverageError(f"expected exactly one deferred cycle_decl, got {len(cycle_rows)}")
    cycle=cycle_rows[0]; cycle_idx=cycle.get("index")
    if not isinstance(cycle_idx,int) or cycle_idx<0 or cycle_idx>=len(opaque): raise CoverageError("invalid cycle index")
    if opaque[cycle_idx].get("kind")!=CONTROL_KIND: raise CoverageError("deferred cycle index does not point to cycle_decl")
    if cycle.get("status")!="EXPLICITLY_DEFERRED_FAIL_CLOSED": raise CoverageError("cycle_decl is not fail-closed")
    if cycle.get("reason")!="OWNED_BY_WP05_CONTROL_FLOW_EVALUATOR": raise CoverageError("cycle_decl ownership boundary changed")
    require_none(cycle,("effect_authority","runtime_execution_authority"),"cycle")

    clause_indexes=set(clause_by_index); metadata_indexes=set(metadata_by_index); cycle_indexes={cycle_idx}
    if clause_indexes & metadata_indexes or clause_indexes & cycle_indexes or metadata_indexes & cycle_indexes:
        raise CoverageError("residual disposition overlap")
    covered=clause_indexes|metadata_indexes|cycle_indexes
    expected=set(range(len(opaque)))
    if covered!=expected:
        raise CoverageError(f"residual disposition gap extra={sorted(covered-expected)} missing={sorted(expected-covered)}")
    if len(clause_indexes)!=81 or len(metadata_indexes)!=18 or len(cycle_indexes)!=1:
        raise CoverageError("measured 81/18/1 partition changed")

    clause_registry=clause_consumer.get("registry")
    metadata_registry=metadata_consumer.get("registry")
    if not isinstance(clause_registry,list) or len(clause_registry)!=81: raise CoverageError("ClauseIR consumer registry mismatch")
    if not isinstance(metadata_registry,list) or len(metadata_registry)!=18: raise CoverageError("MetadataIR consumer registry mismatch")
    if metadata_consumer.get("control_flow_deferred")!=[cycle]: raise CoverageError("consumer cycle deferral mismatch")
    for row in clause_registry:
        require_none(row,("effect_authority","truth_authority"),"clause_registry")
    for row in metadata_registry:
        require_none(row,("effect_authority","runtime_execution_authority"),"metadata_registry")

    core={
      "schema":SCHEMA,
      "typed_ir_sha256":typed_hash,
      "work_revision":dict(expected_work_revision),
      "residual_count":len(opaque),
      "class_counts":observed,
      "disposition":{"clause_ir":81,"metadata_ir":18,"cycle_wp05_deferred":1,"gaps":0,"overlaps":0,"rejected":0},
      "consumer":{"clause_registry":81,"metadata_registry":18,"implicit_execution_count":0},
      "authority":{"effect":"NONE","truth":"NONE","runtime_execution":"NONE"},
      "cycle_decl":"EXPLICITLY_DEFERRED_FAIL_CLOSED_TO_WP05_CONTROL_FLOW_EVALUATOR",
      "scope":"EXACT_ONCE_RESIDUAL_DISPOSITION_AND_CONSUMPTION_COVERAGE_ONLY",
    }
    return {
      **core,
      "coverage_receipt_sha256":sha256(DOMAIN+stable_json(core)),
      "status":"PASS_COVERAGE_ONLY",
      "promotion":"NONE",
      "wp03_status":"OPEN_PENDING_PACKAGE_ADJUDICATION",
    }
