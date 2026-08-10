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
        self.assertFalse(store.commit_effect(
            effect_key="E-old", lease=old, current_spec_rev=4, result={"ok": 1}, success=True, now=112
        )["accepted"])
        self.assertTrue(store.commit_effect(
            effect_key="E-new", lease=new, current_spec_rev=5, result={"ok": 1}, success=True, now=112
        )["accepted"])

    def test_stale_spec_revision_fails_closed(self):
        store = WorkLeaseFenceStore()
        lease = store.claim(work_id="W", spec_rev=1, holder="A", now=0)
        self.assertEqual(
            store.commit_effect(effect_key="E", lease=lease, current_spec_rev=2, result={}, success=True, now=1),
            {"accepted": False, "reason": "STALE_SPEC_REV"},
        )

    def test_idempotent_effect_replay_and_conflict(self):
        store = WorkLeaseFenceStore()
        lease = store.claim(work_id="W", spec_rev=1, holder="A", now=0)
        first = store.commit_effect(effect_key="E", lease=lease, current_spec_rev=1, result={"v": 1}, success=True, now=1)
        replay = store.commit_effect(effect_key="E", lease=lease, current_spec_rev=1, result={"v": 1}, success=True, now=2)
        conflict = store.commit_effect(effect_key="E", lease=lease, current_spec_rev=1, result={"v": 2}, success=True, now=3)
        self.assertEqual(first["reason"], "COMMITTED")
        self.assertEqual(replay["reason"], "IDEMPOTENT_REPLAY")
        self.assertEqual(conflict["reason"], "IDEMPOTENCY_CONFLICT")

    def test_restart_preserves_fence_and_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "lease.sqlite"
            s1 = WorkLeaseFenceStore(path)
            lease = s1.claim(work_id="W", spec_rev=1, holder="A", ttl_s=5, now=0)
            self.assertEqual(s1.commit_effect(
                effect_key="E", lease=lease, current_spec_rev=1, result={"ok": True}, success=True, now=1
            )["reason"], "COMMITTED")
            s1.close()
            s2 = WorkLeaseFenceStore(path)
            new = s2.claim(work_id="W", spec_rev=2, holder="B", ttl_s=5, now=6)
            self.assertEqual(new.fence_epoch, lease.fence_epoch + 1)
            self.assertEqual(s2.commit_effect(
                effect_key="E", lease=new, current_spec_rev=2, result={"ok": True}, success=True, now=7
            )["reason"], "IDEMPOTENT_REPLAY")
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
