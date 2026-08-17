import hashlib
import json

from clayverse.effect_journal import EffectJournal
from clayverse.identity import IdentityRouter
from clayverse.recovery import _causal_credit, _decode_persisted_effect_outcome, recover_incomplete_episodes
from clayverse.store import UnifiedDB
from clayverse.workspace import Workspace


def test_valid_redacted_receipt_reuses_live_raw_outcome_digest():
    raw_outcome = {
        "ok": True,
        "exit": 0,
        "boundary": "entityos",
        "certainty": "verified",
    }
    receipt = EffectJournal._outcome_receipt(raw_outcome)
    persisted = EffectJournal._payload(receipt)

    recovered, outcome_hash, structurally_valid = _decode_persisted_effect_outcome(persisted)

    assert structurally_valid is True
    assert recovered == receipt
    assert outcome_hash == receipt["sha256"]
    assert outcome_hash == hashlib.sha256(
        EffectJournal._payload(raw_outcome).encode()
    ).hexdigest()
    # This helper remains the live effect-credit law. Recovery reconstruction is
    # separately fail-closed when the original causal row is missing.
    assert _causal_credit("VERIFIED", recovered, "entityos.exec") == 1.0


def test_malformed_json_receipt_stays_unknown_and_non_rewarding():
    recovered, outcome_hash, structurally_valid = _decode_persisted_effect_outcome("{not-json")

    assert structurally_valid is False
    assert recovered["ok"] is False
    assert recovered["certainty"] == "unknown"
    assert recovered["reason"] == "invalid_persisted_outcome_receipt"
    assert len(recovered["persisted_receipt_sha256"]) == 64
    assert len(outcome_hash) == 64
    assert _causal_credit("VERIFIED", recovered, "entityos.exec") == 0.0


def test_structurally_invalid_verified_receipt_cannot_mint_positive_credit():
    malformed = '{"ok":true,"sha256":"' + ("a" * 64) + '","bytes":12}'
    recovered, _outcome_hash, structurally_valid = _decode_persisted_effect_outcome(malformed)

    assert structurally_valid is False
    assert recovered["ok"] is False
    assert recovered["certainty"] == "unknown"
    assert _causal_credit("VERIFIED", recovered, "entityos.exec") == 0.0


def test_receipt_with_unknown_fields_or_invalid_digest_is_rejected():
    for persisted in (
        '{"audit":"redacted-outcome-v1","sha256":"xyz","bytes":12,"ok":true}',
        '{"audit":"redacted-outcome-v1","sha256":"' + ("a" * 64) + '","bytes":12,"ok":true,"surprise":1}',
        '{"audit":"redacted-outcome-v1","sha256":"' + ("a" * 64) + '","bytes":true,"ok":true}',
    ):
        recovered, _outcome_hash, structurally_valid = _decode_persisted_effect_outcome(persisted)
        assert structurally_valid is False
        assert recovered["certainty"] == "unknown"
        assert _causal_credit("VERIFIED", recovered, "entityos.exec") == 0.0


def test_structurally_valid_forged_receipt_preserves_identity_but_cannot_reward_recovery(tmp_path):
    db = UnifiedDB(tmp_path / "state.db")
    router = IdentityRouter(db, {})
    session_id = router.db.ensure_session("gabriel", "terminal-gabriel")
    turn_id = db.append_turn(session_id, "gabriel", "user", "recover forged receipt")
    episode = Workspace(db).open(session_id, turn_id, "recover forged receipt", [])
    Workspace(db).select(episode["episode_id"], "request_effect")

    effect_id = db.record_effect(
        episode["episode_id"],
        "gabriel",
        "entityos.exec",
        "checkpoint",
        db.session_generation(session_id),
        "VERIFIED",
        ["checkpoint"],
        {"ok": True, "exit": 0, "boundary": "entityos", "certainty": "verified"},
    )

    forged_digest = "a" * 64
    forged = json.dumps(
        {
            "audit": "redacted-outcome-v1",
            "sha256": forged_digest,
            "bytes": 1,
            "ok": True,
            "exit": 0,
            "boundary": "entityos",
            "certainty": "verified",
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    db.db.execute("UPDATE effects SET outcome=? WHERE effect_id=?", (forged, effect_id))

    decoded, decoded_hash, structurally_valid = _decode_persisted_effect_outcome(forged)
    assert structurally_valid is True
    assert decoded["ok"] is True
    assert decoded_hash == forged_digest
    assert _causal_credit("VERIFIED", decoded, "entityos.exec") == 1.0

    result = recover_incomplete_episodes(db)

    row = db.db.execute(
        "SELECT effect_id,outcome_hash,credit,reentered FROM causal_episodes WHERE episode_id=?",
        (episode["episode_id"],),
    ).fetchone()
    assert dict(row) == {
        "effect_id": effect_id,
        "outcome_hash": forged_digest,
        "credit": 0.0,
        "reentered": 1,
    }
    assert result["reentered_effects"] == 1
