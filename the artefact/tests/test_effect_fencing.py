"""Regressions for journaled EntityOS effect fencing."""
import pytest
from clayverse.store import UnifiedDB,StaleGeneration
from clayverse.identity import IdentityRouter
from clayverse.effects import EffectGate,EffectRequest
from clayverse.entityos_bridge import EntityOSIntegrityError

def setup_db(tmp_path):
    db=UnifiedDB(tmp_path/'unified.db'); uid,sid=IdentityRouter(db,{'g':'gabriel'}).resolve('g'); return db,uid,sid

class FakeBridge:
    sha256='a'*64
    def __init__(self,run): self._run=run
    def run(self,argv): return self._run(argv)

def test_pending_receipt_exists_before_entityos_execution(tmp_path):
    db,uid,sid=setup_db(tmp_path); seen={}
    def run(argv):
        seen['status']=db.db.execute('SELECT status FROM effects ORDER BY ts DESC LIMIT 1').fetchone()[0]
        return {'ok':True,'exit':0,'stdout':'ok','stderr':''}
    eid,out=EffectGate(db,entityos_bridge=FakeBridge(run)).execute(EffectRequest(uid,sid,'entityos.exec','transport',['hello']))
    assert seen['status']=='PENDING'; assert out['ok']; assert db.db.execute('SELECT status FROM effects WHERE effect_id=?',(eid,)).fetchone()[0]=='VERIFIED'; db.close()

def test_completion_rechecks_lease_and_records_stale_outcome(tmp_path):
    db,uid,sid=setup_db(tmp_path); lease=db.acquire_lease('repo:main','worker',ttl=60)
    def run(argv):
        db.db.execute("UPDATE leases SET generation=generation+1,nonce='replaced' WHERE resource='repo:main'")
        return {'ok':True,'exit':0,'stdout':'did-it','stderr':''}
    with pytest.raises(StaleGeneration): EffectGate(db,entityos_bridge=FakeBridge(run)).execute(EffectRequest(uid,sid,'entityos.exec','transport',['hello']),lease=lease)
    effect=db.db.execute('SELECT effect_id,status,outcome FROM effects').fetchone(); assert effect['status']=='STALE_OUTCOME' and 'did-it' in effect['outcome']
    causal=db.db.execute('SELECT credit,reentered FROM causal_episodes WHERE effect_id=?',(effect['effect_id'],)).fetchone(); assert tuple(causal)==(0.0,1); db.close()

def test_generation_change_during_entityos_effect_is_stale_not_verified(tmp_path):
    db,uid,sid=setup_db(tmp_path)
    def run(argv):
        db.bump_generation(sid)
        return {'ok':True,'exit':0,'stdout':'did-it','stderr':''}
    with pytest.raises(StaleGeneration): EffectGate(db,entityos_bridge=FakeBridge(run)).execute(EffectRequest(uid,sid,'entityos.exec','transport',['hello']))
    effect=db.db.execute('SELECT effect_id,status FROM effects').fetchone(); assert effect['status']=='STALE_OUTCOME'
    assert db.db.execute('SELECT credit FROM causal_episodes WHERE effect_id=?',(effect['effect_id'],)).fetchone()[0]==0.0; db.close()

def test_failed_entityos_attempt_is_receipted(tmp_path):
    db,uid,sid=setup_db(tmp_path)
    def run(argv): raise EntityOSIntegrityError('digest mismatch')
    with pytest.raises(EntityOSIntegrityError): EffectGate(db,entityos_bridge=FakeBridge(run)).execute(EffectRequest(uid,sid,'entityos.exec','transport',['hello']))
    effect=db.db.execute('SELECT effect_id,status,outcome FROM effects').fetchone(); assert effect['status']=='FAILED' and 'EntityOSIntegrityError' in effect['outcome']
    assert db.db.execute('SELECT credit FROM causal_episodes WHERE effect_id=?',(effect['effect_id'],)).fetchone()[0]==0.0; db.close()

def test_restart_reenters_pending_as_unknown(tmp_path):
    p=tmp_path/'unified.db'; db,uid,sid=setup_db(tmp_path); gate=EffectGate(db); eid=gate.journal.begin(None,sid,uid,'state.noop','x',db.session_generation(sid)); db.close()
    db=UnifiedDB(p); EffectGate(db); effect=db.db.execute('SELECT status,outcome FROM effects WHERE effect_id=?',(eid,)).fetchone(); assert effect['status']=='UNKNOWN_AFTER_RESTART' and 'restart_before_verified_outcome' in effect['outcome']
    assert db.db.execute('SELECT credit FROM causal_episodes WHERE effect_id=?',(eid,)).fetchone()[0]==0.0; db.close()

def test_direct_host_process_remains_forbidden(tmp_path):
    db,uid,sid=setup_db(tmp_path)
    with pytest.raises(PermissionError,match='direct host process execution forbidden'):
        EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','echo',['/bin/echo','no']))
    assert db.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0]==0; db.close()
