#!/usr/bin/env python3
"""Fail-closed source admission for the ClayVerse go/zero provider swarm.

This tool never reads provider secrets and never performs network I/O.  It has two
separate jobs:

1. assert that current ClayVerse authority still requires the legacy swarm to stay
   quarantined unless a controller is positively source-admitted;
2. report whether the current controller is actually source-admitted.

A safety/assertion PASS is therefore not the same thing as provider-swarm admission.
Use ``--require-admitted`` at an execution boundary that intends to touch keys/network.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM = ROOT / "research_entity/rooms/PROGRAM_STATE.json"
CONTROL = ROOT / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
CONTRACT = ROOT / "research_entity/continuity/GO_ZERO_FREE_SWARM_TRIGGER_CONTRACT.md"
PROTOCOL = ROOT / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md"
LEGACY = ROOT / "tools/run_free_go_swarm.py"
CURRENT = ROOT / "tools/run_go_zero_swarm.py"

OWNER_DIRECTIVE = "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md"
CLAYVERSE_PROTOCOL = "[CLAYVERSE :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"
LEGACY_PROTOCOL = "[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"
PRESECRET_GUARD_CALL = "assert_clayverse_swarm_admission.py"
REQUIRE_ADMITTED_ARG = "--require-admitted"

LEGACY_ACTIVE_MARKERS = (
    "MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md",
    LEGACY_PROTOCOL,
    "current Mini Entity",
    "MiniUnifiedDB",
    "current Mini Entity/EntityOS product boundary",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"NOT_OBJECT:{path}")
    return value


def inspect(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    paths = {
        "boot": root / BOOT.relative_to(ROOT),
        "program": root / PROGRAM.relative_to(ROOT),
        "control": root / CONTROL.relative_to(ROOT),
        "contract": root / CONTRACT.relative_to(ROOT),
        "protocol": root / PROTOCOL.relative_to(ROOT),
        "legacy": root / LEGACY.relative_to(ROOT),
        "current": root / CURRENT.relative_to(ROOT),
    }
    missing_required = [name for name in ("boot", "program", "control", "contract", "protocol") if not paths[name].is_file()]
    if missing_required:
        return {
            "schema": "CLAYVERSE_SWARM_ADMISSION_ASSERTION/v2",
            "assertion_pass": False,
            "provider_swarm_admitted": False,
            "authority_errors": [f"MISSING_REQUIRED:{name}" for name in missing_required],
            "admission_errors": ["AUTHORITY_UNRESOLVED"],
        }

    try:
        boot = load(paths["boot"])
        program = load(paths["program"])
        control = load(paths["control"])
        contract = paths["contract"].read_text(encoding="utf-8")
        protocol = paths["protocol"].read_text(encoding="utf-8")
        legacy = paths["legacy"].read_text(encoding="utf-8") if paths["legacy"].exists() else ""
        current = paths["current"].read_text(encoding="utf-8") if paths["current"].exists() else ""
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "schema": "CLAYVERSE_SWARM_ADMISSION_ASSERTION/v2",
            "assertion_pass": False,
            "provider_swarm_admitted": False,
            "authority_errors": [f"LOAD_ERROR:{type(exc).__name__}:{exc}"],
            "admission_errors": ["AUTHORITY_UNRESOLVED"],
        }

    authority_errors: list[str] = []
    hard = control.get("preserved_hard_rules") or {}
    execution = program.get("execution_policy") or {}

    def authority(ok: bool, code: str) -> None:
        if not ok:
            authority_errors.append(code)

    authority(boot.get("active_program") == "CLAYVERSE_SINGLE_CONTAINER", "BOOT_PROGRAM")
    authority(boot.get("active_stage") == "CLAYVERSE_ARTIFACT", "BOOT_STAGE")
    authority(boot.get("sole_owner_directive") == OWNER_DIRECTIVE, "BOOT_OWNER")
    authority(program.get("program_id") == "clayverse-single-container", "PROGRAM_ID")
    authority(program.get("stage") == "CLAYVERSE_ARTIFACT", "PROGRAM_STAGE")
    authority(program.get("owner_directive") == OWNER_DIRECTIVE, "PROGRAM_OWNER")
    authority(execution.get("free_only") is True, "PROGRAM_FREE_ONLY")
    authority(execution.get("isolated_sandbox_only") is True, "PROGRAM_ISOLATED_ONLY")
    authority(execution.get("together_forbidden") is True, "PROGRAM_TOGETHER")
    authority(execution.get("vps_testing_forbidden") is True, "PROGRAM_VPS")
    authority(control.get("status") == "ACTIVE", "CONTROL44_NOT_ACTIVE")
    authority(hard.get("free_only") is True and hard.get("paid_fallback") is False, "FREE_ONLY_WEAKENED")
    authority(hard.get("together_forbidden") is True, "TOGETHER_WEAKENED")
    authority(hard.get("secret_lookup_before_admission") is False, "SECRET_LOOKUP_BEFORE_ADMISSION")
    authority(hard.get("vps_testing") is False, "VPS_TESTING_WEAKENED")
    authority(hard.get("runtime_credit_requires_exact_admitted_isolated_execution") is True, "RUNTIME_EVIDENCE_WEAKENED")
    authority(
        hard.get("legacy_mini_entity_swarm_controller") == "FORBIDDEN_UNTIL_CLAYVERSE_PROMPT_AND_AUTHORITY_MIGRATION",
        "LEGACY_SWARM_NOT_QUARANTINED",
    )
    authority("FAIL-CLOSED UNTIL CLAYVERSE CONTROLLER ADMISSION" in contract, "MISSING_FAIL_CLOSED_CONTRACT")
    authority("LEGACY_MINI_ENTITY_CONTROLLER_NOT_ADMITTED" in contract, "LEGACY_CONTROLLER_NOT_MARKED_BLOCKED")

    admission_errors: list[str] = []
    if not current:
        admission_errors.append("CURRENT_CONTROLLER_MISSING")
    else:
        # A current controller must positively bind the ClayVerse owner/protocol and
        # must invoke this gate in require-admitted mode before its first key collection.
        if OWNER_DIRECTIVE not in current:
            admission_errors.append("CURRENT_CONTROLLER_OWNER_NOT_CLAYVERSE")
        if CLAYVERSE_PROTOCOL not in current:
            admission_errors.append("CURRENT_CONTROLLER_PROTOCOL_NOT_CLAYVERSE")
        if PRESECRET_GUARD_CALL not in current or REQUIRE_ADMITTED_ARG not in current:
            admission_errors.append("CURRENT_CONTROLLER_PRESECRET_ADMISSION_GUARD_MISSING")
        key_lookup = current.find("BASE.collect_keys(")
        guard_call = current.find(PRESECRET_GUARD_CALL)
        if key_lookup >= 0 and (guard_call < 0 or guard_call > key_lookup):
            admission_errors.append("CURRENT_CONTROLLER_GUARD_NOT_BEFORE_KEY_LOOKUP")
        for marker in LEGACY_ACTIVE_MARKERS:
            if marker in current:
                admission_errors.append(f"CURRENT_CONTROLLER_LEGACY_MARKER:{marker}")

    # The loaded worker protocol and base controller are part of the generated prompt/
    # state path. A wrapper cannot be admitted while these still inject Mini Entity as
    # current authority.
    if CLAYVERSE_PROTOCOL not in protocol:
        admission_errors.append("WORKER_PROTOCOL_CLAYVERSE_MARKER_MISSING")
    if LEGACY_PROTOCOL in protocol:
        admission_errors.append("WORKER_PROTOCOL_LEGACY_MARKER_ACTIVE")
    for marker in LEGACY_ACTIVE_MARKERS:
        if marker in legacy:
            admission_errors.append(f"BASE_CONTROLLER_LEGACY_MARKER:{marker}")

    admitted = not authority_errors and not admission_errors
    assertion_pass = not authority_errors
    if not assertion_pass:
        status = "FAIL_AUTHORITY_UNRESOLVED"
    elif admitted:
        status = "PASS_CONTROLLER_SOURCE_ADMITTED"
    else:
        status = "PASS_QUARANTINE_ENFORCED"

    return {
        "schema": "CLAYVERSE_SWARM_ADMISSION_ASSERTION/v2",
        "status": status,
        "assertion_pass": assertion_pass,
        "provider_swarm_admitted": admitted,
        "authority_errors": authority_errors,
        "admission_errors": admission_errors,
        "current_controller_exists": bool(current),
        "legacy_controller_present": bool(legacy),
        "secret_lookup": "NOT_PERFORMED",
        "network": "NOT_PERFORMED",
        "credit": "SOURCE_CONTROL_ASSERTION_ONLY_ZERO_PROVIDER_RUNTIME_CREDIT",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--require-admitted", action="store_true")
    args = parser.parse_args()
    result = inspect(Path(args.repo_root))
    print(json.dumps(result, sort_keys=True))
    if not result["assertion_pass"]:
        return 2
    if args.require_admitted and not result["provider_swarm_admitted"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
