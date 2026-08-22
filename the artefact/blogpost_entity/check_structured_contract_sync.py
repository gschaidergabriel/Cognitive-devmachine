#!/usr/bin/env python3
"""Fail-closed static guard for canonical Clay <-> Python reference contract drift.

The canonical Clay source has already moved to a DB-resident profile plus generic
`inference_generate` boundary. The Python reference runtime/tests may lag, but that lag
must be explicit and must never cause the canonical Clay contract to be rolled backward.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-gap",
        action="store_true",
        help="Report the current convergence gap without returning failure",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve()
    root = here.parents[2]
    clay_path = here.with_name("BLOGPOST_ENTITY.clay")
    runtime_path = root / "tools" / "clay_profile_pipeline_runtime.py"
    tests_path = here.with_name("test_blogpost_entity.py")

    clay = clay_path.read_text(encoding="utf-8")
    runtime = runtime_path.read_text(encoding="utf-8")
    tests = tests_path.read_text(encoding="utf-8")

    signature = re.search(r"fn\s+run\((.*?)\)\s*->\s*Map", clay, re.S)
    run_args = []
    if signature:
        run_args = [item.strip().split(":", 1)[0].strip() for item in signature.group(1).split(",") if item.strip()]

    clay_contract = {
        "run_args": run_args,
        "three_argument_runtime_boundary": run_args == ["entity_db", "source_db", "secret_file"],
        "db_resident_profile_effect": 'effect("pipeline_profile_read"' in clay,
        "generic_inference_effect": 'effect("inference_generate"' in clay,
        "old_profile_load_absent": 'effect("profile_load"' not in clay,
        "old_provider_chat_absent": 'effect("provider_chat_json"' not in clay,
    }

    runtime_contract = {
        "supports_pipeline_profile_read": '"pipeline_profile_read"' in runtime,
        "supports_inference_generate": '"inference_generate"' in runtime,
        "still_contains_profile_load": '"profile_load"' in runtime,
        "still_contains_provider_chat_json": '"provider_chat_json"' in runtime,
    }

    tests_contract = {
        "still_mentions_external_profile_path": "str(profile_path)" in tests,
        "still_constructs_profile_json_file": "write_profile(" in tests,
    }

    canonical_current = all(
        [
            clay_contract["three_argument_runtime_boundary"],
            clay_contract["db_resident_profile_effect"],
            clay_contract["generic_inference_effect"],
            clay_contract["old_profile_load_absent"],
            clay_contract["old_provider_chat_absent"],
        ]
    )
    reference_converged = (
        runtime_contract["supports_pipeline_profile_read"]
        and runtime_contract["supports_inference_generate"]
        and not runtime_contract["still_contains_profile_load"]
        and not runtime_contract["still_contains_provider_chat_json"]
        and not tests_contract["still_mentions_external_profile_path"]
        and not tests_contract["still_constructs_profile_json_file"]
    )

    errors: list[str] = []
    if not canonical_current:
        errors.append("CANONICAL_CLAY_CONTRACT_UNEXPECTED")
    if not reference_converged:
        errors.append("REFERENCE_RUNTIME_NOT_CONVERGED")

    report = {
        "schema": "clay-structured-contract-sync/v1",
        "canonical_clay": clay_contract,
        "python_reference_runtime": runtime_contract,
        "python_reference_tests": tests_contract,
        "canonical_current_contract_detected": canonical_current,
        "reference_converged": reference_converged,
        "policy": "Canonical Clay DB-resident profile + inference_generate semantics are forward authority; update the reference runtime/tests to match rather than rolling Clay backward.",
        "errors": errors,
        "pass": not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors and not args.allow_gap:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
