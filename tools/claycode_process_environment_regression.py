#!/usr/bin/env python3
"""Ensure process.exec children do not inherit unrelated host environment authority."""
from __future__ import annotations
import json,os,tempfile
from pathlib import Path
from claycode_base_runtime import ClayRuntime
ROOT=Path(__file__).resolve().parents[1]
def main()->int:
 env_bin=Path('/usr/bin/env').resolve(strict=True)
 secret='CLAYCODE_TEST_AMBIENT_SECRET';old=os.environ.get(secret);os.environ[secret]='must-not-cross-boundary'
 try:
  with tempfile.TemporaryDirectory(prefix='clay_env_gate_') as td:
   rt=ClayRuntime(td);cap=rt.mint_capability('process.exec',{'programs':[str(env_bin)]})
   row=rt.invoke('process.exec',cap,[str(env_bin)]);lines=set(row['stdout'].splitlines())
   leaked=any(x.startswith(secret+'=') for x in lines)
   suspicious=[name for name in ('GITHUB_TOKEN','GH_TOKEN','AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY','OPENAI_API_KEY') if any(x.startswith(name+'=') for x in lines)]
   report={'schema_version':'1.0','experiment':'ClayCode process child ambient authority isolation','runtime_version':__import__('claycode_base_runtime').RUNTIME_VERSION,'secret_leaked':leaked,'known_credential_names_present':suspicious,'child_environment_lines':sorted(lines),'pass':not leaked and not suspicious}
 finally:
  if old is None:os.environ.pop(secret,None)
  else:os.environ[secret]=old
 out=ROOT/'research_entity/claycode/autonomous/BASE_PROCESS_ENVIRONMENT_REGRESSION_RECEIPT.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'pass':report['pass'],'secret_leaked':leaked,'credential_names_present':suspicious}));return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
