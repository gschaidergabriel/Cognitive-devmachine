#!/usr/bin/env python3
"""Forschungsrun 1 v2: target-blind cumulative two-role Qwen3-0.6B J-Space search.

This successor fixes the two largest scientific weaknesses of the v1 adaptive search:
1) TARGET never receives the requested semantic identity. Within each family the exact same
   model-facing prompt bytes are reused for all three evaluator-side semantic targets.
2) CONTROLLER receives cumulative action statistics across the complete run, so late turns
   can exploit evidence learned hundreds of turns earlier instead of forgetting at episode
   boundaries.

The search uses the execution-free abstract-state challenge as a frozen prompt universe.
The first three target-blind families are the adaptive SEARCH partition. The final three
families are never shown to the controller/search loop; they are opened only after one best
bounded action per semantic target is frozen. Optional native replay then evaluates those
frozen actions with the established six matched controls through pinned llama.cpp cvec.

This program is research evidence only. It never mints canonical semantic, J-Space-model,
HCU, EntityOS, training, or real-effect authority.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

from tools import trigger1_abstract_state_challenge_v1 as challenge_mod
from tools import trigger1_local_qwen06_midlayer_causal_execute as base
from tools import trigger1_local_qwen06_native_semantic_counterbalanced_execute as native
from tools import forschungsrun1_dual_qwen06_jspace_search as v1

SCHEMA = "CLAY_FORSCHUNGSRUN1_DUAL_QWEN06_BLIND_CUMULATIVE/v2"
TRACE_SCHEMA = "CLAY_FORSCHUNGSRUN1_DUAL_QWEN06_BLIND_TURN/v2"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
LAYERS = (14, 20)
ACTION_SPECS = v1.ACTION_SPECS
ACTION_COUNT = len(ACTION_SPECS)
DEFAULT_EPOCHS = 16
DEFAULT_TURNS_PER_CASE = 4
DEFAULT_NATIVE_TOP_K = 3


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _unit(torch: Any, vector: Any, name: str) -> Any:
    norm = torch.linalg.vector_norm(vector)
    if not bool(torch.isfinite(norm)) or float(norm) <= 1e-12:
        raise RuntimeError(f"DEGENERATE_VECTOR:{name}")
    return vector / norm


def family_balanced_geometry(
    torch: Any,
    tokenizer: Any,
    model: Any,
    device: Any,
    layer: Any,
    calibration_rows: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Build equal-family-energy three-state geometry from instruction-free calibration rows."""
    by_family: dict[str, dict[str, Any]] = collections.defaultdict(dict)
    receipts: list[dict[str, Any]] = []
    for row in calibration_rows:
        target = str(row["semantic_target"])
        family = str(row["family_id"])
        prompt = str(row["prompt"])
        act = base.extract_internal_activation(torch, tokenizer, model, device, layer, prompt).to(device)
        by_family[family][target] = act
        receipts.append({
            "family_id": family,
            "semantic_target": target,
            "prompt_sha256": row["prompt_sha256"],
            "activation_sha256": base.tensor_sha(act),
        })

    centered_rows: dict[str, list[Any]] = {target: [] for target in TARGETS}
    energies: dict[str, float] = {}
    for family in sorted(by_family):
        triad = by_family[family]
        if set(triad) != set(TARGETS):
            raise RuntimeError(f"INCOMPLETE_CALIBRATION_TRIAD:{family}")
        a, n, u = triad["AFFIRMATIVE"], triad["NEGATIVE"], triad["NEUTRAL"]
        grand = (a + n + u) / 3.0
        h1 = a - 0.5 * (n + u)
        d2 = n - u
        energy = math.sqrt(float(torch.linalg.vector_norm(h1)) ** 2 + float(torch.linalg.vector_norm(d2)) ** 2)
        if not math.isfinite(energy) or energy <= 1e-12:
            raise RuntimeError(f"DEGENERATE_FAMILY_ENERGY:{family}")
        energies[family] = energy
        scale = 1.0 / energy
        centered_rows["AFFIRMATIVE"].append((a - grand) * scale)
        centered_rows["NEGATIVE"].append((n - grand) * scale)
        centered_rows["NEUTRAL"].append((u - grand) * scale)

    means = {target: torch.stack(centered_rows[target], dim=0).mean(dim=0) for target in TARGETS}
    residual = means["AFFIRMATIVE"] + means["NEGATIVE"] + means["NEUTRAL"]
    if float(torch.linalg.vector_norm(residual)) > 1e-5:
        raise RuntimeError("BALANCED_GEOMETRY_ZERO_SUM_FAILED")

    geometry: dict[str, dict[str, Any]] = {}
    for target in TARGETS:
        competitors = [x for x in TARGETS if x != target]
        c1, c2 = competitors
        pole = _unit(torch, means[target], f"{target}:pole")
        vs1 = _unit(torch, means[target] - means[c1], f"{target}:vs1")
        vs2 = _unit(torch, means[target] - means[c2], f"{target}:vs2")
        geometry[target] = {
            "competitors": competitors,
            "target_pole": pole,
            "anti_target": -pole,
            "target_vs_comp1": vs1,
            "target_vs_comp2": vs2,
            "mix_70_30": _unit(torch, 0.70 * vs1 + 0.30 * vs2, f"{target}:mix70"),
            "mix_30_70": _unit(torch, 0.30 * vs1 + 0.70 * vs2, f"{target}:mix30"),
        }
    receipt = {
        "calibration_rows_sha256": canonical_sha(receipts),
        "family_count": len(by_family),
        "family_pair_energies": energies,
        "family_weighting": "INVERSE_WITHIN_FAMILY_CONTRAST_PAIR_ENERGY",
        "vectors": {
            target: {kind: base.tensor_sha(vec) for kind, vec in g.items() if kind != "competitors"}
            for target, g in geometry.items()
        },
    }
    receipt["geometry_receipt_sha256"] = canonical_sha(receipt)
    return geometry, receipt


def resolve_action(torch: Any, geometry_by_layer: dict[int, dict[str, dict[str, Any]]], target: str, action_id: int):
    spec = ACTION_SPECS[action_id]
    layer = int(spec["layer"])
    gain = float(spec["gain"])
    kind = str(spec["kind"])
    if kind == "baseline":
        return None, layer, gain
    return geometry_by_layer[layer][target][kind].to(dtype=torch.float32) * gain, layer, gain


def ledger_stats(turns: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, float]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = collections.defaultdict(list)
    for row in turns:
        grouped[(str(row["semantic_target"]), int(row["executed_action"]))].append(row)
    out: dict[tuple[str, int], dict[str, float]] = {}
    for key, rows in grouped.items():
        deltas = [float(r["delta_vs_baseline"]) for r in rows]
        hits = [1.0 if r["target_output"] == r["target_code"] else 0.0 for r in rows]
        out[key] = {
            "n": float(len(rows)),
            "mean_delta": sum(deltas) / len(deltas),
            "min_delta": min(deltas),
            "hit_rate": sum(hits) / len(hits),
        }
    return out


def controller_prompt(target: str, ledger: dict[tuple[str, int], dict[str, float]], recent: list[dict[str, Any]]) -> str:
    actions = "; ".join(f"{i}={ACTION_SPECS[i]['name']}" for i in range(ACTION_COUNT))
    rows = []
    for action_id in range(ACTION_COUNT):
        s = ledger.get((target, action_id))
        if s is None:
            rows.append(f"a{action_id}:untried")
        else:
            rows.append(f"a{action_id}:n={int(s['n'])},d={s['mean_delta']:.4f},hit={s['hit_rate']:.3f}")
    rec = " | ".join(
        f"a{r['executed_action']} d={r['delta_vs_baseline']:.4f} out={r['target_output']}" for r in recent[-3:]
    ) or "none"
    return (
        "/no_think\nYou are CONTROLLER, one Qwen3-0.6B inference context controlling another Qwen3-0.6B context only through bounded J-Space vectors. "
        "TARGET receives target-blind prompt bytes: it is never told the evaluator semantic target. "
        f"Evaluator target={target}. Actions: {actions}. "
        f"Cumulative evidence for this target: {'; '.join(rows)}. Recent outcomes: {rec}. "
        "Prefer reproducibly positive causal delta, but explore untried or uncertain actions. Return exactly one digit 0-9."
    )


def choose_executed_action(target: str, selected: int, ledger: dict[tuple[str, int], dict[str, float]], global_turn: int) -> tuple[int, str]:
    untried = [i for i in range(ACTION_COUNT) if (target, i) not in ledger]
    if untried:
        return untried[0], "FORCED_GLOBAL_COVERAGE"
    if global_turn % 7 == 0:
        return (global_turn // 7) % ACTION_COUNT, "DETERMINISTIC_GLOBAL_EXPLORATION"
    return selected, "CONTROLLER_POLICY"


def partition_holdout(challenge: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    families = []
    for row in challenge["holdout_rows"]:
        family = str(row["family_id"])
        if family not in families:
            families.append(family)
    if len(families) != 6:
        raise RuntimeError("EXACT_SIX_HOLDOUT_FAMILIES_REQUIRED")
    search_families = families[:3]
    final_families = families[3:]
    search_rows = [r for r in challenge["holdout_rows"] if r["family_id"] in search_families]
    final_rows = [r for r in challenge["holdout_rows"] if r["family_id"] in final_families]
    if len(search_rows) != 9 or len(final_rows) != 9:
        raise RuntimeError("THREE_BY_THREE_PARTITION_REQUIRED")
    return search_rows, final_rows, search_families, final_families


def freeze_best_actions(turns: list[dict[str, Any]]) -> dict[str, int]:
    ledger = ledger_stats(turns)
    frozen: dict[str, int] = {}
    for target in TARGETS:
        candidates = []
        for action_id in range(1, ACTION_COUNT):
            s = ledger.get((target, action_id))
            if s is not None:
                candidates.append((s["mean_delta"], s["hit_rate"], s["n"], -action_id, action_id))
        if not candidates:
            raise RuntimeError(f"NO_NONBASELINE_ACTION_EVIDENCE:{target}")
        candidates.sort(reverse=True)
        frozen[target] = candidates[0][-1]
    return frozen


def native_cases(final_rows: list[dict[str, Any]], target: str, candidate_key: str) -> list[dict[str, Any]]:
    rows = []
    for case in final_rows:
        if case["semantic_target"] != target:
            continue
        for control in base.CONTROLS:
            rows.append({
                "case_id": f"{candidate_key}-{case['family_id']}-{control}",
                "seed": int(case["seed"]),
                "target_label": str(case["output_code_identity"]),
                "prompt": str(case["prompt"]),
                "prompt_family": str(case["family_id"]),
                "control": control,
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", required=True)
    ap.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    ap.add_argument("--turns-per-case", type=int, default=DEFAULT_TURNS_PER_CASE)
    ap.add_argument("--skip-native", action="store_true")
    ap.add_argument("--llama-root")
    ap.add_argument("--gguf")
    ap.add_argument("--harness")
    args = ap.parse_args()
    if args.epochs < 1 or args.turns_per_case < 1:
        raise SystemExit("epochs and turns-per-case must be positive")

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    trace_path = out / "blind_cumulative_dialogue.jsonl"
    result_path = out / "forschungsrun1_dual_qwen06_blind_cumulative_result.json"
    started = dt.datetime.now(dt.timezone.utc).isoformat()

    challenge = challenge_mod.build_challenge()
    challenge_verdict = challenge_mod.validate(challenge)
    if not challenge_verdict["pass"]:
        raise RuntimeError(f"ABSTRACT_CHALLENGE_INVALID:{challenge_verdict['failures']}")
    search_rows, final_rows, search_families, final_families = partition_holdout(challenge)

    (
        torch, transformers, snapshot, tokenizer, model, device,
        checkpoint_sha, tokenizer_sha, weight_manifest, _default_layer,
    ) = base.load_exact_runtime(Path(args.cache_dir))
    layers = model.model.layers
    abc_ids, _ = base.resolve_token_triplet(tokenizer)
    controller_ids = v1.resolve_single_token_codes(tokenizer, [str(i) for i in range(ACTION_COUNT)])

    geometry_by_layer = {}
    geometry_receipts = {}
    for layer_index in LAYERS:
        geometry, receipt = family_balanced_geometry(
            torch, tokenizer, model, device, layers[layer_index], challenge["calibration_rows"]
        )
        geometry_by_layer[layer_index] = geometry
        geometry_receipts[str(layer_index)] = receipt

    baseline_cache: dict[tuple[str, int], dict[str, Any]] = {}
    all_turns: list[dict[str, Any]] = []
    global_turn = 0
    with trace_path.open("w", encoding="utf-8") as trace:
        for epoch in range(args.epochs):
            for case in search_rows:
                target = str(case["semantic_target"])
                target_code = str(case["output_code_identity"])
                prompt = str(case["prompt"])
                seed = int(case["seed"])
                bkey = (str(case["prompt_sha256"]), seed)
                if bkey not in baseline_cache:
                    baseline_cache[bkey] = v1.target_infer(
                        torch, tokenizer, model, device, layers, abc_ids, prompt, seed, None, 20
                    )
                baseline = baseline_cache[bkey]
                baseline_score = v1.score_for_code(baseline["token_logits"], target_code)
                for local_turn in range(args.turns_per_case):
                    ledger = ledger_stats(all_turns)
                    recent = [r for r in all_turns if r["semantic_target"] == target]
                    cprompt = controller_prompt(target, ledger, recent)
                    clogits = v1.model_choice_logits(torch, tokenizer, model, device, cprompt, controller_ids)
                    selected = int(max(clogits, key=clogits.get))
                    executed, policy = choose_executed_action(target, selected, ledger, global_turn)
                    vector, layer_index, gain = resolve_action(torch, geometry_by_layer, target, executed)
                    result = v1.target_infer(
                        torch, tokenizer, model, device, layers, abc_ids, prompt, seed, vector, layer_index
                    )
                    score = v1.score_for_code(result["token_logits"], target_code)
                    row = {
                        "schema": TRACE_SCHEMA,
                        "epoch": epoch,
                        "case_id": case.get("family_id"),
                        "turn": local_turn,
                        "global_turn": global_turn,
                        "semantic_target": target,
                        "target_code": target_code,
                        "target_prompt": prompt,
                        "target_prompt_sha256": case["prompt_sha256"],
                        "target_prompt_blind": True,
                        "model_facing_target_identity_exposed": False,
                        "controller_prompt": cprompt,
                        "controller_prompt_sha256": hashlib.sha256(cprompt.encode("utf-8")).hexdigest(),
                        "controller_selected_action": selected,
                        "controller_action_logits": clogits,
                        "executed_action": executed,
                        "executed_action_spec": ACTION_SPECS[executed],
                        "execution_policy": policy,
                        "layer": layer_index,
                        "gain": gain,
                        "vector_sha256": base.tensor_sha(vector) if vector is not None else None,
                        "baseline_output": baseline["best_label"],
                        "baseline_score": baseline_score,
                        "target_output": result["best_label"],
                        "target_logits": result["token_logits"],
                        "target_score": score,
                        "delta_vs_baseline": score - baseline_score,
                        "global_ledger_sha256_before_turn": canonical_sha({str(k): v for k, v in ledger.items()}),
                        "roles": {
                            "controller_model": base.MODEL_ID,
                            "target_model": base.MODEL_ID,
                            "shared_weights": True,
                            "separate_inference_contexts": True,
                            "controller_text_delivered_to_target": False,
                        },
                    }
                    row["turn_sha256"] = canonical_sha(row)
                    trace.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
                    trace.flush()
                    all_turns.append(row)
                    global_turn += 1

    frozen = freeze_best_actions(all_turns)
    frozen_before_final_sha = canonical_sha({"actions": frozen, "search_trace_sha256": native.sha_file(trace_path)})

    fast_final = []
    for case in final_rows:
        target = str(case["semantic_target"])
        action_id = frozen[target]
        vector, layer_index, gain = resolve_action(torch, geometry_by_layer, target, action_id)
        prompt = str(case["prompt"])
        seed = int(case["seed"])
        baseline = v1.target_infer(torch, tokenizer, model, device, layers, abc_ids, prompt, seed, None, 20)
        treated = v1.target_infer(torch, tokenizer, model, device, layers, abc_ids, prompt, seed, vector, layer_index)
        target_code = str(case["output_code_identity"])
        bscore = v1.score_for_code(baseline["token_logits"], target_code)
        tscore = v1.score_for_code(treated["token_logits"], target_code)
        fast_final.append({
            "family_id": case["family_id"],
            "semantic_target": target,
            "target_code": target_code,
            "prompt_sha256": case["prompt_sha256"],
            "target_prompt_blind": True,
            "action_id": action_id,
            "layer": layer_index,
            "gain": gain,
            "baseline_score": bscore,
            "treated_score": tscore,
            "delta_vs_baseline": tscore - bscore,
            "baseline_output": baseline["best_label"],
            "treated_output": treated["best_label"],
        })

    native_results = []
    native_status = "SKIPPED_BY_ARGUMENT" if args.skip_native else "PENDING"
    if not args.skip_native:
        if not (args.llama_root and args.gguf and args.harness):
            raise RuntimeError("NATIVE_PATHS_REQUIRED_UNLESS_SKIP_NATIVE")
        llama_root = Path(args.llama_root).resolve()
        gguf = Path(args.gguf).resolve()
        harness = Path(args.harness).resolve()
        identity = v1.validate_native_runtime(gguf, llama_root, harness)
        identity.update({
            "source_checkpoint_sha256": checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "python_runtime_build_sha256": canonical_sha(base.runtime_manifest(torch, transformers, model)),
        })
        state = native.NativeApiState(harness, gguf, llama_root, out / "native", identity)
        for target in TARGETS:
            action_id = frozen[target]
            spec = ACTION_SPECS[action_id]
            layer_index = int(spec["layer"])
            gain = float(spec["gain"])
            kind = str(spec["kind"])
            unit_vector = geometry_by_layer[layer_index][target][kind]
            key = f"blind-{target.lower()}-a{action_id}"
            controls = native.make_control_files(torch, unit_vector, gain, layer_index, out / "native" / "cvec" / key)
            state.register(key, layer_index, gain, controls)
            response = state.execute({
                "schema": "CLAY_FORSCHUNGSRUN1_BLIND_NATIVE_REPLAY_REQUEST/v1",
                "candidate_key": key,
                "cases": native_cases(final_rows, target, key),
            })
            native_results.append({
                "semantic_target": target,
                "action_id": action_id,
                "native_metrics": native.metrics(response["rows"]),
                "response_sha256": response["response_sha256"],
                "rows_sha256": canonical_sha(response["rows"]),
            })
        native_status = "COMPLETE"

    search_ledger = ledger_stats(all_turns)
    summary_core = {
        "schema": SCHEMA,
        "status": "COMPLETE",
        "started_at_utc": started,
        "finished_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": {
            "repo_head": base.git_text("rev-parse", "HEAD"),
            "executor_sha256": native.sha_file(Path(__file__)),
        },
        "model": {
            "id": base.MODEL_ID,
            "revision": base.MODEL_REVISION,
            "checkpoint_sha256": checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "logical_roles": 2,
            "resident_model_copies_claimed": 1,
        },
        "challenge": {
            "challenge_sha256": challenge["challenge_sha256"],
            "challenge_gate_pass": challenge_verdict["pass"],
            "search_families": search_families,
            "final_families": final_families,
            "search_final_family_disjoint": set(search_families).isdisjoint(final_families),
            "target_prompt_blind": True,
            "final_partition_unopened_until_action_freeze": True,
            "frozen_action_receipt_sha256": frozen_before_final_sha,
        },
        "search": {
            "epochs": args.epochs,
            "turns_per_case": args.turns_per_case,
            "dialogue_turns": len(all_turns),
            "cumulative_controller_memory": True,
            "controller_text_delivered_to_target": False,
            "action_specs": ACTION_SPECS,
            "geometry_receipts": geometry_receipts,
            "frozen_best_actions": frozen,
            "ledger": {f"{target}:{action}": stats for (target, action), stats in sorted(search_ledger.items())},
        },
        "fast_final_eval": fast_final,
        "native_replay_status": native_status,
        "native_replay": native_results,
        "trace": {
            "path": str(trace_path),
            "rows": len(all_turns),
            "sha256": native.sha_file(trace_path),
        },
        "evidence_boundary": {
            "full_jspace_control_established": False,
            "abstract_native_semantic_jspace_promoted": False,
            "canonical_semantics_minted": False,
            "whole_hcu_runtime_credit": False,
            "whole_entityos_runtime_credit": False,
            "training_credit": False,
            "external_llm_provider_used": False,
            "paid_provider_used": False,
        },
    }
    summary = {**summary_core, "result_sha256": canonical_sha(summary_core)}
    result_path.write_text(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": summary["status"],
        "dialogue_turns": len(all_turns),
        "frozen_best_actions": frozen,
        "fast_final_mean_delta": sum(r["delta_vs_baseline"] for r in fast_final) / len(fast_final),
        "native_replay_status": native_status,
        "trace_sha256": summary["trace"]["sha256"],
        "result_sha256": summary["result_sha256"],
        "result_path": str(result_path),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
