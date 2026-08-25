"""Observable-interface Claude Code workspace/re-entry bridge v1.

No activation-level access is claimed. The bridge binds compact handoff and
return packets so causal re-entry can be measured at the strongest actually
exposed text/tool/session interface.
"""
from __future__ import annotations

from typing import Any, Mapping

from cognitive_process_abi_v1 import CognitiveABIError

HANDOFF_VERSION = "ENTITYOS_HCU_CLAUDE_CODE_HANDOFF/v1"
RETURN_VERSION = "ENTITYOS_HCU_CLAUDE_CODE_RETURN/v1"
REENTRY_VERSION = "ENTITYOS_HCU_GLOBAL_WORKSPACE_REENTRY/v1"

ALLOWED_INTERFACE_MODES = frozenset({"TEXT", "TOOL", "SESSION", "TEXT_TOOL_SESSION"})


def _text(packet: Mapping[str, Any], key: str) -> str:
    value = packet.get(key)
    if not isinstance(value, str) or not value:
        raise CognitiveABIError(f"{key}:REQUIRED_NONEMPTY_TEXT")
    return value


def build_handoff(*, process_instance_id: str, workspace_slice_ref: str,
                  claycode_packet_ref: str, evidence_refs: list[str],
                  interface_mode: str = "TEXT_TOOL_SESSION") -> dict[str, Any]:
    if interface_mode not in ALLOWED_INTERFACE_MODES:
        raise CognitiveABIError("UNPROVEN_CLAUDE_CODE_INTERFACE_MODE")
    if not all(isinstance(x, str) and x for x in evidence_refs):
        raise CognitiveABIError("EVIDENCE_REFS_INVALID")
    return {
        "schema_version": HANDOFF_VERSION,
        "process_instance_id": process_instance_id,
        "workspace_slice_ref": workspace_slice_ref,
        "claycode_packet_ref": claycode_packet_ref,
        "evidence_refs": list(evidence_refs),
        "interface_mode": interface_mode,
        "activation_access_claim": False,
        "canonical_truth_authority": False,
        "effect_authority": False,
    }


def ingest_return(packet: Mapping[str, Any]) -> dict[str, Any]:
    if packet.get("schema_version") != RETURN_VERSION:
        raise CognitiveABIError("CLAUDE_RETURN_SCHEMA_VERSION")
    _text(packet, "process_instance_id")
    _text(packet, "handoff_id")
    _text(packet, "return_id")
    mode = _text(packet, "interface_mode")
    if mode not in ALLOWED_INTERFACE_MODES:
        raise CognitiveABIError("UNPROVEN_CLAUDE_CODE_INTERFACE_MODE")
    if packet.get("activation_access_claim") is True:
        raise CognitiveABIError("UNPROVEN_ACTIVATION_ACCESS_CLAIM")
    evidence_refs = packet.get("evidence_refs", [])
    if not isinstance(evidence_refs, list) or not all(isinstance(x, str) and x for x in evidence_refs):
        raise CognitiveABIError("EVIDENCE_REFS_INVALID")
    return dict(packet)


def build_reentry_probe(*, claude_return: Mapping[str, Any],
                        pre_reentry_state_ref: str,
                        post_reentry_observation_ref: str,
                        downstream_action_ref: str | None,
                        discriminator_ref: str) -> dict[str, Any]:
    checked = ingest_return(claude_return)
    if not pre_reentry_state_ref or not post_reentry_observation_ref or not discriminator_ref:
        raise CognitiveABIError("REENTRY_REF_REQUIRED")
    return {
        "schema_version": REENTRY_VERSION,
        "process_instance_id": checked["process_instance_id"],
        "handoff_id": checked["handoff_id"],
        "return_id": checked["return_id"],
        "interface_mode": checked["interface_mode"],
        "pre_reentry_state_ref": pre_reentry_state_ref,
        "post_reentry_observation_ref": post_reentry_observation_ref,
        "downstream_action_ref": downstream_action_ref,
        "discriminator_ref": discriminator_ref,
        "causal_claim_status": "UNRESOLVED_UNTIL_CONTROLLED_DISCRIMINATOR",
        "global_jspace_claim": "OBSERVABLE_WORKSPACE_BRIDGE_ONLY",
        "canonical_truth_authority": False,
        "effect_authority": False,
    }
