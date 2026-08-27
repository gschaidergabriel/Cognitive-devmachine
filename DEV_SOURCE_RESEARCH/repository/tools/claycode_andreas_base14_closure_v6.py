#!/usr/bin/env python3
"""Authoritative ClayCode BASE14 closure entrypoint.

Compatibility fix over v5: the V2 collector's actual structured PASS key is
`target_component_battery_pass`. v5 accidentally looked for `component_gates_pass`,
which would fail closed even after a genuinely green target-component run.

No acceptance condition is weakened: every other v5 process, structured receipt,
ten-application, full-FRANK, strict-acceptance and independent WP14 requirement remains
identical.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import claycode_andreas_base14_closure_v5 as base

_original_file_pass = base.file_pass


def _receipt_key_compat(path: Path, key: str = "pass") -> bool:
    if path == base.COLLECTOR and key == "component_gates_pass":
        return _original_file_pass(path, "target_component_battery_pass")
    return _original_file_pass(path, key)


base.file_pass = _receipt_key_compat

if __name__ == "__main__":
    raise SystemExit(base.main())
