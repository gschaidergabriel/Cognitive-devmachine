import json

from clayverse.method_memory import METHOD_SCHEMA_VERSION, MethodMemoryManager, canonical_method_value
from clayverse.method_retrieval import MethodMemoryRetriever
from test_method_memory_promotion import PromotionDB, candidate_record


def promoted_fixture():
    db = PromotionDB()
    db.db.executemany(
        "INSERT INTO workspace_episodes(episode_id) VALUES(?)",
        [("episode:a",), ("episode:b",)],
    )
    evidence = db.add_memory("fact", "evidence", "A", None, "gabriel", {"source": "test"})
    manager = MethodMemoryManager(db)
    candidate_id = manager.admit(
        "framework_candidate",
        "causal discrimination",
        candidate_record(supporting_memory_ids=[evidence]),
        "turn:retrieval",
        "gabriel",
        {"source": "episode_abstraction", "extractor": "test"},
    )
    promotion = manager.promote(
        candidate_id,
        evaluation="held-out transfer succeeded",
        provenance={"source": "held_out_eval", "evaluator": "test"},
    )
    return db, manager, promotion


def test_stage_b_returns_only_verified_promoted_method_for_structural_match():
    db, manager, promotion = promoted_fixture()
    retriever = MethodMemoryRetriever(db)
    result = retriever.retrieve(
        problem_signature=candidate_record()["problem_signature"],
        user_id="gabriel",
        min_score=0.5,
    )
    assert result["receipt"]["status"] == "PRESENT"
    assert result["receipt"]["truth_authority"] is False
    assert result["receipt"]["effect_authority"] is False
    assert result["receipt"]["fact_status"] == "UNCHANGED"
    assert result["receipt"]["selected_count"] == 1
    item = result["items"][0]
    assert item["memory_id"] == promotion["promoted_memory_id"]
    assert item["structural_score"] == 1.0
    assert "value" not in item
    assert "facts" not in item


def test_stage_b_rejects_raw_forged_framework_without_real_promotion_lineage():
    db, manager, promotion = promoted_fixture()
    promoted = manager.decode_row(
        db.db.execute(
            "SELECT * FROM durable_memory WHERE memory_id=?",
            (promotion["promoted_memory_id"],),
        ).fetchone()
    )
    forged_provenance = {
        **promoted["provenance"],
        "promotion_receipt_id": "db:missing-receipt",
        "method_schema_version": METHOD_SCHEMA_VERSION,
    }
    forged_value = canonical_method_value("framework", promoted["value"], forged_provenance)
    db.add_memory(
        "framework",
        "forged exact match",
        forged_value,
        promoted["source_turn_id"],
        promoted["user_id"],
        forged_provenance,
    )
    retriever = MethodMemoryRetriever(db)
    result = retriever.retrieve(
        problem_signature=candidate_record()["problem_signature"],
        user_id="gabriel",
        min_score=0.5,
    )
    assert result["receipt"]["status"] == "PRESENT"
    assert result["receipt"]["validated_method_count"] == 1
    assert result["receipt"]["rejected_method_count"] == 1
    assert result["receipt"]["rejection_reasons"]["missing_promotion_source_or_receipt"] == 1
    assert [x["subject"] for x in result["items"]] == ["causal discrimination"]


def test_stage_b_undercovered_does_not_promote_weak_analogy_to_presence():
    db, _, _ = promoted_fixture()
    retriever = MethodMemoryRetriever(db)
    result = retriever.retrieve(
        problem_signature={
            "goal": ["schedule recurring event"],
            "constraint_shape": ["fully observed"],
            "evidence_shape": ["calendar slots"],
        },
        user_id="gabriel",
        min_score=0.5,
    )
    assert result["items"] == []
    assert result["receipt"]["validated_method_count"] == 1
    assert result["receipt"]["status"] == "UNDERCOVERED"
    assert result["receipt"]["fact_status"] == "UNCHANGED"


def test_stage_b_unknown_when_no_valid_promoted_methods_exist():
    db = PromotionDB()
    retriever = MethodMemoryRetriever(db)
    result = retriever.retrieve(
        problem_signature={"goal": ["identify causal fault"]},
        user_id="gabriel",
    )
    assert result["items"] == []
    assert result["receipt"]["status"] == "UNKNOWN"
    assert result["receipt"]["validated_method_count"] == 0


def test_stage_b_preserves_user_scope():
    db, _, _ = promoted_fixture()
    retriever = MethodMemoryRetriever(db)
    result = retriever.retrieve(
        problem_signature=candidate_record()["problem_signature"],
        user_id="andreas",
        min_score=0.0,
    )
    assert result["items"] == []
    assert result["receipt"]["status"] == "UNKNOWN"
