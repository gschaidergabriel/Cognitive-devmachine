#!/usr/bin/env python3
"""Matched PyTorch LAST_TOKEN / ALL_PROMPT_TOKENS probe for Trigger-1 scope isolation.

This is the missing executable half of the scope discriminator.  It consumes one frozen
1024-D basis vector and one frozen case plan, then runs the exact same six-control family
at layer 20 under two PyTorch intervention scopes:

  PYTORCH_LAST_TOKEN        -> hidden[:, -1, :] += vector
  PYTORCH_ALL_PROMPT_TOKENS -> hidden[:, :,  :] += vector

Rows are emitted in the schema consumed by trigger1_scope_equivalence_gate_v1.  Native
llama.cpp cvec rows are intentionally NOT synthesized here; they must come from the pinned
native harness.  The combined gate can therefore isolate scope before comparing carriers.

No promotion/canonical credit is minted by this probe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_local_qwen06_midlayer_causal_execute as base
from tools import trigger1_scope_equivalence_gate_v1 as scope_gate

SCHEMA = "CLAY_TRIGGER1_PYTORCH_SCOPE_MATCHED_PROBE_INPUT/v1"
RESULT_SCHEMA = "CLAY_TRIGGER1_PYTORCH_SCOPE_MATCHED_PROBE_RESULT/v1"
LAYER = 20
N_EMBD = 1024
SCOPES = (
    "PYTORCH_LAST_TOKEN",
    "PYTORCH_ALL_PROMPT_TOKENS",
)
SCOPE_TEXT = {
    "PYTORCH_LAST_TOKEN": "LAST_TOKEN_ONLY_AT_SELECTED_BLOCK_OUTPUT",
    "PYTORCH_ALL_PROMPT_TOKENS": "ALL_PROMPT_TOKEN_POSITIONS_AT_SELECTED_BLOCK_OUTPUT",
}


def canonical_sha(value: Any) -> str:
    return scope_gate.canonical_sha(value)


def is_sha(value: Any) -> bool:
    return scope_gate.is_sha(value)


def apply_vector(output: Any, vector: Any, scope: str) -> Any:
    hidden = base.unpack_hidden(output).clone()
    v = vector.to(device=hidden.device, dtype=hidden.dtype)
    if scope == "PYTORCH_LAST_TOKEN":
        hidden[:, -1, :] = hidden[:, -1, :] + v
    elif scope == "PYTORCH_ALL_PROMPT_TOKENS":
        hidden = hidden + v.view(1, 1, -1)
    else:
        raise ValueError(f"UNKNOWN_SCOPE:{scope}")
    return base.replace_hidden(output, hidden)


def validate_input(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise ValueError("INPUT_SCHEMA_INVALID")
    if int(payload.get("layer", -1)) != LAYER:
        raise ValueError("EXACT_LAYER20_REQUIRED")
    try:
        gain = float(payload["gain"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("GAIN_REQUIRED")
    if not math.isfinite(gain) or gain <= 0:
        raise ValueError("GAIN_INVALID")
    vector = payload.get("basis_vector_f32")
    if not isinstance(vector, list) or len(vector) != N_EMBD:
        raise ValueError("EXACT_1024D_BASIS_VECTOR_REQUIRED")
    if any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(float(x)) for x in vector):
        raise ValueError("BASIS_VECTOR_NONFINITE")
    if not is_sha(payload.get("basis_vector_sha256")):
        raise ValueError("BASIS_VECTOR_SHA256_REQUIRED")
    if not is_sha(payload.get("case_plan_sha256")):
        raise ValueError("CASE_PLAN_SHA256_REQUIRED")
    if not is_sha(payload.get("control_family_sha256")):
        raise ValueError("CONTROL_FAMILY_SHA256_REQUIRED")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("NONEMPTY_CASES_REQUIRED")
    seen: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"CASE_{index}_OBJECT_REQUIRED")
        case_id = case.get("case_identity_sha256")
        if not is_sha(case_id) or case_id in seen:
            raise ValueError(f"CASE_{index}_IDENTITY_INVALID_OR_DUPLICATE")
        seen.add(case_id)
        if not isinstance(case.get("prompt"), str) or not case["prompt"]:
            raise ValueError(f"CASE_{index}_PROMPT_REQUIRED")
        if str(case.get("target_label") or "") not in ("A", "B", "C"):
            raise ValueError(f"CASE_{index}_OPAQUE_TARGET_CODE_REQUIRED")
        if not isinstance(case.get("seed"), int) or isinstance(case.get("seed"), bool):
            raise ValueError(f"CASE_{index}_INTEGER_SEED_REQUIRED")


def run(payload: dict[str, Any], cache_dir: Path) -> dict[str, Any]:
    validate_input(payload)
    (
        torch,
        transformers,
        snapshot,
        tokenizer,
        model,
        device,
        checkpoint_sha,
        tokenizer_sha,
        weight_manifest,
        _default_layer,
    ) = base.load_exact_runtime(cache_dir)

    layers = model.model.layers
    if LAYER >= len(layers) - 1:
        raise RuntimeError("LAYER20_NOT_NONTERMINAL")
    layer = layers[LAYER]
    token_ids, token_labels = base.resolve_token_triplet(tokenizer)
    vector = torch.tensor(payload["basis_vector_f32"], dtype=torch.float32, device=device)
    actual_vector_sha = base.tensor_sha(vector)
    if actual_vector_sha != payload["basis_vector_sha256"]:
        raise RuntimeError(f"BASIS_VECTOR_SHA256_MISMATCH:{actual_vector_sha}")
    gain = float(payload["gain"])
    family = base.matched_family(torch, vector, gain)

    rows: list[dict[str, Any]] = []
    for case in payload["cases"]:
        prompt = case["prompt"]
        target = case["target_label"]
        seed = int(case["seed"])
        for scope in SCOPES:
            for control in base.CONTROLS:
                intervention = family[control].to(device)
                hook_calls = 0

                def hook(_module: Any, _inputs: Any, output: Any):
                    nonlocal hook_calls
                    hook_calls += 1
                    if control == "BASELINE":
                        return output
                    return apply_vector(output, intervention, scope)

                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed_all(seed)
                inputs = tokenizer(prompt, return_tensors="pt")
                inputs = {k: v.to(device) for k, v in inputs.items()}
                handle = layer.register_forward_hook(hook)
                try:
                    with torch.no_grad():
                        output = model(**inputs)
                        logits = output.logits[0, -1].float().detach().cpu()
                finally:
                    handle.remove()
                trio = {label: float(logits[token_id]) for label, token_id in token_ids.items()}
                others = [label for label in ("A", "B", "C") if label != target]
                score = trio[target] - 0.5 * (trio[others[0]] + trio[others[1]])
                material = {
                    "condition": scope,
                    "case_identity_sha256": case["case_identity_sha256"],
                    "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "control": control,
                    "basis_vector_sha256": payload["basis_vector_sha256"],
                    "applied_vector_sha256": base.tensor_sha(intervention),
                    "layer": LAYER,
                    "gain": gain,
                    "target_score": score,
                    "target_label": target,
                    "token_logits": trio,
                    "intervention_scope": SCOPE_TEXT[scope],
                    "hook_calls": hook_calls,
                    "native_cvec_rc": None,
                }
                rows.append({**material, "runtime_receipt_sha256": canonical_sha(material)})

    runtime = base.runtime_manifest(torch, transformers, model)
    core = {
        "schema": RESULT_SCHEMA,
        "source_input_sha256": canonical_sha(payload),
        "model_id": base.MODEL_ID,
        "model_revision": base.MODEL_REVISION,
        "checkpoint_manifest_sha256": checkpoint_sha,
        "tokenizer_json_sha256": tokenizer_sha,
        "runtime_build_sha256": canonical_sha(runtime),
        "layer": LAYER,
        "gain": gain,
        "basis_vector_sha256": payload["basis_vector_sha256"],
        "case_plan_sha256": payload["case_plan_sha256"],
        "control_family_sha256": payload["control_family_sha256"],
        "conditions": list(SCOPES),
        "observation_count": len(rows),
        "observations": rows,
        "native_rows_synthesized": False,
        "runtime_credit_minted": False,
        "canonical_semantics_promotion": False,
    }
    return {**core, "receipt_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--cache-dir", type=Path, required=True)
    args = ap.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = run(payload, args.cache_dir)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
