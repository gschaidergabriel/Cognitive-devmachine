"""Regressions for journaled EntityOS effect fencing."""
import hashlib,json
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

def test_effect_journal_persists_hash_receipts_not_raw_payloads(tmp_path):
    db,uid,sid=setup_db(tmp_path); secret_arg='ARG_SECRET_42'; secret_out='OUTPUT_SECRET_77'
    def run(argv):
        assert secret_arg in argv
        return {'ok':True,'exit':0,'stdout':secret_out,'stderr':'sensitive-stderr'}
    eid,out=EffectGate(db,entityos_bridge=FakeBridge(run)).execute(EffectRequest(uid,sid,'entityos.exec','transport',[secret_arg]))
    assert out['stdout']==secret_out
    row=db.db.execute('SELECT argv,outcome FROM effects WHERE effect_id=?',(eid,)).fetchone()
    assert secret_arg not in row['argv'] and secret_out not in row['outcome'] and 'sensitive-stderr' not in row['outcome']
    argv_receipt=json.loads(row['argv']); outcome_receipt=json.loads(row['outcome'])
    expected_argv=json.dumps([secret_arg],ensure_ascii=False,separators=(',',':')).encode()
    assert argv_receipt=={'audit':'redacted-argv-v1','argc':1,'sha256':hashlib.sha256(expected_argv).hexdigest(),'bytes':len(expected_argv)}
    assert outcome_receipt['audit']=='redacted-outcome-v1' and outcome_receipt['ok'] is True and outcome_receipt['exit']==0
    assert len(outcome_receipt['sha256'])==64 and 'stdout' not in outcome_receipt and 'stderr' not in outcome_receipt
    db.close()

def test_completion_rechecks_lease_and_records_stale_outcome_without_reentry(tmp_path):
    db,uid,sid=setup_db(tmp_path); lease=db.acquire_lease('repo:main','worker',ttl=60)
    def run(argv):
        db.db.execute("UPDATE leases SET generation=generation+1,nonce='replaced' WHERE resource='repo:main'")
        return {'ok':True,'exit':0,'stdout':'did-it','stderr':''}
    with pytest.raises(StaleGeneration): EffectGate(db,entityos_bridge=FakeBridge(run)).execute(EffectRequest(uid,sid,'entityos.exec','transport',['hello']),lease=lease)
    effect=db.db.execute('SELECT effect_id,status,outcome FROM effects').fetchone(); persisted=json.loads(effect['outcome'])
    assert effect['status']=='STALE_OUTCOME' and 'did-it' not in effect['outcome'] and persisted['audit']=='redacted-outcome-v1' and persisted['ok'] is True
    causal=db.db.execute('SELECT credit,reentered,outcome_hash FROM causal_episodes WHERE effect_id=?',(effect['effect_id'],)).fetchone(); assert causal['credit']==0.0 and causal['reentered']==0 and len(causal['outcome_hash'])==64; db.close()

def test_generation_change_during_entityos_effect_is_stale_not_verified(tmp_path):
    db,uid,sid=setup_db(tmp_path)
    def run(argv):
        db.bump_generation(sid)
        return {'ok':True,'exit':0,'stdout':'did-it','stderr':''}
    with pytest.raises(StaleGeneration): EffectGate(db,entityos_bridge=FakeBridge(run)).execute(EffectRequest(uid,sid,'entityos.exec','transport',['hello']))
    effect=db.db.execute('SELECT effect_id,status,outcome FROM effects').fetchone(); assert effect['status']=='STALE_OUTCOME' and 'did-it' not in effect['outcome']
    causal=db.db.execute('SELECT credit,reentered FROM causal_episodes WHERE effect_id=?',(effect['effect_id'],)).fetchone(); assert tuple(causal)==(0.0,0); db.close()

def test_failed_entityos_attempt_is_receipted_without_reentry(tmp_path):
    db,uid,sid=setup_db(tmp_path)
    def run(argv): raise EntityOSIntegrityError('digest mismatch')
    with pytest.raises(EntityOSIntegrityError): EffectGate(db,entityos_bridge=FakeBridge(run)).execute(EffectRequest(uid,sid,'entityos.exec','transport',['hello']))
    effect=db.db.execute('SELECT effect_id,status,outcome FROM effects').fetchone(); assert effect['status']=='FAILED' and 'EntityOSIntegrityError' in effect['outcome']
    causal=db.db.execute('SELECT credit,reentered FROM causal_episodes WHERE effect_id=?',(effect['effect_id'],)).fetchone(); assert tuple(causal)==(0.0,0); db.close()

def test_restart_records_pending_as_unknown_without_reentry(tmp_path):
    p=tmp_path/'unified.db'; db,uid,sid=setup_db(tmp_path); gate=EffectGate(db); eid=gate.journal.begin(None,sid,uid,'state.noop','x',db.session_generation(sid)); db.close()
    db=UnifiedDB(p); EffectGate(db); effect=db.db.execute('SELECT status,outcome FROM effects WHERE effect_id=?',(eid,)).fetchone(); assert effect['status']=='UNKNOWN_AFTER_RESTART' and 'restart_before_verified_outcome' in effect['outcome']
    causal=db.db.execute('SELECT credit,reentered FROM causal_episodes WHERE effect_id=?',(eid,)).fetchone(); assert tuple(causal)==(0.0,0); db.close()

def test_direct_host_process_remains_forbidden(tmp_path):
    db,uid,sid=setup_db(tmp_path)
    with pytest.raises(PermissionError,match='direct host process execution forbidden'):
        EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','echo',['/bin/echo','no']))
    assert db.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0]==0; db.close()
