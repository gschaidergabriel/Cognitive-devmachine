#!/usr/bin/env python3
"""Fail-closed compiler/validator for ZERO_WORKSPACE_CAPSULE/v1.

Scope: deterministic control-envelope construction only.
It does not create truth, state, effect, J-Space runtime, model-runtime, or product credit.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA = "ZERO_WORKSPACE_CAPSULE/v1"
COMPILER_VERSION = "zero-workspace-capsule/1.0"
ZERO_IDENTITY_ID = "ZERO"
GRF_ID = "GENERATIVE_REALITY_FRAMEWORK"
GRF_STAGES = ("R0_OBSERVED", "R1_INFERRED", "R2_GENERATED", "R3_COUNTER_REALITY",
              "R4_INTERVENTION", "R5_EMERGENT", "R6_VERIFIED")
AUTHORITY = {
    "truth": "MINIUNIFIEDDB_DETERMINISTIC_GATES",
    "state": "MINIUNIFIEDDB_DETERMINISTIC_GATES",
    "effects": "DETERMINISTIC_EFFECT_GATES",
    "model_output": "CANDIDATE_ONLY",
    "jspace": "MEASUREMENT_NOT_TRUTH",
    "hyperposition": "ALTERNATIVES_NOT_FACTS",
}
UNAVAILABLE_REASONS = {
    "JSPACE_UNAVAILABLE",
    "LENS_UNFITTED",
    "LOCAL_MODEL_UNAVAILABLE",
    "IDENTITY_PROJECTION_STALE",
    "GRF_PROJECTION_STALE",
    "HYPERPOSITION_STATE_UNAVAILABLE",
    "WORKSPACE_ABSTAINED",
}
CAPSULE_KEYS = {
    "schema", "compiler_version", "identity", "grf", "authority",
    "entity_generation", "causal_turn_id", "task", "mode",
    "zero_identity_digest", "grf_digest", "hyperposition_digest",
    "local_model_digest", "jacobian_lens_digest", "workspace_digest",
    "selected_workspace_slots", "contradiction_state", "provenance_refs",
    "required_zero_mode", "abstention_reason", "capsule_digest",
}
TASK_KEYS = {"format", "text", "sha256", "structural_authority"}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CapsuleError(ValueError):
    pass


def _need(cond: bool, msg: str) -> None:
    if not cond:
        raise CapsuleError(msg)


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _digest(value: str, name: str) -> str:
    _need(isinstance(value, str) and bool(_HEX64.fullmatch(value)), f"{name} must be lowercase sha256")
    _need(len(set(value)) > 1, f"{name} placeholder digest rejected")
    return value


def _nonempty(value: str, name: str) -> str:
    _need(isinstance(value, str) and value.strip() != "", f"{name} must be nonempty")
    return value.strip()


def _base(*, entity_generation: int, causal_turn_id: str, task_text: str) -> dict[str, Any]:
    _need(isinstance(entity_generation, int) and not isinstance(entity_generation, bool) and entity_generation >= 0,
          "entity_generation must be nonnegative integer")
    _need(isinstance(task_text, str), "task_text must be string")
    causal_turn_id = _nonempty(causal_turn_id, "causal_turn_id")
    task = {
        "format": "OPAQUE_USER_TASK_TEXT/v1",
        "text": task_text,
        "sha256": hashlib.sha256(task_text.encode("utf-8")).hexdigest(),
        "structural_authority": "NONE",
    }
    return {
        "schema": SCHEMA,
        "compiler_version": COMPILER_VERSION,
        "identity": {
            "identity_id": ZERO_IDENTITY_ID,
            "source": "UNIFIEDDB_VERSIONED_OBJECT",
            "task_override_allowed": False,
        },
        "grf": {
            "framework_id": GRF_ID,
            "source": "UNIFIEDDB_VERSIONED_OBJECT",
            "active": True,
            "task_disable_allowed": False,
            "stages": list(GRF_STAGES),
        },
        "authority": dict(AUTHORITY),
        "entity_generation": entity_generation,
        "causal_turn_id": causal_turn_id,
        "task": task,
    }


def compile_workspace_capsule(
    *,
    entity_generation: int,
    causal_turn_id: str,
    task_text: str,
    zero_identity_digest: str,
    grf_digest: str,
    hyperposition_digest: str,
    local_model_digest: str,
    jacobian_lens_digest: str,
    workspace_digest: str,
    selected_workspace_slots: list[str],
    contradiction_state: str,
    provenance_refs: list[str],
    required_zero_mode: str,
) -> dict[str, Any]:
    doc = _base(
        entity_generation=entity_generation,
        causal_turn_id=causal_turn_id,
        task_text=task_text,
    )
    _need(isinstance(selected_workspace_slots, list) and all(isinstance(x, str) and x.strip() for x in selected_workspace_slots),
          "selected_workspace_slots must be nonempty strings")
    _need(len(selected_workspace_slots) == len(set(selected_workspace_slots)), "selected_workspace_slots duplicate")
    _need(isinstance(provenance_refs, list) and all(isinstance(x, str) and x.strip() for x in provenance_refs),
          "provenance_refs must be nonempty strings")
    _need(len(provenance_refs) == len(set(provenance_refs)), "provenance_refs duplicate")
    doc.update({
        "mode": "WORKSPACE_BOUND",
        "zero_identity_digest": _digest(zero_identity_digest, "zero_identity_digest"),
        "grf_digest": _digest(grf_digest, "grf_digest"),
        "hyperposition_digest": _digest(hyperposition_digest, "hyperposition_digest"),
        "local_model_digest": _digest(local_model_digest, "local_model_digest"),
        "jacobian_lens_digest": _digest(jacobian_lens_digest, "jacobian_lens_digest"),
        "workspace_digest": _digest(workspace_digest, "workspace_digest"),
        "selected_workspace_slots": selected_workspace_slots,
        "contradiction_state": _nonempty(contradiction_state, "contradiction_state"),
        "provenance_refs": provenance_refs,
        "required_zero_mode": _nonempty(required_zero_mode, "required_zero_mode"),
        "abstention_reason": None,
    })
    doc["capsule_digest"] = sha256_obj(doc)
    validate(doc)
    return doc


def compile_abstention_capsule(
    *,
    entity_generation: int,
    causal_turn_id: str,
    task_text: str,
    reason: str,
    zero_identity_digest: str | None = None,
    grf_digest: str | None = None,
    provenance_refs: list[str] | None = None,
) -> dict[str, Any]:
    doc = _base(
        entity_generation=entity_generation,
        causal_turn_id=causal_turn_id,
        task_text=task_text,
    )
    _need(reason in UNAVAILABLE_REASONS, "unsupported abstention reason")
    refs = [] if provenance_refs is None else provenance_refs
    _need(isinstance(refs, list) and all(isinstance(x, str) and x.strip() for x in refs), "provenance_refs invalid")
    _need(len(refs) == len(set(refs)), "provenance_refs duplicate")
    doc.update({
        "mode": "ABSTAINED",
        "zero_identity_digest": None if zero_identity_digest is None else _digest(zero_identity_digest, "zero_identity_digest"),
        "grf_digest": None if grf_digest is None else _digest(grf_digest, "grf_digest"),
        "hyperposition_digest": None,
        "local_model_digest": None,
        "jacobian_lens_digest": None,
        "workspace_digest": None,
        "selected_workspace_slots": [],
        "contradiction_state": "UNKNOWN",
        "provenance_refs": refs,
        "required_zero_mode": "ABSTAIN",
        "abstention_reason": reason,
    })
    doc["capsule_digest"] = sha256_obj(doc)
    validate(doc)
    return doc


def validate(doc: dict[str, Any]) -> dict[str, Any]:
    _need(isinstance(doc, dict), "capsule must be object")
    _need(set(doc) == CAPSULE_KEYS, "capsule field set mismatch")
    _need(doc.get("schema") == SCHEMA, "schema mismatch")
    _need(doc.get("compiler_version") == COMPILER_VERSION, "compiler_version mismatch")
    _need(doc.get("identity") == {
        "identity_id": ZERO_IDENTITY_ID,
        "source": "UNIFIEDDB_VERSIONED_OBJECT",
        "task_override_allowed": False,
    }, "ZERO identity contract mismatch")
    _need(doc.get("grf") == {
        "framework_id": GRF_ID,
        "source": "UNIFIEDDB_VERSIONED_OBJECT",
        "active": True,
        "task_disable_allowed": False,
        "stages": list(GRF_STAGES),
    }, "GRF contract mismatch")
    _need(doc.get("authority") == AUTHORITY, "authority contract mismatch")
    _need(isinstance(doc.get("entity_generation"), int) and not isinstance(doc.get("entity_generation"), bool) and doc["entity_generation"] >= 0,
          "entity_generation invalid")
    _nonempty(doc.get("causal_turn_id"), "causal_turn_id")
    task = doc.get("task")
    _need(isinstance(task, dict), "task missing")
    _need(set(task) == TASK_KEYS, "task field set mismatch")
    _need(task.get("format") == "OPAQUE_USER_TASK_TEXT/v1", "task format mismatch")
    _need(task.get("structural_authority") == "NONE", "task structural authority forbidden")
    _need(isinstance(task.get("text"), str), "task text invalid")
    _need(task.get("sha256") == hashlib.sha256(task["text"].encode("utf-8")).hexdigest(), "task digest mismatch")

    mode = doc.get("mode")
    _need(mode in {"WORKSPACE_BOUND", "ABSTAINED"}, "mode invalid")
    if mode == "WORKSPACE_BOUND":
        for name in ("zero_identity_digest", "grf_digest", "hyperposition_digest", "local_model_digest",
                     "jacobian_lens_digest", "workspace_digest"):
            _digest(doc.get(name), name)
        _need(doc.get("abstention_reason") is None, "workspace-bound capsule cannot abstain")
        _need(isinstance(doc.get("selected_workspace_slots"), list) and
              all(isinstance(x, str) and x.strip() for x in doc["selected_workspace_slots"]),
              "selected_workspace_slots invalid")
        _need(len(doc["selected_workspace_slots"]) == len(set(doc["selected_workspace_slots"])),
              "selected_workspace_slots duplicate")
    else:
        _need(doc.get("abstention_reason") in UNAVAILABLE_REASONS, "abstention reason invalid")
        for name in ("hyperposition_digest", "local_model_digest", "jacobian_lens_digest", "workspace_digest"):
            _need(doc.get(name) is None, f"{name} must be null while abstained")
        _need(doc.get("selected_workspace_slots") == [], "abstained capsule cannot carry workspace slots")
        _need(doc.get("required_zero_mode") == "ABSTAIN", "abstained capsule must require ABSTAIN")

    refs = doc.get("provenance_refs")
    _need(isinstance(refs, list) and all(isinstance(x, str) and x.strip() for x in refs), "provenance_refs invalid")
    _need(len(refs) == len(set(refs)), "provenance_refs duplicate")
    digest = doc.get("capsule_digest")
    _need(isinstance(digest, str) and _HEX64.fullmatch(digest), "capsule_digest invalid")
    unsigned = dict(doc)
    unsigned.pop("capsule_digest", None)
    _need(digest == sha256_obj(unsigned), "capsule_digest mismatch")
    return {
        "ok": True,
        "schema": SCHEMA,
        "mode": mode,
        "capsule_digest": digest,
        "runtime_credit": "ZERO",
        "truth_credit": "ZERO",
        "effect_credit": "ZERO",
    }
