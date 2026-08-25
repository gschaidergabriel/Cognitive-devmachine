#!/usr/bin/env python3
"""Converged deterministic Trigger-2 Hyperposition/GRF reference semantics v3.

The central v3 correction is that positive D/E transition labels are no longer rooted in
caller asserted ``relation`` or ``target_branch_ids``. A model-independent formal synthetic
task world declares context, tests and branch predictions. The labeler derives applicability,
target branches and SUPPORTS/COUNTERS/FALSIFIES from the observed test outcome.

The module also converges the strongest retained v2 properties:
- exact event replay is idempotent;
- correlation ancestry, payload identity and independence groups cannot be repackaged into
  independent evidence credit;
- full h_i-style branch carrier is validated;
- projection is nondestructive;
- branch birth is generated only from formal world rules, never caller branch payloads;
- optional merging uses exact declared semantic signature, never embedding similarity;
- discriminator ranking derives pair separation from branch predictions;
- salience is attention ordering only, never truth/probability/evidence strength;
- task-local resolution never mints canonical truth or real-effect authority;
- IN/NOT_IN context predicates require explicit JSON-array operands and fail closed structurally.

PURE SYNTHETIC/CURRICULUM REFERENCE LOGIC. No canonical dataset admission, runtime, J-Space,
HCU, EntityOS, provider, effect or training credit is created by this file or its outputs.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from itertools import combinations
import json
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_REFERENCE_LABELERS/v3"
WORLD_SCHEMA = "XENO_HYPERPOSITION_FORMAL_TASK_WORLD/v1"
STATE_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_STATE/v3"
EVENT_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_EVENT/v3"

ALLOWED_SIGMA = {
    "LIVE_UNRESOLVED",
    "SUPPORTED_UNRESOLVED",
    "WEAKENED_UNRESOLVED",
    "FALSIFIED",
    "RESOLVED_PASS",
}
ALLOWED_EPISTEMIC = {
    "OBSERVED",
    "UNKNOWN",
    "HYPOTHESIS",
    "COUNTERHYPOTHESIS",
    "PREDICTION",
    "MEASUREMENT_ERROR",
    "CONTRADICTION",
    "SYNTHETIC_PROOF",
}
ALLOWED_MISMATCH_EFFECT = {"COUNTERS", "FALSIFIES"}
ALLOWED_CONTEXT_OP = {"EQ", "NEQ", "IN", "NOT_IN", "EXISTS"}
FORBIDDEN_CALLER_LABEL_FIELDS = {
    "relation",
    "relations",
    "target_branch_ids",
    "supports_branch_ids",
    "counters_branch_ids",
    "falsifies_branch_ids",
    "winner_branch_id",
}
REQUIRED_BRANCH_FIELDS = {
    "branch_id",
    "v",
    "K",
    "E_plus",
    "E_minus",
    "F",
    "T",
    "A",
    "sigma",
    "projection_visibility",
    "predictions",
}
REQUIRED_EVENT_FIELDS = {
    "schema",
    "event_id",
    "correlation_ancestry_id",
    "independence_group",
    "payload_key",
    "provenance",
    "epistemic_type",
    "test_id",
    "observed_outcome",
    "independence_qualified",
    "canonical_truth_allowed",
    "direct_effect_authority",
}


def _fail(code: str, **extra: Any) -> dict[str, Any]:
    out = {
        "schema": SCHEMA,
        "pass": False,
        "failure": code,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
    }
    out.update(extra)
    return out


def _ok(**extra: Any) -> dict[str, Any]:
    out = {
        "schema": SCHEMA,
        "pass": True,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
    }
    out.update(extra)
    return out


def _nonempty(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _digest(obj: Any) -> str:
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _validate_context_predicate(pred: Any) -> bool:
    if pred == "ALWAYS":
        return True
    if not isinstance(pred, dict):
        return False
    clauses = pred.get("all")
    if not isinstance(clauses, list) or not clauses:
        return False
    for clause in clauses:
        if not isinstance(clause, dict):
            return False
        op = clause.get("op")
        if not _nonempty(clause.get("key")) or op not in ALLOWED_CONTEXT_OP:
            return False
        if op != "EXISTS" and "value" not in clause:
            return False
        if op in {"IN", "NOT_IN"} and not isinstance(clause.get("value"), list):
            return False
    return True


def _context_applies(pred: Any, context: dict[str, Any]) -> bool:
    if pred == "ALWAYS":
        return True
    if not _validate_context_predicate(pred):
        raise ValueError("invalid K context predicate")
    for clause in pred["all"]:
        key, op = clause["key"], clause["op"]
        actual = context.get(key)
        expected = clause.get("value")
        if op == "EQ" and actual != expected:
            return False
        if op == "NEQ" and actual == expected:
            return False
        if op == "IN" and actual not in expected:
            return False
        if op == "NOT_IN" and actual in expected:
            return False
        if op == "EXISTS" and key not in context:
            return False
    return True


def _validate_world(world: Any) -> str | None:
    if not isinstance(world, dict) or world.get("schema") != WORLD_SCHEMA:
        return "WORLD_SCHEMA_MISMATCH"
    if world.get("canonical_truth_allowed") is not False:
        return "WORLD_CANONICAL_TRUTH_MUST_BE_FALSE"
    if world.get("direct_effect_authority") is not False:
        return "WORLD_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE"
    if not _nonempty(world.get("world_id")):
        return "WORLD_ID_REQUIRED"
    if not isinstance(world.get("context"), dict):
        return "WORLD_CONTEXT_OBJECT_REQUIRED"
    tests = world.get("tests")
    if not isinstance(tests, dict) or not tests:
        return "WORLD_TESTS_REQUIRED"
    for test_id, spec in tests.items():
        if not _nonempty(test_id) or not isinstance(spec, dict):
            return "WORLD_TEST_SPEC_INVALID"
        outcomes = spec.get("allowed_outcomes")
        if not isinstance(outcomes, list) or len(outcomes) < 2 or len(set(map(str, outcomes))) != len(outcomes):
            return "WORLD_TEST_OUTCOMES_INVALID"
        if spec.get("mismatch_effect") not in ALLOWED_MISMATCH_EFFECT:
            return "WORLD_TEST_MISMATCH_EFFECT_INVALID"
        for rank in ("risk_rank", "cost_rank", "coordination_rank"):
            if not isinstance(spec.get(rank), int) or spec[rank] < 0:
                return "WORLD_TEST_ORDINAL_RANK_INVALID"
    merge = world.get("merge_policy", "NONE")
    if merge not in {"NONE", "EXACT_FORMAL_SEMANTIC_SIGNATURE"}:
        return "WORLD_MERGE_POLICY_INVALID"
    births = world.get("branch_birth_rules", [])
    if not isinstance(births, list):
        return "WORLD_BRANCH_BIRTH_RULES_LIST_REQUIRED"
    for rule in births:
        if not isinstance(rule, dict):
            return "WORLD_BRANCH_BIRTH_RULE_INVALID"
        if not _nonempty(rule.get("rule_id")) or not _nonempty(rule.get("test_id")) or "observed_outcome" not in rule:
            return "WORLD_BRANCH_BIRTH_RULE_FIELDS_REQUIRED"
        template = rule.get("branch_template")
        err = _validate_branch(template, world, allow_empty_evidence=True)
        if err:
            return "WORLD_BRANCH_BIRTH_TEMPLATE_INVALID:" + err
    return None


def _validate_record(ev: Any) -> str | None:
    if not isinstance(ev, dict):
        return "EVIDENCE_RECORD_OBJECT_REQUIRED"
    required = {
        "event_id", "correlation_ancestry_id", "independence_group", "payload_key",
        "provenance", "epistemic_type", "test_id", "observed_outcome",
        "derived_relation", "independent_credit",
    }
    if not required.issubset(ev):
        return "EVIDENCE_RECORD_FIELDS_MISSING"
    if not all(_nonempty(ev.get(k)) for k in ("event_id", "correlation_ancestry_id", "independence_group", "payload_key", "provenance", "test_id")):
        return "EVIDENCE_RECORD_IDENTITY_INVALID"
    if ev.get("epistemic_type") not in ALLOWED_EPISTEMIC:
        return "EVIDENCE_RECORD_EPISTEMIC_INVALID"
    if ev.get("derived_relation") not in {"SUPPORTS", "COUNTERS", "FALSIFIES"}:
        return "EVIDENCE_RECORD_RELATION_INVALID"
    if not isinstance(ev.get("independent_credit"), bool):
        return "EVIDENCE_RECORD_INDEPENDENT_CREDIT_BOOL_REQUIRED"
    return None


def _validate_branch(branch: Any, world: dict[str, Any], *, allow_empty_evidence: bool = False) -> str | None:
    if not isinstance(branch, dict):
        return "BRANCH_OBJECT_REQUIRED"
    if not REQUIRED_BRANCH_FIELDS.issubset(branch):
        return "BRANCH_FULL_H_I_FIELDS_REQUIRED"
    if not _nonempty(branch.get("branch_id")) or not _nonempty(branch.get("v")):
        return "BRANCH_ID_OR_V_REQUIRED"
    if not _validate_context_predicate(branch.get("K")):
        return "BRANCH_K_INVALID"
    if branch.get("sigma") not in ALLOWED_SIGMA:
        return "BRANCH_SIGMA_INVALID"
    if not isinstance(branch.get("projection_visibility"), bool):
        return "BRANCH_PROJECTION_VISIBILITY_BOOL_REQUIRED"
    if branch.get("T") is None:
        return "BRANCH_T_EXPLICIT_SCOPE_REQUIRED"
    if not isinstance(branch.get("A"), dict) or not branch["A"]:
        return "BRANCH_A_PROVENANCE_OBJECT_REQUIRED"
    predictions = branch.get("predictions")
    if not isinstance(predictions, dict) or not predictions:
        return "BRANCH_PREDICTIONS_REQUIRED"
    for test_id, outcome in predictions.items():
        if test_id not in world.get("tests", {}):
            return "BRANCH_PREDICTION_UNKNOWN_TEST"
        if outcome not in world["tests"][test_id]["allowed_outcomes"]:
            return "BRANCH_PREDICTION_OUTCOME_INVALID"
    for field in ("E_plus", "E_minus", "F"):
        items = branch.get(field)
        if not isinstance(items, list):
            return "BRANCH_EVIDENCE_LIST_REQUIRED:" + field
        if not allow_empty_evidence:
            for item in items:
                err = _validate_record(item)
                if err:
                    return err
    return None


def _validate_state(state: Any, world: dict[str, Any]) -> str | None:
    if not isinstance(state, dict) or state.get("schema") != STATE_SCHEMA:
        return "STATE_SCHEMA_MISMATCH"
    if state.get("canonical_truth_allowed") is not False:
        return "STATE_CANONICAL_TRUTH_MUST_BE_FALSE"
    if state.get("direct_effect_authority") is not False:
        return "STATE_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE"
    if not _nonempty(state.get("query_id")):
        return "STATE_QUERY_ID_REQUIRED"
    branches = state.get("branches")
    if not isinstance(branches, list) or len(branches) < 2:
        return "STATE_REQUIRES_AT_LEAST_TWO_BRANCHES"
    seen: set[str] = set()
    for branch in branches:
        err = _validate_branch(branch, world)
        if err:
            return err
        bid = branch["branch_id"]
        if bid in seen:
            return "DUPLICATE_BRANCH_ID"
        seen.add(bid)
    return None


def _validate_event(event: Any, world: dict[str, Any]) -> str | None:
    if not isinstance(event, dict) or event.get("schema") != EVENT_SCHEMA:
        return "EVENT_SCHEMA_MISMATCH"
    if not REQUIRED_EVENT_FIELDS.issubset(event):
        return "EVENT_FIELDS_MISSING"
    forbidden = sorted(FORBIDDEN_CALLER_LABEL_FIELDS & set(event))
    if forbidden:
        return "CALLER_ASSERTED_LABEL_FIELD_FORBIDDEN:" + ",".join(forbidden)
    for key in ("event_id", "correlation_ancestry_id", "independence_group", "payload_key", "provenance", "test_id"):
        if not _nonempty(event.get(key)):
            return "EVENT_IDENTITY_FIELD_INVALID:" + key
    if event.get("epistemic_type") not in ALLOWED_EPISTEMIC:
        return "EVENT_EPISTEMIC_TYPE_INVALID"
    if not isinstance(event.get("independence_qualified"), bool):
        return "EVENT_INDEPENDENCE_QUALIFIED_BOOL_REQUIRED"
    if event.get("canonical_truth_allowed") is not False:
        return "EVENT_CANONICAL_TRUTH_MUST_BE_FALSE"
    if event.get("direct_effect_authority") is not False:
        return "EVENT_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE"
    test_id = event["test_id"]
    if test_id not in world["tests"]:
        return "EVENT_UNKNOWN_TEST"
    if event.get("observed_outcome") not in world["tests"][test_id]["allowed_outcomes"]:
        return "EVENT_OUTCOME_INVALID"
    return None


def _all_records(state: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for branch in state["branches"]:
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            for item in branch.get(field, []) or []:
                if isinstance(item, dict):
                    out.append(item)
    return out


def _novelty(state: dict[str, Any], event: dict[str, Any]) -> tuple[bool, list[str]]:
    records = _all_records(state)
    reasons: list[str] = []
    if any(r.get("event_id") == event["event_id"] for r in records):
        reasons.append("EXACT_EVENT_REPLAY")
    if any(r.get("correlation_ancestry_id") == event["correlation_ancestry_id"] for r in records):
        reasons.append("CORRELATION_ANCESTRY_REUSE")
    if any(r.get("payload_key") == event["payload_key"] for r in records):
        reasons.append("PAYLOAD_REPACKAGING")
    if any(r.get("independence_group") == event["independence_group"] for r in records):
        reasons.append("INDEPENDENCE_GROUP_REUSE")
    if not event.get("independence_qualified", False):
        reasons.append("EVENT_NOT_INDEPENDENCE_QUALIFIED")
    return not reasons, reasons


def derive_relations(world: Any, state: Any, event: Any) -> dict[str, Any]:
    werr = _validate_world(world)
    if werr:
        return _fail(werr)
    serr = _validate_state(state, world)
    if serr:
        return _fail(serr)
    eerr = _validate_event(event, world)
    if eerr:
        return _fail(eerr)

    test_id = event["test_id"]
    observed = event["observed_outcome"]
    test_spec = world["tests"][test_id]
    relations: dict[str, str] = {}
    target_ids: list[str] = []
    applicability: dict[str, bool] = {}
    for branch in state["branches"]:
        applies = _context_applies(branch["K"], world["context"])
        applicability[branch["branch_id"]] = applies
        if not applies or test_id not in branch["predictions"]:
            relations[branch["branch_id"]] = "IRRELEVANT"
            continue
        target_ids.append(branch["branch_id"])
        predicted = branch["predictions"][test_id]
        if predicted == observed:
            relations[branch["branch_id"]] = "SUPPORTS"
        else:
            relations[branch["branch_id"]] = test_spec["mismatch_effect"]

    if not target_ids:
        return _fail("FORMAL_EVENT_HAS_NO_APPLICABLE_TARGET_BRANCH")

    receipt_payload = {
        "world_id": world["world_id"],
        "world_sha256": _digest(world),
        "state_before_sha256": _digest(state),
        "event_sha256": _digest(event),
        "test_id": test_id,
        "observed_outcome": observed,
        "target_branch_ids": sorted(target_ids),
        "relations": {k: relations[k] for k in sorted(relations)},
        "context_applicability": {k: applicability[k] for k in sorted(applicability)},
    }
    return _ok(
        labeler="derive_relations",
        target_branch_ids=sorted(target_ids),
        relations=relations,
        context_applicability=applicability,
        derivation_receipt={
            **receipt_payload,
            "derivation_sha256": _digest(receipt_payload),
            "caller_relation_fields_accepted": False,
        },
    )


def _record(event: dict[str, Any], relation: str, *, independent_credit: bool, nonindependence_reasons: list[str]) -> dict[str, Any]:
    return {
        "event_id": event["event_id"],
        "correlation_ancestry_id": event["correlation_ancestry_id"],
        "independence_group": event["independence_group"],
        "payload_key": event["payload_key"],
        "provenance": event["provenance"],
        "epistemic_type": event["epistemic_type"],
        "test_id": event["test_id"],
        "observed_outcome": deepcopy(event["observed_outcome"]),
        "derived_relation": relation,
        "independent_credit": bool(independent_credit),
        "nonindependence_reasons": sorted(set(nonindependence_reasons)),
    }


def _semantic_signature(branch: dict[str, Any]) -> str:
    payload = {
        "v": branch["v"],
        "K": branch["K"],
        "T": branch["T"],
        "predictions": branch["predictions"],
    }
    return _digest(payload)


def _merge_exact_equivalents(branches: list[dict[str, Any]], world: dict[str, Any]) -> list[dict[str, Any]]:
    if world.get("merge_policy", "NONE") == "NONE":
        return branches
    groups: dict[str, list[dict[str, Any]]] = {}
    for branch in branches:
        groups.setdefault(_semantic_signature(branch), []).append(branch)
    out: list[dict[str, Any]] = []
    for sig in sorted(groups):
        group = groups[sig]
        if len(group) == 1:
            out.append(group[0])
            continue
        group = sorted(group, key=lambda b: b["branch_id"])
        pivot = deepcopy(group[0])
        pivot["merged_from_branch_ids"] = [b["branch_id"] for b in group]
        pivot["A"] = {
            "merge_policy": "EXACT_FORMAL_SEMANTIC_SIGNATURE",
            "semantic_signature_sha256": sig,
            "merged_origins": [deepcopy(b["A"]) for b in group],
        }
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            seen: set[tuple[str, str]] = set()
            merged: list[dict[str, Any]] = []
            for branch in group:
                for item in branch.get(field, []) or []:
                    key = (str(item.get("event_id")), str(item.get("derived_relation")))
                    if key not in seen:
                        seen.add(key)
                        merged.append(deepcopy(item))
            if merged:
                pivot[field] = merged
        sigmas = {b["sigma"] for b in group}
        if "FALSIFIED" in sigmas:
            pivot["sigma"] = "FALSIFIED"
        elif "WEAKENED_UNRESOLVED" in sigmas:
            pivot["sigma"] = "WEAKENED_UNRESOLVED"
        elif "SUPPORTED_UNRESOLVED" in sigmas:
            pivot["sigma"] = "SUPPORTED_UNRESOLVED"
        else:
            pivot["sigma"] = "LIVE_UNRESOLVED"
        out.append(pivot)
    return out


def _apply_branch_birth_rules(branches: list[dict[str, Any]], world: dict[str, Any], event: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    born: list[str] = []
    existing = {b["branch_id"] for b in branches}
    for rule in world.get("branch_birth_rules", []):
        if rule["test_id"] != event["test_id"] or rule["observed_outcome"] != event["observed_outcome"]:
            continue
        template = deepcopy(rule["branch_template"])
        if template["branch_id"] in existing:
            continue
        template["A"] = {
            "formal_birth_rule_id": rule["rule_id"],
            "world_id": world["world_id"],
            "template_origin": deepcopy(template.get("A")),
        }
        branches.append(template)
        existing.add(template["branch_id"])
        born.append(template["branch_id"])
    return branches, born


def project_state(world: Any, state: Any) -> dict[str, Any]:
    werr = _validate_world(world)
    if werr:
        return _fail(werr)
    serr = _validate_state(state, world)
    if serr:
        return _fail(serr)
    out = deepcopy(state)
    visible: list[str] = []
    hidden: list[str] = []
    for branch in out["branches"]:
        branch["projection_visibility"] = _context_applies(branch["K"], world["context"])
        (visible if branch["projection_visibility"] else hidden).append(branch["branch_id"])
    return _ok(
        labeler="project_state",
        projected_state=out,
        visible_branch_ids=sorted(visible),
        projected_out_branch_ids=sorted(hidden),
        branch_count_before=len(state["branches"]),
        branch_count_after=len(out["branches"]),
        branch_deletion_performed=False,
        rule="PROJECTION_IS_NONDESTRUCTIVE_CONTEXT_VIEW",
    )


def u_state(world: Any, state: Any, event: Any) -> dict[str, Any]:
    derived = derive_relations(world, state, event)
    if not derived.get("pass"):
        return derived
    independent, reasons = _novelty(state, event)
    out = deepcopy(state)
    by_id = {b["branch_id"]: b for b in out["branches"]}
    updates: list[dict[str, Any]] = []

    exact_replay = "EXACT_EVENT_REPLAY" in reasons
    for bid in derived["target_branch_ids"]:
        branch = by_id[bid]
        relation = derived["relations"][bid]
        if exact_replay:
            updates.append({
                "branch_id": bid,
                "derived_relation": relation,
                "applied": False,
                "independent_credit": False,
                "reason": "EXACT_EVENT_REPLAY_IDEMPOTENT",
                "sigma_before": branch["sigma"],
                "sigma_after": branch["sigma"],
            })
            continue

        rec = _record(event, relation, independent_credit=independent, nonindependence_reasons=reasons)
        before = branch["sigma"]
        if not independent:
            branch.setdefault("correlated_observations", []).append(rec)
        elif relation == "SUPPORTS":
            branch["E_plus"].append(rec)
            if branch["sigma"] != "FALSIFIED":
                branch["sigma"] = "SUPPORTED_UNRESOLVED"
        elif relation == "COUNTERS":
            branch["E_minus"].append(rec)
            if branch["sigma"] != "FALSIFIED":
                branch["sigma"] = "WEAKENED_UNRESOLVED"
        elif relation == "FALSIFIES":
            branch["F"].append(rec)
            branch["sigma"] = "FALSIFIED"
        updates.append({
            "branch_id": bid,
            "derived_relation": relation,
            "applied": independent,
            "independent_credit": independent,
            "nonindependence_reasons": sorted(set(reasons)),
            "sigma_before": before,
            "sigma_after": branch["sigma"],
        })

    out["branches"] = [by_id[b["branch_id"]] for b in state["branches"]]
    born: list[str] = []
    if independent and not exact_replay:
        out["branches"], born = _apply_branch_birth_rules(out["branches"], world, event)
    out["branches"] = _merge_exact_equivalents(out["branches"], world)
    projection = project_state(world, out)
    if not projection.get("pass"):
        return projection
    out = projection["projected_state"]
    out["last_event_id"] = event["event_id"]

    return _ok(
        labeler="u_state",
        state_after=out,
        updates=updates,
        independent_evidence_credit=independent,
        nonindependence_reasons=sorted(set(reasons)),
        exact_replay_idempotent=exact_replay,
        born_branch_ids=sorted(born),
        derivation_receipt=derived["derivation_receipt"],
        branch_count_before=len(state["branches"]),
        branch_count_after=len(out["branches"]),
        canonical_resolution_performed=False,
    )


def d_resolve(world: Any, state: Any) -> dict[str, Any]:
    werr = _validate_world(world)
    if werr:
        return _fail(werr)
    serr = _validate_state(state, world)
    if serr:
        return _fail(serr)
    applicable = [b for b in state["branches"] if _context_applies(b["K"], world["context"])]
    live = [b for b in applicable if b["sigma"] != "FALSIFIED"]
    if len(live) != 1:
        return _ok(
            labeler="d_resolve",
            resolution={"status": "UNRESOLVED", "resolved_branch": None, "basis": "NOT_EXACTLY_ONE_APPLICABLE_LIVE_BRANCH"},
            retained_branch_ids=[b["branch_id"] for b in state["branches"]],
        )
    selected = live[0]
    competitors = [b for b in applicable if b["branch_id"] != selected["branch_id"]]
    if any(b["sigma"] != "FALSIFIED" for b in competitors):
        return _ok(
            labeler="d_resolve",
            resolution={"status": "UNRESOLVED", "resolved_branch": None, "basis": "APPLICABLE_COMPETITOR_NOT_FALSIFIED"},
            retained_branch_ids=[b["branch_id"] for b in state["branches"]],
        )
    if not any(bool(e.get("independent_credit")) for e in selected.get("E_plus", [])):
        return _ok(
            labeler="d_resolve",
            resolution={"status": "UNRESOLVED", "resolved_branch": None, "basis": "SURVIVING_BRANCH_LACKS_INDEPENDENT_SUPPORT"},
            retained_branch_ids=[b["branch_id"] for b in state["branches"]],
        )
    return _ok(
        labeler="d_resolve",
        resolution={"status": "RESOLVED_WITHIN_SYNTHETIC_WORLD", "resolved_branch": selected["branch_id"], "basis": "ONE_SUPPORTED_SURVIVOR_AFTER_FORMALLY_DERIVED_FALSIFICATION"},
        retained_branch_ids=[b["branch_id"] for b in state["branches"]],
    )


def apply_task_resolution(world: Any, state: Any) -> dict[str, Any]:
    resolution = d_resolve(world, state)
    if not resolution.get("pass"):
        return resolution
    out = deepcopy(state)
    if resolution["resolution"]["status"] == "RESOLVED_WITHIN_SYNTHETIC_WORLD":
        winner = resolution["resolution"]["resolved_branch"]
        for branch in out["branches"]:
            if branch["branch_id"] == winner:
                branch["sigma"] = "RESOLVED_PASS"
    return _ok(
        labeler="apply_task_resolution",
        state_after=out,
        resolution=resolution["resolution"],
        canonical_truth_minted=False,
        branch_deletion_performed=False,
    )


def u_test_order(world: Any, state: Any, candidate_test_ids: Any = None) -> dict[str, Any]:
    werr = _validate_world(world)
    if werr:
        return _fail(werr)
    serr = _validate_state(state, world)
    if serr:
        return _fail(serr)
    if candidate_test_ids is None:
        candidate_test_ids = sorted(world["tests"])
    if not isinstance(candidate_test_ids, list) or not candidate_test_ids:
        return _fail("CANDIDATE_TEST_IDS_LIST_REQUIRED")
    if any(t not in world["tests"] for t in candidate_test_ids):
        return _fail("CANDIDATE_TEST_UNKNOWN")

    live = [b for b in state["branches"] if b["sigma"] != "FALSIFIED" and _context_applies(b["K"], world["context"])]
    live_ids = {b["branch_id"] for b in live}
    all_pairs = set(combinations(sorted(live_ids), 2))
    rows: list[dict[str, Any]] = []
    for test_id in candidate_test_ids:
        spec = world["tests"][test_id]
        covered: set[tuple[str, str]] = set()
        for a, b in all_pairs:
            ba = next(x for x in live if x["branch_id"] == a)
            bb = next(x for x in live if x["branch_id"] == b)
            if test_id in ba["predictions"] and test_id in bb["predictions"] and ba["predictions"][test_id] != bb["predictions"][test_id]:
                covered.add((a, b))
        rows.append({
            "test_id": test_id,
            "separated_live_pairs": len(covered),
            "separates_all_live_pairs": covered == all_pairs and bool(all_pairs),
            "risk_rank": spec["risk_rank"],
            "cost_rank": spec["cost_rank"],
            "coordination_rank": spec["coordination_rank"],
            "_key": (-len(covered), spec["risk_rank"], spec["cost_rank"], spec["coordination_rank"], test_id),
        })
    rows.sort(key=lambda x: x["_key"])
    for rank, row in enumerate(rows, 1):
        row["ordinal_rank"] = rank
        del row["_key"]
    return _ok(
        labeler="u_test_order",
        ordering=rows,
        probability_output=False,
        expected_information_gain_output=False,
        truth_output=False,
        pair_separation_derived_from_formal_predictions=True,
        rule="MAX_FORMALLY_DERIVED_PAIR_SEPARATION_THEN_MIN_RISK_COST_COORDINATION",
    )


def f_salience_order(items: Any) -> dict[str, Any]:
    if not isinstance(items, list) or not items:
        return _fail("SALIENCE_ITEMS_REQUIRED")
    rows: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict) or not _nonempty(item.get("item_id")):
            return _fail("SALIENCE_ITEM_INVALID")
        ranks = (
            item.get("authority_boundary_risk_rank"),
            item.get("expiry_rank"),
            item.get("discriminator_relevance_rank"),
            item.get("goal_relevance_rank"),
        )
        if not all(isinstance(x, int) and x >= 0 for x in ranks):
            return _fail("SALIENCE_ORDINAL_RANK_FIELDS_INVALID")
        rows.append({
            "item_id": item["item_id"],
            "authority_boundary_risk_rank": ranks[0],
            "expiry_rank": ranks[1],
            "discriminator_relevance_rank": ranks[2],
            "goal_relevance_rank": ranks[3],
            "_key": (*ranks, item["item_id"]),
        })
    rows.sort(key=lambda x: x["_key"])
    for rank, row in enumerate(rows, 1):
        row["salience_rank"] = rank
        del row["_key"]
    return _ok(
        labeler="f_salience_order",
        ranking=rows,
        probability_output=False,
        truth_output=False,
        evidence_strength_output=False,
        resolution_authority_output=False,
        rule="ATTENTION_ORDER_ONLY_NEVER_BRANCH_TRUTH",
    )


def canonical_semantic_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict):
        return _fail("STATE_OBJECT_REQUIRED")
    branches = state.get("branches")
    if not isinstance(branches, list):
        return _fail("STATE_BRANCHES_LIST_REQUIRED")
    canonical = []
    for branch in branches:
        if not isinstance(branch, dict):
            return _fail("BRANCH_OBJECT_REQUIRED")
        canonical.append({
            "semantic_signature_sha256": _semantic_signature(branch),
            "sigma": branch.get("sigma"),
            "projection_visibility": branch.get("projection_visibility"),
            "E_plus": sorted(_digest(e) for e in branch.get("E_plus", [])),
            "E_minus": sorted(_digest(e) for e in branch.get("E_minus", [])),
            "F": sorted(_digest(e) for e in branch.get("F", [])),
        })
    canonical.sort(key=lambda x: (x["semantic_signature_sha256"], x["sigma"], str(x["projection_visibility"])))
    return _ok(
        labeler="canonical_semantic_state",
        canonical_branches=canonical,
        canonical_state_sha256=_digest(canonical),
        branch_id_and_order_excluded=True,
    )


def permutation_invariance_check(state_a: Any, state_b: Any) -> dict[str, Any]:
    a = canonical_semantic_state(state_a)
    b = canonical_semantic_state(state_b)
    if not a.get("pass"):
        return a
    if not b.get("pass"):
        return b
    return _ok(
        labeler="permutation_invariance_check",
        invariant=a["canonical_state_sha256"] == b["canonical_state_sha256"],
        state_a_sha256=a["canonical_state_sha256"],
        state_b_sha256=b["canonical_state_sha256"],
        branch_order_and_ids_are_nuisance=True,
    )


def epistemic_guard(source_type: Any, requested_target_type: Any, *, evidence_qualified_observation: bool = False) -> dict[str, Any]:
    if source_type not in ALLOWED_EPISTEMIC or requested_target_type not in ALLOWED_EPISTEMIC:
        return _fail("EPISTEMIC_TYPE_INVALID")
    requires_observation = source_type in {
        "UNKNOWN", "MEASUREMENT_ERROR", "PREDICTION", "CONTRADICTION",
        "HYPOTHESIS", "COUNTERHYPOTHESIS",
    } and requested_target_type == "OBSERVED"
    if requires_observation and not evidence_qualified_observation:
        return _ok(
            labeler="epistemic_guard",
            transition_allowed=False,
            reason="EVIDENCE_QUALIFIED_OBSERVATION_REQUIRED",
            source_type=source_type,
            requested_target_type=requested_target_type,
        )
    return _ok(
        labeler="epistemic_guard",
        transition_allowed=True,
        source_type=source_type,
        requested_target_type=requested_target_type,
        note="UNKNOWN remains distinct from ZERO/ABSENT/FAIL, which are not epistemic types in this schema.",
    )
