from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import mini_cognitive_admission_v1 as admission
import miniunifieddb_active_turn_v1 as active_turn
import miniunifieddb_cognition_store_v1 as store


def h(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def build_fixture(*, route_patch: dict | None = None):
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE entity_state(id INTEGER PRIMARY KEY,generation INTEGER NOT NULL)")
    db.execute("INSERT INTO entity_state VALUES(1,3)")
    store.install_schema(db)
    active_turn.install_schema(db)

    inference = {
        "kind": "local_exec_json",
        "model": "fixture-model",
        "runner": "fixture-runner",
    }
    route = {
        "schema": admission.ROUTE_SCHEMA,
        "target_engine_class": "BUNDLED_LOCAL_08B",
        "jspace_mode": "LOCAL_OBSERVE_ONLY",
        "inference_config_digest": admission.packet_v2.sha256_obj(inference),
        "allowed_inference_kinds": ["local_exec_json"],
        "candidate_only": True,
        "direct_state_authority": False,
        "direct_effect_authority": False,
    }
    if route_patch:
        route.update(route_patch)

    digests: dict[str, str] = {}
    for field_name, object_kind in store.BOOT_FIELD_KINDS.items():
        digest = h("object:" + field_name)
        digests[field_name] = digest
        payload = {
            "identity": field_name,
            "classification": "TEST_FIXTURE_ONLY",
        }
        if field_name == "jspace_profile_digest":
            payload["cognitive_route_capability"] = route
        store.register_object(
            db,
            object_kind=object_kind,
            object_version="v1",
            object_digest=digest,
            digest_basis="EXTERNAL_BYTES",
            payload=payload,
            provenance_refs=["test:object:" + field_name],
        )
        store.admit_object(
            db,
            object_kind=object_kind,
            object_version="v1",
            object_digest=digest,
            entity_generation=3,
            admission_receipt_digest=h("admission:" + field_name),
        )

    boot = store.admit_boot_binding(
        db,
        entity_generation=3,
        provenance_refs=["test:boot"],
        **digests,
    )
    task = "preserve exact causal identity"
    turn = store.bind_turn(
        db,
        entity_generation=3,
        causal_turn_id="turn-3-a",
        boot_binding_digest=boot["binding_digest"],
        task_text=task,
        workspace_digest=h("workspace"),
        selected_workspace_slots=["slot-a", "slot-b"],
        contradiction_state="NONE",
        provenance_refs=["test:turn"],
        required_zero_mode="ZERO_FULL",
    )
    active = active_turn.activate_bound_turn(
        db,
        entity_generation=3,
        causal_turn_id="turn-3-a",
        task_text=task,
        expected_turn_binding_digest=turn["binding_digest"],
        provenance_refs=["test:active"],
    )
    db.commit()

    profile_base = {
        "profile_id": "fixture-profile",
        "inference": inference,
    }
    profile = {
        **profile_base,
        "_runtime_profile_snapshot": {
            "profile_id": "fixture-profile",
            "profile_hash": admission.sha256_obj(profile_base),
        },
    }
    invocation = {
        "expected_generation": 3,
        "causal_turn_id": "turn-3-a",
        "task_text": task,
        "turn_binding_digest": turn["binding_digest"],
    }
    compiled = {
        "canonical_state_hash": h("canonical-state"),
        "packet_hash": h("source-packet"),
    }
    prompt = {"system": "system-context", "user": "user-context"}
    return db, profile, invocation, compiled, prompt, active


def run_fixture(db, profile, invocation, compiled, prompt):
    return admission.admit(
        db,
        previous={"generation": 3},
        compiled=compiled,
        prompt=prompt,
        profile=profile,
        invocation=invocation,
    )


def test_exact_bound_admission_compiles_capsule_packet_and_receipt():
    db, profile, invocation, compiled, prompt, _ = build_fixture()
    result = run_fixture(db, profile, invocation, compiled, prompt)
    assert result["ok"] is True
    assert result["generation"] == 3
    assert result["causal_turn_id"] == "turn-3-a"
    assert result["inference"] == profile["inference"]
    assert result["system"] == prompt["system"]
    assert result["user"] == prompt["user"]
    assert result["inference_packet"]["target_engine_class"] == "BUNDLED_LOCAL_08B"
    assert result["inference_packet"]["jspace_mode"] == "LOCAL_OBSERVE_ONLY"
    assert result["inference_packet_digest"] == result["inference_packet"]["packet_digest"]
    assert result["workspace_capsule"]["task"]["text"] == invocation["task_text"]
    assert result["authority"]["durable_state"] == "MiniUnifiedDB"
    assert result["authority"]["direct_effect_authority"] is False
    db.close()


def test_selector_cannot_smuggle_workspace_or_engine_authority():
    db, profile, invocation, compiled, prompt, _ = build_fixture()
    poisoned = dict(invocation)
    poisoned["workspace_digest"] = h("caller-workspace")
    with pytest.raises(admission.CognitiveAdmissionError, match="INVOCATION_FIELDS_MISMATCH"):
        run_fixture(db, profile, poisoned, compiled, prompt)
    db.close()


def test_selector_must_match_active_same_generation_turn():
    db, profile, invocation, compiled, prompt, _ = build_fixture()
    poisoned = dict(invocation)
    poisoned["causal_turn_id"] = "turn-3-other"
    with pytest.raises(admission.CognitiveAdmissionError, match="SELECTOR_CAUSAL_TURN_MISMATCH"):
        run_fixture(db, profile, poisoned, compiled, prompt)
    db.close()


def test_route_capability_binds_exact_inference_config_not_provider_name():
    db, profile, invocation, compiled, prompt, _ = build_fixture(
        route_patch={"inference_config_digest": h("different-inference-config")}
    )
    with pytest.raises(admission.CognitiveAdmissionError, match="ROUTE_INFERENCE_CONFIG_MISMATCH"):
        run_fixture(db, profile, invocation, compiled, prompt)
    db.close()


def test_local_08b_cannot_claim_plain_or_external_jspace_mode():
    db, profile, invocation, compiled, prompt, _ = build_fixture(
        route_patch={"jspace_mode": "PLAIN_COMPATIBILITY"}
    )
    with pytest.raises(admission.CognitiveAdmissionError, match="ROUTE_LOCAL_08B_JSPACE_MODE_INVALID"):
        run_fixture(db, profile, invocation, compiled, prompt)
    db.close()


def test_route_capability_cannot_grant_direct_state_authority():
    db, profile, invocation, compiled, prompt, _ = build_fixture(
        route_patch={"direct_state_authority": True}
    )
    with pytest.raises(admission.CognitiveAdmissionError, match="ROUTE_STATE_AUTHORITY_FORBIDDEN"):
        run_fixture(db, profile, invocation, compiled, prompt)
    db.close()


def test_persisted_jspace_payload_mutation_cannot_keep_old_admission_identity():
    db, profile, invocation, compiled, prompt, _ = build_fixture()
    digest = db.execute(
        "SELECT jspace_profile_digest FROM mini_cognition_boot_bindings WHERE entity_generation=3"
    ).fetchone()[0]
    row = db.execute(
        "SELECT object_version,payload_json FROM mini_cognition_objects WHERE object_kind='JSPACE_PROFILE' AND object_digest=?",
        (digest,),
    ).fetchone()
    payload = json.loads(row[1])
    payload["cognitive_route_capability"]["jspace_mode"] = "FULL_LOCAL_LATENT"
    db.execute(
        "UPDATE mini_cognition_objects SET payload_json=? WHERE object_kind='JSPACE_PROFILE' AND object_version=? AND object_digest=?",
        (admission.canonical_json(payload), row[0], digest),
    )
    db.commit()
    with pytest.raises(admission.CognitiveAdmissionError, match="ROUTE_JSPACE_PROFILE_PAYLOAD_DIGEST_MISMATCH"):
        run_fixture(db, profile, invocation, compiled, prompt)
    db.close()


def test_stale_generation_cannot_reuse_active_turn_admission():
    db, profile, invocation, compiled, prompt, _ = build_fixture()
    db.execute("UPDATE entity_state SET generation=4 WHERE id=1")
    db.commit()
    with pytest.raises(ValueError, match="STALE_GENERATION"):
        run_fixture(db, profile, invocation, compiled, prompt)
    db.close()
