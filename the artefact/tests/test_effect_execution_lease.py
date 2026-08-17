"""Full-window execution fencing for EntityOS effects."""
import threading,time
import pytest
from clayverse.store import UnifiedDB,LeaseConflict,StaleGeneration
from clayverse.identity import IdentityRouter
from clayverse.effects import EffectGate,EffectRequest

class FakeBridge:
    sha256='b'*64
    timeout=1.0
    def __init__(self,run): self._run=run
    def run(self,argv): return self._run(argv)

def setup_db(tmp_path):
    path=tmp_path/'unified.db'; db=UnifiedDB(path); uid,sid=IdentityRouter(db,{'g':'gabriel'}).resolve('g'); return path,db,uid,sid

def test_same_target_entityos_effects_cannot_overlap(tmp_path):
    path,db1,uid,sid=setup_db(tmp_path)
    db2=UnifiedDB(path)
    started=threading.Event(); release=threading.Event(); calls=[]; result={}
    def slow(argv):
        calls.append(('slow',tuple(argv))); started.set(); assert release.wait(2.0)
        return {'ok':True,'exit':0,'stdout':'a','stderr':''}
    def fast(argv):
        calls.append(('fast',tuple(argv))); return {'ok':True,'exit':0,'stdout':'b','stderr':''}
    gate1=EffectGate(db1,entityos_bridge=FakeBridge(slow)); gate2=EffectGate(db2,entityos_bridge=FakeBridge(fast))
    def worker():
        try: result['value']=gate1.execute(EffectRequest(uid,sid,'entityos.exec','same-target',['one']))
        except Exception as exc: result['error']=exc
    thread=threading.Thread(target=worker); thread.start(); assert started.wait(1.0)
    with pytest.raises(LeaseConflict):
        gate2.execute(EffectRequest(uid,sid,'entityos.exec','same-target',['two']))
    assert calls==[('slow',('one',))]
    release.set(); thread.join(2.0); assert not thread.is_alive() and 'error' not in result
    eid,out=gate2.execute(EffectRequest(uid,sid,'entityos.exec','same-target',['two']))
    assert out['ok'] is True and calls[-1]==('fast',('two',))
    assert db2.db.execute('SELECT status FROM effects WHERE effect_id=?',(eid,)).fetchone()[0]=='VERIFIED'
    db2.close(); db1.close()

def test_tampered_execution_lease_fails_stale_and_new_owner_survives_cleanup(tmp_path):
    path,db,uid,sid=setup_db(tmp_path); seen={}
    def tamper(argv):
        row=db.db.execute("SELECT resource,holder,generation,nonce FROM leases WHERE resource LIKE 'effect:%'").fetchone(); assert row is not None
        seen['resource']=row['resource']; seen['generation']=int(row['generation'])
        db.db.execute("UPDATE leases SET holder='replacement',generation=generation+1,expires_at=?,nonce='replacement-nonce' WHERE resource=?",(time.time()+60,row['resource']))
        return {'ok':True,'exit':0,'stdout':'did-it','stderr':''}
    gate=EffectGate(db,entityos_bridge=FakeBridge(tamper))
    with pytest.raises(StaleGeneration):
        gate.execute(EffectRequest(uid,sid,'entityos.exec','same-target',['one']))
    effect=db.db.execute('SELECT status,outcome FROM effects').fetchone(); assert effect['status']=='STALE_OUTCOME' and 'did-it' not in effect['outcome']
    lease=db.db.execute('SELECT holder,generation,nonce FROM leases WHERE resource=?',(seen['resource'],)).fetchone()
    assert lease['holder']=='replacement' and int(lease['generation'])==seen['generation']+1 and lease['nonce']=='replacement-nonce'
    db.close()

def test_entityos_execution_rejects_caller_supplied_fencing_lease(tmp_path):
    path,db,uid,sid=setup_db(tmp_path); external=db.acquire_lease('repo:main','worker',ttl=60)
    gate=EffectGate(db,entityos_bridge=FakeBridge(lambda argv:{'ok':True,'exit':0,'stdout':'x','stderr':''}))
    with pytest.raises(ValueError,match='managed internally'):
        gate.execute(EffectRequest(uid,sid,'entityos.exec','same-target',['one']),lease=external)
    assert db.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0]==0
    db.close()

def test_invalid_bridge_timeout_fails_before_journal_or_execution(tmp_path):
    path,db,uid,sid=setup_db(tmp_path); called=[]
    bridge=FakeBridge(lambda argv:called.append(argv) or {'ok':True,'exit':0,'stdout':'x','stderr':''}); bridge.timeout=float('inf')
    with pytest.raises(ValueError,match='invalid EntityOS timeout'):
        EffectGate(db,entityos_bridge=bridge).execute(EffectRequest(uid,sid,'entityos.exec','same-target',['one']))
    assert called==[] and db.db.execute('SELECT COUNT(*) FROM effects').fetchone()[0]==0
    db.close()
