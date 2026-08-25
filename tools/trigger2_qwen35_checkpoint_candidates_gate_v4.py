#!/usr/bin/env python3
"""Fail-closed architecture hardening for Trigger-2 Qwen3.5 candidate gate v3.

Gate v3 correctly resolves checkpoint identity from bound receipts and normalizes the
Qwen3.5 text architecture from config.text_config. This successor adds one missing
source-integrity invariant: a measured candidate cannot remain source-valid when a
known bound architecture field is absent, null, ill-typed, or changed.

This is source-integrity only. Loader smoke is still not exact consumed-file/input
identity; consumed_identity_match remains UNKNOWN and no checkpoint/J-Space/training
credit is minted.
"""
from __future__ import annotations

import copy
import json
from typing import Any

import trigger2_qwen35_checkpoint_candidates_gate_v3 as v3

GATE_SCHEMA = "CLAY_TRIGGER2_QWEN35_CHECKPOINT_CANDIDATES_GATE/v4"

# These three bound candidates intentionally belong to one pinned Qwen3.5-0.8B text
# architecture family. Exact values come from their immutable checkpoint identity
# receipts; changing model family requires a new versioned gate rather than weakening
# this invariant.
EXPECTED_ARCHITECTURE = {
    "model_type": "qwen3_5",
    "text_model_type": "qwen3_5_text",
    "num_hidden_layers": 24,
    "hidden_size": 1024,
    "num_attention_heads": 8,
    "num_key_value_heads": 2,
    "vocab_size": 248320,
    "max_position_embeddings": 262144,
    "architectures": ["Qwen3_5ForConditionalGeneration"],
}


def _architecture_complete(identity: Any) -> bool:
    if not isinstance(identity, dict):
        return False
    arch = v3._normalized_architecture(identity)
    if not isinstance(arch, dict):
        return False

    for key in ("model_type", "text_model_type"):
        value = arch.get(key)
        if not isinstance(value, str) or value != EXPECTED_ARCHITECTURE[key]:
            return False

    for key in (
        "num_hidden_layers",
        "hidden_size",
        "num_attention_heads",
        "num_key_value_heads",
        "vocab_size",
        "max_position_embeddings",
    ):
        value = arch.get(key)
        # bool is an int subclass and must not satisfy a numeric architecture field.
        if isinstance(value, bool) or not isinstance(value, int):
            return False
        if value <= 0 or value != EXPECTED_ARCHITECTURE[key]:
            return False

    architectures = arch.get("architectures")
    if (
        not isinstance(architectures, list)
        or not architectures
        or any(not isinstance(x, str) or not x for x in architectures)
        or architectures != EXPECTED_ARCHITECTURE["architectures"]
    ):
        return False
    return True


def adjudicate(
    x: Any,
    identities: dict[str, dict[str, Any]] | None = None,
    loaders: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if identities is None or loaders is None:
        loaded_identities, loaded_loaders = v3.load_bound_receipts()
        identities = loaded_identities if identities is None else identities
        loaders = loaded_loaders if loaders is None else loaders

    result = copy.deepcopy(v3.adjudicate(x, identities=identities, loaders=loaders))
    failures = set(result.get("failures", []))

    candidates: dict[str, dict[str, Any]] = {}
    if isinstance(x, dict) and isinstance(x.get("candidates"), list):
        for candidate in x["candidates"]:
            if isinstance(candidate, dict) and isinstance(candidate.get("candidate_id"), str):
                candidates[candidate["candidate_id"]] = candidate

    for cid in v3.BOUND_MEASURED:
        identity = identities.get(cid)
        if not _architecture_complete(identity):
            failures.add("BOUND_ARCHITECTURE_INCOMPLETE:" + cid)

        # v3 correctly interprets selection_eligible as matched-baseline participation,
        # not winner eligibility. For the three preregistered measured arms, mutating it
        # to false silently changes the experiment and must fail source integrity.
        candidate = candidates.get(cid)
        if not isinstance(candidate, dict) or candidate.get("selection_eligible") is not True:
            failures.add("BOUND_MATCHED_BASELINE_PARTICIPATION_REQUIRED:" + cid)

    failures = sorted(failures)
    result["schema"] = GATE_SCHEMA
    result["failures"] = failures
    result["pass"] = not failures
    result["registry_source_integrity_valid"] = not failures
    result["selection_ready"] = False
    result["checkpoint_winner"] = None
    result["runtime_credit_minted"] = False
    result["jspace_credit_minted"] = False
    result["training_credit_minted"] = False
    result["checkpoint_winner_credit_minted"] = False
    result["bound_architecture_contract"] = EXPECTED_ARCHITECTURE
    result["evidence_boundary"] = (
        "PASS means registry + bound checkpoint/loader-smoke receipts are source-integrity "
        "consistent and the known Qwen3.5 text architecture is complete. It does not prove "
        "the exact consumed weight set or rendered/tokenized model input, does not close "
        "consumed_identity_match, does not run the matched pilot, and selects no winner."
    )
    return result


if __name__ == "__main__":
    registry_path = (
        v3.ROOT
        / "research_entity/global/j-space/research/trigger2_qwen35_08b_checkpoint_candidates_v2.json"
    )
    with registry_path.open(encoding="utf-8") as fh:
        registry = json.load(fh)
    print(json.dumps(adjudicate(registry), indent=2, sort_keys=True))
