#!/usr/bin/env python3
"""Trigger-1 non-terminal Qwen3-0.6B hidden-state steering experiment.

This experiment is deliberately distinct from the terminal output-head positive control.
It injects a vector at a fixed middle decoder layer and requires the effect to propagate
through substantive downstream transformer computation before the scored lm_head readout.
The probe vector is an input-embedding contrast (A vs B/C), not the scored lm_head contrast,
and tied input/output embeddings fail closed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import threading
from http.server import ThreadingHTTPServer
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "tools" / "trigger1_local_qwen06_activation_api_execute.py"
_SPEC = importlib.util.spec_from_file_location("clay_trigger1_shared_local_harness", BASE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("TRIGGER1_BASE_MODULE_LOAD_FAILED")
base = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = base
_SPEC.loader.exec_module(base)

SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_INTERNAL_LAYER_API_EXPERIMENT/v1"
CANDIDATE_SCHEMA = base.CANDIDATE_SCHEMA
VECTOR_BASIS_CLASS = "INPUT_EMBEDDING_CONTRAST_A_VS_BC"


def input_embedding_probe_vector(torch: Any, model: Any, token_ids: dict[str, int]):
    if bool(getattr(model.config, "tie_word_embeddings", False)):
        raise RuntimeError("INPUT_OUTPUT_EMBEDDINGS_TIED_INDEPENDENT_BASIS_REQUIRED")
    weight = model.get_input_embeddings().weight.detach().float()
    v = weight[token_ids["A"]] - 0.5 * (weight[token_ids["B"]] + weight[token_ids["C"]])
    norm = torch.linalg.vector_norm(v)
    if not bool(torch.isfinite(norm)) or float(norm) <= 0:
        raise RuntimeError("INPUT_EMBEDDING_PROBE_VECTOR_DEGENERATE")
    return v / norm


def choose_internal_layer(model: Any) -> tuple[int, int, str]:
    layers = getattr(getattr(model, "model", None), "layers", None)
    if layers is None or len(layers) < 3:
        raise RuntimeError("NONTERMINAL_TRANSFORMER_LAYER_SURFACE_UNAVAILABLE")
    total = int(len(layers))
    layer_index = min(total - 2, max(0, total // 2))
    site = f"model.model.layers[{layer_index}]:output:last_token"
    return layer_index, total, site


class InternalLayerRuntimeState(base.RuntimeState):
    def __init__(
        self,
        torch: Any,
        tokenizer: Any,
        model: Any,
        device: Any,
        base_vector: Any,
        token_ids: dict[str, int],
        layer_index: int,
        num_hidden_layers: int,
        activation_site: str,
    ):
        super().__init__(torch, tokenizer, model, device, base_vector, token_ids)
        self.layer_index = int(layer_index)
        self.num_hidden_layers = int(num_hidden_layers)
        self.activation_site = str(activation_site)

    def infer(self, payload: dict[str, Any]) -> dict[str, Any]:
        prompt = str(payload.get("prompt") or "")
        control = str(payload.get("control") or "")
        gain = float(payload.get("gain") or 0.0)
        seed = int(payload.get("seed"))
        if control not in base.CONTROLS:
            raise ValueError("UNKNOWN_CONTROL")
        family = base.matched_family(self.torch, self.base_vector, gain)
        vector = family[control].to(self.device)
        applied_sha = base.tensor_sha(vector)
        hook_calls = 0

        def hook(_module: Any, _inputs: Any, output: Any):
            nonlocal hook_calls
            hook_calls += 1
            if control == "BASELINE":
                return output
            if isinstance(output, tuple):
                hidden = output[0].clone()
                hidden[:, -1, :] = hidden[:, -1, :] + vector.to(dtype=hidden.dtype)
                return (hidden, *output[1:])
            hidden = output.clone()
            hidden[:, -1, :] = hidden[:, -1, :] + vector.to(dtype=hidden.dtype)
            return hidden

        target_layer = self.model.model.layers[self.layer_index]
        with self.lock:
            self.torch.manual_seed(seed)
            if self.torch.cuda.is_available():
                self.torch.cuda.manual_seed_all(seed)
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            handle = target_layer.register_forward_hook(hook)
            try:
                with self.torch.no_grad():
                    output = self.model(**inputs)
                    logits = output.logits[0, -1].float().detach().cpu()
            finally:
                handle.remove()
            self.invocations += 1

        trio = {label: float(logits[token_id]) for label, token_id in self.token_ids.items()}
        score = trio["A"] - 0.5 * (trio["B"] + trio["C"])
        best = max(trio, key=trio.get)
        receipt_material = {
            "invocation": self.invocations,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "control": control,
            "gain": gain,
            "seed": seed,
            "applied_vector_sha256": applied_sha,
            "hook_calls": hook_calls,
            "activation_site": self.activation_site,
            "layer_index": self.layer_index,
            "num_hidden_layers": self.num_hidden_layers,
            "downstream_transformer_layers": self.num_hidden_layers - self.layer_index - 1,
            "vector_basis_class": VECTOR_BASIS_CLASS,
            "token_logits": trio,
            "target_score": score,
            "best_label": best,
        }
        return {
            **receipt_material,
            "runtime_receipt_sha256": base.canonical_sha(receipt_material),
            "runtime_observed_intervention": bool(hook_calls > 0 and control != "BASELINE"),
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", default=str(Path.home() / ".cache" / "huggingface"))
    args = ap.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "trigger1_local_activation_api_result.json"
    candidate_path = out / "trigger1_direct_steering_candidate.json"
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    source = {"repo_head": base.git_text("rev-parse", "HEAD"), "repo_tree": base.git_text("rev-parse", "HEAD^{tree}")}

    server: ThreadingHTTPServer | None = None
    try:
        torch, transformers, snapshot, tokenizer, model, device, checkpoint_sha, tokenizer_sha, weight_manifest = base.load_exact_runtime(Path(args.cache_dir))
        token_ids, token_labels = base.resolve_token_triplet(tokenizer)
        layer_index, num_hidden_layers, activation_site = choose_internal_layer(model)
        probe_vector = input_embedding_probe_vector(torch, model, token_ids).to(device)
        runtime = base.runtime_manifest(torch, transformers, model)
        runtime_build_sha = base.canonical_sha(runtime)

        source_packet = {
            "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "intent": "increase latent preference for semantic output label A relative to B and C",
            "basis": f"exact Qwen3-0.6B residual-stream coordinate system at {activation_site}",
            "vector_basis_class": VECTOR_BASIS_CLASS,
            "scored_readout_basis": "LM_HEAD_A_VS_BC",
            "algebraically_identical_to_scored_output_head_contrast": False,
            "token_labels": token_labels,
            "token_ids": token_ids,
            "model": base.MODEL_ID,
            "revision": base.MODEL_REVISION,
            "layer_index": layer_index,
            "num_hidden_layers": num_hidden_layers,
            "downstream_transformer_layers": num_hidden_layers - layer_index - 1,
        }
        source_packet_sha = base.canonical_sha(source_packet)
        adapter = {
            "schema": "JSPACE_LATENT_BASIS_ADAPTER/v1",
            "model": base.MODEL_ID,
            "revision": base.MODEL_REVISION,
            "activation_site": activation_site,
            "hidden_size": int(probe_vector.numel()),
            "construction": "input_embedding(A)-mean(input_embedding(B),input_embedding(C)) normalized",
            "basis_independence_guard": "tie_word_embeddings=false required",
            "downstream_transformer_layers": num_hidden_layers - layer_index - 1,
        }
        adapter_sha = base.canonical_sha(adapter)
        local_vector_sha = base.tensor_sha(probe_vector)

        state = InternalLayerRuntimeState(
            torch,
            tokenizer,
            model,
            device,
            probe_vector,
            token_ids,
            layer_index,
            num_hidden_layers,
            activation_site,
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), base.make_handler(state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/jspace/logits"

        calibration_rows: list[dict[str, Any]] = []
        for gain in base.CALIBRATION_GAINS:
            for seed, prompt in base.CALIBRATION:
                for control in ("BASELINE", "+VECTOR", "SIGN_FLIP"):
                    row = base.post_json(endpoint, {"prompt": prompt, "control": control, "gain": gain, "seed": seed})
                    row["prompt_family"] = f"cal-{seed}"
                    calibration_rows.append(row)
        selected_gain = base.select_gain(calibration_rows)

        holdout_rows: list[dict[str, Any]] = []
        if selected_gain is not None:
            for seed, prompt in base.HOLDOUT:
                family = f"hold-{seed}"
                for control in base.CONTROLS:
                    row = base.post_json(endpoint, {"prompt": prompt, "control": control, "gain": selected_gain, "seed": seed})
                    row["prompt_family"] = family
                    holdout_rows.append(row)
        verdict = base.adjudicate(holdout_rows, selected_gain)

        controls: dict[str, Any] = {}
        for control in base.CONTROLS:
            receipts = [r["runtime_receipt_sha256"] for r in holdout_rows if r["control"] == control]
            controls[control] = {
                "runtime_receipt_sha256": base.canonical_sha(receipts),
                "observations": len(receipts),
            }

        applied_plus_rows = [r for r in holdout_rows if r["control"] == "+VECTOR"]
        applied_vector_sha = (
            applied_plus_rows[0]["applied_vector_sha256"]
            if applied_plus_rows
            else base.tensor_sha(probe_vector * float(selected_gain or 0.0))
        )
        intervention_receipt_sha = base.canonical_sha([r["runtime_receipt_sha256"] for r in applied_plus_rows])
        analysis_receipt_sha = base.canonical_sha({
            "verdict": verdict,
            "holdout_receipts": [r["runtime_receipt_sha256"] for r in holdout_rows],
        })
        local_runtime_receipt = base.canonical_sha({
            "endpoint": endpoint,
            "runtime_build_sha256": runtime_build_sha,
            "checkpoint_sha256": checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "source": source,
            "activation_site": activation_site,
            "vector_basis_class": VECTOR_BASIS_CLASS,
            "api_invocations": state.invocations,
        })

        candidate = {
            "schema": CANDIDATE_SCHEMA,
            "runtime_intervention_class": "LOCAL_PYTORCH_ACTIVATION_INTERVENTION",
            "source_identity": {
                "repo_head": source["repo_head"],
                "runtime_build_sha256": runtime_build_sha,
                "checkpoint_sha256": checkpoint_sha,
                "tokenizer_sha256": tokenizer_sha,
            },
            "intervention": {
                "runtime_observed": bool(applied_plus_rows and all(r["hook_calls"] > 0 for r in applied_plus_rows)),
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
                "terminal_output_projection_shortcut": False,
                "downstream_transformer_layers": num_hidden_layers - layer_index - 1,
                "vector_basis_class": VECTOR_BASIS_CLASS,
            },
            "controls": controls,
            "calibration": {
                "family_id": base.canonical_sha([p for _, p in base.CALIBRATION]),
                "seeds": [s for s, _ in base.CALIBRATION],
                "selected_gain": selected_gain,
                "fixed_layer_index": layer_index,
            },
            "holdout": {
                "family_id": base.canonical_sha([p for _, p in base.HOLDOUT]),
                "seeds": [s for s, _ in base.HOLDOUT],
                "reproducible_directional_effect": bool(verdict.get("pass")),
                "strongest_counterexample_recorded": True,
                "analysis_receipt_sha256": analysis_receipt_sha,
            },
            "basis_independence": {
                "probe_basis": VECTOR_BASIS_CLASS,
                "scored_basis": "LM_HEAD_A_VS_BC",
                "tie_word_embeddings_required_false": True,
                "algebraically_identical_to_scored_output_head_contrast": False,
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
            "snapshot_path": str(snapshot),
            "checkpoint_weight_manifest": weight_manifest,
            "checkpoint_sha256": checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "token_ids": token_ids,
            "token_labels": token_labels,
            "device": str(device),
            "runtime_manifest": runtime,
            "runtime_build_sha256": runtime_build_sha,
            "source_packet": source_packet,
            "source_packet_sha256": source_packet_sha,
            "adapter": adapter,
            "adapter_sha256": adapter_sha,
            "local_vector_sha256": local_vector_sha,
            "activation_site": activation_site,
            "layer_index": layer_index,
            "num_hidden_layers": num_hidden_layers,
            "downstream_transformer_layers": num_hidden_layers - layer_index - 1,
            "terminal_output_projection_shortcut": False,
            "vector_basis_class": VECTOR_BASIS_CLASS,
            "api_endpoint": endpoint,
            "api_loopback_only": True,
            "zero_provider_billing": True,
            "external_provider_credentials_read": False,
            "calibration_rows": calibration_rows,
            "selected_gain": selected_gain,
            "holdout_rows": holdout_rows,
            "verdict": verdict,
            "promotion_candidate_written": bool(verdict.get("pass")),
            "scientific_scope": (
                "NONTERMINAL_INTERNAL_LAYER_CAUSAL_STEERING_DISCRIMINATOR; a positive effect must survive "
                "downstream transformer computation and is not algebraically forced by the scored lm_head contrast"
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
            "status": "BLOCKED_LOCAL_FASTPATH",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "reason": f"{type(exc).__name__}:{str(exc)[:1000]}",
            "external_provider_credentials_read": False,
            "zero_provider_billing": True,
            "next_action": "REPAIR_NOW_OR_ROUTE_AROUND_WITHOUT_WAITING_FOR_EXTERNAL_PROVIDER",
        }
        blocked["result_sha256"] = base.canonical_sha(blocked)
        result_path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
