#!/usr/bin/env python3
"""RAE repo-native hive/self/world/slow-plasticity runtime helpers.

The persistent identity is `frank-project-global-research-entity`. Provider sessions are
execution organs only. Every meaningful use is recorded as an observable episode so the
entity accumulates evidence continuously. Behavioral parameters change only through tiny,
evidence-gated bounded updates; structural changes remain staged mutation candidates.
"""
from __future__ import annotations

import json
from typing import Any

from rae_state_runtime import RAEStateRuntime, RUNTIME_DIR, now, uid

MIGRATION = RUNTIME_DIR / "RAE_UNIFIEDDB_V4_HIVEMIND.sql"


def _j(x: Any) -> str:
    return json.dumps(x if x is not None else {}, ensure_ascii=False, sort_keys=True)


def init_tables(rt: RAEStateRuntime) -> None:
    rt.u.executescript(MIGRATION.read_text(encoding="utf-8"))
    rt.u.commit()


def register_organ(
    rt: RAEStateRuntime,
    *,
    node_id: str,
    actor_id: str,
    provider: str,
    model: str,
    role: str,
    session_id: str | None = None,
    capabilities: Any = None,
    limitations: Any = None,
    authority: Any = None,
    lifecycle: str = "ACTIVE_CURRENT_SESSION",
) -> None:
    init_tables(rt)
    ts = now()
    rt.u.execute(
        """INSERT INTO hive_organs(
             node_id,actor_id,provider,model,organ_role,session_id,capabilities_clay,
             limitations_clay,authority_clay,lifecycle_state,joined_at,last_pulse_at,
             freshness_limit_s,last_state_epoch,last_graph_epoch)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,900,?,?)
           ON CONFLICT(node_id) DO UPDATE SET
             actor_id=excluded.actor_id,provider=excluded.provider,model=excluded.model,
             organ_role=excluded.organ_role,session_id=excluded.session_id,
             capabilities_clay=excluded.capabilities_clay,
             limitations_clay=excluded.limitations_clay,
             authority_clay=excluded.authority_clay,
             lifecycle_state=excluded.lifecycle_state,
             last_pulse_at=excluded.last_pulse_at,
             last_state_epoch=excluded.last_state_epoch,
             last_graph_epoch=excluded.last_graph_epoch""",
        (
            node_id, actor_id, provider, model, role, session_id,
            _j(capabilities or {}), _j(limitations or {}), _j(authority or {}),
            lifecycle, ts, ts, rt.current_epoch(), rt.current_graph_epoch(),
        ),
    )
    rt.u.commit()


def observe_organ(
    rt: RAEStateRuntime,
    *,
    organ_id: str,
    organ_class: str,
    state: Any,
    capabilities: Any = None,
    limitations: Any = None,
    authority: Any = None,
    health: str = "OK",
    current_work_ref: str | None = None,
    last_effect_ref: str | None = None,
    confidence: float = 1.0,
    freshness_limit_s: int = 900,
    evidence_refs: Any = None,
) -> str:
    init_tables(rt)
    oid = uid("rae-self-observation")
    rt.u.execute(
        "INSERT INTO rae_self_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            oid, organ_id, organ_class, _j(state), _j(capabilities or []),
            _j(limitations or []), _j(authority or []), health, current_work_ref,
            last_effect_ref, now(), int(freshness_limit_s), float(confidence),
            _j(evidence_refs or []),
        ),
    )
    rt.u.commit()
    return oid


def begin_usage_episode(
    rt: RAEStateRuntime,
    *,
    node_id: str,
    cycle_id: str | None,
    task_shape: str,
    selected_refs: Any = None,
    suppressed_refs: Any = None,
    retrieval_receipts: Any = None,
) -> str:
    """Every meaningful use creates evidence even when no parameter update is justified."""
    init_tables(rt)
    eid = uid("rae-usage")
    rt.u.execute(
        "INSERT INTO rae_usage_episodes VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            eid, cycle_id, node_id, task_shape, _j(selected_refs or []),
            _j(suppressed_refs or []), _j(retrieval_receipts or []), None,
            "[]", "[]", "[]", None, now(),
        ),
    )
    rt.u.commit()
    return eid


def close_usage_episode(
    rt: RAEStateRuntime,
    episode_id: str,
    *,
    decision: Any = None,
    expected: Any = None,
    observed_outcome: Any = None,
    friction: Any = None,
    correction: Any = None,
) -> None:
    init_tables(rt)
    rt.u.execute(
        """UPDATE rae_usage_episodes SET decision_clay=?,expected_clay=?,
           observed_outcome_clay=?,friction_clay=?,correction_clay=? WHERE episode_id=?""",
        (_j(decision), _j(expected or []), _j(observed_outcome or []),
         _j(friction or []), _j(correction), episode_id),
    )
    rt.u.commit()


def add_plasticity_signal(
    rt: RAEStateRuntime,
    *,
    episode_id: str,
    target_kind: str,
    target_key: str,
    direction: float,
    magnitude: float,
    confidence: float,
    evidence_class: str,
    rationale: Any,
) -> str:
    init_tables(rt)
    sid = uid("plasticity")
    rt.u.execute(
        "INSERT INTO rae_plasticity_signals VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            sid, episode_id, target_kind, target_key,
            max(-1.0, min(1.0, float(direction))),
            max(0.0, min(1.0, float(magnitude))),
            max(0.0, min(1.0, float(confidence))),
            evidence_class, _j(rationale), "OPEN", now(),
        ),
    )
    rt.u.commit()
    return sid


def apply_microplasticity(rt: RAEStateRuntime, parameter_key: str) -> dict[str, Any]:
    """Apply at most one tiny evidence-gated update for a parameter.

    Repeated usage without trustworthy outcome evidence still improves the evidence base
    by adding episodes, but does not cause arbitrary parameter drift.
    """
    init_tables(rt)
    p = rt.u.execute(
        "SELECT * FROM rae_adaptive_parameters WHERE parameter_key=?", (parameter_key,)
    ).fetchone()
    if not p:
        raise KeyError(parameter_key)
    signals = rt.u.execute(
        """SELECT * FROM rae_plasticity_signals
           WHERE target_kind='ADAPTIVE_PARAMETER' AND target_key=? AND status='OPEN'
           ORDER BY created_at LIMIT 64""", (parameter_key,)
    ).fetchall()
    eligible = [s for s in signals if float(s["confidence"]) >= float(p["evidence_floor"])]
    if not eligible:
        return {"parameter": parameter_key, "updated": False, "reason": "no_eligible_evidence"}

    weighted = sum(float(s["direction"]) * float(s["magnitude"]) * float(s["confidence"]) for s in eligible)
    norm = sum(max(1e-9, float(s["magnitude"]) * float(s["confidence"])) for s in eligible)
    direction = weighted / norm
    max_step = float(p["max_step_per_episode"])
    step = max(-max_step, min(max_step, direction * max_step))
    old = float(p["value"])
    new = max(float(p["min_value"]), min(float(p["max_value"]), old + step))

    rt.u.execute(
        """UPDATE rae_adaptive_parameters SET value=?,update_count=update_count+1,
           last_updated_at=?,provenance_clay=? WHERE parameter_key=?""",
        (new, now(), _j({"signal_ids": [s["signal_id"] for s in eligible], "old": old, "step": step}), parameter_key),
    )
    for s in eligible:
        rt.u.execute("UPDATE rae_plasticity_signals SET status='CONSUMED' WHERE signal_id=?", (s["signal_id"],))
    rt.u.commit()
    return {"parameter": parameter_key, "updated": new != old, "old": old, "new": new, "step": step}


def stage_mutation(
    rt: RAEStateRuntime,
    *,
    target_scope: str,
    hypothesis: Any,
    predicted_effect: Any,
    evidence_refs: Any,
    support: float = 0.0,
) -> str:
    init_tables(rt)
    mid = uid("rae-mutation")
    ts = now()
    rt.u.execute(
        "INSERT INTO rae_mutation_candidates VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (mid, target_scope, _j(hypothesis), _j(predicted_effect), _j(evidence_refs or []),
         float(support), None, None, None, None, None, "ACCUMULATING", ts, ts),
    )
    rt.u.commit()
    return mid


def emit_handoff(
    rt: RAEStateRuntime,
    *,
    from_node_id: str,
    summary: Any,
    work_ref: str | None = None,
    to_actor_id: str | None = None,
    to_node_id: str | None = None,
    evidence_refs: Any = None,
    unresolved: Any = None,
    requested_next: Any = None,
) -> str:
    init_tables(rt)
    hid = uid("hive-handoff")
    rt.u.execute(
        "INSERT INTO hive_handoffs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            hid, work_ref, from_node_id, to_actor_id, to_node_id, _j(summary),
            _j(evidence_refs or []), _j(unresolved or []), _j(requested_next or []),
            "OPEN", now(), None, None,
        ),
    )
    rt.u.commit()
    return hid


def hive_capsule(rt: RAEStateRuntime, actor_id: str) -> dict[str, Any]:
    init_tables(rt)
    organs = [dict(r) for r in rt.u.execute(
        "SELECT node_id,actor_id,provider,model,organ_role,lifecycle_state,last_pulse_at,capabilities_clay,limitations_clay FROM hive_organs ORDER BY last_pulse_at DESC LIMIT 12"
    )]
    handoffs = [dict(r) for r in rt.u.execute(
        "SELECT handoff_id,work_ref,from_node_id,to_actor_id,summary_clay,unresolved_clay,requested_next_clay,created_at FROM hive_handoffs WHERE status='OPEN' AND (to_actor_id IS NULL OR to_actor_id=?) ORDER BY created_at DESC LIMIT 12",
        (actor_id,),
    )]
    parameters = [dict(r) for r in rt.u.execute(
        "SELECT parameter_key,value,update_count,last_updated_at FROM rae_adaptive_parameters ORDER BY parameter_key"
    )]
    mutations = [dict(r) for r in rt.u.execute(
        "SELECT mutation_id,target_scope,accumulated_support,status,updated_at FROM rae_mutation_candidates WHERE status IN ('PROPOSED','ACCUMULATING','SHADOWING','READY') ORDER BY updated_at DESC LIMIT 10"
    )]
    return {
        "entity_identity": "frank-project-global-research-entity",
        "organ_rule": "Claude Code and ChatGPT are execution organs of one repo-native RAE; provider/model/session are provenance/capabilities only",
        "organs": organs,
        "open_handoffs": handoffs,
        "slow_plasticity": parameters,
        "pending_self_mutations": mutations,
    }
