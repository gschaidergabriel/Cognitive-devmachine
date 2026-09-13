from __future__ import annotations

from .grf_emergence import _mix64
from .grf_field_v2 import GRFHomeostaticField


class GRFSignedField(GRFHomeostaticField):
    def __init__(self, *args, inhibitory_fraction: float = 0.25, **kwargs):
        super().__init__(*args, **kwargs)
        frac = max(0.05, min(0.45, float(inhibitory_fraction)))
        threshold = int(frac * 65536)
        signed = []
        for i, row in enumerate(self.weights):
            vals = []
            for k, magnitude in enumerate(row):
                h = _mix64(self.seed ^ 0xC6A4A7935BD1E995 ^ (i * 0x9E3779B97F4A7C15) ^ (k * 0xD1B54A32D192ED03))
                sign = -1.0 if (h & 0xFFFF) < threshold else 1.0
                vals.append(sign * abs(magnitude))
            norm = sum(abs(x) for x in vals) or 1.0
            signed.append(tuple(x / norm for x in vals))
        self.weights = signed
        self.inhibitory_fraction = frac

    def snapshot(self):
        out = super().snapshot()
        out["schema"] = "OMEGA_GRF_EMERGENCE_FIELD/v3-candidate"
        out["controller_revision"] = "SIGNED_RECURRENCE_PLUS_SATURATION_HOMEOSTASIS"
        out["inhibitory_fraction"] = self.inhibitory_fraction
        return out
