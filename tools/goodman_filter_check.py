#!/usr/bin/env python3
"""Validate FRANK↔ClayCode Goodman anti-echo review and mesh binding.

Registry/mesh membership changes over time. The run validator therefore derives the
scientific branch set from INTERCONNECT_MANIFEST instead of hard-coding a branch count.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

ALLOWED={"SUPPORTED","REFINED","REFUTED","UNRESOLVED"}
REVIEW_NAME="FRANK_CLAYCODE_GOODMAN_REVIEW.json"
INTERCONNECT_NAME="INTERCONNECT_MANIFEST.json"

def _load(path:Path)->dict[str,Any]:
    try: obj=json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e: raise ValueError(f"missing required file: {path.name}") from e
    except json.JSONDecodeError as e: raise ValueError(f"invalid JSON in {path.name}: {e}") from e
    if not isinstance(obj,dict): raise ValueError(f"{path.name} must be a JSON object")
    return obj

def template(run_id:str)->dict[str,Any]:
    return {"schema_version":"1.1","protocol":"research_entity/global/GOODMAN_ANTI_ECHO_PROTOCOL.md","claycode_run_id":run_id,"latest_frank_run":None,"latest_frank_architecture_artifact":None,"shared_ancestry_is_not_replication":True,"reviews":[{"claim_id":"REPLACE_ME","frank_statement":"REPLACE_ME","frank_source_refs":[],"ancestry_families":[],"shared_ancestry_collapsed":True,"counterhypothesis":"REPLACE_ME","falsifier":"REPLACE_ME","independent_checks":[],"adversarial_checks":[],"verdict":"UNRESOLVED","reason":"REPLACE_ME","claycode_action":"keep_open","affected_claycode_artifacts":[]}]}

def _nonempty(x:Any)->bool: return isinstance(x,str) and bool(x.strip()) and x!="REPLACE_ME"

def validate(path:Path)->dict[str,Any]:
    d=_load(path); v=[]
    if d.get("shared_ancestry_is_not_replication") is not True:v.append("shared_ancestry_is_not_replication must be true")
    if not d.get("claycode_run_id"):v.append("claycode_run_id required")
    if not d.get("latest_frank_run"):v.append("latest_frank_run required")
    rs=d.get("reviews")
    if not isinstance(rs,list) or not rs:v.append("reviews must be a non-empty list")
    else:
        ids=[]
        for i,r in enumerate(rs):
            if not isinstance(r,dict):v.append(f"reviews[{i}] must be object");continue
            cid=r.get("claim_id")
            if not _nonempty(cid):v.append(f"reviews[{i}].claim_id required")
            else:ids.append(cid)
            if not _nonempty(r.get("frank_statement")):v.append(f"reviews[{i}].frank_statement required")
            if not isinstance(r.get("frank_source_refs"),list) or not r.get("frank_source_refs"):v.append(f"reviews[{i}].frank_source_refs must be non-empty list")
            if not isinstance(r.get("ancestry_families"),list) or not r.get("ancestry_families"):v.append(f"reviews[{i}].ancestry_families must be non-empty list")
            if r.get("shared_ancestry_collapsed") is not True:v.append(f"reviews[{i}].shared_ancestry_collapsed must be true")
            if not _nonempty(r.get("counterhypothesis")):v.append(f"reviews[{i}].counterhypothesis required")
            if not _nonempty(r.get("falsifier")):v.append(f"reviews[{i}].falsifier required")
            if not isinstance(r.get("independent_checks"),list):v.append(f"reviews[{i}].independent_checks must be list")
            if not isinstance(r.get("adversarial_checks"),list) or not r.get("adversarial_checks"):v.append(f"reviews[{i}].adversarial_checks must be non-empty list")
            verdict=r.get("verdict")
            if verdict not in ALLOWED:v.append(f"reviews[{i}].verdict invalid")
            if verdict in {"SUPPORTED","REFINED"} and not r.get("independent_checks"):v.append(f"reviews[{i}] {verdict} requires independent_checks")
            if verdict=="REFUTED" and str(r.get("claycode_action","")).lower() not in {"reject","supersede","negative_result","remove"}:v.append(f"reviews[{i}] REFUTED must reject/supersede/preserve negative result")
            if verdict=="UNRESOLVED" and str(r.get("claycode_action","")).lower() in {"integrate_as_true","promote","canonicalize"}:v.append(f"reviews[{i}] UNRESOLVED cannot be promoted as truth")
            if not _nonempty(r.get("reason")):v.append(f"reviews[{i}].reason required")
            if not _nonempty(r.get("claycode_action")):v.append(f"reviews[{i}].claycode_action required")
            if not isinstance(r.get("affected_claycode_artifacts"),list):v.append(f"reviews[{i}].affected_claycode_artifacts must be list")
        if len(ids)!=len(set(ids)):v.append("claim_id values must be unique")
    return {"ok":not v,"review_file":str(path),"violations":v}

def validate_run(run_dir:Path)->dict[str,Any]:
    inter=_load(run_dir/INTERCONNECT_NAME); review=_load(run_dir/REVIEW_NAME); base=validate(run_dir/REVIEW_NAME);v=list(base["violations"])
    if inter.get("trigger")!="claycode":v.append("INTERCONNECT_MANIFEST.trigger must be claycode")
    registered=list(inter.get("registry_scientific_branches") or [])
    branch_names=[x.get("branch") for x in inter.get("branches",[]) if isinstance(x,dict)]
    if not registered:v.append("registry_scientific_branches must be non-empty")
    if set(branch_names)!=set(registered):v.append("preflight branches must cover exactly registry_scientific_branches")
    priority=inter.get("branch_priority") or []
    required_prefix=[x for x in ["frank","clay","claygraph","unifieddb"] if x in registered]
    if priority[:len(required_prefix)]!=required_prefix:v.append(f"ClayCode preflight priority must begin {required_prefix}")
    if set(priority)!=set(registered):v.append("branch_priority must cover exactly registered scientific branches")
    special=inter.get("special_rules") or inter.get("requirements") or {}
    def truthy(*keys):return any(special.get(k) is True for k in keys)
    if not truthy("claycode_requires_latest_frank_research_as_primary_feedback","latest_frank_primary_feedback"):v.append("preflight must require latest FRANK research as primary feedback")
    if not truthy("claycode_requires_deep_claygraph_input","deep_claygraph"):v.append("preflight must require deep ClayGraph input")
    if "unifieddb" in registered and not truthy("claycode_requires_deep_unifieddb_input","deep_unifieddb"):v.append("preflight must require deep UnifiedDB input")
    if not truthy("claycode_requires_goodman_anti_echo_review","goodman_required"):v.append("preflight must require Goodman anti-echo review")
    frank=next((x for x in inter.get("branches",[]) if x.get("branch")=="frank"),None)
    if not frank:v.append("preflight must contain FRANK branch material")
    else:
        latest=frank.get("latest_run") or frank.get("latest_completed_run")
        if not latest:v.append("preflight must contain latest FRANK run")
        elif review.get("latest_frank_run")!=latest:v.append("review.latest_frank_run must match FRANK latest run captured by preflight")
    if review.get("claycode_run_id")!=inter.get("run_id"):v.append("review.claycode_run_id must match INTERCONNECT_MANIFEST.run_id")
    expected=(inter.get("special_rules") or {}).get("claycode_latest_frank_architecture_artifact")
    if expected is not None and review.get("latest_frank_architecture_artifact")!=expected:v.append("review latest_frank_architecture_artifact must match preflight")
    return {"ok":not v,"run_dir":str(run_dir),"registered_branch_count":len(registered),"violations":v}

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    t=sub.add_parser("template");t.add_argument("--run-id",required=True);t.add_argument("--output")
    q=sub.add_parser("validate");q.add_argument("path")
    r=sub.add_parser("validate-run");r.add_argument("run_dir")
    a=ap.parse_args()
    if a.cmd=="template":
        text=json.dumps(template(a.run_id),ensure_ascii=False,indent=2)+"\n"
        if a.output:Path(a.output).write_text(text,encoding="utf-8")
        print(text,end="");return
    out=validate_run(Path(a.run_dir)) if a.cmd=="validate-run" else validate(Path(a.path));print(json.dumps(out,ensure_ascii=False,indent=2));raise SystemExit(0 if out["ok"] else 2)
if __name__=="__main__":main()
