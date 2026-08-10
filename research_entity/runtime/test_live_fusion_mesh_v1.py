from live_fusion_mesh_v1 import LiveFusionMesh


def test_delta_semantic_dedupe_and_targeted_ack():
    mesh = LiveFusionMesh.memory()
    first = mesh.publish_delta(
        subject="reward-gap",
        payload={"x": 1},
        targets=["gwt", "frank"],
        actor="w1",
        evidence_class="RESEARCH_EVIDENCE",
        source_epoch=18,
        event_id="e1",
        created_at=1,
    )
    second = mesh.publish_delta(
        subject="reward-gap",
        payload={"x": 1},
        targets=["frank", "gwt"],
        actor="w2",
        evidence_class="RESEARCH_EVIDENCE",
        source_epoch=18,
        event_id="e2",
        created_at=2,
    )
    assert first["delta_id"] == second["delta_id"]
    assert mesh.pending_targets(first["delta_id"]) == ["frank", "gwt"]
    assert mesh.ack_delta(
        delta_id=first["delta_id"], target="frank", actor="frank", event_id="a1", created_at=3
    )
    assert mesh.pending_targets(first["delta_id"]) == ["gwt"]
    assert not mesh.ack_delta(
        delta_id=first["delta_id"], target="frank", actor="frank", event_id="a1", created_at=3
    )


def test_lease_blocks_collision_and_fences_old_holder():
    mesh = LiveFusionMesh.memory()
    old = mesh.claim(work_id="W", spec_rev=4, holder="A", ttl_s=10, now=100)
    assert old is not None
    assert mesh.claim(work_id="W", spec_rev=4, holder="B", ttl_s=10, now=101) is None

    new = mesh.claim(work_id="W", spec_rev=5, holder="B", ttl_s=10, now=111)
    assert new is not None and new.fence_epoch == old.fence_epoch + 1
    assert not mesh.effect_receipt(
        effect_key="eff:W", lease=old, current_spec_rev=4, result={"ok": 1}, success=True, now=112
    )["accepted"]
    assert mesh.effect_receipt(
        effect_key="eff:W", lease=new, current_spec_rev=5, result={"ok": 1}, success=True, now=112
    )["accepted"]


def test_effect_idempotency_and_conflict_detection():
    mesh = LiveFusionMesh.memory()
    lease = mesh.claim(work_id="W", spec_rev=1, holder="A", ttl_s=10, now=0)
    first = mesh.effect_receipt(
        effect_key="K", lease=lease, current_spec_rev=1, result={"v": 1}, success=True, now=1
    )
    replay = mesh.effect_receipt(
        effect_key="K", lease=lease, current_spec_rev=1, result={"v": 1}, success=True, now=2
    )
    conflict = mesh.effect_receipt(
        effect_key="K", lease=lease, current_spec_rev=1, result={"v": 2}, success=True, now=3
    )
    assert first == {"accepted": True, "duplicate": False, "reason": "COMMITTED"}
    assert replay == {"accepted": True, "duplicate": True, "reason": "IDEMPOTENT_REPLAY"}
    assert not conflict["accepted"] and conflict["reason"] == "IDEMPOTENCY_CONFLICT"


def test_stale_spec_receipt_rejected():
    mesh = LiveFusionMesh.memory()
    lease = mesh.claim(work_id="W", spec_rev=1, holder="A", ttl_s=10, now=0)
    assert mesh.effect_receipt(
        effect_key="K", lease=lease, current_spec_rev=2, result={}, success=True, now=1
    ) == {"accepted": False, "reason": "STALE_SPEC_REV"}


def test_premise_invalidation_is_append_only():
    mesh = LiveFusionMesh.memory()
    assert mesh.invalidate_premise(
        premise_key="P",
        invalidation_epoch=19,
        reason={"why": "new evidence"},
        actor="w",
        event_id="i1",
        created_at=1,
    )
    assert not mesh.invalidate_premise(
        premise_key="P",
        invalidation_epoch=19,
        reason={"why": "new evidence"},
        actor="w",
        event_id="i1",
        created_at=1,
    )
