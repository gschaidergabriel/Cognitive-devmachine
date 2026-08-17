"""Ordinary regressions for effect fencing and the pinned EntityOS transport candidate."""
import hashlib, os, shutil, uuid
import pytest
from clayverse.store import UnifiedDB,StaleGeneration
from clayverse.identity import IdentityRouter
from clayverse.effects import EffectGate,EffectRequest
from clayverse.entityos_bridge import EntityOSBridge

def setup_db(tmp_path):
    db=UnifiedDB(tmp_path/'unified.db'); uid,sid=IdentityRouter(db,{'g':'gabriel'}).resolve('g'); return db,uid,sid

def prov(): return {'source':'test','request_id':uuid.uuid4().hex}

def test_regression_completion_rechecks_lease_before_outcome_record(tmp_path,monkeypatch):
    db,uid,sid=setup_db(tmp_path); lease=db.acquire_lease('effect:noop','worker',ttl=60); calls=0; original=db.assert_lease
    def fence(value):
        nonlocal calls; calls+=1
        if calls==3: raise StaleGeneration(value.resource)
        return original(value)
    monkeypatch.setattr(db,'assert_lease',fence)
    with pytest.raises(StaleGeneration): EffectGate(db).execute(EffectRequest(uid,sid,'state.noop','noop',None,db.session_generation(sid),prov()),lease=lease)
    row=db.db.execute('SELECT status,outcome FROM effects').fetchone(); assert row['status']=='REQUESTED' and row['outcome'] is None; db.close()

def test_entityos_bridge_is_open_object_digest_pinned_and_failures_are_observed(tmp_path):
    target=tmp_path/'EntityOS'; shutil.copy2('/bin/echo',target); os.chmod(target,0o755); digest=hashlib.sha256(target.read_bytes()).hexdigest(); db,uid,sid=setup_db(tmp_path)
    gate=EffectGate(db,entityos_bridge=EntityOSBridge(str(target),digest)); lease=db.acquire_lease('entityos:good','worker',60)
    eid,out=gate.execute(EffectRequest(uid,sid,'entityos.exec','transport',['hello'],db.session_generation(sid),prov()),lease=lease)
    assert eid and out['ok'] and out['stdout'].strip()=='hello' and out['boundary']=='EntityOS'; db.release_lease(lease)
    bad=EffectGate(db,entityos_bridge=EntityOSBridge(str(target),'0'*64)); lease=db.acquire_lease('entityos:bad','worker',60)
    eid2,out2=bad.execute(EffectRequest(uid,sid,'entityos.exec','transport',['must-not-execute'],db.session_generation(sid),prov()),lease=lease)
    row=db.db.execute('SELECT status,outcome_hash,verifier FROM effects WHERE effect_id=?',(eid2,)).fetchone()
    assert out2['ok'] is False and out2['kind']=='integrity_error' and row['status']=='VERIFIED' and len(row['outcome_hash'])==64 and row['verifier']; db.release_lease(lease)
    assert db.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0]==2; db.close()
