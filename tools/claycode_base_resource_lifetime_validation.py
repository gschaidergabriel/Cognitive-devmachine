#!/usr/bin/env python3
"""Executable resource lifetime / generation / ABA validation for ClayCode BASE."""
from __future__ import annotations
import json,tempfile
from pathlib import Path
from claycode_base_runtime_gateway import RuntimeGateway,ResourceHandle,StaleResource,CapabilityDenied,VersionedCell
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research_entity/claycode/autonomous/BASE_RESOURCE_LIFETIME_RECEIPT.json'
def main()->int:
 checks=[]
 def ck(n,v,d=None):checks.append({'name':n,'pass':bool(v),'detail':d})
 def reject(n,fn,t):
  try:fn();ck(n,False,'unexpected_accept')
  except t as e:ck(n,True,str(e))
 with tempfile.TemporaryDirectory(prefix='clay_resource_lifetime_') as td:
  rt=RuntimeGateway(td);open_cap=rt.grant('db.open','*');exec_cap=rt.grant('db.exec','*')
  h1=rt.sqlite_open(open_cap,'state.db');rt.sqlite_exec(exec_cap,h1,'CREATE TABLE IF NOT EXISTS t(k INTEGER)',());rt.close(h1)
  reject('use_after_close_rejected',lambda:rt.sqlite_exec(exec_cap,h1,'SELECT * FROM t',()),StaleResource)
  h2=rt.sqlite_open(open_cap,'state.db');ck('slot_reuse_generation_increments',h2.slot==h1.slot and h2.generation==h1.generation+1,{'old':[h1.slot,h1.generation],'new':[h2.slot,h2.generation]})
  reject('stale_handle_after_slot_reuse_rejected',lambda:rt.sqlite_exec(exec_cap,h1,'SELECT * FROM t',()),StaleResource)
  forged=ResourceHandle(h2._issuer,h2.slot,h2.generation+99,h2.kind);reject('forged_generation_rejected',lambda:rt.sqlite_exec(exec_cap,forged,'SELECT * FROM t',()),StaleResource)
  other=RuntimeGateway(Path(td)/'other');foreign=other.sqlite_open(other.grant('db.open','*'),'other.db');reject('cross_runtime_resource_rejected',lambda:rt.sqlite_exec(exec_cap,foreign,'SELECT 1',()),StaleResource)
  rt.close(h2);reject('double_close_rejected',lambda:rt.close(h2),StaleResource)
  cell=VersionedCell('A');v,ver=cell.read();ok1,_=cell.compare_exchange(v,ver,'B');v2,ver2=cell.read();ok2,_=cell.compare_exchange(v2,ver2,'A');stale,_=cell.compare_exchange('A',ver,'C');ck('versioned_cas_aba_rejected',ok1 and ok2 and not stale)
  # A resource handle never authorizes an effect: a structurally unrelated object is not a capability.
  reject('resource_handle_not_capability',lambda:rt.file_read_text(h1,'x'),CapabilityDenied)
 failures=[x['name'] for x in checks if not x['pass']];report={'schema_version':'1.0','experiment':'ClayCode BASE generation-bound resource lifetime and ABA validation','checks':checks,'passed':len(checks)-len(failures),'total':len(checks),'failures':failures,'pass':not failures,'supports':['CC-WP-07-RUNTIME-ABI-FFI','CC-WP-09-CONCURRENCY-MEMORY'],'authority_invariant':'resource identity != capability authority','scope_guard':'Execution host is recorded by the enclosing target gate; standalone hosted execution is proxy evidence only.'};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'pass':report['pass'],'failures':failures}));return 0 if report['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
