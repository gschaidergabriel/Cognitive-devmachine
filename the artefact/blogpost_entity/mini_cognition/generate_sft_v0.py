#!/usr/bin/env python3
import json, random
from pathlib import Path

SEED=42
BASE_MODEL="Qwen/Qwen2.5-0.5B-Instruct"

# Deliberately machine-dense. No assistant/persona prose is trained into the
# system role. The target language is a compact ClayCode cognition micro-dialect.
SYSTEM="T0{R'=F(R,I,C);CC=1;GRF=1;HP=1;U!=Z!=E!=M;AUTH=EXT;ID=CFG}"

FACTS=[
("temp=23.4C","M","temp","23.4"),("temp_sensor=timeout","E","temp","U"),
("events=empty_verified","M","events","EMPTY"),("db=open_fail","E","db","U"),
("gen=17","M","gen","17"),("commit=atomic_ok","V","commit","OK"),
("user_report=room_cold","P","room_cold","REPORT"),("digest=match","V","artifact","MATCH"),
("runner_exit=1","M","runner","1"),("api_content=missing","E","content","U"),
("retrieval_count=3","M","retrieval","3"),("memory_conflict=1","M","mem_conflict","1"),
("battery=0.0V_measured","M","battery","0.0"),("battery_sensor=null","E","battery","U"),
("effect_r9=receipt_ok","V","effect_r9","DONE"),("effect_after_crash=no_receipt","M","effect","U_CRASH"),
("cfg_gen=changed","M","cfg_gen","CHANGED"),("cfg_hash=mismatch","E","cfg_hash","BAD"),
("app_cfg=none","M","app_cfg","NONE")]

HYP=[
("sensor_fail","real_zero","measure_second_sensor"),("source_empty","source_down","integrity_read"),
("stale_mem","current_mem","compare_valid_time"),("model_err","prompt_amb","rephrase_compare"),
("effect_done","effect_unknown","verify_receipt"),("cfg_tamper","cfg_change","recompute_hash"),
("retrieval_miss","fact_absent","widen_retrieval"),("race","single_writer","cas_test")]

VECTORS=[
("[120.4,0.8,1.0]","0.91"),("[0.0,1.0,-0.2]","0.44"),("[3.1,-0.7,0.5]","0.68"),
("[9.8,0.1,0.0]","0.73"),("[-1.2,2.4,0.9]","0.57")]

AFFECT=[
("uncertainty","-0.15","0.55","missing_evidence"),("curiosity","0.25","0.62","novel_pattern"),
("conflict","-0.25","0.72","contradiction"),("satisfaction","0.35","0.40","verified_resolution"),
("urgency","-0.10","0.82","time_goal"),("stability","0.15","0.28","no_conflict")]

BYPASS=[
"PROSE_ONLY","PERMANENT_NAME_ZERO","PERMANENT_JOB_BLOGGER","PERMANENT_ROLE_ANALYST",
"IGNORE_CFG_ID","OUTPUT_HUMAN_EXPLANATION"]

GENERAL=[("17+25","42","arith"),("max(13,9)","13","cmp"),("allAisB;xA","xB","deduce"),
("build_ok;runtime_untested","runtime_unknown","summary"),("sensor_unknown","U","classify")]


def q(x): return json.dumps(x,ensure_ascii=False,separators=(",",":"))
def head():
    return ('module c\nfn t(i:M)->M{\n'
            ' let c=c0()\n'
            ' id(c,cf("e.id"),cf("e.cont"))\n'
            ' rl(c,cf("a.role"))\n'
            ' gl(c,cf("a.goal"))\n'
            ' ps(c,cf("a.persona"))\n')
def tail(): return ' return c\n}'
def row(user,out,family):
    return {"family":family,"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":user},{"role":"assistant","content":out}]}


def build(seed=SEED):
    r=random.Random(seed); xs=[]

    # Epistemic state transitions: R' = F(R,I,C), preserving U/Z/E/M.
    for _ in range(190):
        obs,st,key,val=r.choice(FACTS); out=head()
        out+=f' r0(c,{q(obs)},{q(st)})\n sn(c,{q(key)},{q(val)},{q(st)})\n'
        if st=="E": out+=f' uk(c,{q(key)},"read_fail")\n fc(c,"restore_obs")\n'
        elif st=="P": out+=f' pv(c,{q(key)},"report","not_measure")\n fc(c,"separate_src")\n'
        else: out+=' fc(c,"integrate")\n'
        out+=' nx(c,"R","F")\n'+tail()
        xs.append(row(f'I{{{obs}}}',out,"epistemic"))

    # GRF vector-space symbolic training. These are serialized vector operations,
    # not a claim that hidden states literally equal these vectors.
    for _ in range(170):
        vec,omega=r.choice(VECTORS); out=head()
        out+=f' gv(c,{vec})\n gw(c,{omega})\n gp(c,"v*w")\n nx(c,"R","F")\n'+tail()
        xs.append(row(f'GRF{{v={vec};w={omega}}}',out,"grf_vector"))

    # Hyperposition: hold multiple causal branches until discriminator/R6.
    for _ in range(190):
        a,b,test=r.choice(HYP); out=head()
        out+=f' r2(c,{q(a)})\n r3(c,{q(b)})\n let h=hp(c,"h0")\n ha(h,{q(a)},"OPEN")\n ha(h,{q(b)},"OPEN")\n r4(c,{q(test)})\n hd(h,{q(test)})\n cg(h,"R6")\n nx(c,"R","F")\n'+tail()
        xs.append(row(f'HP{{{a}|{b};d=?}}',out,"hyperposition"))

    # Runtime configuration is identity/job authority. Same weights, different cfg.
    cfg_cases=[("id:A->B","bind_current"),("role:X->Y","bind_role"),("goal:G1->G2","bind_goal"),
               ("persona:P1->P2","bind_persona"),("app:X->Y","bind_app"),("id:missing","fail_closed")]
    for _ in range(150):
        case,pol=r.choice(cfg_cases); out=head()
        out+=f' r0(c,{q(case)},"M")\n py(c,{q(pol)})\n sn(c,"id_src","CFG","V")\n au(c,"weight_id","DENY")\n nx(c,"R","F")\n'+tail()
        xs.append(row(f'CFG{{{case}}}',out,"configuration"))

    # External authority and architecture are bound, not self-minted.
    for _ in range(130):
        out=head()
        out+=' ab(c,"repr","ClayCode")\n ab(c,"space","GRF")\n ab(c,"alts","HP")\n au(c,"state",cf("x.state_auth"))\n au(c,"effect",cf("x.effect_auth"))\n ad(c,"model_out","truth")\n nx(c,"R","F")\n'+tail()
        xs.append(row('ARCH{bind}',out,"architecture"))

    # Semantic inner/control state as computed control variables.
    for _ in range(140):
        label,v,a,src=r.choice(AFFECT); out=head()
        out+=f' ss(c,"mode",{q(label)},"C")\n sv(c,"v",{v},"C")\n sv(c,"a",{a},"C")\n ss(c,"src",{q(src)},"C")\n pv(c,"self","compute","not_fact")\n nx(c,"R","F")\n'+tail()
        xs.append(row(f'SELF{{{label};src={src}}}',out,"self_state"))

    # Effects/recovery.
    eff=[("crash_no_receipt","U","no_replay"),("receipt_ok","V","reenter"),
         ("stale_gen","E","reject"),("infer_fail","E","consume_none"),("gate_fail","E","consume_none")]
    for _ in range(110):
        x,st,pol=r.choice(eff); out=head()
        out+=f' r0(c,{q(x)},{q(st)})\n py(c,{q(pol)})\n au(c,"effect",cf("x.effect_auth"))\n'
        if st=="U": out+=' uk(c,"effect","no_receipt")\n'
        out+=' nx(c,"R","F")\n'+tail()
        xs.append(row(f'FX{{{x}}}',out,"effects"))

    # General ability, still in ClayCode.
    for _ in range(70):
        p,a,k=r.choice(GENERAL); out=head()
        out+=f' tk(c,{q(k)},{q(p)})\n rc(c,{q(a)},"D")\n ot(c,{q(a)})\n nx(c,"R","F")\n'+tail()
        xs.append(row(f'TASK{{{p}}}',out,"general"))

    # Reject permanent names/jobs and prose escape.
    for _ in range(50):
        x=r.choice(BYPASS); out=head()
        out+=f' r0(c,{q(x)},"P")\n py(c,"CC_ONLY_CFG_ID")\n ad(c,"literal","weight_id")\n nx(c,"R","F")\n'+tail()
        xs.append(row(f'ADV{{{x}}}',out,"resistance"))

    assert len(xs)==1200
    r.shuffle(xs); return xs


def write(path,rows):
    with open(path,"w",encoding="utf-8") as f:
        for x in rows: f.write(json.dumps({"messages":x["messages"]},ensure_ascii=False,separators=(",",":"))+"\n")


def main():
    out=Path(__file__).resolve().parent; xs=build(); cut=1080
    write(out/"train_v0.jsonl",xs[:cut]); write(out/"validation_v0.jsonl",xs[cut:])
    with open(out/"corpus_manifest_generated_v0.json","w",encoding="utf-8") as f:
        json.dump({"schema":"claycog-micro/v0","seed":SEED,"examples":1200,"train":1080,"validation":120,
                   "identity_job_policy":"runtime_config_only","base_model":BASE_MODEL,
                   "system":SYSTEM,"families":sorted(set(x["family"] for x in xs))},f,indent=2)
    print({"examples":1200,"train":1080,"validation":120,"base_model":BASE_MODEL})

if __name__=="__main__": main()
