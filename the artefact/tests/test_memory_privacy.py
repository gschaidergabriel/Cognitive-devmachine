import hashlib
import json
import pytest

from clayverse.graph import ClayGraphProjection
from clayverse.identity import IdentityRouter
from clayverse.memory import MemoryManager
from clayverse.retrieval import WorldAssembler
from clayverse.store import UnifiedDB


@pytest.fixture
def db(tmp_path):
    d = UnifiedDB(tmp_path / "unified.db")
    yield d
    d.close()


def test_old_conversation_is_really_compressed_and_collision_uses_extracted_fragments(db):
    router = IdentityRouter(db, {"g": "gabriel", "a": "andreas"})
    guid, gsid = router.resolve("g")
    _, asid = router.resolve("a")
    mm = MemoryManager(db)
    original = "FACT: alpha is beta\nordinary opening words private heliotrope durable content"
    first_id = db.append_turn(gsid, guid, "user", original, resources=["repo:x"])
    for i in range(125):
        db.append_turn(gsid, guid, "user", f"filler {i} " + ("x " * 40))
    mm.compact(gsid)

    first = db.db.execute("SELECT * FROM turns WHERE turn_id=?", (first_id,)).fetchone()
    assert first["compression_generation"] == 5
    assert len(first["content"].split()) <= 2
    assert "heliotrope" not in first["content"]
    assert not db.db.execute(
        "SELECT 1 FROM durable_memory WHERE kind='source_archive' AND source_turn_id=?", (first_id,)
    ).fetchone()

    receipt = db.db.execute(
        "SELECT value,provenance FROM durable_memory WHERE kind='compression_receipt' AND source_turn_id=?",
        (first_id,),
    ).fetchone()
    assert receipt["value"] == hashlib.sha256(original.encode("utf-8")).hexdigest()
    assert json.loads(receipt["provenance"])["lossless_source_retained"] is False
    fact = db.db.execute(
        "SELECT value FROM durable_memory WHERE kind='fact' AND source_turn_id=?", (first_id,)
    ).fetchone()
    assert fact["value"] == "alpha is beta"

    world = WorldAssembler(db).assemble(asid, [])
    assert "heliotrope" not in json.dumps(world, sort_keys=True)

    collision = WorldAssembler(db).assemble(asid, ["repo:x"])
    item = collision["cross_session_collision"][0]
    assert "heliotrope" not in item["content"]
    assert item["retrieval_fidelity"] == "compressed_with_extracted_fragments"
    assert {x["value"] for x in item["extracted_fragments"]} == {"alpha is beta"}


def test_recompression_does_not_duplicate_extracted_semantic_memory(db):
    router = IdentityRouter(db, {"g": "gabriel"})
    uid, sid = router.resolve("g")
    mm = MemoryManager(db)
    turn_id = db.append_turn(sid, uid, "user", "DECISION: keep one durable copy")
    for i in range(50):
        db.append_turn(sid, uid, "user", f"filler {i}")
    mm.compact(sid)
    for i in range(80):
        db.append_turn(sid, uid, "user", f"later {i}")
    mm.compact(sid)
    count = db.db.execute(
        "SELECT COUNT(*) FROM durable_memory WHERE kind='decision' AND source_turn_id=?",
        (turn_id,),
    ).fetchone()[0]
    assert count == 1


def test_compression_receipt_is_not_a_claygraph_semantic_node(db):
    router = IdentityRouter(db, {"g": "gabriel"})
    uid, sid = router.resolve("g")
    turn_id = db.append_turn(sid, uid, "user", "FACT: visible semantic fact")
    mm = MemoryManager(db)
    for i in range(25):
        db.append_turn(sid, uid, "user", f"filler {i}")
    mm.compact(sid)

    ClayGraphProjection(db).rebuild()
    labels = [r["label"] for r in db.db.execute("SELECT label FROM graph_nodes")]
    source_ids = [r["source_id"] for r in db.db.execute("SELECT source_id FROM graph_nodes")]
    assert "visible semantic fact" in labels
    receipt_id = db.db.execute(
        "SELECT memory_id FROM durable_memory WHERE kind='compression_receipt' AND source_turn_id=?",
        (turn_id,),
    ).fetchone()[0]
    assert receipt_id not in source_ids
