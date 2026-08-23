from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import PipelineFault, ProfilePipelineRuntime
from test_blogpost_entity import profile_b


pytestmark = pytest.mark.skipif(
    not hasattr(ProfilePipelineRuntime, "_pipeline_profile_read"),
    reason="activates only when DB-profile reference convergence is present",
)


def _empty_collected() -> dict:
    return {
        "sources": {},
        "sensors": {},
        "probes": {},
        "source_count": 0,
        "quiet_sensors_ok": False,
    }


def _compiled_profile_b(runtime: ProfilePipelineRuntime, profile: dict) -> dict:
    return runtime._pipeline_compile({"profile": profile, "data": _empty_collected()})


def _generated_claim(compiled: dict, strength) -> dict:
    return {
        "payload": {
            "canonical_state_hash_seen": compiled["canonical_state_hash"],
            "packet_hash_seen": compiled["packet_hash"],
            "heading": "h",
            "lead": "l",
            "blocks": [
                {
                    "body": "b",
                    "refs": ["state:confidence"],
                    "state": {"confidence": strength},
                }
            ],
            "carry": "c",
            "open_questions": "q",
        }
    }


def _assert_compile_rejected(callable_) -> None:
    try:
        result = callable_()
    except (PipelineFault, ValueError, OverflowError):
        return
    assert result.get("ok") is False, (
        "non-finite claim-authorizing metric entered canonical state/hash instead of failing closed"
    )


def test_nonfinite_claim_authorizing_metric_never_enters_canonical_hash() -> None:
    """NaN/Inf are neither UNKNOWN, ZERO nor MEASURED and cannot become truth authority."""
    runtime = ProfilePipelineRuntime()
    for bad in ("nan", "inf", "-inf", float("nan"), float("inf"), float("-inf")):
        profile = profile_b()
        profile["state_metrics"][0]["value"] = bad
        _assert_compile_rejected(lambda p=profile: _compiled_profile_b(runtime, p))


@pytest.mark.parametrize("strength", ["nan", "-inf", float("nan"), float("-inf")])
def test_nonfinite_state_claim_strength_cannot_bypass_overshoot_gate(strength) -> None:
    """IEEE non-finites must not exploit comparisons such as NaN > limit == False."""
    runtime = ProfilePipelineRuntime()
    profile = profile_b()
    compiled = _compiled_profile_b(runtime, profile)
    generated = _generated_claim(compiled, strength)

    try:
        gated = runtime._pipeline_gate(
            {"profile": profile, "data": {"generated": generated, "compiled": compiled}}
        )
    except (PipelineFault, ValueError, OverflowError):
        return
    assert gated.get("ok") is False, (
        "non-finite state-claim strength bypassed the deterministic truth gate"
    )


def test_nonfinite_claim_tolerance_cannot_disable_overshoot_gate() -> None:
    """Editable tolerance itself is claim authority and must be finite before comparison."""
    runtime = ProfilePipelineRuntime()
    profile = profile_b()
    profile["gate"]["max_claim_overshoot"] = "nan"
    compiled = _compiled_profile_b(runtime, profile)
    generated = _generated_claim(compiled, 0.9)

    try:
        gated = runtime._pipeline_gate(
            {"profile": profile, "data": {"generated": generated, "compiled": compiled}}
        )
    except (PipelineFault, ValueError, OverflowError):
        return
    assert gated.get("ok") is False, (
        "non-finite max_claim_overshoot disabled deterministic overshoot rejection"
    )
