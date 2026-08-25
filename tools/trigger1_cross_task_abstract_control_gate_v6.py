#!/usr/bin/env python3
"""Conditional structural-deconfound successor to cross-task gate v5.

V6 closes a remaining false-pass interaction: equal target-marginal token/topology
histograms do not imply independence once opaque output code and query polarity are
known. It therefore requires the exact structural-signature multiset to be identical
across S0/S1/S2 inside every family x code x polarity stratum, and requires the
calibration rows used to derive basis directions to satisfy the same invariant.

Execution-free adjudication only. No canonical/J-Space/HCU/EntityOS/training credit.
"""
from __future__ import annotations
import collections, copy
from typing import Any
from tools import trigger1_cross_task_abstract_control_gate_v5 as v5

SCHEMA="CLAY_TRIGGER1_CROSS_TASK_ABSTRACT_CONTROL_GATE/v6"
ATTESTATION_SCHEMA="CLAY_TRIGGER1_CROSS_TASK_ABSTRACT_CONTROL_EVIDENCE/v6"
STATES=v5.STATES
CODES=v5.v4.CODES
POLARITIES=v5.v4.POLARITIES
FIELDS=("proof_topology_id","prompt_tokens","probe_tokens","last_token_index")


def _sig(row: dict[str,Any]) -> tuple[Any,...] | None:
    top=row.get("proof_topology_id"); pt=row.get("prompt_tokens"); qt=row.get("probe_tokens"); li=row.get("last_token_index")
    if not isinstance(top,str) or not top: return None
    if not isinstance(pt,int) or isinstance(pt,bool) or pt<=0: return None
    if not isinstance(qt,int) or isinstance(qt,bool) or qt<=0: return None
    if not isinstance(li,int) or isinstance(li,bool) or li!=pt-1: return None
    return (top,pt,qt,li)


def _conditional(rows: Any, failures: list[str], prefix: str, expected: set[str], target_only: bool) -> dict[str,Any]:
    if not isinstance(rows,list) or not rows:
        failures.append(prefix+"_ROWS_REQUIRED"); return {}
    strata: dict[tuple[str,str,str],dict[str,collections.Counter[tuple[Any,...]]]]={}
    families=set(); valid=0
    for i,row in enumerate(rows):
        if not isinstance(row,dict): failures.append(f"{prefix}_{i}_OBJECT_REQUIRED"); continue
        if target_only and row.get("control")!="TARGET": continue
        fam=row.get("family_id"); target=row.get("vector_state_id"); code=row.get("requested_code"); pol=row.get("probe_polarity")
        if not isinstance(fam,str) or not fam or target not in STATES or code not in CODES or pol not in POLARITIES:
            failures.append(f"{prefix}_{i}_FACTOR_FIELDS_INVALID"); continue
        sig=_sig(row)
        if sig is None: failures.append(f"{prefix}_{i}_STRUCTURE_FIELDS_INVALID"); continue
        families.add(fam); valid+=1
        by=strata.setdefault((fam,code,pol),{s:collections.Counter() for s in STATES})
        by[target][sig]+=1
    for fam in sorted(expected-families): failures.append(prefix+"_EXPECTED_FAMILY_MISSING:"+fam)
    for fam in sorted(families-expected): failures.append(prefix+"_UNBOUND_EXTRA_FAMILY:"+fam)
    checked=0
    for fam in sorted(expected):
        for code in CODES:
            for pol in POLARITIES:
                key=(fam,code,pol); by=strata.get(key)
                if by is None: failures.append(prefix+"_STRATUM_MISSING:"+":".join(key)); continue
                cs=[by[s] for s in STATES]
                if any(not c for c in cs): failures.append(prefix+"_TARGET_CELL_MISSING:"+":".join(key)); continue
                checked+=1
                if any(c!=cs[0] for c in cs[1:]): failures.append(prefix+"_TARGET_LEAK_GIVEN_CODE_POLARITY:"+":".join(key))
    need=len(expected)*len(CODES)*len(POLARITIES)
    ok=checked==need and not any(f.startswith(prefix+"_") for f in failures)
    return {"families":sorted(families),"valid_rows":valid,"conditional_strata_checked":checked,"conditional_strata_required":need,"signature_fields":list(FIELDS),"exact_target_match_given_family_code_polarity":ok}


def _delegate(candidate: dict[str,Any]) -> dict[str,Any]:
    out=copy.deepcopy(candidate); out["schema"]=v5.ATTESTATION_SCHEMA; return out


def adjudicate(candidate: Any) -> dict[str,Any]:
    failures=[]
    if not isinstance(candidate,dict): candidate={}; failures.append("ATTESTATION_OBJECT_REQUIRED")
    if candidate.get("schema")!=ATTESTATION_SCHEMA: failures.append("ATTESTATION_SCHEMA_MISMATCH")
    base=v5.adjudicate(_delegate(candidate)); failures.extend("V5:"+f for f in (base.get("failures") or []))
    basis={r.get("family_id") for r in candidate.get("basis_family_directions",[]) if isinstance(r,dict) and isinstance(r.get("family_id"),str) and r.get("family_id")}
    hold={r.get("family_id") for r in candidate.get("holdout_causal_rows",[]) if isinstance(r,dict) and isinstance(r.get("family_id"),str) and r.get("family_id")}
    cal=_conditional(candidate.get("basis_calibration_structure_rows"),failures,"CALIBRATION_CONDITIONAL_STRUCTURE",basis,False)
    h=_conditional(candidate.get("holdout_causal_rows"),failures,"HOLDOUT_CONDITIONAL_STRUCTURE",hold,True)
    passed=not failures and base.get("cross_task_abstract_native_control_pass") is True
    return {"schema":SCHEMA,"cross_task_abstract_native_control_pass":passed,"conditional_structure_deconfound_pass":passed,"failures":sorted(set(failures)),"delegated_v5":base,"calibration_conditional_structure":cal,"holdout_conditional_structure":h,"canonical_credit_minted":False,"canonical_semantics_promotion":False,"jspace_model_runtime_credit":False,"whole_hcu_credit":False,"whole_entityos_hcu_credit":False,"training_credit":False,"claim_scope_if_pass":"QWEN3_0_6B_CONDITIONALLY_STRUCTURE_MATCHED_EXACT_NUISANCE_CROSS_TASK_NATIVE_CONTROL_COMPONENT_ONLY","evidence_boundary":"V5 exact nuisance/control/rank/topology gates plus exact calibration and holdout structural-signature equality across states conditional on family, opaque code and polarity. Execution-free; no canonical/global J-Space credit."}
