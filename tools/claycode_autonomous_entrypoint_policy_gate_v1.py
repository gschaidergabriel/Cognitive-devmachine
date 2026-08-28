#!/usr/bin/env python3
"""Fail-closed source policy for autonomous provider-capable ClayCode entrypoints.

This gate is provider-independent and uses only repository bytes.  It prevents source-level
promotion while any canonical workflow/caller can still reach the legacy provider-capable cycle
without first crossing the current supervisor-inbox authority gate.

It intentionally does NOT claim runtime/provider quiescence.  It only proves source routing.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = "tools/claycode_autonomous_cycle.py"
GUARDED = "tools/claycode_autonomous_cycle_guarded.py"
WORKFLOW = ".github/workflows/claycode-autonomous-research.yml"

# Repository locations that are execution/routing surfaces.  Research prose/receipts are excluded
# because historical mentions are not executable callers.
EXECUTABLE_SUFFIXES = {".py", ".sh", ".yml", ".yaml", ".toml", ".json"}
EXCLUDED_PREFIXES = (
    "research_entity/continuity/",
    "research_entity/trigger_runs/",
    "research_entity/claycode/autonomous/cycles/",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def executable_direct_callers() -> list[str]:
    needle = "claycode_autonomous_cycle.py"
    out: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in EXECUTABLE_SUFFIXES:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel == LEGACY or rel == GUARDED or any(rel.startswith(p) for p in EXCLUDED_PREFIXES):
            continue
        try:
            text = _text(path)
        except OSError:
            continue
        # Ignore comments that merely document the legacy name; require a shell/python-ish
        # execution token around the path/name.
        if needle in text and re.search(
            r"(?:python(?:3)?|runpy\.run_path|exec|subprocess|command:|run:)\s*[^\n]{0,160}claycode_autonomous_cycle\.py",
            text,
            flags=re.IGNORECASE,
        ):
            out.append(rel)
    return sorted(set(out))


def evaluate() -> dict[str, object]:
    legacy = ROOT / LEGACY
    guarded = ROOT / GUARDED
    workflow = ROOT / WORKFLOW
    failures: list[str] = []

    if not legacy.exists():
        failures.append("LEGACY_CYCLE_MISSING")
    if not guarded.exists():
        failures.append("GUARDED_ENTRYPOINT_MISSING")
    if not workflow.exists():
        failures.append("CANONICAL_WORKFLOW_MISSING")

    guarded_text = _text(guarded) if guarded.exists() else ""
    workflow_text = _text(workflow) if workflow.exists() else ""

    # Gate must precede legacy execution in the guarded shim.
    gate_pos = guarded_text.find("check_inbox()")
    run_pos = guarded_text.find("runpy.run_path")
    if gate_pos < 0 or run_pos < 0 or gate_pos > run_pos:
        failures.append("GUARD_NOT_BEFORE_LEGACY_EXECUTION")
    if 'decision.get("admitted") is not True' not in guarded_text:
        failures.append("GUARD_NOT_FAIL_CLOSED")
    if '"provider_calls": 0' not in guarded_text or '"secret_lookups": 0' not in guarded_text:
        failures.append("BLOCKED_PATH_ZERO_BOUNDARY_RECEIPT_MISSING")

    # Canonical workflow must route through the guarded entrypoint and must not directly execute
    # the legacy provider-capable cycle.
    if "claycode_autonomous_cycle_guarded.py" not in workflow_text:
        failures.append("CANONICAL_WORKFLOW_NOT_GUARDED")
    if re.search(r"python(?:3)?\s+tools/claycode_autonomous_cycle\.py", workflow_text):
        failures.append("CANONICAL_WORKFLOW_DIRECT_LEGACY_CALL")

    callers = executable_direct_callers()
    if callers:
        failures.append("OTHER_EXECUTABLE_DIRECT_LEGACY_CALLERS")

    # The legacy file itself is still not authority-safe as a direct CLI because provider imports
    # occur before any current-inbox gate.  Keep that fact explicit instead of accidentally
    # promoting the source policy to whole-entrypoint safety.
    legacy_text = _text(legacy) if legacy.exists() else ""
    direct_cli_quarantined = True
    if legacy_text:
        gate = legacy_text.find("evaluate_provider_authority")
        secret_import = legacy_text.find("from rae_secret_loader import secret_source")
        if gate >= 0 and secret_import >= 0 and gate < secret_import:
            direct_cli_quarantined = False

    return {
        "schema": "CLAYCODE_AUTONOMOUS_ENTRYPOINT_POLICY_GATE/v1",
        "pass": not failures,
        "canonical_workflow_guarded": "CANONICAL_WORKFLOW_NOT_GUARDED" not in failures
        and "CANONICAL_WORKFLOW_DIRECT_LEGACY_CALL" not in failures,
        "other_executable_direct_callers": callers,
        "legacy_direct_cli_quarantined": direct_cli_quarantined,
        "runtime_provider_credit": 0,
        "failures": failures,
    }


def main() -> int:
    result = evaluate()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
