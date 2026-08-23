from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import PipelineFault, ProfilePipelineRuntime


def _profile_without_snapshot_namespace() -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "snapshot-source-identity-guard",
        "inference": {"kind": "mock", "secret_names": []},
        "personality": {
            "output_contract": {
                "title_field": "title",
                "intro_field": "intro",
                "sections_field": "sections",
                "section_text_field": "text",
                "section_evidence_field": "evidence",
                "section_claims_field": "claims",
                "continuity_field": "thread",
                "autobiographical_hypotheses_field": "hypotheses",
            }
        },
        "sources": [
            {
                "kind": "snapshot",
                "adapter": "json_snapshot",
                "path": "replaceable-location.json",
                "evidence_prefix": "snapshot:",
                "required_for_quiet": False,
            }
        ],
        "canonical_probes": [],
        "state_metrics": [],
        "gate": {},
    }


def test_snapshot_that_can_mint_evidence_requires_explicit_logical_source_identity() -> None:
    """Snapshot evidence must not silently bind provenance to a replaceable profile/path.

    SQLite and JSONL sources already require explicit source_namespace. A json_snapshot can
    also mint an allowed evidence ref, so omitting logical identity would let two different
    snapshot sources reuse the same presentation prefix across profile swaps. The generic
    source-identity contract therefore requires the same explicit namespace boundary.
    """
    with pytest.raises(PipelineFault) as excinfo:
        ProfilePipelineRuntime._normalize_profile(_profile_without_snapshot_namespace())

    assert "SOURCE_NAMESPACE_REQUIRED:snapshot" in str(excinfo.value)
