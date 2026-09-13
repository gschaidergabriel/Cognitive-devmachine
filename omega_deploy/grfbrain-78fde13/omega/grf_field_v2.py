from __future__ import annotations

import math
from typing import Any

from .grf_emergence import GRFEmergenceField, GRFMetrics, clamp, _mix64


class GRFHomeostaticField(GRFEmergenceField):
    def _stimulus(self, digest: str | bytes | None) -> list[float]:
        base = super()._stimulus(digest)
        slow = self.causal_step / 96.0
        out: list[float] = []
        for i, x in enumerate(base):
            phase_bits = _mix64(self.seed ^ (i * 0x9E3779B97F4A7C15))
            phase = (phase_bits & 0xFFFF) / 65535.0 * 2.0 * math.pi
            modulation = 0.12 * math.sin(slow + phase) + 0.05 * math.sin(slow * 0.173 + phase * 0.41)
            out.append(clamp(0.78 * x + modulation, -1.0, 1.0))
        return out

    def state_shape(self) -> dict[str, float]:
        n = max(1, len(self.state)); mean = sum(self.state) / n
        variance = sum((x - mean) ** 2 for x in self.state) / n
        mean_abs = sum(abs(x) for x in self.state) / n
        saturated = sum(abs(x) >= 0.92 for x in self.state) / n
        return {"mean": mean, "std": math.sqrt(max(0.0, variance)), "mean_abs": mean_abs, "saturation_fraction": saturated}

    def regulate(self, metrics: GRFMetrics) -> str:
        p = self.params; shape = self.state_shape()
        frozen = metrics.macro_entropy < 0.18 or metrics.switching_rate < 0.06
        saturated = shape["saturation_fraction"] > 0.62 or shape["mean_abs"] > 0.86
        runaway = metrics.closure_residual > 0.55 or metrics.switching_rate > 0.90 or metrics.macro_reproducibility < 0.20
        action = "HOLD"
        if frozen and saturated:
            p.recurrent_gain -= 0.055; p.self_memory -= 0.018; p.macro_feedback -= 0.012; p.nonlinear_gain -= 0.008; p.inhibition += 0.022; p.input_gain += 0.016; action = "BREAK_SATURATED_ATTRACTOR"
        elif runaway:
            p.recurrent_gain -= 0.035; p.nonlinear_gain -= 0.010; p.inhibition += 0.018; action = "STABILIZE_DYNAMICS"
        elif frozen:
            p.recurrent_gain += 0.012; p.nonlinear_gain += 0.004; p.input_gain += 0.006; action = "WAKE_QUIET_REGIME"
        elif metrics.causal_emergence_proxy < -0.03:
            p.macro_feedback += 0.004; p.recurrent_gain -= 0.004; action = "INCREASE_MACRO_CLOSURE"
        elif metrics.control_advantage < 0.48:
            p.recurrent_gain += 0.003; p.inhibition += 0.002; action = "STRENGTHEN_INTERACTION_STRUCTURE"
        elif metrics.cognitive_temperature < 0.30:
            p.nonlinear_gain += 0.002; p.input_gain += 0.002; action = "WARM_METASTABLE_REGIME"
        elif metrics.cognitive_temperature > 0.72:
            p.inhibition += 0.006; action = "COOL_METASTABLE_REGIME"
        p.clamp_inplace(); return action

    def snapshot(self) -> dict[str, Any]:
        out = super().snapshot(); out["schema"] = "OMEGA_GRF_EMERGENCE_FIELD/v2-candidate"; out["state_shape"] = self.state_shape(); out["controller_revision"] = "SATURATION_AWARE_HOMEOSTASIS"; return out
