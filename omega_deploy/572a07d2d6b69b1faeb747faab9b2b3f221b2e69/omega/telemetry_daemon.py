from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from .alignment import EffectBinding, ExecutorObservation, OutcomeUnknown, dispatch
from .bridge_transport import BridgeOutcomeUnknown, BridgeTarget, GitBranchTransport, command_from_effect
from .policy_kernel import PolicyKernel
from .unified_store import UnifiedStore, digest, now


PROBE_COMMAND = r'''python3 - <<'PY'
import json, os
la=os.getloadavg()[0] if hasattr(os,'getloadavg') else 0.0
cpus=max(1,os.cpu_count() or 1)
mem={}
try:
    for line in open('/proc/meminfo'):
        k,v=line.split(':',1); mem[k]=int(v.strip().split()[0])
except Exception: pass
total=max(1,mem.get('MemTotal',1)); avail=mem.get('MemAvailable',mem.get('MemFree',0))
print(json.dumps({'cpu_load':max(0.0,min(1.0,la/cpus)),'ram_load':max(0.0,min(1.0,1-(avail/total))),'cpu_count':cpus,'load1':la}))
PY'''


def _atomic(path: Path, payload: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8'); os.replace(tmp,path)


class TelemetryDaemon:
    def __init__(self, *, runtime_root: Path, repo_root: Path, db_path: Path, carrier_repo: Path,
                 router_path: Path, policy_path: Path) -> None:
        self.runtime_root=runtime_root; self.repo_root=repo_root
        self.store=UnifiedStore(db_path,repo_root/'schema'); self.policy=PolicyKernel.from_path(policy_path)
        cfg=json.loads(router_path.read_text(encoding='utf-8'))
        self.targets=[]
        for organ in cfg['organs']:
            if organ.get('kind')!='host_frankenstein': continue
            self.targets.append(BridgeTarget(organ_id=str(organ['organ_id']),owner_id=str(organ['owner_id']),machine_id=str(organ['machine_id']),control_branch=str(organ['control_branch']),results_branch=str(organ['results_branch'])))
        self.transport=GitBranchTransport(carrier_repo=carrier_repo,work_root=runtime_root/'telemetry_bridge_git',poll_seconds=2.0)

    def probe(self,target:BridgeTarget)->dict[str,Any]:
        bucket=int(time.time()//60); effect_id=f"effect_telemetry_{target.machine_id}_{bucket}"
        request={'op':'exec','command':PROBE_COMMAND,'cwd':'/tmp','timeout_seconds':30,'receipt_timeout_seconds':120}
        identity=digest({'organ':target.organ_id,'owner':target.owner_id,'machine':target.machine_id,'kind':'telemetry'})
        binding=EffectBinding.prepare(effect_id=effect_id,invocation_id=f'inv_{bucket}_{target.machine_id}',tool_use_id=f'tool_probe_{bucket}_{target.machine_id}',delegation_id=f'deleg_telemetry_{target.machine_id}',child_identity_sha256=identity,request=request,organ_id=target.organ_id,owner_id=target.owner_id,machine_id=target.machine_id)
        gate=self.policy.authorize(binding,request)
        holder={}
        def executor(b:EffectBinding)->ExecutorObservation:
            command=command_from_effect(b.effect_id,target,request)
            receipt,cmd_d,rec_d=self.transport.dispatch(target,command,receipt_timeout=120)
            holder.update(receipt=receipt,command_digest=cmd_d,receipt_digest=rec_d)
            return ExecutorObservation(effect_id=b.effect_id,binding_id=b.binding_id,invocation_id=b.invocation_id,tool_use_id=b.tool_use_id,delegation_id=b.delegation_id,child_identity_sha256=b.child_identity_sha256,request_sha256=b.request_sha256,organ_id=b.organ_id,result_id=str(receipt.get('command_id')),result_sha256=rec_d)
        try:
            res=dispatch(binding,authorize=lambda _b:gate,executor=executor)
        except (OutcomeUnknown,BridgeOutcomeUnknown) as exc:
            telem={'schema':'OMEGA_ORGAN_TELEMETRY/v1','organ_id':target.organ_id,'owner_id':target.owner_id,'machine_id':target.machine_id,'observed_at':now(),'health':'UNKNOWN','bridge_health':0.0,'error':str(exc)}
            _atomic(self.runtime_root/'telemetry'/f"{target.machine_id}.json",telem); self.store.record_telemetry(target.organ_id,telem); return telem
        receipt=holder['receipt']; metrics={}
        try:
            lines=[x for x in str(receipt.get('stdout_tail','')).splitlines() if x.strip()]
            metrics=json.loads(lines[-1]) if lines else {}
        except Exception: metrics={}
        health='GREEN' if receipt.get('status')=='PASS' and 'cpu_load' in metrics and 'ram_load' in metrics else 'UNKNOWN'
        telem={'schema':'OMEGA_ORGAN_TELEMETRY/v1','organ_id':target.organ_id,'owner_id':target.owner_id,'machine_id':target.machine_id,'observed_at':str(receipt.get('finished_at') or now()),'health':health,'cpu_load':metrics.get('cpu_load'),'ram_load':metrics.get('ram_load'),'bridge_health':1.0 if receipt.get('status')=='PASS' else 0.0,'information_gain':0.75,'independence':0.65,'latency_score':0.65,'capabilities':[],'data_domains':[target.owner_id+'-local'],'receipt_id':receipt.get('command_id'),'execution_boundary':receipt.get('execution_boundary')}
        _atomic(self.runtime_root/'telemetry'/f"{target.machine_id}.json",telem); self.store.record_telemetry(target.organ_id,telem)
        self.store.record_observation(source_id=target.organ_id,subject_id=target.organ_id,payload=telem,observed_at=telem['observed_at'],evidence_class='LIVE_READBACK',owner_id=target.owner_id,machine_id=target.machine_id,receipt_id=str(receipt.get('command_id')),authority_rank=90,confidence=1.0 if health=='GREEN' else 0.5)
        self.store.record_effect_receipt(effect_id=effect_id,subject_id=target.organ_id,owner_id=target.owner_id,machine_id=target.machine_id,action_kind='telemetry_probe',request_digest=binding.request_sha256,result_digest=holder.get('receipt_digest'),status=str(receipt.get('status')),requested_at=str(receipt.get('started_at') or telem['observed_at']),completed_at=telem['observed_at'],receipt_locator=str(receipt.get('command_id')),metadata={'policy_decision':gate.decision.value})
        return telem

    def run_once(self)->list[dict[str,Any]]:
        return [self.probe(t) for t in self.targets]


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--runtime-root',default=os.getenv('OMEGA_RUNTIME_ROOT','/workspace/omega_runtime/state')); ap.add_argument('--repo-root',default=os.getenv('OMEGA_REPO_ROOT','/workspace/omega_runtime/current')); ap.add_argument('--db',default=os.getenv('OMEGA_UNIFIED_DB','/workspace/omega_runtime/data/omega_unified.db')); ap.add_argument('--carrier-repo',default=os.getenv('OMEGA_CARRIER_REPO','/workspace/omega_runtime/carrier_repo')); ap.add_argument('--router',default=os.getenv('OMEGA_ROUTER_CONFIG','/workspace/omega_runtime/current/config/organ_router.json')); ap.add_argument('--policy',default=os.getenv('OMEGA_AUTONOMY_POLICY','/workspace/omega_runtime/current/config/autonomy_policy.json')); ap.add_argument('--interval',type=float,default=60.0); ap.add_argument('--once',action='store_true'); a=ap.parse_args()
    d=TelemetryDaemon(runtime_root=Path(a.runtime_root),repo_root=Path(a.repo_root),db_path=Path(a.db),carrier_repo=Path(a.carrier_repo),router_path=Path(a.router),policy_path=Path(a.policy))
    if a.once: print(json.dumps(d.run_once(),indent=2)); return 0
    while True:
        try: d.run_once()
        except Exception as exc:
            _atomic(Path(a.runtime_root)/'telemetry'/'LAST_ERROR.json',{'at':now(),'error':f'{type(exc).__name__}:{exc}'})
        time.sleep(max(15.0,a.interval))

if __name__=='__main__': raise SystemExit(main())
