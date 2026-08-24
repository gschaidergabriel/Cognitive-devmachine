#!/usr/bin/env python3
"""Hookable local Transformers executor for direct EntityOS/HCU J-Space activation steering.

This is a research executor candidate behind ``jspace_activation_steering_search_v1``.
Unlike closed chat APIs, it changes an actual decoder-layer activation tensor.  It is
intentionally model-object injected: importing this module does not download a checkpoint,
look up a credential, contact a provider, or create a second model/state/effect authority.

Intervention contract (v1):

* target one exact decoder layer selected by ``layer_id='model.layers.<index>'``;
* on the first decoder-layer forward whose hidden-state tensor contains more than one token
  (the prompt-prefill pass), add ``alpha * vector`` to the final token activation only;
* apply the vector exactly once per invocation; subsequent decode steps are observed but not
  modified by this hook;
* hash the exact pre/post target activation vector as canonical float32 little-endian bytes;
* return the existing ``HCU_ACTIVATION_STEERING_HOOK_RECEIPT/v1`` required by the bounded
  search harness.

The one-shot prefill intervention makes temporal position explicit and avoids silently adding
an intervention at every autoregressive decode step.  A different intervention policy must
use a different schema/version rather than changing these semantics in place.

Source presence is NOT runtime evidence.  Positive direct-steering credit requires exact
checkpoint/tokenizer/runtime/build identity, actual loader/model execution, a hook receipt,
and the sign/zero controls enforced by ``search_activation_steering``.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import struct
from typing import Any, Iterator, Sequence

try:
    from .jspace_activation_steering_search_v1 import (
        HOOK_RECEIPT_SCHEMA,
        HookReceipt,
        SteeringObservation,
        applied_vector_sha256,
    )
except ImportError:
    from jspace_activation_steering_search_v1 import (
        HOOK_RECEIPT_SCHEMA,
        HookReceipt,
        SteeringObservation,
        applied_vector_sha256,
    )

EXECUTOR_SCHEMA = "HCU_TRANSFORMERS_ACTIVATION_STEERING_EXECUTOR/v1"
INTERVENTION_SCHEMA = "HCU_QWEN3_PREFILL_LAST_TOKEN_RESIDUAL_ADD/v1"
EXPECTED_QWEN3_06B_HIDDEN_SIZE = 1024
MAX_NEW_TOKENS = 256


class TransformersActivationExecutorError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise TransformersActivationExecutorError(message)


def _text(value: Any, field: str, max_len: int = 1024) -> str:
    _need(isinstance(value, str) and bool(value.strip()), f"{field}:NONEMPTY_STRING_REQUIRED")
    normalized = value.strip()
    _need(value == normalized, f"{field}:NONCANONICAL_TEXT")
    _need(len(normalized) <= max_len, f"{field}:TOO_LONG")
    return normalized


def _seed(value: Any) -> int:
    _need(not isinstance(value, bool) and isinstance(value, int) and value >= 0, "seed:NONNEGATIVE_INTEGER_REQUIRED")
    _need(value <= 9_007_199_254_740_991, "seed:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _alpha(value: Any) -> float:
    import math

    _need(not isinstance(value, bool) and isinstance(value, (int, float)), "alpha:FINITE_NUMBER_REQUIRED")
    normalized = float(value)
    _need(math.isfinite(normalized), "alpha:FINITE_NUMBER_REQUIRED")
    return normalized


def _vector(values: Sequence[float], expected_size: int) -> tuple[float, ...]:
    import math

    _need(not isinstance(values, (str, bytes, bytearray)) and isinstance(values, Sequence), "vector:SEQUENCE_REQUIRED")
    _need(len(values) == expected_size, "VECTOR_HIDDEN_SIZE_MISMATCH")
    normalized = []
    for index, value in enumerate(values):
        _need(not isinstance(value, bool) and isinstance(value, (int, float)), f"vector[{index}]:FINITE_NUMBER_REQUIRED")
        converted = float(value)
        _need(math.isfinite(converted), f"vector[{index}]:FINITE_NUMBER_REQUIRED")
        normalized.append(converted)
    return tuple(normalized)


def _canonical_float32_sha256(values: Sequence[float]) -> str:
    """Hash exact little-endian float32 coordinates, independent of tensor object identity."""
    normalized = tuple(float(value) for value in values)
    raw = struct.pack("<" + "f" * len(normalized), *normalized)
    return hashlib.sha256(raw).hexdigest()


def _layer_index(layer_id: str) -> int:
    layer_id = _text(layer_id, "layer_id", 128)
    prefix = "model.layers."
    _need(layer_id.startswith(prefix), "LAYER_ID_SCHEMA_UNSUPPORTED")
    suffix = layer_id[len(prefix):]
    _need(suffix.isdigit() and str(int(suffix)) == suffix, "LAYER_ID_INDEX_INVALID")
    return int(suffix)


def _resolve_layers(model: Any) -> Any:
    """Resolve HF Qwen-style decoder layers without accepting arbitrary dotted paths."""
    root = getattr(model, "model", None)
    layers = getattr(root, "layers", None)
    _need(layers is not None, "QWEN_DECODER_LAYERS_UNAVAILABLE")
    return layers


def _model_hidden_size(model: Any) -> int:
    config = getattr(model, "config", None)
    hidden = getattr(config, "hidden_size", None)
    _need(type(hidden) is int and hidden > 0, "MODEL_HIDDEN_SIZE_UNAVAILABLE")
    return hidden


def _model_identity(model: Any) -> str:
    config = getattr(model, "config", None)
    name = getattr(config, "_name_or_path", None)
    if not isinstance(name, str) or not name.strip():
        name = type(model).__name__
    return _text(name.strip(), "model_identity", 512)


def _tensor_vector_f32(tensor: Any) -> tuple[float, ...]:
    """Extract one 1-D activation vector as exact Python float32 values for hashing."""
    try:
        values = tensor.detach().to(dtype=getattr(tensor, "dtype", None)).float().cpu().contiguous().tolist()
    except Exception as exc:  # runtime adapter boundary
        raise TransformersActivationExecutorError("ACTIVATION_TENSOR_EXTRACTION_FAILED") from exc
    _need(isinstance(values, list) and values, "ACTIVATION_VECTOR_REQUIRED")
    return tuple(float(value) for value in values)


def _replace_first_output(output: Any, steered_hidden: Any) -> Any:
    if isinstance(output, tuple):
        _need(len(output) >= 1, "DECODER_LAYER_OUTPUT_EMPTY")
        return (steered_hidden, *output[1:])
    return steered_hidden


def _first_hidden(output: Any) -> Any:
    hidden = output[0] if isinstance(output, tuple) else output
    _need(hasattr(hidden, "shape") and len(hidden.shape) == 3, "DECODER_HIDDEN_STATE_3D_REQUIRED")
    return hidden


@dataclass
class _HookState:
    applied: bool = False
    pre_sha256: str | None = None
    post_sha256: str | None = None


class TransformersActivationExecutor:
    """Real activation-hook executor compatible with ``SteerableExecutor`` protocol.

    ``model`` and ``tokenizer`` must already be materialized and admitted by the surrounding
    runtime.  This adapter performs no download and no credential access.
    """

    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        *,
        executor_id: str,
        max_new_tokens: int = 64,
        do_sample: bool = True,
        temperature: float = 0.7,
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.executor_id = _text(executor_id, "executor_id", 256)
        self.max_new_tokens = int(max_new_tokens)
        _need(1 <= self.max_new_tokens <= MAX_NEW_TOKENS, "max_new_tokens:OUT_OF_RANGE")
        self.do_sample = bool(do_sample)
        self.temperature = float(temperature)
        _need(self.temperature > 0.0, "temperature:POSITIVE_REQUIRED")
        self.hidden_size = _model_hidden_size(model)
        self.layers = _resolve_layers(model)
        _need(len(self.layers) > 0, "DECODER_LAYERS_EMPTY")

    @contextmanager
    def _steering_hook(
        self,
        *,
        layer_id: str,
        vector: tuple[float, ...],
        alpha: float,
    ) -> Iterator[_HookState]:
        index = _layer_index(layer_id)
        _need(index < len(self.layers), "LAYER_INDEX_OUT_OF_RANGE")
        target = self.layers[index]
        state = _HookState()

        def hook(_module: Any, _inputs: Any, output: Any) -> Any:
            hidden = _first_hidden(output)
            # Apply exactly once and only on prompt-prefill (>1 token), final token position.
            if state.applied or int(hidden.shape[1]) <= 1:
                return output
            _need(int(hidden.shape[-1]) == self.hidden_size, "RUNTIME_HIDDEN_SIZE_MISMATCH")
            try:
                delta = hidden.new_tensor(vector).to(dtype=hidden.dtype, device=hidden.device)
                before = hidden[:, -1, :].detach().clone()
                steered = hidden.clone()
                steered[:, -1, :] = steered[:, -1, :] + alpha * delta
                after = steered[:, -1, :].detach().clone()
            except Exception as exc:
                raise TransformersActivationExecutorError("ACTIVATION_STEERING_TENSOR_OPERATION_FAILED") from exc
            state.pre_sha256 = _canonical_float32_sha256(_tensor_vector_f32(before[0]))
            state.post_sha256 = _canonical_float32_sha256(_tensor_vector_f32(after[0]))
            state.applied = True
            return _replace_first_output(output, steered)

        handle = target.register_forward_hook(hook)
        try:
            yield state
        finally:
            handle.remove()

    def _tokenize(self, prompt: str) -> Any:
        prompt = _text(prompt, "prompt", 262144)
        try:
            encoded = self.tokenizer(prompt, return_tensors="pt")
        except Exception as exc:
            raise TransformersActivationExecutorError("TOKENIZATION_FAILED") from exc
        _need(isinstance(encoded, dict) or hasattr(encoded, "to"), "TOKENIZER_OUTPUT_UNSUPPORTED")
        device = getattr(self.model, "device", None)
        if hasattr(encoded, "to") and device is not None:
            return encoded.to(device)
        if isinstance(encoded, dict) and device is not None:
            return {key: value.to(device) if hasattr(value, "to") else value for key, value in encoded.items()}
        return encoded

    def _generate(self, encoded: Any, *, seed: int) -> tuple[Any, int]:
        try:
            import torch
        except ImportError as exc:
            raise TransformersActivationExecutorError("PYTORCH_RUNTIME_REQUIRED") from exc
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        input_ids = encoded["input_ids"]
        prompt_tokens = int(input_ids.shape[-1])
        kwargs = dict(
            max_new_tokens=self.max_new_tokens,
            do_sample=self.do_sample,
            pad_token_id=getattr(self.tokenizer, "pad_token_id", None) or getattr(self.tokenizer, "eos_token_id", None),
        )
        if self.do_sample:
            kwargs["temperature"] = self.temperature
        try:
            with torch.no_grad():
                output_ids = self.model.generate(**encoded, **kwargs)
        except Exception as exc:
            raise TransformersActivationExecutorError("MODEL_GENERATION_FAILED") from exc
        return output_ids, prompt_tokens

    def _decode(self, output_ids: Any, prompt_tokens: int) -> str:
        try:
            generated = output_ids[0][prompt_tokens:]
            text = self.tokenizer.decode(generated, skip_special_tokens=True)
        except Exception as exc:
            raise TransformersActivationExecutorError("OUTPUT_DECODE_FAILED") from exc
        return str(text)

    def run(
        self,
        prompt: str,
        *,
        layer_id: str | None,
        vector: tuple[float, ...] | None,
        alpha: float,
        seed: int,
    ) -> SteeringObservation:
        seed = _seed(seed)
        alpha = _alpha(alpha)
        invocation_id = f"activation-steering:{seed}:{layer_id or 'baseline'}:{alpha.hex()}"
        encoded = self._tokenize(prompt)

        if layer_id is None:
            _need(vector is None and alpha == 0.0, "BASELINE_STEERING_ARGUMENTS_FORBIDDEN")
            output_ids, prompt_tokens = self._generate(encoded, seed=seed)
            return SteeringObservation(self._decode(output_ids, prompt_tokens), None)

        _need(vector is not None, "STEERING_VECTOR_REQUIRED")
        normalized_vector = _vector(vector, self.hidden_size)
        vector_sha = applied_vector_sha256(normalized_vector)
        with self._steering_hook(layer_id=layer_id, vector=normalized_vector, alpha=alpha) as state:
            output_ids, prompt_tokens = self._generate(encoded, seed=seed)
        _need(state.applied, "STEERING_HOOK_NOT_APPLIED_TO_PREFILL")
        _need(state.pre_sha256 is not None and state.post_sha256 is not None, "STEERING_HOOK_HASHES_MISSING")
        receipt = HookReceipt(
            schema=HOOK_RECEIPT_SCHEMA,
            executor_id=self.executor_id,
            invocation_id=invocation_id,
            layer_id=_text(layer_id, "layer_id", 128),
            seed=seed,
            alpha=alpha,
            applied_vector_sha256=vector_sha,
            pre_activation_sha256=state.pre_sha256,
            post_activation_sha256=state.post_sha256,
        )
        return SteeringObservation(self._decode(output_ids, prompt_tokens), receipt)


__all__ = [
    "EXECUTOR_SCHEMA",
    "INTERVENTION_SCHEMA",
    "EXPECTED_QWEN3_06B_HIDDEN_SIZE",
    "TransformersActivationExecutorError",
    "TransformersActivationExecutor",
]
