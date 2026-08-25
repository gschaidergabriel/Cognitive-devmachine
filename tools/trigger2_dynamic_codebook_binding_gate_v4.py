#!/usr/bin/env python3
"""Trigger-2 binding gate v4: accepted-atom membership + source-archive closure.

v3 already binds exact provenance bytes, exact codebook order, holdout axes and an
exact-tokenizer atom-tokenization audit. v4 closes the remaining semantic provenance
hole: an atom can no longer pass merely because it appears in the tokenization audit.
Every episode atom and target must belong to a normalized exact 46-atom accepted ABI
inventory that is itself bound to the actual supplied Claude source archive and ABI
manifest. The tokenization audit atom set must exactly equal that accepted inventory.

Source/candidate validation only. No accepted dataset, model, training, J-Space, HCU or
EntityOS runtime credit is granted.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Callable

SCHEMA = "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_GATE/v4"
ROW_SCHEMA = "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_CANDIDATE/v4"
BASE_ROW_SCHEMA = "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_CANDIDATE/v3"
ATOM_INVENTORY_SCHEMA = "TRIGGER2_ACCEPTED_ATOM_INVENTORY/v1"
TOKEN_AUDIT_SCHEMA = "TRIGGER2_ATOM_TOKENIZATION_AUDIT/v1"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _load_base_validate() -> Callable:
    path = Path(__file__).with_name("trigger2_dynamic_codebook_binding_gate_v3.py")
    spec = importlib.util.spec_from_file_location("trigger2_binding_gate_v3_for_v4", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load required v3 base gate: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.validate


def _accepted_inventory(value, *, source_archive_sha256: str, abi_manifest_sha256: str):
    failures = []
    if not isinstance(value, dict) or value.get("schema") != ATOM_INVENTORY_SCHEMA:
        return set(), ["ATOM_INVENTORY_SCHEMA"]
    if value.get("source_archive_sha256") != source_archive_sha256:
        failures.append("ATOM_INVENTORY_SOURCE_ARCHIVE_BINDING")
    if value.get("abi_manifest_sha256") != abi_manifest_sha256:
        failures.append("ATOM_INVENTORY_ABI_MANIFEST_BINDING")
    if value.get("accepted_atom_count") != 46:
        failures.append("ATOM_INVENTORY_ACCEPTED_COUNT_46_REQUIRED")
    items = value.get("atoms")
    if not isinstance(items, list) or len(items) != 46:
        return set(), sorted(set(failures + ["ATOM_INVENTORY_ROWS_46_REQUIRED"]))
    atoms, source_rows = set(), set()
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            failures.append(f"ATOM_INVENTORY_ROW_OBJECT:{i}")
            continue
        atom, source_row = item.get("atom"), item.get("source_row")
        if not isinstance(atom, str) or not atom:
            failures.append(f"ATOM_INVENTORY_ATOM:{i}")
            continue
        if atom in atoms:
            failures.append("ATOM_INVENTORY_DUPLICATE_ATOM:" + atom)
        atoms.add(atom)
        if atom.casefold() == "or":
            failures.append("ATOM_INVENTORY_REJECTED_ATOM_OR_PRESENT")
        if not isinstance(source_row, int) or source_row < 0:
            failures.append(f"ATOM_INVENTORY_SOURCE_ROW:{i}")
        elif source_row in source_rows:
            failures.append(f"ATOM_INVENTORY_DUPLICATE_SOURCE_ROW:{source_row}")
        else:
            source_rows.add(source_row)
    if len(atoms) != 46:
        failures.append("ATOM_INVENTORY_UNIQUE_ACCEPTED_46_REQUIRED")
    return atoms, sorted(set(failures))


def _token_audit_atoms(value, *, tokenizer_identity_sha256: str):
    failures = []
    if not isinstance(value, dict) or value.get("schema") != TOKEN_AUDIT_SCHEMA:
        return set(), ["ATOM_TOKENIZATION_AUDIT_SCHEMA"]
    if value.get("tokenizer_identity_sha256") != tokenizer_identity_sha256:
        failures.append("ATOM_TOKENIZATION_AUDIT_TOKENIZER_BINDING")
    counts = value.get("atom_token_counts")
    if not isinstance(counts, dict):
        return set(), sorted(set(failures + ["ATOM_TOKENIZATION_AUDIT_COUNTS_REQUIRED"]))
    atoms = set()
    for atom, count in counts.items():
        if not isinstance(atom, str) or not atom or not isinstance(count, int) or count != 1:
            failures.append("ATOM_TOKENIZATION_AUDIT_SINGLE_TOKEN_REQUIRED:" + str(atom))
            continue
        atoms.add(atom)
    return atoms, sorted(set(failures))


def validate(
    rows: list[dict], forbidden_lexemes: list[str], expected_hashes: dict, atom_token_counts: dict,
    *, source_archive_path: Path, atom_inventory_path: Path, abi_manifest_path: Path,
    tokenizer_identity_path: Path, atom_tokenization_audit_path: Path,
    base_validate: Callable | None = None,
):
    global_failures, row_failures = [], []
    source_archive_sha = _sha256(source_archive_path)
    abi_sha = _sha256(abi_manifest_path)
    tokenizer_sha = _sha256(tokenizer_identity_path)
    token_audit_sha = _sha256(atom_tokenization_audit_path)
    atom_inventory_sha = _sha256(atom_inventory_path)

    try:
        inv = _load_json(atom_inventory_path)
    except Exception as exc:
        inv = {}
        global_failures.append("ATOM_INVENTORY_JSON_INVALID:" + type(exc).__name__)
    accepted, inv_fail = _accepted_inventory(
        inv, source_archive_sha256=source_archive_sha, abi_manifest_sha256=abi_sha
    )
    global_failures.extend(inv_fail)

    try:
        token_audit = _load_json(atom_tokenization_audit_path)
    except Exception as exc:
        token_audit = {}
        global_failures.append("ATOM_TOKENIZATION_AUDIT_JSON_INVALID:" + type(exc).__name__)
    audited, audit_fail = _token_audit_atoms(token_audit, tokenizer_identity_sha256=tokenizer_sha)
    global_failures.extend(audit_fail)
    if audited != accepted:
        if accepted - audited:
            global_failures.append("TOKEN_AUDIT_MISSING_ACCEPTED_ATOMS")
        if audited - accepted:
            global_failures.append("TOKEN_AUDIT_CONTAINS_NONACCEPTED_ATOMS")

    for i, row in enumerate(rows):
        fail = []
        if row.get("schema") != ROW_SCHEMA:
            fail.append("ROW_SCHEMA")
        if row.get("source_archive_sha256") != source_archive_sha:
            fail.append("PROVENANCE_BYTES_MISMATCH:source_archive_sha256")
        if row.get("atom_inventory_sha256") != atom_inventory_sha:
            fail.append("PROVENANCE_BYTES_MISMATCH:atom_inventory_sha256")
        if row.get("atom_tokenization_audit_sha256") != token_audit_sha:
            fail.append("PROVENANCE_BYTES_MISMATCH:atom_tokenization_audit_sha256")
        triplet = row.get("episode_atom_triplet")
        if isinstance(triplet, list):
            for atom in triplet:
                if not isinstance(atom, str) or atom not in accepted:
                    fail.append("ATOM_NOT_IN_VERIFIED_ACCEPTED_INVENTORY:" + str(atom))
        else:
            fail.append("ATOM_TRIPLET")
        target = row.get("target")
        if not isinstance(target, str) or target not in accepted:
            fail.append("TARGET_NOT_IN_VERIFIED_ACCEPTED_INVENTORY:" + str(target))
        if fail:
            row_failures.append({"row": i, "row_id": row.get("row_id"), "failures": sorted(set(fail))})

    projected = []
    for row in rows:
        x = copy.deepcopy(row)
        x["schema"] = BASE_ROW_SCHEMA
        projected.append(x)
    if base_validate is None:
        base_validate = _load_base_validate()
    base = base_validate(projected, forbidden_lexemes, expected_hashes, atom_token_counts)
    global_failures.extend(base.get("failures", []))
    row_failures.extend(base.get("row_failures", []))

    return {
        "schema": SCHEMA,
        "candidate_binding_gate_pass": not global_failures and not row_failures and bool(base.get("candidate_binding_gate_pass")),
        "failures": sorted(set(global_failures)),
        "row_failures": row_failures,
        "metrics": {
            "rows": len(rows),
            "verified_accepted_atoms": len(accepted),
            "verified_token_audit_atoms": len(audited),
            "source_archive_sha256": source_archive_sha,
            "v3": base.get("metrics", {}),
        },
        "credits": {
            "canonical_dataset_write": 0, "accepted_dataset_tokens": 0,
            "training_credit": 0, "jspace_model_runtime_credit": 0,
            "full_hcu_runtime_credit": 0, "whole_entityos_hcu_runtime_credit": 0,
        },
        "boundary": "Accepted-atom semantic provenance source/candidate validation only; no training admission.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", type=Path)
    ap.add_argument("--forbidden-lexemes", type=Path, required=True)
    ap.add_argument("--abi-manifest", type=Path, required=True)
    ap.add_argument("--atom-inventory", type=Path, required=True)
    ap.add_argument("--generator-source", type=Path, required=True)
    ap.add_argument("--model-identity", type=Path, required=True)
    ap.add_argument("--tokenizer-identity", type=Path, required=True)
    ap.add_argument("--atom-tokenization-audit", type=Path, required=True)
    ap.add_argument("--source-archive", type=Path, required=True)
    ns = ap.parse_args()
    paths = {
        "forbidden_lexemes": ns.forbidden_lexemes, "abi_manifest": ns.abi_manifest,
        "atom_inventory": ns.atom_inventory, "generator_source": ns.generator_source,
        "model_identity": ns.model_identity, "tokenizer_identity": ns.tokenizer_identity,
        "atom_tokenization_audit": ns.atom_tokenization_audit,
    }
    for p in [ns.jsonl, ns.source_archive, *paths.values()]:
        if not p.is_file():
            raise SystemExit(f"required input missing: {p}")
    lexemes = _load_json(ns.forbidden_lexemes)
    token_audit = _load_json(ns.atom_tokenization_audit)
    atom_token_counts = token_audit.get("atom_token_counts", {}) if isinstance(token_audit, dict) else {}
    expected_hashes = {name: _sha256(path) for name, path in paths.items()}
    rows = [json.loads(x) for x in ns.jsonl.read_text(encoding="utf-8").splitlines() if x.strip()]
    result = validate(
        rows, lexemes, expected_hashes, atom_token_counts,
        source_archive_path=ns.source_archive,
        atom_inventory_path=ns.atom_inventory,
        abi_manifest_path=ns.abi_manifest,
        tokenizer_identity_path=ns.tokenizer_identity,
        atom_tokenization_audit_path=ns.atom_tokenization_audit,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["candidate_binding_gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
