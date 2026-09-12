import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from omega.unified_store import EffectIdentityConflict, UnifiedStore


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


def test_effect_id_cannot_be_rebound_to_different_request(tmp_path):
    store = UnifiedStore(tmp_path / "omega.db", ROOT / "schema")
    intent = {
        "schema":"OMEGA_GRID_EFFECT_INTENT/v1","effect_id":"effect_fixed","frame_id":"frame_1",
        "organ_id":"host:ai-core-node","authority":"NOT_YET_GRANTED",
        "task":{"effect":{"op":"status"}},
    }
    store.record_effect_intent(intent, owner_id="gabriel", machine_id="ai-core-node")
    changed = json.loads(json.dumps(intent))
    changed["task"]["effect"] = {"op":"read_file","path":"/tmp/other"}
    with pytest.raises(EffectIdentityConflict, match="EFFECT_ID_REBIND_CONFLICT"):
        store.record_effect_intent(changed, owner_id="gabriel", machine_id="ai-core-node")


def test_atomic_relay_claim_allows_exactly_one_concurrent_attempt(tmp_path):
    store = UnifiedStore(tmp_path / "omega.db", ROOT / "schema")
    intent = {
        "schema":"OMEGA_GRID_EFFECT_INTENT/v1","effect_id":"effect_race","frame_id":"frame_race",
        "organ_id":"host:ai-core-node","authority":"NOT_YET_GRANTED",
        "task":{"effect":{"op":"status"}},
    }
    store.record_effect_intent(intent, owner_id="gabriel", machine_id="ai-core-node")

    def attempt() -> str:
        try:
            store.upsert_relay(
                effect_id="effect_race", organ_id="host:ai-core-node",
                state="DISPATCHING", increment_attempt=True,
            )
            return "CLAIMED"
        except EffectIdentityConflict as exc:
            assert "RELAY_DISPATCH_ALREADY_CLAIMED" in str(exc)
            return "BLOCKED"

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(lambda _: attempt(), range(16)))

    assert outcomes.count("CLAIMED") == 1
    assert outcomes.count("BLOCKED") == 15
    with store.connect() as con:
        row = con.execute(
            "SELECT state,attempt_count,organ_id FROM relay_ledger WHERE effect_id='effect_race'"
        ).fetchone()
    assert tuple(row) == ("DISPATCHING", 1, "host:ai-core-node")


def test_terminal_relay_state_cannot_be_reopened_as_new_attempt(tmp_path):
    store = UnifiedStore(tmp_path / "omega.db", ROOT / "schema")
    intent = {
        "schema":"OMEGA_GRID_EFFECT_INTENT/v1","effect_id":"effect_done","frame_id":"frame_done",
        "organ_id":"host:andreas-maco","authority":"NOT_YET_GRANTED",
        "task":{"effect":{"op":"status"}},
    }
    store.record_effect_intent(intent, owner_id="andreas", machine_id="andreas-maco")
    store.upsert_relay(
        effect_id="effect_done", organ_id="host:andreas-maco",
        state="DISPATCHING", increment_attempt=True,
    )
    store.upsert_relay(effect_id="effect_done", organ_id="host:andreas-maco", state="UNKNOWN")
    with pytest.raises(EffectIdentityConflict, match="RELAY_DISPATCH_ALREADY_CLAIMED:effect_done:UNKNOWN"):
        store.upsert_relay(
            effect_id="effect_done", organ_id="host:andreas-maco",
            state="DISPATCHING", increment_attempt=True,
        )
    with store.connect() as con:
        row = con.execute("SELECT state,attempt_count FROM relay_ledger WHERE effect_id='effect_done'").fetchone()
    assert tuple(row) == ("UNKNOWN", 1)


def test_unknown_relay_state_is_durable(tmp_path):
    store = UnifiedStore(tmp_path / "omega.db", ROOT / "schema")
    store.upsert_relay(effect_id="effect_u",organ_id="host:andreas-maco",state="UNKNOWN",increment_attempt=False,last_error="timeout")
    with store.connect() as con:
        row = con.execute("SELECT state,attempt_count,last_error FROM relay_ledger WHERE effect_id='effect_u'").fetchone()
    assert tuple(row) == ("UNKNOWN",0,"timeout")
