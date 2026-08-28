#!/usr/bin/env python3
import json, pathlib, sqlite3
ROOT=pathlib.Path(__file__).resolve().parent
MANIFEST=ROOT/'SEED_MANIFEST_2026-08-29.json'
DB=ROOT/'pending_research.sqlite'
SCHEMA='''
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS architecture_snapshots(snapshot_id TEXT PRIMARY KEY,created_at_utc TEXT,f2_sha TEXT,research_sha TEXT,status TEXT);
CREATE TABLE IF NOT EXISTS seeds(seed_id TEXT PRIMARY KEY,repo TEXT,url TEXT,hypothesis TEXT,counterhypothesis TEXT,readme_blob_sha TEXT,targets_json TEXT,priority INTEGER,status TEXT,snapshot_id TEXT,created_at_utc TEXT,updated_at_utc TEXT);
CREATE TABLE IF NOT EXISTS hypotheses(hypothesis_id TEXT PRIMARY KEY,seed_id TEXT,statement TEXT,counterhypothesis TEXT,affected_modules_json TEXT,architecture_snapshot_id TEXT,status TEXT,evidence_grade INTEGER,created_at_utc TEXT,updated_at_utc TEXT);
CREATE TABLE IF NOT EXISTS architecture_deltas(delta_id TEXT PRIMARY KEY,snapshot_id TEXT,source_stream TEXT,source_ref TEXT,affected_modules_json TEXT,delta_class TEXT,summary TEXT,impact_on_research TEXT,created_at_utc TEXT);
CREATE TABLE IF NOT EXISTS experiments(experiment_id TEXT PRIMARY KEY,hypothesis_id TEXT,worker_role TEXT,plan TEXT,baseline TEXT,required_measurements_json TEXT,acceptance_rule TEXT,status TEXT,created_at_utc TEXT,updated_at_utc TEXT);
CREATE TABLE IF NOT EXISTS evidence(evidence_id TEXT PRIMARY KEY,hypothesis_id TEXT,source_repo TEXT,source_sha TEXT,artifact_ref TEXT,evidence_type TEXT,direction TEXT,grade INTEGER,summary TEXT,created_at_utc TEXT);
CREATE TABLE IF NOT EXISTS worker_cycles(cycle_slot_id TEXT PRIMARY KEY,cycle_id TEXT,slot INTEGER,role TEXT,status TEXT,claimed_seed_id TEXT,claimed_hypothesis_id TEXT,architecture_snapshot_id TEXT,output_ref TEXT,created_at_utc TEXT,updated_at_utc TEXT);
CREATE TABLE IF NOT EXISTS build_candidates(candidate_id TEXT PRIMARY KEY,hypothesis_id TEXT,status TEXT,source_repo TEXT,source_sha TEXT,source_tree_sha TEXT,license TEXT,integration_class TEXT,target_workpackages_json TEXT,target_modules_json TEXT,package_ref TEXT,trigger4_inbox_ref TEXT,architecture_snapshot_id TEXT,net_benefit_summary TEXT,created_at_utc TEXT,updated_at_utc TEXT);
CREATE TABLE IF NOT EXISTS trigger4_feedback(feedback_id TEXT PRIMARY KEY,candidate_id TEXT,workpackage_id TEXT,vps_run_id TEXT,result_status TEXT,result_ref TEXT,measurements_ref TEXT,root_cause_ref TEXT,created_at_utc TEXT);
'''
ROLES=['ARCHITECTURE_DELTA_FUSER','DISCOVERY_SCOUT','SOURCE_ARCHAEOLOGIST','EXPERIMENTAL_FALSIFIER','INTEGRATION_DISTILLER']
def main():
 m=json.loads(MANIFEST.read_text()); a=m['architecture_snapshot']; ts=m['created_at_utc']; sid=f"ADF-{ts[:10].replace('-','')}-{a['f2_sha_at_seed'][:8]}-{a['research_entity_sha_at_seed'][:8]}"
 db=sqlite3.connect(DB); db.executescript(SCHEMA)
 db.execute('INSERT OR REPLACE INTO architecture_snapshots VALUES(?,?,?,?,?)',(sid,ts,a['f2_sha_at_seed'],a['research_entity_sha_at_seed'],'BOOTSTRAP'))
 for s in m['seeds']:
  url='https://github.com/'+s['repo']; targets=json.dumps(s.get('targets',[]))
  db.execute('''INSERT OR REPLACE INTO seeds VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(s['seed_id'],s['repo'],url,s['hypothesis'],s['counterhypothesis'],s.get('readme_blob_sha'),targets,int(s.get('priority',50)),'PENDING_RESEARCH',sid,ts,ts))
  hid='R6-H-'+s['seed_id'].split('-')[-1]
  db.execute('INSERT OR IGNORE INTO hypotheses VALUES(?,?,?,?,?,?,?,?,?,?)',(hid,s['seed_id'],s['hypothesis'],s['counterhypothesis'],targets,sid,'PENDING_FALSIFICATION',0,ts,ts))
 for i,role in enumerate(ROLES,1):
  slot=f'R6-CYCLE-0001-SLOT-{i}'; db.execute('INSERT OR IGNORE INTO worker_cycles VALUES(?,?,?,?,?,?,?,?,?,?,?)',(slot,'R6-CYCLE-0001',i,role,'OPEN',None,None,sid,None,ts,ts))
 for k,v in {'schema':'FRANKENSTEIN2_TRIGGER6_PENDING_RESEARCH/v1','role':'FULL_PROVENANCE_MIRROR','canonical_repo':'gschaidergabriel/frankenstein-2.0','architecture_fusion_required':'true','trigger4_handoff_required':'true'}.items(): db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',(k,v))
 db.commit(); qc=db.execute('PRAGMA quick_check').fetchone()[0]; db.close()
 if qc!='ok': raise SystemExit(qc)
 print(DB)
if __name__=='__main__': main()
