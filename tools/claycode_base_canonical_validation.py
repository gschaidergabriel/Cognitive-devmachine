#!/usr/bin/env python3
"""Receipt-oriented validation for ClayCode BASE WP-02 canonical frontend.

Proves only strict V17 parser construction, full admitted-source canonicalization,
deterministic grammar-bound canonical bytes/hash, roundtrip stability, and mutation/trivia
discrimination. It does not prove typed IR, type/effect semantics, evaluator, or release PASS.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "research_entity/claycode/base/implementation"
sys.path.insert(0, str(IMPL))

from claycode_frontend import CANON_SCHEMA, ClayCodeFrontend, sha256_bytes  # noqa: E402

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]


def q(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, max(0, int((len(s) - 1) * p)))]


def os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v.strip().strip('"')
    return out


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED"


def case(frontend: ClayCodeFrontend, name: str, left: str, right: str, expected_same: bool) -> dict:
    lh = frontend.semantic_hash(left)
    rh = frontend.semantic_hash(right)
    observed = lh == rh
    return {
        "case": name,
        "left_hash": lh,
        "right_hash": rh,
        "expected_same": expected_same,
        "observed_same": observed,
        "pass": observed == expected_same,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output")
    ap.add_argument("--repetitions", type=int, default=7)
    ap.add_argument("--nonstrict", action="store_true", help="Local diagnostic only; receipts must be strict")
    args = ap.parse_args()

    started_wall = datetime.now(timezone.utc)
    started_mono = time.perf_counter_ns()
    frontend = ClayCodeFrontend.from_path(GRAMMAR, strict=not args.nonstrict)

    source_results = []
    for path in SOURCES:
        source = path.read_text(encoding="utf-8")
        durations_ms: list[float] = []
        hashes: list[str] = []
        sizes: list[int] = []
        roundtrip_ok = True
        for _ in range(max(2, args.repetitions)):
            t0 = time.perf_counter_ns()
            doc = frontend.canonicalize(source)
            payload = doc.bytes()
            durations_ms.append((time.perf_counter_ns() - t0) / 1e6)
            hashes.append(doc.semantic_hash())
            sizes.append(len(payload))
            rt = doc.roundtrip()
            roundtrip_ok = roundtrip_ok and (rt.bytes() == payload and rt.semantic_hash() == doc.semantic_hash())
        source_results.append({
            "path": str(path.relative_to(ROOT)),
            "source_sha256": sha256_bytes(source.encode("utf-8")),
            "semantic_hashes": hashes,
            "deterministic_repeat": len(set(hashes)) == 1,
            "roundtrip_stable": roundtrip_ok,
            "canonical_bytes": sizes[0],
            "latency_ms": {
                "n": len(durations_ms),
                "min": min(durations_ms),
                "p50": statistics.median(durations_ms),
                "p90": q(durations_ms, 0.90),
                "p95": q(durations_ms, 0.95),
                "p99": q(durations_ms, 0.99),
                "max": max(durations_ms),
            },
        })

    equivalence_cases = [
        case(frontend, "owns_horizontal_trivia", "rule Needle.owns(X)\n", "rule Needle.owns ( X ) // comment\n", True),
        case(frontend, "block_semicolon_vs_newline", "record X { a:Int; b:Int }\n", "record X {\n a:Int\n b:Int\n}\n", True),
        case(frontend, "ignored_comment", "rule x>0\n", "rule x > 0 // ignored\n", True),
    ]
    mutation_cases = [
        case(frontend, "greater_vs_less", "rule x>0\n", "rule x<0\n", False),
        case(frontend, "equal_vs_not_equal", "rule x==0\n", "rule x!=0\n", False),
        case(frontend, "ordered_call_arguments", "rule f(a,b)\n", "rule f(b,a)\n", False),
        case(frontend, "boolean_flip", "rule true\n", "rule false\n", False),
    ]

    # Exactly one GO out-of-the-box experiment: a metamorphic canonicalization orbit.
    orbit_variants = [
        "record Meta { a:Int; b:Int }\n",
        "record Meta { a:Int\n b:Int }\n",
        "record Meta {\n a:Int; b:Int\n}\n",
        "record Meta {\n\n a:Int\n\n b:Int\n\n}\n",
        "record Meta { a:Int; // split\n b:Int }\n",
        "record   Meta   {   a:Int ; b:Int   } // tail\n",
    ]
    orbit_hashes = [frontend.semantic_hash(v) for v in orbit_variants]
    mutation_hash = frontend.semantic_hash("record Meta { a:Int; b:Bool }\n")
    orbit_pass = len(set(orbit_hashes)) == 1 and mutation_hash != orbit_hashes[0]
    out_of_box = {
        "experiment_id": "GO-OOB-WP02-METAMORPHIC-CANONICAL-ORBIT-20260810",
        "hypothesis": "All grammar-declared trivia/block-separator variants map to one canonical semantic hash while a typed field mutation leaves that orbit.",
        "counterhypothesis": "Surface separator/comment choices leak into the canonical hash or the canonicalizer collapses a semantic type mutation.",
        "variant_count": len(orbit_variants),
        "variant_hashes": orbit_hashes,
        "unique_variant_hashes": len(set(orbit_hashes)),
        "semantic_mutation_hash": mutation_hash,
        "reversible": True,
        "baseline": "record Meta { a:Int; b:Int }",
        "pass": orbit_pass,
        "promotion_rule": "Experiment is diagnostic only; WP-02 promotion still requires strict Ubuntu/full-source receipt.",
    }

    duration_ms = (time.perf_counter_ns() - started_mono) / 1e6
    strict_mode = not args.nonstrict
    passed = (
        strict_mode
        and all(x["deterministic_repeat"] and x["roundtrip_stable"] for x in source_results)
        and all(x["pass"] for x in equivalence_cases)
        and all(x["pass"] for x in mutation_cases)
        and out_of_box["pass"]
    )
    out = {
        "schema_version": "1.0",
        "receipt_type": "CC_WP02_V17_CANONICAL_FRONTEND_VALIDATION",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "started_at": started_wall.isoformat(),
        "pass": passed,
        "strict_mode": strict_mode,
        "canonical_schema": CANON_SCHEMA,
        "grammar": {
            "path": str(GRAMMAR.relative_to(ROOT)),
            "sha256": hashlib.sha256(GRAMMAR.read_bytes()).hexdigest(),
        },
        "runtime": {
            "python": sys.version,
            "implementation": platform.python_implementation(),
            "lark": package_version("lark"),
            "interegular": package_version("interegular"),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or "UNKNOWN",
            "cpu_count": os.cpu_count(),
            "node": platform.node() or "UNKNOWN",
            "os_release": os_release(),
        },
        "source_results": source_results,
        "equivalence_cases": equivalence_cases,
        "mutation_cases": mutation_cases,
        "out_of_box_experiment": out_of_box,
        "duration_ms": duration_ms,
        "scope_guard": "PASS proves strict V17 construction plus deterministic grammar-bound canonicalization/roundtrip and selected metamorphic/mutation discriminators on current G9 V3 + Dialect V3. It does not prove typed IR, type/effect, evaluator, lowering, runtime, WP-02 final PASS, or BASE release PASS.",
    }
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
