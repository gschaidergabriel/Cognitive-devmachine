"""Ordinary causal/effect regressions. This file is not a new unusual go experiment."""
import hashlib, os, shutil, threading, uuid
import pytest
from clayverse.store import UnifiedDB,StaleGeneration,ReplayDetected,IntegrityFailure
from clayverse.identity import IdentityRouter
from clayverse.effects import EffectGate,EffectRequest
from clayverse.engine import ClayVerseEngine,InferenceAdapter
from clayverse.entityos_bridge import EntityOSBridge


def setup(tmp_path):
    db=UnifiedDB(tmp_path/'u.db'); r=IdentityRouter(db,{'g':'gabriel','a':'andreas'}); return db,r

def prov(value=None): return {'source':'test','request_id':value or uuid.uuid4().hex}

def test_effect_is_not_verified_until_explicit_verification(tmp_path):
    db,r=setup(tmp_path); uid,sid=r.resolve('g'); lease=db.acquire_lease('effect:test','w',60)
    eid=db.prepare_effect(None,uid,sid,'state.noop','x',None,db.session_generation(sid),prov(),lease)
    assert db.db.execute('select status from effects where effect_id=?',(eid,)).fetchone()[0]=='REQUESTED'
    db.record_effect_outcome(eid,{'ok':True,'kind':'noop','target':'x','boundary':'internal'},lease)
    assert db.db.execute('select status from effects where effect_id=?',(eid,)).fetchone()[0]=='OBSERVED'
    with pytest.raises(IntegrityFailure): db.record_causal_reentry('missing',eid,'missing')
    db.verify_effect(eid,lease,verified=True,verifier='test-v1')
    assert db.db.execute('select status from effects where effect_id=?',(eid,)).fetchone()[0]=='VERIFIED'
    db.release_lease(lease); db.close()

def test_gate_requires_lease_and_provenance_and_rejects_replay(tmp_path):
    db,r=setup(tmp_path); uid,sid=r.resolve('g'); gate=EffectGate(db)
    with pytest.raises(PermissionError,match='provenance'):
        gate.execute(EffectRequest(uid,sid,'state.noop','x'),lease=db.acquire_lease('a','w',60))
    p=prov('same-request'); l1=db.acquire_lease('b','w',60)
    eid,out=gate.execute(EffectRequest(uid,sid,'state.noop','x',provenance=p),lease=l1); assert eid and out['ok']
    db.release_lease(l1); l2=db.acquire_lease('b','w2',60)
    with pytest.raises(ReplayDetected): gate.execute(EffectRequest(uid,sid,'state.noop','x',provenance=p),lease=l2)
    assert db.db.execute('select count(*) from effects').fetchone()[0]==1; db.close()

def test_release_preserves_aba_generation(tmp_path):
    db,r=setup(tmp_path); r.resolve('g'); l1=db.acquire_lease('shared','a',60); db.release_lease(l1); l2=db.acquire_lease('shared','b',60)
    assert l2.generation==l1.generation+1
    with pytest.raises(StaleGeneration): db.assert_lease(l1)
    db.assert_lease(l2); db.close()

def test_generation_change_after_request_blocks_outcome(tmp_path):
    db,r=setup(tmp_path); uid,sid=r.resolve('g'); lease=db.acquire_lease('effect:x','w',60); eid=db.prepare_effect(None,uid,sid,'state.noop','x',None,db.session_generation(sid),prov(),lease); db.bump_generation(sid)
    with pytest.raises(StaleGeneration): db.record_effect_outcome(eid,{'ok':True,'kind':'noop','target':'x','boundary':'internal'},lease)
    assert db.db.execute('select status from effects where effect_id=?',(eid,)).fetchone()[0]=='REQUESTED'; db.close()

def test_failed_entityos_exit_is_verified_failure_not_success(tmp_path):
    target=tmp_path/'EntityOS'; shutil.copy2('/bin/false',target); os.chmod(target,0o755); digest=hashlib.sha256(target.read_bytes()).hexdigest()
    db,r=setup(tmp_path); uid,sid=r.resolve('g'); lease=db.acquire_lease('effect:false','w',60); gate=EffectGate(db,entityos_bridge=EntityOSBridge(str(target),digest))
    eid,out=gate.execute(EffectRequest(uid,sid,'entityos.exec','false',['x'],db.session_generation(sid),prov()),lease=lease)
    row=db.db.execute('select status,outcome_hash,verifier from effects where effect_id=?',(eid,)).fetchone()
    assert out['ok'] is False and out['exit']!=0 and row['status']=='VERIFIED' and len(row['outcome_hash'])==64 and row['verifier']; db.release_lease(lease); db.close()

class NoopInference(InferenceAdapter):
    def reason(self,world,observation): return {'text':'done','selection':'respond','effect':{'capability':'state.noop','target':'unit','argv':None}}

def test_only_verified_effect_reenters_and_no_effect_does_not(tmp_path):
    p=tmp_path/'u.db'; db=UnifiedDB(p)
    plain=ClayVerseEngine(db,{'g':'gabriel'}).ingest('g','plain'); plain_row=db.db.execute('select reentered,effect_id from causal_episodes where causal_id=?',(plain['causal_id'],)).fetchone(); assert plain_row['reentered']==0 and plain_row['effect_id'] is None
    eff=ClayVerseEngine(db,{'g':'gabriel'},inference=NoopInference()).ingest('g','effect'); row=db.db.execute('select reentered,outcome_hash from causal_episodes where causal_id=?',(eff['causal_id'],)).fetchone(); assert row['reentered']==1 and len(row['outcome_hash'])==64
    assert db.integrity_check()['causal_events']==4; db.close(); db=UnifiedDB(p); assert db.integrity_check()['ok']; db.close()

def test_two_user_threaded_writes_and_same_session_turn_order(tmp_path):
    db=UnifiedDB(tmp_path/'u.db'); engine=ClayVerseEngine(db,{'g':'gabriel','a':'andreas'}); errors=[]
    def worker(sub,prefix):
        try:
            for i in range(15): engine.ingest(sub,f'{prefix}-{i}')
        except Exception as exc: errors.append(exc)
    t1=threading.Thread(target=worker,args=('g','g')); t2=threading.Thread(target=worker,args=('a','a')); t1.start(); t2.start(); t1.join(); t2.join(); assert errors==[]
    for sid in ('session:gabriel','session:andreas'):
        rows=db.all_turns(sid); assert len(rows)==30; assert [r['ordinal'] for r in rows]==list(range(1,31)); assert [r['role'] for r in rows]==['user','assistant']*15
    assert db.integrity_check()['ok']; db.close()

def test_causal_event_tamper_is_detected_as_ordinary_integrity_regression(tmp_path):
    db,r=setup(tmp_path); uid,sid=r.resolve('g'); lease=db.acquire_lease('effect:x','w',60); EffectGate(db).execute(EffectRequest(uid,sid,'state.noop','x',provenance=prov()),lease=lease)
    db.db.execute("update causal_events set payload='{}' where seq=1")
    with pytest.raises(IntegrityFailure): db.integrity_check()
    db.close()
