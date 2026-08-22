from __future__ import annotations
import hashlib, json, sqlite3, sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
TOOLS=ROOT/'tools'
sys.path.insert(0,str(TOOLS))
import claycode_structured_backend as clay
from clay_profile_pipeline_runtime import ProfilePipelineRuntime, execute_source
SRC_PATH=Path(__file__).with_name('BLOGPOST_ENTITY.clay')
SRC=SRC_PATH.read_text()

def make_source_db(path:Path):
    db=sqlite3.connect(path); db.executescript("""
    CREATE TABLE source_a(id TEXT PRIMARY KEY,status TEXT,note TEXT);
    CREATE TABLE source_b(id TEXT PRIMARY KEY,value REAL,note TEXT);
    INSERT INTO source_a VALUES('a1','PASS','alpha evidence');
    INSERT INTO source_b VALUES('b1',0.8,'beta evidence');
    """); db.commit(); db.close()

def contract(prefix='a'):
    if prefix=='a':
        return {'title_field':'title','intro_field':'intro','sections_field':'sections','section_text_field':'text','section_evidence_field':'evidence','section_claims_field':'claims','continuity_field':'thread','autobiographical_hypotheses_field':'hypotheses','longitudinal_self_report_field':'self_report'}
    return {'title_field':'heading','intro_field':'lead','sections_field':'blocks','section_text_field':'body','section_evidence_field':'refs','section_claims_field':'state','continuity_field':'carry','autobiographical_hypotheses_field':'open_questions','longitudinal_self_report_field':'report'}

def profile_a():
    return {'schema':'clay-pipeline-profile/v2','profile_id':'profile_a','inference':{'kind':'mock','model':'model-a','secret_names':[]},
      'personality':{'system_prompt':'Warm first-person workshop diary.','public_style':'German.','output_contract':contract('a')},
      'sources':[{'kind':'alpha','adapter':'sqlite_query','required_for_quiet':True,'db':'source','query':'SELECT id AS source_id,status,note FROM source_a ORDER BY id','id_field':'source_id','evidence_prefix':'alpha:'}],
      'canonical_probes':[],
      'state_metrics':[{'name':'satisfaction','evidence_ref':'state:satisfaction','unknown_if':{'op':'not','arg':{'ref':'sensors.alpha.ok'}},'value':{'op':'clamp01','arg':{'op':'div','a':{'count_where':{'ref':'sources.alpha.rows','field':'status','in':['PASS']}},'b':1.0}}},{'name':'locality_pressure','evidence_ref':'state:locality_pressure','status':'UNKNOWN','value':0.0}],
      'gate':{'require_hash_echo':True,'require_evidence_per_section':True,'max_claim_overshoot':0.05,'leak_patterns':['PRIVATE_ALPHA']}}

def profile_b():
    return {'schema':'clay-pipeline-profile/v2','profile_id':'profile_b','inference':{'kind':'mock','model':'model-b','secret_names':[]},
      'personality':{'system_prompt':'Dry lab note.','public_style':'English.','output_contract':contract('b')},
      'sources':[{'kind':'beta','adapter':'sqlite_query','required_for_quiet':True,'db':'source','query':'SELECT id AS source_id,value,note FROM source_b ORDER BY id','id_field':'source_id','evidence_prefix':'beta:'}],
      'canonical_probes':[], 'state_metrics':[{'name':'confidence','evidence_ref':'state:confidence','status':'VERIFIED','value':0.8}],
      'gate':{'require_hash_echo':True,'require_evidence_per_section':True,'max_claim_overshoot':0.0,'leak_patterns':['PRIVATE_BETA']}}

def provider(req):
    state=json.loads(req['user']); refs=state['ALLOWED_EVIDENCE_REFS']; ev=[r for r in refs if r.startswith(('alpha:','beta:'))][:1] or (['quiet:verified'] if 'quiet:verified' in refs else refs[:1])
    if req['inference'].get('model')=='model-a':
        return {'canonical_state_hash_seen':state['CANONICAL_STATE_HASH'],'packet_hash_seen':state['PACKET_HASH'],'title':'Werkstattnotiz','intro':'Stand.','sections':[{'text':'Nur Evidenz.','evidence':ev,'claims':{}}],'thread':'weiter','hypotheses':'offen','self_report':{'uncertainty':0.4,'felt_conflict':0.7,'qualia_result':'FAILED','qualia_confidence':0.2}}
    return {'canonical_state_hash_seen':state['CANONICAL_STATE_HASH'],'packet_hash_seen':state['PACKET_HASH'],'heading':'Lab','lead':'Status','blocks':[{'body':'Evidence.','refs':ev,'state':{}}],'carry':'continue','open_questions':'none','report':{}}

def run(tmp_path, profile, study=None, override=provider):
    source_db=tmp_path/'source.db'; entity_db=tmp_path/'entity.db'
    if not source_db.exists(): make_source_db(source_db)
    rt=ProfilePipelineRuntime(root=tmp_path,provider_override=override); rt.apply_profile(str(entity_db),profile)
    if study:rt.apply_study_surface(str(entity_db),study)
    result,_=execute_source(SRC,'run',[str(entity_db),str(source_db),''],rt)
    return result,rt,entity_db

def study_config():
    return {'schema':'generic-study/v1','profile_id':'profile_a','enabled':True,
      'render':{'append_after_public_post':True,'fence':'text','title':'ZERO STATE','sections':['SYSTEM STATE','MODEL SELF-REPORT','AUSWERTUNG'],'max_evaluation_lines':5},
      'canonical_fields':['generation','source_count','sensor_health','quiet_status','satisfaction','locality_pressure'],
      'self_report_object_field':'self_report','self_report_fields':['uncertainty','felt_conflict','qualia_result','qualia_confidence'],
      'forbidden_render_terms':['Gasthaus','Bier','am Tisch'],
      'deterministic_evaluation':[{'kind':'unknown_guard','text':'- UNKNOWN bleibt UNKNOWN; fehlende Werte werden nicht imputiert.'},{'kind':'static','text':'- MODEL SELF-REPORT ist keine kanonische Systemmessung.'}]}

def test_canonical_clay_is_application_neutral_and_parses():
    program=clay.parse(SRC); assert program.module=='clay.entity_pipeline'
    for forbidden in ('zero','mistral','gasthaus','eos_architekt','t_omega','bare metal'): assert forbidden not in SRC.lower()

def test_profile_is_db_resident_and_switch_does_not_reset_state(tmp_path):
    make_source_db(tmp_path/'source.db'); source_hash=hashlib.sha256(SRC.encode()).hexdigest()
    first,_,entity_db=run(tmp_path,profile_a()); assert first['generation']==1 and first['profile_id']=='profile_a'
    second,_,_=run(tmp_path,profile_b()); assert second['generation']==2 and second['profile_id']=='profile_b'
    assert hashlib.sha256(SRC.encode()).hexdigest()==source_hash
    db=sqlite3.connect(entity_db); assert db.execute('select generation from eos_pipeline_state').fetchone()[0]==2
    assert {x[0] for x in db.execute('select profile_id from eos_pipeline_outputs')}=={'profile_a','profile_b'}; db.close()

def test_exactly_once_and_verified_quiet_are_profile_driven(tmp_path):
    make_source_db(tmp_path/'source.db'); first,_,_=run(tmp_path,profile_a()); second,_,_=run(tmp_path,profile_a())
    assert first['source_count']==1 and second['source_count']==0 and second['generation']==2

def test_metrics_are_bound_into_canonical_hash(tmp_path):
    make_source_db(tmp_path/'source.db'); p=profile_a(); p['state_metrics'][0]['value']['arg']['b']=10.0; first,_,_=run(tmp_path,p)
    db=sqlite3.connect(tmp_path/'source.db'); db.execute("insert into source_a values('a2','PASS','more')"); db.execute("insert into source_a values('a3','PASS','more2')"); db.commit(); db.close()
    second,_,_=run(tmp_path,p); assert first['canonical_state_hash']!=second['canonical_state_hash']

def test_unverified_claim_still_fails_without_consumption(tmp_path):
    make_source_db(tmp_path/'source.db'); p=profile_a()
    def bad(req):
        s=json.loads(req['user']); return {'canonical_state_hash_seen':s['CANONICAL_STATE_HASH'],'packet_hash_seen':s['PACKET_HASH'],'title':'x','intro':'x','sections':[{'text':'need local','evidence':['state:locality_pressure'],'claims':{'locality_pressure':0.8}}],'thread':'x','hypotheses':'x','self_report':{}}
    rt=ProfilePipelineRuntime(root=tmp_path,provider_override=bad); rt.apply_profile(str(tmp_path/'entity.db'),p)
    with pytest.raises(clay.StructuredFault): execute_source(SRC,'run',[str(tmp_path/'entity.db'),str(tmp_path/'source.db'),''],rt)
    db=sqlite3.connect(tmp_path/'entity.db'); assert db.execute('select count(*) from eos_pipeline_outputs').fetchone()[0]==0; assert db.execute('select count(*) from eos_pipeline_consumed').fetchone()[0]==0; db.close()

def test_study_state_box_is_pipeline_owned_and_atomic(tmp_path):
    make_source_db(tmp_path/'source.db'); result,_,entity_db=run(tmp_path,profile_a(),study_config())
    assert result['study_recorded'] is True and result['public_suffix'].count('```text')==1
    assert 'SYSTEM STATE' in result['public_suffix'] and 'MODEL SELF-REPORT' in result['public_suffix'] and 'AUSWERTUNG' in result['public_suffix']
    assert 'Gasthaus' not in result['public_suffix'] and 'Bier' not in result['public_suffix']
    db=sqlite3.connect(entity_db); row=db.execute('select study_json,rendered_suffix,generation from eos_pipeline_studies').fetchone(); study=json.loads(row[0])
    assert row[2]==1 and study['system_state']['satisfaction']['value']==1.0 and study['model_self_report']['felt_conflict']==0.7
    assert study['system_state']['locality_pressure']['status']=='UNKNOWN'
    assert db.execute('select count(*) from eos_pipeline_outputs').fetchone()[0]==1 and db.execute('select count(*) from eos_pipeline_consumed').fetchone()[0]==1
    db.close()

def test_bad_self_report_aborts_entire_atomic_commit(tmp_path):
    make_source_db(tmp_path/'source.db')
    def bad_report(req):
        out=provider(req); out['self_report']['uncertainty']=1.7; return out
    entity_db=tmp_path/'entity.db'; rt=ProfilePipelineRuntime(root=tmp_path,provider_override=bad_report); rt.apply_profile(str(entity_db),profile_a()); rt.apply_study_surface(str(entity_db),study_config())
    with pytest.raises(clay.StructuredFault): execute_source(SRC,'run',[str(entity_db),str(tmp_path/'source.db'),''],rt)
    db=sqlite3.connect(entity_db); assert db.execute('select generation from eos_pipeline_state').fetchone()[0]==0
    assert db.execute('select count(*) from eos_pipeline_outputs').fetchone()[0]==0; assert db.execute('select count(*) from eos_pipeline_studies').fetchone()[0]==0; assert db.execute('select count(*) from eos_pipeline_consumed').fetchone()[0]==0; db.close()

def test_local_exec_uses_direct_argv_and_same_gate_commit_path(tmp_path):
    make_source_db(tmp_path/'source.db'); p=profile_a(); p['inference']={'kind':'local_exec','local_model_path':'model.gguf','local_argv_json':['python','runner.py','{{PROMPT_FILE}}'],'max_tokens':100,'temperature':0.1}
    (tmp_path/'model.gguf').write_text('fixture')
    (tmp_path/'runner.py').write_text("import json,sys\ns=open(sys.argv[1]).read()\na=json.loads(s.split('\\n\\n')[-1])\nrefs=a['ALLOWED_EVIDENCE_REFS']; ev=[r for r in refs if r.startswith('alpha:')][:1] or ['quiet:verified']\nprint(json.dumps({'canonical_state_hash_seen':a['CANONICAL_STATE_HASH'],'packet_hash_seen':a['PACKET_HASH'],'title':'local','intro':'ok','sections':[{'text':'ok','evidence':ev,'claims':{}}],'thread':'x','hypotheses':'x','self_report':{}}))\n")
    entity_db=tmp_path/'entity.db'; rt=ProfilePipelineRuntime(root=tmp_path); rt.apply_profile(str(entity_db),p)
    result,_=execute_source(SRC,'run',[str(entity_db),str(tmp_path/'source.db'),''],rt); assert result['inference_kind']=='local_exec' and result['generation']==1
