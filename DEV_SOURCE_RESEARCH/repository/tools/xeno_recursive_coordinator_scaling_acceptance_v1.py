#!/usr/bin/env python3
"""Recursive coordinator scaling acceptance candidate v1.

Architecture-only deterministic harness for the current GO target. It proves the
coordination topology can keep per-coordinator fan-in bounded while ordinary Xeno
modules remain shared-state read-only and only leased coordinators emit scoped S1
summary deltas. This is NOT a physical-scale/HCU pass until repository-bound runtime
evidence exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import argparse, json, math
from typing import Iterable

SCHEMA = "XENO_RECURSIVE_COORDINATOR_SCALING_ACCEPTANCE/v1"


def dg(obj) -> str:
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class Packet:
    packet_id: str
    source_kind: str
    leaf_count: int
    evidence_digest: str
    raw_payload_bytes: int
    hot_payload_bytes: int
    s1_write_intent: bool


@dataclass(frozen=True)
class Lease:
    coordinator_id: str
    level: int
    scope: str
    valid: bool = True


def leaf_packet(i: int) -> Packet:
    core = {"leaf": i, "observation": f"result:{i}"}
    raw = len(json.dumps(core, sort_keys=True).encode())
    return Packet(
        packet_id=f"leaf:{i}", source_kind="ORDINARY_NODE", leaf_count=1,
        evidence_digest=dg(core), raw_payload_bytes=raw, hot_payload_bytes=raw,
        s1_write_intent=False,
    )


def coordinator_summary(lease: Lease, children: list[Packet]) -> Packet:
    if not lease.valid:
        raise ValueError("COORDINATOR_LEASE_INVALID")
    if not children:
        raise ValueError("EMPTY_FANIN")
    if any(c.s1_write_intent for c in children if c.source_kind == "ORDINARY_NODE"):
        raise ValueError("ORDINARY_NODE_WRITE_INTENT_FORBIDDEN")
    # Higher levels carry only hashes/counts, never concatenated raw child payloads.
    core = {
        "coordinator": lease.coordinator_id,
        "level": lease.level,
        "scope": lease.scope,
        "children": sorted(c.evidence_digest for c in children),
        "leaf_count": sum(c.leaf_count for c in children),
    }
    hot = len(json.dumps(core, sort_keys=True).encode())
    return Packet(
        packet_id=f"coord:{lease.level}:{lease.coordinator_id}",
        source_kind="COORDINATOR",
        leaf_count=core["leaf_count"], evidence_digest=dg(core),
        raw_payload_bytes=sum(c.raw_payload_bytes for c in children),
        hot_payload_bytes=hot, s1_write_intent=True,
    )


def chunks(seq: list[Packet], n: int) -> Iterable[list[Packet]]:
    for i in range(0, len(seq), n):
        yield seq[i:i+n]


def build_tree(node_count: int, max_fanin: int) -> dict:
    if node_count < 2 or max_fanin < 2:
        raise ValueError("INVALID_SCALE_PARAMETERS")
    current = [leaf_packet(i) for i in range(node_count)]
    levels = []
    level = 1
    total_coordinators = 0
    max_observed_fanin = 0
    while len(current) > 1:
        nxt = []
        groups = list(chunks(current, max_fanin))
        for gi, group in enumerate(groups):
            max_observed_fanin = max(max_observed_fanin, len(group))
            lease = Lease(f"c{level}-{gi}", level, f"L{level}:G{gi}")
            nxt.append(coordinator_summary(lease, group))
            total_coordinators += 1
        levels.append({"level": level, "inputs": len(current), "coordinators": len(nxt), "max_fanin": max(len(g) for g in groups)})
        current = nxt
        level += 1
    root = current[0]
    theoretical_depth = math.ceil(math.log(node_count, max_fanin))
    return {
        "node_count": node_count,
        "max_fanin_policy": max_fanin,
        "levels": levels,
        "depth": len(levels),
        "theoretical_depth_bound": theoretical_depth,
        "total_coordinators": total_coordinators,
        "max_observed_fanin": max_observed_fanin,
        "root_leaf_count": root.leaf_count,
        "root_evidence_digest": root.evidence_digest,
        "root_raw_payload_bytes": root.raw_payload_bytes,
        "root_hot_payload_bytes": root.hot_payload_bytes,
        "root_compression_ratio": root.raw_payload_bytes / max(root.hot_payload_bytes, 1),
        "root_is_coordinator_write": root.s1_write_intent,
    }


def run(max_fanin: int = 8) -> dict:
    scales = [10, 100, 1_000, 10_000]
    results = [build_tree(n, max_fanin) for n in scales]
    tests = {
        "ordinary_nodes_read_only": all(not leaf_packet(i).s1_write_intent for i in range(32)),
        "coordinator_only_summary_writes": all(r["root_is_coordinator_write"] for r in results),
        "bounded_fanin": all(r["max_observed_fanin"] <= max_fanin for r in results),
        "all_leaves_accounted": all(r["root_leaf_count"] == r["node_count"] for r in results),
        "logarithmic_depth_bound": all(r["depth"] <= r["theoretical_depth_bound"] + 1 for r in results),
        "compression_improves_with_scale": results[-1]["root_compression_ratio"] > results[0]["root_compression_ratio"],
        "invalid_lease_fails_closed": False,
    }
    try:
        coordinator_summary(Lease("bad", 1, "x", valid=False), [leaf_packet(0), leaf_packet(1)])
    except ValueError as exc:
        tests["invalid_lease_fails_closed"] = str(exc) == "COORDINATOR_LEASE_INVALID"
    return {
        "schema": SCHEMA,
        "pass": all(tests.values()),
        "tests": tests,
        "results": results,
        "credit_scope": "SOURCE/DETERMINISTIC_ARCHITECTURE_COMPONENT_ONLY",
        "whole_hcu_credit": 0,
        "physical_scale_credit": 0,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-fanin", type=int, default=8)
    args = ap.parse_args()
    print(json.dumps(run(args.max_fanin), indent=2, sort_keys=True))
