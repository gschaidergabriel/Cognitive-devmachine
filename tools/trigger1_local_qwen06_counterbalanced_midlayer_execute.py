#!/usr/bin/env python3
"""Trigger-1 v3 counterbalanced midlayer causal discriminator.

This successor keeps the exact zero-provider-billing local Qwen3-0.6B runtime and
six matched controls, but closes the scientific-independence mismatch between the
canonical midlayer executor and CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v3:

* the steering vector is derived only from a disjoint semantic internal-activation
  family and never from output-head weights or holdout data;
* gain calibration and holdout use explicit codebooks that rotate the semantic
  TARGET role across A/B/C exactly once each;
* the token-output metric is therefore genuinely label-counterbalanced rather than
  merely declared counterbalanced;
* derivation and metric receipts are persisted into both candidate and result.

A positive result remains a promotion candidate only. No canonical EntityOS/HCU,
J-Space model-runtime, or training credit is minted here.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import trigger1_local_qwen06_midlayer_causal_execute as base

SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_COUNTERBALANCED_MIDLAYER_EXPERIMENT/v1"
CANDIDATE_SCHEMA = base.CANDIDATE_SCHEMA
VECTOR_DERIVATION_METHOD = "INTERNAL_ACTIVATION_SEMANTIC_CONTRAST_MEAN"
METRIC_NAME = "COUNTERBALANCED_TARGET_LOGIT_MINUS_MEAN_NONTARGET_LOGITS"

# These prompts derive the intervention direction. They contain no A/B/C codebook and
# are disjoint from both gain calibration and holdout.
BASIS_PROMPTS = (
    (1101, "TARGET", "/no_think\nRepresent the abstract relation intended selection. Hold that semantic relation internally."),
    (1102, "REJECTED", "/no_think\nRepresent the abstract relation rejected alternative. Hold that semantic relation internally."),
    (1103, "IRRELEVANT", "/no_think\nRepresent the abstract relation irrelevant alternative. Hold that semantic relation internally."),
    (1111, "TARGET", "/no_think\nPrepare an internal representation of the chosen or intended relation, without emitting a code symbol."),
    (1112, "REJECTED", "/no_think\nPrepare an internal representation of a specifically rejected relation, without emitting a code symbol."),
    (1113, "IRRELEVANT", "/no_think\nPrepare an internal representation of a non-selected irrelevant relation, without emitting a code symbol."),
)

# Semantic TARGET is mapped to A, B and C exactly once in each evaluation family.
GAIN_CALIBRATION = (
    (1701, "A", "/no_think\nCodebook C1: intended=A, rejected=B, irrelevant=C. Output only the symbol for intended."),
    (1702, "B", "/no_think\nCodebook C2: rejected=A, intended=B, irrelevant=C. Output only the symbol for intended."),
    (1703, "C", "/no_think\nCodebook C3: irrelevant=A, rejected=B, intended=C. Output only the symbol for intended."),
)
HOLDOUT = (
    (2718, "B", "/no_think\nFresh code H1: decoy=A, selected=B, unused=C. Return only the code for selected."),
    (3141, "C", "/no_think\nFresh code H2: unused=A, decoy=B, selected=C. Return only the code for selected."),
    (5772, "A", "/no_think\nFresh code H3: selected=A, unused=B, decoy=C. Return only the code for selected."),
)


def canonical_sha(value: Any) -> str:
    return base.canonical_sha(value)


def family_id(rows: tuple[tuple[int, str, str], ...]) -> str:
    return canonical_sha([{"seed": seed, "target": target, "prompt": prompt} for seed, target, prompt in rows])


def counterbalance_manifest(rows: tuple[tuple[int, str, str], ...]) -> dict[str, Any]:
    targets = [target for _seed, target, _prompt in rows]
    return {
        "targets_in_order": targets,
        "counts": {label: targets.count(label) for label in ("A", "B", "C")},
        "exact_once_each": sorted(targets) == ["A", "B", "C"],
        "surface_labels": ["A", "B", "C"],
    }


def metric_definition() -> dict[str, Any]:
    return {
        "name": METRIC_NAME,
        "formula": "logit(target_surface_label)-mean(logit(other_two_surface_labels))",
        "metric_uses_output_tokens": True,
        "label_mapping_counterbalanced": True,
        "gain_calibration_counterbalance": counterbalance_manifest(GAIN_CALIBRATION),
        "holdout_counterbalance": counterbalance_manifest(HOLDOUT),
        "basis_prompts_used_for_metric": False,
    }


def metric_definition_sha256() -> str:
    return canonical_sha(metric_definition())


def vector_derivation_evidence(basis_receipts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "method": VECTOR_DERIVATION_METHOD,
        "uses_output_head_weights": False,
        "uses_holdout_data": False,
        "derivation_family_id": family_id(BASIS_PROMPTS),
        "derivation_receipt_sha256": canonical_sha(basis_receipts),
    }


def semantic_activation_basis(torch: Any, tokenizer: Any, model: Any, device: Any, layer: Any):
    rows: dict[str, list[Any]] = {"TARGET": [], "REJECTED": [], "IRRELEVANT": []}
    receipts: list[dict[str, Any]] = []
    for seed, role, prompt in BASIS_PROMPTS:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        act = base.extract_internal_activation(torch, tokenizer, model, device, layer, prompt)
        rows[role].append(act)
        receipts.append({
            "seed": seed,
            "semantic_role": role,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "activation_sha256": base.tensor_sha(act),
        })
    means = {role: torch.stack(values, dim=0).mean(dim=0) for role, values in rows.items()}
    raw = means["TARGET"] - 0.5 * (means["REJECTED"] + means["IRRELEVANT"])
    norm = torch.linalg.vector_norm(raw)
    if not bool(torch.isfinite(norm)) or float(norm) <= 1e-12:
        raise RuntimeError("SEMANTIC_INTERNAL_CONTRAST_BASIS_DEGENERATE")
    return (raw / norm).to(device), receipts


def target_score(token_logits: dict[str, float], target_label: str) -> float:
    if target_label not in {"A", "B", "C"}:
        raise ValueError("TARGET_LABEL_MUST_BE_ABC")
    others = [value for label, value in token_logits.items() if label != target_label]
    if len(others) != 2:
        raise ValueError("DISTINCT_ABC_LOGITS_REQUIRED")
    return float(token_logits[target_label]) - 0.5 * (float(others[0]) + float(others[1]))


class CounterbalancedRuntimeState:
    def __init__(self, torch: Any, tokenizer: Any, model: Any, device: Any, layer: Any, layer_index: int, base_vector: Any, token_ids: dict[str, int]):
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
        target_label = str(payload.get("target_label") or "")
        if control not in base.CONTROLS:
            raise ValueError("UNKNOWN_CONTROL")
        if target_label not in {"A", "B", "C"}:
            raise ValueError("TARGET_LABEL_MUST_BE_ABC")

        family = base.matched_family(self.torch, self.base_vector, gain)
        vector = family[control].to(self.device)
        applied_sha = base.tensor_sha(vector)
        hook_calls = 0

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
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            handle = self.layer.register_forward_hook(hook)
            try:
                with self.torch.no_grad():
                    output = self.model(**inputs)
                    logits = output.logits[0, -1].float().detach().cpu()
            finally:
                handle.remove()
            self.invocations += 1

        trio = {label: float(logits[token_id]) for label, token_id in self.token_ids.items()}
        score = target_score(trio, target_label)
        material = {
            "invocation": self.invocations,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "control": control,
            "gain": gain,
            "seed": seed,
            "target_label": target_label,
            "activation_site": f"model.model.layers[{self.layer_index}]:output:last_token",
            "applied_vector_sha256": applied_sha,
            "hook_calls": hook_calls,
            "token_logits": trio,
            "target_score": score,
            "metric_definition_sha256": metric_definition_sha256(),
            "best_label": max(trio, key=trio.get),
        }
        return {
            **material,
            "runtime_receipt_sha256": canonical_sha(material),
            "runtime_observed_intervention": bool(hook_calls > 0 and control != "BASELINE"),
        }


def make_handler(state: CounterbalancedRuntimeState):
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


def post_case(endpoint: str, seed: int, target_label: str, prompt: str, control: str, gain: float) -> dict[str, Any]:
    row = base.post_json(endpoint, {
        "prompt": prompt,
        "control": control,
        "gain": gain,
        "seed": seed,
        "target_label": target_label,
    })
    row["prompt_family"] = f"case-{seed}"
    return row


def select_gain(rows: list[dict[str, Any]]) -> float | None:
    ranked: list[tuple[float, float]] = []
    for gain in base.GAIN_GRID:
        by_seed: dict[int, dict[str, float]] = {}
        for row in rows:
            if row["gain"] == gain:
                by_seed.setdefault(int(row["seed"]), {})[row["control"]] = float(row["target_score"])
        margins: list[float] = []
        for values in by_seed.values():
            if all(key in values for key in ("BASELINE", "+VECTOR", "SIGN_FLIP")):
                margins.append(min(values["+VECTOR"] - values["BASELINE"], values["BASELINE"] - values["SIGN_FLIP"]))
        if margins:
            ranked.append((min(margins), gain))
    ranked.sort(reverse=True)
    return ranked[0][1] if ranked and ranked[0][0] > 0 else None


def adjudicate(rows: list[dict[str, Any]], selected_gain: float | None) -> dict[str, Any]:
    if selected_gain is None:
        return {"pass": False, "classification": "NO_COUNTERBALANCED_DIRECTIONAL_GAIN_CALIBRATION"}
    grouped = {name: [] for name in base.CONTROLS}
    by_case: dict[tuple[int, str], dict[str, float]] = {}
    for row in rows:
        grouped[row["control"]].append(float(row["target_score"]))
        key = (int(row["seed"]), str(row["target_label"]))
        by_case.setdefault(key, {})[row["control"]] = float(row["target_score"])

    paired_plus: list[float] = []
    paired_sign: list[float] = []
    paired_null: list[float] = []
    plus_vs_orth: list[float] = []
    plus_vs_perm: list[float] = []
    for values in by_case.values():
        if all(key in values for key in base.CONTROLS):
            paired_plus.append(values["+VECTOR"] - values["BASELINE"])
            paired_sign.append(values["BASELINE"] - values["SIGN_FLIP"])
            paired_null.append(abs(values["NULL_VECTOR"] - values["BASELINE"]))
            plus_vs_orth.append(values["+VECTOR"] - values["ORTHOGONAL_SAME_NORM"])
            plus_vs_perm.append(values["+VECTOR"] - values["PERMUTED_SAME_NORM"])

    passed = bool(
        paired_plus
        and min(paired_plus) > 0
        and min(paired_sign) > 0
        and max(paired_null) <= 1e-5
        and min(plus_vs_orth) > 0
        and min(plus_vs_perm) > 0
        and all(row.get("hook_calls", 0) > 0 for row in rows if row["control"] != "BASELINE")
    )
    return {
        "pass": passed,
        "classification": "COUNTERBALANCED_NONTERMINAL_INTERNAL_VECTOR_EFFECT_REPRODUCED" if passed else "COUNTERBALANCED_CONTROL_FAMILY_DID_NOT_ESTABLISH_SPECIFIC_INTERNAL_EFFECT",
        "selected_gain": selected_gain,
        "target_labels_observed": sorted({str(row.get("target_label")) for row in rows}),
        "min_paired_plus_vs_baseline": min(paired_plus) if paired_plus else None,
        "min_paired_baseline_vs_sign_flip": min(paired_sign) if paired_sign else None,
        "max_null_drift": max(paired_null) if paired_null else None,
        "min_plus_vs_orthogonal_same_norm": min(plus_vs_orth) if plus_vs_orth else None,
        "min_plus_vs_permuted_same_norm": min(plus_vs_perm) if plus_vs_perm else None,
        "strongest_counterexample_plus_delta": min(paired_plus) if paired_plus else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--cache-dir", default=os.getenv("HF_HOME") or str(Path.home() / ".cache" / "huggingface"))
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "trigger1_local_activation_api_result.json"
    candidate_path = out / "trigger1_direct_steering_candidate.json"
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    source = {
        "repo_head": base.git_text("rev-parse", "HEAD"),
        "repo_tree": base.git_text("rev-parse", "HEAD^{tree}"),
        "repo_dirty_porcelain_sha256": canonical_sha(base.git_text("status", "--porcelain=v1")),
        "executor_sha256": base.sha256_file(Path(__file__)),
    }
    server: ThreadingHTTPServer | None = None

    try:
        (
            torch,
            transformers,
            _snapshot,
            tokenizer,
            model,
            device,
            checkpoint_sha,
            tokenizer_sha,
            weight_manifest,
            layer_index,
        ) = base.load_exact_runtime(Path(args.cache_dir))
        token_ids, token_labels = base.resolve_token_triplet(tokenizer)
        layers = model.model.layers
        layer = layers[layer_index]
        steering_vector, basis_receipts = semantic_activation_basis(torch, tokenizer, model, device, layer)
        derivation = vector_derivation_evidence(basis_receipts)
        metric = metric_definition()
        metric_sha = metric_definition_sha256()
        runtime = base.runtime_manifest(torch, transformers, model)
        runtime_build_sha = canonical_sha(runtime)
        num_layers = len(layers)
        downstream_layers = num_layers - layer_index - 1
        if downstream_layers < 1:
            raise RuntimeError("NO_DOWNSTREAM_TRANSFORMER_COMPUTATION")

        activation_site = f"model.model.layers[{layer_index}]:output:last_token"
        source_packet = {
            "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "intent": "shift a semantic intended-selection representation before downstream transformer computation",
            "basis": "semantic internal activation contrast TARGET vs REJECTED/IRRELEVANT",
            "basis_family_sha256": derivation["derivation_family_id"],
            "derivation_receipt_sha256": derivation["derivation_receipt_sha256"],
            "uses_output_head_weights": False,
            "uses_holdout_data": False,
            "metric_definition_sha256": metric_sha,
            "label_mapping_counterbalanced": True,
            "token_labels": token_labels,
            "token_ids": token_ids,
            "model": base.MODEL_ID,
            "revision": base.MODEL_REVISION,
            "activation_site": activation_site,
        }
        source_packet_sha = canonical_sha(source_packet)
        adapter = {
            "schema": "JSPACE_LATENT_BASIS_ADAPTER/v1",
            "model": base.MODEL_ID,
            "revision": base.MODEL_REVISION,
            "activation_site": activation_site,
            "hidden_size": int(steering_vector.numel()),
            "construction": "mean(TARGET)-0.5*(mean(REJECTED)+mean(IRRELEVANT)), normalized",
            "basis_constructed_without_output_head": True,
            "basis_constructed_without_holdout": True,
            "downstream_transformer_layers": downstream_layers,
            "terminal_output_projection_shortcut": False,
        }
        adapter_sha = canonical_sha(adapter)
        local_vector_sha = base.tensor_sha(steering_vector)

        state = CounterbalancedRuntimeState(torch, tokenizer, model, device, layer, layer_index, steering_vector, token_ids)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(state))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        endpoint = f"http://127.0.0.1:{server.server_port}/v1/jspace/logits"

        calibration_rows: list[dict[str, Any]] = []
        for gain in base.GAIN_GRID:
            for seed, target_label, prompt in GAIN_CALIBRATION:
                for control in ("BASELINE", "+VECTOR", "SIGN_FLIP"):
                    calibration_rows.append(post_case(endpoint, seed, target_label, prompt, control, gain))
        selected_gain = select_gain(calibration_rows)

        holdout_rows: list[dict[str, Any]] = []
        if selected_gain is not None:
            for seed, target_label, prompt in HOLDOUT:
                for control in base.CONTROLS:
                    holdout_rows.append(post_case(endpoint, seed, target_label, prompt, control, selected_gain))
        verdict = adjudicate(holdout_rows, selected_gain)

        controls: dict[str, Any] = {}
        for control in base.CONTROLS:
            receipts = [row["runtime_receipt_sha256"] for row in holdout_rows if row["control"] == control]
            controls[control] = {"runtime_receipt_sha256": canonical_sha(receipts), "observations": len(receipts)}

        plus_rows = [row for row in holdout_rows if row["control"] == "+VECTOR"]
        applied_vector_sha = plus_rows[0]["applied_vector_sha256"] if plus_rows else base.tensor_sha(steering_vector * float(selected_gain or 0.0))
        intervention_receipt_sha = canonical_sha([row["runtime_receipt_sha256"] for row in plus_rows])
        holdout_receipts = [row["runtime_receipt_sha256"] for row in holdout_rows]
        analysis_receipt_sha = canonical_sha({"verdict": verdict, "holdout_receipts": holdout_receipts, "metric_definition_sha256": metric_sha})
        local_runtime_receipt = canonical_sha({
            "endpoint": endpoint,
            "runtime_build_sha256": runtime_build_sha,
            "checkpoint_sha256": checkpoint_sha,
            "tokenizer_sha256": tokenizer_sha,
            "source": source,
            "activation_site": activation_site,
            "vector_derivation_receipt_sha256": derivation["derivation_receipt_sha256"],
            "metric_definition_sha256": metric_sha,
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
                "runtime_observed": bool(plus_rows and all(row["hook_calls"] > 0 for row in plus_rows)),
                "invocation_id": canonical_sha(holdout_receipts),
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
            },
            "vector_derivation": derivation,
            "controls": controls,
            "calibration": {
                "family_id": family_id(GAIN_CALIBRATION),
                "seeds": [seed for seed, _target, _prompt in GAIN_CALIBRATION],
                "selected_gain": selected_gain,
                "label_mapping_counterbalanced": counterbalance_manifest(GAIN_CALIBRATION)["exact_once_each"],
            },
            "holdout": {
                "family_id": family_id(HOLDOUT),
                "seeds": [seed for seed, _target, _prompt in HOLDOUT],
                "reproducible_directional_effect": bool(verdict.get("pass")),
                "strongest_counterexample_recorded": True,
                "analysis_receipt_sha256": analysis_receipt_sha,
                "evaluation_independent_of_vector_derivation": True,
                "metric_definition_sha256": metric_sha,
                "metric_uses_output_tokens": True,
                "label_mapping_counterbalanced": counterbalance_manifest(HOLDOUT)["exact_once_each"],
            },
            "transport": {
                "hosted_prompt_only": False,
                "api_served": True,
                "loopback_only": True,
                "endpoint": endpoint,
            },
            "target": {
                "relation": base.OWNER_API_TARGET_CLASS if hasattr(base, "OWNER_API_TARGET_CLASS") else "ZERO_COST_API_SERVED_MODEL_RUNTIME",
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
            "terminal_output_projection_shortcut": False,
            "basis_receipts": basis_receipts,
            "vector_derivation": derivation,
            "metric_definition": metric,
            "metric_definition_sha256": metric_sha,
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
            "evidence_boundary": "PASS is a model-specific nonterminal counterbalanced causal promotion candidate only; no canonical EntityOS/HCU, J-Space model-runtime or training credit is minted.",
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
            "status": "BLOCKED_COUNTERBALANCED_MIDLAYER_FASTPATH",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "reason": f"{type(exc).__name__}:{str(exc)[:1000]}",
            "external_provider_credentials_read": False,
            "zero_provider_billing": True,
            "terminal_output_projection_shortcut": False,
            "next_action": "REPAIR_OR_ROUTE_AROUND_COUNTERBALANCED_MIDLAYER_BLOCKER",
        }
        blocked["result_sha256"] = canonical_sha(blocked)
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
