#!/usr/bin/env python3
"""Fail-closed verifier for JSPACE_GWT_BOOT_BINDING_RECEIPT/v1.

This module binds exact source/model/lens/workspace/control identities before any
J-Space/GWT runtime credit is admissible. Structural success is not model-quality,
semantic-correctness, Claude-adapter, or whole-product PASS.
"""
from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any

SCHEMA = "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1"
SEMANTIC_DIGEST_METHOD = "ordered-fp32-finite-v1"
SEMANTIC_DIGEST_DOMAIN = b"CLAY/JSPACE_LENS_SEMANTIC/ordered-fp32-finite-v1\x00"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GITSHA = re.compile(r"^[0-9a-f]{40}$")
_JSPACE_MODES = {
    "FULL_LOCAL_LATENT",
    "LOCAL_OBSERVE_ONLY",
    "COMPILED_EXTERNAL",
    "PLAIN_COMPATIBILITY",
}
_ACTION_ORIGINS = {
    "zero",
    "hook",
    "timer",
    "claude_code",
    "sandbox_controller",
    "proxy",
    "other",
}


class ReceiptError(ValueError):
    pass


def _require_obj(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ReceiptError(f"MISSING_OBJECT:{key}")
    return value


def _require_str(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReceiptError(f"MISSING_STRING:{key}")
    return value


def _require_sha256(parent: dict[str, Any], key: str) -> str:
    value = _require_str(parent, key)
    if not _SHA256.fullmatch(value):
        raise ReceiptError(f"BAD_SHA256:{key}")
    return value


def _require_gitsha(parent: dict[str, Any], key: str) -> str:
    value = _require_str(parent, key)
    if not _GITSHA.fullmatch(value):
        raise ReceiptError(f"BAD_GITSHA:{key}")
    return value


def _require_bool(parent: dict[str, Any], key: str) -> bool:
    value = parent.get(key)
    if type(value) is not bool:
        raise ReceiptError(f"MISSING_BOOL:{key}")
    return value


def _require_nonnegative_int(parent: dict[str, Any], key: str) -> int:
    value = parent.get(key)
    if type(value) is not int or value < 0:
        raise ReceiptError(f"BAD_INT:{key}")
    return value


def _require_positive_int(parent: dict[str, Any], key: str) -> int:
    value = _require_nonnegative_int(parent, key)
    if value == 0:
        raise ReceiptError(f"ZERO_INT:{key}")
    return value


def _sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_source_layers(value: Any) -> list[int]:
    if (
        not isinstance(value, list)
        or not value
        or any(type(item) is not int or item < 0 for item in value)
    ):
        raise ReceiptError("BAD_SOURCE_LAYERS")
    if value != sorted(set(value)):
        raise ReceiptError("SOURCE_LAYERS_NOT_CANONICAL")
    return value


def semantic_digest_from_lens_checkpoint(path: str | Path) -> dict[str, Any]:
    """Compute a filename/serialization-independent digest of persisted J matrices.

    The checkpoint must use the public JacobianLens save shape: J, n_prompts,
    source_layers, d_model. Every matrix is canonicalized to CPU contiguous finite
    little-endian float32 before hashing. The raw artifact SHA remains separate.
    """
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ReceiptError("TORCH_REQUIRED_FOR_LENS_SEMANTIC_DIGEST") from exc

    checkpoint = torch.load(str(path), map_location="cpu", weights_only=True)
    if not isinstance(checkpoint, dict):
        raise ReceiptError("LENS_CHECKPOINT_NOT_OBJECT")
    required = {"J", "n_prompts", "source_layers", "d_model"}
    if not required.issubset(checkpoint):
        raise ReceiptError("LENS_CHECKPOINT_FIELDS_MISSING")

    n_prompts = checkpoint["n_prompts"]
    d_model = checkpoint["d_model"]
    if type(n_prompts) is not int or n_prompts <= 0:
        raise ReceiptError("BAD_LENS_N_PROMPTS")
    if type(d_model) is not int or d_model <= 0:
        raise ReceiptError("BAD_LENS_D_MODEL")
    source_layers = _canonical_source_layers(checkpoint["source_layers"])

    matrices = checkpoint["J"]
    if not isinstance(matrices, dict) or set(matrices) != set(source_layers):
        raise ReceiptError("LENS_MATRIX_LAYER_SET_MISMATCH")

    digest = hashlib.sha256()
    digest.update(SEMANTIC_DIGEST_DOMAIN)
    digest.update(struct.pack("<qqq", n_prompts, d_model, len(source_layers)))

    for layer in source_layers:
        matrix = matrices[layer]
        if not isinstance(matrix, torch.Tensor):
            raise ReceiptError("LENS_MATRIX_NOT_TENSOR")
        matrix = matrix.detach().to(device="cpu", dtype=torch.float32).contiguous()
        if matrix.ndim != 2 or tuple(matrix.shape) != (d_model, d_model):
            raise ReceiptError("LENS_MATRIX_SHAPE_MISMATCH")
        if not bool(torch.isfinite(matrix).all().item()):
            raise ReceiptError("NONFINITE_LENS_REJECTED")
        digest.update(struct.pack("<qqq", layer, matrix.shape[0], matrix.shape[1]))
        # PyTorch CPU numpy arrays use native endian. astype('<f4') makes the wire
        # representation deterministic across little/big-endian hosts.
        payload = matrix.numpy().astype("<f4", copy=False).tobytes(order="C")
        digest.update(payload)

    return {
        "artifact_sha256": _sha256_file(path),
        "semantic_content_sha256": digest.hexdigest(),
        "semantic_digest_method": SEMANTIC_DIGEST_METHOD,
        "finite_check_passed": True,
        "n_prompts": n_prompts,
        "source_layers": source_layers,
        "d_model": d_model,
    }


def validate_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ReceiptError("RECEIPT_NOT_OBJECT")
    if receipt.get("schema") != SCHEMA:
        raise ReceiptError("BAD_SCHEMA")

    source = _require_obj(receipt, "source")
    _require_gitsha(source, "repo_commit")
    _require_gitsha(source, "repo_tree")
    if _require_bool(source, "dirty"):
        raise ReceiptError("DIRTY_SOURCE_FORBIDDEN")

    core = _require_obj(receipt, "bundled_core")
    _require_str(core, "engine_id")
    _require_str(core, "model_family")
    _require_sha256(core, "checkpoint_sha256")
    _require_sha256(core, "tokenizer_sha256")
    _require_str(core, "runtime_identity")

    lens = _require_obj(receipt, "lens")
    _require_gitsha(lens, "implementation_commit")
    _require_sha256(lens, "artifact_sha256")
    _require_sha256(lens, "semantic_content_sha256")
    _require_sha256(lens, "fit_corpus_sha256")
    _require_positive_int(lens, "fit_prompt_count")
    source_layers = _canonical_source_layers(lens.get("source_layers"))
    target_layer = lens.get("target_layer")
    if type(target_layer) is not int or target_layer <= max(source_layers):
        raise ReceiptError("BAD_TARGET_LAYER")
    if _require_str(lens, "semantic_digest_method") != SEMANTIC_DIGEST_METHOD:
        raise ReceiptError("UNSUPPORTED_SEMANTIC_DIGEST_METHOD")
    if not _require_bool(lens, "finite_check_passed"):
        raise ReceiptError("NONFINITE_LENS_REJECTED")

    workspace = _require_obj(receipt, "workspace")
    for key in (
        "jspace_profile_sha256",
        "lens_profile_sha256",
        "gwt_policy_sha256",
        "workspace_calibration_sha256",
    ):
        _require_sha256(workspace, key)
    mode = _require_str(workspace, "jspace_mode")
    if mode not in _JSPACE_MODES:
        raise ReceiptError("BAD_JSPACE_MODE")
    _require_positive_int(workspace, "jspace_sparsity_k")
    _require_positive_int(workspace, "gwt_slot_limit")

    control = _require_obj(receipt, "control_projection")
    _require_sha256(control, "zero_identity_sha256")
    _require_sha256(control, "grf_sha256")
    hp = control.get("hyperposition_state_sha256")
    if hp is not None and (not isinstance(hp, str) or not _SHA256.fullmatch(hp)):
        raise ReceiptError("BAD_HYPERPOSITION_DIGEST")

    claude = _require_obj(receipt, "claude_adapter")
    _require_str(claude, "adapter_version")
    _require_sha256(claude, "capability_profile_sha256")
    _require_sha256(claude, "transport_profile_sha256")

    runtime = _require_obj(receipt, "runtime")
    _require_str(runtime, "execution_surface")
    if not _require_bool(runtime, "started"):
        raise ReceiptError("RUNTIME_NOT_STARTED")
    _require_str(runtime, "first_engine_choice")
    if _require_str(runtime, "first_action_origin") not in _ACTION_ORIGINS:
        raise ReceiptError("BAD_FIRST_ACTION_ORIGIN")

    policy = _require_obj(receipt, "policy")
    free_only = _require_bool(policy, "free_only")
    paid_network = _require_nonnegative_int(policy, "paid_or_unknown_network_attempts")
    secret_lookups = _require_nonnegative_int(policy, "paid_or_unknown_secret_lookups")
    if free_only and (paid_network != 0 or secret_lookups != 0):
        raise ReceiptError("FREE_ONLY_BOUNDARY_BREACH")

    canonical = json.dumps(
        receipt,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return {
        "ok": True,
        "schema": SCHEMA,
        "receipt_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "evidence_class": "STRUCTURAL_BINDING_ONLY",
    }


def verify_lens_artifact(receipt: dict[str, Any], lens_path: str | Path) -> dict[str, Any]:
    """Recompute and compare both raw-byte and semantic J-matrix identities."""
    result = validate_receipt(receipt)
    observed = semantic_digest_from_lens_checkpoint(lens_path)
    lens = receipt["lens"]
    if observed["artifact_sha256"] != lens["artifact_sha256"]:
        raise ReceiptError("LENS_ARTIFACT_HASH_MISMATCH")
    if observed["semantic_content_sha256"] != lens["semantic_content_sha256"]:
        raise ReceiptError("LENS_SEMANTIC_HASH_MISMATCH")
    if observed["semantic_digest_method"] != lens["semantic_digest_method"]:
        raise ReceiptError("LENS_SEMANTIC_METHOD_MISMATCH")
    if observed["source_layers"] != lens["source_layers"]:
        raise ReceiptError("LENS_SOURCE_LAYER_MISMATCH")
    if observed["n_prompts"] != lens["fit_prompt_count"]:
        raise ReceiptError("LENS_PROMPT_COUNT_MISMATCH")
    result["lens_artifact_verified"] = True
    return result


def load_and_validate(path: str | Path) -> dict[str, Any]:
    def reject_constant(_: str) -> Any:
        raise ReceiptError("NONFINITE_JSON")

    data = json.loads(Path(path).read_text(encoding="utf-8"), parse_constant=reject_constant)
    return validate_receipt(data)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("receipt")
    parser.add_argument("--lens", default=None)
    args = parser.parse_args()
    try:
        receipt_data = json.loads(
            Path(args.receipt).read_text(encoding="utf-8"),
            parse_constant=lambda _: (_ for _ in ()).throw(ReceiptError("NONFINITE_JSON")),
        )
        output = (
            verify_lens_artifact(receipt_data, args.lens)
            if args.lens
            else validate_receipt(receipt_data)
        )
        print(json.dumps(output, sort_keys=True))
    except Exception as exc:
        print(
            json.dumps(
                {"ok": False, "error_kind": type(exc).__name__, "error": str(exc)},
                sort_keys=True,
            )
        )
        raise SystemExit(2)
