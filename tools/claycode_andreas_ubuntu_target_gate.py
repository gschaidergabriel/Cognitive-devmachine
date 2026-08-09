#!/usr/bin/env python3
"""Compatibility entrypoint for Andreas Ubuntu ClayCode target diagnostics.

The historical implementation duplicated the complete target evidence battery and pinned
its own WP02 grammar. That made it possible for this legacy/manual path to drift away from
the canonical target collector and the strict acceptance assembler.

This entrypoint now delegates fail-closed to `claycode_base_andreas_target_runner_v2.py`.
The canonical runner reads the sole WP02 grammar selection from
`research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json`, verifies the
registered physical Andreas host, and writes the requested diagnostic receipt. No legacy
V9/V17 grammar selection remains here.

`--allow-dirty-input` is accepted only for CLI compatibility and is intentionally ignored:
the canonical collector remains stricter and will reject a dirty checkout. A compatibility
flag must never weaken release evidence.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "research_entity/claycode/target_receipts/ANDREAS_UBUNTU_BASE_TARGET_GATE.json"
CANONICAL_RUNNER = ROOT / "tools/claycode_base_andreas_target_runner_v2.py"
CONTRACT = ROOT / "research_entity/claycode/base/ANDREAS_UBUNTU_TARGET_RECEIPT_CONTRACT.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--allow-dirty-input",
        action="store_true",
        help="Deprecated compatibility flag. It never weakens the canonical clean-checkout gate.",
    )
    args = ap.parse_args()

    if not CANONICAL_RUNNER.exists() or not CONTRACT.exists():
        print(json.dumps({
            "error": "CANONICAL_TARGET_GATE_DEPENDENCY_MISSING",
            "canonical_runner": str(CANONICAL_RUNNER.relative_to(ROOT)),
            "contract": str(CONTRACT.relative_to(ROOT)),
        }, sort_keys=True))
        return 3

    try:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        selected = (contract.get("wp02_parser_contract") or {}).get("selected_grammar_path")
    except Exception as exc:
        print(json.dumps({"error": "TARGET_CONTRACT_INVALID", "detail": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 3
    if not isinstance(selected, str) or not selected or not (ROOT / selected).exists():
        print(json.dumps({"error": "TARGET_CONTRACT_SELECTED_GRAMMAR_INVALID", "selected": selected}, sort_keys=True))
        return 3

    args.output.parent.mkdir(parents=True, exist_ok=True)
    cp = subprocess.run(
        [sys.executable, str(CANONICAL_RUNNER.relative_to(ROOT)), "--output", str(args.output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    summary = {
        "compatibility_entrypoint": "tools/claycode_andreas_ubuntu_target_gate.py",
        "delegated_to": str(CANONICAL_RUNNER.relative_to(ROOT)),
        "contract": str(CONTRACT.relative_to(ROOT)),
        "selected_wp02_grammar": selected,
        "allow_dirty_input_requested": bool(args.allow_dirty_input),
        "allow_dirty_input_honored": False,
        "returncode": cp.returncode,
        "stdout_tail": cp.stdout[-4000:],
        "stderr_tail": cp.stderr[-4000:],
        "output": str(args.output),
        "authority_invariant": "model output != execution authority",
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return cp.returncode


if __name__ == "__main__":
    raise SystemExit(main())
