from __future__ import annotations

import hashlib
import json
import re
import time
import uuid

from .effect_journal import EffectJournal
from .store import UnifiedDB


_RECOVERY_NAMESPACE = uuid.UUID("77f43847-1c48-5fa1-918d-eaa7d8db7b5c")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class RecoveryIntegrityError(RuntimeError):
    pass


def _causal_credit(status: str, outcome: object, capability: str) -> float:
    """Use the live effect-credit law only where the original outcome is authoritative."""
    return EffectJournal._credit(status, outcome, capability)


def _causal_id(episode_id: str, effect_id: str | None) -> str:
    return str(uuid.uuid5(_RECOVERY_NAMESPACE, f"{episode_id}\x1f{effect_id or 'no-effect'}"))


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _decode_persisted_effect_outcome(raw: object) -> tuple[dict, str, bool]:
    """Recover effect-outcome identity without manufacturing learning authority.

    Current EffectJournal rows store `redacted-outcome-v1`; their inner `sha256`
    preserves the raw-outcome identity. Older/fixture rows may still persist the raw
    JSON outcome itself, in which case its canonical hash remains the legacy identity.

    Neither form is sufficient to recreate positive causal credit after the original
    causal row has been lost. Current redacted receipts no longer contain the raw
    outcome needed to authenticate copied safe fields such as `ok`, while legacy rows
    have crossed an artifact-generation recovery boundary. Recovery therefore uses
    this decoder for identity only and synthesizes zero credit separately.
    """
    raw_text = raw if isinstance(raw, str) else repr(raw)
    persisted_digest = hashlib.sha256(raw_text.encode("utf-8", errors="replace")).hexdigest()
    unknown = {
        "ok": False,
        "certainty": "unknown",
        "reason": "invalid_persisted_outcome_receipt",
        "persisted_receipt_sha256": persisted_digest,
    }
    try:
        outcome = json.loads(raw) if isinstance(raw, (str, bytes, bytearray)) else None
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return unknown, _hash(unknown), False
    if not isinstance(outcome, dict):
        return unknown, _hash(unknown), False

    # Legacy raw-outcome rows predate the redacted receipt envelope. Preserve their
    # canonical outcome identity, but recovery still reconstructs zero credit below.
    if "audit" not in outcome:
        return outcome, _hash(outcome), True

    allowed = {"audit", "sha256", "bytes", *EffectJournal.SAFE_OUTCOME_FIELDS}
    digest = outcome.get("sha256")
    byte_count = outcome.get("bytes")
    safe_values = [outcome[key] for key in EffectJournal.SAFE_OUTCOME_FIELDS if key in outcome]
    if (
        set(outcome) - allowed
        or outcome.get("audit") != "redacted-outcome-v1"
        or not isinstance(digest, str)
        or _HEX64.fullmatch(digest) is None
        or isinstance(byte_count, bool)
        or not isinstance(byte_count, int)
        or byte_count < 0
        or any(not isinstance(value, (str, int, float, bool, type(None))) for value in safe_values)
    ):
        return unknown, _hash(unknown), False
    return outcome, digest, True


def _insert_unknown_reentry(tx, episode, reason: str, *, count: int | None = None) -> str:
    receipt = {"ok": False, "certainty": "unknown", "reason": reason}
    if count is not None:
        receipt["count"] = int(count)
    cid = _causal_id(episode["episode_id"], None)
    tx.execute(
        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,0,1,?)",
        (cid, episode["episode_id"], None, episode["observation_turn_id"], _hash(receipt), time.time()),
    )
    return cid


def _append_recovery_turn(tx, active, reason: str, effect_id: str | None) -> None:
    ordinal = int(tx.execute(
        "SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id=?", (active["session_id"],)
    ).fetchone()[0])
    tx.execute(
        "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            str(uuid.uuid4()), active["session_id"], active["user_id"], ordinal, time.time(), "system",
            f"TURN_ABORTED:{reason}", active["resource_refs"], json.dumps([effect_id] if effect_id else []),
            json.dumps({"source": "container-recovery", "causal_id": active["causal_id"], "generation": int(active["generation"])}, sort_keys=True),
        ),
    )


def recover_incomplete_episodes(db: UnifiedDB) -> dict[str, int]:
    """Close interrupted work without replay, then advance the one entity generation."""

    # Explicit boot boundary: no concurrent request path performs this recovery.
    EffectJournal(db).recover_pending()

    counts = {
        "scanned": 0,
        "reentered_effects": 0,
        "existing_reentries_closed": 0,
        "aborted_no_effect": 0,
        "uncertain_effects": 0,
        "ambiguous_effects": 0,
        "active_turns_closed": 0,
        "leases_expired": 0,
        "generation": 0,
    }

    with db.tx() as tx:
        active_rows = tx.execute("SELECT * FROM active_turns ORDER BY started_at,session_id").fetchall()
        for active in active_rows:
            counts["scanned"] += 1
            episode = tx.execute("SELECT * FROM workspace_episodes WHERE episode_id=?", (active["episode_id"],)).fetchone()
            if not episode:
                raise RecoveryIntegrityError(f"active turn without workspace episode: {active['episode_id']}")

            causal = tx.execute(
                "SELECT * FROM causal_episodes WHERE episode_id=? ORDER BY ts DESC LIMIT 1", (active["episode_id"],)
            ).fetchone()
            if causal and causal["causal_id"] != active["causal_id"]:
                raise RecoveryIntegrityError("active turn causal identity diverged before recovery")

            effects = tx.execute(
                "SELECT * FROM effects WHERE episode_id=? ORDER BY ts,effect_id", (active["episode_id"],)
            ).fetchall()
            effect_id = causal["effect_id"] if causal else None

            if causal is None:
                if len(effects) == 1 and effects[0]["outcome"] is not None:
                    effect = effects[0]
                    _outcome, outcome_hash, identity_valid = _decode_persisted_effect_outcome(effect["outcome"])
                    effect_id = effect["effect_id"]
                    tx.execute(
                        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,?,1,?)",
                        (
                            active["causal_id"], active["episode_id"], effect_id, active["turn_id"], outcome_hash,
                            0.0, time.time(),
                        ),
                    )
                    # Persisted effect evidence may preserve identity across restart, but
                    # a missing canonical causal row is learning-authority loss. Never
                    # reconstruct positive credit from either redacted or legacy payloads.
                    counts["reentered_effects"] += 1
                    if not identity_valid:
                        counts["uncertain_effects"] += 1
                elif len(effects) > 1:
                    receipt = {"ok": False, "certainty": "unknown", "reason": "multiple_effect_records_after_restart", "count": len(effects)}
                    tx.execute(
                        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,0,1,?)",
                        (active["causal_id"], active["episode_id"], None, active["turn_id"], _hash(receipt), time.time()),
                    )
                    counts["ambiguous_effects"] += 1
                else:
                    reason = "effect_requested_but_no_effect_receipt" if episode["selected"] == "request_effect" else "restart_before_assistant_completion"
                    receipt = {"ok": False, "certainty": "unknown", "reason": reason}
                    tx.execute(
                        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,0,1,?)",
                        (active["causal_id"], active["episode_id"], None, active["turn_id"], _hash(receipt), time.time()),
                    )
                    if episode["selected"] == "request_effect": counts["uncertain_effects"] += 1
                    else: counts["aborted_no_effect"] += 1

            state = "RECOVERY_CLOSED_AFTER_EFFECT_REENTRY" if effect_id else "RECOVERY_ABORTED_INCOMPLETE_TURN"
            tx.execute("UPDATE workspace_episodes SET state=? WHERE episode_id=?", (state, active["episode_id"]))
            _append_recovery_turn(tx, active, "container_restart", effect_id)
            tx.execute("DELETE FROM active_turns WHERE session_id=?", (active["session_id"],))
            counts["active_turns_closed"] += 1

        # EffectJournal may have recovered a legacy PENDING effect that had no active
        # hook row. The causal re-entry now exists; make workspace closure match it.
        already_reentered = tx.execute(
            "SELECT w.episode_id FROM workspace_episodes w "
            "WHERE w.state IN ('OPEN','SELECTED') "
            "AND NOT EXISTS (SELECT 1 FROM active_turns a WHERE a.episode_id=w.episode_id) "
            "AND EXISTS (SELECT 1 FROM causal_episodes c WHERE c.episode_id=w.episode_id)"
        ).fetchall()
        for row in already_reentered:
            tx.execute(
                "UPDATE workspace_episodes SET state='RECOVERY_CLOSED_EXISTING_REENTRY' WHERE episode_id=?",
                (row["episode_id"],),
            )
            counts["existing_reentries_closed"] += 1

        # Legacy/open episodes without an active hook row or causal row are evidence
        # from older artifact generations. Every branch gets an explicit re-entry;
        # unknown stays unknown and no external effect is replayed.
        episodes = tx.execute(
            "SELECT w.* FROM workspace_episodes w "
            "WHERE w.state IN ('OPEN','SELECTED') "
            "AND NOT EXISTS (SELECT 1 FROM active_turns a WHERE a.episode_id=w.episode_id) "
            "AND NOT EXISTS (SELECT 1 FROM causal_episodes c WHERE c.episode_id=w.episode_id) "
            "ORDER BY w.ts,w.episode_id"
        ).fetchall()
        for episode in episodes:
            counts["scanned"] += 1
            effects = tx.execute("SELECT * FROM effects WHERE episode_id=? ORDER BY ts,effect_id", (episode["episode_id"],)).fetchall()
            if len(effects) == 1 and effects[0]["outcome"] is not None:
                effect = effects[0]
                _outcome, outcome_hash, identity_valid = _decode_persisted_effect_outcome(effect["outcome"])
                tx.execute(
                    "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,?,1,?)",
                    (
                        _causal_id(episode["episode_id"], effect["effect_id"]), episode["episode_id"], effect["effect_id"],
                        episode["observation_turn_id"], outcome_hash,
                        0.0, time.time(),
                    ),
                )
                # Missing canonical causal evidence is authority loss. Preserve the
                # effect-outcome identity, never recreate its former positive credit.
                tx.execute("UPDATE workspace_episodes SET state='RECOVERED_LEGACY_EFFECT_REENTERED' WHERE episode_id=?", (episode["episode_id"],))
                counts["reentered_effects"] += 1
                if not identity_valid:
                    counts["uncertain_effects"] += 1
            elif len(effects) > 1:
                _insert_unknown_reentry(tx, episode, "multiple_effect_records_after_restart", count=len(effects))
                tx.execute("UPDATE workspace_episodes SET state='RECOVERY_ABORTED_AMBIGUOUS_EFFECTS' WHERE episode_id=?", (episode["episode_id"],))
                counts["ambiguous_effects"] += 1
            elif episode["selected"] == "request_effect":
                _insert_unknown_reentry(tx, episode, "effect_requested_but_no_effect_receipt")
                tx.execute("UPDATE workspace_episodes SET state='RECOVERY_ABORTED_EFFECT_UNCERTAIN' WHERE episode_id=?", (episode["episode_id"],))
                counts["uncertain_effects"] += 1
            else:
                _insert_unknown_reentry(tx, episode, "restart_before_assistant_completion")
                tx.execute("UPDATE workspace_episodes SET state='RECOVERY_ABORTED_NO_EFFECT' WHERE episode_id=?", (episode["episode_id"],))
                counts["aborted_no_effect"] += 1

        counts["leases_expired"] = int(tx.execute("SELECT COUNT(*) FROM leases WHERE expires_at>0").fetchone()[0])
        tx.execute("UPDATE leases SET expires_at=0")

    counts["generation"] = db.advance_entity_generation()
    return counts
