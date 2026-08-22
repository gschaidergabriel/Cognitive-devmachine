from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

from tools.clay_profile_pipeline_runtime import PipelineFault, ProfilePipelineRuntime


def _contract() -> dict:
    return {
        "title_field": "title",
        "intro_field": "intro",
        "sections_field": "sections",
        "section_text_field": "text",
        "section_evidence_field": "evidence",
        "section_claims_field": "claims",
        "continuity_field": "thread",
        "autobiographical_hypotheses_field": "hypotheses",
    }


def _profile() -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "security_regression",
        "inference": {"kind": "mock", "model": "fixture", "secret_names": []},
        "personality": {
            "system_prompt": "fixture",
            "public_style": "fixture",
            "output_contract": _contract(),
        },
        "sources": [],
        "canonical_probes": [],
        "state_metrics": [],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": True,
            "max_claim_overshoot": 0.0,
            "leak_patterns": ["PRIVATE_LEAK"],
        },
    }


def _payload() -> dict:
    return {
        "canonical_state_hash_seen": "canonical",
        "packet_hash_seen": "packet",
        "title": "safe",
        "intro": "safe",
        "sections": [{"text": "safe", "evidence": ["e:1"], "claims": {}}],
        "thread": "safe",
        "hypotheses": "safe",
    }


def _gate(runtime: ProfilePipelineRuntime, payload: dict) -> dict:
    return runtime._pipeline_gate(
        {
            "profile": _profile(),
            "data": {
                "generated": {"payload": payload},
                "compiled": {
                    "canonical_state_hash": "canonical",
                    "packet_hash": "packet",
                    "allowed_evidence_refs": ["e:1"],
                    "personality_state": {},
                },
            },
        }
    )


def test_leak_gate_scans_mapping_keys_not_only_values(tmp_path: Path):
    runtime = ProfilePipelineRuntime(root=tmp_path)
    payload = _payload()
    payload["metadata"] = {"PRIVATE_LEAK": "innocent-value"}
    result = _gate(runtime, payload)
    assert result["ok"] is False
    assert "LEAK" in str(result.get("error", "")).upper()


@pytest.mark.parametrize("secret_field", ["client_secret", "bearer_token", "refresh_token", "auth_token"])
def test_profile_import_rejects_common_embedded_secret_field_names(tmp_path: Path, secret_field: str):
    runtime = ProfilePipelineRuntime(root=tmp_path)
    profile = _profile()
    profile["profile_notes"] = {secret_field: "must-never-enter-miniunifieddb"}
    with pytest.raises(PipelineFault, match="SECRET"):
        runtime.import_profile(str(tmp_path / "entity.db"), profile)


def test_profile_cannot_whitelist_provider_secret_into_local_exec_child(tmp_path: Path, monkeypatch):
    model = tmp_path / "model.gguf"
    model.write_bytes(b"fixture")
    runner = tmp_path / "runner.py"
    runner.write_text(
        "#!/usr/bin/env python3\n"
        "import json,os\n"
        "print(json.dumps({'seen_secret': os.environ.get('MISTRAL_API_KEY')}))\n",
        encoding="utf-8",
    )
    runner.chmod(runner.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("MISTRAL_API_KEY", "provider-secret-must-stay-out")

    runtime = ProfilePipelineRuntime(root=tmp_path)
    generated = runtime._local_exec_generate(
        {
            "kind": "local_exec",
            "local_model_path": str(model),
            "local_argv_json": [sys.executable, str(runner)],
            "local_env_allowlist": ["PATH", "MISTRAL_API_KEY"],
        },
        {"system": "s", "user": "u"},
    )
    assert generated["ok"] is False or generated.get("payload", {}).get("seen_secret") is None
    assert os.environ["MISTRAL_API_KEY"] == "provider-secret-must-stay-out"


def test_division_by_zero_never_collapses_unknown_or_undefined_to_zero(tmp_path: Path):
    runtime = ProfilePipelineRuntime(root=tmp_path)
    with pytest.raises((PipelineFault, ZeroDivisionError, ValueError)):
        runtime._expr({"op": "div", "a": 1.0, "b": 0.0}, {})
