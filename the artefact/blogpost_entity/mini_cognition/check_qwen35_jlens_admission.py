#!/usr/bin/env python3
"""Offline-first Qwen3.5-0.8B -> Anthropic Jacobian Lens admission gate.

This gate deliberately separates three claims:

1. CONFIG/LAYOUT: can the exact local Qwen3.5 config construct a text-only
   ``AutoModelForCausalLM`` whose residual stack is accepted by jlens.from_hf?
2. FORWARD: can the exact weighted text backbone run through the official
   HFLensModel path with both Qwen3.5 hybrid layer classes present?
3. JACOBIAN: can one bounded ``jacobian_for_prompt`` complete and produce the
   expected fp32 [d_model, d_model] matrix for one source layer?

Passing an earlier phase never promotes a later phase.  This script is not a
lens fit, a GWT calibration, a truth test, or whole Mini Entity acceptance.
Network access is OFF unless ``--allow-network`` is supplied explicitly.
Weighted phases require a hashed local model tree so their receipts bind exact
checkpoint/tokenizer/config bytes rather than only a mutable model reference.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from collections import Counter
from pathlib import Path
from typing import Any


EXPECTED_MODEL_TYPE = "qwen3_5"
EXPECTED_LAYERS = 24
EXPECTED_D_MODEL = 1024


def _version(dist: str) -> str:
    try:
        return importlib.metadata.version(dist)
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _tree_manifest_digest(root: Path) -> tuple[str, list[dict[str, Any]]]:
    """Hash exact ordinary files under a local model directory.

    The aggregate digest binds relative path, size and per-file SHA-256.  It is
    intentionally generic: it records the bytes actually supplied to this gate
    instead of trusting a model/provider label.
    """

    if not root.is_dir():
        raise ValueError("identity hashing requires --model to be a local directory")
    rows: list[dict[str, Any]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        digest = _sha256_file(path)
        rows.append({"path": rel, "bytes": path.stat().st_size, "sha256": digest})
    agg = hashlib.sha256()
    for row in rows:
        agg.update(
            (f"{row['path']}\0{row['bytes']}\0{row['sha256']}\n").encode("utf-8")
        )
    return agg.hexdigest(), rows


def _write_result(result: dict[str, Any], output: str | None) -> None:
    payload = json.dumps(result, indent=2, sort_keys=True)
    print(payload)
    if output:
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_name(f".{out.name}.tmp.{os.getpid()}")
        tmp.write_text(payload + "\n", encoding="utf-8")
        os.replace(tmp, out)


def _base_receipt(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "schema": "mini-entity/qwen35-jlens-admission/v1",
        "phase": args.phase,
        "model_ref": args.model,
        "network_allowed": bool(args.allow_network),
        "expected": {
            "model_type": args.expected_model_type,
            "layers": args.expected_layers,
            "d_model": args.expected_d_model,
            "preferred_text_only_jlens_layout": "model",
        },
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "torch": _version("torch"),
            "transformers": _version("transformers"),
            "jlens": _version("jlens"),
        },
        "authority": {
            "runtime_credit_scope": "ONLY_EXACT_PHASE_OBSERVED",
            "exact_model_bytes_bound": bool(args.hash_local_tree),
            "jspace_measurement_is_truth": False,
            "model_output_is_canonical_truth": False,
            "whole_gwt_pass": False,
        },
        "status": "STARTED",
    }


def _load_config_and_meta_model(args: argparse.Namespace):
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM

    config = AutoConfig.from_pretrained(
        args.model,
        local_files_only=not args.allow_network,
        trust_remote_code=args.trust_remote_code,
    )
    text_config = config.get_text_config() if hasattr(config, "get_text_config") else config
    if getattr(text_config, "model_type", None) != args.expected_model_type:
        raise AssertionError(
            f"model_type mismatch: {getattr(text_config, 'model_type', None)!r} "
            f"!= {args.expected_model_type!r}"
        )
    if int(text_config.num_hidden_layers) != args.expected_layers:
        raise AssertionError(
            f"num_hidden_layers={text_config.num_hidden_layers} != {args.expected_layers}"
        )
    if int(text_config.hidden_size) != args.expected_d_model:
        raise AssertionError(
            f"hidden_size={text_config.hidden_size} != {args.expected_d_model}"
        )

    # Meta construction checks class/layout without allocating checkpoint weights.
    with torch.device("meta"):
        model = AutoModelForCausalLM.from_config(
            config, trust_remote_code=args.trust_remote_code
        )
    return config, text_config, model


def _layout_phase(args: argparse.Namespace, result: dict[str, Any]) -> None:
    from jlens import from_hf

    class _TokenizerStub:
        bos_token_id = None
        add_bos_token = False

    config, text_config, model = _load_config_and_meta_model(args)
    lens_model = from_hf(model, _TokenizerStub(), compile=False, force_bos=False)

    if lens_model.layout.path != args.expected_layout:
        raise AssertionError(
            f"jlens layout={lens_model.layout.path!r} != {args.expected_layout!r}"
        )
    if lens_model.n_layers != args.expected_layers:
        raise AssertionError(
            f"jlens n_layers={lens_model.n_layers} != {args.expected_layers}"
        )
    if lens_model.d_model != args.expected_d_model:
        raise AssertionError(
            f"jlens d_model={lens_model.d_model} != {args.expected_d_model}"
        )

    layer_types = list(getattr(text_config, "layer_types", []) or [])
    counts = Counter(str(x) for x in layer_types)
    if layer_types and len(layer_types) != args.expected_layers:
        raise AssertionError(
            f"len(layer_types)={len(layer_types)} != {args.expected_layers}"
        )
    if args.require_hybrid_layers and layer_types:
        if counts.get("linear_attention", 0) == 0 or counts.get("full_attention", 0) == 0:
            raise AssertionError(f"hybrid layer types not both present: {dict(counts)}")

    result["observed"] = {
        "config_class": type(config).__name__,
        "text_config_class": type(text_config).__name__,
        "model_class": type(model).__name__,
        "jlens_layout": lens_model.layout.path,
        "n_layers": lens_model.n_layers,
        "d_model": lens_model.d_model,
        "layer_type_counts": dict(sorted(counts.items())),
        "model_parameters_device_class": "meta",
    }
    result["status"] = "PASS_LAYOUT_SOURCE_RUNTIME"
    result["next_gate"] = "FORWARD_WEIGHTED_EXACT_BYTES"


def _load_weighted(args: argparse.Namespace):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        local_files_only=not args.allow_network,
        trust_remote_code=args.trust_remote_code,
    )
    kwargs: dict[str, Any] = {
        "local_files_only": not args.allow_network,
        "trust_remote_code": args.trust_remote_code,
        "dtype": args.dtype,
    }
    if args.device_map:
        kwargs["device_map"] = args.device_map
    model = AutoModelForCausalLM.from_pretrained(args.model, **kwargs)
    model.eval()
    return torch, tokenizer, model


def _weighted_lens(args: argparse.Namespace):
    from jlens import from_hf

    torch, tokenizer, model = _load_weighted(args)
    if args.compile and args.device_map == "auto":
        raise ValueError("jlens compile=True must not be combined with device_map='auto'")
    lens_model = from_hf(
        model,
        tokenizer,
        compile=args.compile,
        force_bos=not args.no_force_bos,
    )
    if lens_model.layout.path != args.expected_layout:
        raise AssertionError(
            f"weighted jlens layout={lens_model.layout.path!r} != {args.expected_layout!r}"
        )
    if lens_model.n_layers != args.expected_layers or lens_model.d_model != args.expected_d_model:
        raise AssertionError(
            f"weighted dimensions mismatch: layers={lens_model.n_layers}, d={lens_model.d_model}"
        )
    return torch, tokenizer, model, lens_model


def _forward_phase(args: argparse.Namespace, result: dict[str, Any]) -> None:
    from jlens import ActivationRecorder

    torch, tokenizer, model, lens_model = _weighted_lens(args)
    ids = lens_model.encode(args.prompt, max_length=args.max_seq_len)
    with ActivationRecorder(lens_model.layers, at=list(range(lens_model.n_layers))) as rec:
        with torch.no_grad():
            lens_model.forward(ids)

    seen = sorted(rec.activations)
    if seen != list(range(args.expected_layers)):
        raise AssertionError(f"activation coverage mismatch: saw {seen}")
    shapes = {str(i): list(rec.activations[i].shape) for i in seen}
    for i, shape in ((i, shapes[str(i)]) for i in seen):
        if not shape or shape[-1] != args.expected_d_model:
            raise AssertionError(f"layer {i} activation shape mismatch: {shape}")

    text_config = model.config.get_text_config()
    layer_types = list(getattr(text_config, "layer_types", []) or [])
    result["observed"] = {
        "model_class": type(model).__name__,
        "jlens_layout": lens_model.layout.path,
        "input_tokens": int(ids.shape[1]),
        "activation_layers_seen": len(seen),
        "activation_shapes": shapes,
        "layer_type_counts": dict(sorted(Counter(str(x) for x in layer_types).items())),
        "input_device": str(lens_model.input_device),
    }
    result["status"] = "PASS_WEIGHTED_FORWARD_HOOKS"
    result["next_gate"] = "BOUNDED_JACOBIAN_ONE_SOURCE_LAYER"


def _jacobian_phase(args: argparse.Namespace, result: dict[str, Any]) -> None:
    from jlens import jacobian_for_prompt

    torch, tokenizer, model, lens_model = _weighted_lens(args)
    source_layers = [args.source_layer]
    jacobians, seq_len, n_valid = jacobian_for_prompt(
        lens_model,
        args.prompt,
        source_layers=source_layers,
        target_layer=args.target_layer,
        dim_batch=args.dim_batch,
        max_seq_len=args.max_seq_len,
        skip_first=args.skip_first,
    )
    j = jacobians[args.source_layer]
    expected_shape = [args.expected_d_model, args.expected_d_model]
    if list(j.shape) != expected_shape:
        raise AssertionError(f"jacobian shape={list(j.shape)} != {expected_shape}")
    if j.dtype != torch.float32 or j.device.type != "cpu":
        raise AssertionError(f"jacobian storage mismatch: dtype={j.dtype}, device={j.device}")
    if not torch.isfinite(j).all():
        raise AssertionError("jacobian contains non-finite values")

    result["observed"] = {
        "model_class": type(model).__name__,
        "jlens_layout": lens_model.layout.path,
        "source_layer": args.source_layer,
        "target_layer": args.target_layer if args.target_layer is not None else "FINAL",
        "seq_len": seq_len,
        "valid_positions": n_valid,
        "jacobian_shape": list(j.shape),
        "jacobian_dtype": str(j.dtype),
        "jacobian_device": str(j.device),
        "jacobian_abs_mean": float(j.abs().mean()),
        "jacobian_abs_max": float(j.abs().max()),
        "jacobian_finite": True,
    }
    result["status"] = "PASS_BOUNDED_JACOBIAN"
    result["next_gate"] = "VERSIONED_MULTI_PROMPT_LENS_FIT_AND_EMPIRICAL_GWT_CALIBRATION"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="Qwen/Qwen3.5-0.8B")
    p.add_argument("--phase", choices=("layout", "forward", "jacobian"), default="layout")
    p.add_argument("--allow-network", action="store_true")
    p.add_argument("--trust-remote-code", action="store_true")
    p.add_argument("--hash-local-tree", action="store_true")
    p.add_argument("--output")
    p.add_argument("--expected-model-type", default=EXPECTED_MODEL_TYPE)
    p.add_argument("--expected-layers", type=int, default=EXPECTED_LAYERS)
    p.add_argument("--expected-d-model", type=int, default=EXPECTED_D_MODEL)
    p.add_argument("--expected-layout", default="model")
    p.add_argument("--require-hybrid-layers", action="store_true", default=True)
    p.add_argument("--no-require-hybrid-layers", dest="require_hybrid_layers", action="store_false")
    p.add_argument("--prompt", default="A careful system distinguishes observation from inference and tests alternatives before acting.")
    p.add_argument("--max-seq-len", type=int, default=64)
    p.add_argument("--source-layer", type=int, default=0)
    p.add_argument("--target-layer", type=int)
    p.add_argument("--dim-batch", type=int, default=1)
    p.add_argument("--skip-first", type=int, default=1)
    p.add_argument("--dtype", default="auto")
    p.add_argument("--device-map")
    p.add_argument("--compile", action="store_true")
    p.add_argument("--no-force-bos", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    result = _base_receipt(args)
    try:
        if args.phase in {"forward", "jacobian"} and not args.hash_local_tree:
            raise ValueError("EXACT_WEIGHTED_PHASE_REQUIRES_HASHED_LOCAL_MODEL_TREE")

        if args.hash_local_tree:
            root = Path(args.model).expanduser().resolve()
            digest, rows = _tree_manifest_digest(root)
            result["local_artifact_identity"] = {
                "root": str(root),
                "tree_manifest_sha256": digest,
                "files": rows,
            }

        if args.phase == "layout":
            _layout_phase(args, result)
        elif args.phase == "forward":
            _forward_phase(args, result)
        else:
            _jacobian_phase(args, result)
    except Exception as exc:  # fail closed with machine-readable evidence
        result["status"] = "FAIL"
        result["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        _write_result(result, args.output)
        return 1

    _write_result(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
