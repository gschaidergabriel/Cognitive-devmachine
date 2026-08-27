"""XENO_DIAGNOSTIC_SPECIALIST_WRAPPER/v1 -- honest diagnostic-tier shell increment.

Scope and honesty, read before using this module:

This is NOT the XENO_MODEL_SLOT/v1 contract (see xeno_shell_model_slot_v1.py). That
module correctly refuses to bind a checkpoint without a real, already-measured
identity receipt under research_entity/global/j-space/research/vps_run_receipts/ --
vector ABI binding, hook registry, loader receipts, the works. The 2026-08-27
Together diagnostic run (huihui-ai/Huihui-Qwen3.5-0.8B-abliterated base + a LoRA
adapter trained on B0-B6 candidate data, see research_entity/topic_packets/
trigger2-together-diagnostic-finetune-20260827/) has NO such receipt. Fabricating
one would mean inventing HRR/vector-ABI measurements that were never taken. This
module does not do that.

What this module actually is: the "specialist wrapper" half of the
"0.8B stays the cognitive core, deterministic policy/scripts wrap and control it"
principle, scoped to exactly what can be honestly built today:

1. Loads the actual trained artifact (base + adapter) for generation.
2. Validates every raw generation against the ACTUAL trained output vocabulary --
   extracted directly from the real target field of all 16 B0-B6 training files
   used in the diagnostic run (not the aspirational 46-symbol production alphabet
   from XENO_SHELL_MASTER_SPEC.md SS7, which this diagnostic model was never
   trained on).
3. Fails closed on anything outside that vocabulary -- most notably the exact
   code-block derailment failure mode found in the 2026-08-27 holdout test
   (B3 multi-hop-dereference prompts produced ```cpp/```python blocks instead of
   an atom). Those get REJECTED here, not passed through as if they were a valid
   candidate. This directly implements Master Spec SS3 ("the shell MUST NOT
   rewrite a candidate because it probably means...") and SS19 ("fail closed on
   ... unknown atom/token mismatch").
4. Wraps validated (or rejected) output in the existing, unmodified
   COGNITIVE_RESULT_PACKET/v1 schema from xeno_shell_packets_v1.py -- result_class
   is always CANDIDATE (a MODEL producer is structurally forbidden from minting
   DETERMINISTIC_CONTROL_RESULT or EFFECT_RECEIPT, enforced by that module, not
   re-implemented here) whether the raw output validated or not; a rejection is a
   CANDIDATE payload with validated=false and a reason, never silently dropped and
   never promoted to a stronger class.

What this module deliberately does NOT do: does not touch S0/S1, does not claim
GRID10/lease/coordinator behavior, does not judge whether a *validated* atom is
the *correct* answer (that is the training/eval question the holdout test already
answers honestly at 2/12 -- this shell layer only judges "is this a well-formed
atom from the trained alphabet", never "is this the right one").
"""
from __future__ import annotations

import re
from typing import Any

from xeno_shell_packets_v1 import build_result_packet, digest

WRAPPER_SCHEMA = "XENO_DIAGNOSTIC_SPECIALIST_WRAPPER/v1"

# Ground truth: extracted directly from the `target` field of every row in the
# 16 B0-B6 training files actually used by the 2026-08-27 Together diagnostic run
# (research_entity/topic_packets/trigger2-together-diagnostic-finetune-20260827/
# PACKET.json "source_files_included"). Not guessed, not the aspirational SS7
# alphabet. Regenerate by re-scanning those files if the training set changes.
TRAINED_ORDINAL_PATTERN = re.compile(r"^ABI_ACCEPTED_ORDINAL:(\d+)$")
TRAINED_ORDINAL_MIN = 0
TRAINED_ORDINAL_MAX = 299

TRAINED_CLASS_WORDS = frozenset({
    "ALLOW", "DENY", "ABSTAIN",
    "STALE_REJECTED", "UNRESOLVABLE",
    "CLAUDE_ASSERTION", "EXTERNAL_TOOL_RECEIPT", "CANONICAL_LEDGER_EVIDENCE",
    "STALE_MISMATCHED_HANDOFF", "CANONICAL_DB", "SIMULATED_HYPOTHESIS",
    "STALE_REBASE_REQUIRED",
    "R", "P", "Q",
    "alpha", "beta", "gamma",
    "PRESERVE_BRANCHES", "COLLAPSE_VALID",
})


def validate_raw_output(raw: str) -> tuple[bool, str]:
    """Pure, offline, no model/network involved. Returns (is_valid, atom_or_reason).

    is_valid=True  -> atom_or_reason is the exact validated atom string.
    is_valid=False -> atom_or_reason is a short machine-readable rejection code.
    """
    if raw is None:
        return False, "EMPTY_OUTPUT"
    text = raw.strip()
    if not text:
        return False, "EMPTY_OUTPUT"

    m = TRAINED_ORDINAL_PATTERN.match(text)
    if m:
        n = int(m.group(1))
        if TRAINED_ORDINAL_MIN <= n <= TRAINED_ORDINAL_MAX:
            return True, text
        return False, f"ORDINAL_OUT_OF_TRAINED_RANGE:{n}"

    if text in TRAINED_CLASS_WORDS:
        return True, text

    # The concrete failure mode from the 2026-08-27 holdout test: generic code
    # instead of an atom. Named explicitly rather than just falling through to
    # the generic "not in vocabulary" branch, so this specific, already-observed
    # failure is traceable in rejection reasons rather than looking like a new
    # unknown case each time it recurs.
    if text.startswith("```") or "#include" in text or "def " in text or "import " in text:
        return False, "CODE_BLOCK_DERAILMENT"

    return False, "NOT_IN_TRAINED_VOCABULARY"


def wrap_as_result_packet(
    *,
    raw_output: str,
    source_work_digest: str,
    unresolved_alternatives: list[Any] | None = None,
) -> dict[str, Any]:
    """Always CANDIDATE, always through the real, unmodified packet schema.
    A rejection is a payload with validated=false -- never dropped, never
    silently upgraded to a stronger result class."""
    is_valid, atom_or_reason = validate_raw_output(raw_output)
    payload = {
        "raw_output": raw_output,
        "validated": is_valid,
        "atom": atom_or_reason if is_valid else None,
        "rejection_reason": None if is_valid else atom_or_reason,
        "wrapper_schema": WRAPPER_SCHEMA,
    }
    return build_result_packet(
        result_class="CANDIDATE",
        producer="MODEL",
        source_work_digest=source_work_digest,
        payload=payload,
        unresolved_alternatives=unresolved_alternatives,
    )


def load_diagnostic_model():
    """I/O + network + torch, deliberately kept out of validate_raw_output /
    wrap_as_result_packet so those stay fast, offline, and unit-testable.
    Mirrors research_entity/topic_packets/trigger2-together-diagnostic-finetune-
    20260827/holdout_inference_script_20260827.py exactly (same base, same
    revision, same adapter loading path) -- not a second, drifted copy of that
    logic, just factored so a shell caller can reuse it."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    BASE = "huihui-ai/Huihui-Qwen3.5-0.8B-abliterated"
    BASE_REV = "4813135658fe51b2e535b8e77927d2f23909ce42"
    ADAPTER_DIR = "/workspace/trigger2_diag_adapter"

    tok = AutoTokenizer.from_pretrained(BASE, revision=BASE_REV)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE, revision=BASE_REV, torch_dtype=torch.bfloat16, low_cpu_mem_usage=True
    )
    model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
    model.eval()
    return model, tok


def generate_and_validate(model, tok, prompt: str, *, source_work_digest: str) -> dict[str, Any]:
    """The actual specialist call: generate once, validate, wrap. No retries, no
    'fixing up' a bad generation -- a rejected candidate is reported as rejected."""
    import torch

    messages = [{"role": "user", "content": prompt}]
    input_ids = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt")
    if hasattr(input_ids, "input_ids"):
        input_ids = input_ids.input_ids
    with torch.no_grad():
        out = model.generate(
            input_ids,
            max_new_tokens=24,
            do_sample=False,
            pad_token_id=tok.pad_token_id or tok.eos_token_id,
        )
    gen_ids = out[0][input_ids.shape[1]:]
    raw = tok.decode(gen_ids, skip_special_tokens=True).strip()
    return wrap_as_result_packet(raw_output=raw, source_work_digest=source_work_digest)
