import json

from clayverse.agency import AgencyView
from clayverse.autonomy import AutonomyController
from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "agency.db")
    IdentityRouter(db, {"g": "gabriel", "a": "andreas"})
    return db


def _goal(db, user_id: str, text: str):
    turn_id = db.append_turn(f"session:{user_id}", user_id, "user", text)
    return AutonomyController(db).create_goal_from_turn(
        user_id,
        f"session:{user_id}",
        turn_id,
        completion_mode="user_ack",
    )


def test_agency_identity_is_server_state_not_prompt_or_device_roleplay(tmp_path):
    db = _db(tmp_path)
    snap = AgencyView(db).snapshot(user_id="gabriel")
    profile = snap["profile"]
    assert snap["authority"] == "UnifiedDB"
    assert profile["identity_mode"] == "PERSISTENT_GOAL_AGENT"
    assert profile["substrate_anchor"] == "SERVER_UNIFIEDDB"
    assert profile["behavior_mode"] == "PROACTIVE_GROUNDED"
    rendered = json.dumps(snap, sort_keys=True).lower()
    assert "usb" not in rendered
    assert "smart contract" not in rendered
    assert "crypto" not in rendered
    assert "model assertions" in rendered
    db.close()


def test_goal_objective_and_view_are_canonical_and_user_scoped(tmp_path):
    db = _db(tmp_path)
    _goal(db, "gabriel", "private-g-objective")
    _goal(db, "andreas", "private-a-objective")

    gs = json.dumps(AgencyView(db).snapshot(user_id="gabriel"), sort_keys=True)
    ass = json.dumps(AgencyView(db).snapshot(user_id="andreas"), sort_keys=True)
    assert "private-g-objective" in gs
    assert "private-a-objective" not in gs
    assert "private-a-objective" in ass
    assert "private-g-objective" not in ass
    db.close()


def test_concept_prototype_final_are_derived_not_second_state_authority(tmp_path):
    db = _db(tmp_path)
    goal = _goal(db, "gabriel", "Build a bounded module")
    snap = AgencyView(db).snapshot(user_id="gabriel")
    projected = snap["autonomy"]["goals"][0]["delivery_milestones"]
    assert projected == {
        "authority": "DERIVED_FROM_AUTONOMY_AND_EFFECT_STATE",
        "CONCEPT": "ACTIVE",
        "PROTOTYPE": "PENDING",
        "FINAL": "PENDING",
    }
    assert snap["autonomy"]["goals"][0]["goal_id"] == goal["goal_id"]
    assert db.db.execute("SELECT value FROM meta WHERE key='autonomy_state_v1'").fetchone() is not None
    assert db.db.execute("SELECT value FROM meta WHERE key='agency_profile_v1'").fetchone() is not None
    db.close()


def test_ers_is_telemetry_and_state_noop_cannot_game_it(tmp_path):
    db = _db(tmp_path)
    db.record_effect(None, "gabriel", "state.noop", "noop", db.entity_generation(), "VERIFIED", outcome={"ok": True})
    metrics = AgencyView(db).metrics("gabriel")
    assert metrics["verified_effect_steps"] == 0
    assert metrics["failed_effect_steps"] == 0
    assert metrics["ers"] == 0.0
    assert metrics["ers_role"] == "telemetry_only_not_authority"
    db.close()
