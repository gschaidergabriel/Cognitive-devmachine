#!/usr/bin/env python3
"""Automatic observable cognition/operation -> ClayCode research derivation.

This module never requests or stores hidden provider chain-of-thought. It consumes only
observable explicit traces, state/tool receipts, corrections, outcomes and compact shape
metadata. Every observation is automatically derived into a research pattern, but no
single observation can directly mutate ClayCode.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any

from rae_state_runtime import RAEStateRuntime, RUNTIME_DIR, now, uid

MIGRATION = RUNTIME_DIR / "RAE_UNIFIEDDB_V6_CLAYCODE_META_COGNITION.sql"
DERIVATION_VERSION = "cc-meta-v1"


def _j(x: Any) -> str:
    return json.dumps(x if x is not None else {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _loads(x: Any, default: Any) -> Any:
    if x is None:
        return default
    if not isinstance(x, str):
        return x
    try:
        return json.loads(x)
    except Exception:
        return default


def init_tables(rt: RAEStateRuntime) -> None:
    rt.u.executescript(MIGRATION.read_text(encoding="utf-8"))
    rt.u.commit()


def compact_text_shape(text: str | None) -> dict[str, Any]:
    """Privacy-minimized shape only; no raw text persistence."""
    s = text or ""
    clay_marks = sum(s.count(x) for x in ("{", "}", "[", "]", "=", ";", "->", "iff", "invariant", "tensor", "rule"))
    words = len(s.split())
    return {
        "chars": len(s),
        "words": words,
        "lines": s.count("\n") + (1 if s else 0),
        "clay_marks": clay_marks,
        "clay_density": round(clay_marks / max(1, words), 4),
        "digest": hashlib.sha256(s.encode("utf-8")).hexdigest()[:16] if s else None,
    }


def _infer_layers(event_class: str, trace_class: str, properties: list[str]) -> list[str]:
    p = set(properties)
    out: list[str] = []
    rules = [
        ({"token_waste", "verbose", "redundant_context"}, "compression_projection"),
        ({"retrieval_miss", "state_miss", "wrong_context"}, "query_state_ir"),
        ({"stale_state", "temporal_conflict"}, "temporal_semantics"),
        ({"misunderstanding", "semantic_loss", "ambiguity"}, "semantic_primitives"),
        ({"wrong_route", "routing_error", "capability_miss"}, "gwt_routing"),
        ({"repair", "recovery", "rollback"}, "reentry_recovery"),
        ({"tool_friction", "adapter_friction", "effect_error"}, "needle_effect_boundary"),
        ({"good_outcome", "high_efficiency"}, "preserve_successful_ir"),
        ({"status_error", "surface_error"}, "surface_contract"),
        ({"handoff_loss", "cross_organ_loss"}, "handoff_ir"),
    ]
    for hits, layer in rules:
        if p & hits:
            out.append(layer)
    e = event_class.lower()
    t = trace_class.lower()
    if "tool" in e and "needle_effect_boundary" not in out:
        out.append("needle_effect_boundary")
    if "handoff" in e and "handoff_ir" not in out:
        out.append("handoff_ir")
    if "gwt" in t and "gwt_routing" not in out:
        out.append("gwt_routing")
    if not out:
        out.append("general_claycode_usage")
    return out


def _candidate_primitives(layers: list[str], properties: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    mapping = {
        "compression_projection": {"family": "compression", "candidate": "pointer/delta primitive or denser typed relation"},
        "query_state_ir": {"family": "query", "candidate": "typed state-query/select primitive"},
        "temporal_semantics": {"family": "time", "candidate": "valid/observed/epoch primitive"},
        "semantic_primitives": {"family": "semantics", "candidate": "missing typed distinction or ambiguity carrier"},
        "gwt_routing": {"family": "gwt", "candidate": "selection/receiver/reentry primitive"},
        "reentry_recovery": {"family": "reentry", "candidate": "repair/replay/rollback primitive"},
        "needle_effect_boundary": {"family": "effect", "candidate": "intent/authority/execution/verification split"},
        "preserve_successful_ir": {"family": "preservation", "candidate": "retain efficient primitive/projection"},
        "surface_contract": {"family": "surface", "candidate": "typed renderer/status primitive"},
        "handoff_ir": {"family": "handoff", "candidate": "causal cross-organ handoff primitive"},
    }
    for layer in layers:
        if layer in mapping:
            out.append(mapping[layer])
    if properties:
        out.append({"observed_properties": sorted(set(properties))})
    return out


def record_observation(
    rt: RAEStateRuntime,
    *,
    node_id: str,
    actor_id: str | None,
    event_class: str,
    trace_class: str,
    trace_shape: Any,
    cycle_id: str | None = None,
    state_refs: Any = None,
    operation_refs: Any = None,
    outcome_refs: Any = None,
    properties: list[str] | None = None,
    token_cost_estimate: float | None = None,
    latency_cost_ms: float | None = None,
    evidence_class: str = "OBSERVABLE_RUNTIME",
    confidence: float = 0.8,
) -> str:
    init_tables(rt)
    props = list(properties or [])
    layers = _infer_layers(event_class, trace_class, props)
    prims = _candidate_primitives(layers, props)
    oid = uid("cc-meta-observation")
    ts = now()
    rt.u.execute(
        "INSERT INTO claycode_meta_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            oid, cycle_id, node_id, actor_id, event_class, ts, trace_class,
            _j(trace_shape), _j(state_refs or []), _j(operation_refs or []), _j(outcome_refs or []),
            _j(props), _j(layers), _j(prims), token_cost_estimate, latency_cost_ms,
            evidence_class, max(0.0, min(1.0, float(confidence))), "OPEN", ts,
        ),
    )
    rt.u.commit()
    derive_observation(rt, oid)
    return oid


def _polarity(props: set[str]) -> tuple[int, int, int]:
    pos = int(bool(props & {"good_outcome", "high_efficiency", "repair_success"}))
    neg = int(bool(props & {"misunderstanding", "retrieval_miss", "stale_state", "wrong_route", "effect_error", "handoff_loss", "status_error"}))
    friction = int(bool(props & {"friction", "awkwardness", "token_waste", "verbose", "redundant_context", "tool_friction"}))
    return pos, neg, friction


def derive_observation(rt: RAEStateRuntime, observation_id: str) -> str:
    init_tables(rt)
    o = rt.u.execute("SELECT * FROM claycode_meta_observations WHERE observation_id=?", (observation_id,)).fetchone()
    if not o:
        raise KeyError(observation_id)
    props = set(_loads(o["detected_properties_clay"], []))
    layers = _loads(o["suspected_claycode_layers_clay"], ["general_claycode_usage"])
    primitives = _loads(o["candidate_primitives_clay"], [])
    layer = str(layers[0] if layers else "general_claycode_usage")
    trace_shape = _loads(o["trace_shape_clay"], {})
    shape_bucket = str(trace_shape.get("shape") or trace_shape.get("event") or o["trace_class"])
    pattern_key = f"{layer}:{o['trace_class']}:{shape_bucket}"[:240]
    pos, neg, friction = _polarity(props)
    weight = float(o["confidence"]) * (1.0 + 0.35 * neg + 0.20 * friction + 0.15 * pos)
    ts = now()
    row = rt.u.execute(
        "SELECT * FROM claycode_meta_patterns WHERE pattern_key=? AND status IN ('ACCUMULATING','READY_FOR_EXPERIMENT','EXPERIMENTING') ORDER BY last_seen_at DESC LIMIT 1",
        (pattern_key,),
    ).fetchone()
    hypothesis = {
        "claim": f"ClayCode layer {layer} can be improved or preserved based on repeated observable usage",
        "source": "observable_explicit_cognition_and_operation_trace",
    }
    counter = {
        "claim": "pattern is provider/task/orchestration noise rather than a ClayCode language defect or strength",
        "required_control": "matched task/model/state budget when feasible",
    }
    language_delta = {
        "candidate_primitives": primitives,
        "action": "preserve" if pos and not (neg or friction) else "investigate_change",
        "no_direct_promotion": True,
    }
    predicted = {"metrics": ["task_success", "verified_outcome_per_token", "repair_rate", "state_error_rate", "latency", "transfer"]}
    falsifier = {"fail_if": ["no matched-budget gain", "hard regression", "benefit disappears across task/provider controls"]}
    bench = {"arms": ["current_claycode", "candidate_claycode"], "require": ["same evidence", "same task", "replay", "negative_result_capture", "rollback"]}
    if row:
        ids = _loads(row["observation_ids_clay"], [])
        if observation_id not in ids:
            ids.append(observation_id)
        count = int(row["count_total"]) + 1
        total_weight = float(row["accumulated_weight"]) + weight
        status = "READY_FOR_EXPERIMENT" if count >= 3 or total_weight >= 3.0 else "ACCUMULATING"
        rt.u.execute(
            """UPDATE claycode_meta_patterns SET last_seen_at=?,observation_ids_clay=?,count_total=?,
               count_positive=count_positive+?,count_negative=count_negative+?,count_friction=count_friction+?,
               accumulated_weight=?,candidate_language_delta_clay=?,status=? WHERE pattern_id=?""",
            (ts, _j(ids), count, pos, neg, friction, total_weight, _j(language_delta), status, row["pattern_id"]),
        )
        pid = row["pattern_id"]
    else:
        pid = uid("cc-meta-pattern")
        status = "READY_FOR_EXPERIMENT" if weight >= 1.4 else "ACCUMULATING"
        rt.u.execute(
            "INSERT INTO claycode_meta_patterns VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                pid, pattern_key, layer, ts, ts, _j([observation_id]), 1, pos, neg, friction, weight,
                _j(hypothesis), _j(counter), _j(language_delta), _j(predicted), _j(falsifier), _j(bench), status,
            ),
        )
    rid = uid("cc-meta-derive")
    conclusion = {"pattern": pattern_key, "target_layer": layer, "candidate": language_delta, "status": status}
    rt.u.execute(
        "INSERT INTO claycode_meta_derivation_receipts VALUES(?,?,?,?,?,?,?,?)",
        (rid, observation_id, pid, ts, DERIVATION_VERSION, _j(["layer_rules", "polarity_rules", "evidence_gate"]), _j(conclusion), _j({"confidence": o["confidence"], "causality": "UNPROVEN_UNTIL_EXPERIMENT"}), "DERIVED"),
    )
    rt.u.execute("UPDATE claycode_meta_observations SET status='DERIVED' WHERE observation_id=?", (observation_id,))
    rt.u.commit()
    return pid


def queue(rt: RAEStateRuntime, limit: int = 20) -> list[dict[str, Any]]:
    init_tables(rt)
    return [dict(r) for r in rt.u.execute("SELECT * FROM v_claycode_meta_research_queue LIMIT ?", (int(limit),))]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir")
    ap.add_argument("--test-mode", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--node", required=True); r.add_argument("--actor")
    r.add_argument("--event", required=True); r.add_argument("--trace-class", required=True)
    r.add_argument("--shape-json", default="{}")
    r.add_argument("--properties", default="")
    r.add_argument("--cycle"); r.add_argument("--token-cost", type=float); r.add_argument("--latency-ms", type=float)
    sub.add_parser("queue")
    args = ap.parse_args()
    rt = RAEStateRuntime(args.state_dir, test_mode=args.test_mode)
    try:
        init_tables(rt)
        if args.cmd == "record":
            oid = record_observation(
                rt, node_id=args.node, actor_id=args.actor, event_class=args.event,
                trace_class=args.trace_class, trace_shape=json.loads(args.shape_json), cycle_id=args.cycle,
                properties=[x for x in args.properties.split(",") if x], token_cost_estimate=args.token_cost,
                latency_cost_ms=args.latency_ms,
            )
            print(json.dumps({"observation_id": oid}, separators=(",", ":")))
        else:
            print(json.dumps(queue(rt), ensure_ascii=False, separators=(",", ":")))
    finally:
        rt.close()


if __name__ == "__main__":
    main()
