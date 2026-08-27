#!/usr/bin/env python3
"""Compose canonical UCF+boot ancestry with ZERO packet-v2 downstream-context binding.

This validator adds no truth/state/effect authority. It composes the existing canonical
UCF+boot chain with ZERO_WORKSPACE_CAPSULE/v1 and ZERO_INFERENCE_PACKET/v2, and requires
the packet to bind the exact inference/system/user values passed to inference_generate.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_CHAIN = ROOT / "tools" / "validate_ucf_boot_ancestry_chain_v1.py"
CAPSULE_IMPL = ROOT / "research_entity" / "global" / "j-space" / "implementations" / "zero_workspace_capsule_v1.py"
PACKET_IMPL = ROOT / "research_entity" / "global" / "j-space" / "implementations" / "zero_inference_packet_v2.py"


class ZeroChainV2Error(ValueError):
    pass


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ZeroChainV2Error(f"IMPORT_SPEC_FAILED:{name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_zero_bindings(
    cycle: dict[str, Any],
    capsule: dict[str, Any],
    packet: dict[str, Any],
    *,
    downstream_inference: dict[str, Any] | None,
    downstream_system: str | None,
    downstream_user: str | None,
    capsule_module: Any | None = None,
    packet_module: Any | None = None,
) -> list[str]:
    errors: list[str] = []
    try:
        capsule_v1 = capsule_module if capsule_module is not None else _load(CAPSULE_IMPL, "zero_capsule_v1")
        capsule_v1.validate(capsule)
    except Exception as exc:
        return [f"CAPSULE_VALIDATION_FAILED:{type(exc).__name__}:{exc}"]

    try:
        packet_v2 = packet_module if packet_module is not None else _load(PACKET_IMPL, "zero_packet_v2")
        packet_v2.validate(
            packet,
            capsule,
            inference=downstream_inference,
            system=downstream_system,
            user=downstream_user,
            require_context=True,
        )
    except Exception as exc:
        return [f"PACKET_VALIDATION_FAILED:{type(exc).__name__}:{exc}"]

    runtime = cycle.get("runtime") if type(cycle.get("runtime")) is dict else {}
    identity = cycle.get("identity") if type(cycle.get("identity")) is dict else {}
    binding = cycle.get("binding") if type(cycle.get("binding")) is dict else {}
    workspace = cycle.get("workspace") if type(cycle.get("workspace")) is dict else {}
    inference = cycle.get("inference") if type(cycle.get("inference")) is dict else {}
    authority = cycle.get("authority") if type(cycle.get("authority")) is dict else {}

    if binding.get("causal_turn_id") != capsule.get("causal_turn_id"):
        errors.append("ZERO_CAUSAL_TURN_BINDING_MISMATCH")
    if binding.get("zero_workspace_capsule_digest") != capsule.get("capsule_digest"):
        errors.append("ZERO_CAPSULE_DIGEST_BINDING_MISMATCH")
    if runtime.get("generation") != capsule.get("entity_generation"):
        errors.append("ZERO_CAPSULE_GENERATION_MISMATCH")
    if identity.get("zero_identity_digest") != capsule.get("zero_identity_digest"):
        errors.append("ZERO_CAPSULE_IDENTITY_MISMATCH")
    if identity.get("grf_digest") != capsule.get("grf_digest"):
        errors.append("ZERO_CAPSULE_GRF_MISMATCH")
    if inference.get("inference_packet_digest") != packet.get("packet_digest"):
        errors.append("ZERO_INFERENCE_PACKET_DIGEST_MISMATCH")

    if packet.get("target_engine_class") != "NO_MODEL_REQUIRED":
        expected = packet_v2.ENGINE_TO_UCF.get(packet.get("target_engine_class"))
        if inference.get("engine_class") != expected:
            errors.append("ZERO_PACKET_ENGINE_CLASS_MISMATCH")
        if inference.get("jspace_mode") != packet.get("jspace_mode"):
            errors.append("ZERO_PACKET_JSPACE_MODE_MISMATCH")

    if capsule.get("mode") == "WORKSPACE_BOUND":
        if workspace.get("after_digest") != capsule.get("workspace_digest"):
            errors.append("ZERO_WORKSPACE_AFTER_DIGEST_MISMATCH")
    else:
        if inference.get("executed") is not False:
            errors.append("ZERO_ABSTENTION_EXECUTED_INFERENCE")
        if inference.get("candidate_result_digest") is not None:
            errors.append("ZERO_ABSTENTION_CANDIDATE_RESULT")
        if authority.get("validation_decision") != "BLOCKED":
            errors.append("ZERO_ABSTENTION_NOT_BLOCKED")
        if authority.get("canonical_write_committed") is not False:
            errors.append("ZERO_ABSTENTION_CANONICAL_WRITE")
        if authority.get("effect_committed") is not False:
            errors.append("ZERO_ABSTENTION_EFFECT_WRITE")

    return sorted(set(errors))


def validate_chain(
    cycle: dict[str, Any],
    boot_receipt: dict[str, Any],
    boot_manifest: Path,
    boot_source_lock: dict[str, Any],
    capsule: dict[str, Any],
    packet: dict[str, Any],
    *,
    downstream_inference: dict[str, Any] | None,
    downstream_system: str | None,
    downstream_user: str | None,
    base_chain: Any | None = None,
    capsule_module: Any | None = None,
    packet_module: Any | None = None,
) -> list[str]:
    try:
        base = base_chain if base_chain is not None else _load(BASE_CHAIN, "canonical_ucf_boot_chain_v1")
        errors = list(base.validate_chain(cycle, boot_receipt, boot_manifest, boot_source_lock))
    except Exception as exc:
        return [f"BASE_CHAIN_FAILED:{type(exc).__name__}:{exc}"]

    errors.extend(
        validate_zero_bindings(
            cycle,
            capsule,
            packet,
            downstream_inference=downstream_inference,
            downstream_system=downstream_system,
            downstream_user=downstream_user,
            capsule_module=capsule_module,
            packet_module=packet_module,
        )
    )
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cycle", type=Path)
    parser.add_argument("boot_receipt", type=Path)
    parser.add_argument("boot_manifest", type=Path)
    parser.add_argument("boot_source_lock", type=Path)
    parser.add_argument("zero_workspace_capsule", type=Path)
    parser.add_argument("zero_inference_packet_v2", type=Path)
    parser.add_argument("downstream_context", type=Path)
    args = parser.parse_args(argv)

    try:
        cycle = json.loads(args.cycle.read_text(encoding="utf-8"))
        boot = json.loads(args.boot_receipt.read_text(encoding="utf-8"))
        source_lock = json.loads(args.boot_source_lock.read_text(encoding="utf-8"))
        capsule = json.loads(args.zero_workspace_capsule.read_text(encoding="utf-8"))
        packet = json.loads(args.zero_inference_packet_v2.read_text(encoding="utf-8"))
        context = json.loads(args.downstream_context.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [f"READ_ERROR:{type(exc).__name__}"]}, sort_keys=True))
        return 2

    if not all(type(x) is dict for x in (cycle, boot, source_lock, capsule, packet, context)):
        print(json.dumps({"ok": False, "errors": ["TOP_LEVEL_OBJECTS_REQUIRED"]}, sort_keys=True))
        return 2
    if set(context) != {"inference", "system", "user"}:
        print(json.dumps({"ok": False, "errors": ["DOWNSTREAM_CONTEXT_FIELDS_MISMATCH"]}, sort_keys=True))
        return 2
    if context["inference"] is not None and type(context["inference"]) is not dict:
        print(json.dumps({"ok": False, "errors": ["DOWNSTREAM_INFERENCE_OBJECT_OR_NULL_REQUIRED"]}, sort_keys=True))
        return 2
    if context["system"] is not None and type(context["system"]) is not str:
        print(json.dumps({"ok": False, "errors": ["DOWNSTREAM_SYSTEM_TEXT_OR_NULL_REQUIRED"]}, sort_keys=True))
        return 2
    if context["user"] is not None and type(context["user"]) is not str:
        print(json.dumps({"ok": False, "errors": ["DOWNSTREAM_USER_TEXT_OR_NULL_REQUIRED"]}, sort_keys=True))
        return 2

    errors = validate_chain(
        cycle,
        boot,
        args.boot_manifest,
        source_lock,
        capsule,
        packet,
        downstream_inference=context["inference"],
        downstream_system=context["system"],
        downstream_user=context["user"],
    )
    print(json.dumps({"ok": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
