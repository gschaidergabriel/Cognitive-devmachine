import unittest

from live_fusion_reentry_v13 import LiveDelta, LiveFusionBus, Resolution, WorkerView
from live_fusion_work_lease_v1 import WorkLeaseFenceStore


class LiveFusionLeaseIntegrationTests(unittest.TestCase):
    def test_terminal_resolution_and_current_lease_are_both_required(self):
        bus = LiveFusionBus()
        bus.register_worker(
            WorkerView(
                worker_id="worker-a",
                branches=("unifieddb",),
                active_keys=("pulse",),
                active_work=("work-1",),
                subscription_revision="sub-1",
                plan_revision="plan-1",
            )
        )
        event = LiveDelta(
            event_id="evt-conflict",
            source="github-main",
            source_seq=1,
            source_epoch="sha-1",
            semantic_keys=("pulse",),
            affected_branches=("unifieddb",),
            novelty="CONTRADICTS",
            impact=0.95,
            urgency=0.90,
            conflict=True,
            payload={"new_evidence": "invalidates current work premise"},
            provenance_refs=("commit:1",),
            applicability="CURRENT_MATERIAL",
            affected_work=("work-1",),
        )
        self.assertEqual(bus.ingest(event), "INGESTED")

        leases = WorkLeaseFenceStore()
        lease = leases.claim(work_id="work-1", spec_rev=1, holder="worker-a", ttl_s=30, now=0)
        self.assertIsNotNone(lease)

        guard_ok, blockers = bus.effect_guard("worker-a", effect_work=("work-1",))
        self.assertFalse(guard_ok)
        self.assertEqual(blockers, ["evt-conflict"])

        bus.resolve(
            Resolution(
                resolution_id="res-1",
                event_id="evt-conflict",
                worker_id="worker-a",
                subscription_revision="sub-1",
                decision="REPLAN",
                prior_plan_revision="plan-1",
                new_plan_revision="plan-2",
                basis_event_ids=("evt-conflict",),
                plan_state_hash="state-plan-2",
            )
        )
        self.assertTrue(bus.effect_guard("worker-a", effect_work=("work-1",))[0])

        stale = leases.reserve_effect(
            effect_key="effect:work-1",
            lease=lease,
            current_spec_rev=2,
            request={"operation": "write"},
            now=1,
        )
        self.assertEqual(stale, {"reserved": False, "reason": "STALE_SPEC_REV"})

        leases.release(lease, now=2)
        fresh = leases.claim(work_id="work-1", spec_rev=2, holder="worker-a", ttl_s=30, now=3)
        self.assertIsNotNone(fresh)
        reserved = leases.reserve_effect(
            effect_key="effect:work-1",
            lease=fresh,
            current_spec_rev=2,
            request={"operation": "write"},
            now=4,
        )
        self.assertEqual(reserved, {"reserved": True, "reason": "RESERVED"})
        finalized = leases.finalize_effect(
            effect_key="effect:work-1",
            lease=fresh,
            result={"ok": True},
            success=True,
            now=5,
        )
        self.assertEqual(finalized["reason"], "FINALIZED")

    def test_new_holder_cannot_repeat_reserved_effect_after_expiry(self):
        leases = WorkLeaseFenceStore()
        old = leases.claim(work_id="work-2", spec_rev=1, holder="worker-a", ttl_s=5, now=0)
        self.assertTrue(leases.reserve_effect(
            effect_key="effect:once",
            lease=old,
            current_spec_rev=1,
            request={"operation": "send"},
            now=1,
        )["reserved"])
        new = leases.claim(work_id="work-2", spec_rev=2, holder="worker-b", ttl_s=5, now=6)
        self.assertEqual(new.fence_epoch, old.fence_epoch + 1)
        retry = leases.reserve_effect(
            effect_key="effect:once",
            lease=new,
            current_spec_rev=2,
            request={"operation": "send"},
            now=7,
        )
        self.assertEqual(retry, {"reserved": False, "reason": "RECOVERY_REQUIRED"})


if __name__ == "__main__":
    unittest.main()
