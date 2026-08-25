#!/usr/bin/env python3
"""Forschungsrun 1: two-role Qwen3-0.6B adaptive J-Space search.

The experiment uses ONE pinned Qwen3-0.6B checkpoint as shared weights with two
logically separate inference contexts:

* CONTROLLER: receives only the semantic goal plus prior structured target feedback
  and emits a single action-code token selecting a bounded J-Space intervention.
* TARGET: receives the task prompt but never the controller prompt/rationale.  The
  selected vector is injected at a non-terminal hidden-state site and the target emits
  a counterbalanced decision code.

This separation prevents text-prompt leakage from masquerading as vector control while
still allowing fast controller<->target iteration.  A deterministic exploration wrapper
prevents mode collapse while recording both the controller-selected and actually executed
action.  Thousands of fast PyTorch turns can be collected with the model loaded once.

The strongest discovered target/action pairs are then replayed on a fresh family through
the pinned Q8_0 GGUF + llama.cpp llama_set_adapter_cvec path with the established six
matched controls.  The native replay is deliberately a transfer/replication stage: the
fast PyTorch hook acts on the final prompt token, whereas native cvec affects the native
prompt-token scope.  Agreement is evidence; disagreement is also first-class evidence.

No external LLM provider, credential, canonical state mutation, training, or real effect
is required or authorized by this program.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_local_qwen06_midlayer_causal_execute as base
from tools import trigger1_local_qwen06_native_semantic_counterbalanced_execute as native

SCHEMA = "CLAY_FORSCHUNGSRUN1_DUAL_QWEN06_JSPACE_SEARCH/v1"
TRACE_SCHEMA = "CLAY_FORSCHUNGSRUN1_DUAL_QWEN06_DIALOGUE_TURN/v1"
SEMANTICS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
LAYERS = (14, 20)
ACTION_COUNT = 10
DEFAULT_EPISODES = 128
DEFAULT_TURNS = 8
DEFAULT_NATIVE_TOP_K = 6

# Action codes are deliberately single digit candidates.  Their vectors are resolved
# relative to the episode semantic target, so the controller searches a reusable geometry
# rather than memorising output-code identities.
ACTION_SPECS: dict[int, dict[str, Any]] = {
    0: {"name": "BASELINE", "kind": "baseline", "layer": 20, "gain": 0.0},
    1: {"name": "TARGET_POLE_L20_G16", "kind": "target_pole", "layer": 20, "gain": 16.0},
    2: {"name": "TARGET_POLE_L20_G32", "kind": "target_pole", "layer": 20, "gain": 32.0},
    3: {"name": "TARGET_POLE_L20_G48", "kind": "target_pole", "layer": 20, "gain": 48.0},
    4: {"name": "ANTI_TARGET_L20_G32", "kind": "anti_target", "layer": 20, "gain": 32.0},
    5: {"name": "TARGET_VS_COMP1_L20_G32", "kind": "target_vs_comp1", "layer": 20, "gain": 32.0},
    6: {"name": "TARGET_VS_COMP2_L20_G32", "kind": "target_vs_comp2", "layer": 20, "gain": 32.0},
    7: {"name": "MIX_70_30_L20_G32", "kind": "mix_70_30", "layer": 20, "gain": 32.0},
    8: {"name": "MIX_30_70_L20_G32", "kind": "mix_30_70", "layer": 20, "gain": 32.0},
    9: {"name": "TARGET_POLE_L14_G32", "kind": "target_pole", "layer": 14, "gain": 32.0},
}

TARGET_TEMPLATES = (
    "Decision task {family}. Codebook: {mapping}. Requested semantic state: {target}. Output only its code token.",
    "State selection {family}. Mapping: {mapping}. Choose the code representing {target}; emit only that single code.",
    "Counterbalanced probe {family}. With {mapping}, select {target} and return exactly its one-letter code.",
    "Semantic routing {family}. Interpret {mapping}. Required state is {target}. Reply with only the mapped code.",
)


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def unit(torch: Any, vector: Any) -> Any:
    norm = torch.linalg.vector_norm(vector)
    if not bool(torch.isfinite(norm)) or float(norm) <= 1e-12:
        raise RuntimeError("DEGENERATE_VECTOR")
    return vector / norm


def semantic_means(torch: Any, tokenizer: Any, model: Any, device: Any, layer: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: dict[str, list[Any]] = {s: [] for s in SEMANTICS}
    receipts: list[dict[str, Any]] = []
    for semantic, family in native.SEMANTIC_BASIS.items():
        for seed, prompt in family:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
            act = base.extract_internal_activation(torch, tokenizer, model, device, layer, prompt)
            rows[semantic].append(act.to(device))
            receipts.append({
                "semantic": semantic,
                "seed": seed,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "activation_sha256": base.tensor_sha(act),
            })
    return {s: torch.stack(rows[s], dim=0).mean(dim=0) for s in SEMANTICS}, receipts


def build_geometry(torch: Any, means: dict[str, Any]) -> dict[str, dict[str, Any]]:
    geometry: dict[str, dict[str, Any]] = {}
    for target in SEMANTICS:
        competitors = [s for s in SEMANTICS if s != target]
        c1, c2 = competitors
        pole = unit(torch, means[target] - 0.5 * (means[c1] + means[c2]))
        vs1 = unit(torch, means[target] - means[c1])
        vs2 = unit(torch, means[target] - means[c2])
        mix70 = unit(torch, 0.70 * vs1 + 0.30 * vs2)
        mix30 = unit(torch, 0.30 * vs1 + 0.70 * vs2)
        geometry[target] = {
            "competitors": competitors,
            "target_pole": pole,
            "anti_target": -pole,
            "target_vs_comp1": vs1,
            "target_vs_comp2": vs2,
            "mix_70_30": mix70,
            "mix_30_70": mix30,
        }
    return geometry


def resolve_action_vector(torch: Any, geometry_by_layer: dict[int, dict[str, dict[str, Any]]], target: str, action_id: int) -> tuple[Any | None, int, float]:
    spec = ACTION_SPECS[action_id]
    layer = int(spec["layer"])
    gain = float(spec["gain"])
    kind = str(spec["kind"])
    if kind == "baseline":
        return None, layer, gain
    basis = geometry_by_layer[layer][target][kind]
    return basis.to(dtype=torch.float32) * gain, layer, gain


def resolve_single_token_codes(tokenizer: Any, values: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    for value in values:
        candidates = (value, " " + value)
        found = None
        for text in candidates:
            ids = tokenizer.encode(text, add_special_tokens=False)
            if len(ids) == 1:
                found = int(ids[0])
                break
        if found is None:
            raise RuntimeError(f"NO_SINGLE_TOKEN_CODE:{value}")
        result[value] = found
    if len(set(result.values())) != len(result):
        raise RuntimeError("ACTION_CODE_TOKEN_COLLISION")
    return result


def model_choice_logits(torch: Any, tokenizer: Any, model: Any, device: Any, prompt: str, token_ids: dict[str, int]) -> dict[str, float]:
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        out = model(**inputs)
        logits = out.logits[0, -1].float().detach().cpu()
    return {code: float(logits[token_id]) for code, token_id in token_ids.items()}


def target_infer(
    torch: Any,
    tokenizer: Any,
    model: Any,
    device: Any,
    layers: Any,
    token_ids: dict[str, int],
    prompt: str,
    seed: int,
    vector: Any | None,
    layer_index: int,
) -> dict[str, Any]:
    hook_calls = 0
    applied_sha = None
    applied_l2 = 0.0
    layer = layers[layer_index]

    def hook(_module: Any, _inputs: Any, output: Any):
        nonlocal hook_calls
        hook_calls += 1
        if vector is None:
            return output
        hidden = base.unpack_hidden(output).clone()
        v = vector.to(device=device, dtype=hidden.dtype)
        hidden[:, -1, :] = hidden[:, -1, :] + v
        return base.replace_hidden(output, hidden)

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    if vector is not None:
        applied_sha = base.tensor_sha(vector)
        applied_l2 = float(torch.linalg.vector_norm(vector).detach().cpu())
    handle = layer.register_forward_hook(hook)
    try:
        with torch.no_grad():
            out = model(**inputs)
            logits = out.logits[0, -1].float().detach().cpu()
    finally:
        handle.remove()
    trio = {label: float(logits[token_id]) for label, token_id in token_ids.items()}
    return {
        "token_logits": trio,
        "best_label": max(trio, key=trio.get),
        "hook_calls": hook_calls,
        "activation_site": f"model.model.layers[{layer_index}]:output:last_token",
        "applied_vector_sha256": applied_sha,
        "applied_vector_l2": applied_l2,
    }


def score_for_code(logits: dict[str, float], target_code: str) -> float:
    others = [x for x in ("A", "B", "C") if x != target_code]
    return float(logits[target_code]) - 0.5 * (float(logits[others[0]]) + float(logits[others[1]]))


def episode_spec(index: int) -> dict[str, Any]:
    semantic = SEMANTICS[index % len(SEMANTICS)]
    perms = list(itertools.permutations(SEMANTICS))
    perm = perms[(index // len(SEMANTICS)) % len(perms)]
    code_to_sem = dict(zip(("A", "B", "C"), perm))
    sem_to_code = {v: k for k, v in code_to_sem.items()}
    mapping = ", ".join(f"{code}={sem}" for code, sem in code_to_sem.items())
    family = f"E{index:04d}"
    template = TARGET_TEMPLATES[(index // (len(SEMANTICS) * len(perms))) % len(TARGET_TEMPLATES)]
    prompt = "/no_think\n" + template.format(family=family, mapping=mapping, target=semantic)
    return {
        "episode": index,
        "family": family,
        "semantic_target": semantic,
        "target_code": sem_to_code[semantic],
        "mapping": code_to_sem,
        "prompt": prompt,
        "seed": 700000 + index * 37,
    }


def controller_prompt(spec: dict[str, Any], history: list[dict[str, Any]]) -> str:
    action_lines = "; ".join(f"{i}={ACTION_SPECS[i]['name']}" for i in range(ACTION_COUNT))
    hist_lines = []
    for row in history[-5:]:
        hist_lines.append(
            f"turn={row['turn']} selected={row['controller_selected_action']} executed={row['executed_action']} "
            f"target_output={row['target_output']} target_code={spec['target_code']} score={row['target_score']:.6f} "
            f"delta={row['delta_vs_baseline']:.6f}"
        )
    history_text = " | ".join(hist_lines) if hist_lines else "none"
    return (
        "/no_think\nYou are CONTROLLER, a Qwen3-0.6B J-Space search policy. "
        "Choose the next bounded vector action that is most likely to make TARGET emit the requested semantic code. "
        "You never send prose to TARGET; only the selected vector action is applied. "
        f"Semantic goal={spec['semantic_target']}; target output code={spec['target_code']}. "
        f"Actions: {action_lines}. Previous structured feedback: {history_text}. "
        "Explore when evidence is weak; exploit actions with positive causal delta when evidence is strong. "
        "Return exactly one digit from 0 1 2 3 4 5 6 7 8 9 and nothing else."
    )


def exploration_override(episode: int, turn: int, selected: int) -> tuple[int, str]:
    # First four turns force coverage of distinct action families.  Afterwards one in
    # four turns is deterministic exploration; all others execute the model's choice.
    initial = (0, 2, 5, 7)
    if turn < len(initial):
        return initial[turn], "FORCED_INITIAL_COVERAGE"
    marker = (episode * 131 + turn * 17) % 4
    if marker == 0:
        return (episode + turn) % ACTION_COUNT, "DETERMINISTIC_EXPLORATION"
    return selected, "CONTROLLER_POLICY"


def action_stats(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = collections.defaultdict(list)
    for row in turns:
        grouped[(str(row["semantic_target"]), int(row["executed_action"]))].append(row)
    result = []
    for (semantic, action_id), rows in grouped.items():
        deltas = [float(r["delta_vs_baseline"]) for r in rows]
        hits = [1.0 if r["target_output"] == r["target_code"] else 0.0 for r in rows]
        result.append({
            "semantic_target": semantic,
            "action_id": action_id,
            "action": ACTION_SPECS[action_id],
            "n": len(rows),
            "mean_delta_vs_baseline": sum(deltas) / len(deltas),
            "min_delta_vs_baseline": min(deltas),
            "max_delta_vs_baseline": max(deltas),
            "target_code_hit_rate": sum(hits) / len(hits),
        })
    result.sort(key=lambda r: (r["mean_delta_vs_baseline"], r["target_code_hit_rate"], r["n"]), reverse=True)
    return result


def native_holdout_cases(semantic_target: str, candidate_key: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    competitors = [s for s in SEMANTICS if s != semantic_target]
    for idx, target_code in enumerate(("A", "B", "C")):
        other_codes = [c for c in ("A", "B", "C") if c != target_code]
        mapping = {
            target_code: semantic_target,
            other_codes[0]: competitors[idx % 2],
            other_codes[1]: competitors[(idx + 1) % 2],
        }
        mapping_text = ", ".join(f"{c}={mapping[c]}" for c in ("A", "B", "C"))
        prompt = (
            "/no_think\nNative adaptive-search holdout "
            f"{candidate_key}-H{idx + 1}. Mapping: {mapping_text}. Requested state: {semantic_target}. "
            "Return only its code token."
        )
        for control in base.CONTROLS:
            cases.append({
                "case_id": f"{candidate_key}-h{idx + 1}-{control}",
                "seed": 880000 + idx * 101,
                "prompt_family": f"NATIVE_{candidate_key}_H{idx + 1}",
                "prompt": prompt,
                "target_label": target_code,
                "control": control,
            })
    return cases


def validate_native_runtime(gguf: Path, llama_root: Path, harness: Path) -> dict[str, Any]:
    commit = subprocess.check_output(["git", "-C", str(llama_root), "rev-parse", "HEAD"], text=True, timeout=10).strip()
    if commit != native.LLAMA_CPP_COMMIT:
        raise RuntimeError(f"LLAMA_CPP_COMMIT_MISMATCH:{commit}")
    gguf_sha = native.sha_file(gguf)
    if gguf_sha != native.MODEL_GGUF_SHA256:
        raise RuntimeError(f"GGUF_SHA256_MISMATCH:{gguf_sha}")
    return {
        "llama_cpp_source_commit": commit,
        "gguf_sha256": gguf_sha,
        "harness_sha256": native.sha_file(harness),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", required=True)
    ap.add_argument("--episodes", type=int, default=DEFAULT_EPISODES)
    ap.add_argument("--turns", type=int, default=DEFAULT_TURNS)
    ap.add_argument("--native-top-k", type=int, default=DEFAULT_NATIVE_TOP_K)
    ap.add_argument("--llama-root")
    ap.add_argument("--gguf")
    ap.add_argument("--harness")
    ap.add_argument("--skip-native", action="store_true")
    args = ap.parse_args()

    if args.episodes < 6 or args.turns < 4:
        raise SystemExit("episodes>=6 and turns>=4 required")
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    trace_path = out / "dual_qwen06_dialogue.jsonl"
    result_path = out / "forschungsrun1_dual_qwen06_jspace_result.json"
    started = dt.datetime.now(dt.timezone.utc).isoformat()

    (
        torch,
        transformers,
        snapshot,
        tokenizer,
        model,
        device,
        checkpoint_sha,
        tokenizer_sha,
        weight_manifest,
        _default_layer,
    ) = base.load_exact_runtime(Path(args.cache_dir))
    layers = model.model.layers
    if max(LAYERS) >= len(layers) - 1:
        raise RuntimeError("REQUESTED_LAYER_NOT_NONTERMINAL")
    abc_ids, _abc_text = base.resolve_token_triplet(tokenizer)
    controller_ids = resolve_single_token_codes(tokenizer, [str(i) for i in range(ACTION_COUNT)])

    geometry_by_layer: dict[int, dict[str, dict[str, Any]]] = {}
    geometry_receipts: dict[str, Any] = {}
    for layer_index in LAYERS:
        means, receipts = semantic_means(torch, tokenizer, model, device, layers[layer_index])
        geometry_by_layer[layer_index] = build_geometry(torch, means)
        geometry_receipts[str(layer_index)] = {
            "basis_rows_sha256": canonical_sha(receipts),
            "vectors": {
                semantic: {
                    kind: base.tensor_sha(vec)
                    for kind, vec in geom.items()
                    if kind != "competitors"
                }
                for semantic, geom in geometry_by_layer[layer_index].items()
            },
        }

    all_turns: list[dict[str, Any]] = []
    trace_fh = trace_path.open("w", encoding="utf-8")
    try:
        for episode in range(args.episodes):
            spec = episode_spec(episode)
            baseline = target_infer(
                torch, tokenizer, model, device, layers, abc_ids, spec["prompt"], spec["seed"], None, 20
            )
            baseline_score = score_for_code(baseline["token_logits"], spec["target_code"])
            history: list[dict[str, Any]] = []
            for turn in range(args.turns):
                cprompt = controller_prompt(spec, history)
                controller_logits = model_choice_logits(torch, tokenizer, model, device, cprompt, controller_ids)
                selected = int(max(controller_logits, key=controller_logits.get))
                executed, policy = exploration_override(episode, turn, selected)
                vector, layer_index, gain = resolve_action_vector(torch, geometry_by_layer, spec["semantic_target"], executed)
                target = target_infer(
                    torch,
                    tokenizer,
                    model,
                    device,
                    layers,
                    abc_ids,
                    spec["prompt"],
                    spec["seed"] + turn + 1,
                    vector,
                    layer_index,
                )
                score = score_for_code(target["token_logits"], spec["target_code"])
                row = {
                    "schema": TRACE_SCHEMA,
                    "episode": episode,
                    "turn": turn,
                    "semantic_target": spec["semantic_target"],
                    "target_code": spec["target_code"],
                    "mapping": spec["mapping"],
                    "target_prompt": spec["prompt"],
                    "target_prompt_sha256": hashlib.sha256(spec["prompt"].encode("utf-8")).hexdigest(),
                    "controller_prompt": cprompt,
                    "controller_prompt_sha256": hashlib.sha256(cprompt.encode("utf-8")).hexdigest(),
                    "controller_selected_action": selected,
                    "controller_action_logits": controller_logits,
                    "executed_action": executed,
                    "executed_action_spec": ACTION_SPECS[executed],
                    "execution_policy": policy,
                    "vector_sha256": base.tensor_sha(vector) if vector is not None else None,
                    "layer": layer_index,
                    "gain": gain,
                    "target_output": target["best_label"],
                    "target_logits": target["token_logits"],
                    "target_score": score,
                    "baseline_score": baseline_score,
                    "baseline_output": baseline["best_label"],
                    "delta_vs_baseline": score - baseline_score,
                    "target_runtime": {
                        "activation_site": target["activation_site"],
                        "hook_calls": target["hook_calls"],
                        "applied_vector_sha256": target["applied_vector_sha256"],
                        "applied_vector_l2": target["applied_vector_l2"],
                    },
                    "roles": {
                        "controller_model": base.MODEL_ID,
                        "target_model": base.MODEL_ID,
                        "shared_weights": True,
                        "separate_inference_contexts": True,
                        "controller_text_delivered_to_target": False,
                    },
                }
                row["turn_sha256"] = canonical_sha(row)
                trace_fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
                trace_fh.flush()
                history.append(row)
                all_turns.append(row)
    finally:
        trace_fh.close()

    stats = action_stats(all_turns)
    native_results: list[dict[str, Any]] = []
    native_status = "SKIPPED_BY_ARGUMENT" if args.skip_native else "PENDING"
    if not args.skip_native:
        if not (args.llama_root and args.gguf and args.harness):
            raise RuntimeError("NATIVE_PATHS_REQUIRED_UNLESS_SKIP_NATIVE")
        llama_root = Path(args.llama_root).resolve()
        gguf = Path(args.gguf).resolve()
        harness = Path(args.harness).resolve()
        native_identity = validate_native_runtime(gguf, llama_root, harness)
        native_identity.update({
            "source_checkpoint_sha256": checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "python_runtime_build_sha256": canonical_sha(base.runtime_manifest(torch, transformers, model)),
        })
        api_state = native.NativeApiState(harness, gguf, llama_root, out / "native", native_identity)
        selected_stats = [r for r in stats if r["action_id"] != 0][: max(1, args.native_top_k)]
        for rank, stat in enumerate(selected_stats, start=1):
            semantic_target = str(stat["semantic_target"])
            action_id = int(stat["action_id"])
            spec = ACTION_SPECS[action_id]
            layer_index = int(spec["layer"])
            gain = float(spec["gain"])
            kind = str(spec["kind"])
            unit_vector = geometry_by_layer[layer_index][semantic_target][kind]
            candidate_key = f"rank{rank}-{semantic_target.lower()}-a{action_id}"
            cdir = out / "native" / "cvec" / candidate_key
            controls = native.make_control_files(torch, unit_vector, gain, layer_index, cdir)
            api_state.register(candidate_key, layer_index, gain, controls)
            response = api_state.execute({
                "schema": "CLAY_FORSCHUNGSRUN1_NATIVE_REPLAY_REQUEST/v1",
                "candidate_key": candidate_key,
                "cases": native_holdout_cases(semantic_target, candidate_key),
            })
            rows = response["rows"]
            measured = native.metrics(rows)
            native_results.append({
                "rank_from_fast_search": rank,
                "semantic_target": semantic_target,
                "action_id": action_id,
                "action": spec,
                "fast_search_stat": stat,
                "native_metrics": measured,
                "native_response_sha256": response["response_sha256"],
                "rows_sha256": canonical_sha(rows),
                "token_scope_transfer_test": {
                    "fast_scope": "PYTORCH_LAYER_OUTPUT_LAST_PROMPT_TOKEN",
                    "native_scope": "PINNED_LLAMA_CPP_CVEC_NATIVE_PROMPT_SCOPE",
                    "interpretation": "agreement supports cross-runtime transfer; disagreement is a token-scope/runtime boundary, not silent failure",
                },
            })
        native_status = "COMPLETE"

    controller_policy_turns = [r for r in all_turns if r["execution_policy"] == "CONTROLLER_POLICY"]
    controller_positive = [r for r in controller_policy_turns if float(r["delta_vs_baseline"]) > 0]
    summary_core = {
        "schema": SCHEMA,
        "status": "COMPLETE",
        "started_at_utc": started,
        "finished_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": {
            "repo_head": base.git_text("rev-parse", "HEAD"),
            "repo_tree": base.git_text("rev-parse", "HEAD^{tree}"),
            "executor_sha256": native.sha_file(Path(__file__)),
        },
        "model": {
            "id": base.MODEL_ID,
            "revision": base.MODEL_REVISION,
            "checkpoint_sha256": checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "weight_manifest_sha256": canonical_sha(weight_manifest),
            "runtime_manifest": base.runtime_manifest(torch, transformers, model),
            "logical_roles": 2,
            "resident_model_copies_claimed": 1,
            "shared_weights": True,
            "separate_inference_contexts": True,
        },
        "experiment": {
            "episodes": args.episodes,
            "turns_per_episode": args.turns,
            "dialogue_turns": len(all_turns),
            "target_baseline_calls": args.episodes,
            "controller_policy_turns": len(controller_policy_turns),
            "controller_policy_positive_delta_fraction": (
                len(controller_positive) / len(controller_policy_turns) if controller_policy_turns else None
            ),
            "controller_to_target_text_leakage": False,
            "action_count": ACTION_COUNT,
            "action_specs": ACTION_SPECS,
            "geometry_receipts": geometry_receipts,
            "fast_token_scope": "last_prompt_token_only",
            "native_replay_status": native_status,
        },
        "fast_search_action_stats": stats,
        "native_replay": native_results,
        "trace": {
            "path": str(trace_path),
            "sha256": native.sha_file(trace_path),
            "rows": len(all_turns),
            "contains_full_controller_prompts": True,
            "contains_full_target_prompts": True,
            "contains_controller_action_logits": True,
            "contains_target_logits": True,
        },
        "evidence_boundary": {
            "full_jspace_control_established": False,
            "canonical_semantics_minted": False,
            "whole_hcu_runtime_credit": False,
            "whole_entityos_runtime_credit": False,
            "training_credit": False,
            "external_llm_provider_used": False,
            "paid_provider_used": False,
            "claim": "adaptive two-role Qwen3-0.6B search plus bounded native matched-control transfer evidence only",
        },
    }
    summary = {**summary_core, "result_sha256": canonical_sha(summary_core)}
    result_path.write_text(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": summary["status"],
        "dialogue_turns": len(all_turns),
        "trace_sha256": summary["trace"]["sha256"],
        "native_replay_status": native_status,
        "native_candidates": len(native_results),
        "result_sha256": summary["result_sha256"],
        "result_path": str(result_path),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
