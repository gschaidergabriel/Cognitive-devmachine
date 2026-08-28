#!/usr/bin/env python3
"""Assert the current 2026-08-23 ClayVerse sandbox-only execution authority."""
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
VERCEL_EXECUTION_PATH = "research_entity/continuity/VERCEL_SANDBOX_EXECUTION_PATH_CURRENT.md"
EXPECTED_SURFACE = "AUTHORIZED_ISOLATED_SANDBOX_ONLY"
EXPECTED_EXECUTION_GATE = "BLOCKED_ON_EXACT_RETAINED_CONTROLLER_READY_REBIND_AND_OWNER_ONE_SHOT_GITHUB_TOKEN_INGRESS"
EXPECTED_VERCEL_BRIDGE = "SANDBOX_ADMISSION_PROVEN_RUNTIME_ONE_SHOT_TOKEN_INGRESS_IMPLEMENTED"
EXPECTED_CONTROLLER_READY_BINDING = "EXACT_RETAINED_CONTROLLER_HEAD_READY_REQUIRED_BEFORE_TOKEN_POST"
EXPECTED_CONTROLLER = "gschaidergabriel/Dr.-Unterweger#810"
CURRENT_OWNER_DIRECTIVE = "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md"
BRIDGE_CANONICAL_CLAUDE_MARKER = "normal interactive claude code"
BRIDGE_ENTITYOS_CONDITIONAL_MARKER = "entityos execution remains conditional"
BRIDGE_RETIRED_PROVIDER_MARKER = "historical mistral/custom-engine acceptance path"
STALE_MANDATORY_PROVIDER_TEXT = "mistral is mandatory for this final test"
STALE_RETIRED_PROBE_TEXT = "final_acceptance_probe.py::run_mistral_acceptance_probe"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def execution_frontier_errors(program: dict, vercel_execution: str) -> list[str]:
    """Cross-bind retained Vercel continuity, current work selection, and product semantics.

    Historical Sandbox admission and one-shot token ingress prove the bridge exists, but they
    do not prove that the current retained controller head is deployed READY. Current work
    selection therefore requires exact controller rebind/READY before the owner-held token POST.
    The continuity record must also preserve current ClayVerse semantics: normal interactive
    Claude Code is canonical cognition, retired Mistral/custom-engine paths remain retired, and
    EntityOS execution remains conditional on explicit admission. This never grants runtime credit.
    """
    errors: list[str] = []
    lower = vercel_execution.lower()
    bridge_proven = (
        "sandbox.create is not the blocker" in lower
        and "runtime one-shot ingress" in lower
        and "github_read_token" in lower
    )
    stage_gate = ((program.get("stage_gates") or {}).get("CLAYVERSE_EXACT_OCI_ACCEPTANCE") or {}).get("status")
    execution = program.get("execution_policy") or {}
    frontier = str(program.get("current_frontier", ""))
    frontier_lower = frontier.lower()
    credit = program.get("runtime_credit") or {}
    program_claims_bridge = (
        stage_gate == EXPECTED_EXECUTION_GATE
        or execution.get("vercel_sandbox_bridge") == EXPECTED_VERCEL_BRIDGE
        or execution.get("execution_frontier_binding") == VERCEL_EXECUTION_PATH
    )

    if program_claims_bridge and not bridge_proven:
        errors.append("VERCEL_EXECUTION_BRIDGE_EVIDENCE_MISSING_OR_DEGRADED")
        require(errors, credit.get("whole_clayverse") == 0, "PROGRAM_VERCEL_BRIDGE_FALSE_RUNTIME_CREDIT")
        return errors
    if not bridge_proven:
        return errors

    require(errors, CURRENT_OWNER_DIRECTIVE.lower() in lower, "VERCEL_BRIDGE_CURRENT_OWNER_DIRECTIVE_MISSING")
    require(errors, BRIDGE_CANONICAL_CLAUDE_MARKER in lower, "VERCEL_BRIDGE_CANONICAL_CLAUDE_PATH_MISSING")
    require(errors, BRIDGE_ENTITYOS_CONDITIONAL_MARKER in lower, "VERCEL_BRIDGE_ENTITYOS_CONDITIONALITY_MISSING")
    require(errors, BRIDGE_RETIRED_PROVIDER_MARKER in lower, "VERCEL_BRIDGE_RETIRED_PROVIDER_TOMBSTONE_MISSING")
    require(errors, STALE_MANDATORY_PROVIDER_TEXT not in lower, "VERCEL_BRIDGE_STALE_MANDATORY_PROVIDER")
    require(errors, STALE_RETIRED_PROBE_TEXT not in lower, "VERCEL_BRIDGE_STALE_RETIRED_PROBE_AUTHORITY")

    require(errors, stage_gate == EXPECTED_EXECUTION_GATE, "PROGRAM_EXECUTION_FRONTIER_STALE_GENERIC_SURFACE_BLOCK")
    require(errors, execution.get("vercel_sandbox_bridge") == EXPECTED_VERCEL_BRIDGE, "PROGRAM_VERCEL_BRIDGE_STATE_MISSING")
    require(errors, execution.get("execution_frontier_binding") == VERCEL_EXECUTION_PATH, "PROGRAM_VERCEL_FRONTIER_BINDING_MISSING")
    require(errors, execution.get("retained_vercel_controller") == EXPECTED_CONTROLLER, "PROGRAM_RETAINED_VERCEL_CONTROLLER_MISSING")
    require(errors, execution.get("vercel_controller_ready_binding") == EXPECTED_CONTROLLER_READY_BINDING, "PROGRAM_VERCEL_CONTROLLER_READY_BINDING_MISSING")
    require(
        errors,
        "rebind" in frontier_lower
        and "ready" in frontier_lower
        and "owner-start" in frontier_lower
        and "github_read_token" in frontier_lower,
        "PROGRAM_CURRENT_FRONTIER_CONTROLLER_READY_AND_TOKEN_SEQUENCE_MISSING",
    )
    require(errors, credit.get("whole_clayverse") == 0, "PROGRAM_VERCEL_BRIDGE_FALSE_RUNTIME_CREDIT")
    return errors


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
        return {"schema": "CLAYVERSE_EXECUTION_BOUNDARY_CONSISTENCY/v3", "pass": False, "errors": errors}

    try:
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        control = load_json(paths["control44"])
        steering = load_json(paths["steering844"])
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": "CLAYVERSE_EXECUTION_BOUNDARY_CONSISTENCY/v3",
            "pass": False,
            "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}:{exc}"],
        }

    sandbox_text = paths["sandbox_directive"].read_text(encoding="utf-8").lower()
    guest_text = paths["vps_guest_directive"].read_text(encoding="utf-8").lower()

    require(errors, "2026-08-23" in sandbox_text, "SANDBOX_DIRECTIVE_CURRENT_OWNER_DATE_MISSING")
    require(errors, "vps testing is **forbidden**" in sandbox_text, "SANDBOX_DIRECTIVE_VPS_BAN_MISSING")
    require(errors, "vps-hosted disposable kvm/vm/microvm/tcg guest testing is **forbidden**" in sandbox_text, "SANDBOX_DIRECTIVE_VPS_GUEST_BAN_MISSING")
    require(errors, "self-hosted vps test runners are **forbidden**" in sandbox_text, "SANDBOX_DIRECTIVE_SELF_HOSTED_BAN_MISSING")
    require(errors, "production/deployment-host testing is **forbidden**" in sandbox_text, "SANDBOX_DIRECTIVE_PRODUCTION_BAN_MISSING")

    require(errors, "**status:** **superseded**" in guest_text, "VPS_GUEST_DIRECTIVE_NOT_SUPERSEDED")
    require(errors, "superseded by the newer owner-directed clayverse bootstrap dated **2026-08-23**" in guest_text, "VPS_GUEST_DIRECTIVE_NEWER_AUTHORITY_MISSING")
    require(errors, "vps-hosted disposable kvm/vm/microvm/tcg guest testing is forbidden" in guest_text, "VPS_GUEST_DIRECTIVE_CURRENT_GUEST_BAN_MISSING")

    require(errors, bootstrap.get("execution_surface") == EXPECTED_SURFACE, "BOOTSTRAP_EXECUTION_SURFACE_MISMATCH")
    require(errors, bootstrap.get("vps_testing") == "FORBIDDEN", "BOOTSTRAP_VPS_BAN_MISSING")
    require(errors, bootstrap.get("vps_disposable_independent_kernel_guest_testing") == "FORBIDDEN", "BOOTSTRAP_VPS_GUEST_BAN_MISSING")
    require(errors, bootstrap.get("self_hosted_vps_test_runners") == "FORBIDDEN", "BOOTSTRAP_SELF_HOSTED_BAN_MISSING")
    require(errors, bootstrap.get("production_host_testing") == "FORBIDDEN", "BOOTSTRAP_PRODUCTION_BAN_MISSING")
    require(errors, VPS_GUEST_DIRECTIVE not in json.dumps(bootstrap, sort_keys=True), "BOOTSTRAP_STALE_VPS_DIRECTIVE_POINTER")

    execution = program.get("execution_policy") or {}
    require(errors, execution.get("isolated_sandbox_only") is True, "PROGRAM_ISOLATED_EXECUTION_MISSING")
    require(errors, execution.get("vps_testing_forbidden") is True, "PROGRAM_VPS_BAN_MISSING")
    require(errors, execution.get("vps_disposable_independent_kernel_guest_testing_admitted") is False, "PROGRAM_VPS_GUEST_REAUTHORIZED")
    require(errors, execution.get("self_hosted_vps_test_runners_forbidden") is True, "PROGRAM_SELF_HOSTED_BAN_MISSING")
    require(errors, execution.get("production_host_testing_forbidden") is True, "PROGRAM_PRODUCTION_BAN_MISSING")
    require(errors, VPS_GUEST_DIRECTIVE not in json.dumps(execution, sort_keys=True), "PROGRAM_STALE_VPS_DIRECTIVE_POINTER")

    vercel_path = root / VERCEL_EXECUTION_PATH
    stage_gate = ((program.get("stage_gates") or {}).get("CLAYVERSE_EXACT_OCI_ACCEPTANCE") or {}).get("status")
    program_claims_vercel = (
        stage_gate == EXPECTED_EXECUTION_GATE
        or execution.get("vercel_sandbox_bridge") == EXPECTED_VERCEL_BRIDGE
        or execution.get("execution_frontier_binding") == VERCEL_EXECUTION_PATH
    )
    if vercel_path.is_file():
        errors.extend(execution_frontier_errors(program, vercel_path.read_text(encoding="utf-8")))
    elif program_claims_vercel:
        errors.append(f"MISSING:vercel_execution:{VERCEL_EXECUTION_PATH}")

    hard = control.get("preserved_hard_rules") or {}
    require(errors, hard.get("vps_testing") is False, "CONTROL44_VPS_BAN_WEAKENED")
    require(errors, hard.get("vps_disposable_independent_kernel_guest_testing") is False, "CONTROL44_VPS_GUEST_REAUTHORIZED")
    require(errors, hard.get("self_hosted_vps_test_runners") is False, "CONTROL44_SELF_HOSTED_REAUTHORIZED")
    require(errors, hard.get("production_host_testing") is False, "CONTROL44_PRODUCTION_REAUTHORIZED")
    require(errors, hard.get("authorized_isolated_sandbox_only") is True, "CONTROL44_SANDBOX_ONLY_FENCE_MISSING")
    require(errors, VPS_GUEST_DIRECTIVE not in json.dumps(control, sort_keys=True), "CONTROL44_STALE_VPS_DIRECTIVE_POINTER")
    require(errors, "4.2 EXECUTION-BOUNDARY" in str(control.get("composition_rule", "")), "CONTROL44_4_2_EXECUTION_BOUNDARY_NOT_PRESERVED")

    adjudication = steering.get("adjudication") or {}
    require(errors, adjudication.get("vps_testing") is False, "STEERING844_VPS_BAN_WEAKENED")
    require(errors, adjudication.get("vps_disposable_independent_kernel_guest_testing") is False, "STEERING844_VPS_GUEST_REAUTHORIZED")
    require(errors, adjudication.get("self_hosted_vps_test_runners") is False, "STEERING844_SELF_HOSTED_REAUTHORIZED")
    require(errors, adjudication.get("production_host_testing") is False, "STEERING844_PRODUCTION_REAUTHORIZED")
    require(errors, adjudication.get("authorized_isolated_sandbox_only") is True, "STEERING844_SANDBOX_ONLY_FENCE_MISSING")
    require(errors, VPS_GUEST_DIRECTIVE not in json.dumps(steering, sort_keys=True), "STEERING844_STALE_VPS_DIRECTIVE_POINTER")

    return {
        "schema": "CLAYVERSE_EXECUTION_BOUNDARY_CONSISTENCY/v3",
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
