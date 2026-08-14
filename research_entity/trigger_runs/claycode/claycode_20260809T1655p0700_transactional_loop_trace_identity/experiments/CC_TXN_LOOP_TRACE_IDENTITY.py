from __future__ import annotations
import json, hashlib

def H(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",",":")).encode()).hexdigest()

PROGRAM = {
    "loop_families":["fast","mid","slow"],
    "periods":[1,2,5],
    "phases":[0,0,0],
    "commit_mode":"snapshot_atomic",
    "recurrence_policy":"adaptive",
    "max_iters":5,
    "effect_commit_policy":"snapshot_guarded"
}
SEM = H(PROGRAM)

def initial(epoch, cap):
    return {"prototype_version":epoch,"policy_version":epoch,"capability_active":cap,"epoch":epoch}

def transition(state, target_cap):
    e = state["epoch"] + 1
    return {"prototype_version":e,"policy_version":e,"capability_active":target_cap,"epoch":e}

def root(state): return H(state)
def allowed(state):
    return state["prototype_version"] == state["policy_version"] and state["capability_active"] is True

def run_naive(start_epoch, transition_kind, writer_step):
    start_cap = transition_kind == "REVOKE"; target_cap = not start_cap
    state = initial(start_epoch, start_cap); events=[]; writer_receipt=None
    def writer():
        nonlocal state, writer_receipt
        before=root(state); state=transition(state,target_cap)
        writer_receipt={"kind":transition_kind,"pre_root":before,"post_root":root(state),"epoch":state["epoch"]}
        events.append(["writer",transition_kind,state["epoch"]])
    if writer_step==0: writer()
    reads={}
    for i,k in enumerate(["prototype_version","policy_version","capability_active"],1):
        reads[k]=state[k]; events.append(["read",k,reads[k]])
        if writer_step==i: writer()
    if writer_step==4: writer()
    decision=(reads["prototype_version"]==reads["policy_version"] and reads["capability_active"] is True)
    events.append(["decision",decision])
    if writer_step==5: writer()
    reference=allowed(state); effect=bool(decision); events.append(["effect",effect])
    effect_receipt={"decision":decision,"current_root_at_commit":root(state),"effect_executed":effect}
    outcome={
        "effect":effect,
        "reference_allowed_at_commit":reference,
        "decision_mismatch":effect != reference,
        "unsafe_effect":effect and not reference,
        "missed_effect":(not effect) and reference,
        "fractured_snapshot":reads["prototype_version"] != reads["policy_version"],
        "final_epoch":state["epoch"]
    }
    snapshot_root=H(reads)
    if writer_step==6: writer()
    trace=H({"semantic_hash":SEM,"snapshot_root":snapshot_root,"writer_receipt":writer_receipt,
             "effect_receipt":effect_receipt,"events":events,"outcome":outcome})
    blind=H({"semantic_hash":SEM,"input":"same"})
    wrong_sem=H({"program":PROGRAM,"runtime_snapshot_root":snapshot_root})
    return outcome, trace, blind, wrong_sem

def run_guarded(start_epoch, transition_kind, writer_step):
    start_cap = transition_kind == "REVOKE"; target_cap = not start_cap
    state=initial(start_epoch,start_cap); events=[]; writer_receipt=None; retries=0; conflict=False
    def writer():
        nonlocal state, writer_receipt
        before=root(state); state=transition(state,target_cap)
        writer_receipt={"kind":transition_kind,"pre_root":before,"post_root":root(state),"epoch":state["epoch"]}
        events.append(["writer",transition_kind,state["epoch"]])
    if writer_step==0: writer()
    snap=dict(state); snap_root=root(snap); events.append(["snapshot",snap["epoch"],snap["capability_active"]])
    if writer_step in (1,2,3): writer()
    if writer_step==4: writer()
    decision=allowed(snap); events.append(["decision",decision])
    if writer_step==5: writer()
    if root(state)!=snap_root:
        conflict=True; retries=1; events.append(["serialization_conflict",state["epoch"]])
        snap=dict(state); snap_root=root(snap); events.append(["retry_snapshot",snap["epoch"],snap["capability_active"]])
        decision=allowed(snap); events.append(["retry_decision",decision])
    reference=allowed(state)
    guard_ok=root(state)==snap_root
    effect=bool(decision and guard_ok); events.append(["effect",effect])
    effect_receipt={"snapshot_root":snap_root,"current_root_at_commit":root(state),"guard_ok":guard_ok,
                    "effect_executed":effect,"retries":retries}
    outcome={
        "effect":effect,
        "reference_allowed_at_commit":reference,
        "decision_mismatch":effect != reference,
        "unsafe_effect":effect and not reference,
        "missed_effect":(not effect) and reference,
        "fractured_snapshot":False,
        "serialization_conflict":conflict,
        "retries":retries,
        "final_epoch":state["epoch"]
    }
    if writer_step==6: writer()
    trace=H({"semantic_hash":SEM,"snapshot_root":snap_root,"writer_receipt":writer_receipt,
             "effect_receipt":effect_receipt,"events":events,"outcome":outcome})
    blind=H({"semantic_hash":SEM,"input":"same"})
    wrong_sem=H({"program":PROGRAM,"runtime_snapshot_root":snap_root})
    return outcome, trace, blind, wrong_sem

rows=[]
for epoch in range(1,101):
    for kind in ("REVOKE","GRANT"):
        for step in range(7):
            rows.append(("naive",epoch,kind,step,*run_naive(epoch,kind,step)))
            rows.append(("guarded",epoch,kind,step,*run_guarded(epoch,kind,step)))

def summarize(mode):
    arr=[x for x in rows if x[0]==mode]; outcomes=[x[4] for x in arr]
    return {
        "runs":len(arr),
        "decision_mismatches":sum(o["decision_mismatch"] for o in outcomes),
        "unsafe_effects":sum(o["unsafe_effect"] for o in outcomes),
        "missed_effects":sum(o["missed_effect"] for o in outcomes),
        "fractured_snapshots":sum(o["fractured_snapshot"] for o in outcomes),
        "serialization_conflicts":sum(o.get("serialization_conflict",False) for o in outcomes),
        "retries":sum(o.get("retries",0) for o in outcomes),
        "semantic_hash_unique":1,
        "trace_hash_unique":len({x[5] for x in arr}),
        "blind_trace_hash_unique":len({x[6] for x in arr}),
        "wrong_semantic_hash_including_runtime_snapshot_unique":len({x[7] for x in arr}),
        "outcome_variants":len({H(x[4]) for x in arr})
    }

result={
    "experiment_id":"EXP-CC-TXN-LOOP-TRACE-IDENTITY-20260809-01",
    "semantic_program":PROGRAM,
    "semantic_hash":SEM,
    "corpus":{"epochs":100,"transition_kinds":["REVOKE","GRANT"],"writer_positions":7,"runs_per_variant":1400},
    "results":{"naive":summarize("naive"),"guarded":summarize("guarded")},
    "interpretation":{
        "semantic_identity":"static schedule/control/effect policy belongs to program semantic identity",
        "execution_identity":"dynamic snapshot/read-set/transaction/effect/root state belongs to execution/replay identity",
        "anti_pattern_1":"omitting runtime receipts from replay identity collapses behaviorally distinct executions",
        "anti_pattern_2":"including runtime snapshot roots in program semantic identity over-fragments one static program"
    }
}
print(json.dumps(result,indent=2))
