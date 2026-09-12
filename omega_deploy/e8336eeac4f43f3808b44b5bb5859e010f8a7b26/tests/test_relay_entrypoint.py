from pathlib import Path
import sqlite3
import tempfile

from omega.relay_entrypoint import RECOVERY_REASON, quarantine_inflight
from omega.unified_store import UnifiedStore, now


ROOT = Path(__file__).resolve().parents[1]


def test_relay_restart_quarantines_inflight_effect_without_replay():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "omega.db"
        store = UnifiedStore(db, ROOT / "schema")
        t = now()
        with store.connect() as con:
            con.execute(
                """
                INSERT INTO effect_intent(
                  effect_id,frame_id,organ_id,owner_id,machine_id,request_digest,payload_json,
                  authority_state,dispatch_state,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    "effect_crash", "frame_crash", "host:ai-core-node", "gabriel", "ai-core-node",
                    "request-digest", "{}", "ALLOW", "DISPATCHING", t, t,
                ),
            )
            con.execute(
                """
                INSERT INTO relay_ledger(
                  effect_id,organ_id,command_id,state,attempt_count,command_digest,receipt_digest,
                  last_error,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    "effect_crash", "host:ai-core-node", "omega-crash", "DISPATCHING", 1,
                    "command-digest", None, None, t, t,
                ),
            )

        quarantined = quarantine_inflight(db)
        assert quarantined == ["effect_crash"]

        with store.connect() as con:
            relay = con.execute(
                "SELECT state,attempt_count,last_error FROM relay_ledger WHERE effect_id='effect_crash'"
            ).fetchone()
            effect = con.execute(
                "SELECT dispatch_state FROM effect_intent WHERE effect_id='effect_crash'"
            ).fetchone()

        assert relay[0] == "UNKNOWN"
        assert relay[1] == 1
        assert relay[2] == RECOVERY_REASON
        assert effect[0] == "UNKNOWN"

        # Recovery is idempotent and never increments attempts or reopens UNKNOWN.
        assert quarantine_inflight(db) == []
        with store.connect() as con:
            relay2 = con.execute(
                "SELECT state,attempt_count,last_error FROM relay_ledger WHERE effect_id='effect_crash'"
            ).fetchone()
        assert tuple(relay2) == ("UNKNOWN", 1, RECOVERY_REASON)


def test_relay_recovery_allows_fresh_partial_database_to_bootstrap():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "omega.db"
        sqlite3.connect(db).close()
        assert quarantine_inflight(db) == []
