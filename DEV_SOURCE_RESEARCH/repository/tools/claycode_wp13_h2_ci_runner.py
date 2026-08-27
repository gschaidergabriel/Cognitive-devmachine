#!/usr/bin/env python3
"""Execute WP13 H2 differential and always materialize a CI execution receipt."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_H2_CI_EXECUTION.json"
DETAIL = ROOT / "research_entity/claycode/autonomous/FRANK_ACTIVE_ASSEMBLY_H2_RECEIPT.json"


def main() -> int:
    cp = subprocess.run(
        [sys.executable, "tools/claycode_wp13_active_assembly_h2.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=300,
    )
    detail = None
    if DETAIL.exists():
        try:
            detail = json.loads(DETAIL.read_text(encoding="utf-8"))
        except Exception:
            detail = None
    report = {
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "command": [sys.executable, "tools/claycode_wp13_active_assembly_h2.py"],
        "returncode": cp.returncode,
        "stdout_tail": cp.stdout[-50000:],
        "stderr_tail": cp.stderr[-50000:],
        "detail_receipt_present": detail is not None,
        "detail_pass": detail.get("pass") if isinstance(detail, dict) else None,
        "pass": cp.returncode == 0 and isinstance(detail, dict) and detail.get("pass") is True,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "returncode": cp.returncode, "output": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
