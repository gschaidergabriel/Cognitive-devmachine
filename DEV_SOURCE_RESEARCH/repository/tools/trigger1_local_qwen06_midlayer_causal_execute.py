#!/usr/bin/env python3
"""Trigger-1 V3: local zero-cost Qwen3-0.6B mid-layer causal vector experiment.

This successor deliberately avoids the terminal output-projection shortcut. It builds
an activation-only contrastive steering basis from calibration prompts at an internal
transformer block, injects that vector at the same non-terminal residual site, leaves
substantive downstream transformer computation intact, and evaluates six matched
controls on disjoint gain-calibration and holdout families through a loopback-only API.

No external LLM credential is read or required.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.request
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "Qwen/Qwen3-0.6B"
MODEL_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
TOKENIZER_JSON_SHA256 = "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4"
SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_MIDLAYER_CAUSAL_EXPERIMENT/v1"
CANDIDATE_SCHEMA = "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1"
CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)
GAIN_GRID = (0.25, 1.0, 4.0, 16.0, 64.0)

BASIS_PROMPTS = (
    (1101, "A", "/no_think\nBasis B1. The designated option is A. Internalize that relation. Answer:"),
    (1102, "B", "/no_think\nBasis B2. The designated option is B. Internalize that relation. Answer:"),
    (1103, "C", "/no_think\nBasis B3. The designated option is C. Internalize that relation. Answer:"),
    (1111, "A", "/no_think\nBasis B4. Target category: A. Prepare the selected category. Answer:"),
    (1112, "B", "/no_think\nBasis B5. Target category: B. Prepare the selected category. Answer:"),
    (1113, "C", "/no_think\nBasis B6. Target category: C. Prepare the selected category. Answer:"),
)
GAIN_CALIBRATION = (
    (1701, "/no_think\nGain calibration C1. Reply using only one token from A B C."),
    (1702, "/no_think\nGain calibration C2. Choose exactly one uppercase option: A, B, or C."),
    (1703, "/no_think\nGain calibration C3. Return exactly one of A B C and nothing else."),
)
HOLDOUT = (
    (2718, "/no_think\nHoldout H1. Reply using only one of these tokens: A B C."),
    (3141, "/no_think\nHoldout H2. Select one uppercase option from A, B, C and output only it."),
    (5772, "/no_think\nHoldout H3. Output exactly one capital letter among A B C."),
)


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_text(*args: str) -> str:
    try:
        p = subprocess.run(
            ["git", "-C", str(ROOT), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        return p.stdout.strip() or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def tensor_sha(tensor: Any) -> str:
    raw = tensor.detach().float().cpu().numpy().tobytes()
    return hashlib.sha256(raw).hexdigest()


def module_file_sha(module: Any) -> str | None:
    path = getattr(module, "__file__", None)
    if not path:
        return None
    p = Path(path)
    return sha256_file(p) if p.is_file() else None


def runtime_manifest(torch: Any, transformers: Any, model: Any) -> dict[str, Any]:
    exe = Path(sys.executable)
    model_module = sys.modules.get(model.__class__.__module__)
    return {
        "python_version": sys.version,
        "python_executable": str(exe),
        "python_executable_sha256": sha256_file(exe) if exe.is_file() else None,
        "platform": platform.platform(),
        "torch_version": getattr(torch, "__version__", None),
        "torch_module_sha256": module_file_sha(torch),
        "transformers_version": getattr(transformers, "__version__", None),
        "transformers_module_sha256": module_file_sha(transformers),
        "model_class": model.__class__.__name__,
        "model_module": model.__class__.__module__,
        "model_module_sha256": module_file_sha(model_module) if model_module else None,
    }


def load_exact_runtime(cache_dir: Path):
    import torch
    import transformers
    from huggingface_hub import snapshot_download
    from transformers import AutoModelForCausalLM, AutoTokenizer

    snapshot = Path(
        snapshot_download(
            repo_id=MODEL_ID,
            revision=MODEL_REVISION,
            cache_dir=str(cache_dir),
            allow_patterns=[
                "config.json",
                "generation_config.json",
                "tokenizer.json",
                "tokenizer_config.json",
                "special_tokens_map.json",
                "*.safetensors",
            ],
        )
    )
    tokenizer_json = snapshot / "tokenizer.json"
    if not tokenizer_json.is_file():
        raise RuntimeError("TOKENIZER_JSON_MISSING")
    got_tok = sha256_file(tokenizer_json)
    if got_tok != TOKENIZER_JSON_SHA256:
        raise RuntimeError(f"TOKENIZER_SHA256_MISMATCH:{got_tok}")

    weights = sorted(snapshot.glob("*.safetensors"))
    if not weights:
        raise RuntimeError("MODEL_SAFETENSORS_MISSING")
    weight_manifest = [{"name": p.name, "size": p.stat().st_size, "sha256": sha256_file(p)} for p in weights]
    checkpoint_sha = canonical_sha(weight_manifest)

    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(snapshot), local_files_only=True, torch_dtype=torch.float32, low_cpu_mem_usage=False
    )
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    layers = getattr(getattr(model, "model", None), "layers", None)
    if layers is None or len(layers) < 4:
        raise RuntimeError("QWEN_INTERNAL_LAYER_HOOK_SURFACE_UNAVAILABLE")
    layer_index = len(layers) // 2
    if layer_index >= len(layers) - 1:
        raise RuntimeError("NONTERMINAL_LAYER_SELECTION_FAILED")
    return (
        torch,
        transformers,
        snapshot,
        tokenizer,
        model,
        device,
        checkpoint_sha,
        got_tok,
        weight_manifest,
        layer_index,
    )


def resolve_token_triplet(tokenizer: Any) -> tuple[dict[str, int], dict[str, str]]:
    candidate_sets = (("A", "B", "C"), (" A", " B", " C"), ("1", "2", "3"))
    for values in candidate_sets:
        ids: list[int] = []
        for text in values:
            encoded = tokenizer.encode(text, add_special_tokens=False)
            if len(encoded) != 1:
                break
            ids.append(int(encoded[0]))
        if len(ids) == 3 and len(set(ids)) == 3:
            return {"A": ids[0], "B": ids[1], "C": ids[2]}, {"A": values[0], "B": values[1], "C": values[2]}
    raise RuntimeError("NO_DISTINCT_SINGLE_TOKEN_ABC_TRIPLET")


def unpack_hidden(output: Any):
    return output[0] if isinstance(output, tuple) else output


def replace_hidden(output: Any, hidden: Any):
    if isinstance(output, tuple):
        return (hidden, *output[1:])
    return hidden


def extract_internal_activation(torch: Any, tokenizer: Any, model: Any, device: Any, layer: Any, prompt: str):
    captured: list[Any] = []

    def hook(_module: Any, _inputs: Any, output: Any):
        hidden = unpack_hidden(output)
        captured.append(hidden[:, -1, :].detach().float().cpu())
        return output

    handle = layer.register_forward_hook(hook)
    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            model(**inputs)
    finally:
        handle.remove()
    if len(captured) != 1:
        raise RuntimeError(f"BASIS_CAPTURE_COUNT_INVALID:{len(captured)}")
    return captured[0][0]


def activation_only_basis(torch: Any, tokenizer: Any, model: Any, device: Any, layer: Any):
    rows: dict[str, list[Any]] = {"A": [], "B": [], "C": []}
    receipts: list[dict[str, Any]] = []
    for seed, label, prompt in BASIS_PROMPTS:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        act = extract_internal_activation(torch, tokenizer, model, device, layer, prompt)
        rows[label].append(act)
        receipts.append({
            "seed": seed,
            "label": label,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "activation_sha256": tensor_sha(act),
        })
    means = {label: torch.stack(vals, dim=0).mean(dim=0) for label, vals in rows.items()}
    raw = means["A"] - 0.5 * (means["B"] + means["C"])
    norm = torch.linalg.vector_norm(raw)
    if not bool(torch.isfinite(norm)) or float(norm) <= 1e-12:
        raise RuntimeError("INTERNAL_CONTRASTIVE_BASIS_DEGENERATE")
    unit = raw / norm
    return unit.to(device), receipts


def matched_family(torch: Any, base: Any, gain: float) -> dict[str, Any]:
    plus = base * float(gain)
    sign = -plus
    null = torch.zeros_like(plus)
    n = plus.numel()
    idx = torch.arange(n, dtype=torch.float32, device=plus.device)
    seed_vec = torch.sin(idx * 0.017 + 0.37) + torch.cos(idx * 0.031 + 0.11)
    denom = torch.dot(plus, plus)
    if float(denom) <= 1e-20:
        raise RuntimeError("CONTROL_VECTOR_ZERO_NORM")
    projection = torch.dot(seed_vec, plus) / denom
    orth = seed_vec - projection * plus
    orth_norm = torch.linalg.vector_norm(orth)
    if float(orth_norm) <= 1e-12:
        raise RuntimeError("ORTHOGONAL_CONTROL_DEGENERATE")
    orth = orth * (torch.linalg.vector_norm(plus) / orth_norm)
    perm = torch.roll(plus, shifts=17)
    if bool(torch.allclose(perm, plus)):
        perm = torch.roll(plus, shifts=1)
    perm = perm * (torch.linalg.vector_norm(plus) / torch.linalg.vector_norm(perm))
    return {
        "BASELINE": torch.zeros_like(plus),
        "+VECTOR": plus,
        "SIGN_FLIP": sign,
        "NULL_VECTOR": null,
        "ORTHOGONAL_SAME_NORM": orth,
        "PERMUTED_SAME_NORM": perm,
    }


class RuntimeState:
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
        self.layer_index = layer_index
        self.base_vector = base_vector
        self.token_ids = token_ids
        self.lock = threading.Lock()
        self.invocations = 0

    def infer(self, payload: dict[str, Any]) -> dict[str, Any]:
        prompt = str(payload.get("prompt") or "")
        control = str(payload.get("control") or "")
        gain = float(payload.get("gain") or 0.0)
        seed = int(payload.get("seed"))
        if control not in CONTROLS:
            raise ValueError("UNKNOWN_CONTROL")
        family = matched_family(self.torch, self.base_vector, gain)
        vector = family[control].to(self.device)
        applied_sha = tensor_sha(vector)
        hook_calls = 0
        applied_l2 = float(self.torch.linalg.vector_norm(vector).detach().cpu())

        def hook(_module: Any, _inputs: Any, output: Any):
            nonlocal hook_calls
            hook_calls += 1
            if control == "BASELINE":
                return output
            hidden = unpack_hidden(output).clone()
            hidden[:, -1, :] = hidden[:, -1, :] + vector.to(dtype=hidden.dtype)
            return replace_hidden(output, hidden)

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

        trio = {label: float(logits[token_id]) for label, token_id in self.token_ids.items()}
        score = trio["A"] - 0.5 * (trio["B"] + trio["C"])
        best = max(trio, key=trio.get)
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
            "token_logits": trio,
            "target_score": score,
            "best_label": best,
        }
        return {
            **material,
            "runtime_receipt_sha256": canonical_sha(material),
            "runtime_observed_intervention": bool(hook_calls > 0 and control != "BASELINE"),
        }


def make_handler(state: RuntimeState):
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
    with urllib.request.urlopen(req, timeout=180) as resp:
        obj = json.loads(resp.read().decode("utf-8"))
    if not isinstance(obj, dict) or obj.get("error"):
        raise RuntimeError(f"LOCAL_API_ERROR:{obj}")
    return obj


def select_gain(rows: list[dict[str, Any]]) -> float | None:
    ranked: list[tuple[float, float]] = []
    for gain in GAIN_GRID:
        by_seed: dict[int, dict[str, float]] = {}
        for r in rows:
            if r["gain"] == gain:
                by_seed.setdefault(int(r["seed"]), {})[r["control"]] = float(r["target_score"])
        margins: list[float] = []
        for vals in by_seed.values():
            if all(k in vals for k in ("BASELINE", "+VECTOR", "SIGN_FLIP")):
                margins.append(min(vals["+VECTOR"] - vals["BASELINE"], vals["BASELINE"] - vals["SIGN_FLIP"]))
        if margins:
            ranked.append((min(margins), gain))
    ranked.sort(reverse=True)
    return ranked[0][1] if ranked and ranked[0][0] > 0 else None


def adjudicate(holdout_rows: list[dict[str, Any]], selected_gain: float | None) -> dict[str, Any]:
    if selected_gain is None:
        return {"pass": False, "classification": "NO_DIRECTIONAL_GAIN_CALIBRATION"}
    grouped = {name: [] for name in CONTROLS}
    by_case: dict[tuple[int, str], dict[str, float]] = {}
    for row in holdout_rows:
        grouped[row["control"]].append(float(row["target_score"]))
        key = (int(row["seed"]), str(row["prompt_family"]))
        by_case.setdefault(key, {})[row["control"]] = float(row["target_score"])

    means = {name: sum(vals) / len(vals) if vals else float("nan") for name, vals in grouped.items()}
    paired_plus: list[float] = []
    paired_sign: list[float] = []
    paired_null: list[float] = []
    plus_vs_orth: list[float] = []
    plus_vs_perm: list[float] = []
    for vals in by_case.values():
        if all(k in vals for k in CONTROLS):
            paired_plus.append(vals["+VECTOR"] - vals["BASELINE"])
            paired_sign.append(vals["BASELINE"] - vals["SIGN_FLIP"])
            paired_null.append(abs(vals["NULL_VECTOR"] - vals["BASELINE"]))
            plus_vs_orth.append(vals["+VECTOR"] - vals["ORTHOGONAL_SAME_NORM"])
            plus_vs_perm.append(vals["+VECTOR"] - vals["PERMUTED_SAME_NORM"])
    passed = bool(
        paired_plus
        and min(paired_plus) > 0
        and min(paired_sign) > 0
        and max(paired_null) <= 1e-5
        and min(plus_vs_orth) > 0
        and min(plus_vs_perm) > 0
        and all(r.get("hook_calls", 0) > 0 for r in holdout_rows if r["control"] != "BASELINE")
    )
    return {
        "pass": passed,
        "classification": "NONTERMINAL_INTERNAL_VECTOR_EFFECT_REPRODUCED" if passed else "CONTROL_FAMILY_DID_NOT_ESTABLISH_SPECIFIC_INTERNAL_DIRECTIONAL_EFFECT",
        "selected_gain": selected_gain,
        "mean_scores": means,
        "min_paired_plus_vs_baseline": min(paired_plus) if paired_plus else None,
        "min_paired_baseline_vs_sign_flip": min(paired_sign) if paired_sign else None,
        "max_null_drift": max(paired_null) if paired_null else None,
        "min_plus_vs_orthogonal_same_norm": min(plus_vs_orth) if plus_vs_orth else None,
        "min_plus_vs_permuted_same_norm": min(plus_vs_perm) if plus_vs_perm else None,
        "strongest_counterexample_plus_delta": min(paired_plus) if paired_plus else None,
    }


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
        "repo_head": git_text("rev-parse", "HEAD"),
        "repo_tree": git_text("rev-parse", "HEAD^{tree}"),
        "repo_dirty_porcelain_sha256": canonical_sha(git_text("status", "--porcelain=v1")),
        "executor_sha256": sha256_file(Path(__file__)),
    }

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
        ) = load_exact_runtime(Path(args.cache_dir))
        token_ids, token_labels = resolve_token_triplet(tokenizer)
        layers = model.model.layers
        layer = layers[layer_index]
        base_vector, basis_receipts = activation_only_basis(torch, tokenizer, model, device, layer)
        runtime = runtime_manifest(torch, transformers, model)
        runtime_build_sha = canonical_sha(runtime)
        num_layers = len(layers)
        downstream_layers = num_layers - layer_index - 1
        if downstream_layers < 1:
            raise RuntimeError("NO_DOWNSTREAM_TRANSFORMER_COMPUTATION")

        activation_site = f"model.model.layers[{layer_index}]:output:last_token"
        source_packet = {
            "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "intent": "causally shift internal representation toward calibration-derived A relation before downstream transformer computation",
            "basis": "contrastive internal activation basis; no lm_head/output-projection weight rows used in vector construction",
            "basis_family_sha256": canonical_sha(basis_receipts),
            "token_labels": token_labels,
            "token_ids": token_ids,
            "model": MODEL_ID,
            "revision": MODEL_REVISION,
            "activation_site": activation_site,
        }
        source_packet_sha = canonical_sha(source_packet)
        adapter = {
            "schema": "JSPACE_LATENT_BASIS_ADAPTER/v1",
            "model": MODEL_ID,
            "revision": MODEL_REVISION,
            "activation_site": activation_site,
            "hidden_size": int(base_vector.numel()),
            "construction": "mean internal activation(A)-0.5*(mean internal activation(B)+mean internal activation(C)), normalized",
            "basis_constructed_without_output_head": True,
            "downstream_transformer_layers": downstream_layers,
            "terminal_output_projection_shortcut": False,
        }
        adapter_sha = canonical_sha(adapter)
        local_vector_sha = tensor_sha(base_vector)

        state = RuntimeState(torch, tokenizer, model, device, layer, layer_index, base_vector, token_ids)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/jspace/logits"

        calibration_rows: list[dict[str, Any]] = []
        for gain in GAIN_GRID:
            for seed, prompt in GAIN_CALIBRATION:
                for control in ("BASELINE", "+VECTOR", "SIGN_FLIP"):
                    row = post_json(endpoint, {"prompt": prompt, "control": control, "gain": gain, "seed": seed})
                    row["prompt_family"] = f"gain-cal-{seed}"
                    calibration_rows.append(row)
        selected_gain = select_gain(calibration_rows)

        holdout_rows: list[dict[str, Any]] = []
        if selected_gain is not None:
            for seed, prompt in HOLDOUT:
                family = f"hold-{seed}"
                for control in CONTROLS:
                    row = post_json(endpoint, {"prompt": prompt, "control": control, "gain": selected_gain, "seed": seed})
                    row["prompt_family"] = family
                    holdout_rows.append(row)
        verdict = adjudicate(holdout_rows, selected_gain)

        server.shutdown()
        server.server_close()

        controls: dict[str, Any] = {}
        for control in CONTROLS:
            receipts = [r["runtime_receipt_sha256"] for r in holdout_rows if r["control"] == control]
            controls[control] = {"runtime_receipt_sha256": canonical_sha(receipts), "observations": len(receipts)}

        plus_rows = [r for r in holdout_rows if r["control"] == "+VECTOR"]
        applied_vector_sha = plus_rows[0]["applied_vector_sha256"] if plus_rows else tensor_sha(base_vector * float(selected_gain or 0.0))
        intervention_receipt_sha = canonical_sha([r["runtime_receipt_sha256"] for r in plus_rows])
        analysis_receipt_sha = canonical_sha({"verdict": verdict, "holdout_receipts": [r["runtime_receipt_sha256"] for r in holdout_rows]})
        local_runtime_receipt = canonical_sha({
            "endpoint": endpoint,
            "runtime_build_sha256": runtime_build_sha,
            "checkpoint_sha256": checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "source": source,
            "activation_site": activation_site,
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
                "runtime_observed": bool(plus_rows and all(r["hook_calls"] > 0 for r in plus_rows)),
                "invocation_id": canonical_sha([r["runtime_receipt_sha256"] for r in holdout_rows]),
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
                "family_id": canonical_sha([p for _, p in GAIN_CALIBRATION]),
                "basis_family_id": canonical_sha([p for _, _, p in BASIS_PROMPTS]),
                "seeds": [s for s, _ in GAIN_CALIBRATION],
                "basis_seeds": [s for s, _, _ in BASIS_PROMPTS],
                "selected_gain": selected_gain,
            },
            "holdout": {
                "family_id": canonical_sha([p for _, p in HOLDOUT]),
                "seeds": [s for s, _ in HOLDOUT],
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
                "model_or_route": f"{MODEL_ID}@{MODEL_REVISION}",
            },
        }

        result = {
            "schema": SCHEMA,
            "status": "PASS" if verdict.get("pass") else "SCIENTIFIC_NEGATIVE",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "model": MODEL_ID,
            "model_revision": MODEL_REVISION,
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
            "terminal_output_projection_shortcut": False,
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
            "evidence_boundary": "A PASS establishes a non-terminal model-specific internal intervention candidate with downstream computation and matched controls; it does not mint canonical EntityOS/HCU, full J-Space, or training credit.",
        }
        result["result_sha256"] = canonical_sha(result)
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
            "status": "BLOCKED_LOCAL_MIDLAYER_FASTPATH",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "reason": f"{type(exc).__name__}:{str(exc)[:1000]}",
            "external_provider_credentials_read": False,
            "zero_provider_billing": True,
            "terminal_output_projection_shortcut": False,
            "next_action": "REPAIR_OR_ROUTE_AROUND_CURRENT_LOCAL_MIDLAYER_BLOCKER",
        }
        blocked["result_sha256"] = canonical_sha(blocked)
        result_path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
