#!/usr/bin/env python3
"""Offline-only model-specific activation intervention probe for EntityOS/HCU.

This executable source bridges HCU_JSPACE_LOCAL_INTERVENTION_BACKEND_GATE_V1.md to a
minimal Hugging Face/PyTorch local experiment. It deliberately grants NO canonical,
whole-HCU, J-Space-model, or training credit by itself. The emitted record is candidate
runtime evidence that still requires canonical admission/review.

No model download is permitted: the model argument must be a local directory and
Transformers/Hugging Face offline modes are forced before those libraries are imported.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
from typing import Any, Iterator

# Fail closed before importing model libraries.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

SCHEMA = "ENTITYOS_HCU_JSPACE_LOCAL_ACTIVATION_PROBE/v1"
CLASSIFICATION = "LOCAL_MODEL_SPECIFIC_CAUSAL_CANDIDATE_EVIDENCE_ONLY"


class ProbeRejected(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_identity(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise ProbeRejected("LOCAL_MODEL_DIRECTORY_REQUIRED")
    rows: list[dict[str, Any]] = []
    combined = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        digest = sha256_file(path)
        size = path.stat().st_size
        rows.append({"path": rel, "size": size, "sha256": digest})
        combined.update(rel.encode("utf-8") + b"\0")
        combined.update(str(size).encode("ascii") + b"\0")
        combined.update(digest.encode("ascii") + b"\n")
    if not rows:
        raise ProbeRejected("LOCAL_MODEL_DIRECTORY_EMPTY")
    return {"tree_sha256": combined.hexdigest(), "files": rows}


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def tensor_digest(tensor: Any) -> str:
    data = tensor.detach().to(dtype=tensor.new_zeros((), dtype=None).dtype if False else None)
    # Convert explicitly to float32 CPU bytes so device/dtype do not change digest encoding.
    data = tensor.detach().to(dtype=__import__("torch").float32, device="cpu").contiguous()
    return hashlib.sha256(data.numpy().tobytes(order="C")).hexdigest()


def in_memory_parameter_identity(model: Any) -> dict[str, Any]:
    """Hash post-load parameter values. This is NOT loader-consumed source-byte attestation."""
    h = hashlib.sha256()
    count = 0
    elements = 0
    for name, param in model.named_parameters():
        raw = param.detach().to(device="cpu").contiguous()
        h.update(name.encode("utf-8") + b"\0")
        h.update(str(tuple(raw.shape)).encode("ascii") + b"\0")
        h.update(str(raw.dtype).encode("ascii") + b"\0")
        h.update(raw.view(__import__("torch").uint8).numpy().tobytes(order="C"))
        count += 1
        elements += raw.numel()
    return {
        "post_load_parameter_sha256": h.hexdigest(),
        "parameter_tensors": count,
        "parameter_elements": elements,
        "loader_consumption_attestation": False,
        "note": "Post-load parameter values are observed; exact source-byte consumption by the loader is not proven.",
    }


class NetworkFence:
    def __init__(self) -> None:
        self.attempts = 0
        self._connect = socket.socket.connect
        self._create_connection = socket.create_connection

    def _blocked_connect(self, *args: Any, **kwargs: Any) -> Any:
        self.attempts += 1
        raise ProbeRejected("NETWORK_ATTEMPT_BLOCKED_OFFLINE_ONLY")

    def _blocked_create_connection(self, *args: Any, **kwargs: Any) -> Any:
        self.attempts += 1
        raise ProbeRejected("NETWORK_ATTEMPT_BLOCKED_OFFLINE_ONLY")

    def __enter__(self) -> "NetworkFence":
        socket.socket.connect = self._blocked_connect  # type: ignore[assignment]
        socket.create_connection = self._blocked_create_connection  # type: ignore[assignment]
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        socket.socket.connect = self._connect  # type: ignore[assignment]
        socket.create_connection = self._create_connection  # type: ignore[assignment]


def resolve_layers(model: Any) -> Any:
    candidates = (
        ("model", "layers"),
        ("model", "decoder", "layers"),
        ("transformer", "h"),
        ("gpt_neox", "layers"),
    )
    for chain in candidates:
        node = model
        try:
            for name in chain:
                node = getattr(node, name)
            if len(node) > 0:
                return node
        except (AttributeError, TypeError):
            continue
    raise ProbeRejected("SUPPORTED_TRANSFORMER_LAYER_STACK_NOT_FOUND")


def normalize_position(position: int, length: int) -> int:
    resolved = position if position >= 0 else length + position
    if resolved < 0 or resolved >= length:
        raise ProbeRejected(f"POSITION_OUT_OF_RANGE:{position}:{length}")
    return resolved


def output_hidden(output: Any) -> Any:
    if hasattr(output, "shape"):
        return output
    if isinstance(output, (tuple, list)) and output and hasattr(output[0], "shape"):
        return output[0]
    raise ProbeRejected("LAYER_OUTPUT_HIDDEN_TENSOR_NOT_FOUND")


def replace_hidden(output: Any, replacement: Any) -> Any:
    if hasattr(output, "shape"):
        return replacement
    if isinstance(output, tuple):
        return (replacement, *output[1:])
    if isinstance(output, list):
        return [replacement, *output[1:]]
    raise ProbeRejected("LAYER_OUTPUT_REPLACEMENT_UNSUPPORTED")


def token_id(tokenizer: Any, text: str, label: str) -> int:
    ids = tokenizer.encode(text, add_special_tokens=False)
    if not ids:
        raise ProbeRejected(f"{label}_TOKEN_REQUIRED")
    return int(ids[-1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Local HF-compatible model snapshot directory")
    parser.add_argument("--clean", required=True)
    parser.add_argument("--corrupted", required=True)
    parser.add_argument("--target-text", required=True, help="Metric token/text; final encoded token is used")
    parser.add_argument("--off-target-text", required=True, help="Unrelated metric token/text")
    parser.add_argument("--layer", type=int, required=True)
    parser.add_argument("--position", type=int, default=-1)
    parser.add_argument("--off-target-position", type=int)
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda", "mps"))
    parser.add_argument("--generation", required=True)
    parser.add_argument("--causal-event-id", required=True)
    parser.add_argument("--admission-id", required=True)
    parser.add_argument("--route-id", required=True)
    parser.add_argument("--inference-receipt-id", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    observed_at = dt.datetime.now(dt.timezone.utc).isoformat()
    model_path = Path(args.model).expanduser().resolve()
    source_identity = tree_identity(model_path)
    network = NetworkFence()

    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "observed_at": observed_at,
        "classification": CLASSIFICATION,
        "authority_epoch": "RESOLVE_FROM_CURRENT_CANONICAL_STATE_AT_ADMISSION",
        "program": "ENTITYOS_HCU",
        "product": "EntityOS",
        "architecture": "HCU",
        "mode": "FREE_ONLY_LOCAL_OFFLINE",
        "source_git_head": git_head(),
        "probe_source_sha256": sha256_file(Path(__file__).resolve()),
        "causal_binding": {
            "generation": args.generation,
            "causal_event_id": args.causal_event_id,
            "admission_id": args.admission_id,
            "route_id": args.route_id,
            "inference_receipt_id": args.inference_receipt_id,
        },
        "model_source_identity": source_identity,
        "network_attempt_count": 0,
        "credit": {
            "entityos_hcu_whole_runtime": 0,
            "hcu_full_runtime": 0,
            "jspace_model_runtime": 0,
            "training": 0,
            "whole_product_pass": False,
        },
    }

    try:
        with network:
            import torch
            import transformers
            from transformers import AutoModelForCausalLM, AutoTokenizer

            torch.manual_seed(0)
            if hasattr(torch, "use_deterministic_algorithms"):
                torch.use_deterministic_algorithms(True, warn_only=True)

            if args.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = args.device

            tokenizer = AutoTokenizer.from_pretrained(
                str(model_path), local_files_only=True, trust_remote_code=False
            )
            model = AutoModelForCausalLM.from_pretrained(
                str(model_path), local_files_only=True, trust_remote_code=False, torch_dtype="auto"
            )
            model.eval()
            model.to(device)
            layers = resolve_layers(model)
            layer_index = args.layer if args.layer >= 0 else len(layers) + args.layer
            if layer_index < 0 or layer_index >= len(layers):
                raise ProbeRejected(f"LAYER_OUT_OF_RANGE:{args.layer}:{len(layers)}")
            layer = layers[layer_index]

            clean_inputs = tokenizer(args.clean, return_tensors="pt", add_special_tokens=True)
            corrupt_inputs = tokenizer(args.corrupted, return_tensors="pt", add_special_tokens=True)
            clean_ids = clean_inputs["input_ids"]
            corrupt_ids = corrupt_inputs["input_ids"]
            if clean_ids.shape != corrupt_ids.shape:
                raise ProbeRejected(
                    f"CLEAN_CORRUPTED_TOKEN_SHAPE_MISMATCH:{tuple(clean_ids.shape)}:{tuple(corrupt_ids.shape)}"
                )
            seq_len = int(clean_ids.shape[1])
            patch_pos = normalize_position(args.position, seq_len)
            off_pos = (
                normalize_position(args.off_target_position, seq_len)
                if args.off_target_position is not None
                else (patch_pos - 1 if patch_pos > 0 else patch_pos + 1)
            )
            if off_pos == patch_pos or off_pos < 0 or off_pos >= seq_len:
                raise ProbeRejected("DISTINCT_OFF_TARGET_POSITION_REQUIRED")

            target_id = token_id(tokenizer, args.target_text, "TARGET")
            off_target_id = token_id(tokenizer, args.off_target_text, "OFF_TARGET")

            def to_device(inputs: Any) -> dict[str, Any]:
                return {k: v.to(device) for k, v in inputs.items()}

            def run_condition(
                label: str,
                inputs: dict[str, Any],
                *,
                reference: Any | None = None,
                intervention_position: int | None = None,
            ) -> tuple[dict[str, Any], Any]:
                capture: dict[str, Any] = {}

                def hook(_module: Any, _inputs: Any, output: Any) -> Any:
                    hidden = output_hidden(output)
                    pos = patch_pos if intervention_position is None else intervention_position
                    before = hidden[0, pos, :].detach().clone()
                    capture["activation_before_sha256"] = tensor_digest(before)
                    capture["activation_shape"] = list(before.shape)
                    capture["activation_dtype"] = str(before.dtype)
                    capture["activation_position"] = pos
                    capture["reference_vector"] = before
                    if reference is None:
                        capture["activation_after_sha256"] = capture["activation_before_sha256"]
                        return output
                    replacement = hidden.clone()
                    replacement[:, pos, :] = reference.to(device=hidden.device, dtype=hidden.dtype)
                    after = replacement[0, pos, :].detach().clone()
                    capture["activation_after_sha256"] = tensor_digest(after)
                    return replace_hidden(output, replacement)

                handle = layer.register_forward_hook(hook)
                try:
                    with torch.no_grad():
                        result = model(**inputs, use_cache=False)
                finally:
                    handle.remove()
                logits = result.logits[:, -1, :].detach()
                record = {
                    "condition": label,
                    "model_execution_id": hashlib.sha256(
                        f"{args.causal_event_id}|{args.admission_id}|{args.route_id}|{label}".encode()
                    ).hexdigest(),
                    "jspace_trace_id": hashlib.sha256(
                        f"{args.inference_receipt_id}|{layer_index}|{capture['activation_position']}|{label}".encode()
                    ).hexdigest(),
                    "layer": layer_index,
                    "activation_site": f"decoder_layer:{layer_index}:position:{capture['activation_position']}",
                    "activation_before_sha256": capture["activation_before_sha256"],
                    "activation_after_sha256": capture["activation_after_sha256"],
                    "activation_shape": capture["activation_shape"],
                    "activation_dtype": capture["activation_dtype"],
                    "final_logits_sha256": tensor_digest(logits),
                    "target_token_id": target_id,
                    "target_logit": float(logits[0, target_id].item()),
                    "off_target_token_id": off_target_id,
                    "off_target_logit": float(logits[0, off_target_id].item()),
                    "field_classification": "OBSERVED_RUNTIME_MEASUREMENT",
                }
                return record, capture["reference_vector"]

            clean_record, clean_reference = run_condition(
                "BASELINE_CLEAN", to_device(clean_inputs)
            )
            corrupt_record, corrupt_reference = run_condition(
                "BASELINE_CORRUPTED", to_device(corrupt_inputs)
            )
            target_record, _ = run_condition(
                "INTERVENTION_TARGET",
                to_device(corrupt_inputs),
                reference=clean_reference,
                intervention_position=patch_pos,
            )
            sham_record, _ = run_condition(
                "SHAM_CONTROL",
                to_device(corrupt_inputs),
                reference=corrupt_reference,
                intervention_position=patch_pos,
            )
            off_record, _ = run_condition(
                "OFF_TARGET_CONTROL",
                to_device(corrupt_inputs),
                reference=clean_reference,
                intervention_position=off_pos,
            )

            receipt.update(
                {
                    "runtime": {
                        "python": platform.python_version(),
                        "torch": torch.__version__,
                        "transformers": transformers.__version__,
                        "device": device,
                        "model_class": type(model).__name__,
                        "tokenizer_class": type(tokenizer).__name__,
                        "layers": len(layers),
                    },
                    "post_load_identity": in_memory_parameter_identity(model),
                    "probe": {
                        "layer": layer_index,
                        "target_position": patch_pos,
                        "off_target_position": off_pos,
                        "clean_token_ids_sha256": tensor_digest(clean_ids),
                        "corrupted_token_ids_sha256": tensor_digest(corrupt_ids),
                        "conditions": [
                            clean_record,
                            corrupt_record,
                            target_record,
                            sham_record,
                            off_record,
                        ],
                        "derived_metrics": {
                            "target_patch_effect_on_target_logit": target_record["target_logit"] - corrupt_record["target_logit"],
                            "sham_effect_on_target_logit": sham_record["target_logit"] - corrupt_record["target_logit"],
                            "off_target_patch_effect_on_target_logit": off_record["target_logit"] - corrupt_record["target_logit"],
                            "target_patch_effect_on_off_target_logit": target_record["off_target_logit"] - corrupt_record["off_target_logit"],
                        },
                    },
                    "promotion": {
                        "status": "UNASSESSED_CANDIDATE_ONLY",
                        "reason": "No predeclared effect/off-target threshold or canonical admission is evaluated by this probe.",
                    },
                }
            )
    except ProbeRejected as exc:
        receipt["failure"] = {"class": "PROBE_REJECTED_FAIL_CLOSED", "detail": str(exc)}
        receipt["promotion"] = {"status": "REJECTED_NO_CREDIT"}
    except Exception as exc:  # Runtime/dependency failure is not scientific negative evidence.
        receipt["failure"] = {
            "class": "RUNTIME_OR_DEPENDENCY_FAILURE_NOT_SCIENTIFIC_NEGATIVE",
            "type": type(exc).__name__,
            "detail": str(exc),
        }
        receipt["promotion"] = {"status": "FAILED_NO_CREDIT"}
    finally:
        receipt["network_attempt_count"] = network.attempts

    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if "failure" not in receipt else 4


if __name__ == "__main__":
    raise SystemExit(main())
