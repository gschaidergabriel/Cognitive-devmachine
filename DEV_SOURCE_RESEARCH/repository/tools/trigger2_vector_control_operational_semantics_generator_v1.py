#!/usr/bin/env python3
"""Trigger-2 vector-control operational-semantics candidate generator v1.

METHOD_ONLY / SYNTHETIC_HARD_NEGATIVE source design. It emits 21 non-training-eligible
candidate rows across seven provenance-disjoint families. Every row carries the semantic
Hyperposition frame so vector control is learned as an evidence-bounded operational relation,
not as a unique raw-vector identity. This generator cannot mint canonical truth, J-Space,
HCU, EntityOS, accepted-dataset-token, or training credit.
"""
from __future__ import annotations
import hashlib, json

ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
HP_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION/v1"
ARTIFACT_ID = "TRIGGER2_VECTOR_CONTROL_OPERATIONAL_SEMANTICS_SEED"
ARTIFACT_VERSION = "v1"
SUPERVISOR = "8.78"
MAIN_AT_DESIGN = "c8a03f457473d58f0027826cd707f5b455484898"
ANTI = ["NO_MAJORITY_AS_TRUTH","NO_SALIENCE_AS_PROBABILITY","NO_RECURRENCE_AS_EVIDENCE","NO_SILENT_BRANCH_DROP","PROJECTION_IS_NOT_DELETION"]

SOURCES = {
 "NON_IDENTIFIABILITY": {"url":"https://arxiv.org/html/2602.06801v3","claim":"Behaviorally equivalent steering interventions can form non-identifiable equivalence classes; raw direction is not unique semantic truth."},
 "ACTADD": {"url":"https://arxiv.org/abs/2308.10248","claim":"Intermediate-activation additions can causally steer high-level output properties."},
 "STEERING_RELIABILITY": {"url":"https://arxiv.org/abs/2505.22637","claim":"Steering effects can be high-variance across samples and depend on activation-difference geometry."},
 "FUNCTION_VECTORS": {"url":"https://arxiv.org/abs/2310.15213","claim":"Compact function representations can have causal cross-context effects; composition is partial rather than guaranteed."},
 "VARIABLE_BINDING": {"url":"https://arxiv.org/abs/2505.20896","claim":"Systematic variable binding can emerge after shallow heuristic phases; causal interventions implicate memory/routing mechanisms."},
 "REFT": {"url":"https://arxiv.org/abs/2404.03592","claim":"Representation finetuning can learn task-specific hidden-state interventions with frozen base weights."},
 "CLAY_SUPERVISOR_8_78": {"path":"research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_78.json","claim":"Qwen3-0.6B transport components remain bounded credit while frozen structural label-free native v1 is behaviorally falsified."},
}

FAMILIES = [
 {"id":"VCOS_F1_NONIDENTIFIABILITY","split":"TRAIN","relation":"JSPACE_VECTOR_CONTROL_EVIDENCE_BOUNDARY","scenario":"Two distinct hidden-state steering vectors produce indistinguishable target behavior on the declared test battery.","shortcut":"Choose the vector with the larger norm as the canonical semantic axis.","unknown":"The vectors agree on the current battery but no off-target, layer-swap or fresh-context controls were run.","target":"Do not declare either raw vector the unique semantic meaning. Record an operational equivalence class bound to model, layer, context, intervention site, strength and measured causal signature.","sources":["NON_IDENTIFIABILITY","ACTADD"]},
 {"id":"VCOS_F2_RELIABILITY","split":"TRAIN","relation":"JSPACE_VECTOR_CONTROL_ROBUSTNESS","scenario":"A steering direction helps on average, but individual prompts show high variance and some opposite-signed effects.","shortcut":"Promote because the mean steering score is positive.","unknown":"The mean is positive but activation-difference geometry is heterogeneous and fresh-family stability is unknown.","target":"Keep the semantic-control claim conditional. Require held-out prompt-family consistency, effect-size distribution, sign stability and off-target preservation before promotion.","sources":["STEERING_RELIABILITY"]},
 {"id":"VCOS_F3_LAYER_CONTEXT_IDENTITY","split":"TRAIN","relation":"JSPACE_VECTOR_CONTROL_ABI","scenario":"A direction is effective at one layer and prompt family, but transfer to another layer or context has not been measured.","shortcut":"Reuse the same vector everywhere because cosine similarity is high.","unknown":"The source layer passes, but target-layer equivalence has no causal intervention evidence.","target":"Bind the control label to exact model/checkpoint, intervention site, prompt family, token-position policy and strength. Transfer is a new hypothesis, not inherited truth.","sources":["STEERING_RELIABILITY","NON_IDENTIFIABILITY"]},
 {"id":"VCOS_F4_COMPOSITION","split":"TRAIN","relation":"HYPERPOSITION_MULTI_CONTROL_COMPOSITION","scenario":"Two independently useful control vectors are proposed for simultaneous composition.","shortcut":"Assume vector addition preserves both meanings exactly because each vector works alone.","unknown":"Single-vector effects pass, but the joint intervention has not been causally characterized.","target":"Treat composition as a separate branch-level hypothesis. Measure each vector alone, composition, interference, order/strength sensitivity and off-target loss; preserve unresolved alternatives if composition is not clean.","sources":["FUNCTION_VECTORS"]},
 {"id":"VCOS_F5_DYNAMIC_BINDING","split":"TRAIN","relation":"DYNAMIC_VARIABLE_BINDING_AND_ROUTING","scenario":"A model solves shallow variable dereferencing but accuracy collapses when bindings are permuted, distractor chains are added, or depth increases.","shortcut":"Call shallow success evidence of a general variable-binding mechanism.","unknown":"The current benchmark cannot distinguish early-position heuristics from systematic routing.","target":"Classify the current behavior as heuristic. Train and evaluate role-filler permutations, distractors, depth variation, episode-local codebook remaps and full nuisance crossing before systematic-binding credit.","sources":["VARIABLE_BINDING","FUNCTION_VECTORS"]},
 {"id":"VCOS_F6_REPRESENTATION_FINETUNING","split":"VALIDATION","relation":"REPRESENTATION_LEVEL_SPECIALIZATION","scenario":"A low-rank representation intervention improves task accuracy while base weights remain frozen.","shortcut":"Treat better task accuracy as proof that the learned subspace is the canonical internal language.","unknown":"Performance improves, but semantic identifiability and cross-context causal stability are untested.","target":"Count this as a candidate specialization mechanism only. Evaluate causal effect, off-target retention, prompt-family transfer, layer sensitivity and J-Space-ABI interaction; task gain alone does not establish a unique semantic axis.","sources":["REFT"]},
 {"id":"VCOS_F7_PROJECT_NATIVE_CVEC_FAILURE","split":"HOLDOUT","relation":"QWEN06_JSPACE_CAUSAL_PROMOTION","scenario":"Project evidence shows Qwen3-0.6B hidden-state specificity and native llama.cpp cvec transport components passed, while the frozen structural label-free native discriminator failed behaviorally.","shortcut":"Convert transport success into positive semantic-control training labels.","unknown":"The mechanism transports intervention coordinates, but correct label-independent behavioral semantics were not established.","target":"Preserve component transport credit but block canonical semantic/J-Space promotion. A successor must be separately versioned and preregistered before opening a fresh holdout.","sources":["CLAY_SUPERVISOR_8_78"]},
]

def hp(fid: str, variant: str, resolved: str | None, evidence: str) -> dict:
    support_ev = [evidence] if resolved == "b_supported" else []
    reject_ev = [evidence] if resolved == "b_rejected" else []
    unknown_ev = [evidence] if resolved is None else []
    return {
      "schema": HP_SCHEMA, "query_id": f"{fid}:{variant}", "canonical_truth_allowed": False,
      "collapse_rule": "ONLY_SYNTHETIC_PROOF_OR_EXPLICIT_DISCRIMINATOR", "anti_collapse": ANTI,
      "projection": {"operation":"NONDESTRUCTIVE_VIEW","context":"CURRENT_EPISODE"},
      "branches": [
        {"branch_id":"b_supported","value":"CONTROL_CLAIM_SUPPORTED","context_predicate":"CURRENT_EPISODE","evidence_for":support_ev,"evidence_against":reject_ev,"falsifier":"fresh matched causal controls contradict the claimed operational effect","validity":"LIVE","provenance":"SYNTHETIC_METHOD_EPISODE","epistemic_status":"HYPOTHESIS"},
        {"branch_id":"b_rejected","value":"CONTROL_CLAIM_REJECTED","context_predicate":"CURRENT_EPISODE","evidence_for":reject_ev,"evidence_against":support_ev,"falsifier":"fresh matched causal controls establish the rejected claim","validity":"LIVE","provenance":"SYNTHETIC_METHOD_EPISODE","epistemic_status":"COUNTERHYPOTHESIS"},
        {"branch_id":"b_unresolved","value":"CONTROL_CLAIM_UNRESOLVED","context_predicate":"CURRENT_EPISODE","evidence_for":unknown_ev,"evidence_against":[],"falsifier":"a preregistered discriminator resolves the operational claim","validity":"LIVE","provenance":"SYNTHETIC_METHOD_EPISODE","epistemic_status":"UNKNOWN"},
      ],
      "task_resolution": {"status":"UNRESOLVED","resolved_branch":None} if resolved is None else {"status":"RESOLVED_WITHIN_SYNTHETIC_WORLD","resolved_branch":resolved}
    }

def make_row(f: dict, variant: str, evidence_class: str, prompt: str, target: str, resolved: str | None, fact_status: str) -> dict:
    ev = f"{f['id']}:{variant}"
    row = {
      "schema": ROW_SCHEMA, "artifact_id": ARTIFACT_ID, "artifact_version": ARTIFACT_VERSION,
      "row_version":"v1", "status":"CURRENT_CANDIDATE_NOT_TRAINING_ELIGIBLE",
      "predecessor":None, "successor":None,
      "revision_reason":"Operationalize vector semantics and prevent unique-vector/transport-as-semantics shortcuts.",
      "family_id":f["id"], "provenance_ancestry_id":f"trigger2-vcos-v1:{f['id']}", "split":f["split"],
      "split_unit":"CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY", "selected_using_holdout":False,
      "training_eligible":False, "canonical_truth_allowed":False, "direct_effect_authority":False,
      "evidence_class":evidence_class, "reality_level":"R3" if evidence_class == "SYNTHETIC_HARD_NEGATIVE" else "R2",
      "fact_status":fact_status, "target_type":"VECTOR_CONTROL_OPERATIONAL_SEMANTICS_AND_EVIDENCE_BOUNDARY",
      "target_architecture_relation":f["relation"], "model_visible_fields":["prompt"], "supervision_field":"target",
      "prompt":prompt, "target":target, "semantic_hyperposition":hp(f["id"], variant, resolved, ev),
      "source_provenance":[{"id":sid, **SOURCES[sid]} for sid in f["sources"]],
      "authority_snapshot":{"supervisor_epoch":SUPERVISOR,"main_sha":MAIN_AT_DESIGN,"mode":"FREE_ONLY"},
    }
    material=json.dumps(row,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    row["row_sha256"]=hashlib.sha256(material.encode()).hexdigest()
    return row

def rows() -> list[dict]:
    out=[]
    for f in FAMILIES:
      out.append(make_row(f,"V1","METHOD_ONLY",f"Scenario: {f['scenario']}\nDecision rule: select only the claim licensed by the stated evidence boundary.\nWhat should Xeno learn?",f["target"],"b_supported","NOT_APPLICABLE"))
      out.append(make_row(f,"V2","SYNTHETIC_HARD_NEGATIVE",f"Scenario: {f['scenario']}\nA reviewer proposes: {f['shortcut']}\nShould this shortcut be accepted?","Reject. "+f["target"],"b_rejected","NOT_APPLICABLE"))
      out.append(make_row(f,"V3","METHOD_ONLY",f"Scenario: {f['unknown']}\nWhat epistemic state should the control claim occupy?","Keep CONTROL_CLAIM_UNRESOLVED. "+f["target"],None,"UNKNOWN"))
    return out

def validate(rr: list[dict]) -> dict:
    failures=[]
    if len(rr)!=21: failures.append("ROW_COUNT")
    fams={r['family_id'] for r in rr}
    if len(fams)!=7: failures.append("FAMILY_COUNT")
    if any(r.get('training_eligible') is not False for r in rr): failures.append("TRAINING_ELIGIBILITY")
    if any(r.get('canonical_truth_allowed') is not False or r.get('direct_effect_authority') is not False for r in rr): failures.append("AUTHORITY_LEAK")
    if any('semantic_hyperposition' not in r for r in rr): failures.append("MISSING_HYPERPOSITION")
    split_by_family={f:{r['split'] for r in rr if r['family_id']==f} for f in fams}
    if any(len(v)!=1 for v in split_by_family.values()): failures.append("FAMILY_SPLIT_LEAK")
    if {r['split'] for r in rr if r['family_id']=='VCOS_F7_PROJECT_NATIVE_CVEC_FAILURE'} != {'HOLDOUT'}: failures.append("PROJECT_NATIVE_NOT_HOLDOUT")
    return {"schema":"TRIGGER2_VCOS_GENERATOR_SELFTEST/v1","pass":not failures,"failures":failures,"rows":len(rr),"families":len(fams),"training_credit_minted":False}

if __name__ == '__main__':
    rr=rows()
    print(json.dumps(validate(rr),sort_keys=True))
    for r in rr:
        print(json.dumps(r,sort_keys=True,separators=(",",":"),ensure_ascii=False))
