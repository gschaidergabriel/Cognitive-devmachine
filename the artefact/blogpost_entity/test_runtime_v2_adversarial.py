from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; TOOLS=ROOT/'tools'
if str(TOOLS) not in sys.path: sys.path.insert(0,str(TOOLS))
from clay_profile_pipeline_runtime_v2 import ProfilePipelineRuntime
from test_blogpost_entity import make_source_db, profile, provider

def prepare(rt,entity_db,source_db):
 p=rt.effect('pipeline_profile_read',{'entity_db':str(entity_db)})['profile']; rt.effect('pipeline_init',{'entity_db':str(entity_db)}); prev=rt.effect('pipeline_state_read',{'entity_db':str(entity_db)}); col=rt.effect('pipeline_collect',{'entity_db':str(entity_db),'source_db':str(source_db),'profile':p,'previous':prev,'data':{}}); comp=rt.effect('pipeline_compile',{'entity_db':str(entity_db),'source_db':str(source_db),'profile':p,'previous':prev,'data':col}); prompt=rt.effect('pipeline_build_prompt',{'entity_db':str(entity_db),'source_db':str(source_db),'profile':p,'previous':prev,'data':comp}); gen=rt.effect('inference_generate',{'inference':p['inference'],'system':prompt['system'],'user':prompt['user'],'secret_file':''}); gate=rt.effect('pipeline_gate',{'entity_db':str(entity_db),'profile':p,'previous':prev,'data':{'generated':gen,'compiled':comp,'prompt':prompt}}); return p,prev,col,comp,gen,gate

def test_mid_run_profile_change_fails_commit_closed(tmp_path):
 source=tmp_path/'source.db'; entity=tmp_path/'entity.db'; make_source_db(source); rt=ProfilePipelineRuntime(root=tmp_path,provider_override=lambda req:provider(req)); rt.apply_profile(str(entity),profile('same',True)); p,prev,col,comp,gen,gate=prepare(rt,entity,source); post=rt.effect('pipeline_post_render',{'entity_db':str(entity),'profile':p,'previous':prev,'data':{'generated':gen,'compiled':comp,'collected':col,'gated':gate}}); changed=profile('same',True); changed['personality']['system_prompt']='changed while old run was active'; rt.apply_profile(str(entity),changed); commit=rt.effect('pipeline_commit',{'entity_db':str(entity),'profile':p,'previous':prev,'data':{'generated':gen,'compiled':comp,'collected':col,'gated':gate,'post_render':post}}); assert not commit['ok'] and 'STALE_PROFILE' in commit['error']; db=sqlite3.connect(entity); assert db.execute('SELECT generation FROM eos_pipeline_state').fetchone()[0]==0; assert db.execute('SELECT COUNT(*) FROM eos_pipeline_consumed').fetchone()[0]==0; db.close()

def test_self_report_leak_cannot_reach_study_or_commit(tmp_path):
 source=tmp_path/'source.db'; entity=tmp_path/'entity.db'; make_source_db(source); p=profile('leak',True); p['gate']['leak_patterns']=['TOPSECRET']
 def leaking(req):
  out=provider(req); out['self_report']['felt_conflict']='TOPSECRET'; return out
 rt=ProfilePipelineRuntime(root=tmp_path,provider_override=leaking); rt.apply_profile(str(entity),p); p,prev,col,comp,gen,gate=prepare(rt,entity,source)
 if gate['ok']:
  post=rt.effect('pipeline_post_render',{'entity_db':str(entity),'profile':p,'previous':prev,'data':{'generated':gen,'compiled':comp,'collected':col,'gated':gate}}); assert not post['ok']
 db=sqlite3.connect(entity); assert db.execute('SELECT generation FROM eos_pipeline_state').fetchone()[0]==0; assert db.execute('SELECT COUNT(*) FROM eos_pipeline_consumed').fetchone()[0]==0; assert db.execute('SELECT COUNT(*) FROM eos_pipeline_studies').fetchone()[0]==0; db.close()
