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

        stale = leases.commit_effect(
            effect_key="effect:work-1",
            lease=lease,
            current_spec_rev=2,
            result={"ok": True},
            success=True,
            now=1,
        )
        self.assertEqual(stale, {"accepted": False, "reason": "STALE_SPEC_REV"})

        leases.release(lease, now=2)
        fresh = leases.claim(work_id="work-1", spec_rev=2, holder="worker-a", ttl_s=30, now=3)
        self.assertIsNotNone(fresh)
        committed = leases.commit_effect(
            effect_key="effect:work-1",
            lease=fresh,
            current_spec_rev=2,
            result={"ok": True},
            success=True,
            now=4,
        )
        self.assertEqual(committed["reason"], "COMMITTED")

    def test_new_holder_fences_late_old_holder_after_expiry(self):
        leases = WorkLeaseFenceStore()
        old = leases.claim(work_id="work-2", spec_rev=1, holder="worker-a", ttl_s=5, now=0)
        new = leases.claim(work_id="work-2", spec_rev=2, holder="worker-b", ttl_s=5, now=6)
        self.assertEqual(new.fence_epoch, old.fence_epoch + 1)
        late = leases.commit_effect(
            effect_key="effect:late-old-holder",
            lease=old,
            current_spec_rev=1,
            result={"ok": True},
            success=True,
            now=7,
        )
        self.assertFalse(late["accepted"])
        self.assertIn(late["reason"], {"LEASE_INACTIVE", "FENCED"})


if __name__ == "__main__":
    unittest.main()
