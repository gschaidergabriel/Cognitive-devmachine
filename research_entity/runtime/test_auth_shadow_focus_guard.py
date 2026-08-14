from __future__ import annotations

import unittest

from research_entity.harness.reference.state_auth_shadow import AuthenticatedStateShadowV1
from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.auth_shadow_focus_guard import AuthShadowFocusGuard, FocusIntegrityError


class AuthShadowFocusGuardTests(unittest.TestCase):
    def seed(self):
        ledger=StateLedger()
        ledger.append_event(
            event_id="seed",idem="seed",base_epoch=ledger.epoch,event_type="SEED",writer="test",
            ops=[
                {"op":"SET","domain":"memory","key":"a","value":{"priority":0.8,"fact":"A"},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"memory","key":"b","value":{"priority":0.2,"fact":"B"},"epistemic":"KNOWN","status":"CURRENT"},
            ],committed_at="2026-08-10T01:55:00Z")
        shadow=AuthenticatedStateShadowV1(ledger)
        shadow.full_rebuild(now="build")
        return ledger,shadow,AuthShadowFocusGuard(ledger,shadow)

    def test_clean_selected_refs_pass_without_full_audit(self):
        ledger,shadow,guard=self.seed()
        out=guard.refresh_and_verify_refs(("memory:a","memory:b"),now="pulse")
        self.assertTrue(out.passed)
        self.assertEqual(out.checked_refs,("memory:a","memory:b"))
        self.assertEqual(out.global_integrity_claim,"NONE_PERIODIC_FULL_AUDIT_STILL_REQUIRED")
        ledger.close()

    def test_committed_event_is_delta_refreshed_before_use(self):
        ledger,shadow,guard=self.seed()
        ledger.append_event(
            event_id="update",idem="update",base_epoch=ledger.epoch,event_type="UPDATE",writer="test",
            ops=[{"op":"SET","domain":"memory","key":"a","value":{"priority":0.9,"fact":"A2"},"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="2026-08-10T01:55:01Z")
        out=guard.refresh_and_verify_refs(("memory:a",),now="pulse")
        self.assertEqual(out.refresh_mode,"DELTA_REFRESH")
        self.assertTrue(out.passed)
        self.assertEqual(out.last_event_seq,2)
        ledger.close()

    def test_valid_json_direct_tamper_of_selected_ref_fails_closed(self):
        ledger,shadow,guard=self.seed()
        ledger.conn.execute(
            "UPDATE state SET value_json=? WHERE domain='memory' AND k='a'",
            ('{"priority":1.0,"fact":"TAMPERED"}',),
        )
        ledger.conn.commit()
        # Shadow refresh sees no authoritative event; the use-boundary leaf comparison must catch it.
        with self.assertRaises(FocusIntegrityError):
            guard.refresh_and_verify_refs(("memory:a",),now="pulse")
        ledger.close()

    def test_tampered_unused_ref_does_not_create_false_global_integrity_claim(self):
        ledger,shadow,guard=self.seed()
        ledger.conn.execute(
            "UPDATE state SET value_json=? WHERE domain='memory' AND k='b'",
            ('{"priority":0.3,"fact":"LATENT_TAMPER"}',),
        )
        ledger.conn.commit()
        out=guard.refresh_and_verify_refs(("memory:a",),now="pulse")
        self.assertTrue(out.passed)
        self.assertEqual(out.global_integrity_claim,"NONE_PERIODIC_FULL_AUDIT_STILL_REQUIRED")
        self.assertFalse(shadow.verify_full().passed)
        ledger.close()

    def test_tampered_unused_ref_fails_when_it_later_enters_context(self):
        ledger,shadow,guard=self.seed()
        ledger.conn.execute(
            "UPDATE state SET value_json=? WHERE domain='memory' AND k='b'",
            ('{"priority":1.0,"fact":"LATENT_TAMPER"}',),
        )
        ledger.conn.commit()
        guard.refresh_and_verify_refs(("memory:a",),now="pulse1")
        with self.assertRaises(FocusIntegrityError):
            guard.refresh_and_verify_refs(("memory:b",),now="pulse2")
        ledger.close()

    def test_missing_selected_ref_fails_closed(self):
        ledger,shadow,guard=self.seed()
        with self.assertRaises(FocusIntegrityError):
            guard.refresh_and_verify_refs(("memory:missing",),now="pulse")
        ledger.close()

    def test_invalid_ref_fails_before_refresh(self):
        ledger,shadow,guard=self.seed()
        with self.assertRaises(ValueError):
            guard.refresh_and_verify_refs(("invalid",),now="pulse")
        ledger.close()


if __name__=="__main__": unittest.main(verbosity=2)
