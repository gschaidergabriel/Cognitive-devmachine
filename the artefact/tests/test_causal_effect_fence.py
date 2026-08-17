import pytest
from clayverse.store import UnifiedDB,StaleGeneration
from clayverse.identity import IdentityRouter
from clayverse.effects import EffectGate,EffectRequest

@pytest.fixture
def db(tmp_path):
    d=UnifiedDB(tmp_path/'unified.db')
    yield d
    d.close()

def test_effect_is_pending_before_host_execution(db,monkeypatch):
    r=IdentityRouter(db,{'g':'gabriel'}); uid,sid=r.resolve('g'); seen={}
    class CP: returncode=0; stdout=b'ok\n'; stderr=b''
    def fake_run(*args,**kwargs):
        row=db.db.execute("SELECT status FROM effects ORDER BY ts DESC LIMIT 1").fetchone(); seen['status']=row['status'] if row else None; return CP()
    monkeypatch.setattr('clayverse.effects.subprocess.run',fake_run)
    eid,out=EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','echo',['/bin/echo','ok']))
    assert seen['status']=='PENDING'
    assert db.db.execute("SELECT status FROM effects WHERE effect_id=?",(eid,)).fetchone()[0]=='VERIFIED'
    assert db.causal_for_effect(eid)

def test_restart_reenters_pending_effect_as_unknown(tmp_path):
    p=tmp_path/'state.db'; d=UnifiedDB(p); r=IdentityRouter(d,{'g':'gabriel'}); uid,sid=r.resolve('g'); gen=d.session_generation(sid); eid=d.begin_effect(None,uid,'state.noop','x',gen); d.close()
    d=UnifiedDB(p); row=d.db.execute("SELECT status,outcome FROM effects WHERE effect_id=?",(eid,)).fetchone(); causal=d.db.execute("SELECT credit,reentered FROM causal_episodes WHERE effect_id=?",(eid,)).fetchone()
    assert row['status']=='UNKNOWN_AFTER_RESTART'
    assert 'restart_before_verified_outcome' in row['outcome']
    assert tuple(causal)==(0.0,1)
    d.close()

def test_generation_change_during_effect_records_stale_outcome(db,monkeypatch):
    r=IdentityRouter(db,{'g':'gabriel'}); uid,sid=r.resolve('g')
    class CP: returncode=0; stdout=b'did-it'; stderr=b''
    def fake_run(*args,**kwargs): db.bump_generation(sid); return CP()
    monkeypatch.setattr('clayverse.effects.subprocess.run',fake_run)
    with pytest.raises(StaleGeneration): EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','x',['/bin/true']))
    effect=db.db.execute("SELECT effect_id,status,outcome FROM effects ORDER BY ts DESC LIMIT 1").fetchone(); causal=db.db.execute("SELECT credit,reentered FROM causal_episodes WHERE effect_id=?",(effect['effect_id'],)).fetchone()
    assert effect['status']=='STALE_OUTCOME'
    assert tuple(causal)==(0.0,1)
    assert 'did-it' in effect['outcome']

def test_lease_change_during_effect_records_stale_outcome(db,monkeypatch):
    r=IdentityRouter(db,{'g':'gabriel'}); uid,sid=r.resolve('g'); lease=db.acquire_lease('repo:x','worker-A',ttl=60)
    class CP: returncode=0; stdout=b'did-it'; stderr=b''
    def fake_run(*args,**kwargs): db.db.execute("UPDATE leases SET generation=generation+1,nonce='replaced' WHERE resource='repo:x'"); return CP()
    monkeypatch.setattr('clayverse.effects.subprocess.run',fake_run)
    with pytest.raises(StaleGeneration): EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','x',['/bin/true']),lease=lease)
    effect=db.db.execute("SELECT effect_id,status FROM effects ORDER BY ts DESC LIMIT 1").fetchone()
    assert effect['status']=='STALE_OUTCOME'
    assert db.causal_for_effect(effect['effect_id'])
