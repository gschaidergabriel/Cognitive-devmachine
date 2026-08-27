#!/usr/bin/env python3
"""Trigger-2 J-Space post-intervention metrology primitive v1.

This module repairs a specific measurement failure observed in the Qwen3.5 Trigger-2
causal-intervention campaign: downstream ``output_hidden_states`` did not prove that the
reported representation was the tensor actually returned by the intervention hook.

The primitive captures the PRE and POST tensors *inside the same forward hook* and
returns the exact captured POST tensor to the model. It is intentionally model-agnostic
and non-promoting: a component PASS proves only hook-local measurement fidelity. It does
not prove J-Space causality, checkpoint eligibility, HCU runtime acceptance, or training
readiness.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import math
from typing import Any, Callable

SCHEMA = "CLAY_TRIGGER2_JSPACE_POST_INTERVENTION_METROLOGY/v1"


class MetrologyError(RuntimeError):
    """Fail-closed metrology error."""


def _json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _tensor_identity(tensor: Any) -> dict[str, Any]:
    import torch

    if not isinstance(tensor, torch.Tensor):
        raise MetrologyError("TENSOR_REQUIRED")
    t = tensor.detach().cpu().contiguous()
    raw = t.view(torch.uint8).numpy().tobytes(order="C")
    envelope = b"TRIGGER2_JSPACE_TENSOR_IDENTITY_V1\0" + _json_bytes(
        {"dtype": str(t.dtype), "shape": [int(x) for x in t.shape]}
    ) + b"\0" + raw
    return {
        "sha256": sha256(envelope).hexdigest(),
        "raw_bytes_sha256": sha256(raw).hexdigest(),
        "dtype": str(t.dtype),
        "shape": [int(x) for x in t.shape],
        "numel": int(t.numel()),
        "raw_nbytes": len(raw),
    }


def _metrics(pre: Any, post: Any) -> dict[str, float]:
    import torch

    a = pre.detach().float().reshape(-1).cpu()
    b = post.detach().float().reshape(-1).cpu()
    delta = b - a
    l2 = float(torch.linalg.vector_norm(delta).item())
    a_norm = float(torch.linalg.vector_norm(a).item())
    b_norm = float(torch.linalg.vector_norm(b).item())
    if a_norm == 0.0 or b_norm == 0.0:
        cosine = math.nan
    else:
        cosine = float(torch.dot(a, b).item() / (a_norm * b_norm))
    return {
        "l2_distance_pre_to_post": l2,
        "cosine_similarity_pre_to_post": cosine,
        "pre_l2_norm": a_norm,
        "post_l2_norm": b_norm,
    }


def _extract_hidden(output: Any) -> tuple[Any, Callable[[Any], Any], str]:
    """Return hidden tensor, output rebuilder, and shape tag.

    Decoder blocks commonly return either a Tensor or a tuple whose first item is the
    hidden-state Tensor. Other structures fail closed rather than being guessed.
    """
    import torch

    if isinstance(output, torch.Tensor):
        return output, lambda replacement: replacement, "tensor"
    if isinstance(output, tuple) and output and isinstance(output[0], torch.Tensor):
        tail = output[1:]
        return output[0], lambda replacement: (replacement, *tail), "tuple_first_tensor"
    raise MetrologyError(f"UNSUPPORTED_MODULE_OUTPUT:{type(output).__name__}")


@dataclass
class CaptureRecord:
    call_index: int
    output_form: str
    pre: dict[str, Any]
    post: dict[str, Any]
    returned: dict[str, Any]
    metrics: dict[str, float]
    post_equals_returned: bool
    changed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_index": self.call_index,
            "output_form": self.output_form,
            "pre": self.pre,
            "post": self.post,
            "returned": self.returned,
            "metrics": self.metrics,
            "post_equals_returned": self.post_equals_returned,
            "changed": self.changed,
        }


@dataclass
class PostInterventionMetrology:
    """Forward-hook metrology that measures the tensor it actually returns."""

    intervention: Callable[[Any], Any]
    require_change: bool = False
    records: list[CaptureRecord] = field(default_factory=list)

    def hook(self, _module: Any, _inputs: Any, output: Any) -> Any:
        import torch

        hidden, rebuild, output_form = _extract_hidden(output)
        pre_tensor = hidden.detach().clone()
        post_tensor = self.intervention(hidden)
        if not isinstance(post_tensor, torch.Tensor):
            raise MetrologyError("INTERVENTION_MUST_RETURN_TENSOR")
        if tuple(post_tensor.shape) != tuple(hidden.shape):
            raise MetrologyError("INTERVENTION_SHAPE_CHANGED")
        if post_tensor.dtype != hidden.dtype:
            raise MetrologyError("INTERVENTION_DTYPE_CHANGED")
        if post_tensor.device != hidden.device:
            raise MetrologyError("INTERVENTION_DEVICE_CHANGED")

        # Capture *inside the hook* before the value leaves the intervention boundary.
        post_capture = post_tensor.detach().clone()
        rebuilt = rebuild(post_tensor)
        returned_hidden, _rebuilder, _returned_form = _extract_hidden(rebuilt)
        returned_capture = returned_hidden.detach().clone()

        pre_id = _tensor_identity(pre_tensor)
        post_id = _tensor_identity(post_capture)
        returned_id = _tensor_identity(returned_capture)
        same = post_id["sha256"] == returned_id["sha256"]
        changed = pre_id["sha256"] != post_id["sha256"]
        if not same:
            raise MetrologyError("POST_CAPTURE_NOT_EQUAL_TO_RETURNED_TENSOR")
        if self.require_change and not changed:
            raise MetrologyError("INTERVENTION_EXPECTED_CHANGE_BUT_TENSOR_UNCHANGED")

        self.records.append(
            CaptureRecord(
                call_index=len(self.records),
                output_form=output_form,
                pre=pre_id,
                post=post_id,
                returned=returned_id,
                metrics=_metrics(pre_tensor, post_capture),
                post_equals_returned=same,
                changed=changed,
            )
        )
        return rebuilt

    def receipt(self, *, site_identity: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "status": "PASS_COMPONENT_ONLY" if self.records and all(r.post_equals_returned for r in self.records) else "UNRESOLVED",
            "measurement_scope": "HOOK_LOCAL_POST_INTERVENTION_TENSOR_FIDELITY_ONLY",
            "site_identity": site_identity or {},
            "calls_observed": len(self.records),
            "records": [r.to_dict() for r in self.records],
            "credit_boundary": {
                "jspace_model_credit": 0,
                "jspace_causal_credit": 0,
                "checkpoint_selection_credit": 0,
                "training_credit": 0,
                "whole_hcu_runtime_credit": 0,
                "whole_entityos_runtime_credit": 0,
            },
            "invariant": "REPRESENTATION_METRIC_MUST_BE_DERIVED_FROM_POST_TENSOR_CAPTURED_INSIDE_THE_SAME_FORWARD_HOOK_AND_RETURNED_TO_THE_MODEL",
        }


def self_test() -> dict[str, Any]:
    """Deterministic synthetic proof that the captured POST tensor is the returned tensor."""
    import torch

    torch.manual_seed(0)
    layer = torch.nn.Identity()
    vector = torch.tensor([0.25, -0.5, 1.0], dtype=torch.float32)

    def intervention(hidden: Any) -> Any:
        return hidden + vector

    metrology = PostInterventionMetrology(intervention=intervention, require_change=True)
    handle = layer.register_forward_hook(metrology.hook)
    try:
        x = torch.tensor([[1.0, 2.0, 3.0]], dtype=torch.float32)
        y = layer(x)
    finally:
        handle.remove()

    expected = x + vector
    if not torch.equal(y, expected):
        raise MetrologyError("SELF_TEST_MODEL_DID_NOT_RECEIVE_INTERVENED_TENSOR")
    receipt = metrology.receipt(site_identity={"kind": "synthetic_identity_layer"})
    if receipt["status"] != "PASS_COMPONENT_ONLY":
        raise MetrologyError("SELF_TEST_RECEIPT_NOT_PASS")
    if receipt["records"][0]["post"]["sha256"] != receipt["records"][0]["returned"]["sha256"]:
        raise MetrologyError("SELF_TEST_POST_RETURN_IDENTITY_MISMATCH")
    return receipt


if __name__ == "__main__":
    print(json.dumps(self_test(), sort_keys=True, indent=2, ensure_ascii=False))
