#!/usr/bin/env python3
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"
EXPECTED = {f"AZP{i:02d}" for i in range(1, 21)}
REQUIRED_PACKETS = {
    "CognitiveWorkUnit", "RouteLease", "CognitiveResult", "WorkspacePacket",
    "DbWriteProposal", "ClaudeCodeBridgePacket", "JSpaceMeasurement", "EffectProposal"
}


def validate(doc):
    errors = []
    if doc.get("schema") != "COGNITIVE_PROCESS_ABI/v1":
        errors.append("wrong schema")
    if doc.get("authority", {}).get("grid_law") != "VARIABLE_N_RUNTIME_PARAMETER_GRID10_ONLY_A_BENCHMARK_CONFIGURATION":
        errors.append("grid law is not variable-N")
    packets = set(doc.get("packet_types", {}))
    if packets != REQUIRED_PACKETS:
        errors.append(f"packet set mismatch: {sorted(packets ^ REQUIRED_PACKETS)}")
    bindings = set(doc.get("process_binding", {}))
    if bindings != EXPECTED:
        errors.append(f"process binding mismatch: {sorted(bindings ^ EXPECTED)}")
    for process_id, names in doc.get("process_binding", {}).items():
        unknown = set(names) - packets
        if unknown:
            errors.append(f"{process_id} references unknown packet(s): {sorted(unknown)}")
    rules = " ".join(doc.get("cross_process_invariants", [])).lower()
    for needle in ("independent of module identity and grid size", "never mint canonical truth", "effectgate/effectjournal", "causal_event_id", "restart/rejoin", "claude code"):
        if needle not in rules:
            errors.append(f"missing invariant: {needle}")
    disc = doc.get("first_executable_discriminator", {})
    steps = " ".join(disc.get("steps", [])).lower()
    for needle in ("different azp", "restart", "stale-generation", "self-granted-capability", "direct-s0-write"):
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
