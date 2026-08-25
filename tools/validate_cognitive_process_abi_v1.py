#!/usr/bin/env python3
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"
EXPECTED = {f"AZP{i:02d}" for i in range(1, 21)}
REQUIRED_PACKETS = {
    "CognitiveWorkUnit", "RouteLease", "CognitiveResult", "WorkspacePacket",
    "StatePlacementDecision", "DbWriteProposal", "ClaudeCodeBridgePacket",
    "JSpaceMeasurement", "EffectProposal", "EffectJournalReceipt"
}
ENTRY_DIGEST_PACKETS = REQUIRED_PACKETS - {"RouteLease"}
CLAUDE_BINDINGS = {"AZP06", "AZP08", "AZP13", "AZP20"}


def validate(doc):
    errors = []
    if doc.get("schema") != "COGNITIVE_PROCESS_ABI/v1":
        errors.append("wrong schema")
    authority = doc.get("authority", {})
    if authority.get("grid_law") != "VARIABLE_N_RUNTIME_PARAMETER_GRID10_ONLY_A_BENCHMARK_CONFIGURATION":
        errors.append("grid law is not variable-N")
    if authority.get("typed_entry_event_identity_schema") != "ENTITYOS_HCU_ENTRY_EVENT_IDENTITY/v3":
        errors.append("Typed Entry event identity schema mismatch")
    if authority.get("typed_entry_admission_identity_schema") != "ENTITYOS_HCU_ENTRY_ADMISSION_IDENTITY/v3":
        errors.append("Typed Entry admission identity schema mismatch")

    packet_defs = doc.get("packet_types", {})
    packets = set(packet_defs)
    if packets != REQUIRED_PACKETS:
        errors.append(f"packet set mismatch: {sorted(packets ^ REQUIRED_PACKETS)}")
    for packet_name in ENTRY_DIGEST_PACKETS & packets:
        required = set(packet_defs.get(packet_name, {}).get("required", []))
        if "entry_event_sha256" not in required:
            errors.append(f"{packet_name} missing entry_event_sha256")
        if packet_name != "StatePlacementDecision" and "entry_admission_sha256" not in required:
            errors.append(f"{packet_name} missing entry_admission_sha256")
        forbidden = {"causal_event_id", "admission_id"} & required
        if forbidden:
            errors.append(f"{packet_name} mints generic identity alias: {sorted(forbidden)}")

    placement = packet_defs.get("StatePlacementDecision", {})
    if placement.get("selected_plane") != ["DATABASE_S0", "WORKSPACE_S1", "LOCAL_EPHEMERAL_S2"]:
        errors.append("state placement planes mismatch")
    placement_rules = " ".join(placement.get("rules", [])).lower()
    for needle in ("not a database write", "cannot self-promote", "canonical fact"):
        if needle not in placement_rules:
            errors.append(f"state placement missing rule: {needle}")

    bridge = packet_defs.get("ClaudeCodeBridgePacket", {})
    if bridge.get("interface_class") != ["TEXT_TOOL_SESSION", "DECLARED_DEEPER_INTERFACE"]:
        errors.append("Claude bridge interface classes mismatch")
    bridge_rules = " ".join(bridge.get("rules", [])).lower()
    for needle in ("strong model/tool/code partner", "conservative default", "causal evidence", "cannot be broadened"):
        if needle not in bridge_rules:
            errors.append(f"Claude bridge missing rule: {needle}")

    effect_receipt = packet_defs.get("EffectJournalReceipt", {})
    if effect_receipt.get("outcome_status") != ["VERIFIED_SUCCESS", "VERIFIED_FAILURE", "UNKNOWN"]:
        errors.append("EffectJournalReceipt outcome status mismatch")
    effect_rules = " ".join(effect_receipt.get("rules", [])).lower()
    for needle in ("deterministic effectgate/effectjournal", "cannot fabricate", "never authorizes blind replay"):
        if needle not in effect_rules:
            errors.append(f"EffectJournalReceipt missing rule: {needle}")

    bindings = doc.get("process_binding", {})
    if set(bindings) != EXPECTED:
        errors.append(f"process binding mismatch: {sorted(set(bindings) ^ EXPECTED)}")
    for process_id, names in bindings.items():
        unknown = set(names) - packets
        if unknown:
            errors.append(f"{process_id} references unknown packet(s): {sorted(unknown)}")

    actual_claude = {pid for pid, names in bindings.items() if "ClaudeCodeBridgePacket" in names}
    if not CLAUDE_BINDINGS <= actual_claude:
        errors.append(f"Claude bridge missing semantic bindings: {sorted(CLAUDE_BINDINGS - actual_claude)}")
    if bindings.get("AZP12") != ["EffectProposal", "EffectJournalReceipt"]:
        errors.append("AZP12 must remain deterministic effect boundary, not CognitiveResult")
    for pid in ("AZP14", "AZP18", "AZP20"):
        if "StatePlacementDecision" not in bindings.get(pid, []):
            errors.append(f"{pid} missing StatePlacementDecision")

    rules = " ".join(doc.get("cross_process_invariants", [])).lower()
    for needle in (
        "independent of module identity and grid size",
        "entry_event_sha256 and entry_admission_sha256",
        "durable-data-vs-simulation",
        "never mint canonical truth",
        "effectgate/effectjournal",
        "restart/rejoin",
        "not acceptance-only",
        "prompt/session presence alone",
        "not posthoc retuned",
    ):
        if needle not in rules:
            errors.append(f"missing invariant: {needle}")

    disc = doc.get("first_executable_discriminator", {})
    steps = " ".join(disc.get("steps", [])).lower()
    for needle in (
        "typed entry",
        "different azp",
        "stateplacementdecision",
        "restart",
        "azp06",
        "claude_code_to_grid",
        "mismatched-entry-digest",
        "self-granted-capability",
        "direct-s0-write",
        "deeper-interface-without-evidence",
    ):
        if needle not in steps:
            errors.append(f"discriminator missing negative/coverage: {needle}")

    credit = doc.get("credit", {})
    for key in ("whole_entityos_hcu", "full_hcu", "jspace_model_runtime", "training"):
        if credit.get(key) != 0:
            errors.append(f"inflated credit: {key}")
    if credit.get("whole_product_pass") is not False:
        errors.append("whole_product_pass must remain false")
    return errors


def main():
    doc = json.loads(PATH.read_text())
    errors = validate(doc)
    if errors:
        for e in errors:
            print("FAIL", e)
        return 1
    print("PASS COGNITIVE_PROCESS_ABI/v1 source contract")
    return 0


if __name__ == "__main__":
    sys.exit(main())
