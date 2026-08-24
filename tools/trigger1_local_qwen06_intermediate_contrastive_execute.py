#!/usr/bin/env python3
"""Trigger-1 zero-cost local Qwen3-0.6B intermediate causal discriminator.

The steering direction is derived only from intermediate calibration activations.
Layer/gain are frozen before holdout. Holdout uses two output-label remaps, the six
matched controls, a wrong-layer control, and lesion/rescue. Every model invocation
binds the applied intervention identity. PASS is only intermediate-representation
causal-candidate evidence; it never mints canonical/HCU/J-Space/training credit.
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
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import trigger1_intermediate_contrastive_protocol as protocol
import trigger1_local_qwen06_activation_api_execute as runtime_base

SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE_EXPERIMENT/v1"
MODEL_ID = runtime_base.MODEL_ID
MODEL_REVISION = runtime_base.MODEL_REVISION
GAINS = (0.5, 2.0, 8.0, 32.0)
LABEL_MAPS = {
    "A_POS": {"positive": "A", "negative": "B"},
    "B_POS": {"positive": "B", "negative": "A"},
}
DERIVATION_POSITIVE = (
    "Consider this claim silently: 2 + 2 = 4.",
    "Consider this claim silently: a triangle has three sides.",
    "Consider this claim silently: 7 is greater than 3.",
    "Consider this claim silently: water is made of hydrogen and oxygen.",
)
DERIVATION_NEGATIVE = (
    "Consider this claim silently: 2 + 2 = 5.",
    "Consider this claim silently: a triangle has four sides.",
    "Consider this claim silently: 7 is less than 3.",
    "Consider this claim silently: water is made only of carbon.",
)
CALIBRATION_CASES = (
    ("cal-1", "11 is greater than 4."),
    ("cal-2", "three times three equals ten."),
)
HOLDOUT_CASES = (
    ("hold-1", "5 + 6 = 11."),
    ("hold-2", "a square has five sides."),
    ("hold-3", "13 is an odd number."),
)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_text(*args: str) -> str:
    try:
        p = subprocess.run(
            ["git", "-C", str(ROOT), *args], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=5, check=False,
        )
        return p.stdout.strip() or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def candidate_layers(model: Any) -> tuple[int, ...]:
    layers = getattr(getattr(model, "model", None), "layers", None)
    if layers is None or len(layers) < 6:
        raise RuntimeError("QWEN_INTERMEDIATE_LAYER_SURFACE_UNAVAILABLE")
    n = len(layers)
    raw = (max(1, n // 4), max(2, n // 2), min(n - 2, (3 * n) // 4))
    out = tuple(sorted(set(i for i in raw if 0 < i < n - 1)))
    if len(out) < 2:
        raise RuntimeError("INSUFFICIENT_DISTINCT_INTERMEDIATE_LAYERS")
    return out


def resolve_ab_token_ids(tokenizer: Any) -> dict[str, int]:
    for values in (("A", "B"), (" A", " B")):
        ids = [tokenizer.encode(v, add_special_tokens=False) for v in values]
        if all(len(x) == 1 for x in ids) and ids[0][0] != ids[1][0]:
            return {"A": int(ids[0][0]), "B": int(ids[1][0])}
    raise RuntimeError("NO_DISTINCT_SINGLE_TOKEN_AB_PAIR")


def prompt_for(statement: str, label_map_id: str) -> str:
    mapping = LABEL_MAPS[label_map_id]
    return (
        "/no_think\nClassify the truth of the statement. "
        f"If the statement is true output only {mapping['positive']}; "
        f"if false output only {mapping['negative']}. Statement: {statement}"
    )


def _hidden(output: Any) -> Any:
    return output[0] if isinstance(output, tuple) else output


def _replace(output: Any, hidden: Any) -> Any:
    return (hidden, *output[1:]) if isinstance(output, tuple) else hidden


class IntermediateRuntime:
    def __init__(self, torch: Any, tokenizer: Any, model: Any, device: Any, token_ids: dict[str, int]):
        self.torch = torch
        self.tokenizer = tokenizer
        self.model = model
        self.device = device
        self.token_ids = token_ids
        self.invocations = 0

    def capture(self, prompt: str, layer: int) -> Any:
        captured: list[Any] = []

        def hook(_module: Any, _inputs: Any, output: Any):
            captured.append(_hidden(output)[0, -1].detach().float().cpu())
            return output

        inputs = {k: v.to(self.device) for k, v in self.tokenizer(prompt, return_tensors="pt").items()}
        handle = self.model.model.layers[layer].register_forward_hook(hook)
        try:
            with self.torch.no_grad():
                self.model(**inputs)
        finally:
            handle.remove()
        if len(captured) != 1:
            raise RuntimeError(f"INTERMEDIATE_CAPTURE_COUNT_INVALID:{len(captured)}")
        return captured[0]

    def score(
        self,
        prompt: str,
        label_map_id: str,
        layer: int,
        transform: Callable[[Any], Any] | None,
        *,
        operation: str,
        intervention_sha256: str,
    ) -> dict[str, Any]:
        hook_calls = 0

        def hook(_module: Any, _inputs: Any, output: Any):
            nonlocal hook_calls
            hook_calls += 1
            if transform is None:
                return output
            hidden = _hidden(output).clone()
            replacement = transform(hidden[:, -1, :].float()).to(device=hidden.device, dtype=hidden.dtype)
            hidden[:, -1, :] = replacement
            return _replace(output, hidden)

        inputs = {k: v.to(self.device) for k, v in self.tokenizer(prompt, return_tensors="pt").items()}
        handle = self.model.model.layers[layer].register_forward_hook(hook)
        try:
            with self.torch.no_grad():
                logits = self.model(**inputs).logits[0, -1].float().detach().cpu()
        finally:
            handle.remove()
        self.invocations += 1
        mapping = LABEL_MAPS[label_map_id]
        pos = float(logits[self.token_ids[mapping["positive"]]])
        neg = float(logits[self.token_ids[mapping["negative"]]])
        material = {
            "invocation": self.invocations,
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "label_map_id": label_map_id,
            "layer": layer,
            "operation": operation,
            "intervention_sha256": intervention_sha256,
            "hook_calls": hook_calls,
            "positive_logit": pos,
            "negative_logit": neg,
            "target_score": pos - neg,
        }
        return {**material, "runtime_receipt_sha256": canonical_sha(material)}


def as_tensor(torch: Any, values: tuple[float, ...], device: Any) -> Any:
    return torch.tensor(values, dtype=torch.float32, device=device)


def add_transform(vector: Any) -> Callable[[Any], Any]:
    return lambda last: last + vector.to(device=last.device, dtype=last.dtype)


def lesion_transform(torch: Any, direction: Any) -> Callable[[Any], Any]:
    unit = direction / torch.linalg.vector_norm(direction)

    def apply(last: Any) -> Any:
        d = unit.to(device=last.device, dtype=last.dtype)
        return last - (last * d).sum(dim=-1, keepdim=True) * d
    return apply


def rescue_transform(torch: Any, direction: Any, gain: float) -> Callable[[Any], Any]:
    lesion = lesion_transform(torch, direction)
    unit = direction / torch.linalg.vector_norm(direction)

    def apply(last: Any) -> Any:
        return lesion(last) + float(gain) * unit.to(device=last.device, dtype=last.dtype)
    return apply


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", default=os.getenv("HF_HOME") or str(Path.home() / ".cache" / "huggingface"))
    args = ap.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    result_path = out / "trigger1_intermediate_contrastive_result.json"
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    source = {"repo_head": git_text("rev-parse", "HEAD"), "repo_tree": git_text("rev-parse", "HEAD^{tree}")}

    try:
        loaded = runtime_base.load_exact_runtime(Path(args.cache_dir))
        torch, transformers, snapshot, tokenizer, model, device, checkpoint_sha, tokenizer_sha, weight_manifest = loaded
        token_ids = resolve_ab_token_ids(tokenizer)
        layers = candidate_layers(model)
        rt = IntermediateRuntime(torch, tokenizer, model, device, token_ids)
        runtime_manifest = runtime_base.runtime_manifest(torch, transformers, model)
        runtime_build_sha = canonical_sha(runtime_manifest)

        directions: dict[int, Any] = {}
        derivation_receipts: dict[str, Any] = {}
        for layer in layers:
            pos = [rt.capture(p, layer).tolist() for p in DERIVATION_POSITIVE]
            neg = [rt.capture(p, layer).tolist() for p in DERIVATION_NEGATIVE]
            direction_tuple = protocol.contrastive_direction(pos, neg)
            direction = as_tensor(torch, direction_tuple, device)
            directions[layer] = direction
            row = {
                "layer": layer,
                "positive_prompt_sha256": [hashlib.sha256(p.encode()).hexdigest() for p in DERIVATION_POSITIVE],
                "negative_prompt_sha256": [hashlib.sha256(p.encode()).hexdigest() for p in DERIVATION_NEGATIVE],
                "positive_activation_rows_sha256": canonical_sha(pos),
                "negative_activation_rows_sha256": canonical_sha(neg),
                "direction_sha256": runtime_base.tensor_sha(direction),
                "dimension": len(direction_tuple),
                "output_embedding_rows_used": False,
                "holdout_used": False,
            }
            row["receipt_sha256"] = canonical_sha(row)
            derivation_receipts[str(layer)] = row

        calibration_rows: list[dict[str, Any]] = []
        for layer in layers:
            direction_tuple = tuple(float(x) for x in directions[layer].detach().float().cpu().tolist())
            for gain in GAINS:
                controls = protocol.control_vectors(direction_tuple, gain)
                for case_id, statement in CALIBRATION_CASES:
                    prompt = prompt_for(statement, "A_POS")
                    for control in protocol.REQUIRED_CONTROLS:
                        vec = as_tensor(torch, controls[control], device)
                        vector_sha = runtime_base.tensor_sha(vec)
                        obs = rt.score(
                            prompt, "A_POS", layer, add_transform(vec),
                            operation=control, intervention_sha256=vector_sha,
                        )
                        calibration_rows.append({
                            "split": "calibration", "layer": layer, "gain": gain,
                            "case_id": case_id, "control": control,
                            "target_score": obs["target_score"],
                            "applied_vector_sha256": vector_sha,
                            "runtime_receipt_sha256": obs["runtime_receipt_sha256"],
                        })

        selected = protocol.select_layer_gain(calibration_rows)
        holdout_rows: list[dict[str, Any]] = []
        runtime_receipts: list[dict[str, Any]] = []
        auxiliary: list[dict[str, Any]] = []
        if selected.get("selected") is True:
            layer = int(selected["layer"])
            gain = float(selected["gain"])
            direction = directions[layer]
            direction_sha = runtime_base.tensor_sha(direction)
            controls = protocol.control_vectors(
                tuple(float(x) for x in direction.detach().float().cpu().tolist()), gain
            )
            wrong_layer = next((x for x in layers if x != layer), layer - 1 if layer > 1 else layer + 1)
            for label_map_id in LABEL_MAPS:
                for case_id, statement in HOLDOUT_CASES:
                    prompt = prompt_for(statement, label_map_id)
                    baseline_identity = canonical_sha({"operation": "BASELINE_REFERENCE", "layer": layer, "vector": "ZERO"})
                    baseline = rt.score(
                        prompt, label_map_id, layer, None,
                        operation="BASELINE_REFERENCE", intervention_sha256=baseline_identity,
                    )
                    wrong_vec = direction * gain
                    wrong = rt.score(
                        prompt, label_map_id, wrong_layer, add_transform(wrong_vec),
                        operation="WRONG_LAYER_PLUS_VECTOR",
                        intervention_sha256=runtime_base.tensor_sha(wrong_vec),
                    )
                    lesion = rt.score(
                        prompt, label_map_id, layer, lesion_transform(torch, direction),
                        operation="LESION",
                        intervention_sha256=canonical_sha({"operation": "LESION", "direction_sha256": direction_sha}),
                    )
                    rescue = rt.score(
                        prompt, label_map_id, layer, rescue_transform(torch, direction, gain),
                        operation="RESCUE",
                        intervention_sha256=canonical_sha({"operation": "RESCUE", "direction_sha256": direction_sha, "gain": gain}),
                    )
                    wrong_delta = wrong["target_score"] - baseline["target_score"]
                    lesion_delta = lesion["target_score"] - baseline["target_score"]
                    rescue_delta = rescue["target_score"] - lesion["target_score"]
                    runtime_receipts.extend((baseline, wrong, lesion, rescue))
                    auxiliary.append({
                        "case_id": case_id, "label_map_id": label_map_id,
                        "selected_layer": layer, "wrong_layer": wrong_layer,
                        "baseline_receipt_sha256": baseline["runtime_receipt_sha256"],
                        "wrong_layer_receipt_sha256": wrong["runtime_receipt_sha256"],
                        "lesion_receipt_sha256": lesion["runtime_receipt_sha256"],
                        "rescue_receipt_sha256": rescue["runtime_receipt_sha256"],
                        "wrong_layer_delta": wrong_delta, "lesion_delta": lesion_delta,
                        "rescue_delta": rescue_delta,
                    })
                    for control in protocol.REQUIRED_CONTROLS:
                        vec = as_tensor(torch, controls[control], device)
                        vector_sha = runtime_base.tensor_sha(vec)
                        obs = rt.score(
                            prompt, label_map_id, layer, add_transform(vec),
                            operation=control, intervention_sha256=vector_sha,
                        )
                        runtime_receipts.append(obs)
                        holdout_rows.append({
                            "split": "holdout", "layer": layer, "gain": gain,
                            "case_id": case_id, "label_map_id": label_map_id,
                            "control": control, "target_score": obs["target_score"],
                            "wrong_layer_delta": wrong_delta, "lesion_delta": lesion_delta,
                            "rescue_delta": rescue_delta,
                            "applied_vector_sha256": vector_sha,
                            "runtime_receipt_sha256": obs["runtime_receipt_sha256"],
                        })

        verdict = (
            protocol.adjudicate_holdout(
                holdout_rows,
                selected_layer=int(selected["layer"]),
                selected_gain=float(selected["gain"]),
            )
            if selected.get("selected") is True
            else {"pass": False, "classification": str(selected.get("reason") or "NO_CALIBRATION_SELECTION")}
        )
        evidence = {
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
            "runtime_manifest": runtime_manifest,
            "runtime_build_sha256": runtime_build_sha,
            "device": str(device),
            "candidate_layers": list(layers),
            "direction_derivation": derivation_receipts,
            "selection": selected,
            "calibration_row_count": len(calibration_rows),
            "calibration_rows_sha256": canonical_sha(calibration_rows),
            "holdout_row_count": len(holdout_rows),
            "holdout_rows": holdout_rows,
            "runtime_receipts_sha256": canonical_sha(runtime_receipts),
            "auxiliary_control_receipts": auxiliary,
            "auxiliary_control_receipts_sha256": canonical_sha(auxiliary),
            "label_maps": LABEL_MAPS,
            "verdict": verdict,
            "external_llm_credentials_read": False,
            "external_llm_provider_calls": 0,
            "zero_provider_billing": True,
            "terminal_output_projection_shortcut_used": False,
            "output_embedding_rows_used_for_direction": False,
            "holdout_used_for_direction_or_layer_gain_selection": False,
            "credit_scope": protocol.CREDIT_SCOPE,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
        }
        evidence["result_sha256"] = canonical_sha(evidence)
        result_path.write_text(json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0 if verdict.get("pass") else 2
    except Exception as exc:
        blocked = {
            "schema": SCHEMA,
            "status": "BLOCKED_LOCAL_INTERMEDIATE_DISCRIMINATOR",
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": source,
            "reason": f"{type(exc).__name__}:{str(exc)[:1000]}",
            "external_llm_credentials_read": False,
            "external_llm_provider_calls": 0,
            "zero_provider_billing": True,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
        }
        blocked["result_sha256"] = canonical_sha(blocked)
        result_path.write_text(json.dumps(blocked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
