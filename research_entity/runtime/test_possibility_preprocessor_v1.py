import sqlite3, importlib.util, pathlib, sys, tempfile
from datetime import datetime, timedelta, timezone

HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pp', HERE/'possibility_preprocessor_v1.py')
pp=importlib.util.module_from_spec(spec); sys.modules['pp']=pp; spec.loader.exec_module(pp)
MIG=(HERE/'RAE_UNIFIEDDB_V10_POSSIBILITY_PREPROCESSOR.sql').read_text()

def db():
    con=sqlite3.connect(':memory:'); con.executescript(MIG); return con

def file_db(path):
    con=sqlite3.connect(path); con.executescript(MIG); return con

def c(cid,sig,utility,evidence,risk,dep,graph=None,hp=()):
    return pp.Candidate(candidate_id=cid,context_signature=sig,source_epoch=1,graph_epoch=1,candidate_kind='AFFORDANCE',semantic_refs=[cid],graph_refs=list(graph or []),hyperposition_refs=list(hp),evidence_refs=[f'e:{cid}'],conflict_refs=[],uncertainty_refs=[],authority_refs=['proposal_only'],dependency_refs=list(dep),utility=utility,coherence=.8,urgency=.4,evidence_score=evidence,risk=risk,cost=.1,provenance={'fixture':cid},derivation_hash=pp.sha256_text(cid))

def test_packet_is_deterministic_and_hot_readable():
    con=db(); sig=pp.canonical_context_signature(['goal:test','constraint:ubuntu'])
    pp.upsert_candidates(con,[c('a',sig,.9,.9,.1,['cap:a'],['g:a']),c('b',sig,.7,.8,.2,['cap:b'],['g:b'],['alt:1'])])
    pp.compile_packet(con,sig,1,1,top_k=2); con.commit(); h1=con.execute("select packet_hash from possibility_packets where status='CURRENT'").fetchone()[0]
    p2=pp.compile_packet(con,sig,1,1,top_k=2); con.commit(); h2=con.execute("select packet_hash from possibility_packets where status='CURRENT'").fetchone()[0]
    assert h1==h2 and p2['selected'][0]['candidate_id']=='a'
    assert pp.read_current_packet(con,sig)['selected'][0]['candidate_id']=='a'
    assert 'alt:1' in p2['selected'][1]['hyperposition_refs']

def test_targeted_invalidation_only_hits_dependency_closure():
    con=db(); s1=pp.canonical_context_signature(['goal:1']); s2=pp.canonical_context_signature(['goal:2'])
    pp.upsert_candidates(con,[c('a',s1,.9,.9,.1,['shared:x']),c('b',s2,.9,.9,.1,['other:y'])]); pp.compile_packet(con,s1,1,1); pp.compile_packet(con,s2,1,1); con.commit()
    assert pp.invalidate_ref(con,'shared:x',2,'CAPABILITY_DELTA')==[s1]; con.commit()
    assert pp.read_current_packet(con,s1) is None and pp.read_current_packet(con,s2) is not None

def test_graph_activation_never_creates_authority():
    con=db(); sig=pp.canonical_context_signature(['goal:authority']); pp.upsert_candidates(con,[c('graph_hot',sig,1.0,.2,.0,['dep:z'],['graph:activation:0.99'])]); p=pp.compile_packet(con,sig,1,1); con.commit()
    assert p['selected'][0]['authority_refs']==['proposal_only'] and 'graph:activation:0.99' in p['selected'][0]['graph_refs']

def test_candidate_retirement_is_dependency_targeted():
    con=db(); s1=pp.canonical_context_signature(['goal:1']); s2=pp.canonical_context_signature(['goal:2'])
    pp.upsert_candidates(con,[c('a',s1,.9,.9,.1,['shared:x']),c('b',s2,.9,.9,.1,['other:y'])]); con.commit(); assert pp.retire_candidates_by_ref(con,'shared:x')==[s1]; con.commit()
    assert con.execute("select status from possibility_candidates where candidate_id='a' order by source_epoch desc limit 1").fetchone()[0]=='STALE'
    assert con.execute("select status from possibility_candidates where candidate_id='b' order by source_epoch desc limit 1").fetchone()[0]=='CURRENT'

def test_logical_candidate_versioning_and_epoch_guard():
    con=db(); sig=pp.canonical_context_signature(['goal:epoch']); a1=c('same',sig,.6,.7,.1,['dep:v1']); pp.upsert_candidates(con,[a1]); pp.compile_packet(con,sig,1,1); con.commit()
    assert pp.read_current_packet(con,sig,expected_source_epoch=1,expected_graph_epoch=1) is not None
    a2=pp.Candidate(**{**a1.__dict__,'source_epoch':2,'graph_epoch':2,'utility':.95,'derivation_hash':pp.sha256_text('same-v2')}); pp.upsert_candidates(con,[a2]); pp.compile_packet(con,sig,2,2); con.commit()
    assert con.execute("select source_epoch,status from possibility_candidates where candidate_id='same' order by source_epoch").fetchall()==[(1,'STALE'),(2,'CURRENT')]
    assert pp.read_current_packet(con,sig,expected_source_epoch=2,expected_graph_epoch=2) is not None
    assert pp.read_current_packet(con,sig,expected_source_epoch=1) is None and pp.read_current_packet(con,sig,expected_graph_epoch=1) is None

def test_family_factorization_and_freshness_gate():
    con=db(); sig=pp.canonical_context_signature(['goal:families'])
    a1=pp.Candidate(**{**c('a1',sig,.99,.95,.05,['dep:a1']).__dict__,'family_id':'family:A'}); a2=pp.Candidate(**{**c('a2',sig,.98,.94,.05,['dep:a2']).__dict__,'family_id':'family:A'}); b=pp.Candidate(**{**c('b1',sig,.80,.90,.05,['dep:b']).__dict__,'family_id':'family:B'})
    pp.upsert_candidates(con,[a1,a2,b]); p=pp.compile_packet(con,sig,1,1,top_k=2); con.commit()
    assert [x['family_id'] for x in p['selected']]==['family:A','family:B'] and p['selected'][0]['candidate_id']=='a1'
    assert any(x.get('reason')=='DUPLICATE_FAMILY' for x in p['suppressed'])
    now=datetime.now(timezone.utc)
    past=(now-timedelta(seconds=30)).isoformat(); future=(now+timedelta(seconds=60)).isoformat()
    sig2=pp.canonical_context_signature(['goal:fresh'])
    expired=pp.Candidate(**{**c('expired',sig2,1.0,1.0,0.0,['dep:old']).__dict__,'family_id':'old','valid_until':past})
    fresh=pp.Candidate(**{**c('fresh',sig2,.6,.8,.1,['dep:new']).__dict__,'family_id':'new','valid_until':future})
    pp.upsert_candidates(con,[expired,fresh]); p2=pp.compile_packet(con,sig2,1,1,top_k=2); con.commit()
    assert [x['candidate_id'] for x in p2['selected']]==['fresh']

def test_restart_and_rollback_preserve_last_coherent_packet():
    with tempfile.TemporaryDirectory() as td:
        path=str(pathlib.Path(td)/'u10.sqlite'); con=file_db(path); sig=pp.canonical_context_signature(['goal:recovery'])
        a1=c('recover',sig,.7,.8,.1,['dep:recover']); pp.upsert_candidates(con,[a1]); pp.compile_packet(con,sig,1,1); con.commit()
        before=con.execute("select packet_hash from possibility_packets where status='CURRENT' and context_signature=?",(sig,)).fetchone()[0]
        con.close(); con=sqlite3.connect(path)
        assert pp.read_current_packet(con,sig,expected_source_epoch=1,expected_graph_epoch=1) is not None
        con.execute('BEGIN IMMEDIATE'); pp.invalidate_ref(con,'dep:recover',2,'TEST_ROLLBACK')
        a2=pp.Candidate(**{**a1.__dict__,'source_epoch':2,'graph_epoch':2,'utility':.95,'derivation_hash':pp.sha256_text('recover-v2')}); pp.upsert_candidates(con,[a2]); pp.compile_packet(con,sig,2,2); con.rollback()
        after=con.execute("select packet_hash from possibility_packets where status='CURRENT' and context_signature=?",(sig,)).fetchone()[0]
        assert after==before and pp.read_current_packet(con,sig,expected_source_epoch=1,expected_graph_epoch=1) is not None
        con.close()

def test_atomic_publication_reader_sees_old_then_new_epoch():
    with tempfile.TemporaryDirectory() as td:
        path=str(pathlib.Path(td)/'u10.sqlite'); writer=file_db(path); writer.execute('PRAGMA journal_mode=WAL'); sig=pp.canonical_context_signature(['goal:atomic'])
        a1=c('atomic',sig,.6,.8,.1,['dep:atomic']); pp.upsert_candidates(writer,[a1]); pp.compile_packet(writer,sig,1,1); writer.commit(); reader=sqlite3.connect(path)
        writer.execute('BEGIN IMMEDIATE'); pp.invalidate_ref(writer,'dep:atomic',2,'ATOMIC_PUBLISH')
        a2=pp.Candidate(**{**a1.__dict__,'source_epoch':2,'graph_epoch':2,'utility':.99,'derivation_hash':pp.sha256_text('atomic-v2')}); pp.upsert_candidates(writer,[a2]); pp.compile_packet(writer,sig,2,2)
        assert pp.read_current_packet(reader,sig,expected_source_epoch=1,expected_graph_epoch=1) is not None
        assert pp.read_current_packet(reader,sig,expected_source_epoch=2,expected_graph_epoch=2) is None
        writer.commit()
        assert pp.read_current_packet(reader,sig,expected_source_epoch=1,expected_graph_epoch=1) is None
        assert pp.read_current_packet(reader,sig,expected_source_epoch=2,expected_graph_epoch=2) is not None
        reader.close(); writer.close()

def test_adaptive_materialization_policy():
    mode,net=pp.choose_materialization_mode(read_rate=10,update_rate=1,lazy_query_ms=4.0,packet_query_ms=.02,maintenance_ms=.8); assert mode=='STANDING' and net>0
    mode,net=pp.choose_materialization_mode(read_rate=.01,update_rate=10,lazy_query_ms=4.0,packet_query_ms=.02,maintenance_ms=.8); assert mode=='LAZY' and net<0
    mode,_=pp.choose_materialization_mode(read_rate=1,update_rate=1,lazy_query_ms=1.0,packet_query_ms=0.0,maintenance_ms=1.0); assert mode=='HYBRID'

if __name__=='__main__':
    tests=[test_packet_is_deterministic_and_hot_readable,test_targeted_invalidation_only_hits_dependency_closure,test_graph_activation_never_creates_authority,test_candidate_retirement_is_dependency_targeted,test_logical_candidate_versioning_and_epoch_guard,test_family_factorization_and_freshness_gate,test_restart_and_rollback_preserve_last_coherent_packet,test_atomic_publication_reader_sees_old_then_new_epoch,test_adaptive_materialization_policy]
    for t in tests: t()
    print(f'PASS {len(tests)} tests')
