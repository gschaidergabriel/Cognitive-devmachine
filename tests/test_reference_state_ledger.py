import json

import pytest

from research_entity.harness.reference_state_ledger import (
    Mutation,
    StateLedger,
    StaleEpoch,
    TamperDetected,
)


PROV = {
    "origin_actor": "chatgpt-secondary",
    "research_entity": "frank-project-global-research-entity",
    "target": "FRANK H1 reference harness",
    "source_ref": "H-WP-02",
}


def ledger(tmp_path):
    return StateLedger(tmp_path / "ledger.sqlite")


def test_deterministic_state_hash_independent_of_mutation_order(tmp_path):
    a = ledger(tmp_path / "a")
    b = ledger(tmp_path / "b")
    muts1 = [
        Mutation("self", "name", "Frank"),
        Mutation("goal", "primary", {"x": 1, "y": 2}),
    ]
    muts2 = list(reversed(muts1))
    ra = a.commit(
        event_id="e1", idempotency_key="k1", base_epoch=0, event_type="TEST",
        mutations=muts1, provenance=PROV, committed_at="2026-08-09T00:00:00Z", writer_node="test"
    )
    rb = b.commit(
        event_id="e2", idempotency_key="k2", base_epoch=0, event_type="TEST",
        mutations=muts2, provenance=PROV, committed_at="2026-08-09T00:00:00Z", writer_node="test"
    )
    assert ra["root_hash"] == rb["root_hash"]


def test_stale_epoch_rejected_and_first_commit_survives(tmp_path):
    l1 = ledger(tmp_path)
    l2 = StateLedger(tmp_path / "ledger.sqlite")
    l1.commit(
        event_id="e1", idempotency_key="k1", base_epoch=0, event_type="TEST",
        mutations=[Mutation("world", "x", 1)], provenance=PROV,
        committed_at="2026-08-09T00:00:00Z", writer_node="one"
    )
    with pytest.raises(StaleEpoch):
        l2.commit(
            event_id="e2", idempotency_key="k2", base_epoch=0, event_type="TEST",
            mutations=[Mutation("world", "x", 2)], provenance=PROV,
            committed_at="2026-08-09T00:00:01Z", writer_node="two"
        )
    assert l1.read("world", "x")["value"] == 1


def test_idempotency_does_not_increment_epoch(tmp_path):
    l = ledger(tmp_path)
    kwargs = dict(
        event_id="e1", idempotency_key="same", base_epoch=0, event_type="TEST",
        mutations=[Mutation("world", "x", 1)], provenance=PROV,
        committed_at="2026-08-09T00:00:00Z", writer_node="one"
    )
    first = l.commit(**kwargs)
    second = l.commit(**kwargs)
    assert first["epoch"] == 1
    assert second["status"] == "IDEMPOTENT_REPLAY"
    assert l.head()["epoch"] == 1


def test_explicit_epistemic_states_preserved(tmp_path):
    l = ledger(tmp_path)
    l.commit(
        event_id="e1", idempotency_key="k1", base_epoch=0, event_type="TEST",
        mutations=[
            Mutation("memory", "a", None, "UNKNOWN"),
            Mutation("memory", "b", ["left", "right"], "CONFLICT"),
            Mutation("memory", "c", "old", "REVOKED"),
        ],
        provenance=PROV, committed_at="2026-08-09T00:00:00Z", writer_node="one"
    )
    assert l.read("memory", "a")["epistemic_state"] == "UNKNOWN"
    assert l.read("memory", "b")["epistemic_state"] == "CONFLICT"
    assert l.read("memory", "c")["epistemic_state"] == "REVOKED"


def test_snapshot_roundtrip_preserves_root_hash(tmp_path):
    l = ledger(tmp_path / "source")
    l.commit(
        event_id="e1", idempotency_key="k1", base_epoch=0, event_type="TEST",
        mutations=[Mutation("self", "epq", {"precision": 0.5})],
        provenance=PROV, committed_at="2026-08-09T00:00:00Z", writer_node="one"
    )
    snap = l.snapshot(snapshot_id="s1", created_at="2026-08-09T00:00:02Z", created_by="test")
    path = l.export_snapshot("s1", tmp_path / "snapshot.json")
    restored = StateLedger.restore_snapshot(path, tmp_path / "restored.sqlite")
    assert restored.head()["root_hash"] == snap["root_hash"]
    assert restored.read("self", "epq")["value"] == {"precision": 0.5}
    assert restored.verify()["status"] == "PASS"


def test_snapshot_tamper_detected(tmp_path):
    l = ledger(tmp_path / "source")
    l.commit(
        event_id="e1", idempotency_key="k1", base_epoch=0, event_type="TEST",
        mutations=[Mutation("world", "door", "closed")],
        provenance=PROV, committed_at="2026-08-09T00:00:00Z", writer_node="one"
    )
    l.snapshot(snapshot_id="s1", created_at="2026-08-09T00:00:02Z", created_by="test")
    path = l.export_snapshot("s1", tmp_path / "snapshot.json")
    payload = json.loads(path.read_text())
    payload["state"][0]["value"] = "open"
    path.write_text(json.dumps(payload))
    with pytest.raises(TamperDetected):
        StateLedger.restore_snapshot(path, tmp_path / "restored.sqlite")


def test_direct_db_tamper_detected(tmp_path):
    l = ledger(tmp_path)
    l.commit(
        event_id="e1", idempotency_key="k1", base_epoch=0, event_type="TEST",
        mutations=[Mutation("world", "x", 1)], provenance=PROV,
        committed_at="2026-08-09T00:00:00Z", writer_node="one"
    )
    l.db.execute("UPDATE ledger_state SET value_json='2' WHERE domain='world' AND state_key='x'")
    with pytest.raises(TamperDetected):
        l.verify()
