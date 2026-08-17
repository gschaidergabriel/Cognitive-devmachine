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
    with pytest.raises(PermissionError): EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','shell',['/bin/sh','-c','echo forbidden']))
    with pytest.raises(ValueError): EffectGate(db,allow_process=True).execute(EffectRequest(uid,sid,'process.exec','nul',['/bin/echo','bad\x00arg']))
def test_causal_reentry_and_restart_continuity(tmp_path):
    p=tmp_path/'state.db'; d=UnifiedDB(p); ClayVerseEngine(d,{'g':'gabriel'}).ingest('g','FACT: persistent'); d.close(); d=UnifiedDB(p); assert d.db.execute('select count(*) from causal_episodes where reentered=1').fetchone()[0]==1; assert d.db.execute('select value from durable_memory').fetchone()[0]=='persistent'; d.close()
def test_checkpoint_hash_changes_on_canonical_state(db):
    r=IdentityRouter(db,{'g':'gabriel'}); _,h1=db.checkpoint('before'); uid,sid=r.resolve('g'); db.append_turn(sid,uid,'user','x'); _,h2=db.checkpoint('after'); assert h1!=h2
