#!/usr/bin/env python3
"""Fail closed unless provider-swarm admission matches current ClayVerse authority.

This is a source/control assertion only. It performs no secret lookup and no network I/O.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
CONTROL = ROOT / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
CONTRACT = ROOT / "research_entity/continuity/GO_ZERO_FREE_SWARM_TRIGGER_CONTRACT.md"
LEGACY = ROOT / "tools/run_free_go_swarm.py"
CURRENT = ROOT / "tools/run_go_zero_swarm.py"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"CLAYVERSE_SWARM_ADMISSION_FAIL:{path}:NOT_OBJECT")
    return value


def require(condition: bool, code: str) -> None:
    if not condition:
        raise SystemExit(f"CLAYVERSE_SWARM_ADMISSION_FAIL:{code}")


def main() -> int:
    boot = load(BOOT)
    control = load(CONTROL)
    contract = CONTRACT.read_text(encoding="utf-8")
    legacy = LEGACY.read_text(encoding="utf-8") if LEGACY.exists() else ""

    require(boot.get("active_program") == "CLAYVERSE_SINGLE_CONTAINER", "BOOT_PROGRAM")
    require(boot.get("active_stage") == "CLAYVERSE_ARTIFACT", "BOOT_STAGE")
    require(boot.get("sole_owner_directive") == "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md", "BOOT_OWNER")

    hard = control.get("preserved_hard_rules") or {}
    require(control.get("status") == "ACTIVE", "CONTROL44_NOT_ACTIVE")
    require(hard.get("free_only") is True, "FREE_ONLY_WEAKENED")
    require(hard.get("together_forbidden") is True, "TOGETHER_WEAKENED")
    require(hard.get("secret_lookup_before_admission") is False, "SECRET_LOOKUP_BEFORE_ADMISSION")
    require(
        hard.get("legacy_mini_entity_swarm_controller")
        == "FORBIDDEN_UNTIL_CLAYVERSE_PROMPT_AND_AUTHORITY_MIGRATION",
        "LEGACY_SWARM_NOT_QUARANTINED",
    )

    current_exists = CURRENT.exists()
    if not current_exists:
        require("FAIL-CLOSED UNTIL CLAYVERSE CONTROLLER ADMISSION" in contract, "MISSING_FAIL_CLOSED_CONTRACT")
        require("LEGACY_MINI_ENTITY_CONTROLLER_NOT_ADMITTED" in contract, "LEGACY_CONTROLLER_NOT_MARKED_BLOCKED")
        require("MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md" in legacy, "LEGACY_DRIFT_FALSIFIER_DISAPPEARED_REVIEW_REQUIRED")
        require("continuous FREE_ONLY Mini Entity `go` macrocycle" in legacy, "LEGACY_PROMPT_DRIFT_FALSIFIER_DISAPPEARED_REVIEW_REQUIRED")

    print(json.dumps({
        "schema": "CLAYVERSE_SWARM_ADMISSION_ASSERTION/v1",
        "status": "PASS",
        "current_controller_exists": current_exists,
        "provider_swarm_admitted": False if not current_exists else "REQUIRES_SEPARATE_CONTROLLER_VALIDATION",
        "legacy_controller": "QUARANTINED" if not current_exists else "NOT_SELECTED_BY_THIS_ASSERTION",
        "secret_lookup": "NOT_PERFORMED",
        "network": "NOT_PERFORMED",
        "credit": "SOURCE_CONTROL_ASSERTION_ONLY_ZERO_PROVIDER_RUNTIME_CREDIT"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
