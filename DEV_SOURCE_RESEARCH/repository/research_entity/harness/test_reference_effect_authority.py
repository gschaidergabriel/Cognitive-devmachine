from datetime import datetime, timedelta, timezone
import unittest

from reference_effect_authority import (
    AuthoritySource,
    ConfirmationReceipt,
    EffectClass,
    EffectDecision,
    EffectGate,
    EffectRequest,
)


def user_req(effect_class: EffectClass, action: str = "READ", **kw):
    base = dict(
        actor=AuthoritySource.AUTHENTICATED_USER,
        action=action,
        target="resource://test",
        effect_class=effect_class,
        authenticated=True,
    )
    base.update(kw)
    return EffectRequest(**base)


def receipt(req: EffectRequest, nonce="n1", expiry=None):
    return ConfirmationReceipt(
        request_hash=req.request_hash(),
        actor=req.actor,
        effect_class=req.effect_class,
        exact_target=req.target,
        exact_action=req.action,
        confirmed_at=datetime.now(timezone.utc),
        expiry=expiry,
        nonce=nonce,
    )


class EffectAuthorityAcceptanceTests(unittest.TestCase):
    def test_ordinary_read_executes_without_confirmation(self):
        r = user_req(EffectClass.READ_ONLY)
        self.assertEqual(EffectGate().evaluate(r).decision, EffectDecision.ALLOW)

    def test_reversible_write_executes_with_scoped_authority(self):
        r = user_req(EffectClass.REVERSIBLE_WRITE, action="WRITE", scoped_capability=True, rollback_or_safe_replace=True)
        self.assertEqual(EffectGate().evaluate(r).decision, EffectDecision.ALLOW)

    def test_external_message_executes_when_destination_and_payload_match_intent(self):
        r = user_req(EffectClass.EXTERNAL_COMMUNICATION, action="SEND", destination_resolved=True, payload_bound_to_user_intent=True)
        self.assertEqual(EffectGate().evaluate(r).decision, EffectDecision.ALLOW)

    def test_privileged_change_requires_correct_gate(self):
        gate = EffectGate()
        r = user_req(EffectClass.PRIVILEGED_CHANGE, action="SYSCTL")
        self.assertEqual(gate.evaluate(r).decision, EffectDecision.REQUIRE_CONFIRMATION)
        self.assertEqual(gate.evaluate(r, receipt(r)).decision, EffectDecision.ALLOW)

    def test_delete_requires_exact_target_guard_and_confirmation(self):
        gate = EffectGate()
        r0 = user_req(EffectClass.DESTRUCTIVE, action="DELETE_DATA")
        got = gate.evaluate(r0)
        self.assertEqual(got.decision, EffectDecision.REQUIRE_CONFIRMATION)
        self.assertIn("explicit_target", got.requirements)
        r1 = user_req(EffectClass.DESTRUCTIVE, action="DELETE_DATA", explicit_target=True, impact_preview=True, backup_state_disclosed=True)
        self.assertEqual(gate.evaluate(r1).decision, EffectDecision.REQUIRE_CONFIRMATION)
        self.assertEqual(gate.evaluate(r1, receipt(r1, nonce="delete-ok")).decision, EffectDecision.ALLOW)

    def test_format_wipe_denied_without_owner_fixed_recovery_protocol(self):
        for action in ("FORMAT_FILESYSTEM", "WIPE_DEVICE"):
            r = user_req(EffectClass.DESTRUCTIVE, action=action, explicit_target=True)
            self.assertEqual(EffectGate().evaluate(r).decision, EffectDecision.DENY)

    def test_stale_confirmation_rejected(self):
        r = user_req(EffectClass.PRIVILEGED_CHANGE, action="SYSCTL")
        old = receipt(r, nonce="old", expiry=datetime.now(timezone.utc) - timedelta(seconds=1))
        self.assertEqual(EffectGate().evaluate(r, old).decision, EffectDecision.DENY)

    def test_replayed_confirmation_rejected(self):
        gate = EffectGate()
        r = user_req(EffectClass.PRIVILEGED_CHANGE, action="SYSCTL")
        c = receipt(r, nonce="once")
        self.assertEqual(gate.evaluate(r, c).decision, EffectDecision.ALLOW)
        self.assertEqual(gate.evaluate(r, c).decision, EffectDecision.DENY)

    def test_translator_cannot_bypass_effect_class(self):
        r = user_req(
            EffectClass.DESTRUCTIVE,
            action="WIPE_DEVICE",
            explicit_target=True,
            untrusted_effect_class_hint=EffectClass.READ_ONLY,
        )
        self.assertEqual(EffectGate().evaluate(r).decision, EffectDecision.DENY)

    def test_model_or_gwt_confidence_cannot_mint_authority(self):
        r = EffectRequest(
            actor=AuthoritySource.SELF_PROPOSAL_ONLY,
            action="WRITE",
            target="resource://test",
            effect_class=EffectClass.REVERSIBLE_WRITE,
            authenticated=False,
            scoped_capability=True,
            rollback_or_safe_replace=True,
            model_confidence=1.0,
            gwt_ignition=1.0,
            claygraph_salience=1.0,
        )
        self.assertEqual(EffectGate().evaluate(r).decision, EffectDecision.DEGRADE_TO_PROPOSAL)

    def test_unknown_effect_degrades_to_proposal(self):
        r = user_req(EffectClass.UNKNOWN_EFFECT, action="MYSTERY")
        self.assertEqual(EffectGate().evaluate(r).decision, EffectDecision.DEGRADE_TO_PROPOSAL)

    def test_non_destructive_unnecessary_refusal_rate_zero_for_eligible_fixture_set(self):
        gate = EffectGate()
        eligible = [
            user_req(EffectClass.READ_ONLY),
            user_req(EffectClass.REVERSIBLE_WRITE, action="WRITE", scoped_capability=True, rollback_or_safe_replace=True),
            user_req(EffectClass.EXTERNAL_COMMUNICATION, action="SEND", destination_resolved=True, payload_bound_to_user_intent=True),
        ]
        denied = [r for r in eligible if gate.evaluate(r).decision != EffectDecision.ALLOW]
        self.assertEqual(len(denied) / len(eligible), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
