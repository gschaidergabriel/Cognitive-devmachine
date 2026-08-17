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


def test_lossless_archive_is_private_until_explicit_resource_collision(db):
    router = IdentityRouter(db, {"g": "gabriel", "a": "andreas"})
    guid, gsid = router.resolve("g")
    _, asid = router.resolve("a")
    mm = MemoryManager(db)
    original = "ordinary opening words private heliotrope durable content"
    first_id = db.append_turn(gsid, guid, "user", original, resources=["repo:x"])
    for i in range(125):
        db.append_turn(gsid, guid, "user", f"filler {i} " + ("x " * 40))
    mm.compact(gsid)

    first = db.db.execute("SELECT * FROM turns WHERE turn_id=?", (first_id,)).fetchone()
    assert first["compression_generation"] == 5
    assert "heliotrope" not in first["content"]
    archive = db.db.execute(
        "SELECT value,provenance FROM durable_memory WHERE kind='source_archive' AND source_turn_id=?",
        (first_id,),
    ).fetchone()
    assert archive["value"] == original
    assert json.loads(archive["provenance"])["lossless"] is True

    world = WorldAssembler(db).assemble(asid, [])
    assert "heliotrope" not in json.dumps(world, sort_keys=True)

    collision = WorldAssembler(db).assemble(asid, ["repo:x"])
    assert len(collision["cross_session_collision"]) == 1
    assert collision["cross_session_collision"][0]["content"] == original
    assert collision["cross_session_collision"][0]["retrieval_fidelity"] == "source_archive"


def test_source_archive_is_not_a_claygraph_semantic_node(db):
    router = IdentityRouter(db, {"g": "gabriel"})
    uid, sid = router.resolve("g")
    turn_id = db.append_turn(sid, uid, "user", "private archived zebra")
    db.add_memory(
        "source_archive", sid, "private archived zebra", turn_id, uid,
        {"archive": "pre-compression-v1", "lossless": True},
    )
    db.add_memory("fact", uid, "visible semantic fact", turn_id, uid, {"extractor": "test"})

    ClayGraphProjection(db).rebuild()
    labels = [r["label"] for r in db.db.execute("SELECT label FROM graph_nodes")]
    source_ids = [r["source_id"] for r in db.db.execute("SELECT source_id FROM graph_nodes")]
    assert "private archived zebra" not in labels
    assert "visible semantic fact" in labels
    archive_id = db.db.execute(
        "SELECT memory_id FROM durable_memory WHERE kind='source_archive'"
    ).fetchone()[0]
    assert archive_id not in source_ids
