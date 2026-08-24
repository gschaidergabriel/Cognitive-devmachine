#!/usr/bin/env python3
"""Build a deterministic live-authority worker envelope for Xeno.

Current worker authority is cross-bound from Supervisor Inbox -> exact steering ->
FREE_PROVIDER_ADMISSION. Older all-worker prose remains compatibility/provenance and
cannot override a newer machine-readable supervisor epoch.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INBOX_REL = Path("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
ADMISSION_REL = Path("research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json")
PROTOCOL_BEGIN = "[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"
PROTOCOL_END = "[/MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"
LIVE_MARKER = "[ENTITYOS/HCU LIVE AUTHORITY ENVELOPE]"
SCHEMA = "ENTITYOS_HCU_LIVE_WORKER_AUTHORITY/v1"


class AuthorityProtocolError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AuthorityProtocolError(f"JSON_READ_FAIL:{path}:{type(exc).__name__}") from exc
    if not isinstance(obj, dict):
        raise AuthorityProtocolError(f"JSON_NOT_OBJECT:{path}")
    return obj


def _safe(root: Path, pointer: str, code: str) -> Path:
    root = root.resolve()
    path = (root / pointer).resolve()
    if path != root and root not in path.parents:
        raise AuthorityProtocolError(f"{code}_ESCAPES_REPO")
    if not path.is_file():
        raise AuthorityProtocolError(f"{code}_MISSING")
    return path


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_current_authority(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    inbox_path = _safe(root, str(INBOX_REL), "INBOX")
    admission_path = _safe(root, str(ADMISSION_REL), "PROVIDER_ADMISSION")
    inbox = _load(inbox_path)
    pointer = inbox.get("steering")
    if not isinstance(pointer, str) or not pointer:
        raise AuthorityProtocolError("STEERING_POINTER_MISSING")
    steering_path = _safe(root, pointer, "STEERING")
    steering = _load(steering_path)
    admission = _load(admission_path)

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

    free_only = steering.get("free_only") or {}
    if free_only.get("enabled") is not True:
        raise AuthorityProtocolError("STEERING_FREE_ONLY_DISABLED")
    if free_only.get("no_paid_fallback") is not True:
        raise AuthorityProtocolError("STEERING_PAID_FALLBACK_NOT_FORBIDDEN")
    if free_only.get("together_forbidden") is not True:
        raise AuthorityProtocolError("STEERING_TOGETHER_NOT_FORBIDDEN")
    if free_only.get("unknown_or_unlisted_route") != "FAIL_CLOSED":
        raise AuthorityProtocolError("STEERING_UNKNOWN_ROUTE_NOT_FAIL_CLOSED")

    if admission.get("schema") != "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION/v1":
        raise AuthorityProtocolError("PROVIDER_ADMISSION_SCHEMA_MISMATCH")
    if admission.get("mode") != "FREE_ONLY":
        raise AuthorityProtocolError("PROVIDER_ADMISSION_NOT_FREE_ONLY")
    if admission.get("product") != "EntityOS" or admission.get("compute_architecture") != "HCU":
        raise AuthorityProtocolError("PROVIDER_ADMISSION_IDENTITY_MISMATCH")

    route = admission.get("route_level_gate") or {}
    if route.get("receipt_schema") != "FREE_LANE_EXECUTION_RECEIPT/v1":
        raise AuthorityProtocolError("FREE_LANE_RECEIPT_GATE_MISSING")
    if route.get("unknown_or_unbound_route") != "FAIL_CLOSED":
        raise AuthorityProtocolError("FREE_LANE_UNKNOWN_ROUTE_NOT_FAIL_CLOSED")
    if route.get("paid_fallback_attempt_count") != 0:
        raise AuthorityProtocolError("FREE_LANE_PAID_FALLBACK_NONZERO")
    implementation = str(route.get("implementation") or "")
    if "tools/free_lane_provenance.py" not in implementation:
        raise AuthorityProtocolError("FREE_LANE_PROVENANCE_IMPLEMENTATION_MISSING")

    providers = admission.get("providers")
    if not isinstance(providers, dict) or not providers:
        raise AuthorityProtocolError("PROVIDER_SET_MISSING")

    return {
        "schema": SCHEMA,
        "epoch": epoch,
        "inbox_path": str(inbox_path.relative_to(root)),
        "steering_path": str(steering_path.relative_to(root)),
        "provider_admission_path": str(admission_path.relative_to(root)),
        "inbox_sha256": _digest(inbox_path),
        "steering_sha256": _digest(steering_path),
        "provider_admission_sha256": _digest(admission_path),
        "providers": sorted(str(k) for k in providers),
        "receipt_schema": route.get("receipt_schema"),
        "route_implementation": implementation,
    }


def build_protocol(root: Path = ROOT) -> str:
    a = resolve_current_authority(root)
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
providers={','.join(a['providers'])}
route_receipt_schema={a['receipt_schema']}

CURRENT AUTHORITY LAW
- This envelope is derived from current machine-readable authority. Older worker-directive prose is compatibility/provenance only where it conflicts.
- Provider-level FREE admission cannot authorize arbitrary traffic. Every autonomous external request must pass the current credential+route economic binding immediately before network I/O and emit FREE_LANE_EXECUTION_RECEIPT/v1.
- Unknown/unbound/paid/subscription routes fail closed. Together and paid fallback are forbidden. Key presence, HTTP success, labels, model consensus and historical traffic cannot self-admit economic safety.
- Canonical state/evidence remains deterministic. HCU/model/J-Space/workspace outputs are candidate/projection/measurement only; real effects remain behind EffectGate/EffectJournal.
- Global J-Space/GWT is model-specific causal research. Self-report/coherence/consensus cannot mint causal credit.
- GRID10 logical cells are not resident model count or physical decode concurrency.
- FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT.

GO TRACKS
A=ENTITYOS_EXECUTABLE_CONVERGENCE
B=HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT
C=GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS

WORKER DISCIPLINE
- Produce one highest-information executable/testable delta when possible; preserve a serious counterhypothesis and falsifier.
- Never invent runtime PASS, provider capability, canonical truth, model causality, training credit, or repository writes.
- Never place plaintext secrets in prompts, source, telemetry or receipts.
{PROTOCOL_END}"""


if __name__ == "__main__":
    print(build_protocol())
