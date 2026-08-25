#!/usr/bin/env python3
"""Fail-closed visible-prompt <-> audit-metadata gate for Trigger-2 binder v2.

This is a supplementary source validator, not a competing generator. It closes a
specific gap in the retained v2 validator: codebook mapping/display order and row
content must be authenticated from the actual model-visible prompt bytes, not only
from self-consistent audit metadata.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import re
from typing import Any, Iterable

CLASSES = ("ALLOW", "DENY", "ABSTAIN")
SLOTS = ("<ABI_SLOT_0>", "<ABI_SLOT_1>", "<ABI_SLOT_2>")
S3 = tuple(itertools.permutations(range(3)))
DISPLAY_ORDERS = tuple(itertools.permutations(CLASSES))
SCHEMA = "CLAY_TRIGGER2_PROMPT_METADATA_GATE/v1"


def _canonical_row_without_digest(row: dict[str, Any]) -> bytes:
    payload = dict(row)
    payload.pop("row_sha256", None)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def recompute_row_sha256(row: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_row_without_digest(row)).hexdigest()


def parse_visible_codebook(prompt: str) -> tuple[dict[str, str], tuple[str, str, str]]:
    if not isinstance(prompt, str):
        raise ValueError("prompt must be string")
    matches = list(re.finditer(r"(?:^|\n)CODEBOOK\n(.*?)\nEND_CODEBOOK(?:\n|$)", prompt, flags=re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one visible codebook, got {len(matches)}")
    mapping: dict[str, str] = {}
    order: list[str] = []
    for line in matches[0].group(1).splitlines():
        lhs, sep, rhs = line.partition("->")
        if not sep:
            raise ValueError("malformed codebook line")
        lhs, rhs = lhs.strip(), rhs.strip()
        if lhs not in CLASSES or rhs not in SLOTS or lhs in mapping:
            raise ValueError("invalid class/symbol codebook entry")
        mapping[lhs] = rhs
        order.append(lhs)
    if set(mapping) != set(CLASSES) or len(order) != 3 or len(set(mapping.values())) != 3:
        raise ValueError("codebook must be injective over exactly three classes and slots")
    return mapping, tuple(order)


def adjudicate(row: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    try:
        visible_mapping, visible_order = parse_visible_codebook(row.get("prompt"))

        perm = tuple(row.get("s3_permutation", ()))
        if perm not in S3:
            failures.append("S3_PERMUTATION_INVALID")
            expected_mapping = None
        else:
            expected_mapping = {CLASSES[i]: SLOTS[perm[i]] for i in range(3)}
            if row.get("s3_permutation_id") != f"P{S3.index(perm)}":
                failures.append("S3_PERMUTATION_ID_MISMATCH")

        declared_mapping = row.get("realized_mapping")
        if visible_mapping != declared_mapping:
            failures.append("VISIBLE_CODEBOOK_MAPPING_METADATA_MISMATCH")
        if expected_mapping is not None and visible_mapping != expected_mapping:
            failures.append("VISIBLE_CODEBOOK_MAPPING_NOT_CAUSAL_FROM_S3")

        declared_order = tuple(row.get("display_order", ()))
        if declared_order not in DISPLAY_ORDERS:
            failures.append("DISPLAY_ORDER_METADATA_INVALID")
        elif row.get("display_order_id") != f"O{DISPLAY_ORDERS.index(declared_order)}":
            failures.append("DISPLAY_ORDER_ID_MISMATCH")
        if visible_order != declared_order:
            failures.append("VISIBLE_CODEBOOK_ORDER_METADATA_MISMATCH")

        target_class = row.get("audit_target_semantic_class")
        if target_class not in CLASSES:
            failures.append("AUDIT_TARGET_CLASS_INVALID")
        elif row.get("target") != visible_mapping[target_class]:
            failures.append("TARGET_NOT_DERIVED_FROM_VISIBLE_CODEBOOK")

        claimed_sha = row.get("row_sha256")
        actual_sha = recompute_row_sha256(row)
        if not isinstance(claimed_sha, str) or claimed_sha != actual_sha:
            failures.append("ROW_SHA256_MISMATCH")
    except Exception as exc:
        failures.append(f"PROMPT_METADATA_PARSE_FAILURE:{type(exc).__name__}:{exc}")

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
        "evidence_boundary": "Source/candidate prompt-metadata integrity only; no ABI materialization, model runtime, J-Space, HCU, EntityOS, or training credit.",
    }


def validate_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    results = [adjudicate(row) for row in rows]
    failures = [{"index": i, "failures": r["failures"]} for i, r in enumerate(results) if not r["pass"]]
    return {
        "schema": SCHEMA + "_BATCH",
        "pass": not failures,
        "rows_total": len(results),
        "rows_pass": len(results) - len(failures),
        "rows_fail": len(failures),
        "failures": failures,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
    }
