from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from .microclay_methods import METHOD_KINDS
from .microclay_retrieval import MicroClayRetrieval, _CONTROL_KINDS
from .store import StaleGeneration


def _parse_memory_ids(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except Exception as exc:
        raise StaleGeneration("retrieval_route_contract") from exc
    if not isinstance(value, list) or not all(
        isinstance(memory_id, str) and memory_id for memory_id in value
    ):
        raise StaleGeneration("retrieval_route_contract")
    return value


def _update_route_capital(
    organ: MicroClayRetrieval,
    db,
    *,
    entry_key: str,
    value: float,
    now: float,
) -> None:
    current = db.execute(
        "SELECT capital,reward_ema,pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
        (entry_key,),
    ).fetchone()
    if current:
        old_capital = float(current["capital"])
        old_ema = float(current["reward_ema"])
        pulls = int(current["pulls"])
    else:
        old_capital, old_ema, pulls = 0.0, 0.0, 0
    new_ema = (
        (1.0 - organ.REWARD_EMA_ALPHA) * old_ema
        + organ.REWARD_EMA_ALPHA * value
    )
    delta = organ.LEARNING_RATE * (value - old_ema) - organ.ACCESS_RENT
    new_capital = max(
        organ.CAPITAL_MIN,
        min(organ.CAPITAL_MAX, old_capital + delta),
    )
    db.execute(
        "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) "
        "VALUES(?,?,?,?,?) ON CONFLICT(entry_key) DO UPDATE SET "
        "capital=excluded.capital,reward_ema=excluded.reward_ema,"
        "pulls=excluded.pulls,updated_at=excluded.updated_at",
        (entry_key, new_capital, new_ema, pulls + 1, now),
    )


def apply_explicit_retrieval_miss(
    organ: MicroClayRetrieval,
    *,
    retrieval_id: str,
    source_turn_id: str,
    memory_id: str,
    user_id: str,
    session_id: str,
    generation: int,
) -> dict[str, Any]:
    """Teach one query->memory-subject entry route from explicit later user feedback.

    This is deliberately narrower than generic caller-supplied reward. The target must
    be an evidence memory that already existed when the original retrieval ran, was
    visible to the same user, and was not selected. The feedback source must be a
    later canonical user turn in the same session. The original canonical turn text is
    hash-checked against the retrieval receipt before its tokens are reused, so callers
    cannot substitute a different query when teaching the route.

    Only hashed query->subject route capital changes. Durable memory, provenance,
    factual status, user rights and effect authority are never changed here. The write
    joins an existing canonical turn transaction when one is active; standalone calls
    receive one atomic transaction through the retained MicroClay transaction helper.
    """
    if not all(isinstance(value, str) and value for value in (
        retrieval_id, source_turn_id, memory_id, user_id, session_id
    )):
        raise ValueError("explicit retrieval miss requires non-empty identities")

    with organ._credit_tx() as db:
        row = db.execute(
            "SELECT * FROM retrieval_episodes WHERE retrieval_id=?",
            (retrieval_id,),
        ).fetchone()
        if not row:
            raise KeyError(retrieval_id)
        if (
            row["user_id"] != user_id
            or row["session_id"] != session_id
            or int(row["generation"]) != int(generation)
        ):
            raise StaleGeneration("retrieval_feedback_identity")
        organ.db.assert_live_generation(session_id, generation)
        organ._assert_replay_route(row)

        original_turn = db.execute(
            "SELECT turn_id,session_id,user_id,role,content,ordinal FROM turns WHERE turn_id=?",
            (row["turn_id"],),
        ).fetchone()
        if not original_turn:
            raise StaleGeneration("retrieval_feedback_source")
        if (
            original_turn["session_id"] != session_id
            or original_turn["user_id"] != user_id
            or original_turn["role"] != "user"
        ):
            raise StaleGeneration("retrieval_feedback_source")
        if hashlib.sha256(original_turn["content"].encode("utf-8")).hexdigest() != row["query_hash"]:
            raise StaleGeneration("retrieval_query_contract")

        feedback_turn = db.execute(
            "SELECT turn_id,session_id,user_id,role,ordinal FROM turns WHERE turn_id=?",
            (source_turn_id,),
        ).fetchone()
        if not feedback_turn:
            raise KeyError(source_turn_id)
        if (
            feedback_turn["session_id"] != session_id
            or feedback_turn["user_id"] != user_id
            or feedback_turn["role"] != "user"
        ):
            raise PermissionError("retrieval feedback must come from the same canonical user session")
        if int(feedback_turn["ordinal"]) <= int(original_turn["ordinal"]):
            raise ValueError("retrieval feedback must be a later canonical user turn")

        target = db.execute(
            "SELECT memory_id,kind,subject,user_id,ts FROM durable_memory WHERE memory_id=?",
            (memory_id,),
        ).fetchone()
        if not target:
            raise KeyError(memory_id)
        if str(target["kind"]) in (METHOD_KINDS | _CONTROL_KINDS):
            raise PermissionError("retrieval feedback target is not Stage-A evidence")
        if target["user_id"] is not None and target["user_id"] != user_id:
            raise PermissionError("retrieval feedback cannot cross the user memory boundary")
        if float(target["ts"]) > float(row["ts"]):
            raise ValueError("retrieval miss target did not exist at retrieval time")

        selected_ids = _parse_memory_ids(row["selected_memory_ids"])
        if memory_id in selected_ids:
            raise ValueError("retrieval miss target was already selected")

        query_tokens = set(sorted(organ._tokens(original_turn["content"]))[: organ.MAX_QUERY_TOKENS])
        if not query_tokens:
            raise ValueError("retrieval miss has no routable query cues")
        route_keys = sorted({organ._route_key(token, str(target["subject"])) for token in query_tokens})
        if not route_keys or len(route_keys) > organ.MAX_QUERY_TOKENS:
            raise StaleGeneration("retrieval_feedback_route_contract")

        signal_class = f"user_feedback:miss:{source_turn_id}:{memory_id}"
        receipt_id = hashlib.sha256(
            f"{retrieval_id}\x1f{source_turn_id}\x1f{memory_id}\x1f{session_id}\x1f{generation}\x1fmiss".encode()
        ).hexdigest()
        if db.execute(
            "SELECT 1 FROM retrieval_feedback WHERE receipt_id=?",
            (receipt_id,),
        ).fetchone():
            return {
                "applied": False,
                "reason": "duplicate_receipt",
                "receipt_id": receipt_id,
            }

        now = time.time()
        for entry_key in route_keys:
            _update_route_capital(organ, db, entry_key=entry_key, value=1.0, now=now)

        db.execute(
            "INSERT INTO retrieval_feedback(receipt_id,retrieval_id,causal_id,generation,"
            "credit,signal_class,ts) VALUES(?,?,?,?,?,?,?)",
            (
                receipt_id,
                retrieval_id,
                row["causal_id"],
                int(generation),
                1.0,
                signal_class,
                now,
            ),
        )

    return {
        "applied": True,
        "receipt_id": receipt_id,
        "signal_class": "user_feedback:miss",
        "updated_entrypoints": len(route_keys),
        "memory_id": memory_id,
        "source_turn_id": source_turn_id,
        "policy_version": organ.POLICY_VERSION,
        "mode": organ.mode(),
        "truth_authority": False,
        "effect_authority": False,
    }
