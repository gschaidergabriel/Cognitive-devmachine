#!/usr/bin/env python3
"""Single evidence-gated status writer for ClayCode BASE release workspace.

preaudit: a valid strict Andreas-Ubuntu receipt may promote WP02..WP13 and the ten app
rows into the release workspace. finalize: only a passing release audit plus generated
manifest may promote WP14 and the two release gates. No proxy receipt is accepted.
"""
from __future__ import annotations
import argparse,hashlib,json,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from claycode_base_release_audit import REQ_APPS,REQ_WP,validate_target
WORKSPACE=ROOT/'research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json'
CONTRACT=ROOT/'research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json'
AUDIT=ROOT/'research_entity/claycode/autonomous/BASE_RELEASE_AUDIT_RECEIPT.json'
MANIFEST=ROOT/'research_entity/claycode/CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json'
PRE=ROOT/'research_entity/claycode/target_receipts/BASE_STRICT_PREAUDIT_PROMOTION_RECEIPT.json'
FINAL=ROOT/'research_entity/claycode/target_receipts/BASE_FINAL_PROMOTION_RECEIPT.json'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic_json(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=p.parent,delete=False) as f:f.write(raw);tmp=Path(f.name)
 tmp.replace(p)
def add_unique(seq,value):
 if value not in seq:seq.append(value)
def strict_path():
 c=load(CONTRACT);return ROOT/c['expected_receipt_path']
def preaudit()->int:
 strict=strict_path()
 if not strict.exists():raise SystemExit('STRICT_TARGET_RECEIPT_MISSING:'+str(strict.relative_to(ROOT)))
 target=load(strict);errors=validate_target(target)
 if errors:print(json.dumps({'promoted':False,'errors':errors}));return 2
 if target.get('overall_pass') is not True:return 2
 ws=load(WORKSPACE);before=sha(WORKSPACE);packages=ws.get('work_packages') or {};promoted=[]
 for name in REQ_WP[1:13]:
  target_row=(target.get('work_packages') or {}).get(name) or {}
  if target_row.get('pass') is not True:raise SystemExit('STRICT_WP_NOT_PASS:'+name)
  row=packages.get(name)
  if not isinstance(row,dict):raise SystemExit('WORKSPACE_WP_MISSING:'+name)
  row['status']='PASS';row['receipt']=str(strict.relative_to(ROOT));row['strict_target_evidence_sha256']=sha(strict);promoted.append(name)
 apps=ws.setdefault('application_acceptance',{});apps['passed']=list(REQ_APPS);apps['target_host']=target.get('target_host');apps['receipt']=str(strict.relative_to(ROOT));apps['receipt_sha256']=sha(strict)
 completed=ws.setdefault('completed_receipts',[]);add_unique(completed,str(strict.relative_to(ROOT)));ws['last_updated']=datetime.now(timezone.utc).date().isoformat();atomic_json(WORKSPACE,ws);after=sha(WORKSPACE)
 rec={'schema_version':'1.0','phase':'PREADUIT','pass':True,'strict_target_receipt':str(strict.relative_to(ROOT)),'strict_target_receipt_sha256':sha(strict),'workspace_sha256_before':before,'workspace_sha256_after':after,'promoted_work_packages':promoted,'promoted_applications':REQ_APPS,'wp14_promoted':False,'authority_rule':'Only strict target receipt can promote WP02..13; proxy evidence is ineligible.'};atomic_json(PRE,rec);print(json.dumps({'promoted':True,'work_packages':len(promoted),'applications':len(REQ_APPS),'workspace_sha256':after}));return 0
def finalize()->int:
 if not AUDIT.exists():raise SystemExit('RELEASE_AUDIT_MISSING')
 if not MANIFEST.exists():raise SystemExit('RELEASE_MANIFEST_MISSING')
 audit=load(AUDIT);manifest=load(MANIFEST)
 errors=[]
 if audit.get('overall_pass') is not True or audit.get('wp14_pass_eligible') is not True or audit.get('release_manifest_created') is not True:errors.append('AUDIT_NOT_PASS_ELIGIBLE')
 if manifest.get('status')!='PASS_ELIGIBLE_PENDING_CANONICAL_PROMOTION':errors.append('MANIFEST_NOT_PENDING_PROMOTION')
 strict=strict_path()
 if not strict.exists():errors.append('STRICT_TARGET_RECEIPT_MISSING')
 else:errors.extend(validate_target(load(strict)))
 if errors:print(json.dumps({'finalized':False,'errors':errors}));return 2
 ws=load(WORKSPACE);before=sha(WORKSPACE)
 for name in REQ_WP[:13]:
  if (ws.get('work_packages',{}).get(name) or {}).get('status')!='PASS':errors.append('WORKSPACE_PREREQ_NOT_PASS:'+name)
 if errors:print(json.dumps({'finalized':False,'errors':errors}));return 2
 wp14=ws['work_packages']['CC-WP-14-BASE-AUDIT'];wp14['status']='PASS';wp14['receipt']=str(AUDIT.relative_to(ROOT));wp14['manifest']=str(MANIFEST.relative_to(ROOT));wp14['audit_sha256']=sha(AUDIT)
 ws['gate_status']='PASS';ws['general_purpose_gate_status']='PASS';ws['status']='BASE_PASS';completed=ws.setdefault('completed_receipts',[]);add_unique(completed,str(AUDIT.relative_to(ROOT)));add_unique(completed,str(MANIFEST.relative_to(ROOT)));ws['last_updated']=datetime.now(timezone.utc).date().isoformat();atomic_json(WORKSPACE,ws);after=sha(WORKSPACE)
 manifest['status']='PASS';manifest['promoted_at']=datetime.now(timezone.utc).isoformat();manifest['workspace_sha256_after_promotion']=after;atomic_json(MANIFEST,manifest)
 rec={'schema_version':'1.0','phase':'FINALIZE','pass':True,'audit_path':str(AUDIT.relative_to(ROOT)),'audit_sha256':sha(AUDIT),'manifest_path':str(MANIFEST.relative_to(ROOT)),'manifest_sha256_after_promotion':sha(MANIFEST),'workspace_sha256_before':before,'workspace_sha256_after':after,'promoted_work_package':'CC-WP-14-BASE-AUDIT','gate_status':'PASS','general_purpose_gate_status':'PASS','automatic_promotion':False,'rule':'Final promotion requires strict target receipt + WP01..13 PASS + release audit PASS + generated manifest.'};atomic_json(FINAL,rec);print(json.dumps({'finalized':True,'workspace_sha256':after,'manifest_sha256':sha(MANIFEST),'all_14_pass':True}));return 0
def main():
 ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['preaudit','finalize']);a=ap.parse_args();return preaudit() if a.phase=='preaudit' else finalize()
if __name__=='__main__':raise SystemExit(main())