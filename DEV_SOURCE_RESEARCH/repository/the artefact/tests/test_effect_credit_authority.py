from clayverse.effect_journal import EffectJournal
from clayverse.recovery import _causal_credit


def test_state_noop_is_never_positive_learning_credit():
    outcome = {"ok": True, "boundary": "internal"}
    assert EffectJournal._credit("VERIFIED", outcome, "state.noop") == 0.0
    assert _causal_credit("VERIFIED", outcome, "state.noop") == 0.0


def test_only_verified_successful_rewarding_effect_gets_positive_credit():
    ok = {"ok": True}
    failed = {"ok": False}
    assert EffectJournal._credit("VERIFIED", ok, "entityos.exec") == 1.0
    assert _causal_credit("VERIFIED", ok, "entityos.exec") == 1.0
    assert EffectJournal._credit("FAILED", ok, "entityos.exec") == 0.0
    assert _causal_credit("FAILED", ok, "entityos.exec") == 0.0
    assert EffectJournal._credit("VERIFIED", failed, "entityos.exec") == 0.0
    assert _causal_credit("VERIFIED", failed, "entityos.exec") == 0.0


def test_live_and_recovery_credit_laws_are_identical_for_admitted_cases():
    for capability in ("state.noop", "entityos.exec"):
        for status in ("VERIFIED", "FAILED", "DENIED", "STALE_OUTCOME", "UNKNOWN_AFTER_RESTART"):
            for outcome in ({"ok": True}, {"ok": False}, {"certainty": "unknown"}, None):
                assert _causal_credit(status, outcome, capability) == EffectJournal._credit(
                    status, outcome, capability
                )
