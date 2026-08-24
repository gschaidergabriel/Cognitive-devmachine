#!/usr/bin/env python3
"""Trigger-1 V2 local zero-cost Qwen3-0.6B hidden-state vector API experiment.

The experiment loads one exact Qwen3-0.6B revision, exposes a loopback-only HTTP
API, applies a model-internal vector at the final model norm output, performs
calibration without holdout peeking, runs the six required matched controls on
disjoint holdout prompts, and emits a promotion-candidate file only when the
directional effect survives the controls.

This is intentionally provider-independent. No external LLM credential is read.
Exact source identity is fail-closed before model loading: HEAD, tree and a digest
of the full porcelain status are bound, and a dirty checkout is rejected.
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
SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_ACTIVATION_API_EXPERIMENT/v1"
CANDIDATE_SCHEMA = "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1"
CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)
CALIBRATION_GAINS = (0.5, 2.0, 8.0, 32.0)
CALIBRATION = (
    (1701, "/no_think\nCalibration C1. Return exactly one symbol from A, B, C."),
    (1702, "/no_think\nCalibration C2. Choose exactly one uppercase letter: A, B, or C."),
)
HOLDOUT = (
    (2718, "/no_think\nHoldout H1. Reply using only one of these tokens: A B C."),
    (3141, "/no_think\nHoldout H2. Select one uppercase option from A, B, C and output only it."),
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
        if p.returncode != 0:
            return "UNKNOWN"
        return p.stdout.strip()
    except Exception:
        return "UNKNOWN"


def exact_source_identity() -> dict[str, Any]:
    head = git_text("rev-parse", "HEAD")
    tree = git_text("rev-parse", "HEAD^{tree}")
    status = git_text("status", "--porcelain=v1", "--untracked-files=all")
    if head == "UNKNOWN" or tree == "UNKNOWN" or status == "UNKNOWN":
        raise RuntimeError("SOURCE_IDENTITY_UNRESOLVED")
    try:
        if len(head) != 40 or len(tree) != 40:
            raise ValueError
        int(head, 16)
        int(tree, 16)
    except ValueError as exc:
        raise RuntimeError("SOURCE_IDENTITY_INVALID") from exc
    return {
        "repo_head": head,
        "repo_tree": tree,
        "repo_dirty": bool(status),
        "repo_status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
    }


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

    if not hasattr(model, "model") or not hasattr(model.model, "norm"):
        raise RuntimeError("QWEN_FINAL_NORM_HOOK_SURFACE_UNAVAILABLE")

    return torch, transformers, snapshot, tokenizer, model, device, checkpoint_sha, got_tok, weight_manifest


def resolve_token_triplet(tokenizer: Any) -> tuple[dict[str, int], dict[str, str]]:
    candidate_sets = (
        ("A", "B", "C"),
        (" A", " B", " C"),
        ("1", "2", "3"),
    )
    for values in candidate_sets:
        ids = []
        for text in values:
            encoded = tokenizer.encode(text, add_special_tokens=False)
            if len(encoded) != 1:
                break
            ids.append(int(encoded[0]))
        if len(ids) == 3 and len(set(ids)) == 3:
            labels = {"A": values[0], "B": values[1], "C": values[2]}
            return {"A": ids[0], "B": ids[1], "C": ids[2]}, labels
    raise RuntimeError("NO_DISTINCT_SINGLE_TOKEN_ABC_TRIPLET")


def unit_target_vector(torch: Any, model: Any, token_ids: dict[str, int]):
    weight = model.get_output_embeddings().weight.detach().float()
    v = weight[token_ids["A"]] - 0.5 * (weight[token_ids["B"]] + weight[token_ids["C"]])
    norm = torch.linalg.vector_norm(v)
    if not bool(torch.isfinite(norm)) or float(norm) <= 0:
        raise RuntimeError("TARGET_VECTOR_DEGENERATE")
    return v / norm


def matched_family(torch: Any, base: Any, gain: float) -> dict[str, Any]:
    plus = base * float(gain)
    sign = -plus
    null = torch.zeros_like(plus)
    n = plus.numel()
    idx = torch.arange(n, dtype=torch.float32, device=plus.device)
    seed_vec = torch.sin(idx * 0.017 + 0.37) + torch.cos(idx * 0.031 + 0.11)
    projection = torch.dot(seed_vec, plus) / torch.dot(plus, plus)
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
    def __init__(self, torch: Any, tokenizer: Any, model: Any, device: Any, base_vector: Any, token_ids: dict[str, int]):
        self.torch = torch
        self.tokenizer = tokenizer
        self.model = model
        self.device = device
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
            handle = self.model.model.norm.register_forward_hook(hook)
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
            "token_logits": trio,
            "target_score": score,
            "best_label": best,
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
    with urllib.request.urlopen(req, timeout=120) as resp:
        obj = json.loads(resp.read().decode("utf-8"))
    if not isinstance(obj, dict) or obj.get("error"):
        raise RuntimeError(f"LOCAL_API_ERROR:{obj}")
    return obj


def select_gain(rows: list[dict[str, Any]]) -> float | None:
    ranked: list[tuple[float, float]] = []
    for gain in CALIBRATION_GAINS:
        plus = [r["target_score"] for r in rows if r["gain"] == gain and r["control"] == "+VECTOR"]
        sign = [r["target_score"] for r in rows if r["gain"] == gain and r["control"] == "SIGN_FLIP"]
        base = [r["target_score"] for r in rows if r["gain"] == gain and r["control"] == "BASELINE"]
        if plus and sign and base:
            metric = min(p - b for p, b in zip(plus, base)) + min(b - s for b, s in zip(base, sign))
            ranked.append((metric, gain))
    ranked.sort(reverse=True)
    return ranked[0][1] if ranked and ranked[0][0] > 0 else None


def adjudicate(holdout_rows: list[dict[str, Any]], selected_gain: float | None) -> dict[str, Any]:
    if selected_gain is None:
        return {"pass": False, "classification": "NO_DIRECTIONAL_CALIBRATION_GAIN"}
    grouped = {name: [] for name in CONTROLS}
    by_case: dict[tuple[int, str], dict[str, float]] = {}
    for row in holdout_rows:
        grouped[row["control"]].append(float(row["target_score"]))
        key = (int(row["seed"]), str(row["prompt_family"]))
        by_case.setdefault(key, {})[row["control"]] = float(row["target_score"])

    means = {name: sum(vals) / len(vals) if vals else float("nan") for name, vals in grouped.items()}
    paired_plus = []
    paired_sign = []
    paired_null = []
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
        "classification": "DIRECT_LOCAL_HIDDEN_STATE_VECTOR_EFFECT_REPRODUCED" if passed else "CONTROL_FAMILY_DID_NOT_ESTABLISH_SPECIFIC_DIRECTIONAL_EFFECT",
        "selected_gain": selected_gain,
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
    source: dict[str, Any] = {
        "repo_head": "UNKNOWN",
        "repo_tree": "UNKNOWN",
        "repo_dirty": None,
        "repo_status_sha256": None,
    }

    try:
        source = exact_source_identity()
        if source["repo_dirty"] is not False:
            raise RuntimeError("DIRTY_SOURCE_TREE_FAIL_CLOSED")

        torch, transformers, snapshot, tokenizer, model, device, checkpoint_sha, tokenizer_sha, weight_manifest = load_exact_runtime(Path(args.cache_dir))
        token_ids, token_labels = resolve_token_triplet(tokenizer)
        base_vector = unit_target_vector(torch, model, token_ids).to(device)
        runtime = runtime_manifest(torch, transformers, model)
        runtime_build_sha = canonical_sha(runtime)
        source_packet = {
            "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "intent": "increase latent preference for semantic output label A relative to B and C",
            "basis": "exact Qwen3-0.6B final-normalized-hidden coordinate system",
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
            "activation_site": "model.model.norm:output:last_token",
            "hidden_size": int(base_vector.numel()),
            "construction": "lm_head(A)-mean(lm_head(B),lm_head(C)) normalized",
        }
        adapter_sha = canonical_sha(adapter)
        local_vector_sha = tensor_sha(base_vector)

        state = RuntimeState(torch, tokenizer, model, device, base_vector, token_ids)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/jspace/logits"

        calibration_rows: list[dict[str, Any]] = []
        for gain in CALIBRATION_GAINS:
            for seed, prompt in CALIBRATION:
                for control in ("BASELINE", "+VECTOR", "SIGN_FLIP"):
                    row = post_json(endpoint, {"prompt": prompt, "control": control, "gain": gain, "seed": seed})
                    row["prompt_family"] = f"cal-{seed}"
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

        controls = {}
        for control in CONTROLS:
            receipts = [r["runtime_receipt_sha256"] for r in holdout_rows if r["control"] == control]
            controls[control] = {
                "runtime_receipt_sha256": canonical_sha(receipts),
                "observations": len(receipts),
            }

        applied_plus_rows = [r for r in holdout_rows if r["control"] == "+VECTOR"]
        applied_vector_sha = (
            applied_plus_rows[0]["applied_vector_sha256"] if applied_plus_rows else tensor_sha(base_vector * float(selected_gain or 0.0))
        )
        intervention_receipt_sha = canonical_sha([r["runtime_receipt_sha256"] for r in applied_plus_rows])
        analysis_receipt_sha = canonical_sha({"verdict": verdict, "holdout_receipts": [r["runtime_receipt_sha256"] for r in holdout_rows]})
        local_runtime_receipt = canonical_sha({
            "endpoint": endpoint,
            "runtime_build_sha256": runtime_build_sha,
            "checkpoint_sha256": checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "source": source,
            "api_invocations": state.invocations,
        })

        candidate = {
            "schema": CANDIDATE_SCHEMA,
            "runtime_intervention_class": "LOCAL_PYTORCH_ACTIVATION_INTERVENTION",
            "source_identity": {
                "repo_head": source["repo_head"],
                "repo_tree": source["repo_tree"],
                "repo_dirty": source["repo_dirty"],
                "repo_status_sha256": source["repo_status_sha256"],
                "runtime_build_sha256": runtime_build_sha,
                "checkpoint_sha256": checkpoint_sha,
                "tokenizer_sha256": tokenizer_sha,
            },
            "intervention": {
                "runtime_observed": bool(applied_plus_rows and all(r["hook_calls"] > 0 for r in applied_plus_rows)),
                "invocation_id": canonical_sha([r["runtime_receipt_sha256"] for r in holdout_rows]),
                "activation_site": "model.model.norm:output:last_token",
                "source_packet_sha256": source_packet_sha,
                "adapter_sha256": adapter_sha,
                "local_vector_sha256": local_vector_sha,
                "applied_vector_sha256": applied_vector_sha,
                "runtime_intervention_receipt_sha256": intervention_receipt_sha,
                "gain": selected_gain,
                "layer_start": int(getattr(model.config, "num_hidden_layers", 28)),
                "layer_end": int(getattr(model.config, "num_hidden_layers", 28)),
            },
            "controls": controls,
            "calibration": {
                "family_id": canonical_sha([p for _, p in CALIBRATION]),
                "seeds": [s for s, _ in CALIBRATION],
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
            "status": "BLOCKED_LOCAL_FASTPATH",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "reason": f"{type(exc).__name__}:{str(exc)[:1000]}",
            "external_provider_credentials_read": False,
            "zero_provider_billing": True,
            "next_action": "ROUTE_AROUND_OR_REPAIR_NOW_WITHOUT_WAITING_FOR_EXTERNAL_PROVIDER",
        }
        blocked["result_sha256"] = canonical_sha(blocked)
        result_path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
