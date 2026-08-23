#!/usr/bin/env python3
"""Static fail-closed source admission for the ClayVerse go/zero provider swarm.

This gate performs no provider/key/network access. It exists to make the current
quarantine executable: stale Mini Entity orchestration must be rejected before a
controller is allowed to look up provider credentials.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_PROGRAM = "CLAYVERSE_SINGLE_CONTAINER"
EXPECTED_STAGE = "CLAYVERSE_ARTIFACT"
EXPECTED_PROGRAM_ID = "clayverse-single-container"
OWNER_DIRECTIVE = "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
DEFAULT_CONTROLLER = "tools/run_go_zero_swarm.py"
DEFAULT_BASE_CONTROLLER = "tools/run_free_go_swarm.py"

# These are product-authority strings, not generic historical comments. An admitted
# live controller must not use them as its active prompt/owner/state contract.
FORBIDDEN_ACTIVE_MARKERS = (
    "MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md",
    "[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]",
    "current Mini Entity",
    "MiniUnifiedDB",
    "current Mini Entity/EntityOS product boundary",
)

REQUIRED_CONTROLLER_MARKERS = (
    "CLAYVERSE_AUTHORITY_GUARD_BEFORE_SECRET_LOOKUP",
    "CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md",
    "[CLAYVERSE :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]",
    "macrocycle_id",
    "unusual_experiment",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        value = json.load(fh)
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def require(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def validate(
    root: Path,
    controller_rel: str = DEFAULT_CONTROLLER,
    base_controller_rel: str = DEFAULT_BASE_CONTROLLER,
) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    paths = {
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "control44": root / CONTROL44,
        "controller": root / controller_rel,
        "base_controller": root / base_controller_rel,
    }
    for name, path in paths.items():
        require(errors, path.is_file(), f"MISSING:{name}:{path.as_posix()}")
    if errors:
        return {"schema": "CLAYVERSE_SWARM_SOURCE_ADMISSION/v1", "pass": False, "errors": errors}

    try:
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        control = load_json(paths["control44"])
        controller = paths["controller"].read_text(encoding="utf-8")
        base_controller = paths["base_controller"].read_text(encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "schema": "CLAYVERSE_SWARM_SOURCE_ADMISSION/v1",
            "pass": False,
            "errors": [f"LOAD_ERROR:{type(exc).__name__}:{exc}"],
        }

    # Current owner/product authority must agree before source admission is considered.
    require(errors, bootstrap.get("active_program") == EXPECTED_PROGRAM, "BOOTSTRAP_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == EXPECTED_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("sole_owner_directive") == OWNER_DIRECTIVE, "BOOTSTRAP_OWNER_DIRECTIVE_MISMATCH")
    require(errors, bootstrap.get("together_api") == "FORBIDDEN", "BOOTSTRAP_TOGETHER_FENCE_MISSING")
    require(errors, bootstrap.get("vps_testing") == "FORBIDDEN", "BOOTSTRAP_VPS_FENCE_MISSING")

    require(errors, program.get("program_id") == EXPECTED_PROGRAM_ID, "PROGRAM_ID_MISMATCH")
    require(errors, program.get("stage") == EXPECTED_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("owner_directive") == OWNER_DIRECTIVE, "PROGRAM_OWNER_DIRECTIVE_MISMATCH")
    execution = program.get("execution_policy") or {}
    require(errors, execution.get("free_only") is True, "PROGRAM_FREE_ONLY_MISSING")
    require(errors, execution.get("together_forbidden") is True, "PROGRAM_TOGETHER_FENCE_MISSING")
    require(errors, execution.get("vps_testing_forbidden") is True, "PROGRAM_VPS_FENCE_MISSING")
    require(errors, execution.get("isolated_sandbox_only") is True, "PROGRAM_ISOLATED_ONLY_MISSING")

    override = control.get("program_identity_override") or {}
    hard = control.get("preserved_hard_rules") or {}
    require(errors, control.get("status") == "ACTIVE", "CONTROL44_NOT_ACTIVE")
    require(errors, override.get("active_program") == EXPECTED_PROGRAM, "CONTROL44_PROGRAM_MISMATCH")
    require(errors, override.get("target_stage") == EXPECTED_STAGE, "CONTROL44_STAGE_MISMATCH")
    require(errors, hard.get("free_only") is True and hard.get("paid_fallback") is False, "CONTROL44_FREE_ONLY_WEAKENED")
    require(errors, hard.get("together_forbidden") is True, "CONTROL44_TOGETHER_WEAKENED")
    require(errors, hard.get("vps_testing") is False, "CONTROL44_VPS_WEAKENED")
    require(
        errors,
        hard.get("runtime_credit_requires_exact_admitted_isolated_execution") is True,
        "CONTROL44_RUNTIME_EVIDENCE_WEAKENED",
    )

    # The exact executable source must explicitly bind ClayVerse before any future
    # secret lookup. Presence of the sentinel is an admission contract, not proof of
    # runtime execution; tests must also verify its control-flow placement when migrated.
    combined = controller + "\n" + base_controller
    for marker in REQUIRED_CONTROLLER_MARKERS:
        require(errors, marker in controller, f"CONTROLLER_REQUIRED_MARKER_MISSING:{marker}")
    for marker in FORBIDDEN_ACTIVE_MARKERS:
        require(errors, marker not in combined, f"LEGACY_MINI_ENTITY_ACTIVE_MARKER:{marker}")

    # Coordination/secret-safety source invariants retained from the old controller.
    require(errors, "key_fingerprint" in combined, "KEY_FINGERPRINT_COORDINATION_MISSING")
    require(
        errors,
        "HTTP_429_PROVIDER_COOLDOWN" in controller or "status == 429" in combined,
        "HTTP429_COOLDOWN_CONTRACT_MISSING",
    )
    require(errors, "status == 402" in combined, "HTTP402_HARD_STOP_CONTRACT_MISSING")
    require(
        errors,
        'child_trigger="go"' in controller or '"child_trigger": "go"' in controller,
        "CHILD_GO_PROPAGATION_MISSING",
    )

    return {
        "schema": "CLAYVERSE_SWARM_SOURCE_ADMISSION/v1",
        "pass": not errors,
        "errors": errors,
        "controller": controller_rel,
        "base_controller": base_controller_rel,
        "credit": "SOURCE_ADMISSION_ONLY_ZERO_PROVIDER_RUNTIME_CREDIT",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--controller", default=DEFAULT_CONTROLLER)
    parser.add_argument("--base-controller", default=DEFAULT_BASE_CONTROLLER)
    args = parser.parse_args()
    result = validate(Path(args.repo_root), args.controller, args.base_controller)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
