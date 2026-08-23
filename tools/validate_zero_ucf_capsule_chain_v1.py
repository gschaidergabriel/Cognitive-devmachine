#!/usr/bin/env python3
"""Compose canonical UCF+boot ancestry with strict ZERO capsule/packet binding.

This adds no truth/state/effect ledger. It calls the current canonical UCF+boot chain,
then proves that a workspace-bound ZERO cycle consumed the exact fresh
ZERO_WORKSPACE_CAPSULE/v1 through a deterministic ZERO_INFERENCE_PACKET/v1.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_CHAIN = ROOT / "tools" / "validate_ucf_boot_ancestry_chain_v1.py"
JSPACE_IMPL = ROOT / "research_entity" / "global" / "j-space" / "implementations"
if str(JSPACE_IMPL) not in sys.path:
    sys.path.insert(0, str(JSPACE_IMPL))
import zero_workspace_capsule_v1 as capsule_v1
import zero_inference_packet_v1 as packet_v1

class ZeroChainError(ValueError): pass

def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ZeroChainError(f"IMPORT_SPEC_FAILED:{name}")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def validate_zero_bindings(cycle: dict[str, Any], capsule: dict[str, Any], packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try: capsule_v1.validate(capsule)
    except Exception as exc: return [f"CAPSULE_VALIDATION_FAILED:{type(exc).__name__}:{exc}"]
    try: packet_v1.validate(packet, capsule)
    except Exception as exc: return [f"PACKET_VALIDATION_FAILED:{type(exc).__name__}:{exc}"]
    runtime = cycle.get("runtime") if type(cycle.get("runtime")) is dict else {}
    identity = cycle.get("identity") if type(cycle.get("identity")) is dict else {}
    binding = cycle.get("binding") if type(cycle.get("binding")) is dict else {}
    workspace = cycle.get("workspace") if type(cycle.get("workspace")) is dict else {}
    inference = cycle.get("inference") if type(cycle.get("inference")) is dict else {}
    authority = cycle.get("authority") if type(cycle.get("authority")) is dict else {}

    if binding.get("causal_turn_id") != capsule.get("causal_turn_id"): errors.append("ZERO_CAUSAL_TURN_BINDING_MISMATCH")
    if binding.get("zero_workspace_capsule_digest") != capsule.get("capsule_digest"): errors.append("ZERO_CAPSULE_DIGEST_BINDING_MISMATCH")
    if runtime.get("generation") != capsule.get("entity_generation"): errors.append("ZERO_CAPSULE_GENERATION_MISMATCH")
    if identity.get("zero_identity_digest") != capsule.get("zero_identity_digest"): errors.append("ZERO_CAPSULE_IDENTITY_MISMATCH")
    if identity.get("grf_digest") != capsule.get("grf_digest"): errors.append("ZERO_CAPSULE_GRF_MISMATCH")
    if inference.get("inference_packet_digest") != packet.get("packet_digest"): errors.append("ZERO_INFERENCE_PACKET_DIGEST_MISMATCH")

    if packet.get("target_engine_class") != "NO_MODEL_REQUIRED":
        expected = packet_v1.ENGINE_TO_UCF.get(packet.get("target_engine_class"))
        if inference.get("engine_class") != expected: errors.append("ZERO_PACKET_ENGINE_CLASS_MISMATCH")
        if inference.get("jspace_mode") != packet.get("jspace_mode"): errors.append("ZERO_PACKET_JSPACE_MODE_MISMATCH")

    if capsule.get("mode") == "WORKSPACE_BOUND":
        if workspace.get("after_digest") != capsule.get("workspace_digest"): errors.append("ZERO_WORKSPACE_AFTER_DIGEST_MISMATCH")
    else:
        if inference.get("executed") is not False: errors.append("ZERO_ABSTENTION_EXECUTED_INFERENCE")
        if inference.get("candidate_result_digest") is not None: errors.append("ZERO_ABSTENTION_CANDIDATE_RESULT")
        if authority.get("validation_decision") != "BLOCKED": errors.append("ZERO_ABSTENTION_NOT_BLOCKED")
        if authority.get("canonical_write_committed") is not False: errors.append("ZERO_ABSTENTION_CANONICAL_WRITE")
        if authority.get("effect_committed") is not False: errors.append("ZERO_ABSTENTION_EFFECT_WRITE")
    return sorted(set(errors))

def validate_chain(cycle: dict[str, Any], boot_receipt: dict[str, Any], boot_manifest: Path,
                   boot_source_lock: dict[str, Any], capsule: dict[str, Any], packet: dict[str, Any],
                   *, base_chain: Any | None = None) -> list[str]:
    try:
        base = base_chain if base_chain is not None else _load(BASE_CHAIN, "canonical_ucf_boot_chain_v1")
        errors = list(base.validate_chain(cycle, boot_receipt, boot_manifest, boot_source_lock))
    except Exception as exc:
        return [f"BASE_CHAIN_FAILED:{type(exc).__name__}:{exc}"]
    errors.extend(validate_zero_bindings(cycle, capsule, packet))
    return sorted(set(errors))

def main(argv: list[str] | None = None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("cycle",type=Path); p.add_argument("boot_receipt",type=Path); p.add_argument("boot_manifest",type=Path); p.add_argument("boot_source_lock",type=Path); p.add_argument("zero_workspace_capsule",type=Path); p.add_argument("zero_inference_packet",type=Path)
    a=p.parse_args(argv)
    try:
        cycle=json.loads(a.cycle.read_text(encoding='utf-8')); boot=json.loads(a.boot_receipt.read_text(encoding='utf-8')); lock=json.loads(a.boot_source_lock.read_text(encoding='utf-8')); capsule=json.loads(a.zero_workspace_capsule.read_text(encoding='utf-8')); packet=json.loads(a.zero_inference_packet.read_text(encoding='utf-8'))
    except (OSError,UnicodeError,json.JSONDecodeError) as exc:
        print(json.dumps({'ok':False,'errors':[f'READ_ERROR:{type(exc).__name__}']},sort_keys=True)); return 2
    if not all(type(x) is dict for x in (cycle,boot,lock,capsule,packet)):
        print(json.dumps({'ok':False,'errors':['TOP_LEVEL_OBJECTS_REQUIRED']},sort_keys=True)); return 2
    errors=validate_chain(cycle,boot,a.boot_manifest,lock,capsule,packet)
    print(json.dumps({'ok':not errors,'errors':errors},sort_keys=True)); return 0 if not errors else 2
if __name__=='__main__': raise SystemExit(main())
