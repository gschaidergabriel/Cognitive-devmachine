from __future__ import annotations

import dataclasses
import math
from typing import Any

from .grf_emergence import GRFEmergenceField, GRFParameters, clamp


@dataclasses.dataclass(frozen=True)
class CandidateScore:
    name: str
    score: float
    closure: float
    reproducibility: float
    interaction: float
    shuffled_difference: float
    richness: float
    parameters: dict[str, Any]


@dataclasses.dataclass(frozen=True)
class OptimizeResult:
    action: str
    accepted: bool
    baseline: CandidateScore
    selected: CandidateScore


def _rms(a: list[float], b: list[float]) -> float:
    if not a or len(a) != len(b):
        return 0.0
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def _code(xs: list[float]) -> int:
    out = 0
    for i, x in enumerate(xs[:16]):
        if x >= 0.0:
            out |= 1 << i
    return out


def _variants(base: GRFParameters) -> list[tuple[str, GRFParameters]]:
    axes=(("recurrent_gain",0.045),("macro_feedback",0.025),("inhibition",0.025),("nonlinear_gain",0.012),("input_gain",0.018))
    out=[("CURRENT",dataclasses.replace(base))]
    for field_name,delta in axes:
        for sign,label in ((1.0,"UP"),(-1.0,"DOWN")):
            p=dataclasses.replace(base); setattr(p,field_name,float(getattr(p,field_name))+sign*delta); p.clamp_inplace(); out.append((f"{field_name}:{label}",p))
    return out


def score_candidate(field: GRFEmergenceField, params: GRFParameters, stimulus_digest: str, *, horizon: int = 6) -> CandidateScore:
    original=field.params; field.params=params
    try:
        stimulus=field._stimulus(stimulus_digest); a=list(field.state); b=list(field.state); shuffled=list(field.state); ablated=list(field.state)
        for k in range(max(1,params.units//64)):
            idx=int((field.seed+field.causal_step*1315423911+k*2654435761)%params.units); direction=-1.0 if ((idx+field.causal_step+k)&1) else 1.0; b[idx]=clamp(b[idx]+direction*params.perturbation_scale,-1.0,1.0)
        macro_path=[field._macro(a)]
        for _ in range(max(3,int(horizon))):
            a=field._step_state(a,stimulus); b=field._step_state(b,stimulus); shuffled=field._step_state(shuffled,stimulus,shuffle=True); ablated=field._step_state(ablated,stimulus,ablate_recurrence=True); macro_path.append(field._macro(a))
        micro_div=_rms(a,b); ma=field._macro(a); mb=field._macro(b); macro_div=_rms(ma,mb); repro=0.0 if micro_div<=1e-12 else clamp(1.0-macro_div/micro_div,0.0,1.0)
        interaction=clamp(_rms(ma,field._macro(ablated))/0.30,0.0,1.0); shuffled_difference=clamp(_rms(ma,field._macro(shuffled))/0.30,0.0,1.0)
        codes=[_code(x) for x in macro_path]; switching=sum(x!=y for x,y in zip(codes,codes[1:]))/max(1,len(codes)-1); switch_quality=math.exp(-2.2*abs(switching-0.42))
        motion=sum(_rms(x,y) for x,y in zip(macro_path,macro_path[1:]))/max(1,len(macro_path)-1); motion_quality=math.exp(-3.0*abs(min(1.0,motion/0.25)-0.48)); richness=clamp(math.sqrt(switch_quality*motion_quality),0.0,1.0)
        d=[macro_path[-2][i]-macro_path[-3][i] for i in range(len(ma))]; pred=[macro_path[-2][i]+d[i] for i in range(len(ma))]; closure=1.0/(1.0+3.0*_rms(pred,macro_path[-1]))
        components=[closure,repro,interaction,shuffled_difference,richness]; score=len(components)/sum(1.0/max(1e-6,x) for x in components)
        return CandidateScore("",score,closure,repro,interaction,shuffled_difference,richness,dataclasses.asdict(params))
    finally:
        field.params=original


class GRFRegimeOptimizer:
    def __init__(self, *, horizon: int = 6, min_improvement: float = 0.015) -> None:
        self.horizon=max(3,min(12,int(horizon))); self.min_improvement=clamp(float(min_improvement),0.001,0.20); self.last_result:OptimizeResult|None=None
    @staticmethod
    def _safe(candidate: CandidateScore, baseline: CandidateScore) -> bool:
        axes=("closure","reproducibility","interaction","shuffled_difference","richness"); severe=0; improved=0
        for axis in axes:
            c=float(getattr(candidate,axis)); b=float(getattr(baseline,axis)); severe+=int(c+0.08<b); improved+=int(c>b+0.01)
        return severe==0 and improved>=2
    def optimize(self, field: GRFEmergenceField, stimulus_digest: str) -> OptimizeResult:
        scores=[]
        for name,params in _variants(field.params):
            s=score_candidate(field,params,stimulus_digest,horizon=self.horizon); scores.append(dataclasses.replace(s,name=name))
        baseline=scores[0]; eligible=[x for x in scores[1:] if x.score>=baseline.score+self.min_improvement and self._safe(x,baseline)]; selected=max(eligible,key=lambda x:(x.score,x.name),default=baseline); accepted=selected.name!="CURRENT"
        if accepted: field.params=GRFParameters(**selected.parameters); field.params.clamp_inplace()
        result=OptimizeResult(action=f"SHADOW_ACCEPT:{selected.name}" if accepted else "SHADOW_HOLD",accepted=accepted,baseline=baseline,selected=selected); self.last_result=result; return result
