from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_structured_backend as clay
from clay_profile_pipeline_runtime import PROFILE_SCHEMA, PipelineFault, ProfilePipelineRuntime


def _profile() -> dict:
    return {
        "schema": PROFILE_SCHEMA,
        "profile_id": "neutral-test",
        "identity": {"entity_name": "fixture"},
        "inference": {"kind": "local_exec"},
        "personality": {"output_contract": {}},
        "sources": [],
        "state_metrics": [],
        "gate": {},
    }


def test_current_effect_surface_deauthorizes_legacy_names(tmp_path: Path) -> None:
    runtime = ProfilePipelineRuntime(root=tmp_path)
    assert runtime.allowed_effects == {
        "pipeline_init",
        "pipeline_profile_read",
        "pipeline_state_read",
        "pipeline_collect",
        "pipeline_compile",
        "pipeline_build_prompt",
        "inference_generate",
        "pipeline_gate",
        "pipeline_commit",
    }
    for legacy in ("profile_load", "provider_chat_json"):
        with pytest.raises(clay.StructuredFault, match="EFFECT_DENIED"):
            runtime.effect(legacy, {})


def test_db_profile_reuses_native_authority_and_hashes_persisted_bytes(tmp_path: Path) -> None:
    runtime = ProfilePipelineRuntime(root=tmp_path)
    entity_db = tmp_path / "entity.db"
    assert runtime.effect("pipeline_init", {"entity_db": str(entity_db)})["ok"] is True

    with sqlite3.connect(entity_db) as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "entity_state" in tables
        assert "profiles" in tables
        assert "eos_pipeline_profile" not in tables
        assert "eos_pipeline_profiles" not in tables
        assert db.execute("SELECT active_profile FROM entity_state WHERE id=1").fetchone()[0] is None

    missing = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})
    assert missing["ok"] is False
    assert missing["error"] == "NO_ACTIVE_PROFILE"

    digest = runtime.install_profile(str(entity_db), _profile())
    loaded = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})
    assert loaded["ok"] is True
    assert loaded["profile_hash"] == digest

    with sqlite3.connect(entity_db) as db:
        assert db.execute("SELECT active_profile FROM entity_state WHERE id=1").fetchone()[0] == "neutral-test"
        raw, stored_hash = db.execute(
            "SELECT profile_json,profile_sha256 FROM profiles WHERE profile_id='neutral-test'"
        ).fetchone()
        assert stored_hash == digest
        tampered = json.loads(raw)
        tampered["identity"] = {"entity_name": "tampered"}
        db.execute(
            "UPDATE profiles SET profile_json=? WHERE profile_id='neutral-test'",
            (json.dumps(tampered, sort_keys=True, separators=(",", ":")),),
        )
    tampered = runtime.effect("pipeline_profile_read", {"entity_db": str(entity_db)})
    assert tampered["ok"] is False
    assert tampered["error"] == "PROFILE_HASH_MISMATCH"


def test_response_pointer_accepts_shipped_rfc6901_shape(tmp_path: Path) -> None:
    runtime = ProfilePipelineRuntime(root=tmp_path)
    response = {"choices": [{"message": {"content": "payload"}}]}
    assert runtime._pointer(response, "/choices/0/message/content") == "payload"
    assert runtime._pointer(response, "choices.0.message.content") == "payload"


def test_local_exec_child_environment_does_not_inherit_provider_secret(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "parent-secret-sentinel")
    model = tmp_path / "model.gguf"
    model.write_bytes(b"fixture")
    runner = tmp_path / "runner.py"
    runner.write_text(
        "import json, os\n"
        "print(json.dumps({'leaked': os.environ.get('MISTRAL_API_KEY'), 'has_path': bool(os.environ.get('PATH'))}))\n",
        encoding="utf-8",
    )
    runtime = ProfilePipelineRuntime(root=tmp_path)
    result = runtime._inference_local_exec(
        {
            "kind": "local_exec",
            "model_path": str(model),
            "argv": [sys.executable, str(runner)],
            "response_content": "json_string",
            "timeout_seconds": 10,
        },
        {"system": "system", "user": "user"},
    )
    assert result["payload"] == {"leaked": None, "has_path": True}


def test_profile_persistence_rejects_literal_credential_values(tmp_path: Path) -> None:
    runtime = ProfilePipelineRuntime(root=tmp_path)
    profile = _profile()
    profile["inference"] = {"kind": "remote_api", "api_key": "literal-secret"}
    with pytest.raises(PipelineFault, match="EMBEDDED_SECRET_VALUE_FORBIDDEN"):
        runtime.install_profile(str(tmp_path / "entity.db"), profile)
