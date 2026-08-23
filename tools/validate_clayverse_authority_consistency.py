#!/usr/bin/env python3
"""Compatibility-named fail-closed authority guard for current EntityOS + HCU."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

CURRENT_PROGRAM="ENTITYOS_HCU"
CURRENT_STAGE="ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
CURRENT_PRODUCT="EntityOS"
CURRENT_COMPUTE_ARCHITECTURE="HCU"
CURRENT_AUTHORITY="research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_53.json"
TRAINING_AUTHORITY="research_entity/claycode/OWNER_ONE_SHOT_08B_JSPACE_GWT_TRAINING_DIRECTIVE_2026-08-24.md"
CURRENT_SCHEMA="ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v2"
CONTROL41="research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
CONTROL42="research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
CONTROL43="research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
CONTROL44="research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
LEGACY_EXPECTED_CONTROL="4.1+4.2-execution-boundary-addendum+4.3-program-authority-addendum+4.4-clayverse-product-authority-addendum"
ROOT_CLAUDE="CLAUDE.md"
WORKER_DIRECTIVE="research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"


def load(path:Path): return json.loads(path.read_text(encoding="utf-8"))
def blob(path:Path):
    b=path.read_bytes(); return hashlib.sha1(f"blob {len(b)}\0".encode()+b).hexdigest()
def git_blob_sha(path:Path): return blob(path)
def req(err, cond, code):
    if not cond: err.append(code)
def has(s, token): return token.upper() in str(s).upper()


def validate(root:Path)->dict:
    e=[]
    p={
      "canonical":root/"research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
      "bootstrap":root/"research_entity/continuity/BOOTSTRAP_MINIMAL.json",
      "program":root/"research_entity/rooms/PROGRAM_STATE.json",
      "steering":root/CURRENT_AUTHORITY,
      "training":root/TRAINING_AUTHORITY,
      "manifest":root/"the artefact/manifest.json",
      "footer":root/"research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md",
      "architecture":root/"the artefact/ARCHITECTURE.md",
      "readme":root/"the artefact/README.md",
      "claude":root/ROOT_CLAUDE,
      "workers":root/WORKER_DIRECTIVE,
      "c41":root/CONTROL41,"c42":root/CONTROL42,"c43":root/CONTROL43,"c44":root/CONTROL44,
    }
    for n,x in p.items(): req(e,x.is_file(),f"MISSING:{n}:{x.as_posix()}")
    if e:return {"schema":CURRENT_SCHEMA,"pass":False,"errors":e}
    try: c=load(p["canonical"]); b=load(p["bootstrap"]); pr=load(p["program"]); s=load(p["steering"]); m=load(p["manifest"]); c41=load(p["c41"]);c42=load(p["c42"]);c43=load(p["c43"]);c44=load(p["c44"])
    except Exception as x:return {"schema":CURRENT_SCHEMA,"pass":False,"errors":[f"LOAD_ERROR:{type(x).__name__}:{x}"]}

    req(e,b.get("entity_id")==c.get("entity_id"),"BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    req(e,(b.get("identity") or {}).get("persistent_research_entity")=="Clay","BOOTSTRAP_PERSISTENT_ENTITY_MISMATCH")
    req(e,b.get("active_program")==CURRENT_PROGRAM,"BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    req(e,b.get("active_stage")==CURRENT_STAGE,"BOOTSTRAP_STAGE_MISMATCH")
    req(e,b.get("product_endpoint")==CURRENT_PRODUCT,"BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    req(e,b.get("integrated_cognition_compute_architecture")==CURRENT_COMPUTE_ARCHITECTURE,"BOOTSTRAP_COMPUTE_ARCHITECTURE_MISMATCH")
    req(e,b.get("authority_correction")==CURRENT_AUTHORITY,"BOOTSTRAP_AUTHORITY_POINTER_MISMATCH")
    req(e,b.get("execution_surface")=="AUTHORIZED_ISOLATED_SANDBOX_ONLY","BOOTSTRAP_EXECUTION_FENCE_MISSING")
    req(e,b.get("together_training_authority")==TRAINING_AUTHORITY,"BOOTSTRAP_TRAINING_AUTHORITY_MISMATCH")
    req(e,b.get("together_one_shot_training_consumed") is False,"BOOTSTRAP_ONE_SHOT_CONSUMPTION_MISMATCH")
    req(e,has(b.get("together_api"),"GENERAL_INFERENCE_AND_FALLBACK_FORBIDDEN"),"BOOTSTRAP_TOGETHER_GENERAL_FALLBACK_FENCE_MISSING")
    req(e,has(b.get("together_api"),"EXACTLY_ONE_OWNER_AUTHORIZED_APPROX_08B_JSPACE_GWT_FINETUNE_ALLOWED_UNTIL_CONSUMED"),"BOOTSTRAP_ONE_SHOT_TRAINING_AUTHORITY_MISSING")
    req(e,has(b.get("final_paid_model_training"),"SECOND_JOB_REQUIRES_NEW_OWNER_AUTHORIZATION"),"BOOTSTRAP_SECOND_TRAINING_GATE_MISSING")

    req(e,pr.get("program_id")=="entityos-hcu" and pr.get("status")=="ACTIVE","PROGRAM_ID_OR_STATUS_MISMATCH")
    req(e,pr.get("stage")==CURRENT_STAGE and pr.get("current_stage")==CURRENT_STAGE,"PROGRAM_STAGE_MISMATCH")
    req(e,pr.get("product")==CURRENT_PRODUCT,"PROGRAM_PRODUCT_MISMATCH")
    req(e,pr.get("integrated_cognition_compute_architecture")==CURRENT_COMPUTE_ARCHITECTURE,"PROGRAM_COMPUTE_ARCHITECTURE_MISMATCH")
    req(e,pr.get("authority_correction")==CURRENT_AUTHORITY,"PROGRAM_AUTHORITY_POINTER_MISMATCH")
    req(e,(pr.get("authority") or {}).get("external_effects")=="EffectGate+EffectJournal","PROGRAM_EFFECT_AUTHORITY_MISMATCH")
    x=pr.get("execution_policy") or {}
    req(e,x.get("free_only_default") is True,"PROGRAM_FREE_ONLY_DEFAULT_MISSING")
    req(e,x.get("isolated_sandbox_only") is True and x.get("vps_testing_forbidden") is True and x.get("self_hosted_vps_test_runners_forbidden") is True and x.get("production_host_testing_forbidden") is True,"PROGRAM_EXECUTION_FENCE_MISSING")
    req(e,x.get("together_general_inference_and_fallback_forbidden") is True,"PROGRAM_TOGETHER_GENERAL_FALLBACK_FENCE_MISSING")
    req(e,x.get("together_one_shot_08b_jspace_gwt_finetune_authorized") is True and x.get("together_one_shot_08b_jspace_gwt_finetune_consumed") is False,"PROGRAM_ONE_SHOT_TRAINING_STATE_MISMATCH")
    req(e,x.get("together_training_authority_file")==TRAINING_AUTHORITY,"PROGRAM_TRAINING_AUTHORITY_MISMATCH")
    req(e,x.get("second_together_training_requires_new_owner_authorization") is True and x.get("other_paid_fallback") is False,"PROGRAM_PAID_TRAINING_SCOPE_WEAKENED")
    tracks=pr.get("go_required_tracks") or {}
    req(e,tracks.get("track_a")=="ENTITYOS_EXECUTABLE_CONVERGENCE","PROGRAM_GO_TRACK_A_MISMATCH")
    req(e,tracks.get("track_b")=="HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT","PROGRAM_GO_TRACK_B_MISMATCH")
    req(e,tracks.get("track_c")=="GLOBAL_JSPACE_GWT_PROTOTYPE_AND_ONE_SHOT_08B_TRAINING_READINESS","PROGRAM_GO_TRACK_C_MISMATCH")
    tp=pr.get("training_program") or {}; req(e,tp.get("one_shot_job_authorized") is True and tp.get("one_shot_job_consumed") is False,"PROGRAM_TRAINING_PROGRAM_STATE_MISMATCH")
    rc=pr.get("runtime_credit") or {}; req(e,rc.get("entityos_hcu_whole_runtime_credit")==0 and rc.get("whole_product_pass") is False,"PROGRAM_RUNTIME_CREDIT_PREMATURE")

    req(e,s.get("schema_version")=="8.53" and s.get("status")=="CURRENT_EXPLICIT_OWNER_STEERING","STEERING853_IDENTITY_MISMATCH")
    req(e,s.get("program")==CURRENT_PROGRAM and s.get("product")==CURRENT_PRODUCT and s.get("compute_architecture")==CURRENT_COMPUTE_ARCHITECTURE,"STEERING853_PROGRAM_MISMATCH")
    sp=s.get("sandbox_pass_directive") or {}; req(e,sp.get("vps_self_hosted_production_fallback_for_test_credit")=="FORBIDDEN" and sp.get("false_pass")=="FORBIDDEN","STEERING853_SANDBOX_FENCE_MISSING")
    t=s.get("together_policy") or {}
    req(e,t.get("general_inference_fallback")=="FORBIDDEN" and t.get("recurring_training")=="FORBIDDEN","STEERING853_TOGETHER_GENERAL_FENCE_MISSING")
    req(e,t.get("one_shot_approx_08b_jspace_gwt_finetune")=="OWNER_AUTHORIZED_UNTIL_ONE_JOB_IS_CREATED" and t.get("one_shot_consumed") is False,"STEERING853_ONE_SHOT_TRAINING_STATE_MISMATCH")
    req(e,t.get("second_job")=="REQUIRES_NEW_EXPLICIT_OWNER_AUTHORIZATION" and t.get("training_contract")==TRAINING_AUTHORITY,"STEERING853_SECOND_JOB_GATE_MISSING")
    impl=s.get("current_implementation_delta") or {}; req(e,impl.get("runtime_credit")==0 and impl.get("training_job_started") is False,"STEERING853_PREMATURE_RUNTIME_OR_TRAINING_CREDIT")

    req(e,m.get("artifact")==CURRENT_PRODUCT and m.get("product_endpoint")==CURRENT_PRODUCT,"MANIFEST_PRODUCT_MISMATCH")
    req(e,m.get("integrated_cognition_compute_architecture")==CURRENT_COMPUTE_ARCHITECTURE and m.get("stage")==CURRENT_STAGE,"MANIFEST_ARCHITECTURE_OR_STAGE_MISMATCH")
    req(e,m.get("authority_correction")==CURRENT_AUTHORITY,"MANIFEST_AUTHORITY_POINTER_MISMATCH")
    req(e,m.get("effect_authority")=="EffectGate+EffectJournal","MANIFEST_EFFECT_AUTHORITY_MISMATCH")
    mx=m.get("execution_policy") or {}
    req(e,mx.get("free_only_default") is True and mx.get("isolated_sandbox_only") is True and mx.get("vps_testing_forbidden") is True,"MANIFEST_EXECUTION_FENCE_MISSING")
    req(e,mx.get("together_general_inference_and_fallback_forbidden") is True,"MANIFEST_TOGETHER_GENERAL_FALLBACK_FENCE_MISSING")
    req(e,mx.get("together_one_shot_08b_jspace_gwt_finetune_authorized") is True and mx.get("together_one_shot_08b_jspace_gwt_finetune_consumed") is False,"MANIFEST_ONE_SHOT_TRAINING_STATE_MISMATCH")
    req(e,mx.get("together_training_authority")==TRAINING_AUTHORITY and mx.get("second_paid_training_requires_owner_authorization") is True and mx.get("other_paid_fallback") is False,"MANIFEST_PAID_TRAINING_SCOPE_WEAKENED")
    mrc=m.get("runtime_credit") or {}; req(e,mrc.get("entityos_hcu_whole_runtime_credit")==0 and mrc.get("whole_product_pass") is False,"MANIFEST_RUNTIME_CREDIT_PREMATURE")

    req(e,c41.get("schema_version")=="4.1" and c41.get("mode")=="FREE_ONLY","CONTROL41_MISMATCH")
    req(e,(c41.get("cycle_policy") or {}).get("paid_fallback") is False and (c41.get("cycle_policy") or {}).get("vps_testing")=="FORBIDDEN","CONTROL41_SAFETY_WEAKENED")
    req(e,c42.get("base_control_path")==CONTROL41 and c42.get("base_control_blob_sha")==blob(p["c41"]),"CONTROL42_BASE_BLOB_MISMATCH")
    req(e,(c42.get("preserved_hard_rules") or {}).get("together_forbidden") is True,"CONTROL42_TOGETHER_FENCE_WEAKENED")
    req(e,c43.get("base_control_blob_sha")==blob(p["c41"]) and c43.get("execution_boundary_addendum_blob_sha")==blob(p["c42"]),"CONTROL43_ANCESTRY_MISMATCH")
    req(e,c44.get("prior_program_authority_addendum_blob_sha")==blob(p["c43"]),"CONTROL44_PRIOR_BLOB_MISMATCH")
    ov=c44.get("program_identity_override") or {}; req(e,ov.get("active_program")=="CLAYVERSE_SINGLE_CONTAINER" and ov.get("product_endpoint")=="ClayVerse","CONTROL44_HISTORICAL_PRODUCT_ANCESTRY_MISMATCH")
    req(e,(c44.get("preserved_hard_rules") or {}).get("runtime_credit_requires_exact_admitted_isolated_execution") is True,"CONTROL44_RUNTIME_EVIDENCE_FENCE_MISSING")

    footer=p["footer"].read_text().upper(); arch=p["architecture"].read_text().upper(); readme=p["readme"].read_text().upper(); claude=p["claude"].read_text().upper(); workers=p["workers"].read_text().upper(); training=p["training"].read_text().upper()
    req(e,"PROGRAM: ENTITYOS + HCU" in footer and "GENERAL_INFERENCE_AND_FALLBACK_FORBIDDEN" in footer,"FOOTER_CURRENT_AUTHORITY_SCOPE_MISSING")
    req(e,"ENTITYOS" in arch[:2500] and "HCU" in arch[:2500] and "CLAYVERSE IS THE PRODUCT ENDPOINT" not in arch[:2500],"ARCHITECTURE_CURRENT_PRODUCT_MISMATCH")
    req(e,"SUPERVISOR_STEERING_8_53.JSON" in readme[:3500] and "ONE-SHOT" in readme[:12000],"README_CURRENT_AUTHORITY_OR_TRAINING_SCOPE_MISSING")
    req(e,"SUPERVISOR_STEERING_8_53.JSON" in claude[:5000],"ROOT_CLAUDE_CURRENT_AUTHORITY_MISSING")
    req(e,"GENERAL TOGETHER INFERENCE/FALLBACK IS FORBIDDEN" in claude[:10000] and "ONE OWNER-AUTHORIZED ~0.8B J-SPACE/GWT FINE-TUNE" in claude[:10000],"ROOT_CLAUDE_TRAINING_SCOPE_MISSING")
    req(e,"TOGETHER REMAINS FORBIDDEN FOR ORDINARY INFERENCE/FALLBACK" in workers and ("SUPERVISOR_STEERING_8_53.JSON" in workers or "NEWEST EXPLICIT OWNER CORRECTION" in workers),"WORKER_CURRENT_AUTHORITY_SCOPE_MISSING")
    req(e,"TOGETHER" in training and "0.8B" in training and "ONE" in training,"TRAINING_DIRECTIVE_SCOPE_MISSING")

    return {"schema":CURRENT_SCHEMA,"pass":not e,"errors":e,"checked":{n:x.relative_to(root).as_posix() for n,x in p.items()}}


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",default="."); r=validate(Path(ap.parse_args().repo_root).resolve()); print(json.dumps(r,sort_keys=True)); return 0 if r["pass"] else 2
if __name__=="__main__": raise SystemExit(main())
