#!/usr/bin/env python3
"""Pure pre-inference Cognitive Fabric admission compositor.

This module owns no turn allocation, truth, durable state, model execution, effects, or
post-turn UCF finalization. It resolves one already-active MiniUnifiedDB cognition turn,
resolves the versioned cognition payload semantics behind that exact boot/turn ancestry,
cross-checks the bounded caller selector, binds routing through the canonical
MINI_INFERENCE_BOUND_ROUTE/v1 capability ancestry, compiles the repository-owned ZERO
workspace capsule + InferencePacket v2, and emits candidate-only pre-inference admission.

Local latent/J-Space modes additionally require their capability evidence to resolve to
that same current-generation MiniUnifiedDB ancestry. A profile-supplied valid-looking
SHA-256 is never enough to grant local activation capability.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ADMISSION_SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
INVOCATION_SCHEMA = "MINI_COGNITIVE_INVOCATION/v1"
SEMANTIC_BINDING_SCHEMA = "MINI_COGNITION_SEMANTIC_BINDING/v1"
CAPABILITY_EVIDENCE_ANCESTRY_SCHEMA = "MINI_BUNDLED_CAPABILITY_EVIDENCE_ANCESTRY/v1"
INVOCATION_FIELDS = {
    "expected_generation",
    "causal_turn_id",
    "task_text",
    "turn_binding_digest",
}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ROOT = Path(__file__).resolve().parents[1]
_ZERO_IMPL = _ROOT / "research_entity" / "global" / "j-space" / "implementations"
_CAPSULE_IMPL = _ZERO_IMPL / "zero_workspace_capsule_v1.py"
_PACKET_IMPL = _ZERO_IMPL / "zero_inference_packet_v2.py"
_REQUIRED_PREPARE_DIGESTS = (
    "turn_binding_digest",
    "boot_binding_digest",
    "workspace_digest",
    "zero_identity_digest",
    "grf_digest",
    "hyperposition_digest",
    "bundled_manifest_digest",
    "local_model_digest",
    "tokenizer_digest",
    "jspace_profile_digest",
    "jacobian_lens_digest",
    "workspace_calibration_digest",
    "boot_source_lock_digest",
    "policy_authority_digest",
)
_SEMANTIC_OBJECT_FIELDS = (
    "zero_identity_digest",
    "grf_digest",
    "hyperposition_digest",
    "bundled_manifest_digest",
    "local_model_digest",
    "tokenizer_digest",
    "jspace_profile_digest",
    "jacobian_lens_digest",
    "workspace_calibration_digest",
    "boot_source_lock_digest",
    "policy_authority_digest",
)
_CAPABILITY_ANCESTRY_FIELDS = (
    "bundled_manifest_digest",
    "local_model_digest",
    "tokenizer_digest",
    "jspace_profile_digest",
    "jacobian_lens_digest",
    "workspace_calibration_digest",
    "boot_source_lock_digest",
    "policy_authority_digest",
)
_LOCAL_JSPACE_MODES = {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"}
_EXTERNAL_JSPACE_MODES = {"COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY"}
_SEMANTIC_AUTHORITY = {
    "durable_state": "MiniUnifiedDB",
    "routing_only": True,
    "candidate_configuration_only": True,
    "direct_truth_authority": False,
    "direct_effect_authority": False,
}


class CognitiveFabricAdmissionError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CognitiveFabricAdmissionError(message)


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CognitiveFabricAdmissionError("NONCANONICAL_JSON") from exc


def _sha256_obj(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _ordered_unique_refs(*groups: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for group in groups:
        _need(type(group) is list, "PROVENANCE_REFS_LIST_REQUIRED")
        for item in group:
            ref = _text(item, "provenance_ref")
            if ref not in seen:
                seen.add(ref)
                out.append(ref)
    _need(bool(out), "PROVENANCE_REQUIRED")
    return out


def _load_module(path: Path, name: str) -> Any:
    _need(path.is_file(), f"CANONICAL_ZERO_MODULE_MISSING:{path.name}")
    spec = importlib.util.spec_from_file_location(name, path)
    _need(spec is not None and spec.loader is not None, f"IMPORT_SPEC_FAILED:{name}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise CognitiveFabricAdmissionError(
            f"IMPORT_EXEC_FAILED:{name}:{type(exc).__name__}:{exc}"
        ) from exc
    return module


def load_default_zero_modules() -> tuple[Any, Any]:
    """Load exactly the canonical ZERO capsule/packet implementations by repo path."""
    capsule = _load_module(_CAPSULE_IMPL, "zero_workspace_capsule_v1")
    previous = sys.modules.get("zero_workspace_capsule_v1")
    sys.modules["zero_workspace_capsule_v1"] = capsule
    try:
        packet = _load_module(_PACKET_IMPL, "zero_inference_packet_v2")
    finally:
        if previous is None:
            sys.modules.pop("zero_workspace_capsule_v1", None)
        else:
            sys.modules["zero_workspace_capsule_v1"] = previous
    _need(getattr(capsule, "SCHEMA", None) == "ZERO_WORKSPACE_CAPSULE/v1", "CAPSULE_V1_REQUIRED")
    _need(getattr(packet, "SCHEMA", None) == "ZERO_INFERENCE_PACKET/v2", "PACKET_V2_REQUIRED")
    return capsule, packet


def _validate_invocation(invocation: Mapping[str, Any], *, entity_generation: int) -> dict[str, Any]:
    _need(isinstance(invocation, Mapping), "COGNITION_INVOCATION_OBJECT_REQUIRED")
    material = dict(invocation)
    _need(set(material) == INVOCATION_FIELDS, "COGNITION_INVOCATION_FIELDS_MISMATCH")
    generation = material.get("expected_generation")
    _need(type(generation) is int and generation >= 0, "COGNITION_INVOCATION_GENERATION_INVALID")
    _need(generation == entity_generation, "COGNITION_INVOCATION_STALE_GENERATION")
    causal_turn_id = _text(material.get("causal_turn_id"), "cognition_invocation.causal_turn_id")
    task_text = material.get("task_text")
    _need(type(task_text) is str, "COGNITION_INVOCATION_TASK_TEXT_REQUIRED")
    turn_binding_digest = _digest(
        material.get("turn_binding_digest"),
        "cognition_invocation.turn_binding_digest",
    )
    return {
        "expected_generation": generation,
        "causal_turn_id": causal_turn_id,
        "task_text": task_text,
        "turn_binding_digest": turn_binding_digest,
    }


def _verify_prompt_compiled_identity(
    prompt: Mapping[str, Any], *, canonical_state_hash: str, packet_hash: str
) -> tuple[str, str]:
    system = _text(prompt.get("system"), "prompt.system")
    user = _text(prompt.get("user"), "prompt.user")
    try:
        decoded = json.loads(user)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CognitiveFabricAdmissionError("PROMPT_USER_JSON_REQUIRED") from exc
    _need(type(decoded) is dict, "PROMPT_USER_OBJECT_REQUIRED")
    _need(
        decoded.get("CANONICAL_STATE_HASH") == canonical_state_hash
        and decoded.get("PACKET_HASH") == packet_hash,
        "PROMPT_COMPILED_IDENTITY_MISMATCH",
    )
    return system, user


def _bind_semantic_bundle(
    semantic_bundle: Mapping[str, Any], prepare: Mapping[str, Any]
) -> dict[str, Any]:
    """Bind unambiguous versioned MiniUnifiedDB payload identities to this exact turn."""
    _need(isinstance(semantic_bundle, Mapping), "COGNITION_SEMANTIC_BUNDLE_REQUIRED")
    _need(semantic_bundle.get("ok") is True, "COGNITION_SEMANTIC_BUNDLE_NOT_OK")
    _need(
        semantic_bundle.get("schema") == "MINIUNIFIEDDB_COGNITION_SEMANTIC_RESOLUTION/v1",
        "COGNITION_SEMANTIC_BUNDLE_SCHEMA_MISMATCH",
    )
    _need(semantic_bundle.get("authority") == _SEMANTIC_AUTHORITY, "COGNITION_SEMANTIC_AUTHORITY_ESCALATION")
    _need(
        semantic_bundle.get("entity_generation") == prepare.get("entity_generation"),
        "COGNITION_SEMANTIC_GENERATION_DRIFT",
    )
    for key, error in (
        ("causal_turn_id", "COGNITION_SEMANTIC_TURN_DRIFT"),
        ("turn_binding_digest", "COGNITION_SEMANTIC_TURN_BINDING_DRIFT"),
        ("boot_binding_digest", "COGNITION_SEMANTIC_BOOT_BINDING_DRIFT"),
        ("workspace_digest", "COGNITION_SEMANTIC_WORKSPACE_DRIFT"),
    ):
        _need(semantic_bundle.get(key) == prepare.get(key), error)

    objects = semantic_bundle.get("objects")
    _need(isinstance(objects, Mapping), "COGNITION_SEMANTIC_OBJECTS_REQUIRED")
    normalized: dict[str, dict[str, Any]] = {}
    provenance_groups: list[list[str]] = []
    for field in _SEMANTIC_OBJECT_FIELDS:
        obj = objects.get(field)
        _need(isinstance(obj, Mapping), f"COGNITION_SEMANTIC_OBJECT_REQUIRED:{field}")
        object_digest = _digest(obj.get("object_digest"), f"{field}.object_digest")
        _need(object_digest == prepare.get(field), f"COGNITION_SEMANTIC_OBJECT_DIGEST_DRIFT:{field}")
        admitted_generation = obj.get("admitted_generation")
        _need(
            type(admitted_generation) is int
            and admitted_generation == prepare.get("entity_generation"),
            f"COGNITION_SEMANTIC_OBJECT_GENERATION_DRIFT:{field}",
        )
        refs = obj.get("provenance_refs")
        _need(type(refs) is list and bool(refs), f"COGNITION_SEMANTIC_PROVENANCE_REQUIRED:{field}")
        provenance_groups.append(list(refs))
        normalized[field] = {
            "object_kind": _text(obj.get("object_kind"), f"{field}.object_kind"),
            "object_version": _text(obj.get("object_version"), f"{field}.object_version"),
            "object_digest": object_digest,
            "payload_digest": _digest(obj.get("payload_digest"), f"{field}.payload_digest"),
            "admission_receipt_digest": _digest(
                obj.get("admission_receipt_digest"),
                f"{field}.admission_receipt_digest",
            ),
            "admitted_generation": admitted_generation,
        }

    semantic_material = {
        "schema": SEMANTIC_BINDING_SCHEMA,
        "entity_generation": prepare["entity_generation"],
        "causal_turn_id": prepare["causal_turn_id"],
        "turn_binding_digest": prepare["turn_binding_digest"],
        "boot_binding_digest": prepare["boot_binding_digest"],
        "workspace_digest": prepare["workspace_digest"],
        "objects": normalized,
    }
    semantic_bundle_digest = _sha256_obj(semantic_material)
    capability_objects = {
        field: normalized[field]
        for field in _CAPABILITY_ANCESTRY_FIELDS
    }
    capability_material = {
        "schema": CAPABILITY_EVIDENCE_ANCESTRY_SCHEMA,
        "entity_generation": prepare["entity_generation"],
        "causal_turn_id": prepare["causal_turn_id"],
        "turn_binding_digest": prepare["turn_binding_digest"],
        "boot_binding_digest": prepare["boot_binding_digest"],
        "workspace_digest": prepare["workspace_digest"],
        "objects": capability_objects,
    }
    capability_ancestry_digest = _sha256_obj(capability_material)
    return {
        "semantic_bundle_digest": semantic_bundle_digest,
        "capability_ancestry_digest": capability_ancestry_digest,
        "object_versions": {field: value["object_version"] for field, value in normalized.items()},
        "object_payload_digests": {field: value["payload_digest"] for field, value in normalized.items()},
        "object_admission_receipt_digests": {
            field: value["admission_receipt_digest"] for field, value in normalized.items()
        },
        "provenance_refs": _ordered_unique_refs(*provenance_groups),
    }


def _validate_capability_evidence(route: Mapping[str, Any], semantic: Mapping[str, Any]) -> str:
    """Require causal current-generation evidence before any local latent admission."""
    mode = _text(route.get("jspace_mode"), "jspace_mode")
    evidence_kind = _text(route.get("capability_evidence_kind"), "capability_evidence_kind")
    receipt_digest = _digest(route.get("capability_receipt_digest"), "capability_receipt_digest")
    ancestry_digest = _digest(
        semantic.get("capability_ancestry_digest"),
        "capability_evidence_ancestry_digest",
    )

    if mode in _LOCAL_JSPACE_MODES:
        if evidence_kind == "BUNDLED_MANIFEST":
            _need(
                receipt_digest == ancestry_digest,
                "CAPABILITY_RECEIPT_NOT_BOUND_TO_CURRENT_MINIUNIFIEDDB_ANCESTRY",
            )
            return "BUNDLED_MANIFEST_CURRENT_ANCESTRY_BOUND"
        if evidence_kind == "RUNTIME_PROBE":
            raise CognitiveFabricAdmissionError("RUNTIME_PROBE_CAPABILITY_EVIDENCE_UNRESOLVED")
        raise CognitiveFabricAdmissionError("LOCAL_JSPACE_CAPABILITY_EVIDENCE_UNSUPPORTED")

    _need(mode in _EXTERNAL_JSPACE_MODES, "JSPACE_MODE_UNSUPPORTED")
    return "LOCAL_CAPABILITY_EVIDENCE_NOT_REQUIRED_FOR_EXTERNAL_MODE"


def build_pre_inference_admission(
    db: Any,
    *,
    entity_generation: int,
    invocation: Mapping[str, Any],
    compiled: Mapping[str, Any],
    prompt: Mapping[str, Any],
    profile: Mapping[str, Any],
    expected_activation_digest: str | None = None,
    origin: str | None = None,
    active_turn_module: Any | None = None,
    cognition_resolver_module: Any | None = None,
    capsule_module: Any | None = None,
    packet_module: Any | None = None,
    capability_module: Any | None = None,
) -> dict[str, Any]:
    """Build one candidate-only admission from exact same-store bound material."""
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    selector = _validate_invocation(invocation, entity_generation=entity_generation)
    selector_digest = _sha256_obj({"schema": INVOCATION_SCHEMA, **selector})

    _need(isinstance(compiled, Mapping), "COMPILED_OBJECT_REQUIRED")
    _need(isinstance(prompt, Mapping), "PROMPT_OBJECT_REQUIRED")
    _need(isinstance(profile, Mapping), "PROFILE_OBJECT_REQUIRED")
    canonical_state_hash = _digest(compiled.get("canonical_state_hash"), "canonical_state_hash")
    packet_hash = _digest(compiled.get("packet_hash"), "packet_hash")
    system, user = _verify_prompt_compiled_identity(
        prompt,
        canonical_state_hash=canonical_state_hash,
        packet_hash=packet_hash,
    )
    if expected_activation_digest is not None:
        expected_activation_digest = _digest(expected_activation_digest, "expected_activation_digest")
    if origin is not None:
        origin = _text(origin, "origin")

    if active_turn_module is None:
        import miniunifieddb_active_turn_v1 as active_turn_module  # type: ignore[no-redef]
    if cognition_resolver_module is None:
        import miniunifieddb_cognition_resolution_v1 as cognition_resolver_module  # type: ignore[no-redef]
    if capability_module is None:
        import mini_inference_capability_binding_v1 as capability_module  # type: ignore[no-redef]
    if capsule_module is None or packet_module is None:
        default_capsule, default_packet = load_default_zero_modules()
        capsule_module = capsule_module or default_capsule
        packet_module = packet_module or default_packet

    prepare = active_turn_module.resolve_active_prepare(
        db,
        entity_generation=entity_generation,
        expected_activation_digest=expected_activation_digest,
    )
    _need(type(prepare) is dict and prepare.get("ok") is True, "ACTIVE_PREPARE_RESOLUTION_FAILED")
    _need(prepare.get("entity_generation") == entity_generation, "STALE_PREPARE_GENERATION")
    causal_turn_id = _text(prepare.get("causal_turn_id"), "causal_turn_id")
    task_text = prepare.get("task_text")
    _need(type(task_text) is str, "TASK_TEXT_REQUIRED")
    expected_task_hash = hashlib.sha256(task_text.encode("utf-8")).hexdigest()
    _need(prepare.get("task_sha256") == expected_task_hash, "TASK_BINDING_MISMATCH")
    for name in _REQUIRED_PREPARE_DIGESTS:
        _digest(prepare.get(name), name)
    activation_digest = _digest(prepare.get("activation_digest"), "activation_digest")

    _need(selector["causal_turn_id"] == causal_turn_id, "COGNITION_INVOCATION_CAUSAL_TURN_MISMATCH")
    _need(selector["task_text"] == task_text, "COGNITION_INVOCATION_TASK_MISMATCH")
    _need(
        selector["turn_binding_digest"] == prepare["turn_binding_digest"],
        "COGNITION_INVOCATION_TURN_BINDING_MISMATCH",
    )
    _need(
        prepare.get("authority")
        == {
            "durable_state": "MiniUnifiedDB",
            "candidate_only": True,
            "direct_truth_authority": False,
            "direct_effect_authority": False,
        },
        "PREPARE_AUTHORITY_ESCALATION",
    )

    semantic_bundle = cognition_resolver_module.resolve_prepare_bundle(
        db,
        entity_generation=entity_generation,
        causal_turn_id=causal_turn_id,
        task_text=task_text,
        expected_turn_binding_digest=prepare["turn_binding_digest"],
    )
    semantic = _bind_semantic_bundle(semantic_bundle, prepare)

    route = capability_module.resolve_bound_route(
        profile,
        prepare,
        expected_generation=entity_generation,
    )
    _need(type(route) is dict and route.get("ok") is True, "BOUND_ROUTE_RESOLUTION_FAILED")
    _need(
        route.get("authority") == "ROUTING_ONLY_BOUND_TO_CANONICAL_PREPARE",
        "CAPABILITY_AUTHORITY_ESCALATION",
    )
    route_digest = _digest(route.get("route_digest"), "capability_route_digest")
    _need(route.get("entity_generation") == entity_generation, "BOUND_ROUTE_GENERATION_DRIFT")
    _need(route.get("causal_turn_id") == causal_turn_id, "BOUND_ROUTE_TURN_DRIFT")
    _need(route.get("turn_binding_digest") == prepare["turn_binding_digest"], "BOUND_ROUTE_BINDING_DRIFT")
    _need(route.get("boot_binding_digest") == prepare["boot_binding_digest"], "BOUND_ROUTE_BOOT_DRIFT")
    _need(route.get("workspace_digest") == prepare["workspace_digest"], "BOUND_ROUTE_WORKSPACE_DRIFT")

    target_engine_class = _text(route.get("target_engine_class"), "target_engine_class")
    ucf_engine_class = _text(route.get("ucf_engine_class"), "ucf_engine_class")
    jspace_mode = _text(route.get("jspace_mode"), "jspace_mode")
    capability_binding_digest = _digest(route.get("capability_binding_digest"), "capability_binding_digest")
    capability_receipt_digest = _digest(route.get("capability_receipt_digest"), "capability_receipt_digest")
    capability_evidence_resolution = _validate_capability_evidence(route, semantic)
    profile_id = _text(route.get("profile_id"), "profile_id")
    profile_hash = _digest(route.get("profile_hash"), "profile_hash")
    inference = profile.get("inference")
    _need(isinstance(inference, Mapping), "PROFILE_INFERENCE_OBJECT_REQUIRED")
    inference_config = json.loads(_canonical_json(dict(inference)))

    refs = _ordered_unique_refs(
        prepare.get("turn_provenance_refs"),
        prepare.get("boot_provenance_refs"),
        prepare.get("activation_provenance_refs"),
        semantic["provenance_refs"],
    )
    capsule = capsule_module.compile_workspace_capsule(
        entity_generation=entity_generation,
        causal_turn_id=causal_turn_id,
        task_text=task_text,
        zero_identity_digest=prepare["zero_identity_digest"],
        grf_digest=prepare["grf_digest"],
        hyperposition_digest=prepare["hyperposition_digest"],
        local_model_digest=prepare["local_model_digest"],
        jacobian_lens_digest=prepare["jacobian_lens_digest"],
        workspace_digest=prepare["workspace_digest"],
        selected_workspace_slots=prepare["selected_workspace_slots"],
        contradiction_state=prepare["contradiction_state"],
        provenance_refs=refs,
        required_zero_mode=prepare["required_zero_mode"],
    )
    _need(type(capsule) is dict and capsule.get("mode") == "WORKSPACE_BOUND", "CAPSULE_NOT_EXECUTABLE")
    capsule_digest = _digest(capsule.get("capsule_digest"), "capsule_digest")

    packet = packet_module.compile_packet(
        capsule,
        target_engine_class=target_engine_class,
        jspace_mode=jspace_mode,
        inference=inference_config,
        system=system,
        user=user,
    )
    _need(type(packet) is dict and packet.get("schema") == "ZERO_INFERENCE_PACKET/v2", "PACKET_V2_REQUIRED")
    inference_packet_digest = _digest(packet.get("packet_digest"), "inference_packet_digest")
    admitted_context_digest = _digest(packet.get("admitted_context_digest"), "admitted_context_digest")

    receipt = {
        "schema": ADMISSION_SCHEMA,
        "generation": entity_generation,
        "causal_turn_id": causal_turn_id,
        "cognition_invocation_digest": selector_digest,
        "canonical_state_hash": canonical_state_hash,
        "packet_hash": packet_hash,
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "activation_digest": activation_digest,
        "turn_binding_digest": prepare["turn_binding_digest"],
        "boot_binding_digest": prepare["boot_binding_digest"],
        "workspace_capsule_digest": capsule_digest,
        "workspace_digest": prepare["workspace_digest"],
        "zero_identity_digest": prepare["zero_identity_digest"],
        "grf_digest": prepare["grf_digest"],
        "hyperposition_digest": prepare["hyperposition_digest"],
        "bundled_manifest_digest": prepare["bundled_manifest_digest"],
        "local_model_digest": prepare["local_model_digest"],
        "tokenizer_digest": prepare["tokenizer_digest"],
        "jspace_profile_digest": prepare["jspace_profile_digest"],
        "jacobian_lens_digest": prepare["jacobian_lens_digest"],
        "workspace_calibration_digest": prepare["workspace_calibration_digest"],
        "boot_source_lock_digest": prepare["boot_source_lock_digest"],
        "policy_authority_digest": prepare["policy_authority_digest"],
        "cognition_semantic_bundle_digest": semantic["semantic_bundle_digest"],
        "cognition_object_versions": semantic["object_versions"],
        "cognition_payload_digests": semantic["object_payload_digests"],
        "cognition_object_admission_receipt_digests": semantic[
            "object_admission_receipt_digests"
        ],
        "capability_evidence_ancestry_digest": semantic["capability_ancestry_digest"],
        "capability_evidence_resolution": capability_evidence_resolution,
        "capability_route_digest": route_digest,
        "capability_binding_digest": capability_binding_digest,
        "capability_receipt_digest": capability_receipt_digest,
        "capability_evidence_kind": _text(route.get("capability_evidence_kind"), "capability_evidence_kind"),
        "adapter_version": _text(route.get("adapter_version"), "adapter_version"),
        "target_engine_class": target_engine_class,
        "ucf_engine_class": ucf_engine_class,
        "jspace_mode": jspace_mode,
        "inference_packet_digest": inference_packet_digest,
        "admitted_context_digest": admitted_context_digest,
        "origin": origin,
        "provenance_refs": refs,
        "authority": "CANDIDATE_INFERENCE_ONLY",
        "real_effect_executed": False,
    }
    admission_digest = _sha256_obj(receipt)

    return {
        "ok": True,
        "schema": ADMISSION_SCHEMA,
        "generation": entity_generation,
        "canonical_state_hash": canonical_state_hash,
        "packet_hash": packet_hash,
        "cognition_invocation_digest": selector_digest,
        "cognition_semantic_bundle_digest": semantic["semantic_bundle_digest"],
        "capability_evidence_ancestry_digest": semantic["capability_ancestry_digest"],
        "capability_evidence_resolution": capability_evidence_resolution,
        "capability_route_digest": route_digest,
        "capability_binding_digest": capability_binding_digest,
        "capability_receipt_digest": capability_receipt_digest,
        "target_engine_class": target_engine_class,
        "ucf_engine_class": ucf_engine_class,
        "jspace_mode": jspace_mode,
        "inference_packet_digest": inference_packet_digest,
        "cognitive_fabric_receipt_digest": admission_digest,
        "inference": inference_config,
        "system": system,
        "user": user,
        "causal_turn_id": causal_turn_id,
        "activation_digest": activation_digest,
        "turn_binding_digest": prepare["turn_binding_digest"],
        "boot_binding_digest": prepare["boot_binding_digest"],
        "workspace_capsule_digest": capsule_digest,
        "admission_receipt": receipt,
    }


__all__ = [
    "ADMISSION_SCHEMA",
    "INVOCATION_SCHEMA",
    "SEMANTIC_BINDING_SCHEMA",
    "CAPABILITY_EVIDENCE_ANCESTRY_SCHEMA",
    "INVOCATION_FIELDS",
    "CognitiveFabricAdmissionError",
    "build_pre_inference_admission",
    "load_default_zero_modules",
]
