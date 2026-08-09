#!/usr/bin/env python3
"""Compile a real frozen FRANK ActiveAssembly subsystem through ClayCode BASE.

APP-09/WP13 evidence only. This takes the exact weighted packet_score mechanism from
research_entity/harness/reference/active_assembly.py, expresses that computation in the
frozen ClayCode function surface, compiles it to native C, executes it, and differentially
compares the observed native result with the frozen FRANK reference.

The surrounding ActiveAssembly validation/rounding/collections/control-flow remain in the
FRANK reference and are explicitly NOT claimed as compiled by this receipt.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from claycode_base_pure_toolchain import compile_source, differential

REFERENCE = ROOT / "research_entity/harness/reference/active_assembly.py"
OUT = ROOT / "research_entity/claycode/autonomous/FRANK_PACKET_SCORE_CLAY_HANDOFF_RECEIPT.json"

CLAY_SOURCE = """module frank.active_assembly.packet_score
fn packet_score(relevance:Real,impact:Real,novelty:Real,uncertainty:Real)->Real=0.45*relevance+0.25*impact+0.15*novelty+0.15*(1.0-uncertainty)
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_reference():
    spec = importlib.util.spec_from_file_location("frank_active_assembly_reference", REFERENCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("REFERENCE_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    ref = load_reference()
    typed = compile_source(CLAY_SOURCE)
    fixtures = [
        ("memory", 0.9, 0.8, 0.4, 0.1),
        ("tool", 0.8, 0.9, 0.5, 0.2),
        ("balanced", 0.5, 0.5, 0.5, 0.5),
        ("low", 0.1, 0.2, 0.3, 0.4),
        ("high", 1.0, 1.0, 1.0, 0.0),
        ("fractional", 0.1234, 0.5678, 0.3456, 0.789),
    ]
    rows = []
    for index, (name, relevance, impact, novelty, uncertainty) in enumerate(fixtures):
        packet = ref.AssemblyPacket(
            packet_id=f"clay-frank-{index}",
            ancestry_family="frank-handoff",
            kind="memory",
            relevance=relevance,
            impact=impact,
            novelty=novelty,
            uncertainty=uncertainty,
            valid_epoch=1,
        )
        expected = float(ref.packet_score(packet))
        diff = differential(typed, "packet_score", [relevance, impact, novelty, uncertainty])
        observed = float(diff["native_stdout"])
        absolute_error = abs(observed - expected)
        rows.append({
            "fixture": name,
            "inputs": [relevance, impact, novelty, uncertainty],
            "frank_reference": expected,
            "clay_interpreter": float(diff["interpreter_result"]),
            "clay_native": observed,
            "native_internal_match": bool(diff["match"]),
            "absolute_error_vs_frozen_frank": absolute_error,
            "generated_c_sha256": diff["generated_c_sha256"],
            "pass": bool(diff["match"]) and absolute_error <= 5e-13,
        })

    failures = [row["fixture"] for row in rows if not row["pass"]]
    report = {
        "schema_version": "1.0",
        "experiment": "ClayCode native compilation of frozen FRANK ActiveAssembly packet_score subsystem",
        "reference_path": str(REFERENCE.relative_to(ROOT)),
        "reference_sha256": sha(REFERENCE.read_bytes()),
        "clay_source": CLAY_SOURCE,
        "clay_source_sha256": sha(CLAY_SOURCE.encode("utf-8")),
        "clay_semantic_hash": typed["semantic_hash"],
        "compiler_version": typed["compiler_version"],
        "rows": rows,
        "failures": failures,
        "pass": not failures,
        "supports": ["APP-09-FRANK-COMPONENT", "CC-WP-13-HARNESS-HANDOFF", "CC-WP-05-EVALUATOR", "CC-WP-06-COMPILER-LOWERING"],
        "counts_as_target_acceptance": False,
        "counts_as_full_work_package_pass": False,
        "scope_guard": "Only the frozen packet_score computation is compiled. ActiveAssembly validation, round(...,12), collections, sorting, conflict preservation, epoch filtering and canonical hashing still require compiler/runtime realization before APP-10/full WP13 closure.",
        "authority_invariant": "FRANK cognitive values remain descriptive; this pure subsystem has no execution authority.",
        "next_required": "Compile the remaining frozen ActiveAssembly data/control/hash surface and rerun this handoff on the Andreas Ubuntu developer system.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "fixtures": len(rows), "failures": failures}))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
