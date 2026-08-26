#!/usr/bin/env python3
"""Bind the exact fused physical GRID10 cohort to recursive coordinator scaling.

v2 consumes the receipt shape actually emitted by
`xeno_physical_grid10_fused_acceptance_v1.py`. It does not invent payload-size or
compression evidence. Its sole job is causal continuity: the exact ten packet
digests proven to come from one simultaneously-live physical cohort and consumed by
the physical coordinator become the level-0 leaves of a bounded-fanin recursive
coordinator tree.

This is source/component evidence until run against a clean repository-bound physical
receipt. It mints no physical-scale or whole-HCU credit by itself.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

SCHEMA = "XENO_RECURSIVE_PHYSICAL_SCALING_BRIDGE_ACCEPTANCE/v2"
PHYSICAL_SCHEMA = "XENO_PHYSICAL_GRID10_FUSED_ACCEPTANCE/v1"
REQUIRED_PHYSICAL_TESTS = (
    "P1_TEN_SIMULTANEOUSLY_LIVE_DISTINCT_PIDS",
    "P1_PARENT_CHILD_PID_BINDING",
    "P1_ONE_SHARED_SNAPSHOT",
    "P1_READ_TRANSACTION_HELD",
    "P2_ORDINARY_RESULTS_NONWRITING",
    "P2_PACKET_MEMBERSHIP_PROCESS_BINDING",
    "P3_EXACT_BARRIER_PACKET_SET_ATOMICALLY_ADMITTED",
    "P3_SINGLE_S1_EPOCH_ADVANCE",
    "P3_NONCANONICAL_COORDINATOR_WRITE",
)


def dg(obj: Any) -> str:
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class Node:
    digest: str
    leaf_count: int


def _chunks(items: list[Node], n: int):
    for i in range(0, len(items), n):
        yield items[i:i+n]


def physical_packet_digests(receipt: dict[str, Any]) -> list[str]:
    if receipt.get("schema") != PHYSICAL_SCHEMA:
        raise ValueError("PHYSICAL_RECEIPT_SCHEMA_INVALID")
    if receipt.get("pass") is not True:
        raise ValueError("PHYSICAL_RECEIPT_NOT_PASS")

    tests = receipt.get("tests")
    if not isinstance(tests, dict):
        raise ValueError("PHYSICAL_TEST_VECTOR_MISSING")
    for name in REQUIRED_PHYSICAL_TESTS:
        if tests.get(name) is not True:
            raise ValueError(f"PHYSICAL_REQUIRED_TEST_NOT_PASS:{name}")

    manifest = receipt.get("cohort_manifest")
    if not isinstance(manifest, dict) or manifest.get("schema") != "GRID10_FUSED_COHORT_MANIFEST/v1":
        raise ValueError("PHYSICAL_COHORT_MANIFEST_INVALID")
    members = manifest.get("members")
    if not isinstance(members, list) or len(members) != 10:
        raise ValueError("PHYSICAL_COHORT_MEMBER_COUNT_INVALID")
    if manifest.get("all_alive_at_barrier") is not True:
        raise ValueError("PHYSICAL_COHORT_NOT_SIMULTANEOUSLY_LIVE")
    pids = [int(m.get("pid", -1)) for m in members]
    if len(set(pids)) != 10 or any(pid <= 0 for pid in pids):
        raise ValueError("PHYSICAL_COHORT_PID_CARDINALITY_INVALID")

    manifest_digests = [str(m.get("packet_digest", "")) for m in members]
    if any(len(d) != 64 for d in manifest_digests):
        raise ValueError("PHYSICAL_PACKET_DIGEST_INVALID")
    if len(set(manifest_digests)) != 10:
        raise ValueError("PHYSICAL_PACKET_DIGEST_CARDINALITY_INVALID")

    coordinator_receipt = receipt.get("receipt")
    if not isinstance(coordinator_receipt, dict):
        raise ValueError("PHYSICAL_COORDINATOR_RECEIPT_MISSING")
    consumed = coordinator_receipt.get("packet_digests")
    if not isinstance(consumed, list) or len(consumed) != 10:
        raise ValueError("COORDINATOR_FANIN_BINDING_MISSING")
    consumed_digests = [str(x) for x in consumed]
    if sorted(consumed_digests) != sorted(manifest_digests):
        raise ValueError("PHYSICAL_TO_RECURSIVE_PACKET_SET_MISMATCH")
    if coordinator_receipt.get("canonical_truth") is not False:
        raise ValueError("COORDINATOR_CANONICAL_TRUTH_FORBIDDEN")
    if coordinator_receipt.get("effect_authority") is not False:
        raise ValueError("COORDINATOR_EFFECT_AUTHORITY_FORBIDDEN")

    boundary = receipt.get("authority_boundary")
    if not isinstance(boundary, dict):
        raise ValueError("PHYSICAL_AUTHORITY_BOUNDARY_MISSING")
    if boundary.get("ordinary_node_s1_write") is not False:
        raise ValueError("ORDINARY_NODE_WRITE_AUTHORITY_FORBIDDEN")
    if boundary.get("coordinator_only_s1_write") is not True:
        raise ValueError("COORDINATOR_ONLY_WRITE_NOT_PROVEN")

    return sorted(manifest_digests)


def summarize(children: list[Node], *, level: int, group: int, lease_valid: bool = True) -> Node:
    if not lease_valid:
        raise ValueError("COORDINATOR_LEASE_INVALID")
    if not children:
        raise ValueError("EMPTY_FANIN")
    core = {
        "schema": "RECURSIVE_COORDINATOR_SUMMARY/v2",
        "level": level,
        "group": group,
        "child_digests": sorted(c.digest for c in children),
        "leaf_count": sum(c.leaf_count for c in children),
    }
    return Node(digest=dg(core), leaf_count=int(core["leaf_count"]))


def bridge(receipt: dict[str, Any], max_fanin: int = 4) -> dict[str, Any]:
    if max_fanin < 2:
        raise ValueError("MAX_FANIN_INVALID")
    packet_digests = physical_packet_digests(receipt)
    current = [Node(digest=d, leaf_count=1) for d in packet_digests]
    levels: list[dict[str, int]] = []
    level = 1
    max_seen = 0
    while len(current) > 1:
        nxt: list[Node] = []
        for group, children in enumerate(_chunks(current, max_fanin)):
            max_seen = max(max_seen, len(children))
            nxt.append(summarize(children, level=level, group=group))
        levels.append({"level": level, "inputs": len(current), "outputs": len(nxt)})
        current = nxt
        level += 1
    root = current[0]

    tests = {
        "exact_physical_packet_set_reused": root.leaf_count == 10,
        "bounded_recursive_fanin": max_seen <= max_fanin,
        "root_accounts_all_physical_leaves": root.leaf_count == 10,
        "recursive_tree_has_multiple_levels": len(levels) >= 2,
    }
    try:
        summarize([Node(packet_digests[0], 1)], level=1, group=0, lease_valid=False)
    except ValueError as exc:
        tests["invalid_recursive_lease_fails_closed"] = str(exc) == "COORDINATOR_LEASE_INVALID"
    else:
        tests["invalid_recursive_lease_fails_closed"] = False

    return {
        "schema": SCHEMA,
        "pass": all(tests.values()),
        "tests": tests,
        "physical_receipt_digest": dg(receipt),
        "physical_leaf_packet_digests": packet_digests,
        "max_fanin": max_fanin,
        "levels": levels,
        "root": {"digest": root.digest, "leaf_count": root.leaf_count},
        "measurement_boundary": {
            "compression_ratio_measured_here": False,
            "latency_measured_here": False,
            "contention_measured_here": False,
            "reason": "v2 proves packet-set causal continuity only; performance must be measured on the real process fabric",
        },
        "credit_scope": "SOURCE/DETERMINISTIC_PACKET_CONTINUITY_COMPONENT_ONLY",
        "physical_scale_credit": 0,
        "whole_hcu_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("receipt", type=Path)
    ap.add_argument("--max-fanin", type=int, default=4)
    args = ap.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    result = bridge(receipt, args.max_fanin)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
