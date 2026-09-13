from __future__ import annotations

import collections
import dataclasses
import hashlib
import math
import os
import time
from typing import Any, Iterable, Mapping


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _mix64(x: int) -> int:
    x &= (1 << 64) - 1
    x ^= x >> 30
    x = (x * 0xbf58476d1ce4e5b9) & ((1 << 64) - 1)
    x ^= x >> 27
    x = (x * 0x94d049bb133111eb) & ((1 << 64) - 1)
    x ^= x >> 31
    return x & ((1 << 64) - 1)


def _entropy(probs: Iterable[float]) -> float:
    out = 0.0
    for p in probs:
        if p > 0.0:
            out -= p * math.log2(p)
    return out


def normalized_effective_information(transitions: Mapping[int, Mapping[int, int]]) -> float:
    """Observed-TPM EI proxy under a uniform distribution over observed source states.

    Exact intervention-backed EI needs an explicit intervention design. This function
    never upgrades an observational trajectory into causal evidence.
    """
    rows: list[dict[int, float]] = []
    targets: set[int] = set()
    for counts in transitions.values():
        total = sum(max(0, int(v)) for v in counts.values())
        if total <= 0:
            continue
        row = {int(k): max(0, int(v)) / total for k, v in counts.items() if int(v) > 0}
        if row:
            rows.append(row)
            targets.update(row)
    if len(rows) < 2 or len(targets) < 2:
        return 0.0
    inv = 1.0 / len(rows)
    py = {y: 0.0 for y in targets}
    row_h = 0.0
    for row in rows:
        row_h += _entropy(row.values()) * inv
        for y, p in row.items():
            py[y] += p * inv
    ei = max(0.0, _entropy(py.values()) - row_h)
    denom = math.log2(max(2, len(targets)))
    return clamp(ei / denom, 0.0, 1.0)


def mutual_information(xs: list[int], ys: list[int]) -> float:
    if len(xs) != len(ys) or len(xs) < 4:
        return 0.0
    joint = collections.Counter(zip(xs, ys))
    cx = collections.Counter(xs)
    cy = collections.Counter(ys)
    n = float(len(xs))
    mi = 0.0
    for (x, y), c in joint.items():
        pxy = c / n
        px = cx[x] / n
        py = cy[y] / n
        mi += pxy * math.log2(pxy / (px * py))
    return max(0.0, mi)


@dataclasses.dataclass
class GRFParameters:
    units: int = 768
    groups: int = 16
    fanout: int = 6
    self_memory: float = 0.36
    recurrent_gain: float = 1.08
    macro_feedback: float = 0.18
    input_gain: float = 0.22
    inhibition: float = 0.24
    nonlinear_gain: float = 0.16
    perturbation_scale: float = 0.012
    probe_horizon: int = 5

    def clamp_inplace(self) -> None:
        self.units = max(128, min(8192, int(self.units)))
        self.groups = max(4, min(64, int(self.groups)))
        self.groups = min(self.groups, self.units)
        self.fanout = max(2, min(16, int(self.fanout)))
        self.self_memory = clamp(float(self.self_memory), 0.05, 0.85)
        self.recurrent_gain = clamp(float(self.recurrent_gain), 0.20, 2.20)
        self.macro_feedback = clamp(float(self.macro_feedback), 0.0, 0.80)
        self.input_gain = clamp(float(self.input_gain), 0.01, 1.0)
        self.inhibition = clamp(float(self.inhibition), 0.0, 1.20)
        self.nonlinear_gain = clamp(float(self.nonlinear_gain), 0.0, 0.60)
        self.perturbation_scale = clamp(float(self.perturbation_scale), 1e-5, 0.10)
        self.probe_horizon = max(2, min(16, int(self.probe_horizon)))


@dataclasses.dataclass(frozen=True)
class GRFMetrics:
    causal_step: int
    closure_residual: float
    closure_quality: float
    micro_divergence: float
    macro_divergence: float
    macro_reproducibility: float
    micro_ei_proxy: float
    macro_ei_proxy: float
    causal_emergence_proxy: float
    pair_synergy_proxy: float
    macro_entropy: float
    switching_rate: float
    metastability: float
    interaction_sensitivity: float
    shuffle_control_reproducibility: float
    control_advantage: float
    cognitive_temperature: float
    emergence_generation_score: float
    layer_sealed: bool
    evidence_note: str

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class GRFEmergenceField:
    HISTORY = 256

    def __init__(self, *, seed: int = 0xF2A7, params: GRFParameters | None = None) -> None:
        self.seed = int(seed) & ((1 << 64) - 1)
        self.params = params or GRFParameters()
        self.params.clamp_inplace()
        p = self.params
        self.state = [self._initial_state(i) for i in range(p.units)]
        self.neighbors: list[tuple[int, ...]] = []
        self.weights: list[tuple[float, ...]] = []
        for i in range(p.units):
            ns: list[int] = []
            ws: list[float] = []
            for k in range(p.fanout):
                h = _mix64(self.seed ^ (i * 0x9e3779b97f4a7c15) ^ (k * 0xD1B54A32D192ED03))
                j = int(h % p.units)
                if j == i:
                    j = (j + 1 + k) % p.units
                ns.append(j)
                wh = _mix64(h ^ 0xA0761D6478BD642F)
                ws.append(0.55 + 0.90 * ((wh & 0xFFFF) / 65535.0))
            total = sum(ws) or 1.0
            self.neighbors.append(tuple(ns))
            self.weights.append(tuple(w / total for w in ws))
        self.causal_step = 0
        self.velocity_ema = [0.0] * p.groups
        self.prev_macro: list[float] | None = None
        self.macro_codes: collections.deque[int] = collections.deque(maxlen=self.HISTORY)
        self.macro_vectors: collections.deque[tuple[float, ...]] = collections.deque(maxlen=self.HISTORY)
        self.micro_sample_codes: collections.deque[int] = collections.deque(maxlen=self.HISTORY)
        self.group_bit_history: collections.deque[tuple[int, ...]] = collections.deque(maxlen=self.HISTORY)
        self.macro_tpm: dict[int, collections.Counter[int]] = collections.defaultdict(collections.Counter)
        self.micro_tpm: dict[int, collections.Counter[int]] = collections.defaultdict(collections.Counter)
        self.last_closure = 1.0
        self.last_probe = {
            "micro_divergence": 0.0,
            "macro_divergence": 0.0,
            "macro_reproducibility": 0.0,
            "interaction_sensitivity": 0.0,
            "shuffle_control_reproducibility": 0.0,
            "control_advantage": 0.0,
        }

    def _initial_state(self, i: int) -> float:
        h = _mix64(self.seed ^ (i * 0x9e3779b97f4a7c15))
        return ((h & 0xFFFF) / 32767.5) - 1.0

    def _macro(self, state: list[float] | None = None) -> list[float]:
        xs = self.state if state is None else state
        p = self.params
        sums = [0.0] * p.groups
        counts = [0] * p.groups
        for i, x in enumerate(xs):
            g = (i * p.groups) // p.units
            if g >= p.groups:
                g = p.groups - 1
            sums[g] += x
            counts[g] += 1
        return [sums[g] / max(1, counts[g]) for g in range(p.groups)]

    def _stimulus(self, digest: str | bytes | None) -> list[float]:
        if digest is None:
            raw = hashlib.sha256(f"{self.seed}:{self.causal_step}".encode()).digest()
        elif isinstance(digest, bytes):
            raw = hashlib.sha256(digest).digest()
        else:
            raw = hashlib.sha256(str(digest).encode("utf-8", errors="replace")).digest()
        return [(raw[i % len(raw)] / 127.5) - 1.0 for i in range(self.params.units)]

    def _step_state(self, state: list[float], stimulus: list[float], *, shuffle: bool = False, ablate_recurrence: bool = False) -> list[float]:
        p = self.params
        macro = self._macro(state)
        global_mean = sum(state) / len(state)
        out = [0.0] * p.units
        shuffle_offset = int(_mix64(self.seed ^ self.causal_step) % max(1, p.units - 1)) + 1
        for i, x in enumerate(state):
            recurrent = 0.0
            if not ablate_recurrence:
                ns = self.neighbors[i]
                ws = self.weights[i]
                if shuffle:
                    recurrent = sum(ws[k] * state[(ns[k] + shuffle_offset) % p.units] for k in range(p.fanout))
                else:
                    recurrent = sum(ws[k] * state[ns[k]] for k in range(p.fanout))
            g = (i * p.groups) // p.units
            if g >= p.groups:
                g = p.groups - 1
            drive = p.self_memory*x + p.recurrent_gain*recurrent + p.macro_feedback*macro[g] + p.input_gain*stimulus[i] - p.inhibition*global_mean + p.nonlinear_gain*math.sin(math.pi*(x+recurrent))
            out[i] = math.tanh(drive)
        return out

    def _codes(self, state: list[float], macro: list[float]) -> tuple[int, int, tuple[int, ...]]:
        macro_bits = tuple(1 if macro[i] >= 0.0 else 0 for i in range(min(8, len(macro))))
        macro_code = sum(bit << i for i, bit in enumerate(macro_bits))
        sample_code = 0
        for k in range(8):
            idx = int(_mix64(self.seed ^ (k * 0x9e3779b97f4a7c15)) % len(state))
            if state[idx] >= 0.0:
                sample_code |= 1 << k
        return macro_code, sample_code, macro_bits

    def step(self, stimulus_digest: str | bytes | None = None) -> None:
        stimulus = self._stimulus(stimulus_digest)
        before_macro = self._macro()
        old_macro_code, old_micro_code, _ = self._codes(self.state, before_macro)
        self.state = self._step_state(self.state, stimulus)
        self.causal_step += 1
        after_macro = self._macro()
        macro_code, micro_code, bits = self._codes(self.state, after_macro)
        if self.prev_macro is not None:
            pred = [self.prev_macro[g] + self.velocity_ema[g] for g in range(self.params.groups)]
            err = math.sqrt(sum((after_macro[g]-pred[g])**2 for g in range(self.params.groups))/self.params.groups)
            self.last_closure = clamp(err,0.0,2.0)
            velocity=[after_macro[g]-self.prev_macro[g] for g in range(self.params.groups)]
            self.velocity_ema=[0.85*self.velocity_ema[g]+0.15*velocity[g] for g in range(self.params.groups)]
        self.prev_macro=after_macro
        self.macro_tpm[old_macro_code][macro_code]+=1
        self.micro_tpm[old_micro_code][micro_code]+=1
        self.macro_codes.append(macro_code)
        self.micro_sample_codes.append(micro_code)
        self.macro_vectors.append(tuple(after_macro))
        self.group_bit_history.append(bits)

    def perturbation_probe(self, stimulus_digest: str | bytes | None = None) -> dict[str,float]:
        p=self.params; stimulus=self._stimulus(stimulus_digest); a=list(self.state); b=list(self.state)
        count=max(1,p.units//64)
        for k in range(count):
            idx=int(_mix64(self.seed^self.causal_step^(k*0xD1B54A32D192ED03))%p.units)
            direction=-1.0 if (_mix64(idx^self.causal_step)&1) else 1.0
            b[idx]=clamp(b[idx]+direction*p.perturbation_scale,-1.0,1.0)
        a_shuffle=list(a); b_shuffle=list(b); a_ablate=list(a)
        for _ in range(p.probe_horizon):
            a=self._step_state(a,stimulus); b=self._step_state(b,stimulus)
            a_shuffle=self._step_state(a_shuffle,stimulus,shuffle=True); b_shuffle=self._step_state(b_shuffle,stimulus,shuffle=True)
            a_ablate=self._step_state(a_ablate,stimulus,ablate_recurrence=True)
        micro_div=math.sqrt(sum((x-y)**2 for x,y in zip(a,b))/p.units)
        ma=self._macro(a); mb=self._macro(b)
        macro_div=math.sqrt(sum((x-y)**2 for x,y in zip(ma,mb))/p.groups)
        repro=0.0 if micro_div<=1e-12 else clamp(1.0-macro_div/micro_div,0.0,1.0)
        msa=self._macro(a_shuffle); msb=self._macro(b_shuffle)
        micro_shuffle=math.sqrt(sum((x-y)**2 for x,y in zip(a_shuffle,b_shuffle))/p.units)
        macro_shuffle=math.sqrt(sum((x-y)**2 for x,y in zip(msa,msb))/p.groups)
        shuffle_repro=0.0 if micro_shuffle<=1e-12 else clamp(1.0-macro_shuffle/micro_shuffle,0.0,1.0)
        mab=self._macro(a_ablate)
        interaction=math.sqrt(sum((x-y)**2 for x,y in zip(ma,mab))/p.groups)
        interaction_sensitivity=clamp(interaction/0.35,0.0,1.0)
        control_advantage=clamp((repro-shuffle_repro+1.0)/2.0,0.0,1.0)
        self.last_probe={"micro_divergence":micro_div,"macro_divergence":macro_div,"macro_reproducibility":repro,"interaction_sensitivity":interaction_sensitivity,"shuffle_control_reproducibility":shuffle_repro,"control_advantage":control_advantage}
        return dict(self.last_probe)

    def _macro_entropy_and_switching(self)->tuple[float,float]:
        codes=list(self.macro_codes)
        if len(codes)<4:return 0.0,0.0
        counts=collections.Counter(codes); probs=[v/len(codes) for v in counts.values()]
        denom=math.log2(max(2,min(256,len(codes)))); ent=clamp(_entropy(probs)/denom,0.0,1.0)
        switches=sum(1 for a,b in zip(codes,codes[1:]) if a!=b)/max(1,len(codes)-1)
        return ent,switches

    def _synergy_proxy(self)->float:
        bits=list(self.group_bit_history); targets=list(self.macro_codes)
        if len(bits)<16 or len(targets)<16:return 0.0
        ys=targets[1:]; samples=bits[:-1]; nbits=min(4,len(samples[0])); vals=[]; denom=max(1.0,math.log2(max(2,len(set(ys)))))
        for i in range(nbits):
            xi=[s[i] for s in samples]; mii=mutual_information(xi,ys)
            for j in range(i+1,nbits):
                xj=[s[j] for s in samples]; mij=mutual_information(xj,ys); pair=[(s[i]<<1)|s[j] for s in samples]; mip=mutual_information(pair,ys)
                vals.append(max(0.0,mip-max(mii,mij))/denom)
        return clamp(sum(vals)/max(1,len(vals)),0.0,1.0)

    def metrics(self)->GRFMetrics:
        macro_entropy,switching=self._macro_entropy_and_switching(); meta=math.exp(-2.4*abs(macro_entropy-0.58)-1.8*abs(switching-0.42))
        closure_quality=1.0/(1.0+3.0*self.last_closure); micro_ei=normalized_effective_information(self.micro_tpm); macro_ei=normalized_effective_information(self.macro_tpm); ce=clamp(macro_ei-micro_ei,-1.0,1.0); synergy=self._synergy_proxy(); probe=self.last_probe
        tc=clamp(0.28*macro_entropy+0.26*switching+0.26*min(1.0,probe["micro_divergence"]/0.25)+0.20*self.params.recurrent_gain/2.2,0.0,1.0)
        components=[max(1e-6,closure_quality),max(1e-6,probe["macro_reproducibility"]),max(1e-6,meta),max(1e-6,0.5+0.5*ce),max(1e-6,0.5+0.5*synergy),max(1e-6,probe["control_advantage"])]
        emergence=len(components)/sum(1.0/x for x in components)
        return GRFMetrics(self.causal_step,self.last_closure,closure_quality,probe["micro_divergence"],probe["macro_divergence"],probe["macro_reproducibility"],micro_ei,macro_ei,ce,synergy,macro_entropy,switching,meta,probe["interaction_sensitivity"],probe["shuffle_control_reproducibility"],probe["control_advantage"],tc,emergence,False,"INTERNAL_GRF_METRICS_ONLY: held-out task gain + independent ablation required for LAYER_SEAL")

    def regulate(self,metrics:GRFMetrics)->str:
        p=self.params; action="HOLD"; frozen=metrics.macro_entropy<0.18 or metrics.switching_rate<0.06; runaway=metrics.closure_residual>0.55 or metrics.switching_rate>0.90 or metrics.macro_reproducibility<0.20
        if frozen:p.recurrent_gain+=0.025;p.nonlinear_gain+=0.010;p.inhibition-=0.008;action="EXPAND_DYNAMICS"
        elif runaway:p.recurrent_gain-=0.035;p.nonlinear_gain-=0.010;p.inhibition+=0.018;action="STABILIZE_DYNAMICS"
        else:
            if metrics.causal_emergence_proxy< -0.03:p.macro_feedback+=0.006;p.recurrent_gain-=0.006;action="INCREASE_MACRO_CLOSURE"
            elif metrics.control_advantage<0.48:p.recurrent_gain+=0.005;p.inhibition+=0.002;action="STRENGTHEN_INTERACTION_STRUCTURE"
            elif metrics.cognitive_temperature<0.30:p.nonlinear_gain+=0.004;action="WARM_METASTABLE_REGIME"
            elif metrics.cognitive_temperature>0.72:p.inhibition+=0.006;action="COOL_METASTABLE_REGIME"
        p.clamp_inplace();return action

    def snapshot(self)->dict[str,Any]:
        return {"schema":"OMEGA_GRF_EMERGENCE_FIELD/v1","grf":{"R":"materialized microstate + macrostate","M":"bounded parameter/potential/intervention space","F":"deterministic nonlinear sparse transition","meta_order":self.causal_step},"parameters":dataclasses.asdict(self.params),"macrostate":self._macro(),"metrics":self.metrics().as_dict(),"authority":"INTERNAL_COGNITIVE_DYNAMICS_ONLY","effect_authority":False,"canonical_truth_authority":False}


def effective_cpu_capacity()->float:
    try:affinity=float(len(os.sched_getaffinity(0)))
    except (AttributeError,OSError):affinity=float(max(1,os.cpu_count() or 1))
    quota_capacity=None
    try:
        raw=open('/sys/fs/cgroup/cpu.max','r',encoding='utf-8').read().strip().split()
        if len(raw)==2 and raw[0]!='max':
            quota=float(raw[0]);period=float(raw[1]);quota_capacity=quota/period if quota>0 and period>0 else None
    except (OSError,ValueError):pass
    return max(0.1,min(affinity,quota_capacity)) if quota_capacity is not None else max(1.0,affinity)


class BrainCpuBudget:
    def __init__(self,target_host_fraction:float=0.20,*,hard_ceiling:float=0.24)->None:
        self.cpu_capacity=effective_cpu_capacity();self.target_host_fraction=clamp(float(target_host_fraction),0.01,0.90);self.hard_ceiling=max(self.target_host_fraction,clamp(float(hard_ceiling),0.02,0.98));self.target_single_process_fraction=min(0.95,self.target_host_fraction*self.cpu_capacity);self.attainable_with_one_process=self.target_host_fraction*self.cpu_capacity<=0.95;self.last_observed_host_fraction=0.0;self._window_wall=time.monotonic();self._window_cpu=time.process_time()
    def pace(self,batch_wall_start:float,batch_cpu_start:float)->float:
        wall_used=max(1e-9,time.monotonic()-batch_wall_start);cpu_used=max(0.0,time.process_time()-batch_cpu_start);desired_wall=cpu_used/max(1e-6,self.target_single_process_fraction);sleep_for=max(0.0,desired_wall-wall_used);now_wall=time.monotonic();now_cpu=time.process_time();dtw=now_wall-self._window_wall
        if dtw>=0.75:
            dtc=max(0.0,now_cpu-self._window_cpu);self.last_observed_host_fraction=clamp(dtc/(dtw*self.cpu_capacity),0.0,1.0);self._window_wall=now_wall;self._window_cpu=now_cpu
            if self.last_observed_host_fraction>self.hard_ceiling:sleep_for+=min(0.25,dtw*(self.last_observed_host_fraction/self.target_host_fraction-1.0))
        return sleep_for
    def status(self)->dict[str,Any]:
        return {"target_host_fraction":self.target_host_fraction,"hard_ceiling_host_fraction":self.hard_ceiling,"observed_host_fraction":self.last_observed_host_fraction,"cpu_capacity":self.cpu_capacity,"target_single_process_fraction":self.target_single_process_fraction,"attainable_with_one_process":self.attainable_with_one_process}
