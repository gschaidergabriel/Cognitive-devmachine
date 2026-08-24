#!/usr/bin/env python3
"""Trigger-1 V4 scientific-independence successor for local Qwen3-0.6B.

This executor keeps the current provider-independent, loopback-only, six-control
mid-layer intervention path, but removes two Promotion Gate v4 confounds:

1. The steering direction is derived from semantic stance prompts whose token
   streams are fail-closed against the evaluation output-label token IDs.
2. Holdout scoring counterbalances the semantic target across A/B/C output
   labels, so no single output token is privileged by the evaluation metric.

The vector is still injected at the same non-terminal residual site and must
survive downstream transformer computation. Source presence is not runtime
evidence and this file mints no canonical/HCU/J-Space/training credit by itself.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
from http.server import ThreadingHTTPServer
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "tools" / "trigger1_local_qwen06_midlayer_causal_execute.py"
_SPEC = importlib.util.spec_from_file_location("clay_trigger1_midlayer_v3_base", BASE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("TRIGGER1_MIDLAYER_BASE_MODULE_LOAD_FAILED")
base = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = base
_SPEC.loader.exec_module(base)

SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_SEMANTIC_COUNTERBALANCED_EXPERIMENT/v1"
VECTOR_DERIVATION_METHOD = "INTERMEDIATE_SEMANTIC_ACTIVATION_CONTRAST_MEAN"
SEM_TARGET = "APPROVAL"
SEM_ALT1 = "REJECTION"
SEM_ALT2 = "UNCERTAINTY"
SEMANTIC_CLASSES = (SEM_TARGET, SEM_ALT1, SEM_ALT2)

BASIS_PROMPTS = (
    (4101, SEM_TARGET, "/no_think\nInternal stance: endorse the proposal because its expected consequences are beneficial. Preserve the stance internally."),
    (4102, SEM_ALT1, "/no_think\nInternal stance: oppose the proposal because its expected consequences are harmful. Preserve the stance internally."),
    (4103, SEM_ALT2, "/no_think\nInternal stance: withhold judgment because the evidence is insufficient. Preserve the stance internally."),
    (4111, SEM_TARGET, "/no_think\nLatent disposition: favor proceeding because the evidence supports a beneficial outcome. Keep only the disposition in mind."),
    (4112, SEM_ALT1, "/no_think\nLatent disposition: favor stopping because the evidence supports a harmful outcome. Keep only the disposition in mind."),
    (4113, SEM_ALT2, "/no_think\nLatent disposition: remain undecided because the evidence is mixed. Keep only the disposition in mind."),
)

# Every semantic class occupies every output label exactly once in each split.
GAIN_CASES = (
    (
        5101,
        {SEM_TARGET: "A", SEM_ALT1: "B", SEM_ALT2: "C"},
        "/no_think\nUse the code key A=approve, B=reject, C=uncertain. A proposal has some promised benefit but incomplete evidence. Return one code only.",
    ),
    (
        5102,
        {SEM_TARGET: "B", SEM_ALT1: "C", SEM_ALT2: "A"},
        "/no_think\nUse the code key A=uncertain, B=approve, C=reject. A proposal has mixed evidence and a plausible upside. Return one code only.",
    ),
    (
        5103,
        {SEM_TARGET: "C", SEM_ALT1: "A", SEM_ALT2: "B"},
        "/no_think\nUse the code key A=reject, B=uncertain, C=approve. A proposal has a plausible benefit but unresolved caveats. Return one code only.",
    ),
)
HOLDOUT_CASES = (
    (
        6101,
        {SEM_TARGET: "A", SEM_ALT1: "C", SEM_ALT2: "B"},
        "/no_think\nCode key: A=approve, B=uncertain, C=reject. The policy may help, but the current evidence is not decisive. Output one code only.",
    ),
    (
        6102,
        {SEM_TARGET: "B", SEM_ALT1: "A", SEM_ALT2: "C"},
        "/no_think\nCode key: A=reject, B=approve, C=uncertain. The intervention may be useful, though important uncertainty remains. Output one code only.",
    ),
    (
        6103,
        {SEM_TARGET: "C", SEM_ALT1: "B", SEM_ALT2: "A"},
        "/no_think\nCode key: A=uncertain, B=reject, C=approve. The change could improve outcomes, but the evidence is still incomplete. Output one code only.",
    ),
)


def _validate_mapping(mapping: dict[str, str]) -> None:
    if set(mapping) != set(SEMANTIC_CLASSES):
        raise ValueError("SEMANTIC_MAPPING_KEYS_INVALID")
    labels = list(mapping.values())
    if sorted(labels) != ["A", "B", "C"]:
        raise ValueError("OUTPUT_LABEL_MAPPING_MUST_BE_ABC_PERMUTATION")


def counterbalance_proof(cases: tuple[tuple[int, dict[str, str], str], ...]) -> dict[str, Any]:
    counts = {semantic: {label: 0 for label in ("A", "B", "C")} for semantic in SEMANTIC_CLASSES}
    for _seed, mapping, _prompt in cases:
        _validate_mapping(mapping)
        for semantic, label in mapping.items():
            counts[semantic][label] += 1
    complete = all(all(counts[semantic][label] == 1 for label in ("A", "B", "C")) for semantic in SEMANTIC_CLASSES)
    return {
        "complete_latin_counterbalance": complete,
        "counts": counts,
        "case_count": len(cases),
    }


def _token_ids_in_prompt(tokenizer: Any, prompt: str) -> set[int]:
    encoded = tokenizer.encode(prompt, add_special_tokens=False)
    return {int(x) for x in encoded}


def assert_basis_omits_evaluation_output_tokens(tokenizer: Any, token_ids: dict[str, int]) -> list[dict[str, Any]]:
    forbidden = set(map(int, token_ids.values()))
    receipts: list[dict[str, Any]] = []
    for seed, semantic, prompt in BASIS_PROMPTS:
        observed = _token_ids_in_prompt(tokenizer, prompt)
        overlap = sorted(observed & forbidden)
        if overlap:
            raise RuntimeError(f"BASIS_PROMPT_EVALUATION_OUTPUT_TOKEN_LEAK:{seed}:{overlap}")
        receipts.append(
            {
                "seed": seed,
                "semantic_class": semantic,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "evaluation_output_token_overlap": overlap,
            }
        )
    return receipts


def semantic_activation_basis(
    torch: Any,
    tokenizer: Any,
    model: Any,
    device: Any,
    layer: Any,
    token_ids: dict[str, int],
):
    leakage_receipts = assert_basis_omits_evaluation_output_tokens(tokenizer, token_ids)
    rows: dict[str, list[Any]] = {semantic: [] for semantic in SEMANTIC_CLASSES}
    activation_receipts: list[dict[str, Any]] = []
    leakage_by_seed = {int(r["seed"]): r for r in leakage_receipts}

    for seed, semantic, prompt in BASIS_PROMPTS:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        activation = base.extract_internal_activation(torch, tokenizer, model, device, layer, prompt)
        rows[semantic].append(activation)
        activation_receipts.append(
            {
                **leakage_by_seed[seed],
                "activation_sha256": base.tensor_sha(activation),
            }
        )

    means = {semantic: torch.stack(values, dim=0).mean(dim=0) for semantic, values in rows.items()}
    raw = means[SEM_TARGET] - 0.5 * (means[SEM_ALT1] + means[SEM_ALT2])
    norm = torch.linalg.vector_norm(raw)
    if not bool(torch.isfinite(norm)) or float(norm) <= 1e-12:
        raise RuntimeError("SEMANTIC_INTERNAL_CONTRASTIVE_BASIS_DEGENERATE")
    return (raw / norm).to(device), activation_receipts


class CounterbalancedRuntimeState:
    def __init__(
        self,
        torch: Any,
        tokenizer: Any,
        model: Any,
        device: Any,
        layer: Any,
        layer_index: int,
        base_vector: Any,
        token_ids: dict[str, int],
    ):
        self.torch = torch
        self.tokenizer = tokenizer
        self.model = model
        self.device = device
        self.layer = layer
        self.layer_index = int(layer_index)
        self.base_vector = base_vector
        self.token_ids = token_ids
        self.lock = threading.Lock()
        self.invocations = 0

    def infer(self, payload: dict[str, Any]) -> dict[str, Any]:
        prompt = str(payload.get("prompt") or "")
        control = str(payload.get("control") or "")
        gain = float(payload.get("gain") or 0.0)
        seed = int(payload.get("seed"))
        mapping = payload.get("semantic_to_output_label")
        if not isinstance(mapping, dict):
            raise ValueError("SEMANTIC_TO_OUTPUT_LABEL_MAPPING_REQUIRED")
        mapping = {str(k): str(v) for k, v in mapping.items()}
        _validate_mapping(mapping)
        if control not in base.CONTROLS:
            raise ValueError("UNKNOWN_CONTROL")

        family = base.matched_family(self.torch, self.base_vector, gain)
        vector = family[control].to(self.device)
        applied_sha = base.tensor_sha(vector)
        hook_calls = 0
        applied_l2 = float(self.torch.linalg.vector_norm(vector).detach().cpu())

        def hook(_module: Any, _inputs: Any, output: Any):
            nonlocal hook_calls
            hook_calls += 1
            if control == "BASELINE":
                return output
            hidden = base.unpack_hidden(output).clone()
            hidden[:, -1, :] = hidden[:, -1, :] + vector.to(dtype=hidden.dtype)
            return base.replace_hidden(output, hidden)

        with self.lock:
            self.torch.manual_seed(seed)
            if self.torch.cuda.is_available():
                self.torch.cuda.manual_seed_all(seed)
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            handle = self.layer.register_forward_hook(hook)
            try:
                with self.torch.no_grad():
                    output = self.model(**inputs)
                    logits = output.logits[0, -1].float().detach().cpu()
            finally:
                handle.remove()
            self.invocations += 1

        label_logits = {
            label: float(logits[self.token_ids[label]])
            for label in ("A", "B", "C")
        }
        semantic_logits = {
            semantic: label_logits[mapping[semantic]]
            for semantic in SEMANTIC_CLASSES
        }
        target_score = semantic_logits[SEM_TARGET] - 0.5 * (
            semantic_logits[SEM_ALT1] + semantic_logits[SEM_ALT2]
        )
        material = {
            "invocation": self.invocations,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "control": control,
            "gain": gain,
            "seed": seed,
            "activation_site": f"model.model.layers[{self.layer_index}]:output:last_token",
            "applied_vector_sha256": applied_sha,
            "applied_vector_l2": applied_l2,
            "hook_calls": hook_calls,
            "semantic_to_output_label": mapping,
            "label_logits": label_logits,
            "semantic_logits": semantic_logits,
            "target_score": target_score,
            "best_semantic_class": max(semantic_logits, key=semantic_logits.get),
        }
        return {
            **material,
            "runtime_receipt_sha256": base.canonical_sha(material),
            "runtime_observed_intervention": bool(hook_calls > 0 and control != "BASELINE"),
        }


def _run_cases(
    endpoint: str,
    cases: tuple[tuple[int, dict[str, str], str], ...],
    gains: tuple[float, ...],
    controls: tuple[str, ...],
    family_prefix: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for gain in gains:
        for seed, mapping, prompt in cases:
            for control in controls:
                row = base.post_json(
                    endpoint,
                    {
                        "prompt": prompt,
                        "control": control,
                        "gain": gain,
                        "seed": seed,
                        "semantic_to_output_label": mapping,
                    },
                )
                row["prompt_family"] = f"{family_prefix}-{seed}"
                rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", default=os.getenv("HF_HOME") or str(Path.home() / ".cache" / "huggingface"))
    args = ap.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "trigger1_local_activation_api_result.json"
    candidate_path = out / "trigger1_direct_steering_candidate.json"
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    source = {
        "repo_head": base.git_text("rev-parse", "HEAD"),
        "repo_tree": base.git_text("rev-parse", "HEAD^{tree}"),
        "repo_dirty_porcelain_sha256": base.canonical_sha(base.git_text("status", "--porcelain=v1")),
        "executor_sha256": base.sha256_file(Path(__file__)),
        "base_executor_sha256": base.sha256_file(BASE_PATH),
    }

    server: ThreadingHTTPServer | None = None
    try:
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
            layer_index,
        ) = base.load_exact_runtime(Path(args.cache_dir))
        token_ids, token_labels = base.resolve_token_triplet(tokenizer)
        if {key: str(value).strip() for key, value in token_labels.items()} != {"A": "A", "B": "B", "C": "C"}:
            raise RuntimeError(f"COUNTERBALANCED_ABC_OUTPUT_LABELS_REQUIRED:{token_labels}")
        layers = model.model.layers
        layer = layers[layer_index]
        base_vector, basis_receipts = semantic_activation_basis(
            torch, tokenizer, model, device, layer, token_ids
        )
        runtime = base.runtime_manifest(torch, transformers, model)
        runtime_build_sha = base.canonical_sha(runtime)
        num_layers = len(layers)
        downstream_layers = num_layers - layer_index - 1
        if downstream_layers < 1:
            raise RuntimeError("NO_DOWNSTREAM_TRANSFORMER_COMPUTATION")

        calibration_counterbalance = counterbalance_proof(GAIN_CASES)
        holdout_counterbalance = counterbalance_proof(HOLDOUT_CASES)
        if not calibration_counterbalance["complete_latin_counterbalance"]:
            raise RuntimeError("GAIN_CASES_NOT_COUNTERBALANCED")
        if not holdout_counterbalance["complete_latin_counterbalance"]:
            raise RuntimeError("HOLDOUT_CASES_NOT_COUNTERBALANCED")

        activation_site = f"model.model.layers[{layer_index}]:output:last_token"
        basis_family_id = base.canonical_sha(
            [{"seed": seed, "semantic": semantic, "prompt": prompt} for seed, semantic, prompt in BASIS_PROMPTS]
        )
        derivation_receipt_sha = base.canonical_sha(basis_receipts)
        source_packet = {
            "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "intent": "causally shift an internal semantic stance toward approval before downstream transformer computation",
            "basis": "semantic internal activation contrast; no output-head weights, holdout data, or evaluation output-label token IDs used",
            "basis_family_id": basis_family_id,
            "derivation_receipt_sha256": derivation_receipt_sha,
            "model": base.MODEL_ID,
            "revision": base.MODEL_REVISION,
            "activation_site": activation_site,
        }
        source_packet_sha = base.canonical_sha(source_packet)
        adapter = {
            "schema": "JSPACE_LATENT_BASIS_ADAPTER/v1",
            "model": base.MODEL_ID,
            "revision": base.MODEL_REVISION,
            "activation_site": activation_site,
            "hidden_size": int(base_vector.numel()),
            "construction": (
                "mean internal activation(APPROVAL)-0.5*(mean internal activation(REJECTION)+"
                "mean internal activation(UNCERTAINTY)), normalized"
            ),
            "basis_constructed_without_output_head": True,
            "basis_uses_holdout_data": False,
            "basis_uses_evaluation_output_labels": False,
            "basis_evaluation_output_token_overlap": [],
            "downstream_transformer_layers": downstream_layers,
            "terminal_output_projection_shortcut": False,
        }
        adapter_sha = base.canonical_sha(adapter)
        local_vector_sha = base.tensor_sha(base_vector)

        state = CounterbalancedRuntimeState(
            torch, tokenizer, model, device, layer, layer_index, base_vector, token_ids
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), base.make_handler(state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/jspace/logits"

        calibration_rows = _run_cases(
            endpoint,
            GAIN_CASES,
            tuple(base.GAIN_GRID),
            ("BASELINE", "+VECTOR", "SIGN_FLIP"),
            "gain-cal",
        )
        selected_gain = base.select_gain(calibration_rows)

        holdout_rows: list[dict[str, Any]] = []
        if selected_gain is not None:
            holdout_rows = _run_cases(
                endpoint,
                HOLDOUT_CASES,
                (float(selected_gain),),
                tuple(base.CONTROLS),
                "hold",
            )
        verdict = base.adjudicate(holdout_rows, selected_gain)

        controls: dict[str, Any] = {}
        for control in base.CONTROLS:
            receipts = [r["runtime_receipt_sha256"] for r in holdout_rows if r["control"] == control]
            controls[control] = {
                "runtime_receipt_sha256": base.canonical_sha(receipts),
                "observations": len(receipts),
            }

        plus_rows = [r for r in holdout_rows if r["control"] == "+VECTOR"]
        applied_vector_sha = (
            plus_rows[0]["applied_vector_sha256"]
            if plus_rows
            else base.tensor_sha(base_vector * float(selected_gain or 0.0))
        )
        intervention_receipt_sha = base.canonical_sha(
            [r["runtime_receipt_sha256"] for r in plus_rows]
        )
        metric_definition = {
            "schema": "TRIGGER1_COUNTERBALANCED_SEMANTIC_OUTPUT_TOKEN_METRIC/v1",
            "formula": "logit(mapped(APPROVAL))-0.5*(logit(mapped(REJECTION))+logit(mapped(UNCERTAINTY)))",
            "token_ids": token_ids,
            "token_labels": token_labels,
            "holdout_mappings": [mapping for _seed, mapping, _prompt in HOLDOUT_CASES],
            "label_mapping_counterbalanced": True,
            "counterbalance_proof": holdout_counterbalance,
        }
        metric_definition_sha = base.canonical_sha(metric_definition)
        analysis_receipt_sha = base.canonical_sha(
            {
                "verdict": verdict,
                "holdout_receipts": [r["runtime_receipt_sha256"] for r in holdout_rows],
                "metric_definition_sha256": metric_definition_sha,
            }
        )
        local_runtime_receipt = base.canonical_sha(
            {
                "endpoint": endpoint,
                "runtime_build_sha256": runtime_build_sha,
                "checkpoint_sha256": checkpoint_sha,
                "tokenizer_sha256": tokenizer_sha,
                "source": source,
                "activation_site": activation_site,
                "api_invocations": state.invocations,
            }
        )

        candidate = {
            "schema": base.CANDIDATE_SCHEMA,
            "runtime_intervention_class": "LOCAL_PYTORCH_ACTIVATION_INTERVENTION",
            "source_identity": {
                "repo_head": source["repo_head"],
                "runtime_build_sha256": runtime_build_sha,
                "checkpoint_sha256": checkpoint_sha,
                "tokenizer_sha256": tokenizer_sha,
            },
            "intervention": {
                "runtime_observed": bool(
                    plus_rows and all(r["hook_calls"] > 0 for r in plus_rows)
                ),
                "invocation_id": base.canonical_sha(
                    [r["runtime_receipt_sha256"] for r in holdout_rows]
                ),
                "activation_site": activation_site,
                "source_packet_sha256": source_packet_sha,
                "adapter_sha256": adapter_sha,
                "local_vector_sha256": local_vector_sha,
                "applied_vector_sha256": applied_vector_sha,
                "runtime_intervention_receipt_sha256": intervention_receipt_sha,
                "gain": selected_gain,
                "layer_start": layer_index,
                "layer_end": layer_index,
                "downstream_transformer_layers": downstream_layers,
                "terminal_output_projection_shortcut": False,
                "basis_constructed_without_output_head": True,
            },
            "controls": controls,
            "calibration": {
                "family_id": base.canonical_sha(
                    [{"seed": seed, "mapping": mapping, "prompt": prompt} for seed, mapping, prompt in GAIN_CASES]
                ),
                "seeds": [seed for seed, _mapping, _prompt in GAIN_CASES],
                "selected_gain": selected_gain,
                "label_mapping_counterbalanced": True,
                "counterbalance_proof": calibration_counterbalance,
            },
            "holdout": {
                "family_id": base.canonical_sha(
                    [{"seed": seed, "mapping": mapping, "prompt": prompt} for seed, mapping, prompt in HOLDOUT_CASES]
                ),
                "seeds": [seed for seed, _mapping, _prompt in HOLDOUT_CASES],
                "reproducible_directional_effect": bool(verdict.get("pass")),
                "strongest_counterexample_recorded": True,
                "analysis_receipt_sha256": analysis_receipt_sha,
                "evaluation_independent_of_vector_derivation": True,
                "metric_definition_sha256": metric_definition_sha,
                "metric_uses_output_tokens": True,
                "label_mapping_counterbalanced": True,
            },
            "vector_derivation": {
                "method": VECTOR_DERIVATION_METHOD,
                "uses_output_head_weights": False,
                "uses_holdout_data": False,
                "uses_evaluation_output_labels": False,
                "derivation_family_id": basis_family_id,
                "derivation_receipt_sha256": derivation_receipt_sha,
            },
            "transport": {
                "hosted_prompt_only": False,
                "api_served": True,
                "loopback_only": True,
                "endpoint": endpoint,
            },
            "target": {
                "relation": "ZERO_COST_API_SERVED_MODEL_RUNTIME",
                "execution_surface": "LOCAL_LOOPBACK_API",
                "zero_provider_billing": True,
                "local_runtime_execution_receipt_sha256": local_runtime_receipt,
                "provider": "local",
                "model_or_route": f"{base.MODEL_ID}@{base.MODEL_REVISION}",
            },
        }

        result = {
            "schema": SCHEMA,
            "status": "PASS" if verdict.get("pass") else "SCIENTIFIC_NEGATIVE",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "model": base.MODEL_ID,
            "model_revision": base.MODEL_REVISION,
            "checkpoint_weight_manifest": weight_manifest,
            "checkpoint_sha256": checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "token_ids": token_ids,
            "token_labels": token_labels,
            "device": str(device),
            "runtime_manifest": runtime,
            "runtime_build_sha256": runtime_build_sha,
            "activation_site": activation_site,
            "layer_index": layer_index,
            "num_hidden_layers": num_layers,
            "downstream_transformer_layers": downstream_layers,
            "basis_constructed_without_output_head": True,
            "basis_uses_holdout_data": False,
            "basis_uses_evaluation_output_labels": False,
            "basis_receipts": basis_receipts,
            "basis_family_id": basis_family_id,
            "derivation_receipt_sha256": derivation_receipt_sha,
            "source_packet": source_packet,
            "source_packet_sha256": source_packet_sha,
            "adapter": adapter,
            "adapter_sha256": adapter_sha,
            "local_vector_sha256": local_vector_sha,
            "metric_definition": metric_definition,
            "metric_definition_sha256": metric_definition_sha,
            "calibration_counterbalance": calibration_counterbalance,
            "holdout_counterbalance": holdout_counterbalance,
            "api_endpoint": endpoint,
            "api_loopback_only": True,
            "zero_provider_billing": True,
            "external_provider_credentials_read": False,
            "gain_calibration_rows": calibration_rows,
            "selected_gain": selected_gain,
            "holdout_rows": holdout_rows,
            "verdict": verdict,
            "promotion_candidate_written": bool(verdict.get("pass")),
            "evidence_boundary": (
                "A PASS is only a candidate for Promotion Gate v4 review: semantic vector derivation "
                "is disjoint from holdout and evaluation output-label token IDs, and output-token "
                "evaluation is counterbalanced. No canonical EntityOS/HCU, full J-Space, or training "
                "credit is minted here."
            ),
        }
        result["result_sha256"] = base.canonical_sha(result)
        result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        if verdict.get("pass"):
            candidate_path.write_text(
                json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            return 0
        if candidate_path.exists():
            candidate_path.unlink()
        return 2
    except Exception as exc:
        blocked = {
            "schema": SCHEMA,
            "status": "BLOCKED_LOCAL_SEMANTIC_COUNTERBALANCED_FASTPATH",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "reason": f"{type(exc).__name__}:{str(exc)[:1000]}",
            "external_provider_credentials_read": False,
            "zero_provider_billing": True,
            "terminal_output_projection_shortcut": False,
            "next_action": "REPAIR_CURRENT_SEMANTIC_COUNTERBALANCED_LOCAL_BLOCKER",
        }
        blocked["result_sha256"] = base.canonical_sha(blocked)
        result_path.write_text(
            json.dumps(blocked, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return 3
    finally:
        if server is not None:
            try:
                server.shutdown()
                server.server_close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
