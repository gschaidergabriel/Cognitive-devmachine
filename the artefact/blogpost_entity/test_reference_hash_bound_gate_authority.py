from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


def _profile() -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "hash-bound-gate",
        "inference": {"kind": "mock", "secret_names": []},
        "personality": {
            "system_prompt": "",
            "public_style": "",
            "output_contract": {
                "title_field": "title",
                "intro_field": "intro",
                "sections_field": "sections",
                "section_text_field": "text",
                "section_evidence_field": "evidence",
                "section_claims_field": "claims",
                "continuity_field": "thread",
                "autobiographical_hypotheses_field": "hypotheses",
            },
        },
        "sources": [],
        "canonical_probes": [],
        "state_metrics": [
            {
                "name": "confidence",
                "status": "VERIFIED",
                "value": 0.2,
                "evidence_ref": "state:confidence",
            }
        ],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": True,
            "max_claim_overshoot": 0.0,
        },
    }


def _empty_collected() -> dict:
    return {
        "sources": {},
        "sensors": {},
        "probes": {},
        "consume": [],
        "next_cursors": {},
        "source_count": 0,
        "quiet_sensors_ok": False,
    }


def test_gate_authority_is_the_metric_state_inside_canonical_hash() -> None:
    """Replacing an un-hashed convenience copy must never strengthen claim authority."""
    runtime = ProfilePipelineRuntime()
    profile = _profile()
    compiled = runtime.effect(
        "pipeline_compile", {"profile": profile, "data": _empty_collected()}
    )
    assert compiled["ok"] is True
    assert compiled["canonical"]["personality_state"]["confidence"]["value"] == 0.2

    # Model an accidental/adversarial divergence after canonical_state_hash was computed.
    # The immutable hash-bound metric stays 0.2; only the parallel convenience slot changes.
    compiled["personality_state"] = {
        "confidence": {
            "status": "VERIFIED",
            "value": 1.0,
            "evidence_ref": "state:confidence",
        }
    }
    generated = {
        "payload": {
            "canonical_state_hash_seen": compiled["canonical_state_hash"],
            "packet_hash_seen": compiled["packet_hash"],
            "title": "t",
            "intro": "i",
            "sections": [
                {
                    "text": "claim",
                    "evidence": ["state:confidence"],
                    "claims": {"confidence": 0.9},
                }
            ],
            "thread": "c",
            "hypotheses": "h",
        }
    }

    result = runtime.effect(
        "pipeline_gate",
        {"profile": profile, "data": {"generated": generated, "compiled": compiled}},
    )
    assert result["ok"] is False
    assert "STATE_CLAIM_OVERSHOOT" in str(result.get("error", "")), (
        "pipeline_gate trusted a mutable parallel personality_state copy rather than the "
        "personality_state committed inside canonical_state_hash"
    )
