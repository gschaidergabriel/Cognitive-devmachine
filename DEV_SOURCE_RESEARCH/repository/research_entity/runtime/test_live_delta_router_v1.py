from research_entity.runtime.live_delta_router_v1 import (
    DeltaEnvelope,
    IdentityConflictError,
    LiveDeltaRouter,
    MissingPredecessorError,
    ReceiptStage,
    StaleWorkRevisionError,
    WorkNode,
    cloud_event_projection,
)


def build_router(dependency_index_complete=True):
    nodes = [
        WorkNode("A", "claycode", spec_rev=3, current_epoch=5),
        WorkNode(
            "B",
            "harness",
            depends_on=("A",),
            premise_claim_ids=("claim-parser-green",),
            spec_rev=2,
            current_epoch=5,
        ),
        WorkNode("C", "unifieddb", depends_on=("B",), spec_rev=1, current_epoch=5),
        WorkNode("D", "gwt", spec_rev=1, current_epoch=5),
    ]
    return LiveDeltaRouter(
        nodes,
        dependency_index_complete=dependency_index_complete,
        dense_fanout_fraction=0.9,
    )


def test_old_causal_origin_is_not_automatic_stale():
    r = build_router()
    e = DeltaEnvelope(
        "evt-old",
        "urn:clay:test",
        "org.clay.research.delta.v1",
        "wp02",
        causal_origin_epoch=1,
        arrival_epoch=10,
        work_spec_rev=3,
        affected_work_ids=("A",),
    )
    assert r.admit_once(e) is True
    d = r.route(e)
    assert d.mode == "TARGETED_DELTA"
    assert d.destinations == ("A", "B", "C")


def test_invalidation_transitive_closure():
    r = build_router()
    e = DeltaEnvelope(
        event_id="evt-1",
        source="urn:clay:test",
        event_type="org.clay.research.delta.v1",
        subject="claim-parser-green",
        causal_origin_epoch=5,
        arrival_epoch=5,
        invalidated_claim_ids=("claim-parser-green",),
    )
    r.admit_once(e)
    d = r.route(e)
    assert d.destinations == ("B", "C")
    assert d.destination_branches == ("harness", "unifieddb")
    assert d.priority == "INTERRUPT"


def test_dedup_and_identity_conflict():
    r = build_router()
    e = DeltaEnvelope("evt-2", "urn:clay:test", "x", "s", 5, 5, affected_work_ids=("A",))
    assert r.admit_once(e) is True
    assert r.admit_once(e) is False
    conflicting = DeltaEnvelope(
        "evt-2",
        "urn:clay:test",
        "x",
        "s",
        5,
        5,
        affected_work_ids=("A",),
        payload={"different": True},
    )
    try:
        r.admit_once(conflicting)
    except IdentityConflictError:
        pass
    else:
        raise AssertionError("same source+id with conflicting content was admitted")


def test_stale_work_revision_fails_closed():
    r = build_router()
    e = DeltaEnvelope(
        "evt-3",
        "urn:clay:test",
        "x",
        "s",
        causal_origin_epoch=9,
        arrival_epoch=10,
        work_spec_rev=2,
        affected_work_ids=("A",),
    )
    r.admit_once(e)
    try:
        r.route(e)
    except StaleWorkRevisionError:
        pass
    else:
        raise AssertionError("stale work revision admitted")


def test_historically_valid_only_preserved_without_plan_churn():
    r = build_router()
    e = DeltaEnvelope(
        "evt-hist",
        "urn:clay:test",
        "x",
        "s",
        causal_origin_epoch=1,
        arrival_epoch=10,
        applicability="HISTORICALLY_VALID_ONLY",
    )
    r.admit_once(e)
    d = r.route(e)
    assert d.mode == "DIGEST_ONLY"
    assert d.destinations == ()


def test_missing_causal_predecessor_holds_material_use():
    r = build_router()
    e = DeltaEnvelope(
        "evt-child",
        "urn:clay:test",
        "x",
        "s",
        5,
        5,
        affected_work_ids=("A",),
        parent_event_ids=("evt-missing-parent",),
    )
    r.admit_once(e)
    try:
        r.route(e)
    except MissingPredecessorError:
        pass
    else:
        raise AssertionError("event with missing causal predecessor admitted for material routing")


def test_incomplete_dependency_index_invalidation_fails_broad():
    r = build_router(dependency_index_complete=False)
    e = DeltaEnvelope(
        "evt-invalidate",
        "urn:clay:test",
        "x",
        "claim-parser-green",
        5,
        5,
        invalidated_claim_ids=("claim-parser-green",),
    )
    r.admit_once(e)
    d = r.route(e)
    assert d.mode == "DENSE_FANOUT"
    assert d.destinations == ("A", "B", "C", "D")


def test_receipt_chain_and_projection():
    r = build_router()
    e = DeltaEnvelope(
        "evt-5",
        "urn:clay:test",
        "org.clay.research.delta.v1",
        "wp02",
        causal_origin_epoch=1,
        arrival_epoch=10,
        work_spec_rev=3,
        affected_work_ids=("A",),
    )
    for stage in ReceiptStage:
        r.record_receipt("evt-5", "A", stage)
    try:
        r.record_receipt("evt-5", "A", ReceiptStage.USED)
    except ValueError:
        pass
    else:
        raise AssertionError("receipt regression admitted")

    assert r.nats_subject("claycode", "claim invalidation", "INTERRUPT") == \
        "clay.delta.claycode.claim-invalidation.interrupt"
    p = cloud_event_projection(e)
    assert p["specversion"] == "1.0"
    assert p["id"] == "evt-5"
    assert p["claycausaloriginepoch"] == 1
    assert p["clayarrivalepoch"] == 10
    assert p["clayworkrev"] == 3
    assert p["clayhash"] == e.content_hash


if __name__ == "__main__":
    test_old_causal_origin_is_not_automatic_stale()
    test_invalidation_transitive_closure()
    test_dedup_and_identity_conflict()
    test_stale_work_revision_fails_closed()
    test_historically_valid_only_preserved_without_plan_churn()
    test_missing_causal_predecessor_holds_material_use()
    test_incomplete_dependency_index_invalidation_fails_broad()
    test_receipt_chain_and_projection()
    print("PASS: 8 live_delta_router_v1 dual-time/hybrid tests")
