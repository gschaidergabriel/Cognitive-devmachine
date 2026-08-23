#!/usr/bin/env python3
"""Deterministic Mini Entity pipeline task/workspace preparation.

This module closes only the source-side material gap before Cognitive Fabric admission.
It does not create truth, model, J-Space/GWT measurement, effect, or second durable-state
authority.  A text-only baseline workspace is compiled from exact already-admitted
pipeline identities/evidence references, then may be bound through the existing
MiniUnifiedDB cognition store + MINI_ENTITY_CAUSAL_TURN_ID/v1 path.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

TASK_SCHEMA = "MINI_ENTITY_PIPELINE_TASK/v1"
WORKSPACE_SCHEMA = "MINI_ENTITY_TEXT_WORKSPACE/v1"
REQUIRED_ZERO_MODE = "TEXT_ONLY_BASELINE"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class PipelineTurnWorkspaceError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise PipelineTurnWorkspaceError(message)


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _refs(value: Any, name: str) -> list[str]:
    _need(type(value) is list, f"{name}:LIST_REQUIRED")
    refs = [_text(item, name) for item in value]
    _need(len(refs) == len(set(refs)), f"{name}:DUPLICATE")
    return refs


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PipelineTurnWorkspaceError("NONCANONICAL_JSON") from exc


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compile_pipeline_task(
    *,
    entity_generation: int,
    profile_id: str,
    profile_hash: str,
    canonical_state_hash: str,
    packet_hash: str,
) -> str:
    """Compile a deterministic causal operation text, never a model-authored task.

    The task is a versioned operational identity for "process this exact active-profile
    packet at this generation".  It intentionally contains no prompt prose and grants no
    structural or semantic truth authority.
    """
    _need(
        type(entity_generation) is int and not isinstance(entity_generation, bool) and entity_generation >= 0,
        "GENERATION_INVALID",
    )
    doc = {
        "schema": TASK_SCHEMA,
        "entity_generation": entity_generation,
        "profile_id": _text(profile_id, "profile_id"),
        "profile_hash": _digest(profile_hash, "profile_hash"),
        "canonical_state_hash": _digest(canonical_state_hash, "canonical_state_hash"),
        "packet_hash": _digest(packet_hash, "packet_hash"),
        "authority": {
            "structural_authority": "NONE",
            "semantic_truth_authority": False,
            "direct_effect_authority": False,
        },
    }
    return canonical_json(doc)


def compile_text_workspace(
    *,
    entity_generation: int,
    task_text: str,
    canonical_state_hash: str,
    packet_hash: str,
    allowed_evidence_refs: list[str],
    max_slots: int = 16,
) -> dict[str, Any]:
    """Build a bounded deterministic text-only baseline workspace.

    Selection is accessibility/routing only: it chooses from refs already admitted by the
    pipeline compiler.  It never labels latent/J-Space/GWT values as measured.  Until an
    admitted contradiction signal exists, contradiction_state stays explicit UNKNOWN.
    """
    _need(
        type(entity_generation) is int and not isinstance(entity_generation, bool) and entity_generation >= 0,
        "GENERATION_INVALID",
    )
    _need(type(task_text) is str and bool(task_text), "TASK_TEXT_REQUIRED")
    canonical_state_hash = _digest(canonical_state_hash, "canonical_state_hash")
    packet_hash = _digest(packet_hash, "packet_hash")
    refs = _refs(allowed_evidence_refs, "allowed_evidence_refs")
    _need(type(max_slots) is int and not isinstance(max_slots, bool) and 1 <= max_slots <= 64, "MAX_SLOTS_INVALID")

    selected = sorted(refs)[:max_slots]
    task_sha256 = sha256_text(task_text)
    provenance_refs = [
        f"mini-entity:canonical-state:{canonical_state_hash}",
        f"mini-entity:source-packet:{packet_hash}",
        f"mini-entity:task:{task_sha256}",
    ]
    provenance_refs.extend(f"mini-entity:evidence:{ref}" for ref in selected)
    material = {
        "schema": WORKSPACE_SCHEMA,
        "entity_generation": entity_generation,
        "task_sha256": task_sha256,
        "canonical_state_hash": canonical_state_hash,
        "packet_hash": packet_hash,
        "selected_workspace_slots": selected,
        "contradiction_state": "UNKNOWN",
        "provenance_refs": provenance_refs,
        "required_zero_mode": REQUIRED_ZERO_MODE,
        "measurement_state": {
            "jspace": "UNMEASURED",
            "gwt": "TEXT_ONLY_BASELINE",
            "workspace_selection": "DETERMINISTIC_EVIDENCE_REF_BASELINE",
        },
        "authority": {
            "candidate_only": True,
            "direct_truth_authority": False,
            "direct_state_authority": False,
            "direct_effect_authority": False,
        },
    }
    digest = sha256_text(canonical_json(material))
    return {**material, "workspace_digest": digest}


def prepare_pipeline_turn_material(
    *,
    profile: Mapping[str, Any],
    previous: Mapping[str, Any],
    compiled: Mapping[str, Any],
    max_slots: int = 16,
) -> dict[str, Any]:
    _need(isinstance(profile, Mapping), "PROFILE_OBJECT_REQUIRED")
    _need(isinstance(previous, Mapping), "PREVIOUS_OBJECT_REQUIRED")
    _need(isinstance(compiled, Mapping), "COMPILED_OBJECT_REQUIRED")
    snapshot = profile.get("_runtime_profile_snapshot")
    _need(isinstance(snapshot, Mapping), "PROFILE_SNAPSHOT_REQUIRED")
    generation = previous.get("generation")
    _need(type(generation) is int and not isinstance(generation, bool) and generation >= 0, "GENERATION_INVALID")
    profile_id = _text(profile.get("profile_id"), "profile_id")
    snapshot_profile_id = _text(snapshot.get("profile_id"), "snapshot_profile_id")
    _need(profile_id == snapshot_profile_id, "PROFILE_SNAPSHOT_ID_MISMATCH")
    profile_hash = _digest(snapshot.get("profile_hash"), "profile_hash")
    canonical_state_hash = _digest(compiled.get("canonical_state_hash"), "canonical_state_hash")
    packet_hash = _digest(compiled.get("packet_hash"), "packet_hash")
    refs = _refs(compiled.get("allowed_evidence_refs"), "allowed_evidence_refs")

    task_text = compile_pipeline_task(
        entity_generation=generation,
        profile_id=profile_id,
        profile_hash=profile_hash,
        canonical_state_hash=canonical_state_hash,
        packet_hash=packet_hash,
    )
    workspace = compile_text_workspace(
        entity_generation=generation,
        task_text=task_text,
        canonical_state_hash=canonical_state_hash,
        packet_hash=packet_hash,
        allowed_evidence_refs=refs,
        max_slots=max_slots,
    )
    return {
        "ok": True,
        "task_schema": TASK_SCHEMA,
        "workspace_schema": WORKSPACE_SCHEMA,
        "entity_generation": generation,
        "task_text": task_text,
        "task_sha256": sha256_text(task_text),
        "workspace_digest": workspace["workspace_digest"],
        "selected_workspace_slots": workspace["selected_workspace_slots"],
        "contradiction_state": workspace["contradiction_state"],
        "provenance_refs": workspace["provenance_refs"],
        "required_zero_mode": workspace["required_zero_mode"],
        "workspace": workspace,
        "authority": {
            "durable_state": "MiniUnifiedDB",
            "candidate_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        },
        "runtime_credit": "ZERO",
    }


def resolve_unique_boot_binding_digest(db: Any, *, entity_generation: int) -> str:
    """Resolve exactly one live-generation boot binding and validate it via the one store."""
    _need(
        type(entity_generation) is int and not isinstance(entity_generation, bool) and entity_generation >= 0,
        "GENERATION_INVALID",
    )
    import miniunifieddb_cognition_store_v1 as cognition_store

    rows = db.execute(
        "SELECT binding_digest FROM mini_cognition_boot_bindings WHERE entity_generation=?",
        (entity_generation,),
    ).fetchall()
    _need(len(rows) == 1, "UNIQUE_BOOT_BINDING_REQUIRED")
    digest = _digest(rows[0][0], "boot_binding_digest")
    cognition_store._load_boot(db, digest, entity_generation)  # single-store integrity validator
    return digest


def prepare_and_bind_pipeline_turn(
    db: Any,
    *,
    profile: Mapping[str, Any],
    previous: Mapping[str, Any],
    compiled: Mapping[str, Any],
    max_slots: int = 16,
) -> dict[str, Any]:
    """Compile baseline material and bind it through PR #1267's single causal-turn path."""
    import mini_causal_turn_id_v1 as causal_turn

    material = prepare_pipeline_turn_material(
        profile=profile,
        previous=previous,
        compiled=compiled,
        max_slots=max_slots,
    )
    boot_binding_digest = resolve_unique_boot_binding_digest(
        db, entity_generation=material["entity_generation"]
    )
    bound = causal_turn.bind_derived_turn(
        db,
        entity_generation=material["entity_generation"],
        boot_binding_digest=boot_binding_digest,
        task_text=material["task_text"],
        workspace_digest=material["workspace_digest"],
        selected_workspace_slots=material["selected_workspace_slots"],
        contradiction_state=material["contradiction_state"],
        provenance_refs=material["provenance_refs"],
        required_zero_mode=material["required_zero_mode"],
    )
    return {
        **material,
        "boot_binding_digest": boot_binding_digest,
        "causal_turn_id": bound["causal_turn_id"],
        "turn_binding_digest": bound["binding_digest"],
        "turn_binding_idempotent": bool(bound.get("idempotent", False)),
    }


__all__ = [
    "TASK_SCHEMA",
    "WORKSPACE_SCHEMA",
    "REQUIRED_ZERO_MODE",
    "PipelineTurnWorkspaceError",
    "compile_pipeline_task",
    "compile_text_workspace",
    "prepare_pipeline_turn_material",
    "resolve_unique_boot_binding_digest",
    "prepare_and_bind_pipeline_turn",
]
