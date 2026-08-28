#!/usr/bin/env python3
"""Calibration-only actuator-orientation successor to cross-task gate v6.

The frozen Run-2 v1 runtime selected the least-bad positive gain even though every
calibration behavioral delta was negative, then exposed holdout. V7 prevents a
fresh successor from using holdout to discover actuator sign: both + and - actuator
orientations at the already-fixed gain must be measured on calibration only, a
deterministic worst-state rule freezes the sign, and every state must clear the
minimum calibration effect before holdout may count.

The +/- orientation here is an actuator-sign calibration, not a claim that -v is
the semantic opposite of a state in rank-2 geometry.

Execution-free adjudication only; no canonical/J-Space/HCU/EntityOS/training credit.
"""
from __future__ import annotations
import collections, copy, math
from typing import Any
from tools import trigger1_cross_task_abstract_control_gate_v6 as v6

SCHEMA="CLAY_TRIGGER1_CROSS_TASK_ABSTRACT_CONTROL_GATE/v7"
ATTESTATION_SCHEMA="CLAY_TRIGGER1_CROSS_TASK_ABSTRACT_CONTROL_EVIDENCE/v7"
ORIENTATION_SCHEMA="CLAY_TRIGGER1_CALIBRATION_ACTUATOR_ORIENTATION/v1"
SIGNS=(-1,1)
MIN_CAL_EFFECT=0.05


def _num(x: Any) -> bool:
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(float(x))


def _orientation(candidate: dict[str,Any], failures: list[str]) -> dict[str,Any]:
    o=candidate.get("actuator_orientation_calibration")
    if not isinstance(o,dict):
        failures.append("ACTUATOR_ORIENTATION_CALIBRATION_REQUIRED"); return {}
    if o.get("schema")!=ORIENTATION_SCHEMA: failures.append("ACTUATOR_ORIENTATION_SCHEMA_MISMATCH")
    if o.get("fit_split")!="CALIBRATION": failures.append("ACTUATOR_ORIENTATION_MUST_BE_CALIBRATION_ONLY")
    if o.get("frozen_before_holdout") is not True: failures.append("ACTUATOR_ORIENTATION_NOT_FROZEN_BEFORE_HOLDOUT")
    if o.get("holdout_seen_during_selection") is not False: failures.append("ACTUATOR_ORIENTATION_HOLDOUT_LEAK")
    if o.get("selection_rule")!="MAXIMIZE_WORST_STATE_MEAN_TARGET_MARGIN_DELTA":
        failures.append("ACTUATOR_ORIENTATION_SELECTION_RULE_MISMATCH")

    primary=candidate.get("primary_settings")
    fixed_gain=primary.get("gain") if isinstance(primary,dict) else None
    if not _num(fixed_gain): failures.append("ACTUATOR_ORIENTATION_PRIMARY_GAIN_REQUIRED")

    rows=o.get("rows")
    groups: dict[tuple[str,str,str,str,str],dict[int,float]]={}
    per_sign_state: dict[int,dict[str,list[float]]]={s:collections.defaultdict(list) for s in SIGNS}
    if not isinstance(rows,list) or not rows:
        failures.append("ACTUATOR_ORIENTATION_ROWS_REQUIRED")
    else:
        for i,r in enumerate(rows):
            p=f"ACTUATOR_ORIENTATION_{i}"
            if not isinstance(r,dict): failures.append(p+"_OBJECT_REQUIRED"); continue
            fam=r.get("family_id"); state=r.get("vector_state_id"); code=r.get("requested_code")
            pol=r.get("probe_polarity"); rep=r.get("replicate_id"); sign=r.get("actuator_sign")
            gain=r.get("gain"); delta=r.get("target_margin_delta_vs_baseline")
            if (not isinstance(fam,str) or not fam or state not in v6.STATES or code not in v6.CODES
                or pol not in v6.POLARITIES or not isinstance(rep,str) or not rep
                or sign not in SIGNS or not _num(gain) or not _num(delta)):
                failures.append(p+"_FIELDS_INVALID"); continue
            if _num(fixed_gain) and float(gain)!=float(fixed_gain):
                failures.append(p+"_GAIN_NOT_FIXED_PRIMARY")
            key=(fam,state,code,pol,rep)
            by=groups.setdefault(key,{})
            if sign in by: failures.append(p+"_DUPLICATE_SIGN"); continue
            by[sign]=float(delta)
            per_sign_state[sign][state].append(float(delta))

    for key,by in sorted(groups.items()):
        if set(by)!=set(SIGNS):
            failures.append("ACTUATOR_ORIENTATION_SIGN_PAIR_INCOMPLETE:"+":".join(key))

    means: dict[int,dict[str,float|None]]={s:{} for s in SIGNS}
    worst: dict[int,float|None]={}
    for sign in SIGNS:
        for state in v6.STATES:
            vals=per_sign_state[sign].get(state,[])
            means[sign][state]=sum(vals)/len(vals) if vals else None
            if not vals: failures.append(f"ACTUATOR_ORIENTATION_STATE_COVERAGE_MISSING:{sign}:{state}")
        present=[means[sign][s] for s in v6.STATES if means[sign][s] is not None]
        worst[sign]=min(present) if len(present)==len(v6.STATES) else None

    chosen=None
    if all(worst[s] is not None for s in SIGNS):
        if math.isclose(float(worst[-1]),float(worst[1]),rel_tol=0.0,abs_tol=1e-12):
            failures.append("ACTUATOR_ORIENTATION_SELECTION_TIE")
        else:
            chosen=max(SIGNS,key=lambda s:float(worst[s]))
            if float(worst[chosen])<=MIN_CAL_EFFECT:
                failures.append("ACTUATOR_ORIENTATION_NO_POSITIVE_WORST_STATE_CALIBRATION_EFFECT")

    declared=o.get("selected_actuator_sign")
    if declared not in SIGNS: failures.append("ACTUATOR_ORIENTATION_SELECTED_SIGN_INVALID")
    elif chosen is not None and declared!=chosen: failures.append("ACTUATOR_ORIENTATION_SELECTED_SIGN_NOT_RULE_OPTIMUM")
    if isinstance(primary,dict):
        if primary.get("actuator_sign")!=declared:
            failures.append("PRIMARY_ACTUATOR_SIGN_NOT_FROZEN_SELECTION")

    return {
        "fixed_gain":float(fixed_gain) if _num(fixed_gain) else None,
        "state_mean_delta_by_sign":{str(k):v for k,v in means.items()},
        "worst_state_mean_delta_by_sign":{str(k):v for k,v in worst.items()},
        "computed_selected_actuator_sign":chosen,
        "declared_selected_actuator_sign":declared,
        "minimum_required_worst_state_effect":MIN_CAL_EFFECT,
        "sign_pair_cells":len(groups),
    }


def adjudicate(candidate: Any) -> dict[str,Any]:
    failures=[]
    if not isinstance(candidate,dict): candidate={}; failures.append("ATTESTATION_OBJECT_REQUIRED")
    if candidate.get("schema")!=ATTESTATION_SCHEMA: failures.append("ATTESTATION_SCHEMA_MISMATCH")
    delegated=copy.deepcopy(candidate); delegated["schema"]=v6.ATTESTATION_SCHEMA
    base=v6.adjudicate(delegated); failures.extend("V6:"+f for f in (base.get("failures") or []))
    orientation=_orientation(candidate,failures)
    passed=not failures and base.get("cross_task_abstract_native_control_pass") is True
    return {
        "schema":SCHEMA,
        "cross_task_abstract_native_control_pass":passed,
        "calibration_actuator_orientation_pass":passed,
        "failures":sorted(set(failures)),
        "delegated_v6":base,
        "actuator_orientation_calibration":orientation,
        "canonical_credit_minted":False,
        "canonical_semantics_promotion":False,
        "jspace_model_runtime_credit":False,
        "whole_hcu_credit":False,
        "whole_entityos_hcu_credit":False,
        "training_credit":False,
        "claim_scope_if_pass":"QWEN3_0_6B_CALIBRATION_ORIENTED_CONDITIONALLY_STRUCTURE_MATCHED_CROSS_TASK_NATIVE_CONTROL_COMPONENT_ONLY",
        "evidence_boundary":"V6 structural/nuisance/rank controls plus calibration-only bidirectional actuator-sign selection at fixed gain with positive worst-state effect before holdout. -v is an actuator orientation probe, not a rank-2 semantic-opposite claim. Execution-free; no canonical/global J-Space credit."
    }
