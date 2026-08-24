#!/usr/bin/env python3
"""Trigger-1 V4: semantic, counterbalanced Qwen3-0.6B mid-layer causal discriminator.

This successor closes the remaining output-label identity leak in the V3 mid-layer
experiment. The steering direction is derived only from nonterminal internal activations
for a semantic living-vs-nonliving contrast. Evaluation uses disjoint multiple-choice
items whose correct A/B/C answer token is exactly counterbalanced in both calibration
and holdout. The metric follows the correct semantic option rather than a fixed token.

The program is a zero-provider-billing local-loopback experiment source. Its existence
is not runtime evidence and it must still run behind the current source/lease/offline
execution fences before any promotion-bearing receipt can exist.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import threading
from http.server import ThreadingHTTPServer
from typing import Any

import trigger1_local_qwen06_midlayer_causal_execute as base
import trigger1_semantic_counterbalance_v1 as semantic

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_SEMANTIC_COUNTERBALANCED_EXPERIMENT/v1"
RESULT_NAME = "trigger1_semantic_counterbalanced_result.json"
CANDIDATE_NAME = "trigger1_semantic_counterbalanced_candidate.json"


class SemanticRuntimeState(base.RuntimeState):
    """Reuse the exact V3 hook/control machinery but score the semantic target label."""

    def infer(self, payload: dict[str, Any]) -> dict[str, Any]:
        correct_label = str(payload.get("correct_label") or "")
        if correct_label not in semantic.LABELS:
            raise ValueError("CORRECT_COUNTERBALANCED_LABEL_REQUIRED")
        row = super().infer(payload)
        row["correct_label"] = correct_label
        row["target_score"] = semantic.score_token_logits(row["token_logits"], correct_label)
        material = {
            key: value
            for key, value in row.items()
            if key not in {"runtime_receipt_sha256", "runtime_observed_intervention"}
        }
        row["runtime_receipt_sha256"] = base.canonical_sha(material)
        return row


def semantic_activation_basis(torch: Any, tokenizer: Any, model: Any, device: Any, layer: Any):
    positive: list[Any] = []
    negative: list[Any] = []
    receipts: list[dict[str, Any]] = []
    for semantic_class, cases, sink in (
        ("living", semantic.DERIVATION_POSITIVE, positive),
        ("nonliving", semantic.DERIVATION_NEGATIVE, negative),
    ):
        for seed, prompt in cases:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
            activation = base.extract_internal_activation(torch, tokenizer, model, device, layer, prompt)
            sink.append(activation)
            receipts.append(
                {
                    "seed": seed,
                    "semantic_class": semantic_class,
                    "prompt_sha256": base.hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "activation_sha256": base.tensor_sha(activation),
                }
            )
    living_mean = torch.stack(positive, dim=0).mean(dim=0)
    nonliving_mean = torch.stack(negative, dim=0).mean(dim=0)
    raw = living_mean - nonliving_mean
    norm = torch.linalg.vector_norm(raw)
    if not bool(torch.isfinite(norm)) or float(norm) <= 1e-12:
        raise RuntimeError("SEMANTIC_INTERNAL_CONTRASTIVE_BASIS_DEGENERATE")
    return (raw / norm).to(device), receipts


def _run_split(endpoint: str, cases: tuple[tuple[int, str, str], ...], gains: tuple[float, ...], controls: tuple[str, ...]):
    rows: list[dict[str, Any]] = []
    for gain in gains:
        for seed, correct_label, prompt in cases:
            for control in controls:
                row = base.post_json(
                    endpoint,
                    {
                        "prompt": f"/no_think\n{prompt}\nAnswer with only A, B, or C.",
                        "correct_label": correct_label,
                        "control": control,
                        "gain": gain,
                        "seed": seed,
                    },
                )
                row["prompt_family"] = f"semantic-{seed}"
                rows.append(row)
    return rows


def _controls_receipt(holdout_rows: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for control in base.CONTROLS:
        receipts = [r["runtime_receipt_sha256"] for r in holdout_rows if r["control"] == control]
        result[control] = {
            "runtime_receipt_sha256": base.canonical_sha(receipts),
            "observations": len(receipts),
        }
    return result


def main() -> int:
    contract = semantic.validate_contract()
    if not contract["pass"]:
        raise RuntimeError(f"SEMANTIC_COUNTERBALANCE_CONTRACT_INVALID:{contract['failures']}")

    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", default=os.getenv("HF_HOME") or str(Path.home() / ".cache" / "huggingface"))
    args = ap.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / RESULT_NAME
    candidate_path = out / CANDIDATE_NAME
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    source = {
        "repo_head": base.git_text("rev-parse", "HEAD"),
        "repo_tree": base.git_text("rev-parse", "HEAD^{tree}"),
        "repo_dirty_porcelain_sha256": base.canonical_sha(base.git_text("status", "--porcelain=v1")),
        "executor_sha256": base.sha256_file(Path(__file__)),
        "semantic_contract_sha256": base.sha256_file(ROOT / "tools" / "trigger1_semantic_counterbalance_v1.py"),
        "v3_runtime_substrate_sha256": base.sha256_file(ROOT / "tools" / "trigger1_local_qwen06_midlayer_causal_execute.py"),
    }

    server = None
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
        layer = model.model.layers[layer_index]
        base_vector, basis_receipts = semantic_activation_basis(torch, tokenizer, model, device, layer)
        derivation_receipt_sha = base.canonical_sha(basis_receipts)
        independence = semantic.scientific_independence_metadata(derivation_receipt_sha)
        runtime = base.runtime_manifest(torch, transformers, model)
        runtime_build_sha = base.canonical_sha(runtime)
        num_layers = len(model.model.layers)
        downstream_layers = num_layers - layer_index - 1
        if downstream_layers < 1:
            raise RuntimeError("NO_DOWNSTREAM_TRANSFORMER_COMPUTATION")

        activation_site = f"model.model.layers[{layer_index}]:output:last_token"
        source_packet = {
            "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "intent": "causally shift a nonterminal internal representation toward the semantic living-organism concept",
            "basis": "living-minus-nonliving contrastive internal activations; no output-head weights or evaluation answer-label mapping used",
            "target_concept": semantic.TARGET_CONCEPT,
            "basis_family_sha256": contract["derivation_family_id"],
            "metric_definition_sha256": contract["metric_definition_sha256"],
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
            "construction": "mean internal activation(living)-mean internal activation(nonliving), normalized",
            "basis_constructed_without_output_head": True,
            "basis_constructed_without_evaluation_output_labels": True,
            "downstream_transformer_layers": downstream_layers,
            "terminal_output_projection_shortcut": False,
        }
        adapter_sha = base.canonical_sha(adapter)
        local_vector_sha = base.tensor_sha(base_vector)

        state = SemanticRuntimeState(torch, tokenizer, model, device, layer, layer_index, base_vector, token_ids)
        server = ThreadingHTTPServer(("127.0.0.1", 0), base.make_handler(state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/jspace/logits"

        calibration_rows = _run_split(
            endpoint,
            semantic.CALIBRATION_CASES,
            tuple(base.GAIN_GRID),
            ("BASELINE", "+VECTOR", "SIGN_FLIP"),
        )
        selected_gain = base.select_gain(calibration_rows)
        holdout_rows: list[dict[str, Any]] = []
        if selected_gain is not None:
            holdout_rows = _run_split(
                endpoint,
                semantic.HOLDOUT_CASES,
                (float(selected_gain),),
                tuple(base.CONTROLS),
            )
        verdict = base.adjudicate(holdout_rows, selected_gain)
        controls = _controls_receipt(holdout_rows)

        plus_rows = [r for r in holdout_rows if r["control"] == "+VECTOR"]
        applied_vector_sha = (
            plus_rows[0]["applied_vector_sha256"]
            if plus_rows
            else base.tensor_sha(base_vector * float(selected_gain or 0.0))
        )
        intervention_receipt_sha = base.canonical_sha([r["runtime_receipt_sha256"] for r in plus_rows])
        analysis_receipt_sha = base.canonical_sha(
            {"verdict": verdict, "holdout_receipts": [r["runtime_receipt_sha256"] for r in holdout_rows]}
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
                "semantic_contract": contract,
            }
        )

        holdout = {
            "family_id": contract["holdout_family_id"],
            "seeds": [seed for seed, _, _ in semantic.HOLDOUT_CASES],
            "reproducible_directional_effect": bool(verdict.get("pass")),
            "strongest_counterexample_recorded": True,
            "analysis_receipt_sha256": analysis_receipt_sha,
            **independence["holdout_science"],
        }
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
                "runtime_observed": bool(plus_rows and all(r["hook_calls"] > 0 for r in plus_rows)),
                "invocation_id": base.canonical_sha([r["runtime_receipt_sha256"] for r in holdout_rows]),
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
                "family_id": contract["calibration_family_id"],
                "basis_family_id": contract["derivation_family_id"],
                "seeds": [seed for seed, _, _ in semantic.CALIBRATION_CASES],
                "basis_seeds": [seed for seed, _ in (*semantic.DERIVATION_POSITIVE, *semantic.DERIVATION_NEGATIVE)],
                "selected_gain": selected_gain,
                "label_mapping_counterbalanced": True,
            },
            "holdout": holdout,
            "vector_derivation": independence["vector_derivation"],
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
            "semantic_counterbalance_contract": contract,
            "basis_constructed_without_output_head": True,
            "basis_constructed_without_evaluation_output_labels": True,
            "basis_receipts": basis_receipts,
            "source_packet": source_packet,
            "source_packet_sha256": source_packet_sha,
            "adapter": adapter,
            "adapter_sha256": adapter_sha,
            "local_vector_sha256": local_vector_sha,
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
                "A PASS is only a candidate for the current Trigger-1 promotion gate: nonterminal model-specific "
                "internal intervention, semantic derivation independent of evaluation answer labels, counterbalanced "
                "token mapping, downstream computation and matched controls. It does not mint canonical EntityOS/HCU, "
                "full J-Space-model or training credit."
            ),
        }
        result["result_sha256"] = base.canonical_sha(result)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        if verdict.get("pass"):
            candidate_path.write_text(json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
            return 0
        if candidate_path.exists():
            candidate_path.unlink()
        return 2
    except Exception as exc:
        blocked = {
            "schema": SCHEMA,
            "status": "BLOCKED",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "error_class": type(exc).__name__,
            "error": str(exc)[:1000],
            "promotion_candidate_written": False,
        }
        blocked["result_sha256"] = base.canonical_sha(blocked)
        result_path.write_text(json.dumps(blocked, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        if candidate_path.exists():
            candidate_path.unlink()
        return 3
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
