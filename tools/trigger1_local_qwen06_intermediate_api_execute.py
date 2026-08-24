#!/usr/bin/env python3
"""Trigger-1 V2 non-terminal Qwen3-0.6B contrastive activation steering experiment.

This is the successor discriminator to the terminal final-norm positive control. It
learns a unit steering direction from contrastive calibration hidden activations at
predeclared intermediate decoder layers, selects layer/gain on calibration only,
serves the intervention through a loopback-only API, and evaluates the frozen setup
on disjoint holdout with six matched controls.

No external LLM provider credential is read. The model/tokenizer revision is fixed.
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
from typing import Any
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "Qwen/Qwen3-0.6B"
MODEL_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
TOKENIZER_JSON_SHA256 = "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4"
SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_ACTIVATION_API_EXPERIMENT/v1"
CANDIDATE_SCHEMA = "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1"
CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)
# Predeclared before observing calibration outcomes. Qwen3-0.6B has 28 decoder layers.
CANDIDATE_LAYERS = (7, 14, 21)
CALIBRATION_GAINS = (1.0, 4.0, 16.0, 64.0)

# The direction is derived from semantic yes/no contrast anchors, not from lm_head rows.
POSITIVE_ANCHORS = (
    "/no_think\nThe proposition is correct. The appropriate response is yes.",
    "/no_think\nThis claim should be affirmed because it is true and valid.",
    "/no_think\nAccept the statement: the answer is yes.",
)
NEGATIVE_ANCHORS = (
    "/no_think\nThe proposition is incorrect. The appropriate response is no.",
    "/no_think\nThis claim should be rejected because it is false and invalid.",
    "/no_think\nReject the statement: the answer is no.",
)

# Calibration selects layer/gain only. Holdout strings and seeds are never used for selection.
CALIBRATION = (
    (1701, "/no_think\nAnswer only yes or no. Is water made of hydrogen and oxygen?"),
    (1702, "/no_think\nAnswer only yes or no. Is Paris located in France?"),
)
HOLDOUT = (
    (2718, "/no_think\nAnswer only yes or no. Does two plus two equal four?"),
    (3141, "/no_think\nAnswer only yes or no. Is Earth a planet in the Solar System?"),
    (5772, "/no_think\nAnswer only yes or no. Can a triangle have three sides?"),
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
    weight_manifest = [
        {"name": p.name, "size": p.stat().st_size, "sha256": sha256_file(p)}
        for p in weights
    ]
    checkpoint_sha = canonical_sha(weight_manifest)

    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(snapshot),
        local_files_only=True,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=False,
    )
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    if not hasattr(model, "model") or not hasattr(model.model, "layers"):
        raise RuntimeError("QWEN_DECODER_LAYER_HOOK_SURFACE_UNAVAILABLE")
    if max(CANDIDATE_LAYERS) >= len(model.model.layers):
        raise RuntimeError(f"CANDIDATE_LAYER_OUT_OF_RANGE:{len(model.model.layers)}")
    return torch, transformers, snapshot, tokenizer, model, device, checkpoint_sha, got_tok, weight_manifest


def resolve_yes_no_tokens(tokenizer: Any) -> tuple[dict[str, int], dict[str, str]]:
    candidate_sets = (
        (" yes", " no"),
        (" Yes", " No"),
        ("YES", "NO"),
        ("yes", "no"),
        (" true", " false"),
    )
    for yes, no in candidate_sets:
        y = tokenizer.encode(yes, add_special_tokens=False)
        n = tokenizer.encode(no, add_special_tokens=False)
        if len(y) == 1 and len(n) == 1 and y[0] != n[0]:
            return {"YES": int(y[0]), "NO": int(n[0])}, {"YES": yes, "NO": no}
    raise RuntimeError("NO_DISTINCT_SINGLE_TOKEN_YES_NO_PAIR")


def final_hidden_at_layer(torch: Any, tokenizer: Any, model: Any, device: Any, prompt: str, layer: int):
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        output = model(**inputs, output_hidden_states=True, use_cache=False)
    hidden_states = output.hidden_states
    if hidden_states is None or len(hidden_states) <= layer + 1:
        raise RuntimeError("HIDDEN_STATES_UNAVAILABLE")
    return hidden_states[layer + 1][0, -1].detach().float()


def contrastive_vectors(torch: Any, tokenizer: Any, model: Any, device: Any) -> dict[int, Any]:
    vectors: dict[int, Any] = {}
    for layer in CANDIDATE_LAYERS:
        pos = [final_hidden_at_layer(torch, tokenizer, model, device, p, layer) for p in POSITIVE_ANCHORS]
        neg = [final_hidden_at_layer(torch, tokenizer, model, device, p, layer) for p in NEGATIVE_ANCHORS]
        pmean = torch.stack(pos).mean(dim=0)
        nmean = torch.stack(neg).mean(dim=0)
        v = pmean - nmean
        norm = torch.linalg.vector_norm(v)
        if not bool(torch.isfinite(norm)) or float(norm) <= 1e-12:
            raise RuntimeError(f"CONTRASTIVE_VECTOR_DEGENERATE:{layer}")
        vectors[layer] = (v / norm).detach()
    return vectors


def matched_family(torch: Any, base: Any, gain: float) -> dict[str, Any]:
    plus = base * float(gain)
    sign = -plus
    null = torch.zeros_like(plus)
    n = plus.numel()
    idx = torch.arange(n, dtype=torch.float32, device=plus.device)
    seed_vec = torch.sin(idx * 0.017 + 0.37) + torch.cos(idx * 0.031 + 0.11)
    denom = torch.dot(plus, plus)
    if float(denom) <= 1e-12:
        raise RuntimeError("CONTROL_VECTOR_ZERO")
    projection = torch.dot(seed_vec, plus) / denom
    orth = seed_vec - projection * plus
    orth_norm = torch.linalg.vector_norm(orth)
    if float(orth_norm) <= 1e-12:
        raise RuntimeError("ORTHOGONAL_CONTROL_DEGENERATE")
    orth = orth * (torch.linalg.vector_norm(plus) / orth_norm)
    perm = torch.roll(plus, shifts=17)
    if bool(torch.allclose(perm, plus)):
        perm = torch.roll(plus, shifts=1)
    perm_norm = torch.linalg.vector_norm(perm)
    if float(perm_norm) <= 1e-12:
        raise RuntimeError("PERMUTED_CONTROL_DEGENERATE")
    perm = perm * (torch.linalg.vector_norm(plus) / perm_norm)
    return {
        "BASELINE": torch.zeros_like(plus),
        "+VECTOR": plus,
        "SIGN_FLIP": sign,
        "NULL_VECTOR": null,
        "ORTHOGONAL_SAME_NORM": orth,
        "PERMUTED_SAME_NORM": perm,
    }


class RuntimeState:
    def __init__(self, torch: Any, tokenizer: Any, model: Any, device: Any, vectors: dict[int, Any], token_ids: dict[str, int]):
        self.torch = torch
        self.tokenizer = tokenizer
        self.model = model
        self.device = device
        self.vectors = vectors
        self.token_ids = token_ids
        self.lock = threading.Lock()
        self.invocations = 0

    def infer(self, payload: dict[str, Any]) -> dict[str, Any]:
        prompt = str(payload.get("prompt") or "")
        control = str(payload.get("control") or "")
        gain = float(payload.get("gain") or 0.0)
        seed = int(payload.get("seed"))
        layer = int(payload.get("layer"))
        if control not in CONTROLS:
            raise ValueError("UNKNOWN_CONTROL")
        if layer not in self.vectors:
            raise ValueError("UNKNOWN_LAYER")
        family = matched_family(self.torch, self.vectors[layer], gain)
        vector = family[control].to(self.device)
        applied_sha = tensor_sha(vector)
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
            handle = self.model.model.layers[layer].register_forward_hook(hook)
            try:
                with self.torch.no_grad():
                    output = self.model(**inputs, use_cache=False)
                    logits = output.logits[0, -1].float().detach().cpu()
            finally:
                handle.remove()
            self.invocations += 1

        yes = float(logits[self.token_ids["YES"]])
        no = float(logits[self.token_ids["NO"]])
        score = yes - no
        receipt_material = {
            "invocation": self.invocations,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "control": control,
            "gain": gain,
            "layer": layer,
            "seed": seed,
            "applied_vector_sha256": applied_sha,
            "hook_calls": hook_calls,
            "token_logits": {"YES": yes, "NO": no},
            "target_score": score,
            "best_label": "YES" if yes >= no else "NO",
        }
        return {
            **receipt_material,
            "runtime_receipt_sha256": canonical_sha(receipt_material),
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


def select_config(rows: list[dict[str, Any]]) -> tuple[int, float] | None:
    ranked: list[tuple[float, int, float]] = []
    for layer in CANDIDATE_LAYERS:
        for gain in CALIBRATION_GAINS:
            plus = [r["target_score"] for r in rows if r["layer"] == layer and r["gain"] == gain and r["control"] == "+VECTOR"]
            sign = [r["target_score"] for r in rows if r["layer"] == layer and r["gain"] == gain and r["control"] == "SIGN_FLIP"]
            base = [r["target_score"] for r in rows if r["layer"] == layer and r["gain"] == gain and r["control"] == "BASELINE"]
            if plus and sign and base and len(plus) == len(sign) == len(base):
                plus_delta = min(p - b for p, b in zip(plus, base))
                sign_delta = min(b - s for b, s in zip(base, sign))
                metric = min(plus_delta, sign_delta)
                ranked.append((metric, layer, gain))
    ranked.sort(reverse=True)
    if not ranked or ranked[0][0] <= 0:
        return None
    return ranked[0][1], ranked[0][2]


def adjudicate(holdout_rows: list[dict[str, Any]], selected: tuple[int, float] | None) -> dict[str, Any]:
    if selected is None:
        return {"pass": False, "classification": "NO_DIRECTIONAL_CALIBRATION_CONFIG"}
    layer, gain = selected
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
    for values in by_case.values():
        if all(k in values for k in ("BASELINE", "+VECTOR", "SIGN_FLIP", "NULL_VECTOR")):
            paired_plus.append(values["+VECTOR"] - values["BASELINE"])
            paired_sign.append(values["BASELINE"] - values["SIGN_FLIP"])
            paired_null.append(abs(values["NULL_VECTOR"] - values["BASELINE"]))
    nuisance = max(means["ORTHOGONAL_SAME_NORM"], means["PERMUTED_SAME_NORM"])
    passed = bool(
        paired_plus
        and min(paired_plus) > 0
        and min(paired_sign) > 0
        and max(paired_null) <= 1e-5
        and means["+VECTOR"] > nuisance
        and all(r.get("hook_calls", 0) > 0 for r in holdout_rows if r["control"] != "BASELINE")
    )
    return {
        "pass": passed,
        "classification": "DIRECT_INTERMEDIATE_HIDDEN_STATE_VECTOR_EFFECT_REPRODUCED" if passed else "INTERMEDIATE_CONTROL_FAMILY_DID_NOT_ESTABLISH_SPECIFIC_DIRECTIONAL_EFFECT",
        "selected_layer": layer,
        "selected_gain": gain,
        "mean_scores": means,
        "min_paired_plus_vs_baseline": min(paired_plus) if paired_plus else None,
        "min_paired_baseline_vs_sign_flip": min(paired_sign) if paired_sign else None,
        "max_null_drift": max(paired_null) if paired_null else None,
        "specificity_gap_vs_best_same_norm_control": means["+VECTOR"] - nuisance,
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
        "repo_dirty": git_text("status", "--porcelain=v1"),
    }

    server = None
    try:
        torch, transformers, snapshot, tokenizer, model, device, checkpoint_sha, tokenizer_sha, weight_manifest = load_exact_runtime(Path(args.cache_dir))
        token_ids, token_labels = resolve_yes_no_tokens(tokenizer)
        vectors = contrastive_vectors(torch, tokenizer, model, device)
        runtime = runtime_manifest(torch, transformers, model)
        runtime_build_sha = canonical_sha(runtime)
        vector_shas = {str(layer): tensor_sha(v) for layer, v in vectors.items()}

        source_packet = {
            "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "intent": "increase latent affirmative/YES preference relative to NO",
            "basis": "contrastive intermediate Qwen3-0.6B decoder hidden activations from calibration anchors; not lm_head/output-embedding rows",
            "basis_positive_family_sha256": canonical_sha(POSITIVE_ANCHORS),
            "basis_negative_family_sha256": canonical_sha(NEGATIVE_ANCHORS),
            "candidate_layers": list(CANDIDATE_LAYERS),
            "token_labels": token_labels,
            "token_ids": token_ids,
            "model": MODEL_ID,
            "revision": MODEL_REVISION,
        }
        source_packet_sha = canonical_sha(source_packet)
        adapter = {
            "schema": "JSPACE_LATENT_BASIS_ADAPTER/v1",
            "model": MODEL_ID,
            "revision": MODEL_REVISION,
            "activation_sites": [f"model.model.layers[{x}]:output:last_token" for x in CANDIDATE_LAYERS],
            "hidden_size": int(next(iter(vectors.values())).numel()),
            "construction": "mean(positive-anchor hidden)-mean(negative-anchor hidden), normalized per candidate layer",
            "terminal_output_projection_shortcut": False,
        }
        adapter_sha = canonical_sha(adapter)

        state = RuntimeState(torch, tokenizer, model, device, vectors, token_ids)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/jspace/logits"

        calibration_rows: list[dict[str, Any]] = []
        for layer in CANDIDATE_LAYERS:
            for gain in CALIBRATION_GAINS:
                for seed, prompt in CALIBRATION:
                    for control in ("BASELINE", "+VECTOR", "SIGN_FLIP"):
                        row = post_json(endpoint, {"prompt": prompt, "control": control, "gain": gain, "layer": layer, "seed": seed})
                        row["prompt_family"] = f"cal-{seed}"
                        calibration_rows.append(row)
        selected = select_config(calibration_rows)

        holdout_rows: list[dict[str, Any]] = []
        if selected is not None:
            selected_layer, selected_gain = selected
            for seed, prompt in HOLDOUT:
                family = f"hold-{seed}"
                for control in CONTROLS:
                    row = post_json(endpoint, {"prompt": prompt, "control": control, "gain": selected_gain, "layer": selected_layer, "seed": seed})
                    row["prompt_family"] = family
                    holdout_rows.append(row)
        verdict = adjudicate(holdout_rows, selected)

        server.shutdown()
        server.server_close()
        server = None

        controls = {}
        for control in CONTROLS:
            receipts = [r["runtime_receipt_sha256"] for r in holdout_rows if r["control"] == control]
            controls[control] = {
                "runtime_receipt_sha256": canonical_sha(receipts),
                "observations": len(receipts),
            }

        selected_layer = selected[0] if selected else None
        selected_gain = selected[1] if selected else None
        applied_plus_rows = [r for r in holdout_rows if r["control"] == "+VECTOR"]
        selected_base = vectors[selected_layer] if selected_layer is not None else next(iter(vectors.values()))
        local_vector_sha = tensor_sha(selected_base)
        applied_vector_sha = applied_plus_rows[0]["applied_vector_sha256"] if applied_plus_rows else tensor_sha(selected_base * float(selected_gain or 0.0))
        intervention_receipt_sha = canonical_sha([r["runtime_receipt_sha256"] for r in applied_plus_rows])
        analysis_receipt_sha = canonical_sha({"verdict": verdict, "holdout_receipts": [r["runtime_receipt_sha256"] for r in holdout_rows]})
        local_runtime_receipt = canonical_sha({
            "endpoint": endpoint,
            "runtime_build_sha256": runtime_build_sha,
            "checkpoint_sha256": checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "source": source,
            "api_invocations": state.invocations,
            "selected_layer": selected_layer,
            "selected_gain": selected_gain,
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
                "invocation_id": canonical_sha([r["runtime_receipt_sha256"] for r in holdout_rows]),
                "activation_site": f"model.model.layers[{selected_layer}]:output:last_token" if selected_layer is not None else "model.model.layers[UNSELECTED]:output:last_token",
                "terminal_output_projection_shortcut": False,
                "source_packet_sha256": source_packet_sha,
                "adapter_sha256": adapter_sha,
                "local_vector_sha256": local_vector_sha,
                "applied_vector_sha256": applied_vector_sha,
                "runtime_intervention_receipt_sha256": intervention_receipt_sha,
                "gain": selected_gain,
                "layer_start": selected_layer,
                "layer_end": selected_layer,
            },
            "controls": controls,
            "calibration": {
                "family_id": canonical_sha({"queries": [p for _, p in CALIBRATION], "positive_anchors": POSITIVE_ANCHORS, "negative_anchors": NEGATIVE_ANCHORS}),
                "seeds": [s for s, _ in CALIBRATION],
                "predeclared_layers": list(CANDIDATE_LAYERS),
                "predeclared_gains": list(CALIBRATION_GAINS),
                "selected_layer": selected_layer,
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
            "layer_vector_sha256": vector_shas,
            "selected_layer": selected_layer,
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
            "terminal_output_projection_shortcut": False,
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
        if server is not None:
            try:
                server.shutdown()
                server.server_close()
            except Exception:
                pass
        blocked = {
            "schema": SCHEMA,
            "status": "BLOCKED_LOCAL_FASTPATH",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "reason": f"{type(exc).__name__}:{str(exc)[:1000]}",
            "external_provider_credentials_read": False,
            "zero_provider_billing": True,
            "terminal_output_projection_shortcut": False,
            "next_action": "REPAIR_NOW_OR_ROUTE_AROUND_WITHOUT_WAITING_FOR_EXTERNAL_PROVIDER",
        }
        blocked["result_sha256"] = canonical_sha(blocked)
        result_path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
