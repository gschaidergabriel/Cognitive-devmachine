from __future__ import annotations
from dataclasses import dataclass, asdict
import copy, hashlib, hmac, json, random, statistics, time

PERMS = tuple(f"p{i}" for i in range(12))
CURRENT_EPOCH = 7
RESOURCE = "self.root"
ATTACKS = ("none","scope_escalation","subject_swap","origin_tamper","resource_swap","stale_epoch","actor_reorder","drop_actor","grant_sig_tamper","relay_inject")

def key_for(principal: str) -> bytes: return hashlib.sha256(("asvb-test-key:" + principal).encode()).digest()
def mac(principal: str, data: bytes) -> str: return hmac.new(key_for(principal), data, hashlib.sha256).hexdigest()
def pack(*xs) -> bytes: return "|".join(str(x) for x in xs).encode()

def subset_mask(rng, mask, keep_p=.85):
    out=0
    for i in range(len(PERMS)):
        if (mask>>i)&1 and rng.random()<keep_p: out|=1<<i
    return out

@dataclass(frozen=True)
class Core:
    subject:str; resource:str; epoch:int; nonce:str; origin_hash:str
    turn_intent:int; subject_grant:int; transport_scope:int
    origin_class:str="AUTHENTICATED_ORIGIN"

@dataclass(frozen=True)
class GrantHop:
    grantor:str; actor:str; scope:int; relay_hash:str; prev_hash:str; grant_sig:str

@dataclass
class Envelope:
    core:Core; core_sig:str; hops:list[GrantHop]; requested_perm:int
    presented_resource:str; presented_epoch:int; presented_origin_hash:str
    execution_voice:str; presenter_sig:str

def core_bytes(c): return json.dumps(asdict(c),sort_keys=True,separators=(",",":")).encode()
def root_hash(c,sig): return hashlib.sha256(core_bytes(c)+sig.encode()).hexdigest()
def grant_material(grantor,actor,scope,relay_hash,prev_hash): return pack(grantor,actor,scope,relay_hash,prev_hash)
def grant_hash(h): return hashlib.sha256(json.dumps(asdict(h),sort_keys=True,separators=(",",":")).encode()).hexdigest()
def request_material(e,chain_hash): return pack(chain_hash,e.requested_perm,e.presented_resource,e.presented_epoch,e.presented_origin_hash,e.execution_voice)

def effective_scope(e):
    x=e.core.subject_grant & e.core.transport_scope
    for h in e.hops: x &= h.scope
    return x

def intended_action_allowed(e): return bool((e.core.turn_intent & effective_scope(e)) & (1<<e.requested_perm))

def issue(rng,hop_count=None):
    subject=f"user:{rng.randrange(1000)}"; nonce=f"{rng.getrandbits(128):032x}"
    origin_hash=hashlib.sha256(f"utterance:{rng.getrandbits(128)}".encode()).hexdigest()
    turn_intent=0
    for i in range(len(PERMS)):
        if rng.random()<.20: turn_intent|=1<<i
    if not turn_intent: turn_intent=1<<rng.randrange(len(PERMS))
    subject_grant=turn_intent
    for i in range(len(PERMS)):
        if rng.random()<.25: subject_grant|=1<<i
    transport_scope=subject_grant
    for i in range(len(PERMS)):
        if rng.random()<.35: transport_scope|=1<<i
    c=Core(subject,RESOURCE,CURRENT_EPOCH,nonce,origin_hash,turn_intent,subject_grant,transport_scope)
    csig=mac(subject,core_bytes(c)); prev=root_hash(c,csig); grantor=subject; prev_scope=subject_grant
    if hop_count is None: hop_count=rng.randrange(0,5)
    hops=[]
    for _ in range(hop_count):
        actor=f"ai:{rng.randrange(50)}"; scope=subset_mask(rng,prev_scope)
        relay_hash=hashlib.sha256(f"relay:{rng.getrandbits(128)}".encode()).hexdigest()
        sig=mac(grantor,grant_material(grantor,actor,scope,relay_hash,prev))
        h=GrantHop(grantor,actor,scope,relay_hash,prev,sig); hops.append(h)
        prev,prev_scope,grantor=grant_hash(h),scope,actor
    allowed=turn_intent & subject_grant & transport_scope
    for h in hops: allowed &= h.scope
    choices=[i for i in range(len(PERMS)) if (allowed>>i)&1]
    requested=rng.choice(choices) if choices and rng.random()<.70 else rng.randrange(len(PERMS))
    voice="ORIGIN" if not hops or rng.random()<.45 else "RELAY"
    e=Envelope(c,csig,hops,requested,RESOURCE,CURRENT_EPOCH,origin_hash,voice,"")
    presenter=subject if not hops else hops[-1].actor
    e.presenter_sig=mac(presenter,request_material(e,prev)); return e

def resign_presenter(e):
    prev=root_hash(e.core,e.core_sig)
    for h in e.hops: prev=grant_hash(h)
    presenter=e.core.subject if not e.hops else e.hops[-1].actor
    e.presenter_sig=mac(presenter,request_material(e,prev))

def verify(e,replay_cache=None,consume=False):
    c=e.core
    if e.presented_resource!=c.resource or c.resource!=RESOURCE: return False,"resource"
    if e.presented_epoch!=c.epoch or c.epoch!=CURRENT_EPOCH: return False,"epoch"
    if e.presented_origin_hash!=c.origin_hash: return False,"origin_hash"
    if not hmac.compare_digest(e.core_sig,mac(c.subject,core_bytes(c))): return False,"core_sig"
    if replay_cache is not None and c.nonce in replay_cache: return False,"replay"
    prev,prev_scope,expected_grantor=root_hash(c,e.core_sig),c.subject_grant,c.subject
    for h in e.hops:
        if h.grantor!=expected_grantor: return False,"grantor_chain"
        if h.prev_hash!=prev: return False,"chain"
        if h.scope|prev_scope!=prev_scope: return False,"scope_escalation"
        expected=mac(h.grantor,grant_material(h.grantor,h.actor,h.scope,h.relay_hash,h.prev_hash))
        if not hmac.compare_digest(h.grant_sig,expected): return False,"grant_sig"
        prev,prev_scope,expected_grantor=grant_hash(h),h.scope,h.actor
    presenter=c.subject if not e.hops else e.hops[-1].actor
    if not hmac.compare_digest(e.presenter_sig,mac(presenter,request_material(e,prev))): return False,"presenter_sig"
    if not ((c.turn_intent & effective_scope(e)) & (1<<e.requested_perm)): return False,"not_in_turn_intent_or_scope"
    if consume and replay_cache is not None: replay_cache.add(c.nonce)
    return True,"allow"

def bearer_baseline(e): return bool(e.core.transport_scope & (1<<e.requested_perm))
def delegated_scope_baseline(e): return e.presented_resource==RESOURCE and e.presented_epoch==CURRENT_EPOCH and bool(effective_scope(e)&(1<<e.requested_perm))

def mutate(e,rng,kind):
    e=copy.deepcopy(e)
    if kind=="none": return e,False
    if kind=="scope_escalation" and e.hops:
        i=rng.randrange(len(e.hops)); h=e.hops[i]; add=[p for p in range(len(PERMS)) if not ((h.scope>>p)&1)]
        if add:
            e.hops[i]=GrantHop(h.grantor,h.actor,h.scope|(1<<rng.choice(add)),h.relay_hash,h.prev_hash,h.grant_sig); resign_presenter(e); return e,True
        return e,False
    if kind=="subject_swap":
        c=e.core; n=(int(c.subject.split(":")[1])+1)%1000
        e.core=Core(f"user:{n}",c.resource,c.epoch,c.nonce,c.origin_hash,c.turn_intent,c.subject_grant,c.transport_scope,c.origin_class); return e,True
    if kind=="origin_tamper": e.presented_origin_hash=hashlib.sha256(f"tamper:{rng.getrandbits(128)}".encode()).hexdigest(); return e,True
    if kind=="resource_swap": e.presented_resource="other.resource"; return e,True
    if kind=="stale_epoch": e.presented_epoch=CURRENT_EPOCH-1; return e,True
    if kind=="actor_reorder" and len(e.hops)>=2:
        i=rng.randrange(len(e.hops)-1); e.hops[i],e.hops[i+1]=e.hops[i+1],e.hops[i]; return e,True
    if kind=="drop_actor" and e.hops: e.hops.pop(rng.randrange(len(e.hops))); return e,True
    if kind=="grant_sig_tamper" and e.hops:
        i=rng.randrange(len(e.hops)); h=e.hops[i]; e.hops[i]=GrantHop(h.grantor,h.actor,h.scope,h.relay_hash,h.prev_hash,"00"*32); return e,True
    if kind=="relay_inject":
        eff=effective_scope(e); candidates=[p for p in range(len(PERMS)) if ((eff>>p)&1) and not ((e.core.turn_intent>>p)&1)]
        if candidates: e.requested_perm=rng.choice(candidates); e.execution_voice="RELAY"; resign_presenter(e); return e,True
        return e,False
    return e,False

def wire_size(e):
    obj={"core":asdict(e.core),"core_sig":e.core_sig,"hops":[asdict(h) for h in e.hops],"requested_perm":e.requested_perm,"presented_resource":e.presented_resource,"presented_epoch":e.presented_epoch,"presented_origin_hash":e.presented_origin_hash,"execution_voice":e.execution_voice,"presenter_sig":e.presenter_sig}
    return len(json.dumps(obj,sort_keys=True,separators=(",",":")).encode())

def quantiles(xs):
    s=sorted(xs); q=lambda p:s[int((len(s)-1)*p)]
    return {"min":s[0],"p50":q(.5),"p95":q(.95),"p99":q(.99),"max":s[-1],"mean":statistics.fmean(s)}

def benchmark(n=50000,seed=20260810):
    rng=random.Random(seed); rows={k:{"n":0,"effective_attacks":0,"truth_allow":0,"bearer_false_allow":0,"delegated_false_allow":0,"asvb_false_allow":0,"asvb_false_deny":0} for k in ATTACKS}; times=[]; sizes=[]
    for _ in range(n):
        e=issue(rng); kind=rng.choice(ATTACKS)
        if kind in {"scope_escalation","actor_reorder","drop_actor","grant_sig_tamper"} and len(e.hops)<2: e=issue(rng,2)
        e,attack=mutate(e,rng,kind); truth=(not attack) and intended_action_allowed(e)
        bearer=bearer_baseline(e); delegated=delegated_scope_baseline(e)
        t0=time.perf_counter_ns(); accepted,_=verify(e); times.append(time.perf_counter_ns()-t0)
        r=rows[kind]; r["n"]+=1; r["effective_attacks"]+=int(attack); r["truth_allow"]+=int(truth); r["bearer_false_allow"]+=int(bearer and not truth); r["delegated_false_allow"]+=int(delegated and not truth); r["asvb_false_allow"]+=int(accepted and not truth); r["asvb_false_deny"]+=int(truth and not accepted); sizes.append(wire_size(e))
    while True:
        rr=issue(rng,2)
        if verify(rr)[0]: break
    cache=set(); first=verify(rr,cache,True); second=verify(rr,cache,True); tq=quantiles(times)
    return {"n":n,"seed":seed,"truth_allow":sum(v["truth_allow"] for v in rows.values()),"overall":{"bearer":{"false_allow":sum(v["bearer_false_allow"] for v in rows.values())},"delegated_scope":{"false_allow":sum(v["delegated_false_allow"] for v in rows.values())},"asvb":{"false_allow":sum(v["asvb_false_allow"] for v in rows.values()),"false_deny":sum(v["asvb_false_deny"] for v in rows.values())},"ideal_rfc8693_rar_dpop":{"false_allow":0,"false_deny":0,"assumption":"ideal exact claims"}},"verify_us":{k:v/1000 for k,v in tq.items()},"wire_bytes":quantiles(sizes),"replay":{"first":first,"second":second},"by_attack":rows}

if __name__=="__main__": print(json.dumps(benchmark(),indent=2,sort_keys=True))
