from research_entity.runtime.live_delta_router_v1 import (
    DeltaEnvelope,
    LiveDeltaRouter,
    ReceiptStage,
    StaleEnvelopeError,
    WorkNode,
    cloud_event_projection,
)


def build_router():
    nodes = [
        WorkNode("A", "claycode", semantic_epoch=5),
        WorkNode("B", "harness", depends_on=("A",), premise_claim_ids=("claim-parser-green",), semantic_epoch=5),
        WorkNode("C", "unifieddb", depends_on=("B",), semantic_epoch=5),
        WorkNode("D", "gwt", semantic_epoch=5),
    ]
    return LiveDeltaRouter(nodes)


def test_invalidation_transitive_closure():
    r = build_router()
    e = DeltaEnvelope(
        event_id="evt-1",
        source="urn:clay:test",
        event_type="org.clay.research.delta.v1",
        subject="claim-parser-green",
        semantic_epoch=5,
        invalidated_claim_ids=("claim-parser-green",),
    )
    d = r.route(e)
    assert d.destinations == ("B", "C")
    assert d.destination_branches == ("harness", "unifieddb")
    assert d.priority == "INTERRUPT"


def test_dedup_exact_event():
    r = build_router()
    e = DeltaEnvelope("evt-2", "urn:clay:test", "x", "s", 5, affected_work_ids=("A",))
    assert r.admit_once(e) is True
    assert r.admit_once(e) is False


def test_stale_epoch_fails_closed():
    r = build_router()
    e = DeltaEnvelope("evt-3", "urn:clay:test", "x", "s", 4, affected_work_ids=("A",))
    try:
        r.route(e)
    except StaleEnvelopeError:
        pass
    else:
        raise AssertionError("stale event admitted")


def test_receipt_chain_monotonic():
    r = build_router()
    for stage in ReceiptStage:
        r.record_receipt("evt-4", "A", stage)
    try:
        r.record_receipt("evt-4", "A", ReceiptStage.USED)
    except ValueError:
        pass
    else:
        raise AssertionError("receipt regression admitted")


def test_subject_and_cloud_event_projection():
    r = build_router()
    e = DeltaEnvelope(
        "evt-5",
        "urn:clay:test",
        "org.clay.research.delta.v1",
        "wp02",
        5,
        affected_work_ids=("A",),
        parent_event_ids=("evt-parent",),
    )
    assert r.nats_subject("claycode", "claim invalidation", "INTERRUPT") == \
        "clay.delta.claycode.claim-invalidation.interrupt"
    p = cloud_event_projection(e)
    assert p["specversion"] == "1.0"
    assert p["id"] == "evt-5"
    assert p["clayparents"] == ["evt-parent"]
    assert p["clayhash"] == e.content_hash


if __name__ == "__main__":
    test_invalidation_transitive_closure()
    test_dedup_exact_event()
    test_stale_epoch_fails_closed()
    test_receipt_chain_monotonic()
    test_subject_and_cloud_event_projection()
    print("PASS: 5 live_delta_router_v1 tests")
