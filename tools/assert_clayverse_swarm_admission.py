#!/usr/bin/env python3
"""Classify provider-swarm admission against current ClayVerse authority.

This is a source/control assertion only. It performs no secret lookup and no network I/O.
An existing controller is never treated as admitted merely because the file exists.
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

LEGACY_CONTROLLER_MARKERS = (
    "MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md",
    "[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]",
    "current Mini Entity product",
    "current Mini Entity/EntityOS product boundary",
    "tools/run_free_go_swarm.py",
)


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"CLAYVERSE_SWARM_ADMISSION_FAIL:{path}:NOT_OBJECT")
    return value


def require(condition: bool, code: str) -> None:
    if not condition:
        raise SystemExit(f"CLAYVERSE_SWARM_ADMISSION_FAIL:{code}")


def classify_current_controller(source: str | None) -> tuple[str, tuple[str, ...]]:
    """Return a fail-closed source classification; never mint admission here."""
    if source is None:
        return "MISSING_BLOCKED", ()
    markers = tuple(marker for marker in LEGACY_CONTROLLER_MARKERS if marker in source)
    if markers:
        return "LEGACY_MINI_ENTITY_CONTROLLER_NOT_ADMITTED", markers
    return "UNADMITTED_REQUIRES_CLAYVERSE_CONTROLLER_VALIDATION", ()


def main() -> int:
    boot = load(BOOT)
    control = load(CONTROL)
    contract = CONTRACT.read_text(encoding="utf-8")
    legacy = LEGACY.read_text(encoding="utf-8") if LEGACY.exists() else ""
    current_source = CURRENT.read_text(encoding="utf-8") if CURRENT.exists() else None

    require(boot.get("active_program") == "CLAYVERSE_SINGLE_CONTAINER", "BOOT_PROGRAM")
    require(boot.get("active_stage") == "CLAYVERSE_ARTIFACT", "BOOT_STAGE")
    require(
        boot.get("sole_owner_directive")
        == "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md",
        "BOOT_OWNER",
    )

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

    require(
        "FAIL-CLOSED UNTIL CLAYVERSE CONTROLLER ADMISSION" in contract,
        "MISSING_FAIL_CLOSED_CONTRACT",
    )
    require(
        "LEGACY_MINI_ENTITY_CONTROLLER_NOT_ADMITTED" in contract,
        "LEGACY_CONTROLLER_NOT_MARKED_BLOCKED",
    )
    require(
        "MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md" in legacy,
        "LEGACY_DRIFT_FALSIFIER_DISAPPEARED_REVIEW_REQUIRED",
    )
    require(
        "continuous FREE_ONLY Mini Entity `go` macrocycle" in legacy,
        "LEGACY_PROMPT_DRIFT_FALSIFIER_DISAPPEARED_REVIEW_REQUIRED",
    )

    classification, markers = classify_current_controller(current_source)
    provider_swarm_admitted = False

    # This assertion intentionally cannot promote a controller. A future migration must
    # add a dedicated deterministic controller validator proving the full re-admission
    # gate (authority, macrocycle, prompt provenance and pre-secret/pre-network order).
    # Until then, file existence is never an admission signal.
    require(provider_swarm_admitted is False, "UNVALIDATED_CONTROLLER_WAS_ADMITTED")

    print(
        json.dumps(
            {
                "schema": "CLAYVERSE_SWARM_ADMISSION_ASSERTION/v2",
                "status": "PASS_BLOCKED",
                "current_controller_exists": current_source is not None,
                "current_controller_classification": classification,
                "legacy_markers_observed": list(markers),
                "provider_swarm_admitted": False,
                "legacy_controller": "QUARANTINED",
                "secret_lookup": "NOT_PERFORMED",
                "network": "NOT_PERFORMED",
                "next_gate": "DEDICATED_CLAYVERSE_CONTROLLER_PLUS_DETERMINISTIC_READMISSION_VALIDATOR",
                "credit": "SOURCE_CONTROL_ASSERTION_ONLY_ZERO_PROVIDER_RUNTIME_CREDIT",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
