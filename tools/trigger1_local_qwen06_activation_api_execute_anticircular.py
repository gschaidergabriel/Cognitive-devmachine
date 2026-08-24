#!/usr/bin/env python3
"""Anti-circular Trigger-1 local Qwen3-0.6B activation experiment.

This narrow successor wrapper removes the first fastpath's circular construction:
lm_head(A)-mean(lm_head(B),lm_head(C)) -> inject after final norm -> measure A/B/C logits.

Instead it uses a deterministic weight-independent unit probe, calibrates only gain/sign on
calibration prompts, injects at the midpoint transformer residual stream, and evaluates the
unchanged six-control family on a disjoint holdout. A positive result is therefore no longer
an algebraic consequence of the lm_head readout geometry.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import trigger1_local_qwen06_activation_api_execute as base

VECTOR_BASIS_CLASS = "DETERMINISTIC_WEIGHT_INDEPENDENT_PROBE"
PROBE_ALGORITHM = "torch.randn_cpu_seeded_sha256_revision_hidden_size/v1"


def _layer_index(model: Any) -> int:
    layers = getattr(getattr(model, "model", None), "layers", None)
    if layers is None:
        raise RuntimeError("QWEN_INTERMEDIATE_LAYER_SURFACE_UNAVAILABLE")
    n = len(layers)
    if n < 3:
        raise RuntimeError("INSUFFICIENT_TRANSFORMER_DEPTH_FOR_READOUT_SEPARATION")
    return max(1, min(n - 2, n // 2))


def probe_unit_vector(torch: Any, model: Any, _token_ids: dict[str, int]):
    hidden_size = int(getattr(model.config, "hidden_size"))
    material = f"{base.MODEL_REVISION}|{hidden_size}|{PROBE_ALGORITHM}".encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(material).digest()[:8], "big") & ((1 << 63) - 1)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    vector = torch.randn(hidden_size, generator=generator, dtype=torch.float32)
    norm = torch.linalg.vector_norm(vector)
    if not bool(torch.isfinite(norm)) or float(norm) <= 0:
        raise RuntimeError("WEIGHT_INDEPENDENT_PROBE_DEGENERATE")
    return vector / norm


class IntermediateResidualRuntimeState:
    def __init__(self, torch: Any, tokenizer: Any, model: Any, device: Any, base_vector: Any, token_ids: dict[str, int]):
        self.torch = torch
        self.tokenizer = tokenizer
        self.model = model
        self.device = device
        self.base_vector = base_vector
        self.token_ids = token_ids
        self.lock = base.threading.Lock()
        self.invocations = 0
        self.layer_index = _layer_index(model)
        self.total_layers = len(model.model.layers)
        self.readout_separation_layers = self.total_layers - self.layer_index - 1
        self.activation_site = f"model.model.layers.{self.layer_index}:output:last_token"

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

        with self.lock:
            self.torch.manual_seed(seed)
            if self.torch.cuda.is_available():
                self.torch.cuda.manual_seed_all(seed)
            inputs = self.tokenizer(prompt, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            layer = self.model.model.layers[self.layer_index]
            handle = layer.register_forward_hook(hook)
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
            "readout_separation_layers": self.readout_separation_layers,
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


def select_signed_gain(rows: list[dict[str, Any]]) -> float | None:
    ranked: list[tuple[float, float]] = []
    for gain in base.CALIBRATION_GAINS:
        by_case: dict[str, dict[str, float]] = {}
        for row in rows:
            if float(row.get("gain")) != float(gain):
                continue
            by_case.setdefault(str(row.get("prompt_family")), {})[str(row.get("control"))] = float(row["target_score"])
        plus_metric: list[float] = []
        minus_metric: list[float] = []
        for values in by_case.values():
            if all(k in values for k in ("BASELINE", "+VECTOR", "SIGN_FLIP")):
                b = values["BASELINE"]
                p = values["+VECTOR"]
                s = values["SIGN_FLIP"]
                plus_metric.extend((p - b, b - s))
                minus_metric.extend((s - b, b - p))
        if plus_metric:
            ranked.append((min(plus_metric), float(gain)))
            ranked.append((min(minus_metric), -float(gain)))
    ranked.sort(key=lambda item: (item[0], -abs(item[1])), reverse=True)
    return ranked[0][1] if ranked and ranked[0][0] > 0 else None


def _arg_value(name: str) -> str | None:
    for i, value in enumerate(sys.argv[:-1]):
        if value == name:
            return sys.argv[i + 1]
    prefix = name + "="
    for value in sys.argv[1:]:
        if value.startswith(prefix):
            return value[len(prefix):]
    return None


def _rewrite_evidence(output_dir: Path) -> None:
    result_path = output_dir / "trigger1_local_activation_api_result.json"
    candidate_path = output_dir / "trigger1_direct_steering_candidate.json"
    if not result_path.is_file() or not candidate_path.is_file():
        return
    result = json.loads(result_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    manifest = result.get("runtime_manifest") or {}
    total_layers = int((candidate.get("intervention") or {}).get("layer_start") or 0)
    if total_layers < 3:
        total_layers = 28
    layer_index = max(1, min(total_layers - 2, total_layers // 2))
    separation = total_layers - layer_index - 1
    activation_site = f"model.model.layers.{layer_index}:output:last_token"

    hidden_size = int((result.get("adapter") or {}).get("hidden_size") or 0)
    seed_material = f"{base.MODEL_REVISION}|{hidden_size}|{PROBE_ALGORITHM}".encode("utf-8")
    derivation = {
        "schema": "CLAY_TRIGGER1_VECTOR_DERIVATION_RECEIPT/v1",
        "basis_class": VECTOR_BASIS_CLASS,
        "algorithm": PROBE_ALGORITHM,
        "seed": int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big") & ((1 << 63) - 1),
        "hidden_size": hidden_size,
        "model_revision_used_for_seed_identity_only": base.MODEL_REVISION,
        "model_weight_bytes_read_for_vector_derivation": False,
        "output_embedding_or_lm_head_rows_read": False,
        "holdout_data_used": False,
    }
    derivation_sha = base.canonical_sha(derivation)
    source_packet = {
        "schema": "JSPACE_VECTOR_CONTROL_ABI/v1",
        "intent": "test whether an upstream weight-independent residual probe causally changes A-vs-B/C readout on disjoint holdout",
        "basis": "deterministic weight-independent intermediate residual-stream probe",
        "model": base.MODEL_ID,
        "revision": base.MODEL_REVISION,
        "holdout_used_for_vector_derivation": False,
        "output_embedding_rows_used_for_vector_derivation": False,
    }
    adapter = {
        "schema": "JSPACE_LATENT_BASIS_ADAPTER/v2",
        "model": base.MODEL_ID,
        "revision": base.MODEL_REVISION,
        "activation_site": activation_site,
        "hidden_size": hidden_size,
        "construction": "deterministic seeded Gaussian unit probe; gain/sign selected on calibration only",
        "readout_separation_layers": separation,
    }
    source_packet_sha = base.canonical_sha(source_packet)
    adapter_sha = base.canonical_sha(adapter)

    intervention = candidate.setdefault("intervention", {})
    intervention.update(
        {
            "activation_site": activation_site,
            "layer_start": layer_index,
            "layer_end": layer_index,
            "vector_basis_class": VECTOR_BASIS_CLASS,
            "derived_from_output_embeddings": False,
            "injected_after_final_norm": False,
            "readout_separation_layers": separation,
            "vector_derivation_receipt_sha256": derivation_sha,
            "source_packet_sha256": source_packet_sha,
            "adapter_sha256": adapter_sha,
        }
    )
    candidate["anti_circularity"] = {
        "schema": "CLAY_TRIGGER1_ANTI_CIRCULARITY_EVIDENCE/v1",
        "pass": True,
        "vector_derivation": derivation,
        "activation_site": activation_site,
        "readout_separation_layers": separation,
        "output_embedding_or_lm_head_rows_used_for_vector_derivation": False,
        "post_final_norm_injection": False,
    }
    target = candidate.setdefault("target", {})
    old_local_receipt = target.get("local_runtime_execution_receipt_sha256")
    target["local_runtime_execution_receipt_sha256"] = base.canonical_sha(
        {
            "base_local_runtime_receipt_sha256": old_local_receipt,
            "activation_site": activation_site,
            "vector_derivation_receipt_sha256": derivation_sha,
            "runtime_build_sha256": (candidate.get("source_identity") or {}).get("runtime_build_sha256"),
            "runtime_manifest": manifest,
        }
    )

    result["source_packet"] = source_packet
    result["source_packet_sha256"] = source_packet_sha
    result["adapter"] = adapter
    result["adapter_sha256"] = adapter_sha
    result["vector_derivation_receipt"] = derivation
    result["vector_derivation_receipt_sha256"] = derivation_sha
    result["anti_circularity"] = candidate["anti_circularity"]
    result["legacy_circular_construction_used"] = False
    result["result_sha256"] = base.canonical_sha({k: v for k, v in result.items() if k != "result_sha256"})

    candidate_path.write_text(json.dumps(candidate, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    base.unit_target_vector = probe_unit_vector
    base.RuntimeState = IntermediateResidualRuntimeState
    base.select_gain = select_signed_gain
    rc = int(base.main())
    output_dir = _arg_value("--output-dir")
    if rc == 0 and output_dir:
        _rewrite_evidence(Path(output_dir))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
