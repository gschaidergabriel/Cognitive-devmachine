#!/usr/bin/env python3
"""Fail-closed cross-split audit for Trigger-2 context-binding candidate rows.

Why this exists
---------------
`trigger2_context_binding_generator_v1.py` validates one generated row set well, but a
`split` label alone does not establish train/validation/holdout isolation. Independent
calls can reuse the same atoms, semantic variants, family structure and even the same
prompts while only changing split-tagged metadata.

This auditor therefore evaluates multiple rendered split files together. It is a dataset
construction guard, not model/runtime/training evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

SPLITS = ("TRAIN", "VALIDATION", "HOLDOUT")
SCHEMA = "CLAY_TRIGGER2_CONTEXT_BINDING_CROSS_SPLIT_AUDIT/v1"
_SPLIT_FAMILY_RE = re.compile(r"^CTX_BIND_(?:TRAIN|VALIDATION|HOLDOUT)_")


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"{path}:{lineno}: row must be object")
        rows.append(obj)
    return rows


def prompt_sha256(row: dict[str, Any]) -> str:
    prompt = row.get("prompt")
    if not isinstance(prompt, str):
        raise ValueError("row.prompt missing/non-string")
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def normalized_family_id(row: dict[str, Any]) -> str:
    family_id = row.get("family_id")
    if not isinstance(family_id, str) or not family_id:
        raise ValueError("row.family_id missing/non-string")
    # The generator v1 prefixes family IDs with the split. Remove that cosmetic prefix
    # before overlap comparison so a split label cannot manufacture family independence.
    return _SPLIT_FAMILY_RE.sub("CTX_BIND_", family_id)


def semantic_signature(row: dict[str, Any]) -> tuple[Any, ...]:
    meta = row.get("curriculum")
    if not isinstance(meta, dict):
        raise ValueError("row.curriculum missing/non-object")
    required = (
        "template_family",
        "query_polarity",
        "base_semantic_class",
        "lexical_variant_index",
    )
    if any(k not in meta for k in required):
        raise ValueError("curriculum lacks semantic-signature fields")
    return tuple(meta[k] for k in required)


def atom_token_ids(row: dict[str, Any]) -> set[int]:
    meta = row.get("curriculum")
    if not isinstance(meta, dict):
        raise ValueError("row.curriculum missing/non-object")
    ids = meta.get("atom_token_ids")
    if not isinstance(ids, list) or len(ids) != 3 or not all(isinstance(x, int) for x in ids):
        raise ValueError("curriculum.atom_token_ids must be three observed integer token IDs")
    return set(ids)


def provenance_without_split(row: dict[str, Any]) -> str:
    ancestry = row.get("provenance_ancestry_id")
    if not isinstance(ancestry, str) or not ancestry:
        raise ValueError("row.provenance_ancestry_id missing/non-string")
    # Generator v1 embeds ':TRAIN:' etc. Remove only that declared split segment.
    return re.sub(r":(?:TRAIN|VALIDATION|HOLDOUT):", ":<SPLIT>:", ancestry, count=1)


def _collect(rows: Iterable[dict[str, Any]]) -> dict[str, set[Any]]:
    prompts: set[str] = set()
    families: set[str] = set()
    semantics: set[tuple[Any, ...]] = set()
    atoms: set[int] = set()
    ancestry: set[str] = set()
    for row in rows:
        prompts.add(prompt_sha256(row))
        families.add(normalized_family_id(row))
        semantics.add(semantic_signature(row))
        atoms.update(atom_token_ids(row))
        ancestry.add(provenance_without_split(row))
    return {
        "prompt_sha256": prompts,
        "normalized_family": families,
        "semantic_signature": semantics,
        "atom_token_id": atoms,
        "normalized_provenance": ancestry,
    }


def audit_splits(split_rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    missing = [s for s in SPLITS if s not in split_rows]
    if missing:
        failures.append({"code": "MISSING_SPLITS", "splits": missing})

    collections: dict[str, dict[str, set[Any]]] = {}
    row_counts: dict[str, int] = {}
    parse_failures: list[str] = []

    for split in SPLITS:
        rows = split_rows.get(split, [])
        row_counts[split] = len(rows)
        for i, row in enumerate(rows):
            if row.get("split") != split:
                parse_failures.append(f"{split}:{i}:DECLARED_SPLIT_MISMATCH:{row.get('split')}")
        try:
            collections[split] = _collect(rows)
        except Exception as exc:
            parse_failures.append(f"{split}:COLLECT:{type(exc).__name__}:{exc}")
            collections[split] = {
                "prompt_sha256": set(),
                "normalized_family": set(),
                "semantic_signature": set(),
                "atom_token_id": set(),
                "normalized_provenance": set(),
            }

    if parse_failures:
        failures.append({"code": "ROW_OR_SCHEMA_FAILURE", "examples": parse_failures[:20]})

    pairwise: dict[str, Any] = {}
    for i, left in enumerate(SPLITS):
        for right in SPLITS[i + 1 :]:
            key = f"{left}__{right}"
            detail: dict[str, Any] = {}
            for field in (
                "prompt_sha256",
                "normalized_family",
                "semantic_signature",
                "atom_token_id",
                "normalized_provenance",
            ):
                overlap = collections[left][field] & collections[right][field]
                detail[field] = {
                    "overlap_count": len(overlap),
                    "examples": sorted(map(str, overlap))[:8],
                }
                if overlap:
                    failures.append(
                        {
                            "code": f"CROSS_SPLIT_{field.upper()}_OVERLAP",
                            "pair": key,
                            "count": len(overlap),
                        }
                    )
            pairwise[key] = detail

    # Holdout is the strictest boundary. Explicitly name its atom/family gate so downstream
    # tooling cannot treat a generic PASS as sufficient while these are unresolved.
    holdout_isolated = True
    for other in ("TRAIN", "VALIDATION"):
        if collections.get("HOLDOUT", {}).get("atom_token_id", set()) & collections.get(other, {}).get("atom_token_id", set()):
            holdout_isolated = False
        if collections.get("HOLDOUT", {}).get("normalized_family", set()) & collections.get(other, {}).get("normalized_family", set()):
            holdout_isolated = False
        if collections.get("HOLDOUT", {}).get("semantic_signature", set()) & collections.get(other, {}).get("semantic_signature", set()):
            holdout_isolated = False

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "status": "PASS" if not failures else "FAIL_CLOSED",
        "scope": "DATASET_CROSS_SPLIT_STATIC_AUDIT_ONLY",
        "row_counts": row_counts,
        "holdout_isolated_on_atom_family_semantic_axes": holdout_isolated,
        "pairwise": pairwise,
        "failures": failures,
        "law": (
            "A split label, split-prefixed family_id, or selected_using_holdout=false flag does not establish "
            "independent train/validation/holdout populations. Isolation must be demonstrated across rendered sets."
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--train", type=Path, required=True)
    p.add_argument("--validation", type=Path, required=True)
    p.add_argument("--holdout", type=Path, required=True)
    p.add_argument("--audit-out", type=Path)
    args = p.parse_args()

    report = audit_splits(
        {
            "TRAIN": load_jsonl(args.train),
            "VALIDATION": load_jsonl(args.validation),
            "HOLDOUT": load_jsonl(args.holdout),
        }
    )
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.audit_out:
        args.audit_out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
