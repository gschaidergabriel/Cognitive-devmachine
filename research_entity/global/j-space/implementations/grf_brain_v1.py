#!/usr/bin/env python3
"""Deterministic, fail-closed GRF cognition trace compiler/validator.

This module implements the typed R0..R6 Generative Reality Framework control
trace as candidate-only cognition. It owns no durable truth/state, model
execution, GWT selection, effect authority, or product/runtime promotion.

A valid trace is bound to the canonical versioned GRF framework object through
``framework_digest``. ``trace_digest`` identifies the concrete R0..R6 evidence
trace itself. These identities are deliberately separate: the per-turn trace
must never replace or impersonate the canonical UnifiedDB GRF object. The trace
remains a reproducible candidate/control artifact with zero direct authority.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

SCHEMA = "OMEGA_GRF_BRAIN_TRACE/v1"
NODE_SCHEMA = "OMEGA_GRF_BRAIN_NODE/v1"
COMPILER_VERSION = "omega-grf-brain/1.0"
GRF_ID = "GENERATIVE_REALITY_FRAMEWORK"

STAGES = (
    "R0_OBSERVED",
    "R1_INFERRED",
    "R2_GENERATED",
    "R3_COUNTER_REALITY",
    "R4_DISCRIMINATED",
    "R5_EMERGENT",
    "R6_VERIFIED",
)
STAGE_INDEX = {stage: i for i, stage in enumerate(STAGES)}

REALITY_CLASSES = {
    "OBSERVED",
    "INFERRED",
    "RETRIEVED",
    "PREDICTED",
    "HYPOTHETICAL",
    "INTERVENTIONAL",
    "COUNTERFACTUAL",
    "PLANNED",
    "DESIRED",
    "IMAGINED",
    "REPLAY",
    "ADVERSARIAL",
}

EPISTEMIC_STATUS = {
    "EVIDENCE",
    "CANDIDATE",
    "SUPPORTED",
    "FALSIFIED",
    "UNKNOWN",
    "VERIFIED",
}

NODE_KINDS = {
    "OBSERVATION",
    "RETRIEVAL",
    "INFERENCE",
    "HYPOTHESIS",
    "COUNTERHYPOTHESIS",
    "POSSIBLE_WORLD",
    "DISCRIMINATOR",
    "INTERVENTION",
    "OBSERVATION_CONFIRMATION",
    "SYNTHESIS",
    "SCOPE_DECISION",
}

AUTHORITY = {
    "direct_truth_authority": False,
    "direct_state_authority": False,
    "direct_effect_authority": False,
    "model_output": "CANDIDATE_ONLY",
    "truth_admission": "EXTERNAL_DETERMINISTIC_GATE_ONLY",
    "effect_admission": "EXTERNAL_DETERMINISTIC_EFFECT_GATE_ONLY",
}

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_NODE_KEYS = {
    "schema",
    "node_id",
    "stage",
    "kind",
    "reality_class",
    "epistemic_status",
    "claim",
    "depends_on",
    "evidence_refs",
    "provenance_refs",
    "factual_parent",
    "interventions",
    "causal_assumptions",
    "shared_factual_context",
    "decision_scope",
    "credit_scope",
    "metadata",
    "node_digest",
}
_TRACE_KEYS = {
    "schema",
    "compiler_version",
    "framework_id",
    "entity_generation",
    "causal_turn_id",
    "question",
    "framework_digest",
    "authority_digest",
    "source_state_digest",
    "authority",
    "state",
    "nodes",
    "negative_evidence_refs",
    "contradiction_state",
    "not_promoted",
    "trace_digest",
}


class GRFError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise GRFError(message)


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise GRFError("NONCANONICAL_JSON") from exc


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str, *, allow_empty: bool = False) -> str:
    _need(type(value) is str, f"{name}:STRING_REQUIRED")
    value = value.strip()
    if not allow_empty:
        _need(bool(value), f"{name}:NONEMPTY_REQUIRED")
    return value


def _strings(value: Any, name: str, *, nonempty: bool = False) -> list[str]:
    _need(type(value) is list, f"{name}:LIST_REQUIRED")
    out = [_text(item, f"{name}[]") for item in value]
    _need(len(out) == len(set(out)), f"{name}:DUPLICATE")
    if nonempty:
        _need(bool(out), f"{name}:NONEMPTY_REQUIRED")
    return out


def make_node(
    *,
    node_id: str,
    stage: str,
    kind: str,
    reality_class: str,
    epistemic_status: str,
    claim: str,
    depends_on: Sequence[str] = (),
    evidence_refs: Sequence[str] = (),
    provenance_refs: Sequence[str] = (),
    factual_parent: str | None = None,
    interventions: Sequence[str] = (),
    causal_assumptions: Sequence[str] = (),
    shared_factual_context: Sequence[str] = (),
    decision_scope: str | None = None,
    credit_scope: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create one immutable GRF node and bind it to its content digest."""
    node = {
        "schema": NODE_SCHEMA,
        "node_id": _text(node_id, "node_id"),
        "stage": stage,
        "kind": kind,
        "reality_class": reality_class,
        "epistemic_status": epistemic_status,
        "claim": _text(claim, "claim"),
        "depends_on": list(depends_on),
        "evidence_refs": list(evidence_refs),
        "provenance_refs": list(provenance_refs),
        "factual_parent": factual_parent,
        "interventions": list(interventions),
        "causal_assumptions": list(causal_assumptions),
        "shared_factual_context": list(shared_factual_context),
        "decision_scope": decision_scope,
        "credit_scope": credit_scope,
        "metadata": {} if metadata is None else copy.deepcopy(dict(metadata)),
    }
    _validate_node_shape(node)
    node["node_digest"] = sha256_obj(node)
    _validate_node_shape(node, require_digest=True)
    return node


def new_trace(
    *,
    entity_generation: int,
    causal_turn_id: str,
    question: str,
    framework_digest: str,
    authority_digest: str,
    source_state_digest: str,
    contradiction_state: str = "UNKNOWN",
    negative_evidence_refs: Sequence[str] = (),
    not_promoted: Sequence[str] = (),
) -> dict[str, Any]:
    _need(type(entity_generation) is int and entity_generation >= 0, "ENTITY_GENERATION_INVALID")
    trace = {
        "schema": SCHEMA,
        "compiler_version": COMPILER_VERSION,
        "framework_id": GRF_ID,
        "entity_generation": entity_generation,
        "causal_turn_id": _text(causal_turn_id, "causal_turn_id"),
        "question": _text(question, "question"),
        "framework_digest": _digest(framework_digest, "framework_digest"),
        "authority_digest": _digest(authority_digest, "authority_digest"),
        "source_state_digest": _digest(source_state_digest, "source_state_digest"),
        "authority": dict(AUTHORITY),
        "state": "OPEN",
        "nodes": [],
        "negative_evidence_refs": list(negative_evidence_refs),
        "contradiction_state": _text(contradiction_state, "contradiction_state"),
        "not_promoted": list(not_promoted),
        "trace_digest": None,
    }
    validate(trace, allow_open=True)
    return trace


def append_node(trace: Mapping[str, Any], node: Mapping[str, Any]) -> dict[str, Any]:
    """Return a new trace with one node appended; never mutates the prior trace."""
    current = copy.deepcopy(dict(trace))
    validate(current, allow_open=True)
    _need(current["state"] == "OPEN", "TRACE_ALREADY_SEALED")
    material = copy.deepcopy(dict(node))
    _validate_node_shape(material, require_digest=True)
    existing = {item["node_id"] for item in current["nodes"]}
    _need(material["node_id"] not in existing, "NODE_ID_REUSE_FORBIDDEN")
    if current["nodes"]:
        last_stage = STAGE_INDEX[current["nodes"][-1]["stage"]]
        this_stage = STAGE_INDEX[material["stage"]]
        _need(this_stage >= last_stage, "STAGE_ORDER_REGRESSION")
        _need(this_stage <= last_stage + 1, "STAGE_SKIP_FORBIDDEN")
    else:
        _need(material["stage"] == STAGES[0], "TRACE_MUST_BEGIN_R0")
    current["nodes"].append(material)
    validate(current, allow_open=True)
    return current


def seal_trace(trace: Mapping[str, Any]) -> dict[str, Any]:
    """Seal only a complete R0..R6 trace with externally evidenced scoped verification."""
    out = copy.deepcopy(dict(trace))
    validate(out, allow_open=True)
    _need(out["state"] == "OPEN", "TRACE_ALREADY_SEALED")
    seen_stages = {node["stage"] for node in out["nodes"]}
    _need(seen_stages == set(STAGES), "SEALED_TRACE_REQUIRES_ALL_R0_R6")
    r6 = [node for node in out["nodes"] if node["stage"] == "R6_VERIFIED"]
    _need(bool(r6), "R6_REQUIRED")
    for node in r6:
        _need(node["kind"] == "SCOPE_DECISION", "R6_SCOPE_DECISION_REQUIRED")
        _need(node["epistemic_status"] == "VERIFIED", "R6_VERIFIED_STATUS_REQUIRED")
        _need(bool(node["evidence_refs"]), "R6_EXTERNAL_EVIDENCE_REQUIRED")
        _need(bool(node["decision_scope"]), "R6_DECISION_SCOPE_REQUIRED")
        _need(bool(node["credit_scope"]), "R6_CREDIT_SCOPE_REQUIRED")
    out["state"] = "SEALED"
    out["trace_digest"] = sha256_obj({k: v for k, v in out.items() if k != "trace_digest"})
    validate(out, allow_open=False)
    return out


def _validate_node_shape(node: Mapping[str, Any], *, require_digest: bool = False) -> None:
    _need(isinstance(node, Mapping), "NODE_OBJECT_REQUIRED")
    data = dict(node)
    allowed = _NODE_KEYS if require_digest else (_NODE_KEYS - {"node_digest"})
    _need(set(data) == allowed, "NODE_FIELD_SET_MISMATCH")
    _need(data.get("schema") == NODE_SCHEMA, "NODE_SCHEMA_MISMATCH")
    _text(data.get("node_id"), "node_id")
    stage = data.get("stage")
    _need(stage in STAGE_INDEX, "NODE_STAGE_INVALID")
    kind = data.get("kind")
    _need(kind in NODE_KINDS, "NODE_KIND_INVALID")
    reality_class = data.get("reality_class")
    _need(reality_class in REALITY_CLASSES, "REALITY_CLASS_INVALID")
    epistemic = data.get("epistemic_status")
    _need(epistemic in EPISTEMIC_STATUS, "EPISTEMIC_STATUS_INVALID")
    _text(data.get("claim"), "claim")
    _strings(data.get("depends_on"), "depends_on")
    _strings(data.get("evidence_refs"), "evidence_refs")
    _strings(data.get("provenance_refs"), "provenance_refs")
    _strings(data.get("interventions"), "interventions")
    _strings(data.get("causal_assumptions"), "causal_assumptions")
    _strings(data.get("shared_factual_context"), "shared_factual_context")
    factual_parent = data.get("factual_parent")
    _need(factual_parent is None or (type(factual_parent) is str and factual_parent.strip()), "FACTUAL_PARENT_INVALID")
    for optional_name in ("decision_scope", "credit_scope"):
        value = data.get(optional_name)
        _need(value is None or (type(value) is str and value.strip()), f"{optional_name}:INVALID")
    _need(type(data.get("metadata")) is dict, "NODE_METADATA_OBJECT_REQUIRED")
    canonical_json(data.get("metadata"))

    if stage == "R0_OBSERVED":
        _need(kind in {"OBSERVATION", "RETRIEVAL", "OBSERVATION_CONFIRMATION"}, "R0_KIND_INVALID")
        _need(reality_class in {"OBSERVED", "RETRIEVED"}, "R0_REALITY_CLASS_INVALID")
        _need(epistemic in {"EVIDENCE", "UNKNOWN"}, "R0_EPISTEMIC_INVALID")
        if reality_class == "OBSERVED":
            _need(bool(data["evidence_refs"]), "OBSERVED_REQUIRES_EVIDENCE")
    elif stage == "R1_INFERRED":
        _need(kind in {"INFERENCE", "HYPOTHESIS"}, "R1_KIND_INVALID")
        _need(reality_class == "INFERRED", "R1_MUST_BE_INFERRED")
        _need(epistemic in {"CANDIDATE", "SUPPORTED", "UNKNOWN", "FALSIFIED"}, "R1_EPISTEMIC_INVALID")
    elif stage == "R2_GENERATED":
        _need(kind in {"HYPOTHESIS", "POSSIBLE_WORLD"}, "R2_KIND_INVALID")
        _need(reality_class not in {"OBSERVED", "RETRIEVED"}, "GENERATED_CANNOT_BE_OBSERVED")
        _need(epistemic in {"CANDIDATE", "SUPPORTED", "UNKNOWN", "FALSIFIED"}, "R2_EPISTEMIC_INVALID")
    elif stage == "R3_COUNTER_REALITY":
        _need(kind in {"COUNTERHYPOTHESIS", "POSSIBLE_WORLD"}, "R3_KIND_INVALID")
        _need(reality_class not in {"OBSERVED", "RETRIEVED"}, "COUNTER_REALITY_CANNOT_BE_OBSERVED")
        _need(epistemic in {"CANDIDATE", "SUPPORTED", "UNKNOWN", "FALSIFIED"}, "R3_EPISTEMIC_INVALID")
    elif stage == "R4_DISCRIMINATED":
        _need(kind in {"DISCRIMINATOR", "INTERVENTION", "OBSERVATION_CONFIRMATION"}, "R4_KIND_INVALID")
        _need(epistemic != "VERIFIED", "R4_CANNOT_MINT_VERIFIED")
    elif stage == "R5_EMERGENT":
        _need(kind == "SYNTHESIS", "R5_SYNTHESIS_REQUIRED")
        _need(reality_class in {"INFERRED", "HYPOTHETICAL", "PREDICTED"}, "R5_REALITY_CLASS_INVALID")
        _need(epistemic in {"CANDIDATE", "SUPPORTED", "UNKNOWN", "FALSIFIED"}, "R5_CANNOT_SELF_VERIFY")
    elif stage == "R6_VERIFIED":
        _need(kind == "SCOPE_DECISION", "R6_SCOPE_DECISION_REQUIRED")
        _need(reality_class in {"OBSERVED", "INFERRED", "RETRIEVED"}, "R6_REALITY_CLASS_INVALID")
        _need(epistemic == "VERIFIED", "R6_VERIFIED_STATUS_REQUIRED")
        _need(bool(data["evidence_refs"]), "R6_EXTERNAL_EVIDENCE_REQUIRED")
        _need(bool(data.get("decision_scope")), "R6_DECISION_SCOPE_REQUIRED")
        _need(bool(data.get("credit_scope")), "R6_CREDIT_SCOPE_REQUIRED")

    if reality_class == "COUNTERFACTUAL":
        _need(bool(factual_parent), "COUNTERFACTUAL_FACTUAL_PARENT_REQUIRED")
        _need(bool(data["interventions"]), "COUNTERFACTUAL_INTERVENTION_REQUIRED")
        _need(bool(data["causal_assumptions"]), "COUNTERFACTUAL_CAUSAL_ASSUMPTIONS_REQUIRED")
        _need(bool(data["shared_factual_context"]), "COUNTERFACTUAL_SHARED_CONTEXT_REQUIRED")

    if reality_class in {"PREDICTED", "HYPOTHETICAL", "INTERVENTIONAL", "COUNTERFACTUAL", "PLANNED", "DESIRED", "IMAGINED", "REPLAY", "ADVERSARIAL"}:
        _need(epistemic != "VERIFIED", "SYNTHETIC_CLASS_CANNOT_BE_VERIFIED_FACT")

    if require_digest:
        digest = _digest(data.get("node_digest"), "node_digest")
        unsigned = dict(data)
        unsigned.pop("node_digest")
        _need(digest == sha256_obj(unsigned), "NODE_DIGEST_MISMATCH")


def validate(trace: Mapping[str, Any], *, allow_open: bool = True) -> dict[str, Any]:
    _need(isinstance(trace, Mapping), "TRACE_OBJECT_REQUIRED")
    doc = dict(trace)
    _need(set(doc) == _TRACE_KEYS, "TRACE_FIELD_SET_MISMATCH")
    _need(doc.get("schema") == SCHEMA, "TRACE_SCHEMA_MISMATCH")
    _need(doc.get("compiler_version") == COMPILER_VERSION, "COMPILER_VERSION_MISMATCH")
    _need(doc.get("framework_id") == GRF_ID, "FRAMEWORK_ID_MISMATCH")
    generation = doc.get("entity_generation")
    _need(type(generation) is int and generation >= 0, "ENTITY_GENERATION_INVALID")
    _text(doc.get("causal_turn_id"), "causal_turn_id")
    _text(doc.get("question"), "question")
    _digest(doc.get("framework_digest"), "framework_digest")
    _digest(doc.get("authority_digest"), "authority_digest")
    _digest(doc.get("source_state_digest"), "source_state_digest")
    _need(doc.get("authority") == AUTHORITY, "AUTHORITY_ESCALATION")
    state = doc.get("state")
    _need(state in {"OPEN", "SEALED"}, "TRACE_STATE_INVALID")
    if state == "OPEN":
        _need(allow_open, "OPEN_TRACE_NOT_ADMITTED")
        _need(doc.get("trace_digest") is None, "OPEN_TRACE_CANNOT_HAVE_TRACE_DIGEST")
    else:
        digest = _digest(doc.get("trace_digest"), "trace_digest")
        unsigned = dict(doc)
        unsigned.pop("trace_digest")
        _need(digest == sha256_obj(unsigned), "TRACE_DIGEST_MISMATCH")

    negatives = _strings(doc.get("negative_evidence_refs"), "negative_evidence_refs")
    _text(doc.get("contradiction_state"), "contradiction_state")
    _strings(doc.get("not_promoted"), "not_promoted")
    nodes = doc.get("nodes")
    _need(type(nodes) is list, "NODES_LIST_REQUIRED")

    by_id: dict[str, dict[str, Any]] = {}
    last_stage = -1
    seen_stage_indexes: set[int] = set()
    for raw in nodes:
        _need(type(raw) is dict, "NODE_OBJECT_REQUIRED")
        _validate_node_shape(raw, require_digest=True)
        node = dict(raw)
        node_id = node["node_id"]
        _need(node_id not in by_id, "NODE_ID_REUSE_FORBIDDEN")
        stage_idx = STAGE_INDEX[node["stage"]]
        _need(stage_idx >= last_stage, "STAGE_ORDER_REGRESSION")
        if last_stage >= 0:
            _need(stage_idx <= last_stage + 1, "STAGE_SKIP_FORBIDDEN")
        else:
            _need(stage_idx == 0, "TRACE_MUST_BEGIN_R0")
        last_stage = stage_idx
        seen_stage_indexes.add(stage_idx)

        for dep in node["depends_on"]:
            _need(dep in by_id, "DEPENDENCY_MUST_PRECEDE_NODE")
            _need(STAGE_INDEX[by_id[dep]["stage"]] <= stage_idx, "DEPENDENCY_FROM_FUTURE_FORBIDDEN")
        if stage_idx > 0:
            _need(bool(node["depends_on"]), "NON_R0_REQUIRES_DEPENDENCY")
            _need(
                any(STAGE_INDEX[by_id[dep]["stage"]] == stage_idx - 1 for dep in node["depends_on"]),
                "IMMEDIATE_PREDECESSOR_DEPENDENCY_REQUIRED",
            )
        if node["factual_parent"] is not None:
            _need(node["factual_parent"] in by_id, "FACTUAL_PARENT_MUST_PRECEDE_NODE")
            if node["reality_class"] == "COUNTERFACTUAL":
                parent = by_id[node["factual_parent"]]
                _need(
                    parent["stage"] == "R0_OBSERVED"
                    and parent["reality_class"] in {"OBSERVED", "RETRIEVED"},
                    "COUNTERFACTUAL_FACTUAL_PARENT_NOT_FACTUAL",
                )

        if node["reality_class"] == "OBSERVED" and node["kind"] == "OBSERVATION_CONFIRMATION":
            _need(bool(node["evidence_refs"]), "OBSERVATION_CONFIRMATION_REQUIRES_INDEPENDENT_EVIDENCE")
        by_id[node_id] = node

    if nodes:
        expected_prefix = set(range(max(seen_stage_indexes) + 1))
        _need(seen_stage_indexes == expected_prefix, "STAGES_MUST_FORM_PREFIX")

    for node in nodes:
        if node["stage"] == "R6_VERIFIED":
            overlap = set(node["evidence_refs"]) & set(negatives)
            _need(not overlap, "NEGATIVE_EVIDENCE_CANNOT_BECOME_POSITIVE_BY_REFERENCE")

    if state == "SEALED":
        _need(seen_stage_indexes == set(range(len(STAGES))), "SEALED_TRACE_REQUIRES_ALL_R0_R6")
        _need(any(node["stage"] == "R6_VERIFIED" for node in nodes), "SEALED_TRACE_REQUIRES_R6")

    return {
        "ok": True,
        "schema": SCHEMA,
        "state": state,
        "nodes": len(nodes),
        "framework_digest": doc.get("framework_digest"),
        "trace_digest": doc.get("trace_digest"),
        "runtime_credit": "ZERO",
        "truth_credit": "ZERO",
        "effect_credit": "ZERO",
        "whole_system_credit": "ZERO",
    }
