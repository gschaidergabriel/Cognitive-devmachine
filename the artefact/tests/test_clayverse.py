import time,pytest
from clayverse.store import UnifiedDB,StaleGeneration
from clayverse.engine import ClayVerseEngine
from clayverse.identity import IdentityRouter
from clayverse.memory import MemoryManager
from clayverse.effects import EffectGate,EffectRequest
@pytest.fixture
def db(tmp_path):
    d=UnifiedDB(tmp_path/'unified.db'); yield d; d.close()
def engine(db): return ClayVerseEngine(db,{'clerk-g':'gabriel','clerk-a':'andreas'})
def test_two_equal_users_one_db(db):
    r=IdentityRouter(db,{'g':'gabriel','a':'andreas'}); assert r.resolve('g')[0]=='gabriel' and r.resolve('a')[0]=='andreas'; assert {x['rights'] for x in db.db.execute('select * from users')}=={'equal'}
def test_unmapped_identity_fails_closed(db):
    with pytest.raises(PermissionError): IdentityRouter(db,{}).resolve('unknown')
def test_last_20_remain_full_and_older_compress(db):
    r=IdentityRouter(db,{'g':'gabriel'}); uid,sid=r.resolve('g'); mm=MemoryManager(db)
    for i in range(45): db.append_turn(sid,uid,'user',f'turn {i} '+('x '*50))
    mm.compact(sid); rows=db.all_turns(sid); assert all(x['fidelity']=='full' for x in rows[-20:]); assert any(x['fidelity']!='full' for x in rows[:-20])
def test_explicit_durable_memory_only(db):
    e=engine(db); e.ingest('clerk-g','FACT: alpha is beta\nnormal sentence'); mem=db.memories(); assert len(mem)==1 and mem[0]['value']=='alpha is beta'
def test_collision_triggers_cross_session_retrieval(db):
    e=engine(db); e.ingest('clerk-g','editing resource',resources=['repo:file.txt']); assert e.ingest('clerk-a','also editing',resources=['repo:file.txt'])['collision_count']>=1; assert e.ingest('clerk-a','unrelated',resources=['repo:other.txt'])['collision_count']==0
def test_claygraph_is_rebuildable_projection(db):
    e=engine(db); e.ingest('clerk-g','FACT: graph source'); c=e.graph.counts(); db.db.execute('delete from graph_nodes'); db.db.execute('delete from graph_edges'); assert e.graph.rebuild()==c and c['nodes']>0
def test_stale_lease_is_rejected_aba(db):
    IdentityRouter(db,{'g':'gabriel'}); l1=db.acquire_lease('repo:x','worker-A',ttl=.01); time.sleep(.02); l2=db.acquire_lease('repo:x','worker-B',ttl=10)
    with pytest.raises(StaleGeneration): db.assert_lease(l1)
    db.assert_lease(l2)
def test_process_gate_no_shell_and_disabled_by_default(db):
    r=IdentityRouter(db,{'g':'gabriel'}); uid,sid=r.resolve('g'); gate=EffectGate(db,allow_process=False)
    with pytest.raises(PermissionError): gate.execute(EffectRequest(uid,sid,'process.exec','echo',['/bin/echo','ok']))
    eid,out=EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','echo',['/bin/echo','ok'])); assert out['ok'] and out['stdout'].strip()=='ok'
def test_causal_reentry_and_restart_continuity(tmp_path):
    p=tmp_path/'state.db'; d=UnifiedDB(p); ClayVerseEngine(d,{'g':'gabriel'}).ingest('g','FACT: persistent'); d.close(); d=UnifiedDB(p); assert d.db.execute('select count(*) from causal_episodes where reentered=1').fetchone()[0]==1; assert d.db.execute('select value from durable_memory').fetchone()[0]=='persistent'; d.close()
def test_checkpoint_hash_changes_on_canonical_state(db):
    r=IdentityRouter(db,{'g':'gabriel'}); _,h1=db.checkpoint('before'); uid,sid=r.resolve('g'); db.append_turn(sid,uid,'user','x'); _,h2=db.checkpoint('after'); assert h1!=h2

def test_effect_is_pending_before_host_execution(db,monkeypatch):
    r=IdentityRouter(db,{'g':'gabriel'}); uid,sid=r.resolve('g'); seen={}
    class CP: returncode=0; stdout=b'ok\n'; stderr=b''
    def fake_run(*args,**kwargs):
        row=db.db.execute("SELECT status FROM effects ORDER BY ts DESC LIMIT 1").fetchone(); seen['status']=row['status'] if row else None; return CP()
    monkeypatch.setattr('clayverse.effects.subprocess.run',fake_run)
    eid,out=EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','echo',['/bin/echo','ok']))
    assert seen['status']=='PENDING'; assert db.db.execute("SELECT status FROM effects WHERE effect_id=?",(eid,)).fetchone()[0]=='VERIFIED'; assert db.causal_for_effect(eid)

def test_restart_reenters_pending_effect_as_unknown(tmp_path):
    p=tmp_path/'state.db'; d=UnifiedDB(p); r=IdentityRouter(d,{'g':'gabriel'}); uid,sid=r.resolve('g'); gen=d.session_generation(sid); eid=d.begin_effect(None,uid,'state.noop','x',gen); d.close()
    d=UnifiedDB(p); row=d.db.execute("SELECT status,outcome FROM effects WHERE effect_id=?",(eid,)).fetchone(); causal=d.db.execute("SELECT credit,reentered FROM causal_episodes WHERE effect_id=?",(eid,)).fetchone(); assert row['status']=='UNKNOWN_AFTER_RESTART'; assert 'restart_before_verified_outcome' in row['outcome']; assert tuple(causal)==(0.0,1); d.close()

def test_generation_change_during_effect_records_stale_outcome(db,monkeypatch):
    r=IdentityRouter(db,{'g':'gabriel'}); uid,sid=r.resolve('g')
    class CP: returncode=0; stdout=b'did-it'; stderr=b''
    def fake_run(*args,**kwargs): db.bump_generation(sid); return CP()
    monkeypatch.setattr('clayverse.effects.subprocess.run',fake_run)
    with pytest.raises(StaleGeneration): EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','x',['/bin/true']))
    effect=db.db.execute("SELECT effect_id,status,outcome FROM effects ORDER BY ts DESC LIMIT 1").fetchone(); assert effect['status']=='STALE_OUTCOME'; causal=db.db.execute("SELECT credit,reentered FROM causal_episodes WHERE effect_id=?",(effect['effect_id'],)).fetchone(); assert tuple(causal)==(0.0,1); assert 'did-it' in effect['outcome']

def test_lease_change_during_effect_records_stale_outcome(db,monkeypatch):
    r=IdentityRouter(db,{'g':'gabriel'}); uid,sid=r.resolve('g'); lease=db.acquire_lease('repo:x','worker-A',ttl=60)
    class CP: returncode=0; stdout=b'did-it'; stderr=b''
    def fake_run(*args,**kwargs): db.db.execute("UPDATE leases SET generation=generation+1,nonce='replaced' WHERE resource='repo:x'"); return CP()
    monkeypatch.setattr('clayverse.effects.subprocess.run',fake_run)
    with pytest.raises(StaleGeneration): EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','x',['/bin/true']),lease=lease)
    effect=db.db.execute("SELECT effect_id,status FROM effects ORDER BY ts DESC LIMIT 1").fetchone(); assert effect['status']=='STALE_OUTCOME'; assert db.causal_for_effect(effect['effect_id'])
