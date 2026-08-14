#!/usr/bin/env python3
"""Aggregate every cloud-safe Full-FRANK semantic proof into one fail-closed receipt.

This gate intentionally cannot create target acceptance.  It executes five independent
host-independent routes that the physical Andreas finalizer later re-runs on target:
  1. H1 -> full structured Clay ActiveAssembly (domain logic visible in Clay source)
  2. H1 -> generic typed-record FFI H2
  3. H1 -> consolidated H3 commutation
  4. frozen packet_score -> typed IR/evaluator/native C11
  5. frozen GRT frame -> block evaluator/lowering trace equivalence

The goal is to distinguish a real semantic/compiler defect from the remaining physical
host-attestation requirement.  Every child result is preserved even on failure.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_entity/claycode/autonomous/FULL_FRANK_CLOUD_SEMANTIC_GATE.json"

STEPS = [
    (
        "STRUCTURED_H2",
        [sys.executable, "tools/claycode_full_frank_active_assembly_validation.py"],
        ROOT / "research_entity/claycode/autonomous/FULL_FRANK_ACTIVE_ASSEMBLY_STRUCTURED_RECEIPT.json",
    ),
    (
        "GENERIC_TYPED_FFI_H2",
        [sys.executable, "tools/claycode_wp13_active_assembly_h2.py"],
        ROOT / "research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_H2_RECEIPT.json",
    ),
    (
        "H3_COMMUTATION",
        [sys.executable, "tools/claycode_wp13_h3_consolidation.py"],
        ROOT / "research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_H3_CONSOLIDATION_RECEIPT.json",
    ),
    (
        "PACKET_SCORE_NATIVE",
        [sys.executable, "tools/claycode_wp13_frank_handoff_validation.py"],
        ROOT / "research_entity/claycode/autonomous/WP13_FRANK_PACKET_SCORE_HANDOFF_RECEIPT.json",
    ),
    (
        "GRT_BLOCK_TOOLCHAIN",
        [sys.executable, "tools/claycode_base_frank_block_toolchain.py"],
        ROOT / "research_entity/claycode/autonomous/FRANK_GRT_BLOCK_TOOLCHAIN_RECEIPT.json",
    ),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"RECEIPT_NOT_OBJECT:{path}")
    return value


def main() -> int:
    rows: list[dict[str, Any]] = []
    for step_id, argv, receipt in STEPS:
        cp = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, check=False, timeout=600)
        row: dict[str, Any] = {
            "step_id": step_id,
            "argv": argv,
            "returncode": cp.returncode,
            "process_pass": cp.returncode == 0,
            "receipt": str(receipt.relative_to(ROOT)),
            "receipt_exists": receipt.exists(),
            "stdout_tail": cp.stdout[-8000:],
            "stderr_tail": cp.stderr[-8000:],
        }
        if receipt.exists():
            row["receipt_sha256"] = sha(receipt)
            try:
                data = read_json(receipt)
                row["receipt_pass"] = data.get("pass") is True
                row["counts_as_target_acceptance"] = data.get("counts_as_target_acceptance")
                row["semantic_escape_hatches"] = data.get("semantic_escape_hatches")
                if step_id == "GENERIC_TYPED_FFI_H2":
                    row["counterexample_disposition"] = data.get("counterexample_disposition")
                    row["language_change_required"] = data.get("language_change_required_by_this_counterexample")
                if step_id == "PACKET_SCORE_NATIVE":
                    row["semantic_mismatches"] = data.get("semantic_mismatches")
                    row["native_mismatches"] = data.get("native_mismatches")
                if step_id == "GRT_BLOCK_TOOLCHAIN":
                    row["trace_equivalent"] = data.get("trace_equivalent")
            except Exception as exc:
                row["receipt_parse_error"] = f"{type(exc).__name__}:{exc}"
        row["pass"] = bool(row["process_pass"] and row.get("receipt_pass") is True)
        rows.append(row)

    by = {row["step_id"]: row for row in rows}
    invariants = {
        "all_five_process_and_receipt_pass": all(row["pass"] for row in rows),
        "structured_h2_no_escape_hatch": by["STRUCTURED_H2"].get("semantic_escape_hatches") in ([], None),
        "generic_h2_resolves_counterexample_without_language_change": (
            by["GENERIC_TYPED_FFI_H2"].get("counterexample_disposition")
            == "IMPLEMENTABLE_VIA_GENERIC_TYPED_FFI_RUNTIME_COLLECTION"
            and by["GENERIC_TYPED_FFI_H2"].get("language_change_required") is False
        ),
        "packet_score_zero_mismatch": (
            by["PACKET_SCORE_NATIVE"].get("semantic_mismatches") == 0
            and by["PACKET_SCORE_NATIVE"].get("native_mismatches") == 0
        ),
        "grt_trace_equivalent": by["GRT_BLOCK_TOOLCHAIN"].get("trace_equivalent") is True,
    }
    overall = all(invariants.values())
    report = {
        "schema_version": "1.0",
        "experiment": "aggregate cloud-safe Full-FRANK semantic/compiler gate",
        "evidence_class": "UBUNTU_GITHUB_ACTIONS_SEMANTIC_PROXY_NOT_PHYSICAL_TARGET_ACCEPTANCE",
        "counts_as_target_acceptance": False,
        "counts_as_wp13_pass": False,
        "steps": rows,
        "invariants": invariants,
        "pass": overall,
        "authority_invariant": "model output != execution authority",
        "remaining_if_pass": [
            "registered physical Andreas Ubuntu target fingerprint attestation",
            "fresh target rerun of the same five semantic routes",
            "hardened ten-application target execution",
            "strict target assembly, WP14 audit and receipt-gated promotion",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": overall, "failed_steps": [r["step_id"] for r in rows if not r["pass"]], "invariants": invariants}, ensure_ascii=False))
    return 0 if overall else 2


if __name__ == "__main__":
    raise SystemExit(main())
