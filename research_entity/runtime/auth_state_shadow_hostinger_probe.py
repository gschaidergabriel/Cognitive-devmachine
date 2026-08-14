from __future__ import annotations
import argparse,json,math,platform,random,sqlite3,statistics,sys,time
from pathlib import Path

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.harness.reference.state_auth_shadow import AuthenticatedStateShadowV1


def q(xs,p):
    ys=sorted(xs); k=(len(ys)-1)*p; a=math.floor(k); b=math.ceil(k)
    return ys[a] if a==b else ys[a]*(b-k)+ys[b]*(k-a)

def stat(xs):
    return {'n':len(xs),'p50_ms':q(xs,.5),'p95_ms':q(xs,.95),'p99_ms':q(xs,.99),'mean_ms':statistics.fmean(xs),'min_ms':min(xs),'max_ms':max(xs)}
def timed(fn):
    t=time.perf_counter_ns(); out=fn(); return out,(time.perf_counter_ns()-t)/1e6

def small_falsifiers():
    l=StateLedger(); l.append_event(event_id='seed',idem='seed',base_epoch=0,event_type='SEED',writer='probe',ops=[
        {'op':'SET','domain':'memory','key':'alpha','value':{'v':1,'u':'ä✓'},'epistemic':'KNOWN','status':'CURRENT'},
        {'op':'SET','domain':'memory','key':'beta','value':{'$kind':'set','items':[3,1,3,2]},'epistemic':'UNKNOWN','status':'CURRENT'},
        {'op':'SET','domain':'goal','key':'g1','value':{'priority':0.8},'epistemic':'KNOWN','status':'CURRENT'},
    ])
    s=AuthenticatedStateShadowV1(l); a=s.full_rebuild(now='t0')['root_hash']; assert s.verify_full().passed
    l.append_event(event_id='u',idem='u',base_epoch=l.epoch,event_type='UPDATE',writer='probe',ops=[{'op':'SET','domain':'memory','key':'alpha','value':{'v':2},'epistemic':'KNOWN','status':'CURRENT'}])
    out=s.refresh(now='t1'); assert out['mode']=='DELTA_REFRESH' and out['touched_refs']==1 and s.verify_full().passed
    b=s.receipt().root_hash; assert a!=b
    rebuilt=s.full_rebuild(now='t2')['root_hash']; assert b==rebuilt and s.verify_full().passed
    l.conn.execute('BEGIN IMMEDIATE'); l.conn.execute("UPDATE state SET value_json=? WHERE domain='memory' AND k='alpha'",('{"tampered":true}',)); assert not s.verify_full().passed; l.conn.rollback()
    assert s.verify_full().passed
    events=l.export_events(); r=StateLedger.replay(events); sr=AuthenticatedStateShadowV1(r); rr=sr.full_rebuild(now='replay')['root_hash']; assert rr==s.receipt().root_hash and sr.verify_full().passed
    r.close(); l.close(); return {'tests':7,'passed':7}

def benchmark(rows,updates):
    l=StateLedger(); ops=[]; epis=('KNOWN','UNKNOWN','CONFLICT')
    for i in range(rows):
        ops.append({'op':'SET','domain':f'd{i%20:02d}','key':f'k{i:06d}','value':{'i':i,'u':'äλ✓','nested':[True,None,{'$kind':'set','items':[3,1,3,2]}]},'epistemic':epis[i%3],'status':'SUPERSEDED' if i%11==0 else 'CURRENT'})
    _,seed_ms=timed(lambda:l.append_event(event_id='bench-seed',idem='bench-seed',base_epoch=0,event_type='BENCH_SEED',writer='probe',ops=ops))
    page_size=int(l.conn.execute('PRAGMA page_size').fetchone()[0]); before=int(l.conn.execute('PRAGMA page_count').fetchone()[0]); s=AuthenticatedStateShadowV1(l); _,rebuild_ms=timed(lambda:s.full_rebuild(now='bench-r0')); after=int(l.conn.execute('PRAGMA page_count').fetchone()[0]); v0,verify_ms=timed(s.verify_full); assert v0.passed
    rng=random.Random(20260810); commit=[]; refresh=[]
    for i in range(updates):
        idx=rng.randrange(rows); d=f'd{idx%20:02d}'; k=f'k{idx:06d}'
        _,dt=timed(lambda i=i,idx=idx,d=d,k=k:l.append_event(event_id=f'bu{i}',idem=f'bu{i}',base_epoch=l.epoch,event_type='BENCH_UPDATE',writer='probe',ops=[{'op':'SET','domain':d,'key':k,'value':{'i':idx,'update':i,'u':'✓'},'epistemic':'KNOWN','status':'CURRENT'}])); commit.append(dt)
        out,dt=timed(lambda i=i:s.refresh(now=f'bench-d{i}')); assert out['mode']=='DELTA_REFRESH' and out['touched_refs']==1; refresh.append(dt)
    root=s.receipt().root_hash; rebuilt,rebuild_after_ms=timed(lambda:s.full_rebuild(now='bench-r1')); assert rebuilt['root_hash']==root; v1,verify_after_ms=timed(s.verify_full); assert v1.passed
    full=[]
    for _ in range(8): _,dt=timed(l._roots); full.append(dt)
    l.conn.execute('BEGIN IMMEDIATE'); row=l.conn.execute('SELECT domain,k FROM state ORDER BY domain,k LIMIT 1').fetchone(); l.conn.execute('UPDATE state SET value_json=? WHERE domain=? AND k=?',('{"tampered":true}',row[0],row[1])); tamper=not s.verify_full().passed; l.conn.rollback(); assert tamper
    result={'rows':rows,'updates':updates,'seed_ms':seed_ms,'full_rebuild_ms':rebuild_ms,'full_verify_ms':verify_ms,'authoritative_commit':stat(commit),'shadow_delta_refresh':stat(refresh),'canonical_full_root_recompute':stat(full),'root_speedup_p50':q(full,.5)/q(refresh,.5),'page_size':page_size,'pages_before_shadow':before,'pages_after_shadow':after,'page_ratio':after/before,'rebuild_after_ms':rebuild_after_ms,'verify_after_ms':verify_after_ms,'rebuild_equivalent':True,'verify_after_pass':True,'tamper_detected':tamper}; l.close(); return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); ap.add_argument('--rows',type=int,default=20000); ap.add_argument('--updates',type=int,default=20); a=ap.parse_args(); tests=small_falsifiers(); bench=benchmark(a.rows,a.updates); payload={'schema_version':'1.0','experiment':'CLAY_AUTH_STATE_SHADOW_EXACT_REPO_HOSTINGER','truth_class':'VERIFIED_REMOTE_EXECUTION_EXACT_CLAY_CHECKOUT_IF_WORKFLOW_RECEIPT_PERSISTS','created_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'python':sys.version,'sqlite':sqlite3.sqlite_version,'platform':platform.platform(),'falsifiers':tests,'benchmark':bench,'pass':tests['passed']==tests['tests'] and bench['rebuild_equivalent'] and bench['verify_after_pass'] and bench['tamper_detected'],'authority':'CANDIDATE_SHADOW_ONLY_NO_CANONICAL_PROMOTION','limitations':['Hostinger VPS is not Andreas final target hardware.','Shadow root does not replace semantic_state_hash.','Fair cross-engine same-semantics benchmark remains required before any broad database superiority claim.']}; Path(a.output).write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps({'pass':payload['pass'],'root_speedup_p50':bench['root_speedup_p50'],'shadow_refresh_p50_ms':bench['shadow_delta_refresh']['p50_ms'],'canonical_root_p50_ms':bench['canonical_full_root_recompute']['p50_ms'],'page_ratio':bench['page_ratio']},sort_keys=True)); raise SystemExit(0 if payload['pass'] else 2)
if __name__=='__main__': main()
