from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def test_unknown_metric_has_no_numeric_value(tmp_path: Path) -> None:
    """UNKNOWN is typed absence, never a numeric zero surrogate."""
    runtime = ProfilePipelineRuntime(root=tmp_path)
    profile = {
        "state_metrics": [
            {
                "name": "unknown_probe",
                "unknown_if": True,
                "value": 0.0,
                "evidence_ref": "state:unknown_probe",
            }
        ]
    }
    collected = {
        "source_count": 0,
        "quiet_sensors_ok": False,
        "sources": {},
        "sensors": {},
        "probes": {},
    }

    compiled = runtime._pipeline_compile({"profile": profile, "data": collected})
    metric = compiled["personality_state"]["unknown_probe"]

    assert metric["status"] == "UNKNOWN"
    assert metric["value"] is None, "UNKNOWN must not be encoded as numeric 0.0"
