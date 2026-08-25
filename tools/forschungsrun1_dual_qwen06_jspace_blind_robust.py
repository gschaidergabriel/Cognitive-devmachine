#!/usr/bin/env python3
"""Forschungsrun 1 v3: robust target-blind dual-Qwen J-Space search.

Successor to blind-cumulative v2. It fixes two runtime-discovered failure modes:
* raw controller digit logits can collapse to a preferred code token (observed baseline/0 policy);
* one-sample action means can overfit a lexical family and reverse sign on fresh families.

The controller now sees a deterministic counterbalanced digit<->action mapping and actions
are selected from evidence-logit minus matched null-prompt logit. Before model policy is
allowed, every target x action is measured once in every SEARCH family. Robust statistics
retain per-family means and worst/median/mean effects. After coverage, model policy and a
non-model robust-bandit comparator alternate. Final actions are frozen by worst-family,
then median, then mean delta before disjoint FINAL families are opened.

Research evidence only; no semantic/J-Space/HCU/EntityOS/canonical credit is minted.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any

from tools import forschungsrun1_dual_qwen06_jspace_blind_cumulative as v2
from tools import forschungsrun1_dual_qwen06_jspace_search as v1
from tools import trigger1_abstract_state_challenge_v1 as challenge_mod
from tools import trigger1_local_qwen06_midlayer_causal_execute as base
from tools import trigger1_local_qwen06_native_semantic_counterbalanced_execute as native

SCHEMA = "CLAY_FORSCHUNGSRUN1_DUAL_QWEN06_BLIND_ROBUST/v3"
TRACE_SCHEMA = "CLAY_FORSCHUNGSRUN1_DUAL_QWEN06_BLIND_ROBUST_TURN/v3"
TARGETS = v2.TARGETS
ACTION_SPECS = v2.ACTION_SPECS
ACTION_COUNT = len(ACTION_SPECS)
DIGITS = tuple(str(i) for i in range(ACTION_COUNT))
TARGET_INDEX = {target: i for i, target in enumerate(TARGETS)}


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def robust_stats(turns: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, Any]]:
    grouped: dict[tuple[str, int, str], list[dict[str, Any]]] = collections.defaultdict(list)
    for row in turns:
        grouped[(str(row["semantic_target"]), int(row["executed_action"]), str(row["family_id"]))].append(row)
    by_action: dict[tuple[str, int], dict[str, Any]] = {}
    action_keys = sorted({(target, action) for target, action, _family in grouped})
    for target, action in action_keys:
        family_means: dict[str, float] = {}
        family_hits: dict[str, float] = {}
        n = 0
        for (t, a, family), rows in grouped.items():
            if t != target or a != action:
                continue
            ds = [float(r["delta_vs_baseline"]) for r in rows]
            hs = [1.0 if r["target_output"] == r["target_code"] else 0.0 for r in rows]
            family_means[family] = statistics.fmean(ds)
            family_hits[family] = statistics.fmean(hs)
            n += len(rows)
        values = list(family_means.values())
        hits = list(family_hits.values())
        by_action[(target, action)] = {
            "n": n,
            "family_count": len(values),
            "family_mean_delta": dict(sorted(family_means.items())),
            "worst_family_delta": min(values),
            "median_family_delta": statistics.median(values),
            "mean_delta": statistics.fmean(values),
            "mean_hit_rate": statistics.fmean(hits),
        }
    return by_action


def coverage_action(turns: list[dict[str, Any]], target: str, family: str) -> int | None:
    tried = {int(r["executed_action"]) for r in turns if r["semantic_target"] == target and r["family_id"] == family}
    for action in range(ACTION_COUNT):
        if action not in tried:
            return action
    return None


def action_code_mapping(global_turn: int, target: str) -> dict[str, int]:
    """Latin-cycle action-code counterbalance with periodic direction reversal."""
    rotation = (global_turn + 3 * TARGET_INDEX[target]) % ACTION_COUNT
    reverse = ((global_turn // ACTION_COUNT) % 2) == 1
    mapping = {}
    for digit in range(ACTION_COUNT):
        action = (rotation - digit) % ACTION_COUNT if reverse else (rotation + digit) % ACTION_COUNT
        mapping[str(digit)] = action
    if set(mapping.values()) != set(range(ACTION_COUNT)):
        raise AssertionError("ACTION_CODE_MAPPING_NOT_BIJECTIVE")
    return mapping


def robust_rank_key(stats: dict[str, Any] | None, action_id: int) -> tuple[float, float, float, float, int]:
    if not stats or int(stats["family_count"]) < 3:
        return (-math.inf, -math.inf, -math.inf, -math.inf, -action_id)
    return (
        float(stats["worst_family_delta"]),
        float(stats["median_family_delta"]),
        float(stats["mean_delta"]),
        float(stats["mean_hit_rate"]),
        -action_id,
    )


def robust_best(target: str, stats: dict[tuple[str, int], dict[str, Any]], *, include_baseline: bool = False) -> int:
    actions = range(0 if include_baseline else 1, ACTION_COUNT)
    ranked = [(robust_rank_key(stats.get((target, action)), action), action) for action in actions]
    ranked.sort(reverse=True)
    if not ranked or ranked[0][0][0] == -math.inf:
        raise RuntimeError(f"ROBUST_FULL_FAMILY_EVIDENCE_REQUIRED:{target}")
    return ranked[0][1]


def controller_prompts(target: str, stats: dict[tuple[str, int], dict[str, Any]], mapping: dict[str, int]) -> tuple[str, str]:
    codebook = "; ".join(f"{digit}=action{action}:{ACTION_SPECS[action]['name']}" for digit, action in sorted(mapping.items()))
    evidence = []
    for action in range(ACTION_COUNT):
        s = stats.get((target, action))
        if s is None:
            evidence.append(f"a{action}:unmeasured")
        else:
            evidence.append(
                f"a{action}:families={s['family_count']},worst={s['worst_family_delta']:.4f},"
                f"median={s['median_family_delta']:.4f},mean={s['mean_delta']:.4f},hit={s['mean_hit_rate']:.3f}"
            )
    common = (
        "/no_think\nYou are CONTROLLER, a Qwen3-0.6B context selecting a bounded J-Space action for another Qwen3-0.6B context. "
        "TARGET never receives the evaluator semantic target. The digit codebook is deliberately rotated each turn. "
        f"Evaluator target={target}. Codebook: {codebook}. "
    )
    evidence_prompt = common + "Cross-family causal evidence: " + "; ".join(evidence) + ". Prefer a reproducibly positive worst-family effect, then median and mean. Return exactly one digit 0-9."
    null_prompt = common + "No causal performance evidence is supplied in this matched null prompt. Return exactly one digit 0-9."
    return evidence_prompt, null_prompt


def corrected_controller_choice(
    torch: Any,
    tokenizer: Any,
    model: Any,
    device: Any,
    token_ids: dict[str, int],
    target: str,
    stats: dict[tuple[str, int], dict[str, Any]],
    mapping: dict[str, int],
    null_cache: dict[tuple[str, str], dict[str, float]],
) -> dict[str, Any]:
    evidence_prompt, null_prompt = controller_prompts(target, stats, mapping)
    mapping_sha = canonical_sha(mapping)
    cache_key = (target, mapping_sha)
    if cache_key not in null_cache:
        null_cache[cache_key] = v1.model_choice_logits(torch, tokenizer, model, device, null_prompt, token_ids)
    evidence_logits = v1.model_choice_logits(torch, tokenizer, model, device, evidence_prompt, token_ids)
    null_logits = null_cache[cache_key]
    corrected = {digit: float(evidence_logits[digit]) - float(null_logits[digit]) for digit in DIGITS}
    selected_digit = max(corrected, key=corrected.get)
    selected_action = int(mapping[selected_digit])
    return {
        "evidence_prompt": evidence_prompt,
        "null_prompt_sha256": hashlib.sha256(null_prompt.encode()).hexdigest(),
        "mapping": mapping,
        "mapping_sha256": mapping_sha,
        "evidence_logits": evidence_logits,
        "null_logits": null_logits,
        "corrected_logits": corrected,
        "selected_digit": selected_digit,
        "selected_action": selected_action,
    }


def freeze_best(turns: list[dict[str, Any]]) -> dict[str, int]:
    stats = robust_stats(turns)
    return {target: robust_best(target, stats, include_baseline=False) for target in TARGETS}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", required=True)
    ap.add_argument("--epochs", type=int, default=7)
    ap.add_argument("--turns-per-case", type=int, default=2)
    args = ap.parse_args()
    if args.epochs < 5 or args.turns_per_case < 1:
        raise SystemExit("epochs>=5 and turns-per-case>=1 required so full action x family coverage can complete")

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    trace_path = out / "blind_robust_dialogue.jsonl"
    result_path = out / "forschungsrun1_dual_qwen06_blind_robust_result.json"
    started = dt.datetime.now(dt.timezone.utc).isoformat()

    challenge = challenge_mod.build_challenge()
    challenge_gate = challenge_mod.validate(challenge)
    if not challenge_gate["pass"]:
        raise RuntimeError(f"ABSTRACT_CHALLENGE_INVALID:{challenge_gate['failures']}")
    search_rows, final_rows, search_families, final_families = v2.partition_holdout(challenge)

    (
        torch, transformers, snapshot, tokenizer, model, device,
        checkpoint_sha, tokenizer_sha, weight_manifest, _default_layer,
    ) = base.load_exact_runtime(Path(args.cache_dir))
    layers = model.model.layers
    abc_ids, _ = base.resolve_token_triplet(tokenizer)
    digit_ids = v1.resolve_single_token_codes(tokenizer, list(DIGITS))

    geometry_by_layer = {}
    geometry_receipts = {}
    for layer_index in v2.LAYERS:
        geometry_by_layer[layer_index], geometry_receipts[str(layer_index)] = v2.family_balanced_geometry(
            torch, tokenizer, model, device, layers[layer_index], challenge["calibration_rows"]
        )

    baseline_cache: dict[tuple[str, int], dict[str, Any]] = {}
    null_cache: dict[tuple[str, str], dict[str, float]] = {}
    turns: list[dict[str, Any]] = []
    global_turn = 0
    model_policy_counter = 0

    with trace_path.open("w", encoding="utf-8") as trace:
        for epoch in range(args.epochs):
            for case in search_rows:
                target = str(case["semantic_target"])
                family = str(case["family_id"])
                target_code = str(case["output_code_identity"])
                prompt = str(case["prompt"])
                seed = int(case["seed"])
                bkey = (str(case["prompt_sha256"]), seed)
                if bkey not in baseline_cache:
                    baseline_cache[bkey] = v1.target_infer(torch, tokenizer, model, device, layers, abc_ids, prompt, seed, None, 20)
                baseline = baseline_cache[bkey]
                baseline_score = v1.score_for_code(baseline["token_logits"], target_code)

                for local_turn in range(args.turns_per_case):
                    stats = robust_stats(turns)
                    coverage = coverage_action(turns, target, family)
                    controller = None
                    if coverage is not None:
                        executed = coverage
                        policy = "FULL_FACTORIAL_FAMILY_COVERAGE"
                    else:
                        mapping = action_code_mapping(global_turn, target)
                        controller = corrected_controller_choice(
                            torch, tokenizer, model, device, digit_ids, target, stats, mapping, null_cache
                        )
                        bandit_action = robust_best(target, stats, include_baseline=False)
                        if model_policy_counter % 2 == 0:
                            executed = int(controller["selected_action"])
                            policy = "DECONFOUNDED_QWEN_CONTROLLER"
                        else:
                            executed = int(bandit_action)
                            policy = "ROBUST_BANDIT_COMPARATOR"
                        model_policy_counter += 1

                    vector, layer_index, gain = v2.resolve_action(torch, geometry_by_layer, target, executed)
                    treated = v1.target_infer(torch, tokenizer, model, device, layers, abc_ids, prompt, seed, vector, layer_index)
                    target_score = v1.score_for_code(treated["token_logits"], target_code)
                    row = {
                        "schema": TRACE_SCHEMA,
                        "epoch": epoch,
                        "local_turn": local_turn,
                        "global_turn": global_turn,
                        "family_id": family,
                        "semantic_target": target,
                        "target_code": target_code,
                        "target_prompt_sha256": case["prompt_sha256"],
                        "target_prompt_blind": True,
                        "model_facing_target_identity_exposed": False,
                        "execution_policy": policy,
                        "executed_action": executed,
                        "executed_action_spec": ACTION_SPECS[executed],
                        "layer": layer_index,
                        "gain": gain,
                        "vector_sha256": base.tensor_sha(vector) if vector is not None else None,
                        "baseline_output": baseline["best_label"],
                        "baseline_score": baseline_score,
                        "target_output": treated["best_label"],
                        "target_score": target_score,
                        "target_logits": treated["token_logits"],
                        "delta_vs_baseline": target_score - baseline_score,
                        "robust_stats_sha256_before": canonical_sha({f"{k[0]}:{k[1]}": v for k, v in sorted(stats.items())}),
                        "controller": controller,
                    }
                    row["turn_sha256"] = canonical_sha(row)
                    trace.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
                    trace.flush()
                    turns.append(row)
                    global_turn += 1

    stats = robust_stats(turns)
    frozen = freeze_best(turns)
    freeze_receipt = canonical_sha({
        "frozen": frozen,
        "stats": {f"{k[0]}:{k[1]}": v for k, v in sorted(stats.items())},
        "trace_sha256": native.sha_file(trace_path),
    })

    final_eval = []
    for case in final_rows:
        target = str(case["semantic_target"])
        action_id = frozen[target]
        vector, layer_index, gain = v2.resolve_action(torch, geometry_by_layer, target, action_id)
        prompt = str(case["prompt"])
        seed = int(case["seed"])
        code = str(case["output_code_identity"])
        baseline = v1.target_infer(torch, tokenizer, model, device, layers, abc_ids, prompt, seed, None, 20)
        treated = v1.target_infer(torch, tokenizer, model, device, layers, abc_ids, prompt, seed, vector, layer_index)
        bs = v1.score_for_code(baseline["token_logits"], code)
        ts = v1.score_for_code(treated["token_logits"], code)
        final_eval.append({
            "family_id": case["family_id"], "semantic_target": target, "target_code": code,
            "prompt_sha256": case["prompt_sha256"], "action_id": action_id,
            "layer": layer_index, "gain": gain, "baseline_score": bs, "treated_score": ts,
            "delta_vs_baseline": ts - bs, "baseline_output": baseline["best_label"], "treated_output": treated["best_label"],
        })

    qwen_rows = [r for r in turns if r["execution_policy"] == "DECONFOUNDED_QWEN_CONTROLLER"]
    bandit_rows = [r for r in turns if r["execution_policy"] == "ROBUST_BANDIT_COMPARATOR"]
    core = {
        "schema": SCHEMA,
        "status": "COMPLETE",
        "started_at_utc": started,
        "finished_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": {"repo_head": base.git_text("rev-parse", "HEAD"), "executor_sha256": native.sha_file(Path(__file__))},
        "model": {"id": base.MODEL_ID, "revision": base.MODEL_REVISION, "checkpoint_sha256": checkpoint_sha, "tokenizer_sha256": tokenizer_sha},
        "challenge": {"challenge_sha256": challenge["challenge_sha256"], "gate_pass": True, "search_families": search_families, "final_families": final_families, "target_prompt_blind": True},
        "dialogue_turns": len(turns),
        "full_factorial_coverage_turns": sum(r["execution_policy"] == "FULL_FACTORIAL_FAMILY_COVERAGE" for r in turns),
        "deconfounded_qwen_policy": {
            "turns": len(qwen_rows),
            "mean_delta": statistics.fmean(float(r["delta_vs_baseline"]) for r in qwen_rows) if qwen_rows else None,
            "positive_fraction": sum(float(r["delta_vs_baseline"]) > 0 for r in qwen_rows) / len(qwen_rows) if qwen_rows else None,
        },
        "robust_bandit_comparator": {
            "turns": len(bandit_rows),
            "mean_delta": statistics.fmean(float(r["delta_vs_baseline"]) for r in bandit_rows) if bandit_rows else None,
            "positive_fraction": sum(float(r["delta_vs_baseline"]) > 0 for r in bandit_rows) / len(bandit_rows) if bandit_rows else None,
        },
        "frozen_best_actions": frozen,
        "freeze_receipt_sha256": freeze_receipt,
        "robust_stats": {f"{k[0]}:{k[1]}": v for k, v in sorted(stats.items())},
        "fast_final_eval": final_eval,
        "fast_final_mean_delta": statistics.fmean(float(r["delta_vs_baseline"]) for r in final_eval),
        "fast_final_positive_fraction": sum(float(r["delta_vs_baseline"]) > 0 for r in final_eval) / len(final_eval),
        "trace": {"path": str(trace_path), "rows": len(turns), "sha256": native.sha_file(trace_path)},
        "evidence_boundary": {"full_jspace_control_established": False, "canonical_semantics_minted": False, "whole_hcu_runtime_credit": False, "whole_entityos_runtime_credit": False, "external_llm_provider_used": False, "paid_provider_used": False},
    }
    result = {**core, "result_sha256": canonical_sha(core)}
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "dialogue_turns": result["dialogue_turns"],
        "qwen_policy": result["deconfounded_qwen_policy"], "bandit": result["robust_bandit_comparator"],
        "frozen_best_actions": frozen, "fast_final_mean_delta": result["fast_final_mean_delta"],
        "fast_final_positive_fraction": result["fast_final_positive_fraction"],
        "trace_sha256": result["trace"]["sha256"], "result_sha256": result["result_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
