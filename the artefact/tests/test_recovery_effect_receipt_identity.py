import hashlib

from clayverse.effect_journal import EffectJournal
from clayverse.recovery import _causal_credit, _decode_persisted_effect_outcome


def test_valid_redacted_receipt_reuses_live_raw_outcome_digest():
    raw_outcome = {
        "ok": True,
        "exit": 0,
        "boundary": "entityos",
        "certainty": "verified",
    }
    receipt = EffectJournal._outcome_receipt(raw_outcome)
    persisted = EffectJournal._payload(receipt)

    recovered, outcome_hash, trusted = _decode_persisted_effect_outcome(persisted)

    assert trusted is True
    assert recovered == receipt
    assert outcome_hash == receipt["sha256"]
    assert outcome_hash == hashlib.sha256(
        EffectJournal._payload(raw_outcome).encode()
    ).hexdigest()
    assert _causal_credit("VERIFIED", recovered, "entityos.exec") == 1.0


def test_malformed_json_receipt_stays_unknown_and_non_rewarding():
    recovered, outcome_hash, trusted = _decode_persisted_effect_outcome("{not-json")

    assert trusted is False
    assert recovered["ok"] is False
    assert recovered["certainty"] == "unknown"
    assert recovered["reason"] == "invalid_persisted_outcome_receipt"
    assert len(recovered["persisted_receipt_sha256"]) == 64
    assert len(outcome_hash) == 64
    assert _causal_credit("VERIFIED", recovered, "entityos.exec") == 0.0


def test_structurally_invalid_verified_receipt_cannot_mint_positive_credit():
    # Syntactically valid JSON and even `ok=true` are insufficient. Recovery only
    # trusts the exact durable receipt envelope emitted by EffectJournal.
    malformed = '{"ok":true,"sha256":"' + ("a" * 64) + '","bytes":12}'
    recovered, _outcome_hash, trusted = _decode_persisted_effect_outcome(malformed)

    assert trusted is False
    assert recovered["ok"] is False
    assert recovered["certainty"] == "unknown"
    assert _causal_credit("VERIFIED", recovered, "entityos.exec") == 0.0


def test_receipt_with_unknown_fields_or_invalid_digest_is_rejected():
    for persisted in (
        '{"audit":"redacted-outcome-v1","sha256":"xyz","bytes":12,"ok":true}',
        '{"audit":"redacted-outcome-v1","sha256":"' + ("a" * 64) + '","bytes":12,"ok":true,"surprise":1}',
        '{"audit":"redacted-outcome-v1","sha256":"' + ("a" * 64) + '","bytes":true,"ok":true}',
    ):
        recovered, _outcome_hash, trusted = _decode_persisted_effect_outcome(persisted)
        assert trusted is False
        assert recovered["certainty"] == "unknown"
        assert _causal_credit("VERIFIED", recovered, "entityos.exec") == 0.0
