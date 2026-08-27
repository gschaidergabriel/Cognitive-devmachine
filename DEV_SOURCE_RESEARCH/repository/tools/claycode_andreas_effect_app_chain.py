#!/usr/bin/env python3
"""Run and attest the six Clay-source effectful app chains on the registered Andreas host."""
from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from claycode_target_host_identity import verify,DEFAULT_REGISTRATION,TARGET_HOST
SOURCE=ROOT/'research_entity/claycode/autonomous/BASE_EFFECT_APPLICATIONS_V2_RECEIPT.json'
OUT=ROOT/'research_entity/claycode/target_receipts/ANDREAS_UBUNTU_EFFECT_APP_CHAIN.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->int:
 ok,host=verify(DEFAULT_REGISTRATION)
 if not ok:print(json.dumps({'error':'TARGET_HOST_IDENTITY_NOT_VERIFIED','details':host}));return 3
 head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,text=True,capture_output=True,check=False).stdout.strip()
 cp=subprocess.run([sys.executable,'tools/claycode_base_effect_apps_v2.py'],cwd=ROOT,text=True,capture_output=True,check=False)
 if not SOURCE.exists():print(json.dumps({'error':'EFFECT_APP_RECEIPT_MISSING','returncode':cp.returncode,'stderr':cp.stderr[-2000:]}));return 2
 d=json.loads(SOURCE.read_text(encoding='utf-8'))
 rows={r['app_id']:r for r in d.get('rows',[])}
 required={'HTTP_WEBSITE','DB_SERVICE','CONCURRENT_SERVICE','GUI_INTERACTIVE','GPU_ML_NUMERICAL','SYSTEM_EFFECT_SANDBOX'}
 passed=cp.returncode==0 and d.get('pass') is True and required==set(rows) and all(rows[x].get('pass') is True for x in required)
 report={'schema_version':'1.0','target_host':TARGET_HOST,'target_host_verified':True,'host_fingerprint':host.get('host_fingerprint',{}),'git_head':head,'runner':'tools/claycode_base_effect_apps_v2.py','runner_returncode':cp.returncode,'source_receipt':str(SOURCE.relative_to(ROOT)),'source_receipt_sha256':sha(SOURCE),'applications':rows,'required':sorted(required),'pass':passed,'target_execution_attested':passed,'promotion_performed':False,'authority_invariant':'model output != execution authority','stdout_tail':cp.stdout[-2000:],'stderr_tail':cp.stderr[-2000:]}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+'\n');print(json.dumps({'pass':passed,'git_head':head,'output':str(OUT.relative_to(ROOT))}));return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
