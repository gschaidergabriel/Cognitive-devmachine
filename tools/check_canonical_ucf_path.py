#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def strip_line_comments(source: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in source.splitlines())


def evaluate(source: str) -> dict[str, object]:
    code = strip_line_comments(source)
    markers = {
        "prompt": 'phase("pipeline_build_prompt"',
        "prepare": 'phase("pipeline_cognitive_fabric_prepare"',
        "infer": 'effect("inference_generate"',
        "gate": 'phase("pipeline_gate"',
        "commit": 'phase("pipeline_commit"',
        "finalize": 'phase("pipeline_cognitive_fabric_finalize"',
    }
    positions = {name: code.find(marker) for name, marker in markers.items()}
    ordered = (
        all(v >= 0 for v in positions.values())
        and positions["prompt"] < positions["prepare"] < positions["infer"]
        < positions["gate"] < positions["commit"] < positions["finalize"]
    )

    required_bindings = {
        "inference_from_prepared": 'map_set(infer,"inference",prepared.inference)' in code,
        "system_from_prepared": 'map_set(infer,"system",prepared.system)' in code,
        "user_from_prepared": 'map_set(infer,"user",prepared.user)' in code,
        "packet_digest_to_inference": 'map_set(infer,"inference_packet_digest",prepared.inference_packet_digest)' in code,
        "prepared_to_gate": 'map_set(gate_data,"cognitive_fabric_prepare",prepared)' in code,
        "packet_digest_to_gate": 'map_set(gate_data,"inference_packet_digest",prepared.inference_packet_digest)' in code,
        "prepared_to_commit": 'map_set(commit_data,"cognitive_fabric_prepare",prepared)' in code,
        "packet_digest_to_commit": 'map_set(commit_data,"inference_packet_digest",prepared.inference_packet_digest)' in code,
        "prepared_to_finalize": 'map_set(cognition_finalize_data,"prepared",prepared)' in code,
        "generated_to_finalize": 'map_set(cognition_finalize_data,"generated",generated)' in code,
        "gated_to_finalize": 'map_set(cognition_finalize_data,"gated",gated)' in code,
        "committed_to_finalize": 'map_set(cognition_finalize_data,"committed",committed)' in code,
        "final_receipt_only_from_finalize": 'map_set(result,"cognitive_fabric_receipt_digest",finalized.cognitive_fabric_receipt_digest)' in code,
    }
    forbidden_raw_bypasses = {
        "profile_inference_direct": 'map_set(infer,"inference",profile.inference)' in code,
        "prompt_system_direct": 'map_set(infer,"system",prompt.system)' in code,
        "prompt_user_direct": 'map_set(infer,"user",prompt.user)' in code,
    }
    temporal_false_green = {
        "legacy_single_admit_phase": 'phase("pipeline_cognitive_fabric_admit"' in code,
        "final_receipt_sent_pre_inference": 'map_set(infer,"cognitive_fabric_receipt_digest"' in code,
        "prepared_claims_final_receipt": 'prepared.cognitive_fabric_receipt_digest' in code,
        "final_receipt_authorizes_gate": 'map_set(gate_data,"cognitive_fabric",finalized)' in code,
        "final_receipt_authorizes_commit": 'map_set(commit_data,"cognitive_fabric",finalized)' in code,
    }
    pass_ = (
        ordered
        and all(required_bindings.values())
        and not any(forbidden_raw_bypasses.values())
        and not any(temporal_false_green.values())
    )
    return {
        "schema": "canonical-ucf-path-static/v3",
        "positions": positions,
        "ordered_prompt_prepare_inference_gate_commit_finalize": ordered,
        "required_bindings": required_bindings,
        "forbidden_raw_bypasses": forbidden_raw_bypasses,
        "temporal_false_green": temporal_false_green,
        "pass": pass_,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", default="the artefact/blogpost_entity/BLOGPOST_ENTITY.clay")
    args = parser.parse_args()
    report = evaluate(Path(args.source).read_text(encoding="utf-8"))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
