from __future__ import annotations

"""Measured-cost routing gate for ONLINE vs FULL_GENERATION vs SPM-S1 maintenance.

This is a performance/resource controller only. It does not decide semantic truth, retrieval
relevance, epistemic status or effect authority. It complements the U16 compile-amortization
gate by choosing a maintenance strategy only after equivalent-quality access paths are
available.

SPM-S1 is admitted only when the caller supplies a bounded estimate of impact-locality.
Unknown locality fails conservatively to the simpler ONLINE/FULL_GENERATION alternatives.
"""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class MaintenanceEconomics:
    expected_reads: float
    expected_updates: float
    online_query_us: float
    compiled_query_us: float
    full_build_us: float
    full_refresh_us: float
    spm_build_us: float
    spm_local_refresh_us: float
    local_impact_probability: float | None
    online_quality: float
    full_quality: float
    spm_quality: float
    safety_factor: float = 1.20


@dataclass(frozen=True)
class MaintenanceDecision:
    mode: str
    online_total_us: float
    full_total_us: float | None
    spm_total_us: float | None
    selected_total_us: float
    expected_savings_vs_online_us: float
    expected_savings_vs_full_us: float | None
    spm_local_update_break_even: float | None
    reason: str
    authority: str = "PERFORMANCE_ROUTING_ONLY_NO_TRUTH_AUTHORITY"


def _finite_nonnegative(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def spm_local_update_break_even(
    *, full_build_us: float, spm_build_us: float, full_refresh_us: float, spm_local_refresh_us: float
) -> float | None:
    """Local updates needed for SPM's extra bootstrap cost to amortize against full-copy."""
    extra_build = float(spm_build_us) - float(full_build_us)
    per_update_saving = float(full_refresh_us) - float(spm_local_refresh_us)
    if extra_build <= 0:
        return 0.0
    if per_update_saving <= 0:
        return None
    return extra_build / per_update_saving


def decide_maintenance(e: MaintenanceEconomics) -> MaintenanceDecision:
    vals = {
        "expected_reads": e.expected_reads,
        "expected_updates": e.expected_updates,
        "online_query_us": e.online_query_us,
        "compiled_query_us": e.compiled_query_us,
        "full_build_us": e.full_build_us,
        "full_refresh_us": e.full_refresh_us,
        "spm_build_us": e.spm_build_us,
        "spm_local_refresh_us": e.spm_local_refresh_us,
        "online_quality": e.online_quality,
        "full_quality": e.full_quality,
        "spm_quality": e.spm_quality,
    }
    checked = {k: _finite_nonnegative(k, v) for k, v in vals.items()}
    safety = float(e.safety_factor)
    if not math.isfinite(safety) or safety < 1.0:
        raise ValueError("safety_factor must be finite and >=1")
    locality = e.local_impact_probability
    if locality is not None:
        locality = float(locality)
        if not math.isfinite(locality) or not 0.0 <= locality <= 1.0:
            raise ValueError("local_impact_probability must be in [0,1] or None")

    reads = checked["expected_reads"]
    updates = checked["expected_updates"]
    online_total = reads * checked["online_query_us"]
    break_even = spm_local_update_break_even(
        full_build_us=checked["full_build_us"],
        spm_build_us=checked["spm_build_us"],
        full_refresh_us=checked["full_refresh_us"],
        spm_local_refresh_us=checked["spm_local_refresh_us"],
    )

    full_total: float | None = None
    if checked["full_quality"] >= checked["online_quality"]:
        full_total = (
            safety * checked["full_build_us"]
            + reads * checked["compiled_query_us"]
            + safety * updates * checked["full_refresh_us"]
        )

    spm_total: float | None = None
    if locality is not None and checked["spm_quality"] >= checked["online_quality"]:
        # A non-local/unknown-impact event pays the conservative full-refresh fallback cost.
        expected_refresh = (
            locality * checked["spm_local_refresh_us"]
            + (1.0 - locality) * checked["full_refresh_us"]
        )
        spm_total = (
            safety * checked["spm_build_us"]
            + reads * checked["compiled_query_us"]
            + safety * updates * expected_refresh
        )

    candidates: list[tuple[str, float]] = [("ONLINE", online_total)]
    if full_total is not None:
        candidates.append(("FULL_GENERATION", full_total))
    if spm_total is not None:
        candidates.append(("SPM_S1", spm_total))
    mode, selected = min(candidates, key=lambda x: (x[1], x[0]))

    if mode == "ONLINE":
        if full_total is None and spm_total is None:
            reason = "COMPILED_QUALITY_BELOW_ONLINE_OR_LOCALITY_UNKNOWN"
        elif min(x for x in (full_total, spm_total) if x is not None) >= online_total:
            reason = "COMPILED_TOTAL_WORK_NOT_CHEAPER"
        else:
            reason = "ONLINE_MIN_TOTAL_WORK"
    elif mode == "FULL_GENERATION":
        if spm_total is None and locality is None:
            reason = "FULL_WINS_AND_SPM_LOCALITY_UNKNOWN"
        elif spm_total is None:
            reason = "FULL_WINS_AND_SPM_QUALITY_REGRESSED"
        else:
            reason = "FULL_GENERATION_MIN_GUARDED_TOTAL_WORK"
    else:
        reason = "SPM_LOCALITY_AMORTIZES_EXTRA_BOOKKEEPING"

    return MaintenanceDecision(
        mode=mode,
        online_total_us=online_total,
        full_total_us=full_total,
        spm_total_us=spm_total,
        selected_total_us=selected,
        expected_savings_vs_online_us=online_total - selected,
        expected_savings_vs_full_us=(None if full_total is None else full_total - selected),
        spm_local_update_break_even=break_even,
        reason=reason,
    )
