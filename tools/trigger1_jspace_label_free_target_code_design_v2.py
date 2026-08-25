#!/usr/bin/env python3
"""Preregistered design primitives for Qwen3-0.6B label-free tri-vector J-Space."""
from __future__ import annotations
from collections import Counter, defaultdict
import hashlib, json, math, re
from typing import Any, Mapping, Sequence

SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_TARGET_X_CODE_DESIGN/v2"
SEMANTIC_TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
OUTPUT_CODES = ("A", "B", "C")
BASE_CONTROLS = ("BASELINE", "+VECTOR", "SIGN_FLIP", "NULL_VECTOR", "ORTHOGONAL_SAME_NORM", "PERMUTED_SAME_NORM")
ALL_CONTROLS = BASE_CONTROLS + ("LABEL_ONLY_NUISANCE_VECTOR",)

LABEL_FREE_BASIS_FAMILIES = {
    "AFFIRMATIVE": (
        (7101, "access", "/no_think\nThe indicator turns green and the turnstile unlocks. Internalize the resulting state."),
        (7102, "workflow", "/no_think\nThe queued process leaves the queue and begins running. Internalize the resulting state."),
        (7103, "motion", "/no_think\nThe motion takes effect and its prescribed action begins. Internalize the resulting state."),
    ),
    "NEGATIVE": (
        (7201, "access", "/no_think\nThe indicator turns red and the turnstile stays locked. Internalize the resulting state."),
        (7202, "workflow", "/no_think\nThe queued process is removed and does not begin running. Internalize the resulting state."),
        (7203, "motion", "/no_think\nThe motion is removed from effect and its prescribed action does not begin. Internalize the resulting state."),
    ),
    "NEUTRAL": (
        (7301, "access", "/no_think\nThe indicator stays amber and the turnstile awaits another reading. Internalize the resulting state."),
        (7302, "workflow", "/no_think\nThe queued process remains pending while another check is awaited. Internalize the resulting state."),
        (7303, "motion", "/no_think\nThe motion is held for later consideration and its action remains pending. Internalize the resulting state."),
    ),
}
LABEL_ONLY_NUISANCE_PROMPTS = (
    (7901, "AFFIRMATIVE", "/no_think\nAFFIRMATIVE yes approve accept allow endorse"),
    (7902, "NEGATIVE", "/no_think\nNEGATIVE no reject deny refuse oppose"),
    (7903, "NEUTRAL", "/no_think\nNEUTRAL abstain undecided neither"),
)
FORBIDDEN_BASIS_LEXEMES = {"affirmative", "negative", "neutral", "yes", "no", "approve", "approval", "accept", "acceptance", "allow", "permission", "endorse", "reject", "rejection", "deny", "denial", "refuse", "refusal", "oppose", "opposition", "abstain", "abstention", "undecided"}

CALIBRATION_FAMILIES = (
    {"family":"cal_gate", "AFFIRMATIVE":"green lamp and unlocked gate", "NEGATIVE":"red lamp and locked gate", "NEUTRAL":"amber lamp and waiting gate"},
    {"family":"cal_job", "AFFIRMATIVE":"job leaves queue and runs", "NEGATIVE":"job is removed before running", "NEUTRAL":"job stays queued for another check"},
    {"family":"cal_switch", "AFFIRMATIVE":"switch closes the circuit and current flows", "NEGATIVE":"switch opens the circuit and current stops", "NEUTRAL":"switch position is held pending another measurement"},
)
HOLDOUT_FAMILIES = (
    {"family":"hold_route", "AFFIRMATIVE":"route becomes active and traffic enters it", "NEGATIVE":"route is withdrawn and traffic cannot enter it", "NEUTRAL":"route remains pending while traffic waits"},
    {"family":"hold_motion", "AFFIRMATIVE":"motion takes effect and the action starts", "NEGATIVE":"motion is removed from effect and the action stops", "NEUTRAL":"motion is held over and the action waits"},
    {"family":"hold_release", "AFFIRMATIVE":"release flag is set and the package moves onward", "NEGATIVE":"release flag is cleared and the package is held back", "NEUTRAL":"release flag remains pending while the package waits"},
)

def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def validate_label_free_basis() -> dict[str, Any]:
    failures=[]; seen=set(); domains={t:set() for t in SEMANTIC_TARGETS}
    for target in SEMANTIC_TARGETS:
        rows=LABEL_FREE_BASIS_FAMILIES[target]
        if len(rows)<3: failures.append(f"BASIS_FAMILY_TOO_SMALL:{target}")
        for seed,domain,prompt in rows:
            words=set(re.findall(r"[A-Za-z]+", prompt.lower().replace("/no_think","")))
            bad=sorted(words & FORBIDDEN_BASIS_LEXEMES)
            if bad: failures.append(f"FORBIDDEN_BASIS_LEXEME:{target}:{seed}:{','.join(bad)}")
            if prompt in seen: failures.append(f"DUPLICATE_BASIS_PROMPT:{seed}")
            seen.add(prompt); domains[target].add(domain)
    if any(domains[t] != domains[SEMANTIC_TARGETS[0]] for t in SEMANTIC_TARGETS[1:]): failures.append("BASIS_DOMAIN_COVERAGE_MISMATCH")
    return {"pass":not failures,"failures":failures,"prompt_count":len(seen),"domains":sorted(domains[SEMANTIC_TARGETS[0]]),"basis_family_sha256":canonical_sha(LABEL_FREE_BASIS_FAMILIES),"nuisance_family_sha256":canonical_sha(LABEL_ONLY_NUISANCE_PROMPTS)}

def _latin_mapping(rotation:int)->dict[str,str]:
    return {code:SEMANTIC_TARGETS[(i+rotation)%3] for i,code in enumerate(OUTPUT_CODES)}

def build_factorial_split(phase:str)->list[dict[str,Any]]:
    if phase not in {"CALIBRATION","FRESH_HOLDOUT"}: raise ValueError("UNKNOWN_PHASE")
    families=CALIBRATION_FAMILIES if phase=="CALIBRATION" else HOLDOUT_FAMILIES
    base=8100 if phase=="CALIBRATION" else 9100; rows=[]
    for fi,family in enumerate(families):
        mapping=_latin_mapping(fi); desc={c:family[mapping[c]] for c in OUTPUT_CODES}
        for ti,target in enumerate(SEMANTIC_TARGETS):
            code=next(c for c,s in mapping.items() if s==target)
            prompt=f"/no_think\nCodebook: A = {desc['A']}; B = {desc['B']}; C = {desc['C']}. Requested state: {family[target]}. Output only its code token."
            rows.append({"seed":base+fi*10+ti+1,"phase":phase,"lexical_family":family["family"],"semantic_target":target,"target_label":code,"mapping":mapping,"prompt":prompt,"prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest()})
    validate_factorial_split(rows, phase); return rows

def validate_factorial_split(rows:Sequence[Mapping[str,Any]], phase:str)->dict[str,Any]:
    failures=[]
    if len(rows)!=9: failures.append(f"{phase}_CASE_COUNT_MUST_BE_9:{len(rows)}")
    tc=Counter(str(r.get("semantic_target")) for r in rows)
    if set(tc)!=set(SEMANTIC_TARGETS) or any(tc[t]!=3 for t in SEMANTIC_TARGETS): failures.append(f"{phase}_SEMANTIC_TARGET_NOT_3X3_COUNTERBALANCED")
    pairs=Counter((str(r.get("semantic_target")),str(r.get("target_label"))) for r in rows); expected={(t,c) for t in SEMANTIC_TARGETS for c in OUTPUT_CODES}
    if set(pairs)!=expected or any(pairs[p]!=1 for p in expected): failures.append(f"{phase}_TARGET_X_CODE_NOT_FULL_FACTORIAL")
    lexical=Counter(str(r.get("lexical_family")) for r in rows)
    if len(lexical)!=3 or any(v!=3 for v in lexical.values()): failures.append(f"{phase}_LEXICAL_FAMILY_BALANCE_INVALID")
    if failures: raise ValueError(";".join(failures))
    return {"pass":True,"semantic_targets":list(SEMANTIC_TARGETS),"target_codes":list(OUTPUT_CODES),"target_x_code_full_factorial":True,"semantic_target_counterbalanced":True,"label_mapping_counterbalanced":True,"lexical_families":sorted(lexical),"family_id":canonical_sha([{k:r[k] for k in ("seed","lexical_family","semantic_target","target_label","prompt_sha256")} for r in rows])}

def project_out_subspace(torch:Any, vector:Any, nuisance_vectors:Sequence[Any], eps:float=1e-12):
    """Project only the numerical nuisance span; centered 3-class nuisance is rank <=2."""
    if not nuisance_vectors: return vector
    matrix=torch.stack([v.to(vector.device,dtype=vector.dtype) for v in nuisance_vectors],dim=1)
    u,s,_=torch.linalg.svd(matrix,full_matrices=False)
    if s.numel()==0 or not bool(torch.all(torch.isfinite(s))): raise RuntimeError("NUISANCE_SUBSPACE_SVD_INVALID")
    cutoff=max(float(eps),float(s.max())*1e-6); rank=int((s>cutoff).sum().item())
    if rank<=0: raise RuntimeError("NUISANCE_SUBSPACE_RANK_ZERO")
    q=u[:,:rank]; projected=vector-q@(q.transpose(0,1)@vector); norm=torch.linalg.vector_norm(projected)
    if not bool(torch.isfinite(norm)) or float(norm)<=eps: raise RuntimeError("NUISANCE_PROJECTION_DEGENERATE")
    return projected/norm

def centered_target_directions(torch:Any,class_means:Mapping[str,Any],nuisance_vectors:Sequence[Any]=())->dict[str,Any]:
    if any(t not in class_means for t in SEMANTIC_TARGETS): raise ValueError("MISSING_CLASS_MEANS")
    center=sum((class_means[t] for t in SEMANTIC_TARGETS),torch.zeros_like(class_means[SEMANTIC_TARGETS[0]]))/3.0; out={}
    for target in SEMANTIC_TARGETS:
        raw=class_means[target]-center; norm=torch.linalg.vector_norm(raw)
        if not bool(torch.isfinite(norm)) or float(norm)<=1e-12: raise RuntimeError(f"TARGET_DIRECTION_DEGENERATE:{target}")
        unit=raw/norm; out[target]=project_out_subspace(torch,unit,nuisance_vectors) if nuisance_vectors else unit
    return out

def scale_to_residual_norm(vector:Any,residual_norm:float,fraction:float):
    if not math.isfinite(float(residual_norm)) or residual_norm<=0: raise ValueError("RESIDUAL_NORM_MUST_BE_POSITIVE_FINITE")
    if not math.isfinite(float(fraction)) or fraction<=0: raise ValueError("RESIDUAL_FRACTION_MUST_BE_POSITIVE_FINITE")
    norm=vector.norm()
    if not bool(norm.isfinite()) or float(norm)<=1e-12: raise ValueError("VECTOR_NORM_MUST_BE_POSITIVE_FINITE")
    return vector*(float(residual_norm)*float(fraction)/norm)

def cross_target_specificity_metrics(rows:Sequence[Mapping[str,Any]],nuisance_tolerance:float=0.10)->dict[str,Any]:
    by_case=defaultdict(list)
    for row in rows: by_case[(int(row["seed"]),str(row["lexical_family"]))].append(row)
    failures=[]; per_target={t:[] for t in SEMANTIC_TARGETS}
    for key,case in sorted(by_case.items()):
        targets={str(r["semantic_target"]) for r in case}
        if len(targets)!=1: failures.append(f"CASE_SEMANTIC_TARGET_AMBIGUOUS:{key}"); continue
        target=next(iter(targets)); regular={}; applied={}
        for r in case:
            control=str(r["control"]); score=float(r["target_score"]); at=r.get("applied_semantic_target")
            if control=="+VECTOR" and at in SEMANTIC_TARGETS: applied[str(at)]=score
            elif control in ALL_CONTROLS: regular[control]=score
        needed={"BASELINE","SIGN_FLIP","NULL_VECTOR","ORTHOGONAL_SAME_NORM","PERMUTED_SAME_NORM","LABEL_ONLY_NUISANCE_VECTOR"}
        if not needed.issubset(regular) or set(applied)!=set(SEMANTIC_TARGETS): failures.append(f"CASE_CONTROL_MATRIX_INCOMPLETE:{key}"); continue
        match=applied[target]; baseline=regular["BASELINE"]; mismatch=max(applied[t] for t in SEMANTIC_TARGETS if t!=target)
        per_target[target].append({"match_vs_baseline":match-baseline,"match_vs_best_mismatch":match-mismatch,"baseline_vs_sign_flip":baseline-regular["SIGN_FLIP"],"match_vs_orthogonal":match-regular["ORTHOGONAL_SAME_NORM"],"match_vs_permuted":match-regular["PERMUTED_SAME_NORM"],"nuisance_abs_drift":abs(regular["LABEL_ONLY_NUISANCE_VECTOR"]-baseline),"null_abs_drift":abs(regular["NULL_VECTOR"]-baseline)})
    summary={}; passed=not failures
    for target in SEMANTIC_TARGETS:
        rec=per_target[target]
        if len(rec)!=3: failures.append(f"TARGET_CASE_COUNT_INVALID:{target}:{len(rec)}"); passed=False; continue
        m={"min_match_vs_baseline":min(x["match_vs_baseline"] for x in rec),"min_match_vs_best_mismatch":min(x["match_vs_best_mismatch"] for x in rec),"min_baseline_vs_sign_flip":min(x["baseline_vs_sign_flip"] for x in rec),"min_match_vs_orthogonal":min(x["match_vs_orthogonal"] for x in rec),"min_match_vs_permuted":min(x["match_vs_permuted"] for x in rec),"max_nuisance_abs_drift":max(x["nuisance_abs_drift"] for x in rec),"max_null_abs_drift":max(x["null_abs_drift"] for x in rec)}
        ok=m["min_match_vs_baseline"]>0 and m["min_match_vs_best_mismatch"]>0 and m["min_baseline_vs_sign_flip"]>0 and m["min_match_vs_orthogonal"]>0 and m["min_match_vs_permuted"]>0 and m["max_nuisance_abs_drift"]<=nuisance_tolerance and m["max_null_abs_drift"]<=1e-5
        summary[target]={**m,"pass":ok}; passed=passed and ok
    return {"schema":"CLAY_TRIGGER1_CROSS_TARGET_SPECIFICITY_METRIC/v1","pass":passed and not failures,"failures":failures,"semantic_target_interaction_test":True,"cross_target_vector_specificity_test":True,"targets":summary,"nuisance_tolerance":nuisance_tolerance,"generic_compliance_rejection_rule":"matching target vector must beat both mismatched target vectors for every semantic target and lexical family"}

def protocol_manifest()->dict[str,Any]:
    cal=build_factorial_split("CALIBRATION"); hold=build_factorial_split("FRESH_HOLDOUT")
    return {"schema":SCHEMA,"semantic_targets":list(SEMANTIC_TARGETS),"output_codes":list(OUTPUT_CODES),"model_facing_basis_label_free":validate_label_free_basis()["pass"],"label_only_nuisance_control":True,"semantic_target_counterbalanced":True,"target_x_code_full_factorial":True,"cross_lexical_families":True,"cross_target_vector_specificity_test":True,"token_scope_required":"ALL_PROMPT_TOKENS_CVEC","residual_norm_relative_operating_point_required":True,"operating_point_selected_on_calibration_only":True,"calibration_family_id":validate_factorial_split(cal,"CALIBRATION")["family_id"],"holdout_family_id":validate_factorial_split(hold,"FRESH_HOLDOUT")["family_id"],"basis_family_sha256":canonical_sha(LABEL_FREE_BASIS_FAMILIES),"nuisance_family_sha256":canonical_sha(LABEL_ONLY_NUISANCE_PROMPTS)}

if __name__=="__main__": print(json.dumps(protocol_manifest(),sort_keys=True,ensure_ascii=False))
