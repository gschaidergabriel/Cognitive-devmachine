#!/usr/bin/env python3
"""Assert current ClayVerse isolated-execution policy without collapsing VPS host and guest scopes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SANDBOX_DIRECTIVE = "research_entity/global/SANDBOX_ONLY_TEST_EXECUTION_DIRECTIVE.md"
VPS_GUEST_DIRECTIVE = "research_entity/global/VPS_DISPOSABLE_GUEST_TEST_EXECUTION_DIRECTIVE.md"
BOOTSTRAP = "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
PROGRAM = "research_entity/rooms/PROGRAM_STATE.json"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
STEERING844 = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_44.json"
DIRECT_SCOPE = "DIRECT_VPS_HOST_ONLY"
GUEST_ADMISSION = "ADMITTED_SUBJECT_TO_VPS_DISPOSABLE_GUEST_TEST_EXECUTION_DIRECTIVE"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def validate(root: Path) -> dict:
    errors: list[str] = []
    paths = {
        "sandbox_directive": root / SANDBOX_DIRECTIVE,
        "vps_guest_directive": root / VPS_GUEST_DIRECTIVE,
        "bootstrap": root / BOOTSTRAP,
        "program": root / PROGRAM,
        "control44": root / CONTROL44,
        "steering844": root / STEERING844,
    }
    for name, path in paths.items():
        require(errors, path.is_file(), f"MISSING:{name}:{path.as_posix()}")
    if errors:
        return {"schema": "CLAYVERSE_EXECUTION_BOUNDARY_CONSISTENCY/v1", "pass": False, "errors": errors}

    try:
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        control = load_json(paths["control44"])
        steering = load_json(paths["steering844"])
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": "CLAYVERSE_EXECUTION_BOUNDARY_CONSISTENCY/v1",
            "pass": False,
            "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}:{exc}"],
        }

    sandbox_text = paths["sandbox_directive"].read_text(encoding="utf-8").lower()
    guest_text = paths["vps_guest_directive"].read_text(encoding="utf-8").lower()

    # Newest owner law distinguishes forbidden host execution from admitted isolated guests.
    require(
        errors,
        "direct test/build/experiment execution on a vps host remains forbidden" in sandbox_text,
        "SANDBOX_DIRECTIVE_DIRECT_VPS_HOST_BAN_MISSING",
    )
    require(
        errors,
        "freshly created disposable independent-kernel guest test sandbox" in sandbox_text,
        "SANDBOX_DIRECTIVE_DISPOSABLE_GUEST_ADMISSION_MISSING",
    )
    require(
        errors,
        "direct execution of clay/clayverse candidate code on the vps host remains forbidden" in guest_text,
        "VPS_GUEST_DIRECTIVE_HOST_BAN_MISSING",
    )
    require(
        errors,
        "disposable independent-kernel guest" in guest_text,
        "VPS_GUEST_DIRECTIVE_GUEST_CONTRACT_MISSING",
    )

    require(
        errors,
        bootstrap.get("execution_surface") == "AUTHORIZED_ISOLATED_SANDBOX_OR_INDEPENDENT_KERNEL_GUEST_ONLY",
        "BOOTSTRAP_EXECUTION_SURFACE_MISMATCH",
    )
    require(errors, bootstrap.get("vps_testing") == "FORBIDDEN", "BOOTSTRAP_LEGACY_VPS_HOST_BAN_MISSING")
    require(errors, bootstrap.get("vps_testing_scope") == DIRECT_SCOPE, "BOOTSTRAP_VPS_SCOPE_NOT_DIRECT_HOST_ONLY")
    require(
        errors,
        bootstrap.get("vps_disposable_independent_kernel_guest_testing") == GUEST_ADMISSION,
        "BOOTSTRAP_DISPOSABLE_GUEST_ADMISSION_MISSING",
    )
    require(errors, bootstrap.get("vps_execution_directive") == VPS_GUEST_DIRECTIVE, "BOOTSTRAP_VPS_DIRECTIVE_POINTER_MISMATCH")

    execution = program.get("execution_policy") or {}
    require(errors, execution.get("isolated_sandbox_only") is True, "PROGRAM_ISOLATED_EXECUTION_MISSING")
    require(errors, execution.get("vps_testing_forbidden") is True, "PROGRAM_LEGACY_VPS_HOST_BAN_MISSING")
    require(errors, execution.get("vps_testing_forbidden_scope") == DIRECT_SCOPE, "PROGRAM_VPS_SCOPE_NOT_DIRECT_HOST_ONLY")
    require(
        errors,
        execution.get("vps_disposable_independent_kernel_guest_testing_admitted") is True,
        "PROGRAM_DISPOSABLE_GUEST_ADMISSION_MISSING",
    )
    require(errors, execution.get("qemu_tcg_guest_development_evidence_only") is True, "PROGRAM_TCG_SCOPE_WEAKENED")
    require(
        errors,
        execution.get("final_hardware_microvm_credit_requires_hardware_virtualized_guest") is True,
        "PROGRAM_FINAL_MICROVM_GATE_WEAKENED",
    )
    require(errors, execution.get("vps_execution_directive") == VPS_GUEST_DIRECTIVE, "PROGRAM_VPS_DIRECTIVE_POINTER_MISMATCH")

    hard = control.get("preserved_hard_rules") or {}
    require(errors, hard.get("vps_testing") is False, "CONTROL44_DIRECT_VPS_HOST_BAN_WEAKENED")
    require(errors, hard.get("vps_testing_scope") == DIRECT_SCOPE, "CONTROL44_VPS_SCOPE_NOT_DIRECT_HOST_ONLY")
    require(
        errors,
        hard.get("vps_disposable_independent_kernel_guest_testing") is True,
        "CONTROL44_DISPOSABLE_GUEST_ADMISSION_MISSING",
    )
    require(errors, hard.get("qemu_tcg_guest_final_hardware_microvm_credit") is False, "CONTROL44_TCG_FINAL_CREDIT_WEAKENED")
    require(errors, hard.get("vps_execution_directive") == VPS_GUEST_DIRECTIVE, "CONTROL44_VPS_DIRECTIVE_POINTER_MISMATCH")
    require(errors, "4.2 EXECUTION-BOUNDARY" in str(control.get("composition_rule", "")), "CONTROL44_4_2_EXECUTION_BOUNDARY_NOT_PRESERVED")

    adjudication = steering.get("adjudication") or {}
    require(errors, adjudication.get("vps_testing") is False, "STEERING844_DIRECT_VPS_HOST_BAN_WEAKENED")
    require(errors, adjudication.get("vps_testing_scope") == DIRECT_SCOPE, "STEERING844_VPS_SCOPE_NOT_DIRECT_HOST_ONLY")
    require(
        errors,
        adjudication.get("vps_disposable_independent_kernel_guest_testing") is True,
        "STEERING844_DISPOSABLE_GUEST_ADMISSION_MISSING",
    )
    require(errors, adjudication.get("qemu_tcg_guest_final_hardware_microvm_credit") is False, "STEERING844_TCG_FINAL_CREDIT_WEAKENED")

    return {
        "schema": "CLAYVERSE_EXECUTION_BOUNDARY_CONSISTENCY/v1",
        "pass": not errors,
        "errors": errors,
        "credit": "SOURCE_POLICY_ASSERTION_ONLY_ZERO_RUNTIME_CREDIT",
        "checked": {name: path.relative_to(root).as_posix() for name, path in paths.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    result = validate(Path(args.repo_root).resolve())
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
