#!/usr/bin/env python3
"""Trigger-1 V2 local Qwen3-0.6B hidden-state causal steering experiment.

Scientific correction over the initial local fastpath:
- the intervention basis is NOT constructed from the LM-head weights used by the outcome;
- the basis is derived from a disjoint family of observed mid-layer activations;
- the vector is applied at the same mid-layer residual output with downstream transformer
  blocks still remaining;
- calibration and holdout remain disjoint and use the same six-control family;
- exact source/runtime/model/tokenizer/intervention identities remain receipt-bound.

The previous final-norm LM-head-contrast construction remains useful as a plumbing
positive control, but its directional logit effect is algebraically coupled to the
measurement and therefore is not sufficient for Trigger-1 owner-goal promotion.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.request
from typing import Any

import trigger1_local_qwen06_activation_api_execute as v1

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_ACTIVATION_API_EXPERIMENT/v2"
CANDIDATE_SCHEMA = v1.CANDIDATE_SCHEMA
BASIS_DERIVATION_CLASS = "DISJOINT_HIDDEN_ACTIVATION_CONTRAST"
BASIS_SOURCE = (
    (8111, "A", "/no_think\nBasis S1. The requested symbolic label is A. Output only A."),
    (8112, "A", "/no_think\nBasis S2. Select the symbolic answer A and output only that label."),
    (8221, "B", "/no_think\nBasis S3. The requested symbolic label is B. Output only B."),
    (8222, "B", "/no_think\nBasis S4. Select the symbolic answer B and output only that label."),
    (8331, "C", "/no_think\nBasis S5. The requested symbolic label is C. Output only C."),
    (8332, "C", "/no_think\nBasis S6. Select the symbolic answer C and output only that label."),
)


def _git_raw(*args: str) -> str:
    try:
        p = subprocess.run(
            ["git", "-C", str(ROOT), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        return p.stdout
    except Exception:
        return "UNKNOWN"


def source_identity() -> dict[str, Any]:
    status = _git_raw("status", "--porcelain=v1", "--untracked-files=no")
    dirty_unknown = status == "UNKNOWN"
    status_bytes = status.encode("utf-8")
    return {
        "repo_head": v1.git_text("rev-parse", "HEAD"),
        "repo_tree": v1.git_text("rev-parse", "HEAD^{tree}"),
        "repo_dirty": None if dirty_unknown else bool(status.strip()),
        "repo_dirty_state_sha256": hashlib.sha256(status_bytes).hexdigest(),
        "executor_sha256": v1.sha256_file(Path(__file__)),
        "v1_helper_sha256": v1.sha256_file(Path(v1.__file__)),
    }


def _hidden_from_output(output: Any):
    return output[0] if isinstance(output, tuple) else output


def choose_layer(model: Any) -> tuple[int, int]:
    layers = getattr(getattr(model, "model", None), "layers", None)
    if layers is None:
        raise RuntimeError("QWEN_DECODER_LAYER_SURFACE_UNAVAILABLE")
    total = len(layers)
    if total < 4:
        raise RuntimeError("INSUFFICIENT_DOWNSTREAM_TRANSFORM_DEPTH")
    layer_index = max(1, min(total - 2, total // 2))
    downstream_depth = total - layer_index - 1
    if downstream_depth < 1:
        raise RuntimeError("POST_INTERVENTION_TRANSFORM_DEPTH_ZERO")
    return layer_index, downstream_depth


def capture_last_token_hidden(
    torch: Any,
    tokenizer: Any,
    model: Any,
    device: Any,
    layer_index: int,
    prompt: str,
    seed: int,
):
    captures: list[Any] = []

    def hook(_module: Any, _inputs: Any, output: Any):
        hidden = _hidden_from_output(output)
        captures.append(hidden[:, -1, :].detach().float().cpu())
        return output

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    handle = model.model.layers[layer_index].register_forward_hook(hook)
    try:
        with torch.no_grad():
            model(**inputs)
    finally:
        handle.remove()
    if len(captures) != 1:
        raise RuntimeError(f"BASIS_CAPTURE_COUNT_INVALID:{len(captures)}")
    return captures[0][0]


def derive_hidden_basis(
    torch: Any,
    tokenizer: Any,
    model: Any,
    device: Any,
    layer_index: int,
) -> tuple[Any, list[dict[str, Any]]]:
    grouped: dict[str, list[Any]] = {"A": [], "B": [], "C": []}
    receipts: list[dict[str, Any]] = []
    for seed, label, prompt in BASIS_SOURCE:
        hidden = capture_last_token_hidden(torch, tokenizer, model, device, layer_index, prompt, seed)
        grouped[label].append(hidden)
        receipts.append(
            {
                "seed": seed,
                "label": label,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "hidden_sha256": v1.tensor_sha(hidden),
            }
        )

    means = {label: torch.stack(rows, dim=0).mean(dim=0) for label, rows in grouped.items()}
    vector = means["A"] - 0.5 * (means["B"] + means["C"])
    norm = torch.linalg.vector_norm(vector)
    if not bool(torch.isfinite(norm)) or float(norm) <= 1e-12:
        raise RuntimeError("DISJOINT_HIDDEN_BASIS_DEGENERATE")
    vector = (vector / norm).to(device)
    return vector, receipts


class LatentRuntimeState:
    def __init__(
        self,
        torch: Any,
        tokenizer: Any,
        model: Any,
        device: Any,
        base_vector: Any,
        token_ids: dict[str, int],
        layer_index: int,
    ):
        self.torch = torch
        self.tokenizer = tokenizer
        self.model = model
        self.device = device
        self.base_vector = base_vector
        self.token_ids = token_ids
        self.layer_index = layer_index
        self.lock = threading.Lock()
        self.invocations = 0

    def infer(self, payload: dict[str, Any]) -> dict[str, Any]:
        prompt = str(payload.get("prompt") or "")
        control = str(payload.get("control") or "")
        gain = float(payload.get("gain") or 0.0)
        seed = int(payload.get("seed"))
        if control not in v1.CONTROLS:
            raise ValueError("UNKNOWN_CONTROL")
        family = v1.matched_family(self.torch, self.base_vector, gain)
        vector = family[control].to(self.device)
        applied_sha = v1.tensor_sha(vector)
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

        with self.lock:
            self.torch.manual_seed(seed)
            if self.torch.cuda.is_available():
                self.torch.cuda.manual_seed_all(seed)
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            handle = self.model.model.layers[self.layer_index].register_forward_hook(hook)
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
        material = {
            "invocation": self.invocations,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "control": control,
            "gain": gain,
            "seed": seed,
            "layer_index": self.layer_index,
            "applied_vector_sha256": applied_sha,
            "hook_calls": hook_calls,
            "token_logits": trio,
            "target_score": score,
            "best_label": best,
        }
        return {
            **material,
            "runtime_receipt_sha256": v1.canonical_sha(material),
            "runtime_observed_intervention": bool(hook_calls > 0 and control != "BASELINE"),
        }


def make_handler(state: LatentRuntimeState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def do_POST(self) -> None:
            if self.path != "/v1/jspace/logits":
                self.send_response(404)
                self.end_headers()
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                result = state.infer(payload)
                raw = json.dumps(result, sort_keys=True).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except Exception as exc:
                raw = json.dumps({"error": f"{type(exc).__name__}:{str(exc)[:500]}"}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

    return Handler


def post_json(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        obj = json.loads(resp.read().decode("utf-8"))
    if not isinstance(obj, dict) or obj.get("error"):
        raise RuntimeError(f"LOCAL_API_ERROR:{obj}")
    return obj


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
    source = source_identity()

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
        ) = v1.load_exact_runtime(Path(args.cache_dir))
        token_ids, token_labels = v1.resolve_token_triplet(tokenizer)
        layer_index, downstream_depth = choose_layer(model)
        base_vector, basis_receipts = derive_hidden_basis(torch, tokenizer, model, device, layer_index)
        runtime = v1.runtime_manifest(torch, transformers, model)
        runtime_build_sha = v1.canonical_sha(runtime)
        basis_family_id = v1.canonical_sha([p for _, _, p in BASIS_SOURCE])
        basis_seeds = [seed for seed, _, _ in BASIS_SOURCE]
        activation_site = f"model.model.layers[{layer_index}]:output:last_token"
        source_packet = {
            "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "intent": "increase latent preference for symbolic output label A relative to B and C",
            "basis": "disjoint observed Qwen3-0.6B mid-layer activation contrast",
            "basis_derivation_class": BASIS_DERIVATION_CLASS,
            "basis_source_family_id": basis_family_id,
            "basis_source_seeds": basis_seeds,
            "token_labels": token_labels,
            "token_ids": token_ids,
            "model": v1.MODEL_ID,
            "revision": v1.MODEL_REVISION,
            "activation_site": activation_site,
            "readout_target_weights_used": False,
        }
        source_packet_sha = v1.canonical_sha(source_packet)
        adapter = {
            "schema": "JSPACE_LATENT_BASIS_ADAPTER/v2",
            "model": v1.MODEL_ID,
            "revision": v1.MODEL_REVISION,
            "activation_site": activation_site,
            "hidden_size": int(base_vector.numel()),
            "construction": "mean(midlayer_hidden[A])-0.5*(mean(midlayer_hidden[B])+mean(midlayer_hidden[C])) normalized",
            "basis_source_family_id": basis_family_id,
            "post_intervention_transform_depth": downstream_depth,
            "readout_target_weights_used": False,
            "direct_readout_algebraically_forced": False,
        }
        adapter_sha = v1.canonical_sha(adapter)
        local_vector_sha = v1.tensor_sha(base_vector)

        state = LatentRuntimeState(torch, tokenizer, model, device, base_vector, token_ids, layer_index)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/jspace/logits"

        calibration_rows: list[dict[str, Any]] = []
        for gain in v1.CALIBRATION_GAINS:
            for seed, prompt in v1.CALIBRATION:
                for control in ("BASELINE", "+VECTOR", "SIGN_FLIP"):
                    row = post_json(endpoint, {"prompt": prompt, "control": control, "gain": gain, "seed": seed})
                    row["prompt_family"] = f"cal-{seed}"
                    calibration_rows.append(row)
        selected_gain = v1.select_gain(calibration_rows)

        holdout_rows: list[dict[str, Any]] = []
        if selected_gain is not None:
            for seed, prompt in v1.HOLDOUT:
                family = f"hold-{seed}"
                for control in v1.CONTROLS:
                    row = post_json(endpoint, {"prompt": prompt, "control": control, "gain": selected_gain, "seed": seed})
                    row["prompt_family"] = family
                    holdout_rows.append(row)
        verdict = v1.adjudicate(holdout_rows, selected_gain)

        server.shutdown()
        server.server_close()

        controls = {}
        for control in v1.CONTROLS:
            receipts = [r["runtime_receipt_sha256"] for r in holdout_rows if r["control"] == control]
            controls[control] = {
                "runtime_receipt_sha256": v1.canonical_sha(receipts),
                "observations": len(receipts),
            }

        applied_plus_rows = [r for r in holdout_rows if r["control"] == "+VECTOR"]
        applied_vector_sha = (
            applied_plus_rows[0]["applied_vector_sha256"]
            if applied_plus_rows
            else v1.tensor_sha(base_vector * float(selected_gain or 0.0))
        )
        intervention_receipt_sha = v1.canonical_sha([r["runtime_receipt_sha256"] for r in applied_plus_rows])
        analysis_receipt_sha = v1.canonical_sha(
            {"verdict": verdict, "holdout_receipts": [r["runtime_receipt_sha256"] for r in holdout_rows]}
        )
        local_runtime_receipt = v1.canonical_sha(
            {
                "endpoint": endpoint,
                "source_identity": source,
                "runtime_build_sha256": runtime_build_sha,
                "checkpoint_sha256": checkpoint_sha,
                "tokenizer_sha256": tokenizer_sha,
                "basis_family_id": basis_family_id,
                "basis_receipts": basis_receipts,
                "activation_site": activation_site,
                "api_invocations": state.invocations,
            }
        )

        candidate = {
            "schema": CANDIDATE_SCHEMA,
            "runtime_intervention_class": "LOCAL_PYTORCH_ACTIVATION_INTERVENTION",
            "source_identity": {
                **source,
                "runtime_build_sha256": runtime_build_sha,
                "checkpoint_sha256": checkpoint_sha,
                "tokenizer_sha256": tokenizer_sha,
            },
            "intervention": {
                "runtime_observed": bool(applied_plus_rows and all(r["hook_calls"] > 0 for r in applied_plus_rows)),
                "invocation_id": v1.canonical_sha([r["runtime_receipt_sha256"] for r in holdout_rows]),
                "activation_site": activation_site,
                "source_packet_sha256": source_packet_sha,
                "adapter_sha256": adapter_sha,
                "local_vector_sha256": local_vector_sha,
                "applied_vector_sha256": applied_vector_sha,
                "runtime_intervention_receipt_sha256": intervention_receipt_sha,
                "gain": selected_gain,
                "layer_start": layer_index,
                "layer_end": layer_index,
                "post_intervention_transform_depth": downstream_depth,
                "basis_derivation_class": BASIS_DERIVATION_CLASS,
                "basis_source_family_id": basis_family_id,
                "basis_source_seeds": basis_seeds,
                "readout_target_weights_used": False,
                "direct_readout_algebraically_forced": False,
            },
            "controls": controls,
            "calibration": {
                "family_id": v1.canonical_sha([p for _, p in v1.CALIBRATION]),
                "seeds": [s for s, _ in v1.CALIBRATION],
                "selected_gain": selected_gain,
            },
            "holdout": {
                "family_id": v1.canonical_sha([p for _, p in v1.HOLDOUT]),
                "seeds": [s for s, _ in v1.HOLDOUT],
                "reproducible_directional_effect": bool(verdict.get("pass")),
                "strongest_counterexample_recorded": True,
                "analysis_receipt_sha256": analysis_receipt_sha,
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
                "model_or_route": f"{v1.MODEL_ID}@{v1.MODEL_REVISION}",
            },
        }

        result = {
            "schema": SCHEMA,
            "status": "PASS" if verdict.get("pass") else "SCIENTIFIC_NEGATIVE",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "model": v1.MODEL_ID,
            "model_revision": v1.MODEL_REVISION,
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
            "basis_receipts": basis_receipts,
            "local_vector_sha256": local_vector_sha,
            "api_endpoint": endpoint,
            "api_loopback_only": True,
            "zero_provider_billing": True,
            "external_provider_credentials_read": False,
            "calibration_rows": calibration_rows,
            "selected_gain": selected_gain,
            "holdout_rows": holdout_rows,
            "verdict": verdict,
            "promotion_candidate_written": bool(verdict.get("pass")),
            "scientific_correction": "READOUT_COUPLING_REMOVED_BY_DISJOINT_MIDLAYER_BASIS_AND_DOWNSTREAM_TRANSFORM_DEPTH",
        }
        result["result_sha256"] = v1.canonical_sha(result)
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
            "next_action": "REPAIR_OR_ROUTE_AROUND_WITHOUT_WEAKENING_READOUT_INDEPENDENCE_GATE",
        }
        blocked["result_sha256"] = v1.canonical_sha(blocked)
        result_path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
