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


def _compiled(runtime: ProfilePipelineRuntime, profile: dict) -> dict:
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


def _fails_closed(callable_) -> bool:
    try:
        result = callable_()
    except (PipelineFault, TypeError, ValueError, OverflowError):
        return True
    return isinstance(result, dict) and result.get("ok") is False


@pytest.mark.parametrize("value", [True, False])
def test_bool_metric_is_not_numeric_measurement(value) -> None:
    runtime = ProfilePipelineRuntime()
    profile = profile_b()
    profile["state_metrics"][0]["value"] = value
    assert _fails_closed(lambda: _compiled(runtime, profile)), (
        "bool entered canonical personality_state as a numeric measurement"
    )


@pytest.mark.parametrize("strength", [True, False])
def test_bool_claim_strength_is_not_numeric_claim_authority(strength) -> None:
    runtime = ProfilePipelineRuntime()
    profile = profile_b()
    compiled = _compiled(runtime, profile)
    assert _fails_closed(
        lambda: runtime._pipeline_gate(
            {
                "profile": profile,
                "data": {
                    "generated": _generated_claim(compiled, strength),
                    "compiled": compiled,
                },
            }
        )
    ), "bool claim strength was coerced to 1/0 and admitted as numeric authority"


@pytest.mark.parametrize("tolerance", [True, False])
def test_bool_overshoot_tolerance_is_not_numeric_gate_authority(tolerance) -> None:
    runtime = ProfilePipelineRuntime()
    profile = profile_b()
    profile["gate"]["max_claim_overshoot"] = tolerance
    compiled = _compiled(runtime, profile)
    assert _fails_closed(
        lambda: runtime._pipeline_gate(
            {
                "profile": profile,
                "data": {
                    "generated": _generated_claim(compiled, 0.8),
                    "compiled": compiled,
                },
            }
        )
    ), "bool max_claim_overshoot was coerced into numeric gate authority"
