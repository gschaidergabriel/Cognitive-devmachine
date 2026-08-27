#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

SCHEMA="h1-reference-freeze-0.1"
PLANES=[
"sensor/reflex ingress","recurrent PerceptualField","Unified Memory/world/self/goals",
"RecognitionValidity + AdaptiveStatePromotion","CognitiveFrame/epochs/Active Assembly",
"Thalamus/attention/access control","GWT competition/WorkspaceEpisode","typed reader/model uptake",
"personality/value/goals/slow adaptation","causal observability/replay","external effect authority/sandbox",
"UnifiedDB/ClayGraph publication","runtime placement/one-module lowering"]
REQ_ROLES={"full_lineage_fusion","loop_projection","clay_native_contract","digital_retina_contract","adaptive_visual_learning_directive"}
MARKERS={
"full_lineage_fusion":["C9 + owner-fixed Clay-native/Retina/online-learning contracts","The Thalamus is retained as a core logical organ","The target organism can now be summarized as these logical planes",*[f"{i}. {x};" if i<13 else f"{i}. {x}." for i,x in enumerate(PLANES,1)]],
"clay_native_contract":["PROJECT-OWNER ARCHITECTURE DIRECTIVE","The target FRANK system is Clay-native end to end.","Needle is the one intentionally retained non-Clay subsystem.","There must not be a second independent semantic architecture"],
"digital_retina_contract":["PROJECT-OWNER ARCHITECTURE DIRECTIVE","Digital Retina is no longer required to survive as a semantically independent cognitive subsystem/process boundary","PerceptualField","VisualPercept","adaptive Micro Visual Classifier","Micro Visual Classifier output may silently become architectural truth"],
"adaptive_visual_learning_directive":["PROJECT-OWNER FIXED FRANK 0.1 REQUIREMENT","micro_classifier_prediction != sensor_truth","GOLD/SILVER","BRONZE one-shot/self-generated labels MUST NOT autonomously become training truth","KNOWN_HIGH_CONFIDENCE","UNKNOWN","CONFLICT","promote atomically only when gates pass","last known-good classifier/prototype state for rollback","MVC-E1","MVC-E7"],
"gwt_overlay":["Trajectory-Capacity Recurrent Workspace Control","semantic_state_hash","state_version_hash","trace_root_hash","small_step != convergence","reentry != authority"]}
REQ_ORGANS={"needle_bridge","digital_retina","clay_model_4b","semantic_state","claygraph_memory","gwt_workspace","hyperposition","loop_dynamics_controller","unifieddb_plane","effect_gateway"}
REQ_FIXED={"clay_native_semantics":True,"needle_only_intentional_foreign_semantic_subsystem":True,"digital_retina_mandatory":True,"model_output_never_mints_authority":True,"frank_self_harness_authority":"PROPOSAL_ONLY"}

def canon(v:Any)->Any:
    if isinstance(v,dict): return {str(k):canon(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,list): return [canon(x) for x in v]
    if v is None or isinstance(v,(str,int,bool)): return v
    if isinstance(v,float) and float('-inf')<v<float('inf'): return v
    raise TypeError(type(v).__name__)
def cjson(v): return json.dumps(canon(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def h(v): return hashlib.sha256(cjson(v).encode()).hexdigest()
def blob(b:bytes): return hashlib.sha1(f"blob {len(b)}\0".encode()+b).hexdigest()
def load(p:Path):
    x=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(x,dict): raise ValueError(f"{p}: object required")
    return x

def sources(root:Path,lock:dict):
    out={}; v=[]
    for i,e in enumerate(lock.get('sources') or []):
        if not isinstance(e,dict): v.append(f"sources[{i}] object required"); continue
        role,path,exp=str(e.get('role','')),str(e.get('path','')),str(e.get('git_blob_sha',''))
        if not role or not path or not exp: v.append(f"sources[{i}] role/path/git_blob_sha required"); continue
        if role in out: v.append(f"duplicate role:{role}"); continue
        p=root/path
        if not p.is_file(): v.append(f"missing source:{path}"); continue
        b=p.read_bytes(); actual=blob(b); text=b.decode('utf-8')
        if actual!=exp: v.append(f"git blob mismatch:{role}:{exp}!={actual}")
        for m in MARKERS.get(role,[]):
            if m not in text: v.append(f"{role} missing marker:{m}")
        out[role]={"role":role,"path":path,"git_blob_sha":actual,"content_sha256":hashlib.sha256(b).hexdigest()}
    for role in sorted(REQ_ROLES-set(out)): v.append(f"missing required role:{role}")
    return out,v

def validate_arch(a):
    v=[]
    if a.get('target_host')!='UBUNTU_LINUX_DEVELOPER_SYSTEM': v.append('wrong target_host')
    fixed=a.get('fixed_contracts') or {}
    for k,x in REQ_FIXED.items():
        if fixed.get(k)!=x: v.append(f"fixed_contracts.{k}!={x!r}")
    ids=[x.get('id') for x in a.get('semantic_organs') or [] if isinstance(x,dict)]
    if len(ids)!=len(set(ids)): v.append('duplicate semantic organ')
    for x in sorted(REQ_ORGANS-set(ids)): v.append(f"missing organ:{x}")
    for k in ('causal_relations','operations'):
        if not isinstance(a.get(k),list) or not a[k]: v.append(f"{k} empty")
    inv=set(a.get('invariants') or [])
    for x in ('recurrence_is_not_emergence','activation_is_not_truth','selection_is_not_authority','model_output_is_not_execution_authority','semantic_hash_is_distinct_from_exact_contract_hash'):
        if x not in inv: v.append(f"missing invariant:{x}")
    return v

def extras():
    return [
      {"id":"perceptual_field","origin":"OWNER_FIXED_DIGITAL_RETINA_OVERLAY","semantic_boundary":"CLAY_NATIVE"},
      {"id":"thalamus_attention","origin":"LINEAGE_FUSED_CORE_LOGICAL_ORGAN","semantic_boundary":"CLAY_NATIVE"},
      {"id":"micro_visual_classifier","origin":"OWNER_FIXED_ADAPTIVE_VISUAL_LEARNING_OVERLAY","semantic_boundary":"CLAY_NATIVE_STATE_WITH_NUMERICAL_BACKING"},
      {"id":"adaptive_state_promotion","origin":"LINEAGE_FUSED_AND_ADAPTIVE_LEARNING_OVERLAY","semantic_boundary":"CLAY_NATIVE"},
      {"id":"causal_observability_replay","origin":"LINEAGE_FUSED_CORE_PLANE","semantic_boundary":"CLAY_NATIVE_RECEIPTS"}]
def overlay_states():
    return {
      "PerceptualField":{"epistemic_states":["KNOWN","UNKNOWN","CONFLICT","SET_VALUED"],"required":["source_identity","capture_epoch","evidence","uncertainty","prior_vs_evidence","familiarity_support","transformation_lineage"]},
      "VisualPercept":{"kind":"AUDIT_MATERIALIZATION","required":["source_identity","capture_epoch","entities_features_relations","uncertainty","familiarity_version_when_used","visual_evidence_provenance","causal_links"]},
      "AdaptiveVisualReadout":{"outcomes":["KNOWN_HIGH_CONFIDENCE","KNOWN_NEEDS_CONFIRMATION","AMBIGUOUS","UNKNOWN","CONFLICT"],"authority":"FAMILIARITY_ROUTING_ONLY"},
      "AdaptiveVisualLearnerState":{"trust_tiers":["GOLD","SILVER","BRONZE"],"bronze_autonomous_positive_truth":False,"required":["classifier_or_prototype_version","feature_backbone_version","calibration_identity","candidate_shadow_state","current_promoted_state","last_known_good_state","resource_budget","rollback_identity","training_example_provenance"]}}

def build(root:Path,lock_path:Path):
    lock=load(lock_path); src,v=sources(root,lock)
    if 'loop_projection' not in src: return {},v
    a=load(root/src['loop_projection']['path']); v+=validate_arch(a)
    if v: return {},v
    mods=[{**x,"origin":"FRANK_LOOP_PROJECTION"} for x in a['semantic_organs']]; seen={x['id'] for x in mods}
    mods += [x for x in extras() if x['id'] not in seen]
    states=dict(a.get('state_contracts') or {}); states.update(overlay_states())
    if 'gwt_overlay' in src:
        states['TrajectoryCapacityReadoutOverlay']={"required":["semantic_state_hash","state_version_hash","trace_root_hash","residual_pressure","trajectory_geometry","state_capacity_context"],"authority":"OBSERVATION_ONLY"}
    rel=list(a.get('causal_relations') or [])
    for x in ("visual_source->digital_retina","digital_retina->perceptual_field","perceptual_field->micro_visual_classifier","micro_visual_classifier->thalamus_attention","perceptual_field->thalamus_attention","thalamus_attention->gwt_workspace","outcome_receipt->perceptual_field","outcome_receipt->adaptive_state_promotion"):
        if x not in rel: rel.append(x)
    inv=sorted(set((a.get('invariants') or [])+[
      "needle_is_only_intentional_non_clay_semantic_subsystem","digital_retina_semantics_are_clay_native","micro_visual_classifier_prediction_is_not_sensor_truth","familiarity_is_not_evidence","confidence_is_not_authority","bronze_self_labels_do_not_autonomously_become_training_truth","visual_prior_familiarity_and_sensor_evidence_are_separable","thalamus_gain_is_not_relay_is_not_causal_use","semantic_state_hash_is_not_state_version_hash_is_not_trace_root_hash","reentry_is_not_authority"]))
    core={"schema_version":SCHEMA,"canonical_parent":a.get('canonical_parent'),"target_host":a.get('target_host'),"base_architecture_id":a.get('architecture_id'),"full_architecture_basis":"C9_PLUS_OWNER_FIXED_OVERLAYS_PLUS_SURVIVING_LINEAGE","logical_planes":PLANES,"modules":sorted(mods,key=lambda x:x['id']),"state_contracts":states,"operations":a.get('operations') or [],"causal_relations":rel,"invariants":inv,"mandatory_acceptance_families":["MVC-E1","MVC-E2","MVC-E3","MVC-E4","MVC-E5","MVC-E6","MVC-E7","crash_restart_rollback_replay","long_horizon_familiar_plus_novel_visual_action_loop"],"gwt_r8_overlay_bound":'gwt_overlay' in src}
    records=[src[k] for k in sorted(src)]
    return {**core,"source_records":records,"source_lock_hash":h(records),"architecture_semantic_hash":h(core),"exact_contract_hash":h({"semantic_core":core,"source_records":records}),"freeze_status":"REFERENCE_HARNESS_ARCHITECTURE_FREEZE_CANDIDATE","release_status":"NOT_H1_RELEASE_PASS","notes":["Loop projection is a compatible vertical-slice delta, not the whole organism.","Owner-fixed Retina/MVC overlays are explicit and provenance-bound.","No ClayCode BASE PASS or live-FRANK claim is implied."]},[]

def verify(root:Path,f:dict):
    v=[]; records=f.get('source_records') or []
    if h(records)!=f.get('source_lock_hash'): v.append('source_lock_hash mismatch')
    for r in records:
        p=root/str(r.get('path',''))
        if not p.is_file(): v.append(f"missing source:{r.get('path')}"); continue
        b=p.read_bytes()
        if blob(b)!=r.get('git_blob_sha'): v.append(f"source drift:{r.get('role')}")
        if hashlib.sha256(b).hexdigest()!=r.get('content_sha256'): v.append(f"content drift:{r.get('role')}")
    keys=['schema_version','canonical_parent','target_host','base_architecture_id','full_architecture_basis','logical_planes','modules','state_contracts','operations','causal_relations','invariants','mandatory_acceptance_families','gwt_r8_overlay_bound']
    core={k:f[k] for k in keys}
    if h(core)!=f.get('architecture_semantic_hash'): v.append('architecture_semantic_hash mismatch')
    if h({'semantic_core':core,'source_records':records})!=f.get('exact_contract_hash'): v.append('exact_contract_hash mismatch')
    return v

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    b=sub.add_parser('build'); b.add_argument('--root',default='.'); b.add_argument('--source-lock',required=True); b.add_argument('--output',required=True)
    q=sub.add_parser('verify'); q.add_argument('--root',default='.'); q.add_argument('freeze')
    a=ap.parse_args(); root=Path(a.root).resolve()
    if a.cmd=='build':
        f,v=build(root,Path(a.source_lock).resolve())
        if v: print(json.dumps({'ok':False,'violations':v},indent=2)); raise SystemExit(2)
        out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'ok':True,'output':str(out),'architecture_semantic_hash':f['architecture_semantic_hash'],'exact_contract_hash':f['exact_contract_hash'],'modules':len(f['modules']),'planes':len(f['logical_planes'])},indent=2)); return
    v=verify(root,load(Path(a.freeze))); print(json.dumps({'ok':not v,'violations':v},indent=2)); raise SystemExit(0 if not v else 2)
if __name__=='__main__': main()
