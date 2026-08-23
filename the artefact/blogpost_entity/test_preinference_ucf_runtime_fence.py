from __future__ import annotations

import hashlib
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
JSPACE_IMPL = ROOT / "research_entity" / "global" / "j-space" / "implementations"
for path in (TOOLS, JSPACE_IMPL):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime
import zero_inference_packet_v1 as packet_v1
import zero_workspace_capsule_v1 as capsule_v1


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def profile() -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "ucf-test",
        "inference": {"kind": "mock", "model": "candidate-only"},
        "personality": {
            "system_prompt": "candidate profile",
            "public_style": "test",
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
        "state_metrics": [],
        "gate": {
            "require_hash_echo": True,
            "require_evidence_per_section": True,
            "leak_patterns": [],
        },
    }


def compiled() -> dict:
    return {
        "ok": True,
        "canonical": {"personality_state": {}},
        "personality_state": {},
        "packet": {"events": []},
        "allowed_evidence_refs": [],
        "source_count": 0,
        "canonical_state_hash": digest("canonical-state"),
        "packet_hash": digest("source-packet"),
    }


def fabric_admitter(request: dict) -> dict:
    capsule = capsule_v1.compile_workspace_capsule(
        entity_generation=request["generation"],
        causal_turn_id="turn-ucf-test",
        task_text=request["task_text"],
        zero_identity_digest=digest("zero-identity"),
        grf_digest=digest("grf"),
        hyperposition_digest=digest("hyperposition"),
        local_model_digest=digest("local-model"),
        jacobian_lens_digest=digest("jacobian-lens"),
        workspace_digest=digest("workspace"),
        selected_workspace_slots=["slot:one"],
        contradiction_state="NONE_OBSERVED",
        provenance_refs=["unifieddb:test"],
        required_zero_mode="ZERO",
    )
    packet = packet_v1.compile_packet(
        capsule,
        target_engine_class="ADAPTIVE_BACKEND",
        jspace_mode="PLAIN_COMPATIBILITY",
    )
    return {
        "zero_workspace_capsule": capsule,
        "zero_inference_packet": packet,
        "boot_binding_receipt_digest": digest("boot-binding"),
        "inference": dict(request["configured_inference"]),
        "system": request["system"],
        "user": request["user"],
        "jspace_measurement_refs": [],
        "gwt_selection_refs": ["slot:one"],
        "origin_trigger": "go",
    }


def provider(request: dict) -> dict:
    return {
        "title": "candidate",
        "intro": "candidate",
        "sections": [],
        "thread": "candidate continuity",
        "hypotheses": [],
        "canonical_state_hash_seen": digest("canonical-state"),
        "packet_hash_seen": digest("source-packet"),
    }


def setup_runtime(tmp_path: Path) -> tuple[ProfilePipelineRuntime, str, dict, dict, dict]:
    entity_db = "entity.sqlite"
    runtime = ProfilePipelineRuntime(
        root=tmp_path,
        provider_override=provider,
        cognitive_fabric_admitter=fabric_admitter,
    )
    runtime.import_profile(entity_db, profile())
    loaded = runtime._pipeline_profile_read({"entity_db": entity_db})
    assert loaded["ok"]
    active_profile = loaded["profile"]
    previous = {"generation": 0, "continuity": {}}
    comp = compiled()
    prompt = runtime._pipeline_build_prompt(
        {"profile": active_profile, "previous": previous, "data": comp}
    )
    assert prompt["ok"]
    return runtime, entity_db, active_profile, previous, {"compiled": comp, "prompt": prompt}


def admit(runtime: ProfilePipelineRuntime, entity_db: str, active_profile: dict, previous: dict, data: dict) -> dict:
    admitted = runtime._pipeline_cognitive_fabric_admit(
        {
            "entity_db": entity_db,
            "source_db": "unused.sqlite",
            "profile": active_profile,
            "previous": previous,
            "data": data,
        }
    )
    assert admitted["ok"], admitted
    return admitted


def inference_payload(admitted: dict) -> dict:
    return {
        "inference": admitted["inference"],
        "system": admitted["system"],
        "user": admitted["user"],
        "inference_packet_digest": admitted["inference_packet_digest"],
        "cognitive_fabric_receipt_digest": admitted["cognitive_fabric_receipt_digest"],
        "secret_file": "",
    }


def test_direct_inference_without_admission_fails_closed(tmp_path: Path) -> None:
    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    result = runtime._inference_generate(
        {
            "inference": {"kind": "mock", "model": "candidate-only"},
            "system": "x",
            "user": "y",
            "inference_packet_digest": digest("fake-packet"),
            "cognitive_fabric_receipt_digest": digest("fake-receipt"),
        }
    )
    assert not result["ok"]
    assert "ADMISSION_UNKNOWN_OR_RESTARTED" in result["error"]


def test_valid_admission_is_one_shot_through_inference_gate_and_commit(tmp_path: Path) -> None:
    runtime, entity_db, active_profile, previous, data = setup_runtime(tmp_path)
    admitted = admit(runtime, entity_db, active_profile, previous, data)
    infer = inference_payload(admitted)

    generated = runtime._inference_generate(dict(infer))
    assert generated["ok"], generated
    replay = runtime._inference_generate(dict(infer))
    assert not replay["ok"]
    assert "ALREADY_CONSUMED" in replay["error"]

    gate = runtime._pipeline_gate(
        {
            "profile": active_profile,
            "previous": previous,
            "data": {
                "generated": generated,
                "compiled": data["compiled"],
                "prompt": data["prompt"],
                "cognitive_fabric": admitted,
            },
        }
    )
    assert gate["ok"], gate
    committed = runtime._pipeline_commit(
        {
            "entity_db": entity_db,
            "source_db": "unused.sqlite",
            "profile": active_profile,
            "previous": previous,
            "data": {
                "gated": gate,
                "compiled": data["compiled"],
                "collected": {"consume": [], "next_cursors": {}},
                "generated": generated,
                "cognitive_fabric": admitted,
            },
        }
    )
    assert committed["ok"], committed
    assert committed["generation"] == 1
    assert admitted["cognitive_fabric_receipt_digest"] not in runtime._active_cognitive_admissions


def test_restart_cannot_reuse_old_preinference_ticket(tmp_path: Path) -> None:
    runtime, entity_db, active_profile, previous, data = setup_runtime(tmp_path)
    admitted = admit(runtime, entity_db, active_profile, previous, data)
    restarted = ProfilePipelineRuntime(
        root=tmp_path,
        provider_override=provider,
        cognitive_fabric_admitter=fabric_admitter,
    )
    result = restarted._inference_generate(inference_payload(admitted))
    assert not result["ok"]
    assert "ADMISSION_UNKNOWN_OR_RESTARTED" in result["error"]


def test_generation_change_after_admission_fails_before_inference(tmp_path: Path) -> None:
    runtime, entity_db, active_profile, previous, data = setup_runtime(tmp_path)
    admitted = admit(runtime, entity_db, active_profile, previous, data)
    db = sqlite3.connect(tmp_path / entity_db)
    db.execute("UPDATE entity_state SET generation=1 WHERE id=1")
    db.commit()
    db.close()
    result = runtime._inference_generate(inference_payload(admitted))
    assert not result["ok"]
    assert "STALE_GENERATION" in result["error"]


def test_digest_decorated_raw_inference_bypass_is_rejected(tmp_path: Path) -> None:
    runtime, _, _, _, _ = setup_runtime(tmp_path)
    result = runtime._inference_generate(
        {
            "inference": {"kind": "mock", "model": "candidate-only"},
            "system": "raw-system",
            "user": "raw-user",
            "inference_packet_digest": digest("looks-valid-packet"),
            "cognitive_fabric_receipt_digest": digest("looks-valid-receipt"),
        }
    )
    assert not result["ok"]
    assert "ADMISSION_UNKNOWN_OR_RESTARTED" in result["error"]
