"""Regressions for causal effect fencing and pinned EntityOS transport."""
import hashlib, os, shutil
import pytest
from clayverse.store import UnifiedDB,StaleGeneration
from clayverse.identity import IdentityRouter
from clayverse.effects import EffectGate,EffectRequest
from clayverse.entityos_bridge import EntityOSBridge,EntityOSIntegrityError

def setup_db(tmp_path):
    db=UnifiedDB(tmp_path/'unified.db'); uid,sid=IdentityRouter(db,{'g':'gabriel'}).resolve('g'); return db,uid,sid

def test_completion_rechecks_lease_and_records_stale_outcome(tmp_path,monkeypatch):
    db,uid,sid=setup_db(tmp_path); lease=db.acquire_lease('repo:main','worker',ttl=60)
    class CP: returncode=0; stdout=b'ok\n'; stderr=b''
    def fake_run(*args,**kwargs):
        db.db.execute("UPDATE leases SET generation=generation+1,nonce='replaced' WHERE resource='repo:main'")
        return CP()
    monkeypatch.setattr('clayverse.effects.subprocess.run',fake_run)
    with pytest.raises(StaleGeneration): EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','echo',['/bin/echo','ok']),lease=lease)
    effect=db.db.execute('SELECT effect_id,status,outcome FROM effects').fetchone(); assert effect['status']=='STALE_OUTCOME' and 'ok' in effect['outcome']
    causal=db.db.execute('SELECT credit,reentered FROM causal_episodes WHERE effect_id=?',(effect['effect_id'],)).fetchone(); assert tuple(causal)==(0.0,1); db.close()

def test_entityos_bridge_attempts_are_receipted(tmp_path):
    target=tmp_path/'EntityOS'; shutil.copy2('/bin/echo',target); os.chmod(target,0o755); digest=hashlib.sha256(target.read_bytes()).hexdigest(); db,uid,sid=setup_db(tmp_path)
    eid,out=EffectGate(db,entityos_bridge=EntityOSBridge(str(target),digest)).execute(EffectRequest(uid,sid,'entityos.exec','transport',['hello']))
    assert eid and out['ok'] and out['stdout'].strip()=='hello'
    with pytest.raises(EntityOSIntegrityError): EffectGate(db,entityos_bridge=EntityOSBridge(str(target),'0'*64)).execute(EffectRequest(uid,sid,'entityos.exec','transport',['hello']))
    rows=db.db.execute('SELECT status FROM effects ORDER BY ts').fetchall(); assert [r['status'] for r in rows]==['VERIFIED','FAILED']; db.close()

def test_pending_receipt_exists_before_host_execution(tmp_path,monkeypatch):
    db,uid,sid=setup_db(tmp_path); seen={}
    class CP: returncode=0; stdout=b'ok\n'; stderr=b''
    def fake_run(*args,**kwargs): seen['status']=db.db.execute('SELECT status FROM effects ORDER BY ts DESC LIMIT 1').fetchone()[0]; return CP()
    monkeypatch.setattr('clayverse.effects.subprocess.run',fake_run)
    eid,_=EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','echo',['/bin/echo','ok']))
    assert seen['status']=='PENDING'; assert db.db.execute('SELECT status FROM effects WHERE effect_id=?',(eid,)).fetchone()[0]=='VERIFIED'; db.close()

def test_generation_change_during_effect_is_stale_not_verified(tmp_path,monkeypatch):
    db,uid,sid=setup_db(tmp_path)
    class CP: returncode=0; stdout=b'did-it'; stderr=b''
    def fake_run(*args,**kwargs): db.bump_generation(sid); return CP()
    monkeypatch.setattr('clayverse.effects.subprocess.run',fake_run)
    with pytest.raises(StaleGeneration): EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','x',['/bin/true']))
    effect=db.db.execute('SELECT effect_id,status FROM effects ORDER BY ts DESC LIMIT 1').fetchone(); assert effect['status']=='STALE_OUTCOME'
    assert db.db.execute('SELECT credit FROM causal_episodes WHERE effect_id=?',(effect['effect_id'],)).fetchone()[0]==0.0; db.close()

def test_restart_reenters_pending_as_unknown(tmp_path):
    p=tmp_path/'unified.db'; db,uid,sid=setup_db(tmp_path); gate=EffectGate(db); eid=gate.journal.begin(None,sid,uid,'state.noop','x',db.session_generation(sid)); db.close()
    db=UnifiedDB(p); EffectGate(db); effect=db.db.execute('SELECT status,outcome FROM effects WHERE effect_id=?',(eid,)).fetchone(); assert effect['status']=='UNKNOWN_AFTER_RESTART' and 'restart_before_verified_outcome' in effect['outcome']
    assert db.db.execute('SELECT credit FROM causal_episodes WHERE effect_id=?',(eid,)).fetchone()[0]==0.0; db.close()
