#!/usr/bin/env python3
"""Deterministic analyzer for Forschungsrun1 blind-robust dual-Qwen results."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any

SCHEMA = "CLAY_FORSCHUNGSRUN1_DUAL_QWEN06_ROBUST_ANALYSIS/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _finite(value: Any, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
        raise ValueError(f"NONFINITE:{name}")
    return float(value)


def analyze(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("schema") != "CLAY_FORSCHUNGSRUN1_DUAL_QWEN06_BLIND_ROBUST/v3":
        raise ValueError("V3_RESULT_REQUIRED")
    frozen = result.get("frozen_best_actions")
    robust = result.get("robust_stats")
    final = result.get("fast_final_eval")
    if not isinstance(frozen, dict) or set(frozen) != set(TARGETS):
        raise ValueError("FROZEN_ACTIONS_INVALID")
    if not isinstance(robust, dict) or not isinstance(final, list) or not final:
        raise ValueError("ROBUST_AND_FINAL_REQUIRED")

    by_target: dict[str, dict[str, Any]] = {}
    all_final = []
    stable_positive_actions: dict[str, list[int]] = {}
    for target in TARGETS:
        action = int(frozen[target])
        key = f"{target}:{action}"
        search = robust.get(key)
        if not isinstance(search, dict):
            raise ValueError(f"FROZEN_SEARCH_STATS_MISSING:{key}")
        final_rows = [r for r in final if r.get("semantic_target") == target]
        if len(final_rows) != 3:
            raise ValueError(f"EXACT_THREE_FINAL_FAMILIES_REQUIRED:{target}")
        final_deltas = [_finite(r.get("delta_vs_baseline"), f"final:{target}") for r in final_rows]
        search_worst = _finite(search.get("worst_family_delta"), f"search_worst:{target}")
        search_median = _finite(search.get("median_family_delta"), f"search_median:{target}")
        search_mean = _finite(search.get("mean_delta"), f"search_mean:{target}")
        final_mean = statistics.fmean(final_deltas)
        final_min = min(final_deltas)
        transfer_sign_agreement = sum((d > 0) == (search_mean > 0) for d in final_deltas) / len(final_deltas)
        by_target[target] = {
            "frozen_action": action,
            "search_worst_family_delta": search_worst,
            "search_median_family_delta": search_median,
            "search_mean_delta": search_mean,
            "final_family_deltas": {str(r["family_id"]): _finite(r["delta_vs_baseline"], "final") for r in final_rows},
            "final_mean_delta": final_mean,
            "final_worst_family_delta": final_min,
            "final_positive_fraction": sum(d > 0 for d in final_deltas) / len(final_deltas),
            "search_to_final_mean_gap": final_mean - search_mean,
            "search_mean_to_final_family_sign_agreement": transfer_sign_agreement,
            "robust_positive_transfer": search_worst > 0 and final_min > 0,
        }
        all_final.extend(final_deltas)
        stable_positive_actions[target] = sorted(
            int(k.split(":", 1)[1]) for k, s in robust.items()
            if k.startswith(target + ":") and isinstance(s, dict)
            and int(s.get("family_count", 0)) >= 3
            and _finite(s.get("worst_family_delta"), f"worst:{k}") > 0
            and int(k.split(":", 1)[1]) != 0
        )

    qwen = result.get("deconfounded_qwen_policy", {})
    bandit = result.get("robust_bandit_comparator", {})
    qmean = qwen.get("mean_delta")
    bmean = bandit.get("mean_delta")
    controller_comparison = {
        "qwen_turns": int(qwen.get("turns", 0)),
        "bandit_turns": int(bandit.get("turns", 0)),
        "qwen_mean_delta": None if qmean is None else _finite(qmean, "qwen_mean"),
        "bandit_mean_delta": None if bmean is None else _finite(bmean, "bandit_mean"),
        "qwen_positive_fraction": qwen.get("positive_fraction"),
        "bandit_positive_fraction": bandit.get("positive_fraction"),
    }
    if controller_comparison["qwen_mean_delta"] is not None and controller_comparison["bandit_mean_delta"] is not None:
        controller_comparison["qwen_minus_bandit_mean_delta"] = controller_comparison["qwen_mean_delta"] - controller_comparison["bandit_mean_delta"]
    else:
        controller_comparison["qwen_minus_bandit_mean_delta"] = None

    stable_targets = [t for t in TARGETS if by_target[t]["robust_positive_transfer"]]
    core = {
        "schema": SCHEMA,
        "source_result_sha256": result.get("result_sha256"),
        "targets": by_target,
        "stable_positive_search_actions": stable_positive_actions,
        "controller_comparison": controller_comparison,
        "global": {
            "final_mean_delta": statistics.fmean(all_final),
            "final_worst_delta": min(all_final),
            "final_positive_fraction": sum(d > 0 for d in all_final) / len(all_final),
            "targets_with_positive_worst_search_and_final": stable_targets,
            "all_targets_robust_positive_transfer": len(stable_targets) == len(TARGETS),
        },
        "interpretation_guard": {
            "full_jspace_control_established": False,
            "native_equivalence_established": False,
            "canonical_semantics_minted": False,
        },
    }
    return {**core, "analysis_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("result")
    ap.add_argument("--output")
    args = ap.parse_args()
    source = json.loads(Path(args.result).read_text(encoding="utf-8"))
    value = analyze(source)
    raw = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        Path(args.output).write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
