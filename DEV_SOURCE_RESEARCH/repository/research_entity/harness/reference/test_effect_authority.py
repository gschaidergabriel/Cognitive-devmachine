import unittest
from datetime import datetime, timedelta, timezone

from effect_authority import (
    AuthoritySource,
    ConfirmationReceipt,
    EffectAuthorityGate,
    EffectClass,
    EffectDecision,
    EffectRequest,
)


NOW = datetime(2026, 8, 10, 13, 16, tzinfo=timezone.utc)


def user_req(**kw):
    base = dict(actor=AuthoritySource.AUTHENTICATED_USER, authenticated=True, action="a", target="r")
    base.update(kw)
    return EffectRequest(**base)


def receipt_for(req, nonce="n", *, expiry=None, request_hash=None):
    return ConfirmationReceipt(
        request_hash=request_hash or req.request_hash(),
        actor=AuthoritySource.AUTHENTICATED_USER,
        effect_class=req.effect_class,
        exact_target=req.target,
        exact_action=req.action,
        impact_summary="test impact",
        confirmed_at=NOW,
        expiry=expiry,
        nonce=nonce,
    )


class EffectAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.gate = EffectAuthorityGate()

    def test_ordinary_read_executes_without_confirmation(self):
        req = user_req(effect_class=EffectClass.READ_ONLY)
        self.assertEqual(self.gate.evaluate(req).decision, EffectDecision.ALLOW)

    def test_reversible_write_executes_with_scoped_authority(self):
        req = user_req(effect_class=EffectClass.REVERSIBLE_WRITE, scoped_capability=True, rollback_available=True)
        self.assertEqual(self.gate.evaluate(req).decision, EffectDecision.ALLOW)

    def test_external_message_executes_when_destination_and_payload_match_intent(self):
        req = user_req(effect_class=EffectClass.EXTERNAL_COMMUNICATION, destination_resolved=True, payload_bound_to_user_intent=True)
        self.assertEqual(self.gate.evaluate(req).decision, EffectDecision.ALLOW)

    def test_privileged_change_requires_correct_gate(self):
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        self.assertEqual(self.gate.evaluate(req).decision, EffectDecision.REQUIRE_CONFIRMATION)

    def test_delete_requires_exact_target_and_confirmation(self):
        req = user_req(effect_class=EffectClass.DESTRUCTIVE, destructive_kind="DELETE_DATA", explicit_target=True, impact_preview=True, backup_state_known=True)
        self.assertEqual(self.gate.evaluate(req).decision, EffectDecision.REQUIRE_CONFIRMATION)
        rcpt = receipt_for(req, "n1", expiry=NOW + timedelta(minutes=5))
        self.assertEqual(self.gate.apply_confirmation(req, rcpt, now=NOW).decision, EffectDecision.ALLOW)

    def test_delete_missing_guard_denied(self):
        req = user_req(effect_class=EffectClass.DESTRUCTIVE, destructive_kind="DELETE_DATA", explicit_target=False)
        self.assertEqual(self.gate.evaluate(req).decision, EffectDecision.DENY)

    def test_format_wipe_denied_without_owner_fixed_one_shot_recovery_protocol(self):
        for kind in ("FORMAT_FILESYSTEM", "WIPE_DEVICE"):
            req = user_req(effect_class=EffectClass.DESTRUCTIVE, destructive_kind=kind, explicit_target=True)
            self.assertEqual(self.gate.evaluate(req).decision, EffectDecision.DENY)

    def test_stale_confirmation_rejected(self):
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        rcpt = receipt_for(req, "n2", expiry=NOW - timedelta(seconds=1))
        self.assertEqual(self.gate.apply_confirmation(req, rcpt, now=NOW).decision, EffectDecision.DENY)

    def test_replayed_confirmation_rejected(self):
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        rcpt = receipt_for(req, "n3", expiry=NOW + timedelta(minutes=5))
        self.assertEqual(self.gate.apply_confirmation(req, rcpt, now=NOW).decision, EffectDecision.ALLOW)
        self.assertEqual(self.gate.apply_confirmation(req, rcpt, now=NOW).decision, EffectDecision.DENY)

    def test_translator_cannot_bypass_effect_class(self):
        req = EffectRequest(actor=AuthoritySource.SELF_PROPOSAL_ONLY, action="write", target="r", effect_class=EffectClass.REVERSIBLE_WRITE, scoped_capability=True, rollback_available=True, translator_claims_authority=True)
        self.assertEqual(self.gate.evaluate(req).decision, EffectDecision.DEGRADE_TO_PROPOSAL)

    def test_model_or_gwt_confidence_cannot_mint_authority(self):
        req = EffectRequest(actor=AuthoritySource.SELF_PROPOSAL_ONLY, action="read", target="private", effect_class=EffectClass.READ_ONLY, model_confidence=1.0, gwt_ignition=True, claygraph_salience=1.0)
        self.assertEqual(self.gate.evaluate(req).decision, EffectDecision.DEGRADE_TO_PROPOSAL)

    def test_unknown_effect_degrades_to_proposal(self):
        req = user_req(effect_class=EffectClass.UNKNOWN_EFFECT)
        self.assertEqual(self.gate.evaluate(req).decision, EffectDecision.DEGRADE_TO_PROPOSAL)

    def test_financial_commitment_confirmation(self):
        req = user_req(effect_class=EffectClass.FINANCIAL_OR_LEGAL_COMMITMENT)
        self.assertEqual(self.gate.evaluate(req).decision, EffectDecision.REQUIRE_CONFIRMATION)

    def test_security_policy_can_deny(self):
        req = user_req(effect_class=EffectClass.CREDENTIAL_SECURITY, security_subeffect_deny=True)
        self.assertEqual(self.gate.evaluate(req).decision, EffectDecision.DENY)

    def test_mismatched_confirmation_rejected(self):
        req = user_req(effect_class=EffectClass.PRIVILEGED_CHANGE)
        rcpt = receipt_for(req, "n4", expiry=NOW + timedelta(minutes=5), request_hash="bad")
        self.assertEqual(self.gate.apply_confirmation(req, rcpt, now=NOW).decision, EffectDecision.DENY)

    def test_confirmation_hash_binds_policy_relevant_fields(self):
        req = user_req(effect_class=EffectClass.DESTRUCTIVE, destructive_kind="DELETE_DATA", explicit_target=True, impact_preview=True, backup_state_known=True)
        rcpt = receipt_for(req, "n5", expiry=NOW + timedelta(minutes=5))
        mutated = user_req(effect_class=EffectClass.DESTRUCTIVE, destructive_kind="DELETE_DATA", explicit_target=True, impact_preview=True, backup_state_known=True, no_backup_disclosed=True)
        self.assertNotEqual(req.request_hash(), mutated.request_hash())
        self.assertEqual(self.gate.apply_confirmation(mutated, rcpt, now=NOW).decision, EffectDecision.DENY)

    def test_non_destructive_unnecessary_refusal_rate_zero_on_eligible_matrix(self):
        eligible = [
            user_req(effect_class=EffectClass.READ_ONLY),
            user_req(effect_class=EffectClass.REVERSIBLE_WRITE, scoped_capability=True, safe_replace=True),
            user_req(effect_class=EffectClass.EXTERNAL_COMMUNICATION, destination_resolved=True, payload_bound_to_user_intent=True),
        ]
        refusals = sum(self.gate.evaluate(r).decision != EffectDecision.ALLOW for r in eligible)
        self.assertEqual(refusals / len(eligible), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
