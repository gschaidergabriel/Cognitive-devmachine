import pytest

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


def test_clerk_subject_binding_survives_restart_and_blocks_identity_swap(tmp_path):
    path = tmp_path / "unified.db"
    mapping = {"clerk-g": "gabriel", "clerk-a": "andreas"}

    db = UnifiedDB(path)
    router = IdentityRouter(db, mapping)
    assert router.resolve("clerk-g")[0] == "gabriel"
    assert router.resolve("clerk-a")[0] == "andreas"
    persisted = {
        row["user_id"]: row["clerk_subject"]
        for row in db.db.execute("SELECT user_id,clerk_subject FROM users")
    }
    assert persisted == {"gabriel": "clerk-g", "andreas": "clerk-a"}
    IdentityRouter(db, mapping)
    db.close()

    db = UnifiedDB(path)
    IdentityRouter(db, mapping)
    with pytest.raises(PermissionError, match="already bound"):
        IdentityRouter(db, {"clerk-g": "andreas", "clerk-a": "gabriel"})
    with pytest.raises(PermissionError, match="already bound"):
        IdentityRouter(db, {"clerk-g2": "gabriel"})
    db.close()


def test_clerk_subject_mapping_rejects_duplicate_canonical_target(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    with pytest.raises(PermissionError, match="multiple Clerk subjects"):
        IdentityRouter(db, {"clerk-g-1": "gabriel", "clerk-g-2": "gabriel"})
    db.close()
