"""Ordinary regressions for effect fencing and the pinned EntityOS transport candidate."""
import hashlib, os, shutil
import pytest
from clayverse.store import UnifiedDB,StaleGeneration
from clayverse.identity import IdentityRouter
from clayverse.effects import EffectGate,EffectRequest
from clayverse.entityos_bridge import EntityOSBridge,EntityOSIntegrityError

def setup_db(tmp_path):
    db=UnifiedDB(tmp_path/'unified.db'); uid,sid=IdentityRouter(db,{'g':'gabriel'}).resolve('g'); return db,uid,sid

def test_regression_completion_records_outcome_before_post_effect_lease_fence(tmp_path,monkeypatch):
    target=tmp_path/'EntityOS'; shutil.copy2('/bin/echo',target); os.chmod(target,0o755); digest=hashlib.sha256(target.read_bytes()).hexdigest()
    db,uid,sid=setup_db(tmp_path); lease=db.acquire_lease('repo:main','worker',ttl=60); calls=0; original=db.assert_lease
    def fence(value):
        nonlocal calls; calls+=1
        if calls==2: raise StaleGeneration(value.resource)
        return original(value)
    monkeypatch.setattr(db,'assert_lease',fence)
    gate=EffectGate(db,entityos_bridge=EntityOSBridge(str(target),digest))
    with pytest.raises(StaleGeneration): gate.execute(EffectRequest(uid,sid,'entityos.exec','echo',['ok'],request_key='g:lease-fence:effect:0'),lease=lease)
    assert db.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0]==1
    assert db.db.execute('SELECT status FROM effect_requests').fetchone()[0]=='VERIFIED'
    db.close()

def test_entityos_bridge_is_open_object_digest_pinned(tmp_path):
    target=tmp_path/'EntityOS'; shutil.copy2('/bin/echo',target); os.chmod(target,0o755); digest=hashlib.sha256(target.read_bytes()).hexdigest(); db,uid,sid=setup_db(tmp_path)
    eid,out=EffectGate(db,entityos_bridge=EntityOSBridge(str(target),digest)).execute(EffectRequest(uid,sid,'entityos.exec','transport',['hello'],request_key='g:entityos-ok:effect:0'))
    assert eid and out['ok'] and out['stdout'].strip()=='hello'
    with pytest.raises(EntityOSIntegrityError): EffectGate(db,entityos_bridge=EntityOSBridge(str(target),'0'*64)).execute(EffectRequest(uid,sid,'entityos.exec','transport',['hello'],request_key='g:entityos-bad-pin:effect:0'))
    assert db.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0]==1
    assert db.db.execute("SELECT status FROM effect_requests WHERE request_key='g:entityos-bad-pin:effect:0'").fetchone()[0]=='FAILED'
    db.close()
