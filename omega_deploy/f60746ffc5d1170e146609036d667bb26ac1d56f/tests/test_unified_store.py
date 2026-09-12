import json
from pathlib import Path

from omega.unified_store import UnifiedStore


ROOT = Path(__file__).resolve().parents[1]


def test_schema_and_observation_roundtrip(tmp_path):
    store = UnifiedStore(tmp_path / "omega.db", ROOT / "schema")
    store.register_source({
        "source_id":"host:test","source_kind":"host_frankenstein","canonical_name":"Test Host",
        "owner_id":"test-owner","machine_id":"test-machine","metadata":{},
    })
    oid = store.record_observation(
        source_id="host:test", subject_id="service:x", payload={"state":"UP"},
        observed_at="2026-09-12T00:00:00+00:00", evidence_class="LIVE_READBACK",
        owner_id="test-owner", machine_id="test-machine",
    )
    with store.connect() as con:
        row = con.execute("SELECT observation_id,machine_id,evidence_class FROM observation WHERE observation_id=?",(oid,)).fetchone()
    assert row["machine_id"] == "test-machine"
    assert row["evidence_class"] == "LIVE_READBACK"


def test_effect_intent_is_idempotent(tmp_path):
    store = UnifiedStore(tmp_path / "omega.db", ROOT / "schema")
    intent = {
        "schema":"OMEGA_GRID_EFFECT_INTENT/v1","effect_id":"effect_1","frame_id":"frame_1",
        "organ_id":"host:ai-core-node","authority":"NOT_YET_GRANTED",
        "task":{"effect":{"op":"status"}},
    }
    store.record_effect_intent(intent, owner_id="gabriel", machine_id="ai-core-node")
    store.record_effect_intent(intent, owner_id="gabriel", machine_id="ai-core-node")
    with store.connect() as con:
        n = con.execute("SELECT count(*) FROM effect_intent WHERE effect_id='effect_1'").fetchone()[0]
    assert n == 1


def test_unknown_relay_state_is_durable(tmp_path):
    store = UnifiedStore(tmp_path / "omega.db", ROOT / "schema")
    store.upsert_relay(effect_id="effect_u",organ_id="host:andreas-maco",state="UNKNOWN",increment_attempt=True,last_error="timeout")
    with store.connect() as con:
        row = con.execute("SELECT state,attempt_count,last_error FROM relay_ledger WHERE effect_id='effect_u'").fetchone()
    assert tuple(row) == ("UNKNOWN",1,"timeout")
