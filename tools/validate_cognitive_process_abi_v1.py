#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ABI_PATH = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"
EXPECTED_PROCESSES = {f"ZECP{i:02d}" for i in range(1, 21)}
REQUIRED_PACKETS = {
    "COGNITIVE_WORK_PACKET/v1", "COGNITIVE_RESULT_PACKET/v1", "DB_STATE_REF/v1",
    "STATE_PLACEMENT_DECISION/v1", "DB_WRITE_PROPOSAL/v1", "WORKSPACE_REENTRY/v1",
    "CLAUDE_CODE_BRIDGE_PACKET/v1", "GRID_EXECUTOR_BINDING/v1", "JSPACE_MEASUREMENT/v1",
    "EFFECT_PROPOSAL/v1", "EFFECT_JOURNAL_RECEIPT/v1",
}
ENTRY_BOUND_PACKETS = REQUIRED_PACKETS - {"DB_STATE_REF/v1", "GRID_EXECUTOR_BINDING/v1"}


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    if doc.get("schema") != "COGNITIVE_PROCESS_ABI/v1":
        errors.append("wrong schema")

    authority = doc.get("authority", {})
    if authority.get("typed_entry_event_identity_schema") != "ENTITYOS_HCU_ENTRY_EVENT_IDENTITY/v3":
        errors.append("Typed Entry event identity schema mismatch")
    if authority.get("typed_entry_admission_identity_schema") != "ENTITYOS_HCU_ENTRY_ADMISSION_IDENTITY/v3":
        errors.append("Typed Entry admission identity schema mismatch")
    if "NO_PARALLEL_CAUSAL_IDENTITY" not in authority.get("identity_binding_law", ""):
        errors.append("parallel causal identity is not explicitly forbidden")

    packets = doc.get("packet_types", {})
    if set(packets) != REQUIRED_PACKETS:
        errors.append(f"packet set mismatch: {sorted(set(packets) ^ REQUIRED_PACKETS)}")

    for name in ENTRY_BOUND_PACKETS & set(packets):
        required = set(packets[name].get("required", []))
        if "entry_event_sha256" not in required:
            errors.append(f"{name} missing entry_event_sha256")
        if name != "STATE_PLACEMENT_DECISION/v1" and "entry_admission_sha256" not in required:
            errors.append(f"{name} missing entry_admission_sha256")

    placement = packets.get("STATE_PLACEMENT_DECISION/v1", {})
    if placement.get("allowed_selected_plane") != ["DATABASE_S0", "WORKSPACE_S1", "LOCAL_EPHEMERAL_S2"]:
        errors.append("state placement planes mismatch")
    placement_rules = " ".join(placement.get("rules", {}).values()).lower()
    for needle in ("cannot mutate s0", "cannot self-promote", "candidate/unknown"):
        if needle not in placement_rules:
            errors.append(f"state placement missing rule: {needle}")

    db_write = packets.get("DB_WRITE_PROPOSAL/v1", {})
    db_rules = " ".join(db_write.get("rules", {}).values()).lower()
    if "state_placement_decision" not in db_rules:
        errors.append("DB write proposal is not placement-bound")
    if "deterministic canonical db admission" not in db_rules:
        errors.append("DB deterministic admission boundary missing")

    bridge = packets.get("CLAUDE_CODE_BRIDGE_PACKET/v1", {})
    bridge_rules = " ".join(bridge.get("rules", {}).values()).lower()
    for needle in ("exact exposed activation/hook interface", "cannot broaden", "zecp13", "zecp14"):
        if needle not in bridge_rules:
            errors.append(f"Claude bridge missing rule: {needle}")

    effect_receipt = packets.get("EFFECT_JOURNAL_RECEIPT/v1", {})
    if effect_receipt.get("allowed_outcome_status") != ["VERIFIED_SUCCESS", "VERIFIED_FAILURE", "UNKNOWN"]:
        errors.append("effect outcome status mismatch")
    effect_rules = " ".join(effect_receipt.get("rules", {}).values()).lower()
    for needle in ("deterministic zecp17", "cannot fabricate", "never authorizes blind replay"):
        if needle not in effect_rules:
            errors.append(f"effect receipt missing rule: {needle}")

    bindings = doc.get("process_bindings", {})
    if set(bindings) != EXPECTED_PROCESSES:
        errors.append(f"process binding mismatch: {sorted(set(bindings) ^ EXPECTED_PROCESSES)}")
    for pid, names in bindings.items():
        unknown = set(names) - set(packets)
        if unknown:
            errors.append(f"{pid} references unknown packet(s): {sorted(unknown)}")
    if "CLAUDE_CODE_BRIDGE_PACKET/v1" not in bindings.get("ZECP13", []):
        errors.append("ZECP13 missing Claude bridge")
    if "CLAUDE_CODE_BRIDGE_PACKET/v1" not in bindings.get("ZECP14", []):
        errors.append("ZECP14 missing Claude bridge")
    if bindings.get("ZECP17") != ["EFFECT_PROPOSAL/v1", "EFFECT_JOURNAL_RECEIPT/v1"]:
        errors.append("ZECP17 must remain deterministic effect boundary")
    if "STATE_PLACEMENT_DECISION/v1" not in bindings.get("ZECP15", []):
        errors.append("ZECP15 missing state placement")

    invariants = " ".join(doc.get("cross_process_invariants", [])).lower()
    for needle in (
        "runtime grid size n", "entry_event_sha256 and entry_admission_sha256",
        "durable-data-vs-simulation", "never mint canonical truth", "cannot be broadened",
        "not acceptance-only", "text/session presence alone", "only deterministic zecp17",
        "never blindly replayed", "not posthoc retuned",
    ):
        if needle not in invariants:
            errors.append(f"missing invariant: {needle}")

    disc = " ".join(doc.get("first_executable_discriminator", {}).get("steps", [])).lower()
    for needle in (
        "typed entry", "two distinct zecp", "database_s0", "restart/rejoin",
        "zecp13", "zecp14", "mismatched-entry-digest", "self-granted-capability",
        "direct-s0-write", "fabricated-effect-receipt", "deeper-interface-without-evidence",
    ):
        if needle not in disc:
            errors.append(f"discriminator missing coverage: {needle}")

    credit = doc.get("credit_boundary", {})
    for key in (
        "abi_component_runtime", "variable_grid_runtime", "claude_code_bridge_runtime",
        "global_jspace_causal_runtime", "end_to_end_zero_equivalence",
        "whole_entityos_hcu_runtime", "training",
    ):
        if credit.get(key) != 0:
            errors.append(f"inflated credit: {key}")
    return errors


def main() -> int:
    doc = json.loads(ABI_PATH.read_text(encoding="utf-8"))
    errors = validate(doc)
    if errors:
        for error in errors:
            print("FAIL", error)
        return 1
    print("PASS COGNITIVE_PROCESS_ABI/v1 source contract")
    return 0


if __name__ == "__main__":
    sys.exit(main())
