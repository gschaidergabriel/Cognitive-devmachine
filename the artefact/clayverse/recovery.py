from __future__ import annotations

import hashlib
import json
import time
import uuid

from .store import UnifiedDB


_RECOVERY_NAMESPACE = uuid.UUID("77f43847-1c48-5fa1-918d-eaa7d8db7b5c")


def _causal_credit(outcome: object) -> float:
    return 1.0 if isinstance(outcome, dict) and outcome.get("ok") is True else 0.0


def _causal_id(episode_id: str, effect_id: str) -> str:
    return str(uuid.uuid5(_RECOVERY_NAMESPACE, f"{episode_id}\x1f{effect_id}"))


def recover_incomplete_episodes(db: UnifiedDB) -> dict[str, int]:
    """Fail closed over interrupted workspace episodes without replaying effects.

    A persisted effect outcome is already an observed fact and may be causally
    re-entered after a crash. A selected effect request without exactly one valid
    persisted outcome is ambiguous: the external action might have happened before
    the process died, so recovery must never execute it again automatically.
    """

    counts = {
        "scanned": 0,
        "reentered_effects": 0,
        "aborted_no_effect": 0,
        "uncertain_effects": 0,
        "ambiguous_effects": 0,
    }

    with db.tx() as tx:
        episodes = tx.execute(
            "SELECT w.* FROM workspace_episodes w "
            "WHERE w.state IN ('OPEN','SELECTED') "
            "AND NOT EXISTS (SELECT 1 FROM causal_episodes c WHERE c.episode_id=w.episode_id) "
            "ORDER BY w.ts,w.episode_id"
        ).fetchall()

        for episode in episodes:
            counts["scanned"] += 1
            effects = tx.execute(
                "SELECT * FROM effects WHERE episode_id=? ORDER BY ts,effect_id",
                (episode["episode_id"],),
            ).fetchall()

            if not effects:
                if episode["selected"] == "request_effect":
                    tx.execute(
                        "UPDATE workspace_episodes SET state='RECOVERY_ABORTED_EFFECT_UNCERTAIN' WHERE episode_id=?",
                        (episode["episode_id"],),
                    )
                    counts["uncertain_effects"] += 1
                else:
                    tx.execute(
                        "UPDATE workspace_episodes SET state='RECOVERY_ABORTED_NO_EFFECT' WHERE episode_id=?",
                        (episode["episode_id"],),
                    )
                    counts["aborted_no_effect"] += 1
                continue

            if len(effects) != 1:
                tx.execute(
                    "UPDATE workspace_episodes SET state='RECOVERY_ABORTED_AMBIGUOUS_EFFECTS' WHERE episode_id=?",
                    (episode["episode_id"],),
                )
                counts["ambiguous_effects"] += 1
                continue

            effect = effects[0]
            if effect["outcome"] is None:
                tx.execute(
                    "UPDATE workspace_episodes SET state='RECOVERY_ABORTED_EFFECT_OUTCOME_UNKNOWN' WHERE episode_id=?",
                    (episode["episode_id"],),
                )
                counts["uncertain_effects"] += 1
                continue

            try:
                outcome = json.loads(effect["outcome"])
            except (TypeError, json.JSONDecodeError):
                outcome = None
            if not isinstance(outcome, dict):
                tx.execute(
                    "UPDATE workspace_episodes SET state='RECOVERY_ABORTED_EFFECT_OUTCOME_UNKNOWN' WHERE episode_id=?",
                    (episode["episode_id"],),
                )
                counts["uncertain_effects"] += 1
                continue

            outcome_hash = hashlib.sha256(
                json.dumps(outcome, sort_keys=True).encode()
            ).hexdigest()
            causal_id = _causal_id(episode["episode_id"], effect["effect_id"])
            tx.execute(
                "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
                "VALUES(?,?,?,?,?,?,1,?)",
                (
                    causal_id,
                    episode["episode_id"],
                    effect["effect_id"],
                    episode["observation_turn_id"],
                    outcome_hash,
                    _causal_credit(outcome),
                    time.time(),
                ),
            )
            tx.execute(
                "UPDATE workspace_episodes SET state='RECOVERED_EFFECT_REENTERED' WHERE episode_id=?",
                (episode["episode_id"],),
            )
            counts["reentered_effects"] += 1

    return counts
