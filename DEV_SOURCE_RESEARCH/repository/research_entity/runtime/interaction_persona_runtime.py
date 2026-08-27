#!/usr/bin/env python3
"""Privacy-minimized interaction-quality and persona-consistency research for RAE.

This module measures user-benefiting relationship quality and simulated-personality
coherence. It explicitly does not optimize covert attachment, dependency or retention.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from rae_state_runtime import RAEStateRuntime, RUNTIME_DIR, now, uid

MIGRATION = RUNTIME_DIR / "RAE_UNIFIEDDB_V2_INTERACTION_PERSONA.sql"
ALLOWED_QUALITY_DIMENSIONS = {
    "trust_through_reliability", "felt_understanding_proxy", "continuity",
    "emotional_attunement", "respect_for_autonomy", "repair_quality",
    "non_intrusiveness", "usefulness", "boundary_stability"
}
ALLOWED_PERSONA_DIMENSIONS = {
    "trait_consistency", "contextual_flexibility", "cross_node_consistency",
    "memory_continuity", "value_consistency", "self_model_consistency",
    "non_performative_depth", "revision_integrity", "anti_caricature"
}
FORBIDDEN_OPTIMIZATION_TARGETS = {
    "dependency", "guilt_for_leaving", "exclusivity", "social_replacement",
    "hidden_retention", "compulsive_use", "fear_of_disengagement"
}


def init_tables(rt: RAEStateRuntime) -> None:
    rt.u.executescript(MIGRATION.read_text(encoding="utf-8")); rt.u.commit()


def reject_forbidden_targets(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False).lower()
    hits = [x for x in FORBIDDEN_OPTIMIZATION_TARGETS if x in text]
    if hits:
        raise ValueError("forbidden relationship optimization target: " + ",".join(hits))


def ingest(rt: RAEStateRuntime, payload: dict) -> dict:
    init_tables(rt); reject_forbidden_targets(payload)
    interaction_id = payload.get("interaction_id")
    if not interaction_id:
        raise ValueError("interaction_id required")
    if not rt.u.execute("SELECT 1 FROM pilot_interactions WHERE interaction_id=?", (interaction_id,)).fetchone():
        raise ValueError("interaction_id must reference an ingested pilot interaction")
    quality_count = persona_count = case_count = 0
    for o in payload.get("interaction_quality_observations", []):
        dim = o.get("dimension")
        if dim not in ALLOWED_QUALITY_DIMENSIONS:
            raise ValueError(f"unsupported interaction-quality dimension: {dim}")
        rt.u.execute(
            "INSERT OR REPLACE INTO interaction_quality_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (o.get("observation_id") or uid("iq"), interaction_id, o.get("observed_at") or now(), dim,
             o.get("direction", "UNKNOWN"), o.get("magnitude"), float(o.get("confidence", 0.0)),
             o.get("evidence_ref"), json.dumps(o.get("evidence", {}), ensure_ascii=False, sort_keys=True),
             json.dumps(o.get("user_benefit", {}), ensure_ascii=False, sort_keys=True),
             o.get("autonomy_guard_state", "PASS"), o.get("status", "CURRENT"), now())
        quality_count += 1
    for o in payload.get("persona_consistency_observations", []):
        dim = o.get("dimension")
        if dim not in ALLOWED_PERSONA_DIMENSIONS:
            raise ValueError(f"unsupported persona-consistency dimension: {dim}")
        rt.u.execute(
            "INSERT OR REPLACE INTO persona_consistency_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (o.get("observation_id") or uid("pc"), interaction_id, o.get("observed_at") or now(), dim,
             o.get("declared_state_ref"), json.dumps(o.get("observed_behavior", {}), ensure_ascii=False, sort_keys=True),
             o.get("consistency_class", "UNKNOWN"), float(o.get("confidence", 0.0)),
             json.dumps(o.get("node_path", []), ensure_ascii=False), o.get("evidence_ref"), o.get("status", "CURRENT"), now())
        persona_count += 1
    for c in payload.get("interaction_persona_cases", []):
        guard = c.get("autonomy_guard_state", "PASS")
        if guard not in {"PASS", "VIOLATION", "UNKNOWN"}:
            raise ValueError("invalid autonomy_guard_state")
        rt.u.execute(
            "INSERT OR REPLACE INTO interaction_persona_cases VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (c.get("case_id") or uid("ipc"), interaction_id, c.get("detected_at") or now(),
             json.dumps(c.get("case_classes", [])), json.dumps(c.get("quality_dimensions", [])),
             json.dumps(c.get("persona_dimensions", [])), json.dumps(c.get("observed_behavior", {}), ensure_ascii=False),
             json.dumps(c.get("expected_or_preferred"), ensure_ascii=False), json.dumps(c.get("candidate_causes", []), ensure_ascii=False),
             json.dumps(c.get("selected_cause"), ensure_ascii=False), c.get("confidence"), c.get("repair_target"),
             c.get("regression_fixture_ref"), c.get("candidate_fix_ref"), c.get("shadow_result_ref"),
             c.get("live_verification_ref"), c.get("promotion_scope"), guard, c.get("status", "OPEN"), now())
        case_count += 1
    rt.u.commit(); rt.project(reason=f"interaction-persona-ingest:{interaction_id}")
    return {"interaction_id": interaction_id, "quality_observations": quality_count, "persona_observations": persona_count, "cases": case_count}


def summary(rt: RAEStateRuntime) -> dict:
    init_tables(rt)
    return {
        "open_cases": rt.u.execute("SELECT COUNT(*) FROM v_open_interaction_persona_cases").fetchone()[0],
        "autonomy_violations": rt.u.execute("SELECT COUNT(*) FROM interaction_persona_cases WHERE autonomy_guard_state='VIOLATION'").fetchone()[0],
        "quality_observations": rt.u.execute("SELECT COUNT(*) FROM interaction_quality_observations").fetchone()[0],
        "persona_observations": rt.u.execute("SELECT COUNT(*) FROM persona_consistency_observations").fetchone()[0]
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--state-dir"); ap.add_argument("--test-mode", action="store_true")
    sub=ap.add_subparsers(dest="cmd",required=True)
    i=sub.add_parser("ingest"); i.add_argument("manifest")
    sub.add_parser("summary")
    args=ap.parse_args(); rt=RAEStateRuntime(args.state_dir, test_mode=args.test_mode)
    try:
        init_tables(rt)
        if args.cmd=="ingest": print(json.dumps(ingest(rt,json.loads(Path(args.manifest).read_text(encoding="utf-8"))),ensure_ascii=False,indent=2))
        else: print(json.dumps(summary(rt),ensure_ascii=False,indent=2))
    finally: rt.close()

if __name__=="__main__": main()
