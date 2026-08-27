#!/usr/bin/env python3
"""Fail closed unless provider-swarm admission matches current ClayVerse authority.

Version 1 is deliberately a quarantine assertion, not a controller admission engine.
It performs no secret lookup and no network I/O. The mere presence of a future
controller MUST NOT turn this gate green; a later, separately reviewed validator
must explicitly replace/version this contract before provider execution can be admitted.
"""
from __future__ import annotations

import json
from pathlib import Path

EXPECTED_OWNER = "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md"
EXPECTED_PROGRAM = "CLAYVERSE_SINGLE_CONTAINER"
EXPECTED_STAGE = "CLAYVERSE_ARTIFACT"
LEGACY_BLOCK = "FORBIDDEN_UNTIL_CLAYVERSE_PROMPT_AND_AUTHORITY_MIGRATION"


class AdmissionError(ValueError):
    pass


def _load_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdmissionError(f"LOAD:{path.as_posix()}:{type(exc).__name__}") from exc
    if not isinstance(value, dict):
        raise AdmissionError(f"NOT_OBJECT:{path.as_posix()}")
    return value


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise AdmissionError(code)


def evaluate(root: Path) -> dict:
    root = root.resolve()
    boot_path = root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
    control_path = root / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
    contract_path = root / "research_entity/continuity/GO_ZERO_FREE_SWARM_TRIGGER_CONTRACT.md"
    legacy_path = root / "tools/run_free_go_swarm.py"
    current_path = root / "tools/run_go_zero_swarm.py"

    boot = _load_object(boot_path)
    control = _load_object(control_path)
    try:
        contract = contract_path.read_text(encoding="utf-8")
        legacy = legacy_path.read_text(encoding="utf-8") if legacy_path.exists() else ""
    except OSError as exc:
        raise AdmissionError(f"LOAD:{type(exc).__name__}") from exc

    _require(boot.get("active_program") == EXPECTED_PROGRAM, "BOOT_PROGRAM")
    _require(boot.get("active_stage") == EXPECTED_STAGE, "BOOT_STAGE")
    _require(boot.get("sole_owner_directive") == EXPECTED_OWNER, "BOOT_OWNER")

    hard = control.get("preserved_hard_rules") or {}
    _require(control.get("status") == "ACTIVE", "CONTROL44_NOT_ACTIVE")
    _require(hard.get("free_only") is True, "FREE_ONLY_WEAKENED")
    _require(hard.get("together_forbidden") is True, "TOGETHER_WEAKENED")
    _require(hard.get("secret_lookup_before_admission") is False, "SECRET_LOOKUP_BEFORE_ADMISSION")
    _require(hard.get("legacy_mini_entity_swarm_controller") == LEGACY_BLOCK, "LEGACY_SWARM_NOT_QUARANTINED")

    _require("FAIL-CLOSED UNTIL CLAYVERSE CONTROLLER ADMISSION" in contract, "MISSING_FAIL_CLOSED_CONTRACT")
    _require("LEGACY_MINI_ENTITY_CONTROLLER_NOT_ADMITTED" in contract, "LEGACY_CONTROLLER_NOT_MARKED_BLOCKED")
    _require("MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md" in legacy, "LEGACY_DRIFT_FALSIFIER_DISAPPEARED_REVIEW_REQUIRED")
    _require("continuous FREE_ONLY Mini Entity `go` macrocycle" in legacy, "LEGACY_PROMPT_DRIFT_FALSIFIER_DISAPPEARED_REVIEW_REQUIRED")

    # Critical v1 invariant: file existence is NOT source admission. A previous
    # implementation returned PASS as soon as this path existed without examining
    # the controller. That makes an accidentally copied/renamed stale controller a
    # false green. Keep provider execution blocked until a separately reviewed,
    # versioned controller validator replaces this quarantine-only contract.
    _require(not current_path.exists(), "CURRENT_CONTROLLER_PRESENT_REQUIRES_SEPARATE_VALIDATION")

    return {
        "schema": "CLAYVERSE_SWARM_ADMISSION_ASSERTION/v2",
        "status": "PASS",
        "gate_mode": "QUARANTINE_ONLY",
        "current_controller_exists": False,
        "provider_swarm_admitted": False,
        "legacy_controller": "QUARANTINED",
        "future_controller_admission": "REQUIRES_SEPARATE_VERSIONED_VALIDATOR",
        "secret_lookup": "NOT_PERFORMED",
        "network": "NOT_PERFORMED",
        "credit": "SOURCE_CONTROL_ASSERTION_ONLY_ZERO_PROVIDER_RUNTIME_CREDIT",
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        result = evaluate(root)
    except AdmissionError as exc:
        print(json.dumps({
            "schema": "CLAYVERSE_SWARM_ADMISSION_ASSERTION/v2",
            "status": "FAIL_CLOSED",
            "provider_swarm_admitted": False,
            "error": str(exc),
            "secret_lookup": "NOT_PERFORMED",
            "network": "NOT_PERFORMED",
            "credit": "ZERO_PROVIDER_RUNTIME_CREDIT",
        }, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
