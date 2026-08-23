from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def _compiled_ref(runtime: ProfilePipelineRuntime, prefix: str, namespace: str) -> tuple[str, ...]:
    profile = {"state_metrics": [], "profile_notes": {}}
    collected = {
        "sources": {
            "event": {
                "ok": True,
                "kind": "event",
                "source_namespace": namespace,
                "rows": [{"source_id": 1, "payload": namespace}],
                "value": None,
                "evidence_prefix": prefix,
                "required_for_quiet": False,
            }
        },
        "sensors": {"event": {"ok": True}},
        "probes": {},
        "source_count": 1,
        "quiet_sensors_ok": False,
    }
    compiled = runtime._pipeline_compile({"profile": profile, "data": collected})
    assert compiled["ok"] is True
    return tuple(compiled["allowed_evidence_refs"])


def test_evidence_ref_encoding_is_injective_over_prefix_and_source_namespace(tmp_path: Path) -> None:
    """Presentation prefix must not make two distinct logical source identities alias.

    Current concatenation without a structural boundary before the namespace can collapse
    `(prefix='ab', namespace='c')` and `(prefix='a', namespace='bc')` to the same visible ref.
    The concrete repaired encoding remains implementation-neutral; only non-aliasing matters.
    """
    runtime = ProfilePipelineRuntime(root=tmp_path)

    refs_a = _compiled_ref(runtime, "ab", "c")
    refs_b = _compiled_ref(runtime, "a", "bc")

    assert refs_a != refs_b, (
        "distinct (evidence_prefix, source_namespace) tuples collapsed to one evidence ref; "
        "encode source provenance structurally rather than by ambiguous concatenation"
    )
