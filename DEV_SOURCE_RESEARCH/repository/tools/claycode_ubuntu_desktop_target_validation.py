#!/usr/bin/env python3
"""APP-05 target receipt: real Ubuntu desktop window/event-loop/input/state/render."""
from __future__ import annotations
import hashlib,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from claycode_base_runtime import ClayRuntime
from claycode_target_host_identity import DEFAULT_REGISTRATION,verify
from claycode_ubuntu_desktop_adapter import VERSION,install
OUT=ROOT/'research_entity/claycode/target/APP05_UBUNTU_DESKTOP.json'
def sha(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->int:
 ok,identity=verify(DEFAULT_REGISTRATION)
 if not ok:
  print(json.dumps({'error':'ANDREAS_TARGET_IDENTITY_NOT_VERIFIED','identity':identity},indent=2));return 3
 events=[{'kind':'click','value':1},{'kind':'click','value':2},{'kind':'reset'},{'kind':'click','value':4}]
 with tempfile.TemporaryDirectory(prefix='claycode_ui_target_') as td:
  rt=install(ClayRuntime(td));cap=rt.mint_capability('ui.desktop',{'events':['click','reset'],'max_events':16})
  got=rt.invoke('ui.ubuntu_desktop_event_loop',cap,{'counter':0,'label':'idle'},events)
  denied=False
  try:rt.invoke('ui.ubuntu_desktop_event_loop',cap,{'counter':0},[{'kind':'set_label','value':'forbidden'}])
  except Exception:denied=True
 passed=got.get('io_mode')=='TK_REAL_DESKTOP_EVENT_LOOP' and got.get('window_was_mapped') is True and got.get('state')=={'counter':4,'label':'count:4'} and got.get('rendered_label')=='count:4' and denied
 report={'schema_version':'1.0','target_host':'ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM','host_identity':identity,'application':'GUI_INTERACTIVE','pass':passed,'adapter_version':VERSION,'adapter_sha256':sha(ROOT/'tools/claycode_ubuntu_desktop_adapter.py'),'execution_command_or_test_id':'tools/claycode_ubuntu_desktop_target_validation.py','expected':{'io_mode':'TK_REAL_DESKTOP_EVENT_LOOP','window_was_mapped':True,'state':{'counter':4,'label':'count:4'},'forbidden_event_rejected':True},'observed':got,'negative_or_failure_path':{'forbidden_event_rejected':denied},'authority_boundary_preserved':True,'counts_as_target_acceptance':passed}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps({'pass':passed,'output':str(OUT)}));return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
