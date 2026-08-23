#!/usr/bin/env python3
"""Fail closed when ClayVerse product authority or inherited safety fences disagree."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

OWNER_DIRECTIVE = "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md"
EXPECTED_PROGRAM = "CLAYVERSE_SINGLE_CONTAINER"
EXPECTED_STAGE = "CLAYVERSE_ARTIFACT"
EXPECTED_RELEASE = "ONE_OCI_DOCKER_COMPATIBLE_CONTAINER_IMAGE"
IDENTITY_GUARD = "research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md"
CONTROL44 = "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_4_CLAYVERSE_PRODUCT_AUTHORITY.json"
STEERING844 = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_44.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def require(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def validate(root: Path) -> dict:
    errors: list[str] = []
    paths = {
        "canonical": root / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json",
        "bootstrap": root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        "program": root / "research_entity/rooms/PROGRAM_STATE.json",
        "directive": root / OWNER_DIRECTIVE,
        "fast_boot": root / "research_entity/continuity/CLAYVERSE_FAST_BOOTSTRAP_SOURCE_CURRENT.md",
        "footer": root / "research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md",
        "manifest": root / "the artefact/manifest.json",
        "architecture": root / "the artefact/ARCHITECTURE.md",
        "readme": root / "the artefact/README.md",
        "root_claude": root / "CLAUDE.md",
        "control44": root / CONTROL44,
        "steering844": root / STEERING844,
    }
    for name, path in paths.items():
        require(errors, path.is_file(), f"MISSING:{name}:{path.as_posix()}")
    if errors:
        return {"schema": "CLAYVERSE_AUTHORITY_CONSISTENCY/v3", "pass": False, "errors": errors}

    try:
        canonical = load_json(paths["canonical"])
        bootstrap = load_json(paths["bootstrap"])
        program = load_json(paths["program"])
        manifest = load_json(paths["manifest"])
        control = load_json(paths["control44"])
        steering = load_json(paths["steering844"])
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": "CLAYVERSE_AUTHORITY_CONSISTENCY/v3",
            "pass": False,
            "errors": [f"JSON_LOAD_ERROR:{type(exc).__name__}:{exc}"],
        }

    directive = paths["directive"].read_text(encoding="utf-8")
    fast_boot = paths["fast_boot"].read_text(encoding="utf-8")
    footer = paths["footer"].read_text(encoding="utf-8")
    architecture = paths["architecture"].read_text(encoding="utf-8")
    readme = paths["readme"].read_text(encoding="utf-8")
    root_claude = paths["root_claude"].read_text(encoding="utf-8")

    # Preserve the older canonical research-entity join/identity fences while changing product authority.
    require(errors, bootstrap.get("entity_id") == canonical.get("entity_id"), "BOOTSTRAP_CANONICAL_ENTITY_MISMATCH")
    require(errors, bootstrap.get("expected_entity_version") == canonical.get("entity_version"), "BOOTSTRAP_CANONICAL_VERSION_MISMATCH")
    require(errors, bootstrap.get("expected_revision") == canonical.get("revision"), "BOOTSTRAP_CANONICAL_REVISION_MISMATCH")
    require(errors, bootstrap.get("expected_state_hash") == canonical.get("state_hash"), "BOOTSTRAP_CANONICAL_STATE_HASH_MISMATCH")
    require(errors, (bootstrap.get("identity") or {}).get("every_turn_guard") == IDENTITY_GUARD, "BOOTSTRAP_IDENTITY_GUARD_POINTER_MISSING")
    require(errors, "every substantive prompt_run_id" in str((bootstrap.get("per_turn") or {}).get("identity_injection", "")), "BOOTSTRAP_PER_TURN_IDENTITY_INJECTION_MISSING")
    invariants = "\n".join(str(x) for x in bootstrap.get("mandatory_invariants", []))
    require(errors, "every substantive prompt_run_id refreshes the Research Entity identity injection" in invariants, "BOOTSTRAP_IDENTITY_INVARIANT_MISSING")

    require(errors, bootstrap.get("active_program") == EXPECTED_PROGRAM, "BOOTSTRAP_ACTIVE_PROGRAM_MISMATCH")
    require(errors, bootstrap.get("active_stage") == EXPECTED_STAGE, "BOOTSTRAP_STAGE_MISMATCH")
    require(errors, bootstrap.get("sole_owner_directive") == OWNER_DIRECTIVE, "BOOTSTRAP_OWNER_DIRECTIVE_MISMATCH")
    require(errors, bootstrap.get("product_endpoint") == "ClayVerse", "BOOTSTRAP_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, bootstrap.get("release_form") == EXPECTED_RELEASE, "BOOTSTRAP_RELEASE_FORM_MISMATCH")
    require(errors, bootstrap.get("together_api") == "FORBIDDEN", "BOOTSTRAP_TOGETHER_FENCE_MISSING")
    require(errors, bootstrap.get("vps_testing") == "FORBIDDEN", "BOOTSTRAP_VPS_TEST_FENCE_MISSING")

    require(errors, program.get("program_id") == "clayverse-single-container", "PROGRAM_ID_MISMATCH")
    require(errors, program.get("stage") == EXPECTED_STAGE and program.get("current_stage") == EXPECTED_STAGE, "PROGRAM_STAGE_MISMATCH")
    require(errors, program.get("owner_directive") == OWNER_DIRECTIVE, "PROGRAM_OWNER_DIRECTIVE_MISMATCH")
    require(errors, program.get("product_endpoint") == "ClayVerse", "PROGRAM_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, program.get("release_form") == EXPECTED_RELEASE, "PROGRAM_RELEASE_FORM_MISMATCH")
    execution = program.get("execution_policy") or {}
    require(errors, execution.get("free_only") is True, "PROGRAM_FREE_ONLY_MISSING")
    require(errors, execution.get("isolated_sandbox_only") is True, "PROGRAM_ISOLATED_ONLY_MISSING")
    require(errors, execution.get("vps_testing_forbidden") is True, "PROGRAM_VPS_TEST_FENCE_MISSING")
    require(errors, execution.get("together_forbidden") is True, "PROGRAM_TOGETHER_FENCE_MISSING")

    require(errors, manifest.get("artifact") == "ClayVerse", "MANIFEST_ARTIFACT_MISMATCH")
    require(errors, manifest.get("product_endpoint") == "ClayVerse", "MANIFEST_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, manifest.get("release_form") == EXPECTED_RELEASE, "MANIFEST_RELEASE_FORM_MISMATCH")
    require(errors, manifest.get("canonical_workspace") == "the artefact/", "MANIFEST_WORKSPACE_MISMATCH")

    override = control.get("program_identity_override") or {}
    hard = control.get("preserved_hard_rules") or {}
    require(errors, control.get("status") == "ACTIVE", "CONTROL44_NOT_ACTIVE")
    require(errors, override.get("active_program") == EXPECTED_PROGRAM, "CONTROL44_PROGRAM_MISMATCH")
    require(errors, override.get("target_stage") == EXPECTED_STAGE, "CONTROL44_STAGE_MISMATCH")
    require(errors, override.get("product_endpoint") == "ClayVerse", "CONTROL44_ENDPOINT_MISMATCH")
    require(errors, override.get("release_form") == EXPECTED_RELEASE, "CONTROL44_RELEASE_MISMATCH")
    require(errors, hard.get("free_only") is True and hard.get("paid_fallback") is False, "CONTROL44_FREE_ONLY_WEAKENED")
    require(errors, hard.get("together_forbidden") is True, "CONTROL44_TOGETHER_WEAKENED")
    require(errors, hard.get("vps_testing") is False, "CONTROL44_VPS_TEST_WEAKENED")
    require(errors, hard.get("runtime_credit_requires_exact_admitted_isolated_execution") is True, "CONTROL44_RUNTIME_EVIDENCE_WEAKENED")

    require(errors, steering.get("program") == EXPECTED_PROGRAM and steering.get("stage") == EXPECTED_STAGE, "STEERING844_PROGRAM_STAGE_MISMATCH")
    require(errors, str(steering.get("effective_control", "")).endswith("4.4-clayverse-product-authority-addendum"), "STEERING844_CONTROL44_NOT_EFFECTIVE")
    adjudication = steering.get("adjudication") or {}
    require(errors, adjudication.get("free_only") is True and adjudication.get("together_forbidden") is True and adjudication.get("vps_testing") is False, "STEERING844_SAFETY_WEAKENED")

    directive_upper = directive[:1200].upper()
    require(errors, "CURRENT OWNER DIRECTIVE" in directive_upper, "DIRECTIVE_NOT_CURRENT")
    require(errors, "SUPERSEDED" not in directive_upper[:220], "DIRECTIVE_MARKED_SUPERSEDED")
    require(errors, "ACTIVE CLAYVERSE PROGRAM" in fast_boot.upper(), "FAST_BOOT_NOT_ACTIVE_CLAYVERSE")
    require(errors, "PROGRAM: CLAYVERSE SINGLE-CONTAINER" in footer.upper(), "FOOTER_PROGRAM_MISMATCH")
    require(errors, "STAGE: CLAYVERSE_ARTIFACT" in footer.upper(), "FOOTER_STAGE_MISMATCH")
    require(errors, "CLAYVERSE IS THE PRODUCT ENDPOINT" in architecture.upper(), "ARCHITECTURE_PRODUCT_MISMATCH")

    readme_head = readme[:3000].upper()
    require(errors, "CLAYVERSE SINGLE-CONTAINER PRODUCT" in readme_head, "README_PRODUCT_MISMATCH")
    require(errors, "CLAYVERSE" in readme_head and "ONE OCI/DOCKER-COMPATIBLE" in readme_head, "README_RELEASE_MISMATCH")
    require(errors, not ("CLAYVERSE SINGLE-CONTAINER ENDPOINT" in readme_head and "SUPERSEDED" in readme_head), "README_CLAYVERSE_SUPERSEDED")

    # Root CLAUDE.md is an executable worker steering surface. It must not silently
    # route repository workers back into the superseded Mini Entity program.
    root_claude_upper = root_claude.upper()
    root_claude_head = root_claude_upper[:5000]
    require(errors, "PROGRAM=CLAYVERSE_SINGLE_CONTAINER" in root_claude_head, "CLAUDE_ROOT_PROGRAM_MISMATCH")
    require(errors, "STAGE=CLAYVERSE_ARTIFACT" in root_claude_head, "CLAUDE_ROOT_STAGE_MISMATCH")
    require(errors, OWNER_DIRECTIVE.upper() in root_claude_upper, "CLAUDE_ROOT_OWNER_DIRECTIVE_MISSING")
    require(errors, "ONE OCI/DOCKER-COMPATIBLE CLAYVERSE CONTAINER IMAGE" in root_claude_head, "CLAUDE_ROOT_PRODUCT_ENDPOINT_MISMATCH")
    require(errors, "UNIFIEDDB REMAINS THE SOLE DURABLE CANONICAL" in root_claude_upper, "CLAUDE_ROOT_UNIFIEDDB_AUTHORITY_MISSING")
    require(errors, "TOGETHER API/SERVICE: **FORBIDDEN**" in root_claude_upper, "CLAUDE_ROOT_TOGETHER_FENCE_MISSING")
    require(errors, "PROGRAM=MINI_ENTITY_PIPELINE_ALL_IN_ONE" not in root_claude_upper, "CLAUDE_ROOT_STALE_MINI_ENTITY_AUTHORITY")
    require(errors, "REPOSITORY-WORKER INSTRUCTION ONLY" in root_claude_upper, "CLAUDE_ROOT_RUNTIME_MEMORY_SCOPE_MISSING")

    return {
        "schema": "CLAYVERSE_AUTHORITY_CONSISTENCY/v3",
        "pass": not errors,
        "errors": errors,
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
