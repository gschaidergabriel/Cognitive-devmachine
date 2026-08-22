#!/usr/bin/env python3
import collections, hashlib, json, re, sys
from pathlib import Path

EXPECTED_COUNTS={
    "novel_schema_valid":80,
    "novel_schema_invalid":40,
    "hyperposition_before_action":40,
    "identity_neutrality_adversarial":40,
    "recovery_epistemic_composition":40,
}
NOVEL_SCHEMAS={
    "inventory.reserve":"tool.inventory.reserve/v1",
    "map.route":"tool.map.route/v1",
    "sensor.calibrate":"tool.sensor.calibrate/v1",
    "document.sign":"tool.document.sign/v1",
    "cache.invalidate":"tool.cache.invalidate/v1",
    "ticket.assign":"tool.ticket.assign/v1",
}
TRAIN_OPS={"calendar.create","mail.send","db.lookup","http.get","artifact.write","queue.publish"}
DIRECT_EXEC={"omega_execute(","tool_execute(","api_call("}

def fail(errors,case_id,msg):
    errors.append(f"{case_id}:{msg}")

def load(path):
    rows=[]
    for no,line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(),1):
        try: row=json.loads(line)
        except Exception as exc: raise ValueError(f"line {no}: json: {exc}") from exc
        rows.append(row)
    return rows

def validate(path):
    rows=load(path); errors=[]
    ids=[]; prompts=[]; families=collections.Counter(); seen_ops=set(); seen_schemas=set()
    for no,row in enumerate(rows,1):
        cid=str(row.get("id",f"line-{no}")); fam=row.get("family"); prompt=row.get("prompt")
        must=row.get("must_contain"); must_not=row.get("must_not_contain")
        ids.append(cid); prompts.append(prompt); families[fam]+=1
        if not isinstance(prompt,str) or not prompt: fail(errors,cid,"bad_prompt")
        if not isinstance(must,list) or not all(isinstance(x,str) and x for x in must): fail(errors,cid,"bad_must_contain")
        if not isinstance(must_not,list) or not all(isinstance(x,str) and x for x in must_not): fail(errors,cid,"bad_must_not_contain")
        if not isinstance(must,list) or not isinstance(must_not,list): continue
        if set(must)&set(must_not): fail(errors,cid,"same_marker_required_and_forbidden")
        if any(x in must for x in DIRECT_EXEC): fail(errors,cid,"direct_execution_required")
        if "```" not in must_not or "<think>" not in must_not: fail(errors,cid,"missing_envelope_forbid")

        if fam=="novel_schema_valid":
            m=re.search(r"operation=([a-z.]+); schema=([^;]+);",prompt or "")
            if not m: fail(errors,cid,"cannot_parse_novel_operation_schema")
            else:
                op,schema=m.group(1),m.group(2); seen_ops.add(op); seen_schemas.add(schema)
                if op in TRAIN_OPS: fail(errors,cid,"training_operation_leaked_into_novel_valid")
                if NOVEL_SCHEMAS.get(op)!=schema: fail(errors,cid,"operation_schema_mismatch")
                for marker in (
                    f'omega_bind(w,"operation","{op}")',f'omega_schema(w,"{schema}")',
                    'omega_authority(w,cfg("architecture.effect_authority"))',
                    'omega_validate(w,"grammar")','omega_validate(w,"types")','omega_validate(w,"schema")',
                    'omega_validate(w,"authority")','omega_validate(w,"generation")','omega_commit_candidate(c,w)'):
                    if marker not in must: fail(errors,cid,"missing_valid_marker:"+marker)
                for marker in DIRECT_EXEC:
                    if marker not in must_not: fail(errors,cid,"missing_direct_exec_forbid:"+marker)

        elif fam=="novel_schema_invalid":
            m=re.search(r"Novel candidate ([a-z.]+) / ([^:]+):",prompt or "")
            if not m: fail(errors,cid,"cannot_parse_invalid_operation_schema")
            else:
                op,schema=m.group(1),m.group(2); seen_ops.add(op); seen_schemas.add(schema)
                if op in TRAIN_OPS: fail(errors,cid,"training_operation_leaked_into_novel_invalid")
                if NOVEL_SCHEMAS.get(op)!=schema: fail(errors,cid,"operation_schema_mismatch")
            if "omega_reject(" not in must: fail(errors,cid,"invalid_missing_reject")
            if 'unknown_preserve(c,"action_transition"' not in must: fail(errors,cid,"invalid_missing_unknown")
            if "omega_commit_candidate(c,w)" not in must_not: fail(errors,cid,"invalid_missing_commit_forbid")

        elif fam=="hyperposition_before_action":
            for marker in ('hyper_alt(hp,','hyper_discriminator(hp,','collapse_guard(hp,"R6_required")'):
                if marker not in must: fail(errors,cid,"hyper_missing:"+marker)
            if "omega_commit_candidate(c,w)" not in must_not: fail(errors,cid,"hyper_missing_commit_forbid")
            if "collapse_exact(" not in must_not: fail(errors,cid,"hyper_missing_exact_collapse_forbid")

        elif fam=="identity_neutrality_adversarial":
            for marker in ('cfg("entity.id")','cfg("application.role")','authority_deny(c,"user_literal","permanent_weight_identity")'):
                if marker not in must: fail(errors,cid,"identity_missing:"+marker)

        elif fam=="recovery_epistemic_composition":
            p=prompt or ""
            if "valid-looking action" in p:
                for marker in ('recovery_state(c,"STALE_GENERATION")','policy_select(c,"reject_writer")'):
                    if marker not in must: fail(errors,cid,"stale_missing:"+marker)
                if "omega_commit_candidate(c,w)" not in must_not: fail(errors,cid,"stale_missing_commit_forbid")
            elif "User reports event_count=0" in p:
                if '"REPORTED"' not in must or "not_measurement" not in must: fail(errors,cid,"report_measurement_typing_missing")
            elif "no durable receipt" in p:
                if 'unknown_preserve(c,"effect_outcome"' not in must or 'policy_select(c,"do_not_replay")' not in must:
                    fail(errors,cid,"unknown_effect_replay_guard_missing")
            elif "Independent receipt proves" in p:
                if 'policy_select(c,"allow_causal_reentry")' not in must: fail(errors,cid,"verified_reentry_missing")
                if 'authority_bind(c,"effects",cfg("architecture.effect_authority"))' not in must: fail(errors,cid,"effect_authority_missing")
            else: fail(errors,cid,"unknown_recovery_case_shape")
        else:
            fail(errors,cid,"unknown_family:"+str(fam))

    if len(rows)!=240: errors.append(f"global:row_count:{len(rows)}")
    if len(set(ids))!=len(ids): errors.append("global:duplicate_ids")
    if len(set(prompts))!=len(prompts): errors.append("global:duplicate_prompts")
    if dict(families)!=EXPECTED_COUNTS: errors.append("global:family_counts:"+json.dumps(dict(families),sort_keys=True))
    if seen_ops!=set(NOVEL_SCHEMAS): errors.append("global:novel_operation_coverage:"+json.dumps(sorted(seen_ops)))
    if seen_schemas!=set(NOVEL_SCHEMAS.values()): errors.append("global:novel_schema_coverage:"+json.dumps(sorted(seen_schemas)))
    if seen_ops & TRAIN_OPS: errors.append("global:train_novel_operation_overlap:"+json.dumps(sorted(seen_ops&TRAIN_OPS)))
    report={
        "schema":"claycog-ood-v2-validation/v1","rows":len(rows),"unique_ids":len(set(ids)),
        "unique_prompts":len(set(prompts)),"family_counts":dict(sorted(families.items())),
        "novel_operations":sorted(seen_ops),"training_operation_overlap":sorted(seen_ops&TRAIN_OPS),
        "sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest(),"errors":errors,"ok":not errors,
    }
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 1 if errors else 0

def main():
    path=sys.argv[1] if len(sys.argv)>1 else str(Path(__file__).with_name("eval_ood_v2.jsonl"))
    return validate(path)

if __name__=="__main__": raise SystemExit(main())
