#!/usr/bin/env python3
"""FRANK ActiveAssembly H3 consolidation semantic commutation test.

H3 is modeled as the general-purpose record-selection implementation inlined into the
same runtime/process rather than reached through the H2 typed-FFI boundary. The test
requires exact H1 ordinary-code == H3 consolidated-data semantics for the same epoch,
candidates and policy. This proves consolidation readiness, not final one-binary
packaging or Andreas-target acceptance.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "research_entity/harness/reference"))

from active_assembly import ActiveAssemblyError, AssemblyPacket, compile_active_assembly  # noqa: E402
from claycode_base_record_selection import RecordSelectionError, VERSION as SELECTOR_VERSION, select_records  # noqa: E402
from claycode_wp13_active_assembly_h2 import h1_policy, random_packet  # noqa: E402

OUT = ROOT / "research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_H3_CONSOLIDATION_RECEIPT.json"


def main() -> int:
    rng = random.Random(202608091306)
    mismatches = []
    shuffle_mismatches = 0
    cases = 256
    for trial in range(cases):
        epoch = rng.randint(1, 40)
        max_items = rng.randint(1, 10)
        max_per = rng.randint(1, 4)
        max_cost = None if rng.random() < .3 else rng.randint(2, 30)
        packets = [random_packet(rng, 1000 + trial, i, epoch) for i in range(rng.randint(2, 30))]
        policy = h1_policy(epoch, max_items, max_per, max_cost)
        expected = compile_active_assembly(
            packets,
            current_epoch=epoch,
            max_items=max_items,
            max_per_ancestry=max_per,
            max_context_cost=max_cost,
        )
        observed = select_records([asdict(p) for p in packets], policy)
        if expected != observed:
            mismatches.append({
                "trial": trial,
                "h1_hash": expected.get("assembly_sha256"),
                "h3_hash": observed.get("assembly_sha256"),
            })
        shuffled = list(packets)
        rng.shuffle(shuffled)
        shuffled_observed = select_records([asdict(p) for p in shuffled], policy)
        if observed != shuffled_observed:
            shuffle_mismatches += 1

    # Collision and authority rejection must commute too.
    p1 = AssemblyPacket("x", "fam", "evidence", .8, .7, .6, .2, 3, context_cost=1)
    p2 = AssemblyPacket("x", "fam", "evidence", .1, .7, .6, .2, 3, context_cost=1)
    policy = h1_policy(3, 8, 2, None)
    h1_collision = h3_collision = False
    try:
        compile_active_assembly([p1, p2], current_epoch=3)
    except ActiveAssemblyError:
        h1_collision = True
    try:
        select_records([asdict(p1), asdict(p2)], policy)
    except RecordSelectionError:
        h3_collision = True

    auth = AssemblyPacket("auth", "fam", "capability", .9, .9, .9, .1, 3, proposed_authority=True, context_cost=1)
    h1_authority = h3_authority = False
    try:
        compile_active_assembly([auth], current_epoch=3)
    except ActiveAssemblyError:
        h1_authority = True
    try:
        select_records([asdict(auth)], policy)
    except RecordSelectionError:
        h3_authority = True

    checks = {
        "h1_h3_exact_commutation": not mismatches,
        "candidate_order_invariant": shuffle_mismatches == 0,
        "identity_collision_rejection_commutes": h1_collision and h3_collision,
        "authority_non_minting_rejection_commutes": h1_authority and h3_authority,
    }
    passed = all(checks.values())
    reference = ROOT / "research_entity/harness/reference/active_assembly.py"
    selector = ROOT / "tools/claycode_base_record_selection.py"
    report = {
        "schema_version": "1.0",
        "experiment": "FRANK H1 ActiveAssembly vs H3 in-process consolidated selector commutation",
        "cases": cases,
        "mismatches": mismatches,
        "shuffle_mismatches": shuffle_mismatches,
        "checks": checks,
        "pass": passed,
        "reference_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
        "selector_sha256": hashlib.sha256(selector.read_bytes()).hexdigest(),
        "selector_version": SELECTOR_VERSION,
        "h3_consolidation_semantics_ready": passed,
        "counts_as_target_acceptance": False,
        "counts_as_one_binary_packaging_proof": False,
        "authority_invariant": "consolidated descriptive record selection has no capability bearer and cannot mint execution authority",
        "claim_boundary": "PASS establishes H1/H3 semantic commutation for the frozen ActiveAssembly selection slice. It does not claim final binary packaging or Andreas-target execution.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": passed, "cases": cases, "mismatches": len(mismatches), "shuffle_mismatches": shuffle_mismatches, "output": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
