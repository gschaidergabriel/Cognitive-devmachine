#!/usr/bin/env python3
"""TurnTraceEnvelope v1 reference validator/differential oracle.

Research-Entity Harness foundation. This module is deliberately host-language and
stdlib-only so it can be executed during BASE without implying H1 completion.
It validates trace evidence; it never grants truth, capability, or effect authority.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import platform
import re
from typing import Any

SCHEMA_VERSION = "1.0"
HASH64 = re.compile(r"^[0-9a-f]{64}$")
HASH40 = re.compile(r"^[0-9a-f]{40}$")
REPLAY_CLASSES = {
    "EXACT_DETERMINISTIC",
    "DETERMINISTIC_UNDER_ENV_FINGERPRINT",
    "RECEIPT_BOUNDARY_NONDETERMINISTIC",
    "LIVE_EXTERNAL_NONREPLAYABLE_WITH_RECORDED_OUTCOME",
}
GWT_FIELDS = (
    "addressable",
    "delivered",
    "reconstructed",
    "uptake",
    "causal_use",
    "outcome",
    "reentry",
)
REQUIRED_GWT_STAGE_REFS = (
    "candidate",
    "competition",
    "workspace",
    "broadcast",
    "outcome",
    "reentry",
)
ADMISSIBILITY_STATES = {"ADMIT", "SUPPLEMENT_ONLY", "QUARANTINE", "ESCALATE", "UNKNOWN", "BYPASS_EXACT"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _without(mapping: dict[str, Any], key: str) -> dict[str, Any]:
    out = dict(mapping)
    out.pop(key, None)
    return out


def environment_fingerprint(environment: dict[str, Any]) -> str:
    return sha256_obj(_without(environment, "fingerprint_hash"))


def status_snapshot_hash(snapshot: dict[str, Any]) -> str:
    return sha256_obj(_without(snapshot, "snapshot_hash"))


def _err(errors: list[dict[str, Any]], code: str, path: str, detail: str) -> None:
    errors.append({"code": code, "path": path, "detail": detail})


def _warn(warnings: list[dict[str, Any]], code: str, path: str, detail: str) -> None:
    warnings.append({"code": code, "path": path, "detail": detail})


def _require(mapping: dict[str, Any], keys: tuple[str, ...], path: str, errors: list[dict[str, Any]]) -> None:
    for key in keys:
        if key not in mapping:
            _err(errors, "MISSING_FIELD", f"{path}.{key}", "required field is absent")


def _hash64(value: Any) -> bool:
    return isinstance(value, str) and bool(HASH64.fullmatch(value))


def _hash40(value: Any) -> bool:
    return isinstance(value, str) and bool(HASH40.fullmatch(value))


def _check_hash(errors: list[dict[str, Any]], value: Any, path: str, *, length: int = 64) -> None:
    ok = _hash64(value) if length == 64 else _hash40(value)
    if not ok:
        _err(errors, "INVALID_HASH", path, f"expected lowercase {length}-hex digest")


def _check_basis(basis: Any, path: str, errors: list[dict[str, Any]]) -> None:
    if not isinstance(basis, dict):
        _err(errors, "INVALID_TYPE", path, "basis must be an object")
        return
    _require(basis, ("semantic_epoch", "semantic_root_hash", "graph_epoch", "graph_root_hash"), path, errors)
    for name in ("semantic_epoch", "graph_epoch"):
        if name in basis and (not isinstance(basis[name], int) or basis[name] < 0):
            _err(errors, "INVALID_EPOCH", f"{path}.{name}", "epoch must be a non-negative integer")
    for name in ("semantic_root_hash", "graph_root_hash"):
        if name in basis:
            _check_hash(errors, basis[name], f"{path}.{name}")


def _bool_or_unknown(value: Any) -> bool:
    return isinstance(value, bool) or value == "UNKNOWN"


def _validate_loops(trace: dict[str, Any], errors: list[dict[str, Any]]) -> set[str]:
    loops = trace.get("loop_episodes")
    if not isinstance(loops, list) or not loops:
        _err(errors, "LOOPS_REQUIRED", "$.loop_episodes", "at least one loop episode is required; trace must not flatten recurrence")
        return set()
    ids: set[str] = set()
    for i, loop in enumerate(loops):
        p = f"$.loop_episodes[{i}]"
        if not isinstance(loop, dict):
            _err(errors, "INVALID_TYPE", p, "loop episode must be an object")
            continue
        _require(loop, ("loop_id", "recurrence_index", "timescale", "status"), p, errors)
        lid = loop.get("loop_id")
        if not isinstance(lid, str) or not lid:
            _err(errors, "INVALID_LOOP_ID", f"{p}.loop_id", "loop_id must be non-empty")
            continue
        if lid in ids:
            _err(errors, "DUPLICATE_LOOP_ID", f"{p}.loop_id", lid)
        ids.add(lid)
        ri = loop.get("recurrence_index")
        if not isinstance(ri, int) or ri < 0:
            _err(errors, "INVALID_RECURRENCE_INDEX", f"{p}.recurrence_index", "must be a non-negative integer")
        for budget_name in ("budget_before", "budget_after"):
            if budget_name in loop and (not isinstance(loop[budget_name], (int, float)) or loop[budget_name] < 0):
                _err(errors, "INVALID_LOOP_BUDGET", f"{p}.{budget_name}", "must be non-negative")
    for i, loop in enumerate(loops):
        if not isinstance(loop, dict):
            continue
        parent = loop.get("parent_loop_id")
        lid = loop.get("loop_id")
        if parent is not None and parent not in ids:
            _err(errors, "UNKNOWN_PARENT_LOOP", f"$.loop_episodes[{i}].parent_loop_id", str(parent))
        if parent == lid:
            _err(errors, "SELF_PARENT_LOOP", f"$.loop_episodes[{i}].parent_loop_id", "loop cannot parent itself")
    return ids


def _validate_stages(trace: dict[str, Any], loop_ids: set[str], errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> tuple[dict[str, int], set[str]]:
    stages = trace.get("stages")
    if not isinstance(stages, list) or not stages:
        _err(errors, "STAGES_REQUIRED", "$.stages", "at least one causal stage is required")
        return {}, set()
    ids: set[str] = set()
    seq_by_id: dict[str, int] = {}
    prior_seq = -1
    for i, stage in enumerate(stages):
        p = f"$.stages[{i}]"
        if not isinstance(stage, dict):
            _err(errors, "INVALID_TYPE", p, "stage must be an object")
            continue
        _require(stage, ("stage_id", "seq", "cycle_id", "loop_id", "kind", "input_hash", "output_hash", "semantic_hash", "semantic_epoch", "graph_epoch", "causal_parents", "receipts", "status"), p, errors)
        sid = stage.get("stage_id")
        seq = stage.get("seq")
        if not isinstance(sid, str) or not sid:
            _err(errors, "INVALID_STAGE_ID", f"{p}.stage_id", "must be non-empty")
        elif sid in ids:
            _err(errors, "DUPLICATE_STAGE_ID", f"{p}.stage_id", sid)
        else:
            ids.add(sid)
            if isinstance(seq, int):
                seq_by_id[sid] = seq
        if not isinstance(seq, int) or seq < 0:
            _err(errors, "INVALID_SEQUENCE", f"{p}.seq", "must be a non-negative integer")
        elif seq <= prior_seq:
            _err(errors, "NON_MONOTONIC_OBSERVATION_ORDER", f"{p}.seq", "stage seq must increase; this is observation order, not an acyclic-architecture claim")
        else:
            prior_seq = seq
        if stage.get("loop_id") not in loop_ids:
            _err(errors, "UNKNOWN_LOOP", f"{p}.loop_id", str(stage.get("loop_id")))
        for hn in ("input_hash", "output_hash", "semantic_hash"):
            if hn in stage:
                _check_hash(errors, stage[hn], f"{p}.{hn}")
        for en in ("semantic_epoch", "graph_epoch"):
            if en in stage and (not isinstance(stage[en], int) or stage[en] < 0):
                _err(errors, "INVALID_EPOCH", f"{p}.{en}", "must be a non-negative integer")
        parents = stage.get("causal_parents")
        if not isinstance(parents, list):
            _err(errors, "INVALID_CAUSAL_PARENTS", f"{p}.causal_parents", "must be a list")
        receipts = stage.get("receipts")
        if not isinstance(receipts, list):
            _err(errors, "INVALID_RECEIPTS", f"{p}.receipts", "must be a list")
        if stage.get("status") == "BYPASS" and not stage.get("bypass_receipt"):
            _err(errors, "BYPASS_WITHOUT_RECEIPT", f"{p}.bypass_receipt", "explicit bypass must be receipted")
        if stage.get("kind") == "model_transform" and stage.get("authority_granted"):
            _err(errors, "MODEL_OUTPUT_AUTHORITY", f"{p}.authority_granted", "model output cannot grant execution authority")
    for i, stage in enumerate(stages):
        if not isinstance(stage, dict) or not isinstance(stage.get("causal_parents"), list) or not isinstance(stage.get("seq"), int):
            continue
        for j, parent in enumerate(stage["causal_parents"]):
            if parent not in seq_by_id:
                _err(errors, "UNKNOWN_CAUSAL_PARENT", f"$.stages[{i}].causal_parents[{j}]", str(parent))
            elif seq_by_id[parent] >= stage["seq"]:
                _err(errors, "NONCAUSAL_PARENT_ORDER", f"$.stages[{i}].causal_parents[{j}]", "parent must have been observed earlier")
    if len(ids) != len(stages):
        _warn(warnings, "STAGE_ID_COVERAGE", "$.stages", "some stage records lacked valid unique ids")
    return seq_by_id, ids


def _validate_gwt(trace: dict[str, Any], stage_ids: set[str], errors: list[dict[str, Any]]) -> None:
    episodes = trace.get("gwt_episodes", [])
    if not isinstance(episodes, list):
        _err(errors, "INVALID_TYPE", "$.gwt_episodes", "must be a list")
        return
    seen: set[str] = set()
    for i, episode in enumerate(episodes):
        p = f"$.gwt_episodes[{i}]"
        if not isinstance(episode, dict):
            _err(errors, "INVALID_TYPE", p, "GWT episode must be an object")
            continue
        _require(episode, ("workspace_episode_id", "stage_refs", "receivers"), p, errors)
        wid = episode.get("workspace_episode_id")
        if wid in seen:
            _err(errors, "DUPLICATE_WORKSPACE_EPISODE", f"{p}.workspace_episode_id", str(wid))
        seen.add(wid)
        refs = episode.get("stage_refs")
        if not isinstance(refs, dict):
            _err(errors, "INVALID_GWT_STAGE_REFS", f"{p}.stage_refs", "must be an object")
        else:
            for key in REQUIRED_GWT_STAGE_REFS:
                if key not in refs:
                    _err(errors, "MISSING_GWT_STAGE", f"{p}.stage_refs.{key}", "GWT causal stage must remain separately addressable")
                elif refs[key] not in stage_ids:
                    _err(errors, "UNKNOWN_GWT_STAGE", f"{p}.stage_refs.{key}", str(refs[key]))
        receivers = episode.get("receivers")
        if not isinstance(receivers, list) or not receivers:
            _err(errors, "GWT_RECEIVER_REQUIRED", f"{p}.receivers", "at least one receiver record is required")
            continue
        for rix, receiver in enumerate(receivers):
            rp = f"{p}.receivers[{rix}]"
            if not isinstance(receiver, dict):
                _err(errors, "INVALID_TYPE", rp, "receiver must be an object")
                continue
            _require(receiver, ("receiver_id",) + GWT_FIELDS + ("receipt_refs",), rp, errors)
            for field in GWT_FIELDS:
                if field in receiver and not _bool_or_unknown(receiver[field]):
                    _err(errors, "INVALID_GWT_STATE", f"{rp}.{field}", "must be boolean or UNKNOWN")
            for idx in range(1, len(GWT_FIELDS)):
                downstream = GWT_FIELDS[idx]
                if receiver.get(downstream) is True:
                    for upstream in GWT_FIELDS[:idx]:
                        if receiver.get(upstream) is not True:
                            _err(errors, "GWT_CAUSAL_CHAIN_VIOLATION", f"{rp}.{downstream}", f"{downstream}=true requires {upstream}=true")
            rr = receiver.get("receipt_refs")
            if isinstance(rr, dict):
                for field in GWT_FIELDS:
                    if receiver.get(field) is True and not rr.get(field):
                        _err(errors, "GWT_TRUE_WITHOUT_RECEIPT", f"{rp}.receipt_refs.{field}", "true causal-stage claim requires receipt ref")
            else:
                _err(errors, "INVALID_GWT_RECEIPTS", f"{rp}.receipt_refs", "must be an object")


def _validate_memory(trace: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    uses = trace.get("memory_uses", [])
    if not isinstance(uses, list):
        _err(errors, "INVALID_TYPE", "$.memory_uses", "must be a list")
        return
    for i, use in enumerate(uses):
        p = f"$.memory_uses[{i}]"
        if not isinstance(use, dict):
            _err(errors, "INVALID_TYPE", p, "memory-use record must be an object")
            continue
        _require(use, ("memory_ref", "retrieved", "admissibility", "consequential_use", "receipt_ref"), p, errors)
        if use.get("admissibility") not in ADMISSIBILITY_STATES:
            _err(errors, "INVALID_ADMISSIBILITY", f"{p}.admissibility", str(use.get("admissibility")))
        if use.get("consequential_use") is True:
            if use.get("retrieved") is not True:
                _err(errors, "MEMORY_USE_WITHOUT_RETRIEVAL", f"{p}.consequential_use", "consequential use requires retrieval")
            if use.get("admissibility") not in {"ADMIT", "BYPASS_EXACT"}:
                _err(errors, "MEMORY_USE_NOT_ADMITTED", f"{p}.consequential_use", "consequential use requires ADMIT or BYPASS_EXACT")
            if not use.get("receipt_ref"):
                _err(errors, "MEMORY_USE_WITHOUT_RECEIPT", f"{p}.receipt_ref", "consequential use must be receipted")


def _validate_topology(trace: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    topo = trace.get("topology")
    if topo is None:
        return
    if not isinstance(topo, dict):
        _err(errors, "INVALID_TYPE", "$.topology", "must be an object")
        return
    for key in ("semantic_hash", "active_hash", "coordination_hash", "physical_hash"):
        if key not in topo:
            _err(errors, "MISSING_TOPOLOGY_IDENTITY", f"$.topology.{key}", "four topology identities must remain distinct/addressable")
        else:
            _check_hash(errors, topo[key], f"$.topology.{key}")
    interventions = topo.get("interventions", [])
    if not isinstance(interventions, list):
        _err(errors, "INVALID_TYPE", "$.topology.interventions", "must be a list")


def _validate_effects(trace: dict[str, Any], loop_ids: set[str], errors: list[dict[str, Any]]) -> None:
    effects = trace.get("effects", [])
    if not isinstance(effects, list):
        _err(errors, "INVALID_TYPE", "$.effects", "must be a list")
        return
    for i, effect in enumerate(effects):
        p = f"$.effects[{i}]"
        if not isinstance(effect, dict):
            _err(errors, "INVALID_TYPE", p, "effect record must be an object")
            continue
        _require(effect, ("effect_id", "loop_id", "attempt_count", "capabilities_before", "capabilities_after", "external_authorization_ref", "denied", "cumulative_resource_cost"), p, errors)
        if effect.get("loop_id") not in loop_ids:
            _err(errors, "UNKNOWN_LOOP", f"{p}.loop_id", str(effect.get("loop_id")))
        before = effect.get("capabilities_before")
        after = effect.get("capabilities_after")
        if not isinstance(before, list) or not all(isinstance(x, str) for x in before):
            _err(errors, "INVALID_CAPABILITY_SET", f"{p}.capabilities_before", "must be string list")
            before = []
        if not isinstance(after, list) or not all(isinstance(x, str) for x in after):
            _err(errors, "INVALID_CAPABILITY_SET", f"{p}.capabilities_after", "must be string list")
            after = []
        widened = sorted(set(after) - set(before))
        if widened and not effect.get("external_authorization_ref"):
            _err(errors, "AUTHORITY_WIDENED_WITHOUT_EXTERNAL_AUTHORIZATION", f"{p}.capabilities_after", f"new capabilities: {widened}")
        attempt = effect.get("attempt_count")
        if not isinstance(attempt, int) or attempt < 1:
            _err(errors, "INVALID_EFFECT_ATTEMPT_COUNT", f"{p}.attempt_count", "must be integer >= 1")
        if isinstance(attempt, int) and attempt > 1:
            if not effect.get("retry_reason"):
                _err(errors, "RECURRENCE_RETRY_WITHOUT_REASON", f"{p}.retry_reason", "repeated effect attempt requires retry reason")
            if effect.get("denied") and not effect.get("repeated_denial_indicator"):
                _err(errors, "REPEATED_DENIAL_UNMARKED", f"{p}.repeated_denial_indicator", "repeated denied effects must be explicit")
        cost = effect.get("cumulative_resource_cost")
        if not isinstance(cost, (int, float)) or cost < 0:
            _err(errors, "INVALID_RESOURCE_COST", f"{p}.cumulative_resource_cost", "must be non-negative")


def _validate_visual(trace: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    visual = trace.get("visual")
    if visual is None:
        return
    if not isinstance(visual, dict):
        _err(errors, "INVALID_TYPE", "$.visual", "must be an object")
        return
    if visual.get("authority_granted_by_visual_model") is not False:
        _err(errors, "VISUAL_MODEL_AUTHORITY", "$.visual.authority_granted_by_visual_model", "visual classifier/familiarity output cannot be effect authority")
    if "familiarity_state" in visual and visual["familiarity_state"] not in {"KNOWN", "UNKNOWN", "AMBIGUOUS", "CONFLICT"}:
        _err(errors, "INVALID_VISUAL_FAMILIARITY_STATE", "$.visual.familiarity_state", str(visual["familiarity_state"]))
    promotion = visual.get("learner_promotion")
    if promotion is not None:
        if not isinstance(promotion, dict):
            _err(errors, "INVALID_TYPE", "$.visual.learner_promotion", "must be an object")
        else:
            _require(promotion, ("candidate_version", "previous_version", "shadow_eval_receipt", "atomic_promotion_receipt", "rollback_ref"), "$.visual.learner_promotion", errors)


def _validate_status_snapshot(trace: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    snap = trace.get("status_snapshot")
    if not isinstance(snap, dict):
        _err(errors, "STATUS_SNAPSHOT_REQUIRED", "$.status_snapshot", "one immutable response-boundary status snapshot is required")
        return
    _require(snap, ("snapshot_id", "source_repo_head", "semantic_epoch", "semantic_root_hash", "graph_epoch", "graph_root_hash", "integrity_state", "now_basis_refs", "next_basis_refs", "node_groups", "v01_gate_vector", "active_skill_revision", "snapshot_hash"), "$.status_snapshot", errors)
    if "snapshot_hash" in snap and _hash64(snap.get("snapshot_hash")):
        expected = status_snapshot_hash(snap)
        if snap["snapshot_hash"] != expected:
            _err(errors, "STATUS_SNAPSHOT_HASH_MISMATCH", "$.status_snapshot.snapshot_hash", f"expected {expected}")
    elif "snapshot_hash" in snap:
        _check_hash(errors, snap.get("snapshot_hash"), "$.status_snapshot.snapshot_hash")
    after = trace.get("basis_after")
    if isinstance(after, dict):
        for key in ("semantic_epoch", "semantic_root_hash", "graph_epoch", "graph_root_hash"):
            if key in snap and key in after and snap[key] != after[key]:
                _err(errors, "STATUS_NOT_BOUND_TO_FINAL_BASIS", f"$.status_snapshot.{key}", f"status={snap[key]!r} final_basis={after[key]!r}")
    arch = trace.get("architecture")
    if isinstance(arch, dict) and snap.get("source_repo_head") != arch.get("source_repo_head"):
        _err(errors, "STATUS_SOURCE_HEAD_MISMATCH", "$.status_snapshot.source_repo_head", "must match trace architecture source repo head")
    if snap.get("integrity_state") not in {"VERIFIED", "DEGRADED", "UNKNOWN"}:
        _err(errors, "INVALID_STATUS_INTEGRITY", "$.status_snapshot.integrity_state", "must be VERIFIED, DEGRADED, or UNKNOWN")
    if not isinstance(snap.get("node_groups"), list):
        _err(errors, "INVALID_NODE_GROUPS", "$.status_snapshot.node_groups", "must retain auditable endpoint multiplicity")
    else:
        for i, group in enumerate(snap["node_groups"]):
            if not isinstance(group, dict) or not isinstance(group.get("member_count"), int) or group.get("member_count", 0) < 1:
                _err(errors, "INVALID_NODE_GROUP", f"$.status_snapshot.node_groups[{i}]", "group requires member_count >= 1")
            elif isinstance(group.get("member_ids"), list) and len(group["member_ids"]) != group["member_count"]:
                _err(errors, "NODE_GROUP_COUNT_MISMATCH", f"$.status_snapshot.node_groups[{i}]", "member_count must equal member_ids length")


def _validate_replay(trace: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    replay = trace.get("replay")
    if not isinstance(replay, dict):
        _err(errors, "REPLAY_REQUIRED", "$.replay", "replay identity is required")
        return
    _require(replay, ("class", "frozen_inputs_hash", "expected_semantic_root_hash", "expected_graph_root_hash", "nondeterminism_receipts"), "$.replay", errors)
    klass = replay.get("class")
    if klass not in REPLAY_CLASSES:
        _err(errors, "INVALID_REPLAY_CLASS", "$.replay.class", str(klass))
    for key in ("frozen_inputs_hash", "expected_semantic_root_hash", "expected_graph_root_hash"):
        if key in replay:
            _check_hash(errors, replay[key], f"$.replay.{key}")
    receipts = replay.get("nondeterminism_receipts")
    if not isinstance(receipts, list):
        _err(errors, "INVALID_NONDETERMINISM_RECEIPTS", "$.replay.nondeterminism_receipts", "must be a list")
        receipts = []
    env = trace.get("environment")
    if klass in {"EXACT_DETERMINISTIC", "DETERMINISTIC_UNDER_ENV_FINGERPRINT"}:
        if not isinstance(env, dict) or not _hash64(env.get("fingerprint_hash")):
            _err(errors, "ENV_FINGERPRINT_REQUIRED", "$.environment.fingerprint_hash", "deterministic replay claim requires environment fingerprint")
    if klass == "EXACT_DETERMINISTIC" and receipts:
        _err(errors, "EXACT_REPLAY_HAS_NONDETERMINISM", "$.replay.nondeterminism_receipts", "EXACT_DETERMINISTIC cannot carry unresolved nondeterministic boundaries")
    after = trace.get("basis_after")
    if isinstance(after, dict):
        if replay.get("expected_semantic_root_hash") != after.get("semantic_root_hash"):
            _err(errors, "REPLAY_FINAL_SEMANTIC_HASH_MISMATCH", "$.replay.expected_semantic_root_hash", "must equal final semantic root hash")
        if replay.get("expected_graph_root_hash") != after.get("graph_root_hash"):
            _err(errors, "REPLAY_FINAL_GRAPH_HASH_MISMATCH", "$.replay.expected_graph_root_hash", "must equal final graph root hash")


def validate_trace(trace: Any) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if not isinstance(trace, dict):
        return {"status": "FAIL", "errors": [{"code": "INVALID_TYPE", "path": "$", "detail": "trace must be an object"}], "warnings": []}
    _require(trace, ("schema_version", "trace_id", "turn_id", "identity", "architecture", "environment", "basis_before", "loop_episodes", "stages", "basis_after", "dynamic_claygraph_delta_hash", "status_snapshot", "replay"), "$", errors)
    if trace.get("schema_version") != SCHEMA_VERSION:
        _err(errors, "SCHEMA_VERSION", "$.schema_version", f"expected {SCHEMA_VERSION}")
    for key in ("trace_id", "turn_id"):
        if not isinstance(trace.get(key), str) or not trace.get(key):
            _err(errors, "INVALID_ID", f"$.{key}", "must be non-empty")
    ident = trace.get("identity")
    if not isinstance(ident, dict):
        _err(errors, "INVALID_TYPE", "$.identity", "must be an object")
    else:
        _require(ident, ("session_id", "node_execution_id", "parent_trace_ids"), "$.identity", errors)
        if not isinstance(ident.get("parent_trace_ids"), list):
            _err(errors, "INVALID_PARENT_TRACE_IDS", "$.identity.parent_trace_ids", "must be a list")
    arch = trace.get("architecture")
    if not isinstance(arch, dict):
        _err(errors, "INVALID_TYPE", "$.architecture", "must be an object")
    else:
        _require(arch, ("source_repo_head", "architecture_freeze_hash", "harness_build_hash", "semantic_contract_hash"), "$.architecture", errors)
        if "source_repo_head" in arch:
            _check_hash(errors, arch["source_repo_head"], "$.architecture.source_repo_head", length=40)
        for key in ("architecture_freeze_hash", "harness_build_hash", "semantic_contract_hash"):
            if key in arch:
                _check_hash(errors, arch[key], f"$.architecture.{key}")
    env = trace.get("environment")
    if not isinstance(env, dict):
        _err(errors, "INVALID_TYPE", "$.environment", "must be an object")
    else:
        _require(env, ("os", "arch", "runtime", "toolchain", "dependency_hash", "fingerprint_hash"), "$.environment", errors)
        if "dependency_hash" in env:
            _check_hash(errors, env["dependency_hash"], "$.environment.dependency_hash")
        if "fingerprint_hash" in env:
            if _hash64(env["fingerprint_hash"]):
                expected = environment_fingerprint(env)
                if env["fingerprint_hash"] != expected:
                    _err(errors, "ENV_FINGERPRINT_MISMATCH", "$.environment.fingerprint_hash", f"expected {expected}")
            else:
                _check_hash(errors, env["fingerprint_hash"], "$.environment.fingerprint_hash")
    _check_basis(trace.get("basis_before"), "$.basis_before", errors)
    _check_basis(trace.get("basis_after"), "$.basis_after", errors)
    before = trace.get("basis_before")
    after = trace.get("basis_after")
    if isinstance(before, dict) and isinstance(after, dict):
        for key in ("semantic_epoch", "graph_epoch"):
            if isinstance(before.get(key), int) and isinstance(after.get(key), int) and after[key] < before[key]:
                _err(errors, "EPOCH_REGRESSION", f"$.basis_after.{key}", f"before={before[key]} after={after[key]}")
    loop_ids = _validate_loops(trace, errors)
    _, stage_ids = _validate_stages(trace, loop_ids, errors, warnings)
    _validate_gwt(trace, stage_ids, errors)
    _validate_memory(trace, errors)
    _validate_topology(trace, errors)
    _validate_effects(trace, loop_ids, errors)
    _validate_visual(trace, errors)
    if "dynamic_claygraph_delta_hash" in trace:
        _check_hash(errors, trace.get("dynamic_claygraph_delta_hash"), "$.dynamic_claygraph_delta_hash")
    _validate_status_snapshot(trace, errors)
    _validate_replay(trace, errors)
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "warnings": warnings, "trace_hash": sha256_obj(trace)}


def semantic_projection(trace: dict[str, Any]) -> dict[str, Any]:
    """Representation-normalized semantic projection for H1/H2/H3 differential checks."""
    stages = trace.get("stages", []) if isinstance(trace.get("stages"), list) else []
    seq_by_id = {s.get("stage_id"): s.get("seq") for s in stages if isinstance(s, dict)}
    stage_projection = []
    for s in stages:
        if not isinstance(s, dict):
            continue
        stage_projection.append({
            "seq": s.get("seq"),
            "loop_id": s.get("loop_id"),
            "kind": s.get("kind"),
            "semantic_hash": s.get("semantic_hash"),
            "semantic_epoch": s.get("semantic_epoch"),
            "graph_epoch": s.get("graph_epoch"),
            "causal_parent_seqs": sorted(seq_by_id.get(p) for p in s.get("causal_parents", []) if p in seq_by_id),
            "intervention_id": s.get("intervention_id"),
            "bypass": bool(s.get("status") == "BYPASS"),
            "status": s.get("status"),
        })
    loops = []
    for loop in trace.get("loop_episodes", []) if isinstance(trace.get("loop_episodes"), list) else []:
        if isinstance(loop, dict):
            loops.append({k: loop.get(k) for k in ("loop_id", "parent_loop_id", "recurrence_index", "timescale", "status")})
    gwt = []
    for ep in trace.get("gwt_episodes", []) if isinstance(trace.get("gwt_episodes"), list) else []:
        if not isinstance(ep, dict):
            continue
        receivers = []
        for r in ep.get("receivers", []) if isinstance(ep.get("receivers"), list) else []:
            if isinstance(r, dict):
                receivers.append({"receiver_id": r.get("receiver_id"), **{k: r.get(k) for k in GWT_FIELDS}})
        gwt.append({"workspace_episode_id": ep.get("workspace_episode_id"), "receivers": sorted(receivers, key=lambda x: str(x.get("receiver_id")))})
    memory = []
    for m in trace.get("memory_uses", []) if isinstance(trace.get("memory_uses"), list) else []:
        if isinstance(m, dict):
            memory.append({k: m.get(k) for k in ("memory_ref", "retrieved", "admissibility", "consequential_use")})
    effects = []
    for e in trace.get("effects", []) if isinstance(trace.get("effects"), list) else []:
        if isinstance(e, dict):
            effects.append({
                "effect_id": e.get("effect_id"),
                "loop_id": e.get("loop_id"),
                "attempt_count": e.get("attempt_count"),
                "capabilities_before": sorted(e.get("capabilities_before", [])) if isinstance(e.get("capabilities_before"), list) else e.get("capabilities_before"),
                "capabilities_after": sorted(e.get("capabilities_after", [])) if isinstance(e.get("capabilities_after"), list) else e.get("capabilities_after"),
                "denied": e.get("denied"),
            })
    snap = trace.get("status_snapshot") if isinstance(trace.get("status_snapshot"), dict) else {}
    return {
        "schema_version": trace.get("schema_version"),
        "architecture_freeze_hash": (trace.get("architecture") or {}).get("architecture_freeze_hash") if isinstance(trace.get("architecture"), dict) else None,
        "semantic_contract_hash": (trace.get("architecture") or {}).get("semantic_contract_hash") if isinstance(trace.get("architecture"), dict) else None,
        "basis_before": trace.get("basis_before"),
        "loops": loops,
        "stages": stage_projection,
        "gwt": gwt,
        "memory": memory,
        "topology": trace.get("topology"),
        "effects": effects,
        "basis_after": trace.get("basis_after"),
        "dynamic_claygraph_delta_hash": trace.get("dynamic_claygraph_delta_hash"),
        "status_basis": {k: snap.get(k) for k in ("semantic_epoch", "semantic_root_hash", "graph_epoch", "graph_root_hash", "v01_gate_vector", "active_skill_revision")},
    }


def _first_diff(a: Any, b: Any, path: str = "$") -> dict[str, Any] | None:
    if type(a) is not type(b):
        return {"path": path, "reference": a, "candidate": b, "kind": "TYPE"}
    if isinstance(a, dict):
        keys = sorted(set(a) | set(b))
        for key in keys:
            if key not in a:
                return {"path": f"{path}.{key}", "reference": "<MISSING>", "candidate": b[key], "kind": "MISSING_REFERENCE"}
            if key not in b:
                return {"path": f"{path}.{key}", "reference": a[key], "candidate": "<MISSING>", "kind": "MISSING_CANDIDATE"}
            d = _first_diff(a[key], b[key], f"{path}.{key}")
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return {"path": path, "reference": len(a), "candidate": len(b), "kind": "LENGTH"}
        for i, (av, bv) in enumerate(zip(a, b)):
            d = _first_diff(av, bv, f"{path}[{i}]")
            if d:
                return d
        return None
    if a != b:
        return {"path": path, "reference": a, "candidate": b, "kind": "VALUE"}
    return None


def compare_traces(reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    rv = validate_trace(reference)
    cv = validate_trace(candidate)
    if rv["status"] != "PASS" or cv["status"] != "PASS":
        return {"status": "INVALID_INPUT", "reference_validation": rv, "candidate_validation": cv}
    rp = semantic_projection(reference)
    cp = semantic_projection(candidate)
    diff = _first_diff(rp, cp)
    return {
        "status": "EQUIVALENT" if diff is None else "DIVERGENT",
        "first_divergence": diff,
        "reference_projection_hash": sha256_obj(rp),
        "candidate_projection_hash": sha256_obj(cp),
    }


def make_environment(runtime: str = "python-stdlib-reference") -> dict[str, Any]:
    env = {
        "os": platform.system().lower(),
        "arch": platform.machine().lower(),
        "runtime": runtime,
        "toolchain": f"python-{platform.python_version()}",
        "dependency_hash": sha256_text("stdlib-only"),
    }
    env["fingerprint_hash"] = environment_fingerprint(env)
    return env


def make_example_trace() -> dict[str, Any]:
    h = sha256_text
    before = {"semantic_epoch": 7, "semantic_root_hash": h("sem-7"), "graph_epoch": 11, "graph_root_hash": h("graph-11")}
    after = {"semantic_epoch": 8, "semantic_root_hash": h("sem-8"), "graph_epoch": 12, "graph_root_hash": h("graph-12")}
    loop_id = "loop:turn:1"
    stage_kinds = ["external_input", "candidate", "competition", "workspace", "broadcast", "receiver_delivery", "reconstruction", "uptake", "causal_use", "model_transform", "outcome", "reentry"]
    stages = []
    prev = None
    ids = {}
    for n, kind in enumerate(stage_kinds, 1):
        sid = f"stage:{n}:{kind}"
        ids[kind] = sid
        stages.append({
            "stage_id": sid,
            "seq": n,
            "cycle_id": "cycle:1",
            "loop_id": loop_id,
            "kind": kind,
            "input_hash": h(f"input:{n}"),
            "output_hash": h(f"output:{n}"),
            "semantic_hash": h(f"semantic:{kind}"),
            "semantic_epoch": 7 if n < len(stage_kinds) else 8,
            "graph_epoch": 11 if n < len(stage_kinds) else 12,
            "causal_parents": [prev] if prev else [],
            "receipts": [f"receipt:{kind}"],
            "status": "OK",
            "authority_granted": False,
        })
        prev = sid
    rr = {k: f"receipt:receiver:{k}" for k in GWT_FIELDS}
    trace = {
        "schema_version": SCHEMA_VERSION,
        "trace_id": "trace:example",
        "turn_id": "turn:example",
        "identity": {"session_id": "session:example", "node_execution_id": "node:example", "parent_trace_ids": []},
        "architecture": {
            "source_repo_head": "d916b98fb65dc62fbf3275d6a48dc52c2bfc2612",
            "architecture_freeze_hash": h("architecture-freeze"),
            "harness_build_hash": h("harness-build"),
            "semantic_contract_hash": h("semantic-contract"),
        },
        "environment": make_environment(),
        "basis_before": before,
        "loop_episodes": [{"loop_id": loop_id, "parent_loop_id": None, "recurrence_index": 0, "timescale": "TURN", "budget_before": 4, "budget_after": 3, "status": "CONTINUE"}],
        "stages": stages,
        "gwt_episodes": [{
            "workspace_episode_id": "workspace:1",
            "stage_refs": {
                "candidate": ids["candidate"], "competition": ids["competition"], "workspace": ids["workspace"],
                "broadcast": ids["broadcast"], "outcome": ids["outcome"], "reentry": ids["reentry"]
            },
            "receivers": [{"receiver_id": "receiver:model", **{k: True for k in GWT_FIELDS}, "receipt_refs": rr}],
        }],
        "memory_uses": [{"memory_ref": "memory:1", "retrieved": True, "admissibility": "ADMIT", "consequential_use": True, "receipt_ref": "receipt:memory:1"}],
        "topology": {
            "semantic_hash": h("topology:semantic"),
            "active_hash": h("topology:active"),
            "coordination_hash": h("topology:coordination"),
            "physical_hash": h("topology:physical"),
            "interventions": [],
        },
        "effects": [{
            "effect_id": "effect:1", "loop_id": loop_id, "attempt_count": 1,
            "capabilities_before": ["read"], "capabilities_after": ["read"],
            "external_authorization_ref": None, "denied": False, "cumulative_resource_cost": 0.1,
        }],
        "visual": {"authority_granted_by_visual_model": False, "familiarity_state": "UNKNOWN"},
        "basis_after": after,
        "dynamic_claygraph_delta_hash": h("run-claygraph-delta"),
        "status_snapshot": {
            "snapshot_id": "status:1", "source_repo_head": "d916b98fb65dc62fbf3275d6a48dc52c2bfc2612",
            "semantic_epoch": after["semantic_epoch"], "semantic_root_hash": after["semantic_root_hash"],
            "graph_epoch": after["graph_epoch"], "graph_root_hash": after["graph_root_hash"],
            "integrity_state": "VERIFIED", "now_basis_refs": ["trace:example"], "next_basis_refs": ["work:next"],
            "node_groups": [{"label": "FRANK-LOCAL", "member_count": 2, "member_ids": ["node:a", "node:b"]}],
            "v01_gate_vector": ["PASS", "OPEN"], "active_skill_revision": None,
        },
        "replay": {
            "class": "DETERMINISTIC_UNDER_ENV_FINGERPRINT",
            "frozen_inputs_hash": h("frozen-inputs"),
            "expected_semantic_root_hash": after["semantic_root_hash"],
            "expected_graph_root_hash": after["graph_root_hash"],
            "nondeterminism_receipts": [],
        },
    }
    trace["status_snapshot"]["snapshot_hash"] = status_snapshot_hash(trace["status_snapshot"])
    return trace


def run_self_tests() -> dict[str, Any]:
    tests: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        tests.append((name, bool(condition), detail))

    base = make_example_trace()
    check("valid_reference_trace", validate_trace(base)["status"] == "PASS")

    t = copy.deepcopy(base)
    t["gwt_episodes"][0]["receivers"][0]["reconstructed"] = False
    codes = {e["code"] for e in validate_trace(t)["errors"]}
    check("gwt_uptake_requires_reconstruction", "GWT_CAUSAL_CHAIN_VIOLATION" in codes)

    t = copy.deepcopy(base)
    t["effects"][0]["capabilities_after"] = ["read", "write"]
    codes = {e["code"] for e in validate_trace(t)["errors"]}
    check("recurrence_cannot_mint_authority", "AUTHORITY_WIDENED_WITHOUT_EXTERNAL_AUTHORIZATION" in codes)

    t = copy.deepcopy(base)
    t["effects"][0]["capabilities_after"] = ["read", "write"]
    t["effects"][0]["external_authorization_ref"] = "owner-auth:1"
    check("external_authorization_can_expand_declared_set", validate_trace(t)["status"] == "PASS")

    t = copy.deepcopy(base)
    t["stages"][0]["causal_parents"] = [t["stages"][1]["stage_id"]]
    codes = {e["code"] for e in validate_trace(t)["errors"]}
    check("future_causal_parent_rejected", "NONCAUSAL_PARENT_ORDER" in codes)

    t = copy.deepcopy(base)
    t["status_snapshot"]["semantic_epoch"] = 999
    t["status_snapshot"]["snapshot_hash"] = status_snapshot_hash(t["status_snapshot"])
    codes = {e["code"] for e in validate_trace(t)["errors"]}
    check("status_snapshot_must_bind_final_epoch", "STATUS_NOT_BOUND_TO_FINAL_BASIS" in codes)

    t = copy.deepcopy(base)
    t["environment"].pop("fingerprint_hash")
    codes = {e["code"] for e in validate_trace(t)["errors"]}
    check("deterministic_replay_requires_environment_fingerprint", "ENV_FINGERPRINT_REQUIRED" in codes)

    t = copy.deepcopy(base)
    t["memory_uses"][0]["admissibility"] = "QUARANTINE"
    codes = {e["code"] for e in validate_trace(t)["errors"]}
    check("quarantined_memory_cannot_drive_consequential_use", "MEMORY_USE_NOT_ADMITTED" in codes)

    t = copy.deepcopy(base)
    t["visual"]["authority_granted_by_visual_model"] = True
    codes = {e["code"] for e in validate_trace(t)["errors"]}
    check("visual_familiarity_never_authority", "VISUAL_MODEL_AUTHORITY" in codes)

    t = copy.deepcopy(base)
    t["loop_episodes"].append({"loop_id": "loop:turn:2", "parent_loop_id": "loop:turn:1", "recurrence_index": 1, "timescale": "REENTRY", "budget_before": 3, "budget_after": 2, "status": "CONTINUE"})
    t["stages"][-1]["loop_id"] = "loop:turn:2"
    check("recurrent_loop_identity_allowed", validate_trace(t)["status"] == "PASS")

    a = copy.deepcopy(base)
    b = copy.deepcopy(base)
    b["stages"][7]["semantic_hash"] = sha256_text("different-uptake-semantics")
    d = compare_traces(a, b)
    check("differential_localizes_first_semantic_divergence", d["status"] == "DIVERGENT" and d["first_divergence"]["path"].endswith(".semantic_hash"), canonical_json(d.get("first_divergence")))

    x1 = {"b": 2, "a": 1}
    x2 = {"a": 1, "b": 2}
    check("canonical_hash_order_independent", sha256_obj(x1) == sha256_obj(x2))

    t = copy.deepcopy(base)
    t["effects"][0].update({"attempt_count": 2, "denied": True, "retry_reason": "reconsider intent", "repeated_denial_indicator": True})
    check("repeated_denial_with_fixed_authority_is_representable", validate_trace(t)["status"] == "PASS")

    failed = [{"name": n, "detail": d} for n, ok, d in tests if not ok]
    return {
        "schema_version": "1.0",
        "status": "PASS" if not failed else "FAIL",
        "tests_total": len(tests),
        "tests_passed": len(tests) - len(failed),
        "failed": failed,
        "evidence_class": "LOCAL_SYNTHETIC_EXECUTION",
        "module_hash": sha256_text(open(__file__, "r", encoding="utf-8").read()),
        "environment": make_environment("trace-replay-v1-self-test"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--validate")
    parser.add_argument("--compare", nargs=2, metavar=("REFERENCE", "CANDIDATE"))
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(run_self_tests(), ensure_ascii=False, sort_keys=True, indent=2))
        return
    if args.validate:
        with open(args.validate, "r", encoding="utf-8") as f:
            trace = json.load(f)
        result = validate_trace(trace)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        raise SystemExit(0 if result["status"] == "PASS" else 1)
    if args.compare:
        with open(args.compare[0], "r", encoding="utf-8") as f:
            ref = json.load(f)
        with open(args.compare[1], "r", encoding="utf-8") as f:
            cand = json.load(f)
        result = compare_traces(ref, cand)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        raise SystemExit(0 if result["status"] == "EQUIVALENT" else 1)
    parser.print_help()


if __name__ == "__main__":
    main()
