import tempfile
import unittest
from pathlib import Path

from live_fusion_work_lease_v1 import WorkLeaseFenceStore


class LeaseFenceTests(unittest.TestCase):
    def test_one_active_lease_and_failover_fences_old_holder(self):
        store = WorkLeaseFenceStore()
        old = store.claim(work_id="W", spec_rev=4, holder="A", ttl_s=10, now=100)
        self.assertIsNotNone(old)
        self.assertIsNone(store.claim(work_id="W", spec_rev=4, holder="B", ttl_s=10, now=101))
        new = store.claim(work_id="W", spec_rev=5, holder="B", ttl_s=10, now=111)
        self.assertEqual(new.fence_epoch, old.fence_epoch + 1)
        self.assertEqual(store.reserve_effect(
            effect_key="E-old", lease=old, current_spec_rev=4, request={"op": 1}, now=112
        )["reason"], "LEASE_INACTIVE")
        self.assertTrue(store.reserve_effect(
            effect_key="E-new", lease=new, current_spec_rev=5, request={"op": 1}, now=112
        )["reserved"])

    def test_stale_spec_revision_fails_closed_before_effect(self):
        store = WorkLeaseFenceStore()
        lease = store.claim(work_id="W", spec_rev=1, holder="A", now=0)
        self.assertEqual(
            store.reserve_effect(effect_key="E", lease=lease, current_spec_rev=2, request={}, now=1),
            {"reserved": False, "reason": "STALE_SPEC_REV"},
        )

    def test_finalize_replay_and_conflict(self):
        store = WorkLeaseFenceStore()
        lease = store.claim(work_id="W", spec_rev=1, holder="A", now=0)
        self.assertTrue(store.reserve_effect(
            effect_key="E", lease=lease, current_spec_rev=1, request={"v": 1}, now=1
        )["reserved"])
        first = store.finalize_effect(effect_key="E", lease=lease, result={"ok": 1}, success=True, now=2)
        replay = store.finalize_effect(effect_key="E", lease=lease, result={"ok": 1}, success=True, now=3)
        conflict = store.finalize_effect(effect_key="E", lease=lease, result={"ok": 2}, success=True, now=4)
        self.assertEqual(first["reason"], "FINALIZED")
        self.assertEqual(replay["reason"], "IDEMPOTENT_REPLAY")
        self.assertEqual(conflict["reason"], "IDEMPOTENCY_CONFLICT")

    def test_crash_after_reserve_fails_closed_on_retry_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "lease.sqlite"
            s1 = WorkLeaseFenceStore(path)
            old = s1.claim(work_id="W", spec_rev=1, holder="A", ttl_s=5, now=0)
            self.assertTrue(s1.reserve_effect(
                effect_key="E", lease=old, current_spec_rev=1, request={"op": "send"}, now=1
            )["reserved"])
            s1.close()

            s2 = WorkLeaseFenceStore(path)
            new = s2.claim(work_id="W", spec_rev=2, holder="B", ttl_s=5, now=6)
            retry = s2.reserve_effect(
                effect_key="E", lease=new, current_spec_rev=2, request={"op": "send"}, now=7
            )
            self.assertEqual(retry, {"reserved": False, "reason": "RECOVERY_REQUIRED"})
            self.assertEqual(s2.effect_state("E")["state"], "RESERVED")
            s2.close()

    def test_restart_preserves_finalized_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "lease.sqlite"
            s1 = WorkLeaseFenceStore(path)
            lease = s1.claim(work_id="W", spec_rev=1, holder="A", ttl_s=10, now=0)
            s1.reserve_effect(effect_key="E", lease=lease, current_spec_rev=1, request={"op": 1}, now=1)
            self.assertEqual(s1.finalize_effect(
                effect_key="E", lease=lease, result={"ok": True}, success=True, now=2
            )["reason"], "FINALIZED")
            s1.close()
            s2 = WorkLeaseFenceStore(path)
            replay = s2.reserve_effect(
                effect_key="E", lease=lease, current_spec_rev=1, request={"op": 1}, now=3
            )
            self.assertEqual(replay, {"reserved": False, "reason": "ALREADY_FINALIZED"})
            s2.close()

    def test_two_connections_cannot_both_claim_same_live_work(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "lease.sqlite"
            a = WorkLeaseFenceStore(path)
            b = WorkLeaseFenceStore(path)
            lease = a.claim(work_id="W", spec_rev=1, holder="A", ttl_s=30, now=0)
            self.assertIsNotNone(lease)
            self.assertIsNone(b.claim(work_id="W", spec_rev=1, holder="B", ttl_s=30, now=1))
            a.close()
            b.close()


if __name__ == "__main__":
    unittest.main()
