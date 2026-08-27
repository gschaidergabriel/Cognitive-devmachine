from dataclasses import dataclass, field
from itertools import product
from collections import Counter
import json

OUTCOMES = ['SUCCESS_ACK','SUCCESS_TIMEOUT','FAIL_ACK','NO_EFFECT_TIMEOUT']
CRASH_POINTS = list(range(0,7))
IDEMP = [False, True]
RECON = ['RESOLVES_SUCCESS','RESOLVES_FAILURE','STAYS_UNKNOWN']
CANCEL_AFTER_CRASH = [False, True]

@dataclass
class R:
    arch:str; outcome:str; idempotent:bool; crash_point:int; reconciliation:str; cancel_after_crash:bool
    evidence_visible:bool=False; belief_visible:bool=False
    verified_success:bool=False; verified_failure:bool=False; unknown:bool=False
    reentered:bool=False; done:bool=False; cancelled:bool=False; effect_count:int=0
    sync_commits:int=0; writes:int=0; recoveries:int=0; violations:list=field(default_factory=list)

def provider_initial(outcome,r):
    if outcome=='SUCCESS_ACK': r.effect_count+=1; return 'VERIFIED_SUCCESS'
    if outcome=='SUCCESS_TIMEOUT': r.effect_count+=1; return 'UNKNOWN'
    if outcome=='FAIL_ACK': return 'VERIFIED_FAILURE'
    return 'UNKNOWN'

def resolve_unknown(r,reconciliation):
    if r.idempotent:
        if r.effect_count==0: r.effect_count=1
        return 'VERIFIED_SUCCESS'
    if reconciliation=='RESOLVES_SUCCESS':
        if r.effect_count==0: r.effect_count=1
        return 'VERIFIED_SUCCESS'
    if reconciliation=='RESOLVES_FAILURE': return 'VERIFIED_FAILURE'
    return 'UNKNOWN'

def maybe_crash(r, phase):
    if r.crash_point == phase:
        r.recoveries += 1
        if r.cancel_after_crash:
            r.cancelled = True
            return True
    return False

def invariants(r):
    if r.belief_visible and not r.verified_success:
        r.violations.append('OUTCOME_CONDITIONED_BELIEF_WITHOUT_VERIFIED_SUCCESS')
    if r.done and not r.reentered:
        r.violations.append('DONE_WITHOUT_REENTRY')
    if r.reentered and not (r.verified_success or r.verified_failure):
        r.violations.append('REENTRY_WITHOUT_VERIFIED_OUTCOME')
    if r.effect_count>1:
        r.violations.append('DUPLICATE_EFFECT')
    if r.unknown and r.done:
        r.violations.append('UNKNOWN_TREATED_AS_DONE')
    if r.cancelled and r.belief_visible and not r.verified_success:
        r.violations.append('CANCELLED_TX_LEFT_OUTCOME_BELIEF_VISIBLE')
    return r

def simulate(arch,outcome,idempotent,crash_point,reconciliation,cancel_after_crash):
    r=R(arch,outcome,idempotent,crash_point,reconciliation,cancel_after_crash)
    if arch=='LOOSE':
        r.evidence_visible=True; r.belief_visible=True; r.writes+=2; r.sync_commits+=2
    elif arch=='TASK_TX':
        r.writes+=1; r.sync_commits+=1
    else:
        r.evidence_visible=True; r.writes+=1
    if maybe_crash(r,1): return invariants(r)

    r.writes+=1; r.sync_commits+=1
    if maybe_crash(r,2): return invariants(r)

    state=provider_initial(outcome,r); r.writes+=1; r.sync_commits+=1
    if maybe_crash(r,3):
        if state=='UNKNOWN': r.unknown=True
        elif state=='VERIFIED_SUCCESS': r.verified_success=True
        elif state=='VERIFIED_FAILURE': r.verified_failure=True
        return invariants(r)

    if state=='UNKNOWN': state=resolve_unknown(r,reconciliation)
    if state=='VERIFIED_SUCCESS': r.verified_success=True
    elif state=='VERIFIED_FAILURE': r.verified_failure=True
    else: r.unknown=True
    r.writes+=1; r.sync_commits+=1
    if maybe_crash(r,4): return invariants(r)

    if arch=='LOOSE':
        if r.verified_success or r.verified_failure:
            r.reentered=True; r.writes+=1; r.sync_commits+=1
    elif arch=='TASK_TX':
        if r.verified_success:
            r.evidence_visible=True; r.belief_visible=True; r.reentered=True; r.writes+=1; r.sync_commits+=1
        elif r.verified_failure:
            r.evidence_visible=True; r.reentered=True; r.writes+=1; r.sync_commits+=1
    else:
        if r.verified_success:
            r.belief_visible=True; r.reentered=True; r.writes+=1; r.sync_commits+=1
        elif r.verified_failure:
            r.reentered=True; r.writes+=1
    if maybe_crash(r,5): return invariants(r)

    if r.verified_success or r.verified_failure: r.done=r.reentered
    if arch in ('LOOSE','TASK_TX') and r.done:
        r.writes+=1; r.sync_commits+=1
    if maybe_crash(r,6): return invariants(r)
    return invariants(r)

results=[]
for args in product(['LOOSE','TASK_TX','ACEF'],OUTCOMES,IDEMP,CRASH_POINTS,RECON,CANCEL_AFTER_CRASH):
    results.append(simulate(*args))

summary={}
for arch in ['LOOSE','TASK_TX','ACEF']:
    rr=[x for x in results if x.arch==arch]
    v=Counter(v for x in rr for v in x.violations)
    cancelled=[x for x in rr if x.cancelled]
    summary[arch]={
      'scenarios':len(rr),
      'scenarios_with_any_violation':sum(bool(x.violations) for x in rr),
      'violation_counts':dict(v),
      'mean_sync_commits':round(sum(x.sync_commits for x in rr)/len(rr),3),
      'mean_writes':round(sum(x.writes for x in rr)/len(rr),3),
      'unknown_suspended':sum(x.unknown and not x.done for x in rr),
      'cancelled_scenarios':len(cancelled),
      'cancelled_with_evidence_retained':sum(x.evidence_visible for x in cancelled),
      'cancelled_with_belief_visible':sum(x.belief_visible for x in cancelled),
    }
print(json.dumps(summary,indent=2))
