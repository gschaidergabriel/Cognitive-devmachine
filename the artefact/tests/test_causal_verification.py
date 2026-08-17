"""Ordinary causal verification regressions; not a second unusual GO experiment."""
import uuid
import pytest
from clayverse.effects import EffectGate,EffectRequest
from clayverse.engine import ClayVerseEngine,InferenceAdapter
from clayverse.identity import IdentityRouter
from clayverse.mcp_server import ClayVerseBridge
from clayverse.store import UnifiedDB,IntegrityFailure,ReplayDetected,StaleGeneration


def setup_db(tmp_path):
    db=UnifiedDB(tmp_path/'unified.db'); router=IdentityRouter(db,{'g':'gabriel','a':'andreas'}); return db,router

def prov(request_id=None): return {'source':'test','request_id':request_id or uuid.uuid4().hex}

def test_requested_observed_verified_are_distinct_states(tmp_path):
    db,router=setup_db(tmp_path); uid,sid=router.resolve('g'); lease=db.acquire_lease('effect:x','worker',60)
    eid=db.prepare_effect(None,uid,sid,'state.noop','x',None,db.session_generation(sid),prov(),lease); assert db.effect_status(eid)=='REQUESTED'
    db.record_effect_outcome(eid,{'ok':True,'kind':'noop','target':'x','boundary':'internal'},lease); assert db.effect_status(eid)=='OBSERVED'
    db.verify_effect(eid,lease,verified=True,verifier='test-contract'); assert db.effect_status(eid)=='VERIFIED'; db.release_lease(lease); db.close()

def test_replay_and_generation_change_fail_closed(tmp_path):
    db,router=setup_db(tmp_path); uid,sid=router.resolve('g'); p=prov('same-request'); lease=db.acquire_lease('effect:x','worker',60)
    eid=db.prepare_effect(None,uid,sid,'state.noop','x',None,db.session_generation(sid),p,lease); db.bump_generation(sid)
    with pytest.raises(StaleGeneration): db.record_effect_outcome(eid,{'ok':True,'kind':'noop','target':'x','boundary':'internal'},lease)
    lease2=db.acquire_lease('effect:y','worker',60)
    with pytest.raises(ReplayDetected): db.prepare_effect(None,uid,sid,'state.noop','y',None,db.session_generation(sid),p,lease2)
    db.close()

class NoopInference(InferenceAdapter):
    def reason(self,world,observation): return {'text':'done','selection':'request_effect','effect':{'capability':'state.noop','target':'unit','argv':None}}
class DeniedInference(InferenceAdapter):
    def reason(self,world,observation): return {'text':'try','selection':'request_effect','effect':{'capability':'entityos.exec','target':'missing','argv':['x']}}

def test_web_engine_reenters_only_verified_effects(tmp_path):
    db=UnifiedDB(tmp_path/'u.db')
    plain=ClayVerseEngine(db,{'g':'gabriel'}).ingest('g','plain'); row=db.db.execute('select reentered,effect_id from causal_episodes where causal_id=?',(plain['causal_id'],)).fetchone(); assert row['reentered']==0 and row['effect_id'] is None
    verified=ClayVerseEngine(db,{'g':'gabriel'},inference=NoopInference()).ingest('g','verified'); row=db.db.execute('select reentered,credit from causal_episodes where causal_id=?',(verified['causal_id'],)).fetchone(); assert row['reentered']==1 and row['credit']==1.0
    denied=ClayVerseEngine(db,{'g':'gabriel'},inference=DeniedInference()).ingest('g','denied'); row=db.db.execute('select reentered,credit from causal_episodes where causal_id=?',(denied['causal_id'],)).fetchone(); assert denied['outcome']['denied'] is True and db.effect_status(denied['effect_id'])=='DENIED' and row['reentered']==0 and row['credit']==0.0
    assert db.verify_effect_integrity(); db.close()

def test_permanent_mcp_terminal_uses_same_verified_reentry_rule(tmp_path):
    db=UnifiedDB(tmp_path/'u.db'); IdentityRouter(db,{'g':'gabriel'}); bridge=ClayVerseBridge(db,'gabriel','session:gabriel')
    bridge.begin_turn('plain terminal turn'); plain=bridge.complete_turn('plain response'); assert plain['reentered'] is False and plain['effect_id'] is None
    bridge.begin_turn('verified terminal effect'); requested=bridge.request_effect('state.noop','unit'); assert requested['verified'] is True and requested['status']=='VERIFIED'; verified=bridge.complete_turn('effect response'); assert verified['reentered'] is True and verified['credit']==1.0
    bridge.begin_turn('denied terminal effect'); denied_request=bridge.request_effect('entityos.exec','missing',['x']); assert denied_request['verified'] is False and denied_request['status']=='DENIED'; denied=bridge.complete_turn('denied response'); assert denied['reentered'] is False and denied['credit']==0.0
    assert db.verify_effect_integrity(); db.close()

def test_legacy_verified_writer_cannot_create_reenterable_truth(tmp_path):
    db,router=setup_db(tmp_path); uid,sid=router.resolve('g'); tid=db.append_turn(sid,uid,'user','x'); from clayverse.workspace import Workspace; ws=Workspace(db).open(sid,tid,'x',[])
    eid=db.record_effect(ws['episode_id'],uid,'state.noop','x',db.session_generation(sid),'VERIFIED',outcome={'ok':True}); assert db.effect_status(eid)=='LEGACY_UNVERIFIED'
    causal=db.record_causal_episode(ws['episode_id'],eid,tid,1.0); row=db.db.execute('select reentered,credit from causal_episodes where causal_id=?',(causal,)).fetchone(); assert row['reentered']==0 and row['credit']==0.0; assert db.verify_effect_integrity(); db.close()
