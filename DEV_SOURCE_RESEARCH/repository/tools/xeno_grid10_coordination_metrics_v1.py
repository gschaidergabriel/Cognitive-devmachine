#!/usr/bin/env python3
"""Measure real GRID10 coordinator overhead without minting architecture credit.

Consumes one JSONL event trace emitted by the physical Xeno fabric. The trace is
observable runtime telemetry, not model self-report. This tool validates causal
continuity and reports fan-in, byte compression, latency and CAS contention.

Required event kinds:
  NODE_RESULT      node_id, packet_digest, emitted_ns, payload_bytes
  COORDINATOR_RECV coordinator_id, packet_digest, received_ns
  S1_COMMIT        coordinator_id, input_packet_digests, started_ns, committed_ns,
                   summary_bytes, cas_attempts, cas_conflicts

Normal Xeno nodes never write S1 in this schema. S1_COMMIT is coordinator-only.
No thresholds are silently invented here; this is a measurement component only.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any

SCHEMA = "XENO_GRID10_COORDINATION_METRICS/v1"


def q(values: list[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return float(xs[0])
    i = (len(xs) - 1) * p
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    frac = i - lo
    return float(xs[lo] * (1 - frac) + xs[hi] * frac)


def digest_obj(obj: Any) -> str:
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_events(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"EVENT_NOT_OBJECT:{n}")
        obj["_line"] = n
        out.append(obj)
    return out


def measure(events: list[dict[str, Any]]) -> dict[str, Any]:
    emitted: dict[str, dict[str, Any]] = {}
    recv: dict[str, list[dict[str, Any]]] = defaultdict(list)
    commits: list[dict[str, Any]] = []
    node_ids: set[str] = set()

    for e in events:
        kind = e.get("kind")
        if kind == "NODE_RESULT":
            d = str(e.get("packet_digest", ""))
            if len(d) != 64:
                raise ValueError(f"BAD_PACKET_DIGEST:{e['_line']}")
            if d in emitted:
                raise ValueError(f"DUPLICATE_NODE_RESULT:{d}")
            node = str(e.get("node_id", ""))
            if not node:
                raise ValueError(f"NODE_ID_MISSING:{e['_line']}")
            if int(e.get("payload_bytes", -1)) < 0:
                raise ValueError(f"PAYLOAD_BYTES_INVALID:{e['_line']}")
            emitted[d] = e
            node_ids.add(node)
        elif kind == "COORDINATOR_RECV":
            d = str(e.get("packet_digest", ""))
            if len(d) != 64:
                raise ValueError(f"BAD_RECV_DIGEST:{e['_line']}")
            if not str(e.get("coordinator_id", "")):
                raise ValueError(f"COORDINATOR_ID_MISSING:{e['_line']}")
            recv[d].append(e)
        elif kind == "S1_COMMIT":
            if not str(e.get("coordinator_id", "")):
                raise ValueError(f"COMMIT_COORDINATOR_MISSING:{e['_line']}")
            inputs = e.get("input_packet_digests")
            if not isinstance(inputs, list) or not inputs:
                raise ValueError(f"COMMIT_INPUTS_INVALID:{e['_line']}")
            if len(set(map(str, inputs))) != len(inputs):
                raise ValueError(f"COMMIT_DUPLICATE_INPUT:{e['_line']}")
            if int(e.get("summary_bytes", -1)) < 0:
                raise ValueError(f"SUMMARY_BYTES_INVALID:{e['_line']}")
            attempts = int(e.get("cas_attempts", 0))
            conflicts = int(e.get("cas_conflicts", 0))
            if attempts < 1 or conflicts < 0 or conflicts >= attempts + 1:
                raise ValueError(f"CAS_COUNTS_INVALID:{e['_line']}")
            commits.append(e)
        elif kind in (None, ""):
            raise ValueError(f"EVENT_KIND_MISSING:{e['_line']}")

    if not emitted:
        raise ValueError("NO_NODE_RESULTS")
    if not commits:
        raise ValueError("NO_S1_COMMITS")

    consumed: Counter[str] = Counter()
    fanins: list[int] = []
    ratios: list[float] = []
    node_to_recv_us: list[float] = []
    commit_us: list[float] = []
    end_to_end_us: list[float] = []
    total_raw = 0
    total_summary = 0
    total_attempts = 0
    total_conflicts = 0

    for d, rs in recv.items():
        if d not in emitted:
            raise ValueError(f"RECEIVE_WITHOUT_EMIT:{d}")
        t0 = int(emitted[d]["emitted_ns"])
        for r in rs:
            dt = int(r["received_ns"]) - t0
            if dt < 0:
                raise ValueError(f"NEGATIVE_NODE_TO_RECV:{d}")
            node_to_recv_us.append(dt / 1000.0)

    for c in commits:
        inputs = [str(x) for x in c["input_packet_digests"]]
        missing = [d for d in inputs if d not in emitted]
        if missing:
            raise ValueError(f"COMMIT_UNKNOWN_INPUT:{missing[0]}")
        for d in inputs:
            if not recv.get(d):
                raise ValueError(f"COMMIT_INPUT_NOT_RECEIVED:{d}")
            consumed[d] += 1
        fanins.append(len(inputs))
        raw = sum(int(emitted[d]["payload_bytes"]) for d in inputs)
        summary = int(c["summary_bytes"])
        total_raw += raw
        total_summary += summary
        ratios.append((raw / summary) if summary > 0 else float("inf"))
        start = int(c["started_ns"])
        end = int(c["committed_ns"])
        if end < start:
            raise ValueError("NEGATIVE_COMMIT_LATENCY")
        commit_us.append((end - start) / 1000.0)
        first_emit = min(int(emitted[d]["emitted_ns"]) for d in inputs)
        if end < first_emit:
            raise ValueError("NEGATIVE_END_TO_END_LATENCY")
        end_to_end_us.append((end - first_emit) / 1000.0)
        total_attempts += int(c["cas_attempts"])
        total_conflicts += int(c["cas_conflicts"])

    duplicates = sorted(d for d, n in consumed.items() if n > 1)
    unconsumed = sorted(d for d in emitted if consumed[d] == 0)
    tests = {
        "all_committed_packets_were_emitted": True,
        "all_committed_packets_were_received": True,
        "no_packet_consumed_by_multiple_commits": not duplicates,
        "all_emitted_packets_consumed": not unconsumed,
        "ordinary_nodes_have_no_s1_commit_event": all(e.get("kind") != "S1_COMMIT" or "node_id" not in e for e in events),
    }

    return {
        "schema": SCHEMA,
        "pass": all(tests.values()),
        "tests": tests,
        "trace_digest": digest_obj([{k:v for k,v in e.items() if k != "_line"} for e in events]),
        "counts": {
            "nodes": len(node_ids),
            "node_results": len(emitted),
            "coordinator_receives": sum(len(v) for v in recv.values()),
            "s1_commits": len(commits),
            "unconsumed_packets": len(unconsumed),
            "multiply_consumed_packets": len(duplicates),
        },
        "fanin": {
            "min": min(fanins), "max": max(fanins), "mean": statistics.fmean(fanins),
            "p50": q([float(x) for x in fanins], .50), "p95": q([float(x) for x in fanins], .95),
        },
        "compression": {
            "raw_input_bytes": total_raw,
            "summary_bytes": total_summary,
            "aggregate_ratio_raw_over_summary": (total_raw / total_summary) if total_summary else None,
            "per_commit_ratio_p50": q(ratios, .50), "per_commit_ratio_p95": q(ratios, .95),
        },
        "latency_us": {
            "node_to_coordinator_p50": q(node_to_recv_us, .50),
            "node_to_coordinator_p95": q(node_to_recv_us, .95),
            "coordinator_commit_p50": q(commit_us, .50),
            "coordinator_commit_p95": q(commit_us, .95),
            "emit_to_s1_commit_p50": q(end_to_end_us, .50),
            "emit_to_s1_commit_p95": q(end_to_end_us, .95),
        },
        "contention": {
            "cas_attempts": total_attempts,
            "cas_conflicts": total_conflicts,
            "conflict_rate_per_attempt": (total_conflicts / total_attempts) if total_attempts else None,
        },
        "unconsumed_packet_digests": unconsumed,
        "multiply_consumed_packet_digests": duplicates,
        "credit_scope": "RUNTIME_TELEMETRY_MEASUREMENT_COMPONENT_ONLY",
        "physical_grid10_credit": 0,
        "whole_hcu_credit": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("trace", type=Path)
    args = ap.parse_args()
    result = measure(load_events(args.trace))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
