from clayverse.hyperposition import HyperpositionProjector
from clayverse.identity import IdentityRouter
from clayverse.needle import NeedleRouter
from clayverse.store import UnifiedDB
from clayverse.turn_lifecycle import TurnLifecycle


def test_hyperposition_preserves_conflicting_facets_without_truth_or_authority():
    world = {
        "durable_memory": [
            {"kind": "fact", "subject": "project:x", "value": "branch-a", "source_turn_id": "t1", "user_id": "gabriel", "ts": 1.0, "provenance": {"source": "a"}},
            {"kind": "fact", "subject": "project:x", "value": "branch-b", "source_turn_id": "t2", "user_id": "gabriel", "ts": 2.0, "provenance": {"source": "b"}},
        ]
    }
    readouts = HyperpositionProjector.from_world(world)
    assert len(readouts) == 1
    hp = readouts[0]
    assert hp["alternative_count"] == 2
    assert {x["value"] for x in hp["facets"]} == {"branch-a", "branch-b"}
    assert hp["truth_promoted"] is False
    assert hp["effect_authority"] is False


def test_single_value_is_not_invented_as_hyperposition():
    world = {"durable_memory": [{"kind": "fact", "subject": "x", "value": "only", "ts": 1.0}]}
    assert HyperpositionProjector.from_world(world) == []


def test_needle_escalates_collision_and_unresolved_alternatives_without_authority():
    world = {"cross_session_collision": [{"turn_id": "other"}], "durable_memory": []}
    decision = NeedleRouter.analyze("change file:x.py", world, [{"relation_id": "h"}], ["file:x.py"])
    assert decision["route"] == "deep_shared_state"
    assert decision["collision_risk"] is True
    assert decision["unresolved_hyperposition"] is True
    assert decision["effect_candidate"] is True
    assert decision["context_budget"] >= 16000


def test_real_turn_path_emits_hyperposition_and_needle(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        IdentityRouter(db, {})
        db.add_memory("fact", "gabriel", "candidate-a", None, "gabriel", {"source": "a"})
        db.add_memory("fact", "gabriel", "candidate-b", None, "gabriel", {"source": "b"})
        life = TurnLifecycle(db, "gabriel", "session:gabriel")
        result = life.begin("inspect file:shared.py")
        assert result["hyperpositions"]
        assert result["hyperpositions"][0]["truth_promoted"] is False
        assert result["needle"]["route"] in {"deep_shared_state", "deep_local", "effect_aware", "direct_local"}
        assert result["generation"] == db.entity_generation()
        life.abort("test-end")
    finally:
        db.close()
