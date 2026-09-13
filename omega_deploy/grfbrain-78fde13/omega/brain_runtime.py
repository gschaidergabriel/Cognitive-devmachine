from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time
from typing import Any

from .grf_emergence import BrainCpuBudget, GRFEmergenceField, GRFParameters


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class BrainRuntime:
    def __init__(self, runtime_root: Path, *, target_cpu: float = 0.20, hard_ceiling: float = 0.24, units: int = 768, groups: int = 16, fanout: int = 6, batch_steps: int = 8, emit_seconds: float = 30.0, status_seconds: float = 1.0, probe_steps: int = 96) -> None:
        self.root = runtime_root
        self.brain_root = runtime_root / "brain"
        self.status_path = self.brain_root / "STATUS.json"
        self.receipt_dir = self.brain_root / "receipts"
        self.cortex_inbox = runtime_root / "cortex_inbox"
        self.brain_root.mkdir(parents=True, exist_ok=True)
        self.receipt_dir.mkdir(parents=True, exist_ok=True)
        self.cortex_inbox.mkdir(parents=True, exist_ok=True)
        params = GRFParameters(units=units, groups=groups, fanout=fanout)
        self.field = GRFEmergenceField(seed=0x0F2A7, params=params)
        self.cpu = BrainCpuBudget(target_cpu, hard_ceiling=hard_ceiling)
        self.batch_steps = max(1, min(256, int(batch_steps)))
        self.emit_seconds = max(5.0, float(emit_seconds))
        self.status_seconds = max(0.5, float(status_seconds))
        self.probe_steps = max(16, int(probe_steps))
        self.stop = False
        self.last_emit = 0.0
        self.last_status = 0.0
        self.last_stimulus_digest = ""
        self.last_regulation = "INIT"
        self.last_emitted_event_id: str | None = None

    def _source_surface(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name, path in (("cortex", self.root / "cortex_state" / "STATE.json"),("grid", self.root / "STATUS.json"),("supervisor", self.root / "SUPERVISOR_STATUS.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict): continue
                if name == "cortex":
                    data = {"state_digest":data.get("state_digest"),"last_meta_order":data.get("last_meta_order"),"history_size":data.get("history_size"),"atom_roles":sorted((data.get("atoms") or {}).keys())[:64] if isinstance(data.get("atoms"),dict) else []}
                elif name == "grid":
                    data = {"frame_id":data.get("frame_id"),"selected_cell":(data.get("selected") or {}).get("cell_id") if isinstance(data.get("selected"),dict) else None,"cortex":data.get("cortex")}
                elif name == "supervisor":
                    data = {"updated_at":data.get("updated_at"),"alive_children":sorted(k for k,v in (data.get("children") or {}).items() if isinstance(v,dict) and v.get("alive") is True)}
                out[name]=data
            except (OSError,json.JSONDecodeError): continue
        return out

    def stimulus_digest(self) -> str:
        surface=self._source_surface()
        return canonical_digest(surface) if surface else hashlib.sha256(b"OMEGA-GRF-IDLE").hexdigest()

    def _emit_cortex_event(self, snapshot: dict[str, Any]) -> str:
        payload={"grf":snapshot["grf"],"macrostate":snapshot["macrostate"],"metrics":snapshot["metrics"],"parameters":snapshot["parameters"],"cpu_budget":self.cpu.status(),"regulation_action":self.last_regulation,"epistemic_scope":"INTERNAL_DYNAMICS","proposal_ready":True,"replace_key":"brain.grf.latest"}
        event_id="brain_"+canonical_digest({"step":self.field.causal_step,"payload":payload})[:24]
        event={"schema":"OMEGA_CORTEX_EVENT/v1","event_id":event_id,"kind":"brain.grf_emergence","causal_id":f"brain-step-{self.field.causal_step}","meta_order":self.field.causal_step,"evidence_class":"SIMULATED","source":"omega.brain.grf","payload":payload,"provenance":{"stimulus_digest":self.last_stimulus_digest,"grf_field_schema":snapshot["schema"],"controller":"GRF_EDC_REVERSE_ENGINEERED/v1","layer_sealed":False}}
        atomic_json(self.cortex_inbox/f"{event_id}.json",event); self.last_emitted_event_id=event_id; return event_id

    def _status(self,snapshot:dict[str,Any])->dict[str,Any]:
        return {"schema":"OMEGA_GRF_BRAIN_STATUS/v1","updated_at_unix":time.time(),"pid":os.getpid(),"grf_field":snapshot,"cpu_budget":self.cpu.status(),"batch_steps":self.batch_steps,"probe_steps":self.probe_steps,"regulation_action":self.last_regulation,"stimulus_digest":self.last_stimulus_digest,"last_emitted_event_id":self.last_emitted_event_id,"one_grid_only":True,"truth_authority":False,"effect_authority":False,"layer_seal_authority":False}

    def cycle(self, *, pace: bool = True) -> dict[str, Any]:
        batch_wall=time.monotonic(); batch_cpu=time.process_time(); self.last_stimulus_digest=self.stimulus_digest()
        for _ in range(self.batch_steps):
            self.field.step(self.last_stimulus_digest)
            if self.field.causal_step % self.probe_steps == 0:
                self.field.perturbation_probe(self.last_stimulus_digest); self.last_regulation=self.field.regulate(self.field.metrics())
        snapshot=self.field.snapshot(); now_m=time.monotonic()
        if now_m-self.last_emit>=self.emit_seconds:
            event_id=self._emit_cortex_event(snapshot)
            receipt={"schema":"OMEGA_GRF_BRAIN_EMISSION_RECEIPT/v1","event_id":event_id,"causal_step":self.field.causal_step,"metrics":snapshot["metrics"],"cpu_budget":self.cpu.status(),"layer_sealed":False,"canonical_credit_minted":0}
            atomic_json(self.receipt_dir/f"{event_id}.json",receipt); self.last_emit=now_m
        if now_m-self.last_status>=self.status_seconds:
            atomic_json(self.status_path,self._status(snapshot)); self.last_status=now_m
        sleep_for=self.cpu.pace(batch_wall,batch_cpu)
        if pace and sleep_for>0: time.sleep(sleep_for)
        return snapshot

    def run(self)->int:
        signal.signal(signal.SIGTERM,lambda *_:setattr(self,"stop",True)); signal.signal(signal.SIGINT,lambda *_:setattr(self,"stop",True))
        while not self.stop: self.cycle(pace=True)
        atomic_json(self.status_path,{**self._status(self.field.snapshot()),"state":"STOPPED"}); return 0


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--runtime-root",default=os.getenv("OMEGA_RUNTIME_ROOT","/workspace/omega_runtime/state")); ap.add_argument("--target-cpu",type=float,default=float(os.getenv("OMEGA_BRAIN_CPU_TARGET","0.20"))); ap.add_argument("--hard-ceiling",type=float,default=float(os.getenv("OMEGA_BRAIN_CPU_HARD_CEILING","0.24"))); ap.add_argument("--units",type=int,default=int(os.getenv("OMEGA_BRAIN_UNITS","768"))); ap.add_argument("--groups",type=int,default=int(os.getenv("OMEGA_BRAIN_GROUPS","16"))); ap.add_argument("--fanout",type=int,default=int(os.getenv("OMEGA_BRAIN_FANOUT","6"))); ap.add_argument("--batch-steps",type=int,default=int(os.getenv("OMEGA_BRAIN_BATCH_STEPS","8"))); ap.add_argument("--probe-steps",type=int,default=int(os.getenv("OMEGA_BRAIN_PROBE_STEPS","96"))); ap.add_argument("--emit-seconds",type=float,default=float(os.getenv("OMEGA_BRAIN_EMIT_SECONDS","30"))); ap.add_argument("--once",action="store_true"); a=ap.parse_args()
    rt=BrainRuntime(Path(a.runtime_root),target_cpu=a.target_cpu,hard_ceiling=a.hard_ceiling,units=a.units,groups=a.groups,fanout=a.fanout,batch_steps=a.batch_steps,emit_seconds=a.emit_seconds,probe_steps=a.probe_steps)
    if a.once:
        for _ in range(max(1,(a.probe_steps*2)//max(1,a.batch_steps))): rt.cycle(pace=False)
        atomic_json(rt.status_path,rt._status(rt.field.snapshot())); print(json.dumps(rt._status(rt.field.snapshot()),sort_keys=True)); return 0
    return rt.run()


if __name__=="__main__": raise SystemExit(main())
