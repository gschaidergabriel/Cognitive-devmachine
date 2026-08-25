#!/usr/bin/env python3
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "research_entity/global/DB_VS_SIMULATION_BOUNDARY_v1.json"

EXPECTED_CLASSES = {"S0", "S1", "S2"}
REQUIRED_TRANSITIONS = {
    "S0_to_S1", "S1_to_S0", "S2_to_S1", "S2_to_S0",
    "S1_to_effect", "S2_to_effect", "ClaudeCode_to_S1",
    "ClaudeCode_to_S0", "JSpace_to_S0",
}
REQUIRED_NEGATIVES = {
    "MODEL_OUTPUT_DIRECT_DB_WRITE",
    "CLAUDE_CODE_DIRECT_CANONICAL_WRITE",
    "MAJORITY_OR_RECURRENCE_TO_TRUTH",
    "HIDDEN_STATE_AS_CANONICAL_FACT",
    "REGENERATE_DURABLE_ID_FROM_MODEL",
    "CANONICAL_FACT_ONLY_IN_MODEL_MEMORY",
    "S1_CACHE_USED_AS_RECOVERY_AUTHORITY",
    "STALE_GENERATION_WRITE_PROPOSAL_ACCEPTED",
    "EFFECT_EXECUTED_WITHOUT_EFFECTGATE_JOURNAL",
    "UNKNOWN_NORMALIZED_TO_FALSE",
}
REQUIRED_PACKETS = {
    "DbWriteProposal", "CognitiveResult", "WorkspacePacket",
    "ClaudeCodeBridgePacket", "EffectProposal", "JSpaceMeasurement",
}


def validate(doc):
    errors = []
    if doc.get("schema") != "DB_VS_SIMULATION_BOUNDARY/v1":
        errors.append("wrong schema")
    if doc.get("status") != "CURRENT_OWNER_ALIGNED_SOURCE_CONTRACT_NOT_RUNTIME_CREDIT":
        errors.append("status must deny runtime credit")
    authority = doc.get("authority", {})
    if authority.get("owner_rule") != "SIMULATE_COGNITION_STORE_DURABLE_DATA":
        errors.append("owner rule drift")
    if authority.get("grid_law") != "VARIABLE_N_RUNTIME_PARAMETER":
        errors.append("grid law is not variable-N")
    if authority.get("abi_dependency_schema") != "COGNITIVE_PROCESS_ABI/v1":
        errors.append("canonical ABI dependency schema missing")
    blob = authority.get("abi_dependency_blob_sha", "")
    if not (isinstance(blob, str) and len(blob) == 40 and all(c in "0123456789abcdef" for c in blob)):
        errors.append("canonical ABI dependency blob sha missing")

    classes = doc.get("state_classes", {})
    if set(classes) != EXPECTED_CLASSES:
        errors.append("state class mismatch")
    if classes.get("S0", {}).get("authority") != "DETERMINISTIC_ONLY":
        errors.append("S0 must remain deterministic authority")
    if classes.get("S1", {}).get("may_mint_truth") is not False:
        errors.append("S1 truth minting must be false")
    if classes.get("S2", {}).get("may_mint_truth") is not False:
        errors.append("S2 truth minting must be false")
    if classes.get("S2", {}).get("survives_restart") is not False:
        errors.append("S2 must be restart-discardable")

    transitions = doc.get("transition_rules", {})
    if set(transitions) != REQUIRED_TRANSITIONS:
        errors.append("transition set mismatch")
    if transitions.get("S2_to_S0") != "FORBIDDEN_DIRECT":
        errors.append("direct S2->S0 must be forbidden")
    if transitions.get("ClaudeCode_to_S0") != "FORBIDDEN_DIRECT":
        errors.append("Claude Code direct S0 must be forbidden")
    if transitions.get("JSpace_to_S0") != "FORBIDDEN_DIRECT":
        errors.append("J-Space direct S0 must be forbidden")
    if "DbWriteProposal" not in transitions.get("S1_to_S0", ""):
        errors.append("S1->S0 must require DbWriteProposal")
    if "EffectGate" not in transitions.get("S1_to_effect", "") or "EffectJournal" not in transitions.get("S1_to_effect", ""):
        errors.append("effect transition must retain EffectGate/EffectJournal")

    packet_values = set(doc.get("required_packet_bindings", {}).values())
    if packet_values != REQUIRED_PACKETS:
        errors.append(f"packet binding mismatch: {sorted(packet_values ^ REQUIRED_PACKETS)}")

    hard_negatives = set(doc.get("hard_negatives", []))
    missing_neg = REQUIRED_NEGATIVES - hard_negatives
    if missing_neg:
        errors.append(f"missing hard negatives: {sorted(missing_neg)}")

    rules = doc.get("placement_rules", [])
    placements = {r.get("place") for r in rules}
    for required in {"S0", "S1", "S2", "S0_PENDING_TYPED_ADMISSION_OR_UNKNOWN"}:
        if required not in placements:
            errors.append(f"missing placement class: {required}")

    inv = " ".join(doc.get("variable_grid_invariants", [])).lower()
    for needle in ("module count n", "restart", "grid resize", "cannot promote s1 into s0", "different cognitive process"):
        if needle not in inv:
            errors.append(f"missing variable-grid invariant: {needle}")

    cc = doc.get("claude_code_boundary", {})
    if cc.get("direct_S0_write") is not False:
        errors.append("Claude Code direct S0 write must be false")
    if cc.get("activation_level_global_jspace_claim_without_exposed_causal_evidence") is not False:
        errors.append("Claude Code activation claim must fail closed")

    js = doc.get("jspace_boundary", {})
    if js.get("can_mint_truth") is not False:
        errors.append("J-Space cannot mint truth")
    if js.get("requires_exact_model_runtime_interface_identity") is not True:
        errors.append("J-Space exact identity requirement missing")

    disc = " ".join(doc.get("first_executable_discriminator", {}).get("steps", [])).lower()
    for needle in ("restart", "grid size n", "direct model-to-s0", "stale-generation", "s1-cache-as-recovery-authority", "direct-effect", "claudecodebridgepacket"):
        if needle not in disc:
            errors.append(f"discriminator missing: {needle}")

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
        for error in errors:
            print("FAIL", error)
        return 1
    print("PASS DB_VS_SIMULATION_BOUNDARY/v1 source contract")
    return 0


if __name__ == "__main__":
    sys.exit(main())
