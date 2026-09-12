import datetime as dt
from pathlib import Path
import tempfile

from omega.supervisor import Supervisor
from omega.unified_store import UnifiedStore, now


ROOT = Path(__file__).resolve().parents[1]


def test_supervisor_detects_only_stale_host_dispatches():
    with tempfile.TemporaryDirectory() as td:
        runtime = Path(td) / "state"
        supervisor = Supervisor(runtime, ROOT)
        store = UnifiedStore(supervisor.db_path, ROOT / "schema")
        old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=900)).isoformat()
        current = now()
        with store.connect() as con:
            con.execute(
                """
                INSERT INTO relay_ledger(
                  effect_id,organ_id,command_id,state,attempt_count,command_digest,receipt_digest,
                  last_error,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                ("effect_local", "omega-vps", None, "DISPATCHING", 1, None, None, None, old, old),
            )
            con.execute(
                """
                INSERT INTO relay_ledger(
                  effect_id,organ_id,command_id,state,attempt_count,command_digest,receipt_digest,
                  last_error,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                ("effect_host", "host:ai-core-node", "omega-host", "DISPATCHING", 1, None, None, None, old, old),
            )
            con.execute(
                """
                INSERT INTO relay_ledger(
                  effect_id,organ_id,command_id,state,attempt_count,command_digest,receipt_digest,
                  last_error,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                ("effect_done", "host:andreas-maco", "omega-done", "COMPLETED", 1, None, "receipt", None, current, current),
            )

        dispatch = supervisor.oldest_host_dispatch()
        assert dispatch is not None
        assert dispatch["effect_id"] == "effect_host"
        assert dispatch["organ_id"] == "host:ai-core-node"
        assert dispatch["age_seconds"] >= 850
