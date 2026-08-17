import pytest

from clayverse.identity import IdentityRouter
from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import StaleGeneration, UnifiedDB


def _db(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    IdentityRouter(db, {})
    return db


def test_legacy_shadow_policy_remains_shadow_under_v3_code(tmp_path):
    db = _db(tmp_path)
    try:
        row = db.db.execute("SELECT mode,policy_version FROM retrieval_policy_state WHERE singleton=1").fetchone()
        assert row["mode"] == "SHADOW"
        assert int(row["policy_version"]) == 1
        assert MicroClayRetrieval(db).mode() == "SHADOW"
    finally:
        db.close()


def test_legacy_active_policy_cannot_drive_v3_adaptive_serving(tmp_path):
    db = _db(tmp_path)
    try:
        db.db.execute("UPDATE retrieval_policy_state SET mode='ACTIVE',policy_version=2 WHERE singleton=1")
        with pytest.raises(StaleGeneration, match="retrieval_policy_version"):
            MicroClayRetrieval(db).mode()
    finally:
        db.close()


def test_v3_active_policy_requires_explicit_matching_version(tmp_path):
    db = _db(tmp_path)
    try:
        db.db.execute(
            "UPDATE retrieval_policy_state SET mode='ACTIVE',policy_version=? WHERE singleton=1",
            (MicroClayRetrieval.POLICY_VERSION,),
        )
        assert MicroClayRetrieval.POLICY_VERSION == 3
        assert MicroClayRetrieval(db).mode() == "ACTIVE"
    finally:
        db.close()
