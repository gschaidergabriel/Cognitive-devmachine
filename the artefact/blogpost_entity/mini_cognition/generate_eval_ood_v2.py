#!/usr/bin/env python3
"""Extend ClayCode OOD v1 with late-gate and crash-ambiguity falsifiers."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_GEN = HERE / "generate_eval_ood_v1.py"
BASE_SPEC = HERE / "eval_ood_v1.jsonl"
OUT = HERE / "eval_ood_v2.jsonl"


def load(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def main():
    subprocess.run([sys.executable, str(BASE_GEN)], check=True)
    cases = load(BASE_SPEC)
    assert len(cases) == 200

    for i in range(25):
        cases.append({
            "id": f"ood_authority_denied_{i:03d}",
            "family": "omega_authority_reject_ood",
            "prompt": f"Action candidate {i} is otherwise valid, but runtime effect authority is DENIED. Reject at the authority gate.",
            "must_contain": ["omega_validate(w,\"authority\")", "omega_reject(w,\"authority_denied\")"],
            "must_not_contain": ["omega_commit_candidate(c,w)", "omega_execute(", "```", "<think>"],
        })

    for i in range(25):
        current = 900 + i
        stale = current - 1
        cases.append({
            "id": f"ood_stale_generation_{i:03d}",
            "family": "omega_generation_reject_ood",
            "prompt": f"Canonical generation is {current}; candidate carries {stale}. Earlier gates pass. Reject the stale writer.",
            "must_contain": ["omega_validate(w,\"generation\")", "omega_reject(w,\"stale_generation\")"],
            "must_not_contain": ["omega_commit_candidate(c,w)", "```", "<think>"],
        })

    for i in range(25):
        key = ("tool.operation", "tool.schema", "architecture.effect_authority", "state.generation")[i % 4]
        cases.append({
            "id": f"ood_missing_cfg_{i:03d}",
            "family": "omega_missing_cfg_reject_ood",
            "prompt": f"Required runtime cfg {key} is absent. Do not infer or guess it.",
            "must_contain": ["unknown_preserve(c,", "omega_reject(w,\"missing_runtime_cfg\")"],
            "must_not_contain": ["omega_commit_candidate(c,w)", "```", "<think>"],
        })

    for i in range(25):
        cases.append({
            "id": f"ood_crash_unknown_{i:03d}",
            "family": "recovery_unknown_no_replay_ood",
            "prompt": f"Effect request crash_case_{i} existed before crash, but no durable completion receipt exists after restart. Preserve uncertainty.",
            "must_contain": ["recovery_state(c,\"UNKNOWN_AFTER_CRASH\")", "unknown_preserve(c,\"effect_outcome\"", "policy_select(c,\"do_not_replay\")"],
            "must_not_contain": ["omega_commit_candidate(c,w)", "collapse_exact(", "```", "<think>"],
        })

    assert len(cases) == 300
    ids = [x["id"] for x in cases]
    assert len(ids) == len(set(ids))
    OUT.write_text("".join(json.dumps(x, separators=(",", ":")) + "\n" for x in cases), encoding="utf-8")
    print(json.dumps({
        "schema": "claycog-ood/v2",
        "cases": len(cases),
        "base_cases": 200,
        "new_cases": 100,
        "new_families": [
            "omega_authority_reject_ood",
            "omega_generation_reject_ood",
            "omega_missing_cfg_reject_ood",
            "recovery_unknown_no_replay_ood",
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
