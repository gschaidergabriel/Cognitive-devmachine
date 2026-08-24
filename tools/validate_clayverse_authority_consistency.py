#!/usr/bin/env python3
"""Successor-aware fail-closed authority guard for current EntityOS + HCU.

The compatibility filename remains because workflows and historical receipts address it.
Current authority is resolved from current-facing pointers, never a hard-coded supervisor
minor. Historical 4.x controls remain donor/safety ancestry, not current routing law.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

CURRENT_PROGRAM="ENTITYOS_HCU"
CURRENT_STAGE="ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
CURRENT_PRODUCT="EntityOS"
CURRENT_COMPUTE_ARCHITECTURE="HCU"
CURRENT_SCHEMA="ENTITYOS_HCU_AUTHORITY_CONSISTENCY/v6"
AUTHORITY_RE=re.compile(r"^research_entity/claycode/autonomous/SUPERVISOR_STEERING_(\d+)_(\d+)\.json$")
ROOT_CLAUDE="CLAUDE.md"
PROVIDER_ADMISSION="research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
PROVIDER_SCHEMA="ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1"
ECONOMIC_PROVENANCE="governance/FREE_LANE_ECONOMIC_PROVENANCE_2026-08-24.json"
ECONOMIC_SCHEMA="ENTITYOS_HCU_FREE_LANE_ECONOMIC_PROVENANCE/v1"
FREE_LANE_RECEIPT="FREE_LANE_EXECUTION_RECEIPT/v1"
NVIDIA_ENTITLEMENT_RECEIPT="NVIDIA_CREDENTIAL_FREE_ENTITLEMENT_RECEIPT/v1"
CONTROL41="research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
CONTROL42="research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json"
CONTROL43="research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_3_PROGRAM_AUTHORITY.json"
CONTROL44="research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
LEGACY_EXPECTED_CONTROL="4.1+4.2-execution-boundary-addendum+4.3-program-authority-addendum+4.4-clayverse-product-authority-addendum"


def load_json(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def git_blob_sha(path:Path)->str:
    data=path.read_bytes(); return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()


def require(errors:list[str], condition:bool, code:str)->None:
    if not condition: errors.append(code)


def _safe_authority_path(value:object)->str|None:
    if not isinstance(value,str) or not AUTHORITY_RE.fullmatch(value): return None
    p=PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts:return None
    return value


def _authority_version(path:str)->str:
    m=AUTHORITY_RE.fullmatch(path); assert m
    return f"{int(m.group(1))}.{int(m.group(2)):02d}"


def _version_tuple(version:str)->tuple[int,int]:
    major,minor=version.split(".",1)
    return int(major),int(minor)


def _quarantined(value:object)->bool:
    return isinstance(value,str) and "QUARANTINED" in value.upper()


def _zero_credit(errors:list[str], obj:dict[str,Any], prefix:str)->None:
    fields=(
        "free_swarm_provider_admission_runtime_credit","external_provider_worker_runtime_credit",
        "entityos_hcu_whole_runtime_credit","hcu_full_runtime_credit","jspace_model_runtime_credit","training_credit"
    )
    for field in fields:
        if field in obj: require(errors,obj.get(field)==0,f"{prefix}_{field.upper()}_NONZERO")
    if "whole_product_pass" in obj: require(errors,obj.get("whole_product_pass") is False,f"{prefix}_WHOLE_PASS_PREMATURE")


def _validate_legacy_safety_ancestry(errors:list[str],root:Path)->None:
    paths=[root/CONTROL41,root/CONTROL42,root/CONTROL43,root/CONTROL44]
    if any(not p.is_file() for p in paths):
        for p in paths: require(errors,p.is_file(),f"MISSING_LEGACY:{p.name}")
        return
    try:c41,c42,c43,c44=(load_json(p) for p in paths)
    except Exception: errors.append("LEGACY_JSON_LOAD_ERROR"); return
    require(errors,c41.get("schema_version")=="4.1","CONTROL41_VERSION_MISMATCH")
    require(errors,c41.get("status")=="ACTIVE" and c41.get("mode")=="FREE_ONLY","CONTROL41_FREE_ONLY_WEAKENED")
    cyc=c41.get("cycle_policy") or {}
    require(errors,cyc.get("paid_fallback") is False,"CONTROL41_PAID_FALLBACK_WEAKENED")
    require(errors,cyc.get("automatic_subscription_upgrade") is False,"CONTROL41_AUTO_UPGRADE_WEAKENED")
    rules=set(c41.get("authority_rules") or [])
    require(errors,"model_output_is_candidate_not_truth" in rules,"CONTROL41_MODEL_TRUTH_FENCE_MISSING")
    require(errors,"autonomous_cycle_may_not_modify_FRANK_harness" in rules,"CONTROL41_FRANK_HARNESS_FENCE_MISSING")
    b41,b42,b43=(git_blob_sha(paths[0]),git_blob_sha(paths[1]),git_blob_sha(paths[2]))
    require(errors,c42.get("base_control_path")==CONTROL41,"CONTROL42_BASE_PATH_MISMATCH")
    require(errors,c42.get("base_control_blob_sha")==b41,"CONTROL42_BASE_BLOB_MISMATCH")
    h42=c42.get("preserved_hard_rules") or {}
    require(errors,h42.get("free_only") is True and h42.get("paid_fallback") is False,"CONTROL42_FREE_ONLY_WEAKENED")
    require(errors,h42.get("together_forbidden") is True,"CONTROL42_TOGETHER_FENCE_WEAKENED")
    require(errors,c43.get("base_control_blob_sha")==b41,"CONTROL43_BASE_BLOB_MISMATCH")
    require(errors,c43.get("execution_boundary_addendum_path")==CONTROL42,"CONTROL43_EXEC_PATH_MISMATCH")
    require(errors,c43.get("execution_boundary_addendum_blob_sha")==b42,"CONTROL43_EXEC_BLOB_MISMATCH")
    h43=c43.get("preserved_hard_rules") or {}
    require(errors,h43.get("free_only") is True and h43.get("paid_fallback") is False,"CONTROL43_FREE_ONLY_WEAKENED")
    require(errors,h43.get("together_forbidden_under_current_control") is True,"CONTROL43_TOGETHER_FENCE_WEAKENED")
    require(errors,c44.get("prior_program_authority_addendum_path")==CONTROL43,"CONTROL44_PRIOR_PATH_MISMATCH")
    require(errors,c44.get("prior_program_authority_addendum_blob_sha")==b43,"CONTROL44_PRIOR_BLOB_MISMATCH")
    require(errors,c44.get("effective_control_version")==LEGACY_EXPECTED_CONTROL,"CONTROL44_EFFECTIVE_VERSION_MISMATCH")
    h44=c44.get("preserved_hard_rules") or {}
    require(errors,h44.get("free_only") is True and h44.get("paid_fallback") is False,"CONTROL44_FREE_ONLY_WEAKENED")
    require(errors,h44.get("together_forbidden") is True,"CONTROL44_TOGETHER_FENCE_WEAKENED")


def validate(root:Path)->dict[str,Any]:
    errors:list[str]=[]
    paths={
        "canonical":root/"research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap":root/"research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program":root/"research_entity/rooms/PROGRAM_STATE.json",
        "inbox":root/"research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
        "manifest":root/"the artefact/manifest.json",
        "provider_admission":root/PROVIDER_ADMISSION,
        "economic_provenance":root/ECONOMIC_PROVENANCE,
        "architecture":root/"the artefact/ARCHITECTURE.md",
        "readme":root/"the artefact/README.md",
        "repo_claude":root/ROOT_CLAUDE,
    }
    for name,p in paths.items():require(errors,p.is_file(),f"MISSING:{name}")
    if errors:return {"schema":CURRENT_SCHEMA,"pass":False,"errors":errors}
    try:
        canonical=load_json(paths["canonical"]); bootstrap=load_json(paths["bootstrap"]); program=load_json(paths["program"])
        inbox=load_json(paths["inbox"]); manifest=load_json(paths["manifest"]); admission=load_json(paths["provider_admission"])
        economic=load_json(paths["economic_provenance"])
    except Exception as exc:return {"schema":CURRENT_SCHEMA,"pass":False,"errors":[f"JSON_LOAD_ERROR:{type(exc).__name__}"]}

    require(errors,bootstrap.get("entity_id")==canonical.get("entity_id"),"BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    ident=bootstrap.get("identity") or {}
    require(errors,ident.get("persistent_research_entity")=="Clay","BOOTSTRAP_PERSISTENT_ENTITY_MISMATCH")
    require(errors,bootstrap.get("active_program")==CURRENT_PROGRAM,"BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors,bootstrap.get("active_stage")==CURRENT_STAGE,"BOOTSTRAP_STAGE_MISMATCH")
    require(errors,bootstrap.get("product_endpoint")==CURRENT_PRODUCT,"BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    require(errors,bootstrap.get("integrated_cognition_compute_architecture")==CURRENT_COMPUTE_ARCHITECTURE,"BOOTSTRAP_COMPUTE_ARCHITECTURE_MISMATCH")
    require(errors,bootstrap.get("free_only") is True,"BOOTSTRAP_FREE_ONLY_MISMATCH")
    require(errors,"FORBIDDEN" in str(bootstrap.get("paid_fallback","")),"BOOTSTRAP_PAID_FALLBACK_FENCE_MISSING")
    require(errors,"FORBIDDEN" in str(bootstrap.get("together_api","")),"BOOTSTRAP_TOGETHER_FENCE_MISSING")
    require(errors,bootstrap.get("effect_authority")=="EffectGate+EffectJournal","BOOTSTRAP_EFFECT_AUTHORITY_MISMATCH")

    require(errors,program.get("program_id")=="entityos-hcu" and program.get("status")=="ACTIVE","PROGRAM_ID_OR_STATUS_MISMATCH")
    require(errors,program.get("stage")==CURRENT_STAGE and program.get("current_stage")==CURRENT_STAGE,"PROGRAM_STAGE_MISMATCH")
    require(errors,program.get("product")==CURRENT_PRODUCT,"PROGRAM_PRODUCT_MISMATCH")
    require(errors,program.get("integrated_cognition_compute_architecture")==CURRENT_COMPUTE_ARCHITECTURE,"PROGRAM_COMPUTE_ARCHITECTURE_MISMATCH")
    pa=program.get("authority") or {}; require(errors,pa.get("external_effects")=="EffectGate+EffectJournal","PROGRAM_EFFECT_AUTHORITY_MISMATCH")
    pe=program.get("execution_policy") or {}
    require(errors,pe.get("free_only") is True,"PROGRAM_FREE_ONLY_EXECUTION_MISMATCH")
    require(errors,pe.get("authorized_zero_cost_local_normal_user_execution") is True,"PROGRAM_LOCAL_ZERO_COST_AUTHORITY_MISSING")
    require(errors,pe.get("authorized_clay_direct_dev_vps_sandbox_execution") is True,"PROGRAM_CLAY_DIRECT_DEV_AUTHORITY_MISSING")
    require(errors,pe.get("other_paid_fallback") is False,"PROGRAM_OTHER_PAID_FALLBACK_WEAKENED")
    require(errors,pe.get("current_provider_runtime_credit",0)==0,"PROGRAM_PROVIDER_CREDIT_NONZERO")
    _zero_credit(errors,program.get("runtime_credit") or {},"PROGRAM")

    require(errors,manifest.get("artifact")==CURRENT_PRODUCT and manifest.get("product_endpoint")==CURRENT_PRODUCT,"MANIFEST_PRODUCT_MISMATCH")
    require(errors,manifest.get("integrated_cognition_compute_architecture")==CURRENT_COMPUTE_ARCHITECTURE,"MANIFEST_ARCHITECTURE_MISMATCH")
    require(errors,manifest.get("effect_authority")=="EffectGate+EffectJournal","MANIFEST_EFFECT_AUTHORITY_MISMATCH")
    me=manifest.get("execution_policy") or {}
    require(errors,me.get("active_supervisor_free_only") is True,"MANIFEST_FREE_ONLY_MISMATCH")
    require(errors,me.get("other_paid_fallback") is False,"MANIFEST_PAID_FALLBACK_WEAKENED")
    _zero_credit(errors,manifest.get("runtime_credit") or {},"MANIFEST")

    raw={"bootstrap":bootstrap.get("authority_correction"),"program":program.get("authority_correction"),"manifest":manifest.get("authority_correction"),"inbox":inbox.get("steering")}
    pointers={k:_safe_authority_path(v) for k,v in raw.items()}
    for k,v in pointers.items():require(errors,v is not None,f"AUTHORITY_POINTER_INVALID:{k}")
    valid=[v for v in pointers.values() if v is not None]
    authority=valid[0] if valid else None
    require(errors,len(valid)==len(pointers) and len(set(valid))==1,"AUTHORITY_POINTER_SPLIT_BRAIN")

    owner={"bootstrap":bootstrap.get("active_owner_authority"),"program":program.get("active_owner_authority")}
    present=[v for v in owner.values() if isinstance(v,str) and v]
    require(errors,len(present)==2,"OWNER_AUTHORITY_POINTER_MISSING")
    if len(present)==2:require(errors,len(set(present))==1,"OWNER_AUTHORITY_POINTER_SPLIT_BRAIN")

    supervisor=None; expected=None
    if authority:
        expected=_authority_version(authority); sp=root/authority
        require(errors,sp.is_file(),"AUTHORITY_TARGET_MISSING")
        if sp.is_file():
            try:supervisor=load_json(sp)
            except Exception:errors.append("AUTHORITY_TARGET_JSON_LOAD_ERROR")
    if supervisor is not None and expected is not None:
        version=_version_tuple(expected)
        require(errors,str(supervisor.get("schema_version"))==expected,"AUTHORITY_FILENAME_SCHEMA_MISMATCH")
        require(errors,str(inbox.get("schema_version"))==expected,"SUPERVISOR_INBOX_SCHEMA_MISMATCH")
        require(errors,str(program.get("schema_version"))==expected,"PROGRAM_SCHEMA_NOT_SUPERVISOR_SUCCESSOR")
        require(errors,str(me.get("active_supervisor_epoch"))==expected,"MANIFEST_SUPERVISOR_EPOCH_MISMATCH")
        require(errors,supervisor.get("active_program",supervisor.get("program"))==CURRENT_PROGRAM,"SUPERVISOR_PROGRAM_MISMATCH")
        require(errors,supervisor.get("product")==CURRENT_PRODUCT,"SUPERVISOR_PRODUCT_MISMATCH")
        require(errors,supervisor.get("integrated_cognition_compute_architecture",supervisor.get("compute_architecture"))==CURRENT_COMPUTE_ARCHITECTURE,"SUPERVISOR_ARCHITECTURE_MISMATCH")
        free=supervisor.get("free_only") or supervisor.get("free_only_policy") or {}
        require(errors,supervisor.get("mode")=="FREE_ONLY" or free.get("enabled") is True,"SUPERVISOR_MODE_NOT_FREE_ONLY")
        require(errors,free.get("no_paid_fallback") is True,"SUPERVISOR_PAID_FALLBACK_WEAKENED")
        require(errors,free.get("together_forbidden") is True or free.get("together_general_inference")=="FORBIDDEN","SUPERVISOR_TOGETHER_FENCE_MISSING")
        promo=supervisor.get("promotion_state") or supervisor.get("promotion") or {}
        require(errors,promo.get("entityos_whole_runtime_pass") is False,"SUPERVISOR_WHOLE_PASS_PREMATURE")
        require(errors,promo.get("hcu_full_runtime_pass") is False,"SUPERVISOR_HCU_PASS_PREMATURE")
        require(errors,promo.get("provider_runtime_credit",0)==0,"SUPERVISOR_PROVIDER_CREDIT_NONZERO")
        require(errors,promo.get("training_credit",0)==0,"SUPERVISOR_TRAINING_CREDIT_NONZERO")

        require(errors,admission.get("schema")==PROVIDER_SCHEMA,"PROVIDER_ADMISSION_SCHEMA_MISMATCH")
        require(errors,str(admission.get("authority_epoch"))==expected,"PROVIDER_ADMISSION_EPOCH_MISMATCH")
        require(errors,admission.get("mode")=="FREE_ONLY","PROVIDER_ADMISSION_MODE_MISMATCH")
        require(errors,admission.get("product")==CURRENT_PRODUCT and admission.get("compute_architecture")==CURRENT_COMPUTE_ARCHITECTURE,"PROVIDER_ADMISSION_PRODUCT_MISMATCH")
        providers=admission.get("providers") or {}
        allow=set(str(x) for x in bootstrap.get("free_provider_allowlist_current") or [])
        require(errors,bool(allow),"BOOTSTRAP_FREE_PROVIDER_ALLOWLIST_EMPTY")
        require(errors,allow.issubset(set(providers)),"PROVIDER_ADMISSION_ALLOWLIST_INCOMPLETE")
        for name in sorted(allow):
            rec=providers.get(name) or {}
            if rec.get("admitted") is True:require(errors,rec.get("cost_class")=="FREE",f"PROVIDER_ADMISSION_NONFREE_SELF_ADMIT:{name}")
        require(errors,admission.get("runtime_provider_credit")==0,"PROVIDER_ADMISSION_RUNTIME_CREDIT_NONZERO")

        if version>=(8,70):
            route_gate=admission.get("route_level_gate") or {}
            require(errors,route_gate.get("receipt_schema")==FREE_LANE_RECEIPT,"PROVIDER_ADMISSION_FREE_LANE_RECEIPT_SCHEMA_MISSING")
            require(errors,route_gate.get("unknown_or_unbound_route")=="FAIL_CLOSED","PROVIDER_ADMISSION_UNBOUND_ROUTE_FENCE_MISSING")
            require(errors,route_gate.get("paid_fallback_attempt_count")==0,"PROVIDER_ADMISSION_PAID_FALLBACK_ATTEMPT_NONZERO")
            require(errors,me.get("provider_level_free_is_runtime_cost_proof") is False,"MANIFEST_PROVIDER_LEVEL_FREE_COST_PROOF_WEAKENED")
            require(errors,pe.get("provider_level_free_is_runtime_cost_proof") is False,"PROGRAM_PROVIDER_LEVEL_FREE_COST_PROOF_WEAKENED")

        if version==(8,70):
            require(errors,free.get("execution_state")=="FREE_CONTINGENTS_AUTHORIZED_PENDING_PER_LANE_COST_PROVENANCE","SUPERVISOR_FREE_LANE_EXECUTION_STATE_MISMATCH")
            receipt=(supervisor.get("new_required_receipts") or {}).get(FREE_LANE_RECEIPT) or {}
            require(errors,isinstance(receipt,dict) and bool(receipt.get("must_bind")),"SUPERVISOR_FREE_LANE_RECEIPT_CONTRACT_MISSING")
            require(errors,FREE_LANE_RECEIPT.replace("/v1","_V1") in str(admission.get("execution_state","")),"PROVIDER_ADMISSION_FREE_LANE_EXECUTION_STATE_MISMATCH")
        elif version>=(8,71):
            require(errors,free.get("nvidia_provider_global_statement_is_not_credential_entitlement_proof") is True,"SUPERVISOR_NVIDIA_PROVIDER_GLOBAL_PROOF_FENCE_MISSING")
            required=supervisor.get("new_required_receipts") or {}
            nvidia_receipt=required.get(NVIDIA_ENTITLEMENT_RECEIPT) or {}
            require(errors,isinstance(nvidia_receipt,dict) and bool(nvidia_receipt.get("must_bind")),"SUPERVISOR_NVIDIA_ENTITLEMENT_RECEIPT_MISSING")
            require(errors,economic.get("schema")==ECONOMIC_SCHEMA,"ECONOMIC_PROVENANCE_SCHEMA_MISMATCH")
            require(errors,str(economic.get("authority_epoch"))==expected,"ECONOMIC_PROVENANCE_EPOCH_MISMATCH")
            nvidia=(economic.get("providers") or {}).get("nvidia") or {}
            fingerprints=nvidia.get("admitted_credential_fingerprints") or []
            require(errors,isinstance(fingerprints,list) and len(fingerprints)>0,"NVIDIA_ADMITTED_CREDENTIAL_FINGERPRINT_MISSING")
            require(errors,nvidia.get("credential_plan_needed") is True,"NVIDIA_CREDENTIAL_PLAN_BINDING_NOT_REQUIRED")
            require(errors,nvidia.get("default")=="FAIL_CLOSED_FOR_UNLISTED_CREDENTIAL","NVIDIA_UNLISTED_CREDENTIAL_NOT_FAIL_CLOSED")
            require(errors,me.get("provider_global_free_statement_is_concrete_credential_entitlement_proof") is False,"MANIFEST_NVIDIA_GLOBAL_PROOF_WEAKENED")
            require(errors,pe.get("provider_global_free_statement_is_concrete_credential_entitlement_proof") is False,"PROGRAM_NVIDIA_GLOBAL_PROOF_WEAKENED")
        else:
            require(errors,_quarantined(free.get("external_llm_provider_execution")),"SUPERVISOR_PROVIDER_QUARANTINE_MISSING")
            require(errors,_quarantined(admission.get("execution_state")),"PROVIDER_ADMISSION_EXECUTION_QUARANTINE_MISSING")

    root_text=paths["repo_claude"].read_text(encoding="utf-8")
    upper=root_text.upper()
    require(errors,"AUTONOMOUS_SUPERVISOR=RESOLVE_FROM_SUPERVISOR_INBOX" in upper,"ROOT_CLAUDE_DYNAMIC_SUPERVISOR_ROUTING_MISSING")
    require(errors,"SUPERVISOR_INBOX.JSON" in upper,"ROOT_CLAUDE_INBOX_MISSING")
    require(errors,re.search(r"AUTONOMOUS_SUPERVISOR\s*=\s*SUPERVISOR_STEERING_\d+_\d+",root_text) is None,"ROOT_CLAUDE_FIXED_SUPERVISOR_PIN_FORBIDDEN")
    arch=paths["architecture"].read_text(encoding="utf-8").upper(); readme=paths["readme"].read_text(encoding="utf-8").upper()
    require(errors,"ENTITYOS" in arch[:3000] and "HCU" in arch[:3000],"ARCHITECTURE_ENTITYOS_HCU_MISSING")
    require(errors,"CLAYVERSE IS THE PRODUCT ENDPOINT" not in arch[:3000],"ARCHITECTURE_STALE_CLAYVERSE_PRODUCT_AUTHORITY")
    require(errors,"ENTITYOS" in readme[:3000] and "HCU" in readme[:3000],"README_ENTITYOS_HCU_MISSING")
    _validate_legacy_safety_ancestry(errors,root)
    return {"schema":CURRENT_SCHEMA,"pass":not errors,"errors":errors,"resolved_authority":authority,"resolved_authority_schema":supervisor.get("schema_version") if supervisor else None,"provider_admission_epoch":admission.get("authority_epoch"),"economic_provenance_epoch":economic.get("authority_epoch")}


def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--repo-root",default=".");a=p.parse_args()
    result=validate(Path(a.repo_root).resolve());print(json.dumps(result,sort_keys=True));return 0 if result["pass"] else 2


if __name__=="__main__":raise SystemExit(main())
