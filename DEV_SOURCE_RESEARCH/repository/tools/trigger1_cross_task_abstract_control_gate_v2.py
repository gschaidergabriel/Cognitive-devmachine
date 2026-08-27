#!/usr/bin/env python3
"""Fail-closed cross-task abstract native-control evidence gate.

This gate is deliberately stricter than the queued single-grammar structural executor.
It does not execute a model and cannot mint canonical/J-Space/HCU/EntityOS/training credit.
"""
from __future__ import annotations
import collections
import math
from typing import Any

SCHEMA = "CLAY_TRIGGER1_CROSS_TASK_ABSTRACT_CONTROL_GATE/v2"
ATTESTATION_SCHEMA = "CLAY_TRIGGER1_CROSS_TASK_ABSTRACT_CONTROL_EVIDENCE/v2"
STATES = ("S0", "S1", "S2")
CODES = ("A", "B", "C")
POLARITIES = ("NONNEGATED", "NEGATED")
CONTROLS = ("TARGET", "NULL", "SIGN_FLIP", "ORTHOGONAL", "PERMUTED", "NUISANCE")
MIN_BASIS_FAMILIES = 3
MIN_HOLDOUT_FAMILIES = 3
MIN_CELL_REPLICATES = 2
MIN_EFFECT = 0.05
MAX_OFF_TARGET_ABS_DELTA = 0.05
PRIMARY_GAIN = 32.0
PRIMARY_LAYER = 20
PINNED_GGUF_SHA256 = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
PINNED_LLAMA_CPP_COMMIT = "bb4caa7540188872173c44d161602d9271386413"

def _num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))

def _vec(x: Any) -> list[float] | None:
    if not isinstance(x, list) or len(x) < 3 or not all(_num(v) for v in x):
        return None
    return [float(v) for v in x]

def _cos(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("VECTOR_DIMENSION_MISMATCH")
    na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(x*x for x in b))
    if na <= 0 or nb <= 0:
        raise ValueError("ZERO_VECTOR")
    return sum(x*y for x,y in zip(a,b))/(na*nb)

def _mean(xs: list[float]) -> float:
    return sum(xs)/len(xs) if xs else float("nan")

def _settings(a: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    s = a.get("primary_settings")
    if not isinstance(s, dict):
        failures.append("PRIMARY_SETTINGS_REQUIRED"); return {}
    if s.get("gguf_sha256") != PINNED_GGUF_SHA256:
        failures.append("PRIMARY_GGUF_IDENTITY_MISMATCH")
    if s.get("llama_cpp_commit") != PINNED_LLAMA_CPP_COMMIT:
        failures.append("PRIMARY_LLAMA_CPP_IDENTITY_MISMATCH")
    if s.get("injection_layer") != PRIMARY_LAYER:
        failures.append("PRIMARY_LAYER_MISMATCH")
    if not _num(s.get("gain")) or float(s["gain"]) != PRIMARY_GAIN:
        failures.append("PRIMARY_GAIN_NOT_FROZEN_32")
    if s.get("gain_selected_on_evaluation") is not False:
        failures.append("EVALUATION_GAIN_SELECTION_FORBIDDEN")
    if s.get("token_scope") != "ALL_PROMPT_TOKENS":
        failures.append("ALL_PROMPT_TOKENS_REQUIRED")
    return s

def _geometry(a: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    rows = a.get("basis_family_directions")
    if not isinstance(rows, list) or len(rows) < MIN_BASIS_FAMILIES:
        failures.append("BASIS_FAMILY_DIRECTIONS_INSUFFICIENT"); return {}
    fams: dict[str, list[float]] = {}
    grammar_ids = set()
    for i,row in enumerate(rows):
        p=f"GEOM_{i}"
        if not isinstance(row, dict) or not isinstance(row.get("family_id"), str) or not isinstance(row.get("task_grammar_id"), str):
            failures.append(p+"_IDENTITY_INVALID"); continue
        v=_vec(row.get("direction"))
        if v is None:
            failures.append(p+"_DIRECTION_INVALID"); continue
        if row["family_id"] in fams:
            failures.append(p+"_DUPLICATE_FAMILY"); continue
        fams[row["family_id"]]=v; grammar_ids.add(row["task_grammar_id"])
    if len(grammar_ids) < MIN_BASIS_FAMILIES:
        failures.append("BASIS_TASK_GRAMMARS_NOT_DISTINCT")
    if len(fams) < MIN_BASIS_FAMILIES:
        failures.append("BASIS_VALID_FAMILIES_INSUFFICIENT"); return {}
    dims={len(v) for v in fams.values()}
    if len(dims)!=1:
        failures.append("BASIS_DIRECTION_DIMENSION_MISMATCH"); return {}
    pair=[]
    keys=sorted(fams)
    try:
        for i,left in enumerate(keys):
            for right in keys[i+1:]:
                pair.append(_cos(fams[left], fams[right]))
        loo=[]
        for held in keys:
            train=[k for k in keys if k!=held]
            mean=[sum(fams[k][d] for k in train)/len(train) for d in range(next(iter(dims)))]
            loo.append(_cos(mean, fams[held]))
    except ValueError as exc:
        failures.append("BASIS_GEOMETRY_INVALID:"+str(exc)); return {}
    null=a.get("geometry_permutation_null")
    if not isinstance(null, dict):
        failures.append("GEOMETRY_PERMUTATION_NULL_REQUIRED"); return {"pairwise_cosines":pair,"loo_cosines":loo}
    pair_thr=null.get("pairwise_cosine_q95"); loo_thr=null.get("loo_cosine_q95")
    if not _num(pair_thr) or not _num(loo_thr):
        failures.append("GEOMETRY_NULL_THRESHOLDS_INVALID")
    else:
        if not pair or min(pair) <= float(pair_thr):
            failures.append("PAIRWISE_GEOMETRY_NOT_ABOVE_NULL")
        if not loo or min(loo) <= float(loo_thr):
            failures.append("LOO_GEOMETRY_NOT_ABOVE_NULL")
    if null.get("derived_from_preregistered_class_assignment_permutations") is not True:
        failures.append("GEOMETRY_NULL_PROVENANCE_REQUIRED")
    return {"pairwise_cosines":pair,"loo_cosines":loo,"families":keys,"task_grammars":len(grammar_ids)}

def _rank_consistency(a: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    r=a.get("rank_consistency")
    if not isinstance(r,dict):
        failures.append("RANK_CONSISTENCY_REQUIRED"); return {}
    allowed={"ONE_DIMENSIONAL_SUPPORTED","TWO_DIMENSIONAL_REQUIRED"}
    vals=[r.get(k) for k in ("representation_rank","intervention_rank","downstream_rank")]
    if any(v not in allowed for v in vals):
        failures.append("RANK_VERDICT_UNRESOLVED_OR_INVALID")
    elif len(set(vals)) != 1:
        failures.append("REPRESENTATION_INTERVENTION_DOWNSTREAM_RANK_MISMATCH")
    if r.get("analyzer") != "trigger1_semantic_simplex_rank_analyze.py":
        failures.append("CANONICAL_RANK_ANALYZER_REQUIRED")
    if r.get("shared_geometry_scale_preserved") is not True:
        failures.append("SHARED_GEOMETRY_SCALE_REQUIRED")
    if r.get("zero_sum_simplex_preserved") is not True:
        failures.append("ZERO_SUM_SIMPLEX_REQUIRED")
    if r.get("downstream_coordinates_in_admitted_orthonormal_basis") is not True:
        failures.append("DOWNSTREAM_ORTHONORMAL_COORDINATES_REQUIRED")
    if r.get("independent_unit_normalization_used") is not False:
        failures.append("INDEPENDENT_UNIT_NORMALIZATION_FORBIDDEN")
    return {"rank":vals[0] if vals and len(set(vals))==1 else None,"representation_rank":vals[0] if vals else None,"intervention_rank":vals[1] if len(vals)>1 else None,"downstream_rank":vals[2] if len(vals)>2 else None}

def _causal(a: dict[str, Any], failures: list[str], rank: dict[str, Any]) -> dict[str, Any]:
    rows=a.get("holdout_causal_rows")
    admitted_rank=rank.get("rank")
    if not isinstance(rows,list) or not rows:
        failures.append("HOLDOUT_CAUSAL_ROWS_REQUIRED"); return {}
    groups=collections.defaultdict(dict)
    cell_counts=collections.Counter()
    topology_counts=collections.Counter()
    family_grammars={}
    demo_contexts=collections.defaultdict(dict)
    length_signatures=collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    basis_ids={r.get("family_id") for r in a.get("basis_family_directions",[]) if isinstance(r,dict)}
    for i,row in enumerate(rows):
        p=f"CAUSAL_{i}"
        if not isinstance(row,dict):
            failures.append(p+"_OBJECT_REQUIRED"); continue
        fam=row.get("family_id"); grammar=row.get("task_grammar_id"); target=row.get("vector_state_id")
        code=row.get("requested_code"); polarity=row.get("probe_polarity"); rep=row.get("replicate_id")
        topology=row.get("proof_topology_id"); demo=row.get("demo_context_id")
        prompt_tokens=row.get("prompt_tokens"); probe_tokens=row.get("probe_tokens"); last_idx=row.get("last_token_index")
        ctrl=row.get("control"); margin=row.get("target_margin")
        if (not all(isinstance(x,str) and x for x in (fam,grammar,rep,demo,topology))
            or target not in STATES or code not in CODES or polarity not in POLARITIES
            or ctrl not in CONTROLS or not _num(margin)
            or not isinstance(prompt_tokens,int) or prompt_tokens <= 0
            or not isinstance(probe_tokens,int) or probe_tokens <= 0
            or not isinstance(last_idx,int) or last_idx != prompt_tokens - 1):
            failures.append(p+"_FIELDS_INVALID"); continue
        if fam in basis_ids:
            failures.append(p+"_BASIS_HOLDOUT_FAMILY_OVERLAP")
        prior=family_grammars.setdefault(fam,grammar)
        if prior != grammar:
            failures.append(p+"_FAMILY_GRAMMAR_DRIFT")
        key=(fam,target,code,polarity,rep)
        if ctrl in groups[key]:
            failures.append(p+"_DUPLICATE_CONTROL")
        groups[key][ctrl]=float(margin)
        demo_key=(fam,target,code,rep)
        demo_prior=demo_contexts[demo_key].setdefault(polarity,demo)
        if demo_prior != demo:
            failures.append(p+"_DEMO_CONTEXT_DRIFT_WITHIN_POLARITY")
        if ctrl=="TARGET":
            cell_counts[(fam,target,code,polarity)] += 1
            topology_counts[(fam,target,topology)] += 1
            length_signatures[fam][target][(prompt_tokens,probe_tokens,last_idx)] += 1
    if len(family_grammars) < MIN_HOLDOUT_FAMILIES:
        failures.append("HOLDOUT_FAMILIES_INSUFFICIENT")
    if len(set(family_grammars.values())) < MIN_HOLDOUT_FAMILIES:
        failures.append("HOLDOUT_TASK_GRAMMARS_NOT_DISTINCT")
    for key,by_pol in demo_contexts.items():
        if set(by_pol) != set(POLARITIES):
            failures.append("POLARITY_PAIR_INCOMPLETE:"+":".join(key)); continue
        if len(set(by_pol.values())) != 1:
            failures.append("DEMO_CONTEXT_NOT_MATCHED_ACROSS_POLARITY:"+":".join(key))
    for key,g in groups.items():
        if set(g) != set(CONTROLS):
            failures.append("CAUSAL_CONTROL_SET_INCOMPLETE:"+":".join(key)); continue
        if g["TARGET"] - g["NULL"] <= MIN_EFFECT:
            failures.append("TARGET_NOT_POSITIVE_VS_NULL:"+":".join(key))
        if g["SIGN_FLIP"] >= g["NULL"] - MIN_EFFECT:
            failures.append("SIGN_FLIP_NOT_REVERSAL:"+":".join(key))
        for ctrl in ("ORTHOGONAL","PERMUTED","NUISANCE"):
            if g["TARGET"] - g[ctrl] <= MIN_EFFECT:
                failures.append("TARGET_NOT_ABOVE_CONTROL:"+ctrl+":"+":".join(key))
    for fam in sorted(family_grammars):
        for target in STATES:
            for code in CODES:
                vals=[cell_counts[(fam,target,code,pol)] for pol in POLARITIES]
                if min(vals,default=0) < MIN_CELL_REPLICATES:
                    failures.append(f"CELL_REPLICATION_LOW:{fam}:{target}:{code}")
                if len(set(vals)) != 1:
                    failures.append(f"POLARITY_COUNTERBALANCE_FAIL:{fam}:{target}:{code}")
        fam_counts=[cell_counts[(fam,target,code,pol)] for target in STATES for code in CODES for pol in POLARITIES]
        if not fam_counts or min(fam_counts) < MIN_CELL_REPLICATES or len(set(fam_counts)) != 1:
            failures.append(f"FULL_TARGET_CODE_POLARITY_FACTORIAL_FAIL:{fam}")
        topologies=sorted({top for (f,t,top),n in topology_counts.items() if f==fam and n>0})
        if len(topologies) < 2:
            failures.append(f"PROOF_TOPOLOGY_DIVERSITY_LOW:{fam}")
        for top in topologies:
            vals=[topology_counts[(fam,target,top)] for target in STATES]
            if min(vals,default=0) < MIN_CELL_REPLICATES or len(set(vals)) != 1:
                failures.append(f"PROOF_TOPOLOGY_TARGET_COUNTERBALANCE_FAIL:{fam}:{top}")
    for fam, by_target in length_signatures.items():
        if set(by_target) != set(STATES):
            failures.append(f"POSITION_LENGTH_TARGET_COVERAGE_FAIL:{fam}")
        else:
            sigs=[by_target[s] for s in STATES]
            if any(sig != sigs[0] for sig in sigs[1:]):
                failures.append(f"POSITION_LENGTH_TARGET_DISTRIBUTION_MISMATCH:{fam}")
    pos=a.get("position_length_design")
    if not isinstance(pos,dict):
        failures.append("POSITION_LENGTH_DESIGN_REQUIRED")
    else:
        if pos.get("tokenizer_identity_bound_to_pinned_runtime") is not True:
            failures.append("TOKENIZER_IDENTITY_BINDING_REQUIRED")
        if pos.get("length_position_nuisance_fit_calibration_only_and_frozen") is not True:
            failures.append("POSITION_LENGTH_NUISANCE_FREEZE_REQUIRED")
        if pos.get("target_token_count_predictability_above_null") is not False:
            failures.append("TARGET_TOKEN_COUNT_PREDICTABILITY_FORBIDDEN")
    per_target_polarity={}
    for fam in sorted(family_grammars):
        for target in STATES:
            for pol in POLARITIES:
                ds=[g["TARGET"]-g["NULL"] for (f,t,c,p,r),g in groups.items()
                    if f==fam and t==target and p==pol and set(g)==set(CONTROLS)]
                k=f"{fam}:{target}:{pol}"
                per_target_polarity[k]=_mean(ds) if ds else None
                if not ds or _mean(ds) <= MIN_EFFECT:
                    failures.append(f"PER_TARGET_POLARITY_EFFECT_NOT_POSITIVE:{k}")
    if admitted_rank == "ONE_DIMENSIONAL_SUPPORTED":
        if a.get("rank1_signed_coordinate_reversal_verified") is not True:
            failures.append("RANK1_SIGNED_COORDINATE_REVERSAL_REQUIRED")
    elif admitted_rank == "TWO_DIMENSIONAL_REQUIRED":
        if a.get("rank2_target_to_target_displacement_verified") is not True:
            failures.append("RANK2_TARGET_TO_TARGET_DISPLACEMENT_REQUIRED")
        if a.get("simple_sign_flip_used_as_semantic_opposite") is not False:
            failures.append("RANK2_SIGN_FLIP_SEMANTIC_OPPOSITE_FORBIDDEN")
    return {
        "families":len(family_grammars),
        "task_grammars":len(set(family_grammars.values())),
        "groups":len(groups),
        "full_factorial":"TARGET_3_X_CODE_3_X_POLARITY_2",
        "per_target_polarity_mean_target_vs_null":per_target_polarity,
        "position_length_target_distributions_equal": not any(f.startswith("POSITION_LENGTH_TARGET_DISTRIBUTION_MISMATCH") for f in failures),
    }

def _off_target(a: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    rows=a.get("off_target_rows")
    if not isinstance(rows,list) or not rows:
        failures.append("OFF_TARGET_ROWS_REQUIRED"); return {}
    groups=collections.defaultdict(dict)
    for i,row in enumerate(rows):
        p=f"OFFTARGET_{i}"
        if not isinstance(row,dict):
            failures.append(p+"_OBJECT_REQUIRED"); continue
        fam=row.get("family_id"); rep=row.get("replicate_id"); ctrl=row.get("control"); score=row.get("unrelated_task_margin")
        if not isinstance(fam,str) or not fam or not isinstance(rep,str) or not rep or ctrl not in ("TARGET","NULL") or not _num(score):
            failures.append(p+"_FIELDS_INVALID"); continue
        key=(fam,rep)
        if ctrl in groups[key]: failures.append(p+"_DUPLICATE_CONTROL")
        groups[key][ctrl]=float(score)
    byfam=collections.defaultdict(list)
    for key,g in groups.items():
        if set(g)!= {"TARGET","NULL"}:
            failures.append("OFF_TARGET_CONTROL_SET_INCOMPLETE:"+":".join(key)); continue
        byfam[key[0]].append(g["TARGET"]-g["NULL"])
    means={}
    for fam,ds in byfam.items():
        means[fam]=_mean(ds)
        if abs(means[fam]) > MAX_OFF_TARGET_ABS_DELTA:
            failures.append("OFF_TARGET_EFFECT_TOO_LARGE:"+fam)
    if len(byfam) < MIN_HOLDOUT_FAMILIES:
        failures.append("OFF_TARGET_FAMILY_COVERAGE_LOW")
    return {"family_mean_delta":means,"groups":len(groups)}

def adjudicate(candidate: Any) -> dict[str, Any]:
    failures=[]
    if not isinstance(candidate,dict):
        candidate={}; failures.append("ATTESTATION_OBJECT_REQUIRED")
    if candidate.get("schema") != ATTESTATION_SCHEMA:
        failures.append("ATTESTATION_SCHEMA_MISMATCH")
    settings=_settings(candidate,failures)
    geometry=_geometry(candidate,failures)
    rank=_rank_consistency(candidate,failures)
    causal=_causal(candidate,failures,rank)
    off=_off_target(candidate,failures)
    passed=not failures
    return {
        "schema":SCHEMA,
        "cross_task_abstract_native_control_pass":passed,
        "failures":sorted(set(failures)),
        "primary_settings":settings,
        "geometry":geometry,
        "rank_consistency":rank,
        "causal":causal,
        "off_target":off,
        "canonical_credit_minted":False,
        "canonical_semantics_promotion":False,
        "jspace_model_runtime_credit":False,
        "whole_hcu_credit":False,
        "whole_entityos_hcu_credit":False,
        "training_credit":False,
        "claim_scope_if_pass":"QWEN3_0_6B_RANK_CONSISTENT_PROOF_TOPOLOGY_MATCHED_CROSS_TASK_NATIVE_CONTROL_COMPONENT_ONLY",
        "evidence_boundary":"Strict cross-task/fixed-gain/rank-consistent/proof-topology-matched/bidirectional/off-target adjudication only; no model execution or canonical/global J-Space credit."
    }
