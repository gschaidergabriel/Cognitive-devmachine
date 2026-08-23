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


def _assert_compile_rejected(runtime: ProfilePipelineRuntime, profile: dict) -> None:
    try:
        result = runtime._pipeline_compile({"profile": profile, "data": _empty_collected()})
    except (PipelineFault, ValueError, TypeError, OverflowError):
        return
    assert result.get("ok") is False, (
        "boolean claim-authorizing input was numerically laundered before the finite/nonboolean boundary"
    )


@pytest.mark.parametrize("bad", [True, False])
def test_boolean_metric_cannot_be_laundered_through_add_expression(bad: bool) -> None:
    """`float(True|False)` must not turn profile booleans into measured numeric truth."""
    runtime = ProfilePipelineRuntime()
    profile = profile_b()
    profile["state_metrics"][0]["value"] = {"op": "add", "args": [bad]}
    _assert_compile_rejected(runtime, profile)


@pytest.mark.parametrize("op", ["clamp01", "div"])
def test_boolean_metric_cannot_be_laundered_by_other_numeric_operators(op: str) -> None:
    """All numeric-expression entry points preserve the nonboolean truth boundary."""
    runtime = ProfilePipelineRuntime()
    profile = profile_b()
    if op == "clamp01":
        expr = {"op": "clamp01", "arg": True}
    else:
        expr = {"op": "div", "a": True, "b": 1.0}
    profile["state_metrics"][0]["value"] = expr
    _assert_compile_rejected(runtime, profile)
