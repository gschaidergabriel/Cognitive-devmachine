#!/usr/bin/env python3
"""Build a deterministic current-authority worker envelope for Xeno.

This module deliberately does not use the prose all-worker directive as current
authority. It cross-binds the canonical Supervisor Inbox, its exact steering target,
and the current typed FREE provider admission object. Older worker directives remain
compatibility/provenance surfaces and cannot override a newer supervisor epoch.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INBOX_PATH = Path("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
PROVIDER_ADMISSION_PATH = Path("research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json")

PROTOCOL_BEGIN = "[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"
PROTOCOL_END = "[/MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"
LIVE_MARKER = "[ENTITYOS/HCU LIVE AUTHORITY ENVELOPE]"
SCHEMA = "ENTITYOS_HCU_LIVE_WORKER_AUTHORITY/v1"


class AuthorityProtocolError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AuthorityProtocolError(f"JSON_READ_FAIL:{path}:{type(exc).__name__}") from exc
    if not isinstance(obj, dict):
        raise AuthorityProtocolError(f"JSON_NOT_OBJECT:{path}")
    return obj


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_path(root: Path, pointer: str, *, code: str) -> Path:
    if not pointer:
        raise AuthorityProtocolError(f"{code}_MISSING")
    root = root.resolve()
    path = (root / pointer).resolve()
    if path != root and root not in path.parents:
        raise AuthorityProtocolError(f"{code}_ESCAPES_REPO")
    if not path.is_file():
        raise AuthorityProtocolError(f"{code}_TARGET_MISSING")
    return path


def resolve_current_authority(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    inbox_path = _repo_path(root, str(INBOX_PATH), code="INBOX")
    admission_path = _repo_path(root, str(PROVIDER_ADMISSION_PATH), code="PROVIDER_ADMISSION")
    inbox = _load_json(inbox_path)

    steering_pointer = inbox.get("steering")
    if not isinstance(steering_pointer, str):
        raise AuthorityProtocolError("STEERING_POINTER_MISSING")
    steering_path = _repo_path(root, steering_pointer, code="STEERING")
    steering = _load_json(steering_path)
    admission = _load_json(admission_path)

    epoch = str(inbox.get("schema_version"))
    if epoch in {"", "None"}:
        raise AuthorityProtocolError("INBOX_EPOCH_MISSING")
    if str(steering.get("schema_version")) != epoch:
        raise AuthorityProtocolError("STEERING_EPOCH_MISMATCH")
    if str(admission.get("authority_epoch")) != epoch:
        raise AuthorityProtocolError("PROVIDER_ADMISSION_EPOCH_MISMATCH")

    for obj, prefix in ((inbox, "INBOX"), (steering, "STEERING")):
        if obj.get("active_program") != "ENTITYOS_HCU":
            raise AuthorityProtocolError(f"{prefix}_PROGRAM_MISMATCH")
        if obj.get("product") != "EntityOS":
            raise AuthorityProtocolError(f"{prefix}_PRODUCT_MISMATCH")
        if obj.get("integrated_cognition_compute_architecture") != "HCU":
            raise AuthorityProtocolError(f"{prefix}_HCU_MISMATCH")

    if admission.get("mode") != "FREE_ONLY":
        raise AuthorityProtocolError("PROVIDER_ADMISSION_NOT_FREE_ONLY")
    if admission.get("product") != "EntityOS" or admission.get("compute_architecture") != "HCU":
        raise AuthorityProtocolError("PROVIDER_ADMISSION_IDENTITY_MISMATCH")

    free_only = steering.get("free_only") or {}
    if free_only.get("enabled") is not True:
        raise AuthorityProtocolError("STEERING_FREE_ONLY_DISABLED")
    if free_only.get("no_paid_fallback") is not True:
        raise AuthorityProtocolError("STEERING_PAID_FALLBACK_NOT_FORBIDDEN")
    if free_only.get("together_forbidden") is not True:
        raise AuthorityProtocolError("STEERING_TOGETHER_NOT_FORBIDDEN")
    if free_only.get("unknown_or_unlisted_route") != "FAIL_CLOSED":
        raise AuthorityProtocolError("STEERING_UNKNOWN_ROUTE_NOT_FAIL_CLOSED")

    route_gate = admission.get("route_level_gate") or {}
    if route_gate.get("receipt_schema") != "FREE_LANE_EXECUTION_RECEIPT/v1":
        raise AuthorityProtocolError("FREE_LANE_RECEIPT_GATE_MISSING")
    if route_gate.get("unknown_or_unbound_route") != "FAIL_CLOSED":
        raise AuthorityProtocolError("FREE_LANE_UNKNOWN_ROUTE_NOT_FAIL_CLOSED")
    if route_gate.get("paid_fallback_attempt_count") != 0:
        raise AuthorityProtocolError("FREE_LANE_PAID_FALLBACK_NONZERO")

    providers = admission.get("providers")
    if not isinstance(providers, dict) or not providers:
        raise AuthorityProtocolError("PROVIDER_SET_MISSING")

    return {
        "schema": SCHEMA,
        "epoch": epoch,
        "inbox_path": str(inbox_path.relative_to(root)),
        "steering_path": str(steering_path.relative_to(root)),
        "provider_admission_path": str(admission_path.relative_to(root)),
        "inbox_sha256": _sha256(inbox_path),
        "steering_sha256": _sha256(steering_path),
        "provider_admission_sha256": _sha256(admission_path),
        "provider_names": sorted(str(name) for name in providers),
        "execution_state": admission.get("execution_state"),
        "route_receipt_schema": route_gate.get("receipt_schema"),
    }


def build_protocol(root: Path = ROOT) -> str:
    a = resolve_current_authority(root)
    providers = ",".join(a["provider_names"])
    return f"""{PROTOCOL_BEGIN}
{LIVE_MARKER}
schema={a['schema']}
current_supervisor_epoch={a['epoch']}
inbox={a['inbox_path']} sha256={a['inbox_sha256']}
steering={a['steering_path']} sha256={a['steering_sha256']}
provider_admission={a['provider_admission_path']} sha256={a['provider_admission_sha256']}
product=EntityOS
compute_architecture=HCU
persistent_research_entity=Clay
temporary_worker=ORGAN_NOT_ENTITY
mode=FREE_ONLY
admitted_provider_names={providers}
route_receipt_schema={a['route_receipt_schema']}

CURRENT AUTHORITY LAW
- This live envelope is derived from current machine-readable authority. Older all-worker prose is compatibility/provenance only when it conflicts with this envelope.
- Provider-level FREE admission does not authorize an arbitrary request. Every external autonomous request must pass the current credential+route economic binding immediately before network I/O and emit FREE_LANE_EXECUTION_RECEIPT/v1.
- Unknown/unbound/paid/subscription routes fail closed. Together and paid fallback are forbidden. HTTP success, key presence, a :free label, worker consensus or historical traffic cannot self-admit economic safety.
- Canonical durable state/evidence remains deterministic. Model/HCU/J-Space/workspace outputs are candidate/projection/measurement only. Real effects remain behind EffectGate/EffectJournal.
- Global J-Space/GWT is an empirical model-specific causal hypothesis. Self-report/coherence/consensus cannot mint causal credit.
- Logical GRID10 cells are not resident-model count or physical decode concurrency.
- FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT.

GO TRACKS
A=ENTITYOS_EXECUTABLE_CONVERGENCE
B=HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT
C=GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS

WORKER DISCIPLINE
- Produce one highest-information executable/testable delta when possible; preserve a serious counterhypothesis and falsifier.
- Never invent runtime PASS, provider capability, canonical truth, model causality, training credit, or repository writes.
- No secret plaintext in prompts, source, telemetry or receipts.
{PROTOCOL_END}"""


if __name__ == "__main__":
    print(build_protocol())
