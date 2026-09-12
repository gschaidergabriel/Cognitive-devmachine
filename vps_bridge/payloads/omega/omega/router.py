from __future__ import annotations

import dataclasses
import datetime as dt
import json
from pathlib import Path
from typing import Any, Iterable

@dataclasses.dataclass(frozen=True)
class OrganTelemetry:
    organ_id: str
    observed_at: str
    health: str = "UNKNOWN"
    capabilities: frozenset[str] = frozenset()
    data_domains: frozenset[str] = frozenset()
    cpu_load: float | None = None
    ram_load: float | None = None
    gpu_load: float | None = None
    bridge_health: float = 1.0
    information_gain: float = 0.5
    independence: float = 0.5
    latency_score: float = 0.5
    def age_seconds(self, now: dt.datetime | None = None) -> float:
        now = now or dt.datetime.now(dt.timezone.utc)
        observed = dt.datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        return max(0.0, (now - observed).total_seconds())
    @property
    def resource_headroom(self) -> float:
        values = [x for x in (self.cpu_load,self.ram_load,self.gpu_load) if x is not None]
        if not values: return 0.5
        return 1.0-max(max(0.0,min(1.0,float(x))) for x in values)

@dataclasses.dataclass(frozen=True)
class TaskRequest:
    task_id: str
    required_capabilities: frozenset[str] = frozenset()
    preferred_data_domains: frozenset[str] = frozenset()
    heavy: bool = False
    high_risk_effect: bool = False
    wants_independent_falsifier: bool = False
    max_organs: int = 1

@dataclasses.dataclass(frozen=True)
class RouteScore:
    organ_id: str
    score: float
    eligible: bool
    reasons: tuple[str,...]

@dataclasses.dataclass(frozen=True)
class RouteDecision:
    task_id: str
    selected_organs: tuple[str,...]
    ranking: tuple[RouteScore,...]
    def as_dict(self)->dict[str,Any]: return dataclasses.asdict(self)

class DynamicOrganRouter:
    def __init__(self, config: dict[str,Any])->None:
        self.config=config; self.organs={o["organ_id"]:o for o in config["organs"]}
        self.weights=config.get("weights",{}); self.max_age=float(config.get("telemetry_max_age_seconds",180)); self.central=str(config.get("central_organ","omega-vps"))
    @classmethod
    def from_path(cls,path:str|Path)->"DynamicOrganRouter": return cls(json.loads(Path(path).read_text(encoding="utf-8")))
    def _score(self,task:TaskRequest,t:OrganTelemetry)->RouteScore:
        cfg=self.organs.get(t.organ_id)
        if not cfg: return RouteScore(t.organ_id,-1e9,False,("unregistered organ",))
        available=set(cfg.get("capabilities",()))|set(t.capabilities); missing=set(task.required_capabilities)-available
        if missing: return RouteScore(t.organ_id,-1e9,False,("missing capabilities: "+",".join(sorted(missing)),))
        if t.health.upper()=="RED": return RouteScore(t.organ_id,-1e9,False,("health RED",))
        external=cfg.get("kind")=="host_frankenstein"
        if task.heavy and external and t.age_seconds()>self.max_age: return RouteScore(t.organ_id,-1e9,False,("stale telemetry for heavy host fanout",))
        fit=1.0 if not task.required_capabilities else len(task.required_capabilities&available)/len(task.required_capabilities)
        locality=0.0 if not task.preferred_data_domains else len(task.preferred_data_domains&set(t.data_domains))/len(task.preferred_data_domains)
        fresh=max(0.0,1.0-min(t.age_seconds(),self.max_age*2)/(self.max_age*2)); risk=1.0 if task.high_risk_effect and external else 0.0
        m={"capability_fit":fit,"data_locality":locality,"state_freshness":fresh,"information_gain":t.information_gain,"independence_for_falsification":t.independence if task.wants_independent_falsifier else 0.0,"compute_availability":t.resource_headroom,"latency":t.latency_score,"bridge_health":t.bridge_health,"host_resource_headroom":t.resource_headroom,"effect_risk":risk,"duplicate_work":0.0}
        score=sum(float(self.weights.get(k,0.0))*float(v) for k,v in m.items())
        return RouteScore(t.organ_id,score,True,tuple(f"{k}={v:.3f}" for k,v in m.items() if abs(float(v))>1e-9))
    def choose(self,task:TaskRequest,telemetry:Iterable[OrganTelemetry])->RouteDecision:
        scores=[self._score(task,t) for t in telemetry]; scores.sort(key=lambda x:(x.eligible,x.score),reverse=True); eligible=[x for x in scores if x.eligible]
        if not eligible: raise RuntimeError(f"no eligible organ for {task.task_id}")
        n=max(1,min(task.max_organs,len(eligible)))
        if task.wants_independent_falsifier and self.config.get("allow_multi_organ_coalitions",False): n=max(n,min(2,len(eligible)))
        return RouteDecision(task.task_id,tuple(x.organ_id for x in eligible[:n]),tuple(scores))
