#!/usr/bin/env python3
"""Bridge acceptance: physical GRID10 evidence -> recursive coordinator tree.

This closes a proof-boundary gap in the GO target architecture. A physical GRID10
cohort receipt is accepted only if it exposes the exact ordinary-node packet digests
that were consumed by the coordinator fan-in. Those same packet digests then become
level-0 leaves of a bounded-fanin recursive coordinator tree. Higher levels carry only
digests/counts and never raw leaf payloads.

This is deterministic source/component evidence only until executed against a current,
repository-bound physical GRID10 receipt. It mints no physical-scale/HCU credit by itself.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

SCHEMA = "XENO_RECURSIVE_PHYSICAL_SCALING_BRIDGE_ACCEPTANCE/v1"


def dg(obj: Any) -> str:
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class Node:
    digest: str
    leaf_count: int
    hot_bytes: int
    raw_bytes: int
    source_kind: str


def _chunks(items: list[Node], n: int):
    for i in range(0, len(items), n):
        yield items[i:i+n]


def physical_leaves(receipt: dict[str, Any]) -> list[Node]:
    if receipt.get("schema") != "XENO_PHYSICAL_GRID10_FUSED_ACCEPTANCE/v1":
        raise ValueError("PHYSICAL_RECEIPT_SCHEMA_INVALID")
    if receipt.get("pass") is not True:
        raise ValueError("PHYSICAL_RECEIPT_NOT_PASS")
    packets = receipt.get("physical_packet_evidence")
    if not isinstance(packets, list) or len(packets) != 10:
        raise ValueError("PHYSICAL_PACKET_EVIDENCE_MISSING")
    fanin = receipt.get("coordinator_consumed_packet_digests")
    if not isinstance(fanin, list) or len(fanin) != 10:
        raise ValueError("COORDINATOR_FANIN_BINDING_MISSING")
    packet_digests = [str(p.get("packet_digest", "")) for p in packets]
    if any(len(d) != 64 for d in packet_digests):
        raise ValueError("PHYSICAL_PACKET_DIGEST_INVALID")
    if len(set(packet_digests)) != 10:
        raise ValueError("PHYSICAL_PACKET_DIGEST_CARDINALITY_INVALID")
    if sorted(packet_digests) != sorted(str(x) for x in fanin):
        raise ValueError("PHYSICAL_TO_RECURSIVE_PACKET_SET_MISMATCH")
    leaves = []
    for p in packets:
        if p.get("source_kind") != "ORDINARY_NODE":
            raise ValueError("NON_ORDINARY_PHYSICAL_LEAF")
        if p.get("s1_write_intent") is not False:
            raise ValueError("ORDINARY_NODE_WRITE_INTENT_FORBIDDEN")
        raw = int(p.get("raw_payload_bytes", 0))
        hot = int(p.get("hot_payload_bytes", raw))
        if raw <= 0 or hot <= 0:
            raise ValueError("PHYSICAL_PACKET_SIZE_INVALID")
        leaves.append(Node(str(p["packet_digest"]), 1, hot, raw, "ORDINARY_NODE"))
    return leaves


def summarize(children: list[Node], *, level: int, group: int, lease_valid: bool = True) -> Node:
    if not lease_valid:
        raise ValueError("COORDINATOR_LEASE_INVALID")
    if not children:
        raise ValueError("EMPTY_FANIN")
    core = {
        "schema": "RECURSIVE_COORDINATOR_SUMMARY/v1",
        "level": level,
        "group": group,
        "child_digests": sorted(c.digest for c in children),
        "leaf_count": sum(c.leaf_count for c in children),
    }
    hot = len(json.dumps(core, sort_keys=True, separators=(",", ":")).encode())
    return Node(
        digest=dg(core),
        leaf_count=core["leaf_count"],
        hot_bytes=hot,
        raw_bytes=sum(c.raw_bytes for c in children),
        source_kind="COORDINATOR",
    )


def bridge(receipt: dict[str, Any], max_fanin: int = 4) -> dict[str, Any]:
    if max_fanin < 2:
        raise ValueError("MAX_FANIN_INVALID")
    leaves = physical_leaves(receipt)
    current = leaves
    levels = []
    level = 1
    max_seen = 0
    while len(current) > 1:
        nxt = []
        for group, children in enumerate(_chunks(current, max_fanin)):
            max_seen = max(max_seen, len(children))
            nxt.append(summarize(children, level=level, group=group))
        levels.append({"level": level, "inputs": len(current), "outputs": len(nxt)})
        current = nxt
        level += 1
    root = current[0]
    tests = {
        "exact_physical_packet_set_reused": root.leaf_count == 10,
        "ordinary_physical_nodes_read_only": all(x.source_kind == "ORDINARY_NODE" for x in leaves),
        "bounded_recursive_fanin": max_seen <= max_fanin,
        "higher_levels_digest_only": root.hot_bytes < root.raw_bytes,
        "root_accounts_all_physical_leaves": root.leaf_count == len(leaves),
    }
    try:
        summarize(leaves[:2], level=1, group=0, lease_valid=False)
    except ValueError as exc:
        tests["invalid_recursive_lease_fails_closed"] = str(exc) == "COORDINATOR_LEASE_INVALID"
    else:
        tests["invalid_recursive_lease_fails_closed"] = False
    return {
        "schema": SCHEMA,
        "pass": all(tests.values()),
        "tests": tests,
        "physical_receipt_digest": dg(receipt),
        "physical_leaf_packet_digests": sorted(x.digest for x in leaves),
        "max_fanin": max_fanin,
        "levels": levels,
        "root": {
            "digest": root.digest,
            "leaf_count": root.leaf_count,
            "raw_payload_bytes": root.raw_bytes,
            "hot_payload_bytes": root.hot_bytes,
            "compression_ratio": root.raw_bytes / max(root.hot_bytes, 1),
        },
        "credit_scope": "SOURCE/DETERMINISTIC_BRIDGE_COMPONENT_ONLY",
        "physical_scale_credit": 0,
        "whole_hcu_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("receipt", type=Path)
    ap.add_argument("--max-fanin", type=int, default=4)
    args = ap.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    print(json.dumps(bridge(receipt, args.max_fanin), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
