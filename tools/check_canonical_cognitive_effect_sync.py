#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from check_structured_contract_sync import runtime_effect_contract


def evaluate(clay_source: str, runtime_source: str) -> dict[str, object]:
    source_effects = sorted(set(re.findall(r'(?:phase|effect)\("([^"]+)"', clay_source)))
    runtime = runtime_effect_contract(runtime_source)
    allowed = set(runtime.get("allowed_effects", []))
    dispatch = set(runtime.get("dispatch", {}))

    missing_allowed = sorted(effect for effect in source_effects if effect not in allowed)
    missing_dispatch = sorted(effect for effect in source_effects if effect not in dispatch)
    missing_runtime_effects = sorted(set(missing_allowed) | set(missing_dispatch))
    legacy_runtime_effects = sorted(({"profile_load", "provider_chat_json", "pipeline_cognitive_fabric_admit"} & (allowed | dispatch)))

    expected_ucf_gap = [
        "pipeline_cognitive_fabric_finalize",
        "pipeline_cognitive_fabric_prepare",
    ]
    exact_expected_gap = missing_runtime_effects == expected_ucf_gap
    converged = not missing_runtime_effects and not legacy_runtime_effects

    return {
        "schema": "canonical-cognitive-effect-sync/v2",
        "source_effects": source_effects,
        "runtime_allowed_effects": sorted(allowed),
        "runtime_dispatch_effects": sorted(dispatch),
        "missing_allowed": missing_allowed,
        "missing_dispatch": missing_dispatch,
        "missing_runtime_effects": missing_runtime_effects,
        "legacy_runtime_effects": legacy_runtime_effects,
        "exact_expected_ucf_gap": exact_expected_gap,
        "converged": converged,
        "policy": "Every literal effect/phase in canonical BLOGPOST_ENTITY.clay must be both allowlisted and executable-dispatched by the single ProfilePipelineRuntime; the two missing UCF temporal phases are explicit blockers, never silently bypassed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-gap", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    clay = (root / "the artefact" / "blogpost_entity" / "BLOGPOST_ENTITY.clay").read_text(encoding="utf-8")
    runtime = (root / "tools" / "clay_profile_pipeline_runtime.py").read_text(encoding="utf-8")
    report = evaluate(clay, runtime)
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["converged"] or args.allow_gap:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
