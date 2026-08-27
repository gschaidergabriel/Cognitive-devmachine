#!/usr/bin/env python3
"""Fail-closed tokenizer-ABI gate for Trigger-2 candidate rows.

Verifies that every Xeno/ClayCode atom a candidate row claims to use resolves
exactly against the measured atoms_index.json for the pinned target checkpoint
tokenizer. No guessed/invented token mappings are accepted.

SOURCE/CANDIDATE PRE-ADMISSION ONLY. Mints zero dataset/training/runtime credit.
Delegates no semantic authority; this only binds symbol -> token-id identity.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_TOKENIZER_ABI_GATE/v1"
ATOMS_INDEX_PATH = Path(__file__).resolve().parents[1] / "research_entity" / "global" / "j-space" / "artifacts" / "atoms_index.json"

EXPECTED_CHECKPOINT = "Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1"
EXPECTED_REVISION = "591852bda6e1979f59e4b0f5ee2919697b12e936"


def _load_atoms_index() -> dict[str, Any]:
    if not ATOMS_INDEX_PATH.exists():
        raise FileNotFoundError(f"atoms_index.json missing at {ATOMS_INDEX_PATH}")
    with open(ATOMS_INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []

    if not isinstance(row, dict):
        return {
            "schema": SCHEMA,
            "pass": False,
            "failures": ["ROW_NOT_DICT"],
            "accepted_dataset_tokens_minted": 0,
        }

    try:
        index = _load_atoms_index()
    except Exception as exc:
        return {
            "schema": SCHEMA,
            "pass": False,
            "failures": ["ATOMS_INDEX_UNAVAILABLE:" + type(exc).__name__],
            "accepted_dataset_tokens_minted": 0,
        }

    if index.get("checkpoint") != EXPECTED_CHECKPOINT or index.get("revision") != EXPECTED_REVISION:
        failures.append("ATOMS_INDEX_CHECKPOINT_OR_REVISION_MISMATCH")

    atoms_map = index.get("atoms")
    rejected = index.get("rejected_atoms", {})
    if not isinstance(atoms_map, dict) or not atoms_map:
        failures.append("ATOMS_INDEX_EMPTY_OR_MALFORMED")
        atoms_map = {}

    tokenizer_hash = row.get("tokenizer_files_sha256")
    if tokenizer_hash is not None and tokenizer_hash != index.get("tokenizer_files_sha256"):
        failures.append("TOKENIZER_HASH_MISMATCH")

    used = row.get("tokenizer_atoms_used")
    if not isinstance(used, list) or not used:
        failures.append("NO_TOKENIZER_ATOMS_USED_DECLARED")
        used = []

    resolved: dict[str, list[int]] = {}
    for sym in used:
        if not isinstance(sym, str):
            failures.append("ATOM_NOT_STRING:" + repr(sym))
            continue
        if sym in rejected:
            failures.append("ATOM_EXPLICITLY_REJECTED:" + sym)
            continue
        if sym not in atoms_map:
            failures.append("ATOM_UNKNOWN_NOT_IN_INDEX:" + sym)
            continue
        claimed_ids = row.get("tokenizer_atom_ids", {}).get(sym) if isinstance(row.get("tokenizer_atom_ids"), dict) else None
        measured_ids = atoms_map[sym]
        if claimed_ids is not None and claimed_ids != measured_ids:
            failures.append("ATOM_ID_MISMATCH:" + sym)
            continue
        resolved[sym] = measured_ids

    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": failures,
        "checkpoint": index.get("checkpoint"),
        "revision": index.get("revision"),
        "resolved_atoms": resolved,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(adjudicate(json.loads(sys.stdin.read())), indent=2))
