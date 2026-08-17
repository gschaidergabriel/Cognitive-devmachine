from __future__ import annotations

import hashlib
import json
import time
import uuid

from .effect_journal import EffectJournal
from .store import UnifiedDB


_RECOVERY_NAMESPACE = uuid.UUID("77f43847-1c48-5fa1-918d-eaa7d8db7b5c")


class RecoveryIntegrityError(RuntimeError):
    pass


def _causal_credit(outcome: object) -> float:
    return 1.0 if isinstance(outcome, dict) and outcome.get("ok") is True else 0.0


def _causal_id(episode_id: str, effect_id: str | None) -> str:
    return str(uuid.uuid5(_RECOVERY_NAMESPACE, f"{episode_id}\x1f{effect_id or 'no-effect'}"))


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


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
    """Fail closed over interrupted work, then create one fresh global entity generation.

    This function is the explicit container-restart boundary. Recovery never replays
    an external effect. PENDING effects are first collapsed to UNKNOWN_AFTER_RESTART
    here, not while constructing an EffectJournal in a concurrent MCP/terminal process.
    A hook-created active turn keeps its predeclared causal_id through durable effect
    evidence, but only status VERIFIED is causal re-entry. Finally every old lease is
    expired and both permanent sessions are fenced together into one new entity generation.
    """

    EffectJournal(db).recover_pending()

    counts = {
        "scanned": 0,
        "reentered_effects": 0,
        "non_reentered_effects": 0,
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
                    try:
                        outcome = json.loads(effect["outcome"])
                    except (TypeError, json.JSONDecodeError):
                        outcome = {"ok": False, "certainty": "unknown", "reason": "invalid_persisted_outcome_receipt"}
                    effect_id = effect["effect_id"]
                    reentered = 1 if effect["status"] == "VERIFIED" else 0
                    credit = _causal_credit(outcome) if reentered else 0.0
                    tx.execute(
                        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,?,?,?)",
                        (active["causal_id"], active["episode_id"], effect_id, active["turn_id"], _hash(outcome), credit, reentered, time.time()),
                    )
                    if reentered:
                        counts["reentered_effects"] += 1
                    else:
                        counts["non_reentered_effects"] += 1
                elif len(effects) > 1:
                    receipt = {"ok": False, "certainty": "unknown", "reason": "multiple_effect_records_after_restart", "count": len(effects)}
                    tx.execute(
                        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,0,0,?)",
                        (active["causal_id"], active["episode_id"], None, active["turn_id"], _hash(receipt), time.time()),
                    )
                    counts["ambiguous_effects"] += 1
                else:
                    reason = "effect_requested_but_no_effect_receipt" if episode["selected"] == "request_effect" else "restart_before_assistant_completion"
                    receipt = {"ok": False, "certainty": "unknown", "reason": reason}
                    tx.execute(
                        "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,0,0,?)",
                        (active["causal_id"], active["episode_id"], None, active["turn_id"], _hash(receipt), time.time()),
                    )
                    if episode["selected"] == "request_effect": counts["uncertain_effects"] += 1
                    else: counts["aborted_no_effect"] += 1

            causal_now = tx.execute(
                "SELECT effect_id,reentered FROM causal_episodes WHERE causal_id=?", (active["causal_id"],)
            ).fetchone()
            if causal_now and causal_now["effect_id"] and int(causal_now["reentered"]) == 1:
                state = "RECOVERY_CLOSED_AFTER_EFFECT_REENTRY"
            elif causal_now and causal_now["effect_id"]:
                state = "RECOVERY_CLOSED_AFTER_EFFECT_EVIDENCE"
            else:
                state = "RECOVERY_ABORTED_INCOMPLETE_TURN"
            tx.execute("UPDATE workspace_episodes SET state=? WHERE episode_id=?", (state, active["episode_id"]))
            _append_recovery_turn(tx, active, "container_restart", effect_id)
            tx.execute("DELETE FROM active_turns WHERE session_id=?", (active["session_id"],))
            counts["active_turns_closed"] += 1

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
                try: outcome = json.loads(effect["outcome"])
                except (TypeError, json.JSONDecodeError): outcome = {"ok": False, "certainty": "unknown", "reason": "invalid_persisted_outcome_receipt"}
                reentered = 1 if effect["status"] == "VERIFIED" else 0
                credit = _causal_credit(outcome) if reentered else 0.0
                tx.execute(
                    "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,?,?,?)",
                    (_causal_id(episode["episode_id"], effect["effect_id"]), episode["episode_id"], effect["effect_id"], episode["observation_turn_id"], _hash(outcome), credit, reentered, time.time()),
                )
                state = "RECOVERED_LEGACY_EFFECT_REENTERED" if reentered else "RECOVERED_LEGACY_EFFECT_NOT_REENTERED"
                tx.execute("UPDATE workspace_episodes SET state=? WHERE episode_id=?", (state, episode["episode_id"]))
                if reentered:
                    counts["reentered_effects"] += 1
                else:
                    counts["non_reentered_effects"] += 1
            elif len(effects) > 1:
                tx.execute("UPDATE workspace_episodes SET state='RECOVERY_ABORTED_AMBIGUOUS_EFFECTS' WHERE episode_id=?", (episode["episode_id"],))
                counts["ambiguous_effects"] += 1
            elif episode["selected"] == "request_effect":
                tx.execute("UPDATE workspace_episodes SET state='RECOVERY_ABORTED_EFFECT_UNCERTAIN' WHERE episode_id=?", (episode["episode_id"],))
                counts["uncertain_effects"] += 1
            else:
                tx.execute("UPDATE workspace_episodes SET state='RECOVERY_ABORTED_NO_EFFECT' WHERE episode_id=?", (episode["episode_id"],))
                counts["aborted_no_effect"] += 1

        counts["leases_expired"] = int(tx.execute("SELECT COUNT(*) FROM leases WHERE expires_at>0").fetchone()[0])
        tx.execute("UPDATE leases SET expires_at=0")

    counts["generation"] = db.advance_entity_generation()
    return counts
