#!/usr/bin/env python3
"""Scope-matched PyTorch witness for the pinned Qwen3 llama.cpp cvec operator.

The historical PyTorch witness changed only hidden[:, -1, :]. Pinned llama.cpp Qwen3
applies build_cvec(cur, il) to the full layer-output tensor, so its one-dimensional layer
vector broadcasts over every token row in the prompt ubatch. This successor applies the
same tensor-level operator shape in PyTorch: H'[:, :, :] = H[:, :, :] + v[None,None,:].

This source does not claim numerical identity between full-precision PyTorch and Q8 GGUF.
It establishes scope/operator-shape parity; causal replication still requires matched
runtime controls on the same frozen cases and is adjudicated separately.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from tools import trigger1_local_qwen06_midlayer_causal_execute as base

SCHEMA = "CLAY_TRIGGER1_SCOPE_MATCHED_BROADCAST_WITNESS/v1"
SCOPE_ATTESTATION_SCHEMA = "CLAY_TRIGGER1_CVEC_SCOPE_CONTRACT/v1"
PINNED_LLAMA_CPP_COMMIT = "bb4caa7540188872173c44d161602d9271386413"
PINNED_QWEN3_SOURCE = "src/models/qwen3.cpp"
INJECTION_LAYER = 20
N_EMBD = 1024
PYTORCH_SCOPE = "LAYER_OUTPUT_ALL_BATCH_SEQUENCE_TOKEN_ROWS"
NATIVE_SCOPE = "QWEN3_L_OUT_ALL_UBATCH_TOKEN_ROWS"
HISTORICAL_SCOPE = "LAYER_OUTPUT_LAST_TOKEN_ONLY"


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def scope_contract() -> dict[str, Any]:
    core = {
        "schema": SCOPE_ATTESTATION_SCHEMA,
        "llama_cpp_commit": PINNED_LLAMA_CPP_COMMIT,
        "native_source_path": PINNED_QWEN3_SOURCE,
        "injection_layer": INJECTION_LAYER,
        "dimension": N_EMBD,
        "native_operator": "cur = build_cvec(cur, il)",
        "native_site": "after ffn residual add and before l_out/layer transition",
        "native_scope": NATIVE_SCOPE,
        "pytorch_operator": "hidden = hidden + vector.reshape(1,1,-1)",
        "pytorch_scope": PYTORCH_SCOPE,
        "historical_last_token_scope": HISTORICAL_SCOPE,
        "historical_last_token_witness_eligible_for_scope_equivalence": False,
        "numerical_backend_identity_claimed": False,
        "required_followup": "matched-control causal-signature replication on frozen cases",
    }
    return {**core, "scope_contract_sha256": canonical_sha(core)}


def apply_all_token_broadcast(output: Any, vector: Any) -> tuple[Any, dict[str, Any]]:
    """Add one hidden vector to every batch/sequence row at a layer output."""
    hidden = base.unpack_hidden(output)
    if getattr(hidden, "ndim", None) != 3:
        raise RuntimeError(f"HIDDEN_RANK_MUST_BE_3:{getattr(hidden, 'ndim', None)}")
    shape = tuple(int(x) for x in hidden.shape)
    if len(shape) != 3 or shape[-1] != N_EMBD:
        raise RuntimeError(f"HIDDEN_SHAPE_INVALID:{shape}")
    v = vector.to(device=hidden.device, dtype=hidden.dtype)
    if getattr(v, "ndim", None) != 1 or int(v.shape[0]) != shape[-1]:
        raise RuntimeError(f"VECTOR_SHAPE_INVALID:{tuple(int(x) for x in v.shape)}")
    shifted = hidden.clone() + v.reshape(1, 1, -1)
    receipt = {
        "schema": SCHEMA,
        "intervention_scope": PYTORCH_SCOPE,
        "batch_rows": shape[0],
        "sequence_token_rows": shape[1],
        "hidden_dimension": shape[2],
        "token_rows_modified": shape[0] * shape[1],
        "last_token_only": False,
        "vector_sha256": base.tensor_sha(v),
    }
    return base.replace_hidden(output, shifted), receipt


def target_infer(
    torch: Any,
    tokenizer: Any,
    model: Any,
    device: Any,
    layer: Any,
    token_ids: dict[str, int],
    prompt: str,
    seed: int,
    vector: Any | None,
) -> dict[str, Any]:
    """Run one scope-matched all-token intervention and return A/B/C logits + receipt."""
    hook_calls = 0
    scope_receipt: dict[str, Any] | None = None

    def hook(_module: Any, _inputs: Any, output: Any):
        nonlocal hook_calls, scope_receipt
        hook_calls += 1
        if vector is None:
            hidden = base.unpack_hidden(output)
            shape = tuple(int(x) for x in hidden.shape)
            scope_receipt = {
                "schema": SCHEMA,
                "intervention_scope": "BASELINE_NO_VECTOR",
                "batch_rows": shape[0],
                "sequence_token_rows": shape[1],
                "hidden_dimension": shape[2],
                "token_rows_modified": 0,
                "last_token_only": False,
                "vector_sha256": None,
            }
            return output
        replaced, receipt = apply_all_token_broadcast(output, vector)
        scope_receipt = receipt
        return replaced

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    handle = layer.register_forward_hook(hook)
    try:
        with torch.no_grad():
            out = model(**inputs)
            logits = out.logits[0, -1].float().detach().cpu()
    finally:
        handle.remove()
    if hook_calls != 1 or scope_receipt is None:
        raise RuntimeError(f"SCOPE_MATCHED_HOOK_COUNT_INVALID:{hook_calls}")
    trio = {label: float(logits[token_id]) for label, token_id in token_ids.items()}
    return {
        "token_logits": trio,
        "best_label": max(trio, key=trio.get),
        "hook_calls": hook_calls,
        "scope_receipt": scope_receipt,
        "scope_contract_sha256": scope_contract()["scope_contract_sha256"],
    }
