from __future__ import annotations
import hashlib, json, sqlite3, sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]; TOOLS=ROOT/'tools'
if str(TOOLS) not in sys.path: sys.path.insert(0,str(TOOLS))
import claycode_structured_backend as clay
from clay_profile_pipeline_runtime_v2 import ProfilePipelineRuntime, execute_source
SRC_PATH=Path(__file__).with_name('BLOGPOST_ENTITY.clay'); SRC=SRC_PATH.read_text(encoding='utf-8')

def make_source_db(path:Path):
 db=sqlite3.connect(path); db.execute('CREATE TABLE source_a(id TEXT PRIMARY KEY,status TEXT)'); db.execute("INSERT INTO source_a VALUES('a1','PASS')"); db.commit(); db.close()

def contract(): return {'title_field':'title','intro_field':'intro','sections_field':'sections','section_text_field':'text','section_evidence_field':'evidence','section_claims_field':'claims','continuity_field':'thread','autobiographical_hypotheses_field':'hypotheses','longitudinal_self_report_field':'self_report'}

def profile(pid='a',post=False):
 p={'schema':'clay-pipeline-profile/v2','profile_id':pid,'inference':{'kind':'mock','model':'model-'+pid},'personality':{'system_prompt':'Neutral '+pid,'public_style':'plain','output_contract':contract()},'sources':[{'kind':'alpha','adapter':'sqlite_query','required_for_quiet':True,'db':'source','query':'SELECT id AS source_id,status FROM source_a ORDER BY id','id_field':'source_id','evidence_prefix':'alpha:'}],'canonical_probes':[],'state_metrics':[{'name':'confidence','evidence_ref':'state:confidence','status':'VERIFIED','value':0.8},{'name':'unknown_metric','evidence_ref':'state:unknown_metric','status':'UNKNOWN','value':0.0}],'gate':{'require_hash_echo':True,'require_evidence_per_section':True,'max_claim_overshoot':0.0,'leak_patterns':['TOPSECRET']}}
 if post:p['post_render']={'enabled':True,'kind':'study_state_box','study_schema':'test-study/v1','title':'STATE','fence':'text','labels':{'system':'SYSTEM','self_report':'SELF','evaluation':'EVAL'},'canonical_fields':['generation','source_count','sensor_health','quiet_status','confidence','unknown_metric'],'self_report_field':'self_report','require_self_report':True,'self_report_fields':['felt_conflict','qualia_result','qualia_confidence'],'self_report_schema':{'felt_conflict':{'type':'scale01_or_unknown','required':True},'qualia_result':{'type':'enum','values':['REPORTED','FAILED','UNKNOWN'],'required':True},'qualia_confidence':{'type':'scale01_or_unknown','required':True}},'show_previous_post_delta':True,'epistemic_law':'SYSTEM_MEASUREMENT != MODEL_SELF_REPORT'}
 return p

def provider(req,bad=False):
 s=json.loads(req['user']); refs=[r for r in s['ALLOWED_EVIDENCE_REFS'] if r.startswith('alpha:')] or ['quiet:verified']
 return {'canonical_state_hash_seen':s['CANONICAL_STATE_HASH'],'packet_hash_seen':s['PACKET_HASH'],'title':'t','intro':'i','sections':[{'text':'evidence-bound','evidence':refs[:1],'claims':{}}],'thread':'next','hypotheses':'none','self_report':{'felt_conflict':1.2 if bad else 0.7,'qualia_result':'UNKNOWN','qualia_confidence':0.3}}

def execute(tmp_path:Path,p:dict,bad=False):
 source_db=tmp_path/'source.db'; entity_db=tmp_path/'entity.db'; rt=ProfilePipelineRuntime(root=tmp_path,provider_override=lambda req:provider(req,bad)); rt.apply_profile(str(entity_db),p)
 result,rt=execute_source(SRC,'run',[str(entity_db),str(source_db),''],rt); return result,rt,entity_db

def test_clay_contract_is_current_and_application_neutral():
 prg=clay.parse(SRC); assert prg.module=='clay.entity_pipeline'; assert 'pipeline_profile_read' in SRC and 'inference_generate' in SRC and 'pipeline_post_render' in SRC
 for x in ('zero','mistral','gasthaus','t_omega','bare metal'): assert x not in SRC.lower()

def test_fresh_db_requires_explicit_active_profile(tmp_path):
 rt=ProfilePipelineRuntime(root=tmp_path,provider_override=lambda req:provider(req)); r=rt.effect('pipeline_profile_read',{'entity_db':str(tmp_path/'entity.db')}); assert not r['ok'] and 'NO_ACTIVE_PROFILE' in r['error']

def test_profile_switch_does_not_reset_generation(tmp_path):
 make_source_db(tmp_path/'source.db'); first,_,dbp=execute(tmp_path,profile('a')); assert first['generation']==1
 rt=ProfilePipelineRuntime(root=tmp_path,provider_override=lambda req:provider(req)); applied=rt.apply_profile(str(dbp),profile('b')); assert applied['generation']==1
 second,_=execute_source(SRC,'run',[str(dbp),str(tmp_path/'source.db'),''],rt); assert second['generation']==2 and second['profile_id']=='b'
 db=sqlite3.connect(dbp); assert db.execute('SELECT generation FROM eos_pipeline_state').fetchone()[0]==2; assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'; db.close()

def test_exactly_once_and_verified_quiet(tmp_path):
 make_source_db(tmp_path/'source.db'); a,_,dbp=execute(tmp_path,profile('a')); rt=ProfilePipelineRuntime(root=tmp_path,provider_override=lambda req:provider(req)); b,_=execute_source(SRC,'run',[str(dbp),str(tmp_path/'source.db'),''],rt); assert a['source_count']==1 and b['source_count']==0 and b['generation']==2

def test_unknown_claim_still_fails_closed(tmp_path):
 make_source_db(tmp_path/'source.db'); p=profile('a')
 def bad(req):
  r=provider(req); r['sections'][0]['claims']={'unknown_metric':0.5}; r['sections'][0]['evidence']=['state:unknown_metric']; return r
 rt=ProfilePipelineRuntime(root=tmp_path,provider_override=bad); rt.apply_profile(str(tmp_path/'entity.db'),p)
 with pytest.raises(clay.StructuredFault): execute_source(SRC,'run',[str(tmp_path/'entity.db'),str(tmp_path/'source.db'),''],rt)
 db=sqlite3.connect(tmp_path/'entity.db'); assert db.execute('SELECT COUNT(*) FROM eos_pipeline_consumed').fetchone()[0]==0; db.close()

def test_post_render_is_atomic_and_machine_readable(tmp_path):
 make_source_db(tmp_path/'source.db'); r,_,dbp=execute(tmp_path,profile('a',True)); assert r['study_enabled'] is True and '```text' in r['public_append_text']
 db=sqlite3.connect(dbp); row=db.execute('SELECT study_json,rendered_text FROM eos_pipeline_studies').fetchone(); study=json.loads(row[0]); assert study['model_self_report']['felt_conflict']==0.7; assert 'unknown_metric' in study['evaluation']['unknown_system_fields']; assert db.execute('SELECT COUNT(*) FROM eos_pipeline_consumed').fetchone()[0]==1; assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'; db.close()

def test_bad_self_report_consumes_nothing(tmp_path):
 make_source_db(tmp_path/'source.db'); p=profile('a',True); rt=ProfilePipelineRuntime(root=tmp_path,provider_override=lambda req:provider(req,True)); rt.apply_profile(str(tmp_path/'entity.db'),p)
 with pytest.raises(clay.StructuredFault): execute_source(SRC,'run',[str(tmp_path/'entity.db'),str(tmp_path/'source.db'),''],rt)
 db=sqlite3.connect(tmp_path/'entity.db'); assert db.execute('SELECT generation FROM eos_pipeline_state').fetchone()[0]==0; assert db.execute('SELECT COUNT(*) FROM eos_pipeline_consumed').fetchone()[0]==0; assert db.execute('SELECT COUNT(*) FROM eos_pipeline_studies').fetchone()[0]==0; db.close()
