#!/usr/bin/env python3
"""ClayCode source-chain integrity probe.

Research-only bounded discriminator:
1. current G9 cycle header accepts anonymous cycle(...) but not cycle name(...);
2. compares prior return-lowering semantics against emit-as-nonterminating event semantics;
3. separates semantic fixture identity from exact source/contract identity.

This does not define ClayCode semantics. It detects where they are currently missing.
"""
from __future__ import annotations
import hashlib
import json
import random
import re

NAMED = """module frank.loop_probe
record LoopInput { state_delta:Float; residual_pressure:Float; instability:Float; recurrence_delta:Float; }
cycle classify(x:LoopInput) {
  if x.instability >= 0.80 { emit(\"DIVERGING_OR_OVERTHINKING\") }
  if x.state_delta <= 0.05 && x.residual_pressure >= 0.50 { emit(\"STALLED\") }
  if x.recurrence_delta >= 0.15 && x.instability < 0.80 { emit(\"PRODUCTIVE_LIMIT_CYCLE\") }
  emit(\"CONVERGING_FIXED_POINT\")
}"""
ANON = NAMED.replace("cycle classify(", "cycle(")

CURRENT_CYCLE = re.compile(r"^\s*cycle\s*\(")
NAMED_CYCLE = re.compile(r"^\s*cycle\s+([A-Za-z_][A-Za-z0-9_-]*)\s*\(")

def header(src: str) -> str:
    return next(x for x in src.splitlines() if x.lstrip().startswith("cycle"))

def sha(obj) -> str:
    if isinstance(obj, str):
        data = obj.encode()
    else:
        data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()

def return_lowering(x):
    if x["instability"] >= 0.80:
        return ["DIVERGING_OR_OVERTHINKING"]
    if x["state_delta"] <= 0.05 and x["residual_pressure"] >= 0.50:
        return ["STALLED"]
    if x["recurrence_delta"] >= 0.15 and x["instability"] < 0.80:
        return ["PRODUCTIVE_LIMIT_CYCLE"]
    return ["CONVERGING_FIXED_POINT"]

def emit_continues(x):
    out = []
    if x["instability"] >= 0.80:
        out.append("DIVERGING_OR_OVERTHINKING")
    if x["state_delta"] <= 0.05 and x["residual_pressure"] >= 0.50:
        out.append("STALLED")
    if x["recurrence_delta"] >= 0.15 and x["instability"] < 0.80:
        out.append("PRODUCTIVE_LIMIT_CYCLE")
    out.append("CONVERGING_FIXED_POINT")
    return out

def main():
    named_header = header(NAMED)
    anon_header = header(ANON)
    header_result = {
        "named_header": named_header,
        "anonymous_header": anon_header,
        "current_cycle_header_accepts_named": bool(CURRENT_CYCLE.match(named_header)),
        "current_cycle_header_accepts_anonymous": bool(CURRENT_CYCLE.match(anon_header)),
        "named_cycle_shape_detected": bool(NAMED_CYCLE.match(named_header)),
    }

    rng = random.Random(20260809)
    n = 20_000
    divergence = 0
    categories = {}
    for _ in range(n):
        x = {
            "state_delta": rng.random(),
            "residual_pressure": rng.random(),
            "instability": rng.random(),
            "recurrence_delta": rng.random(),
        }
        a = return_lowering(x)
        b = emit_continues(x)
        categories[a[0]] = categories.get(a[0], 0) + 1
        divergence += int(a != b)

    canonical_fixture = {
        "kind": "cycle_fixture",
        "params": [{"name": "x", "type": "LoopInput"}],
        "body_semantics": "UNRESOLVED_EMIT_TERMINATION",
    }
    semantic_hash = sha(canonical_fixture)
    contract_hashes = set()
    for i in range(10_000):
        contract_hashes.add(sha({"fixture_label": f"probe_{i}", "source": ANON}))

    result = {
        "header_result": header_result,
        "emit_vs_return_discriminator": {
            "seed": 20260809,
            "cases": n,
            "different_observable_traces": divergence,
            "same_observable_traces": n - divergence,
            "prior_return_lowering_categories": categories,
            "interpretation": "Ambiguity discriminator only; neither arm is promoted as ClayCode semantics.",
        },
        "identity_discriminator": {
            "candidate_semantic_hash": semantic_hash,
            "distinct_contract_hashes_for_10000_fixture_labels": len(contract_hashes),
            "rule_under_test": "unreferenced harness label may be nonsemantic while exact source/fixture identity remains provenance-bound",
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
