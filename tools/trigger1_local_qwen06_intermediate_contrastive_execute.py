#!/usr/bin/env python3
"""Trigger-1 zero-cost local Qwen3-0.6B intermediate causal discriminator.

Derives the steering direction only from intermediate calibration activations,
freezes layer/gain before holdout, and evaluates label-remapped holdout with six
matched controls plus wrong-layer and lesion/rescue tests. No provider credential
or external LLM API is used. A PASS is only an intermediate-representation causal
candidate and never mints canonical/HCU/J-Space/training credit by itself.
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

# Direction derivation uses only these prompt-end intermediate activations.
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
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


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


def output_hidden(output: Any) -> Any:
    return output[0] if isinstance(output, tuple) else output


def replace_hidden(output: Any, hidden: Any) -> Any:
    if isinstance(output, tuple):
        return (hidden, *output[1:])
    return hidden


class IntermediateRuntime:
    def __init__(self, torch: Any, tokenizer: Any, model: Any, device: Any, token_ids: dict[str, int]):
        self.torch = torch
        self.tokenizer = tokenizer
        self.model = model
        self.device = device
        self.token_ids = token_ids
        self.invocations = 0

    def capture(self, prompt: str, layer_index: int) -> Any:
        captured: list[Any] = []

        def hook(_module: Any, _inputs: Any, output: Any):
            hidden = output_hidden(output)
            captured.append(hidden[0, -1].detach().float().cpu())
            return output

        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        handle = self.model.model.layers[layer_index].register_forward_hook(hook)
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
        layer_index: int,
        transform: Callable[[Any], Any] | None,
        *,
        operation: str,
    ) -> dict[str, Any]:
        hook_calls = 0

        def hook(_module: Any, _inputs: Any, output: Any):
            nonlocal hook_calls
            hook_calls += 1
            if transform is None:
                return output
            hidden = output_hidden(output).clone()
            last = hidden[:, -1, :]
            replacement = transform(last.float()).to(device=hidden.device, dtype=hidden.dtype)
            hidden[:, -1, :] = replacement
            return replace_hidden(output, hidden)

        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        handle = self.model.model.layers[layer_index].register_forward_hook(hook)
        try:
            with self.torch.no_grad():
                output = self.model(**inputs)
                logits = output.logits[0, -1].float().detach().cpu()
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
            "layer": layer_index,
            "operation": operation,
            "hook_calls": hook_calls,
            "positive_logit": pos,
            "negative_logit": neg,
            "target_score": pos - neg,
        }
        return {**material, "runtime_receipt_sha256": canonical_sha(material)}


def tensor_from_tuple(torch: Any, values: tuple[float, ...], device: Any) -> Any:
    return torch.tensor(values, dtype=torch.float32, device=device)


def add_transform(vector: Any) -> Callable[[Any], Any]:
    def apply(last: Any) -> Any:
        return last + vector.to(device=last.device, dtype=last.dtype)
    return apply


def lesion_transform(torch: Any, direction: Any) -> Callable[[Any], Any]:
    d = direction / torch.linalg.vector_norm(direction)

    def apply(last: Any) -> Any:
        dd = d.to(device=last.device, dtype=last.dtype)
        projection = (last * dd).sum(dim=-1, keepdim=True)
        return last - projection * dd
    return apply


def rescue_transform(torch: Any, direction: Any, gain: float) -> Callable[[Any], Any]:
    lesion = lesion_transform(torch, direction)
    d = direction / torch.linalg.vector_norm(direction)

    def apply(last: Any) -> Any:
        base = lesion(last)
        return base + float(gain) * d.to(device=last.device, dtype=last.dtype)
    return apply


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--cache-dir", default=os.getenv("HF_HOME") or str(Path.home() / ".cache" / "huggingface"))
    args = ap.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "trigger1_intermediate_contrastive_result.json"
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    source = {"repo_head": git_text("rev-parse", "HEAD"), "repo_tree": git_text("rev-parse", "HEAD^{tree}")}

    try:
        torch, transformers, snapshot, tokenizer, model, device, checkpoint_sha, tokenizer_sha, weight_manifest = runtime_base.load_exact_runtime(Path(args.cache_dir))
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
            direction = tensor_from_tuple(torch, direction_tuple, device)
            directions[layer] = direction
            derivation_receipts[str(layer)] = {
                "layer": layer,
                "positive_prompt_sha256": [hashlib.sha256(p.encode()).hexdigest() for p in DERIVATION_POSITIVE],
                "negative_prompt_sha256": [hashlib.sha256(p.encode()).hexdigest() for p in DERIVATION_NEGATIVE],
                "direction_sha256": runtime_base.tensor_sha(direction),
                "dimension": len(direction_tuple),
                "output_embedding_rows_used": False,
                "holdout_used": False,
            }
            derivation_receipts[str(layer)]["receipt_sha256"] = canonical_sha(derivation_receipts[str(layer)])

        calibration_rows: list[dict[str, Any]] = []
        for layer in layers:
            direction_tuple = tuple(float(x) for x in directions[layer].detach().float().cpu().tolist())
            for gain in GAINS:
                controls = protocol.control_vectors(direction_tuple, gain)
                for case_id, statement in CALIBRATION_CASES:
                    prompt = prompt_for(statement, "A_POS")
                    for control_name in protocol.REQUIRED_CONTROLS:
                        vec = tensor_from_tuple(torch, controls[control_name], device)
                        row = rt.score(prompt, "A_POS", layer, add_transform(vec), operation=control_name)
                        calibration_rows.append({
                            "split": "calibration",
                            "layer": layer,
                            "gain": gain,
                            "case_id": case_id,
                            "control": control_name,
                            "target_score": row["target_score"],
                            "runtime_receipt_sha256": row["runtime_receipt_sha256"],
                        })

        selected = protocol.select_layer_gain(calibration_rows)
        holdout_rows: list[dict[str, Any]] = []
        holdout_runtime_receipts: list[dict[str, Any]] = []
        if selected.get("selected") is True:
            layer = int(selected["layer"])
            gain = float(selected["gain"])
            direction = directions[layer]
            direction_tuple = tuple(float(x) for x in direction.detach().float().cpu().tolist())
            controls = protocol.control_vectors(direction_tuple, gain)
            wrong_layer = next((x for x in layers if x != layer), layer - 1 if layer > 1 else layer + 1)
            for label_map_id in LABEL_MAPS:
                for case_id, statement in HOLDOUT_CASES:
                    prompt = prompt_for(statement, label_map_id)
                    baseline = rt.score(prompt, label_map_id, layer, None, operation="BASELINE_REFERENCE")
                    wrong = rt.score(
                        prompt,
                        label_map_id,
                        wrong_layer,
                        add_transform(direction * gain),
                        operation="WRONG_LAYER_PLUS_VECTOR",
                    )
                    lesion = rt.score(
                        prompt,
                        label_map_id,
                        layer,
                        lesion_transform(torch, direction),
                        operation="LESION",
                    )
                    rescue = rt.score(
                        prompt,
                        label_map_id,
                        layer,
                        rescue_transform(torch, direction, gain),
                        operation="RESCUE",
                    )
                    wrong_delta = wrong["target_score"] - baseline["target_score"]
                    lesion_delta = lesion["target_score"] - baseline["target_score"]
                    rescue_delta = rescue["target_score"] - lesion["target_score"]
                    holdout_runtime_receipts.extend((baseline, wrong, lesion, rescue))
                    for control_name in protocol.REQUIRED_CONTROLS:
                        vec = tensor_from_tuple(torch, controls[control_name], device)
                        obs = rt.score(prompt, label_map_id, layer, add_transform(vec), operation=control_name)
                        holdout_runtime_receipts.append(obs)
                        holdout_rows.append({
                            "split": "holdout",
                            "layer": layer,
                            "gain": gain,
                            "case_id": case_id,
                            "label_map_id": label_map_id,
                            "control": control_name,
                            "target_score": obs["target_score"],
                            "wrong_layer_delta": wrong_delta,
                            "lesion_delta": lesion_delta,
                            "rescue_delta": rescue_delta,
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
            "holdout_runtime_receipts_sha256": canonical_sha(holdout_runtime_receipts),
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
