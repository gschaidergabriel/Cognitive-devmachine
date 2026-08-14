#!/usr/bin/env python3
"""Run the WP03 typed-IR gate and always write a machine-readable execution receipt."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_entity/claycode/autonomous/WP03_CI_EXECUTION_RECEIPT.json"
GRAMMAR = "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"


def run(name: str, cmd: list[str]) -> dict:
    try:
        cp = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=180)
        return {
            "name": name,
            "command": cmd,
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-30000:],
            "stderr_tail": cp.stderr[-30000:],
            "pass": cp.returncode == 0,
        }
    except Exception as exc:
        return {"name": name, "command": cmd, "pass": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    stages = [
        run("strict_v7", [
            sys.executable, "tools/claycode_strict_lalr_probe.py",
            "--grammar", GRAMMAR,
            "--output", "research_entity/claycode/autonomous/WP03_STRICT_V7_DEPENDENCY_RECEIPT.json",
        ]),
        run("typed_ir_validation", [sys.executable, "tools/claycode_wp03_typed_ir_validation.py"]),
        run("materialize_full_ir", [
            sys.executable, "tools/claycode_base_typed_ir.py",
            "--grammar", GRAMMAR,
            "--output", "research_entity/claycode/autonomous/BASE_TYPED_IR_V1.json",
        ]),
    ]
    overall = all(x.get("pass") for x in stages)
    receipt = {
        "schema_version": "1.0",
        "scope": "CC-WP-03_CI_EXECUTION_OBSERVABILITY",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "actor": {"actor_id": "chatgpt-secondary", "provider": "OpenAI", "model": "GPT-5.6 Sol"},
        "stages": stages,
        "overall_pass": overall,
        "promotion": "NONE_AUTOMATIC",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"overall_pass": overall, "failed": [x["name"] for x in stages if not x.get("pass")], "out": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
