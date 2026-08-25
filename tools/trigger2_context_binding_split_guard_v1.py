#!/usr/bin/env python3
"""Fail-closed cross-split guard for Trigger-2 context-binding candidates.

This guard exists because a row-level candidate gate cannot prove that TRAIN,
VALIDATION and HOLDOUT are semantically or symbolically disjoint. It checks
obvious cross-split leakage in model-visible semantic surfaces, template-family
reuse, exact family/provenance reuse, and holdout atom reuse.

Passing this guard does NOT establish statistical independence or training
readiness. It mints no dataset/model/J-Space/HCU/EntityOS credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_CONTEXT_BINDING_SPLIT_GUARD/v1"
SPLITS = ("TRAIN", "VALIDATION", "HOLDOUT")
_CODEBOOK = re.compile(r"CODEBOOK\n.*?\nEND_CODEBOOK", re.DOTALL)
_WS = re.compile(r"\s+")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def model_visible_semantic_surface(prompt: str) -> str:
    """Remove the episode-local codebook and normalize the remaining model text.

    The codebook is intentionally removed because different symbol assignments
    must not hide identical semantic/template text reused across data splits.
    """
    if not isinstance(prompt, str):
        raise ValueError("prompt must be string")
    if not _CODEBOOK.search(prompt):
        raise ValueError("delimited CODEBOOK/END_CODEBOOK span required")
    stripped = _CODEBOOK.sub("<CODEBOOK_REDACTED>", prompt)
    return _WS.sub(" ", stripped).strip().casefold()


def _set_from_meta(rows: Iterable[dict[str, Any]], key: str) -> set[str]:
    out: set[str] = set()
    for row in rows:
        meta = row.get("curriculum")
        if isinstance(meta, dict):
            value = meta.get(key)
            if isinstance(value, str) and value:
                out.add(value)
    return out


def _atom_ids(rows: Iterable[dict[str, Any]]) -> set[int]:
    out: set[int] = set()
    for row in rows:
        meta = row.get("curriculum")
        if not isinstance(meta, dict):
            continue
        ids = meta.get("atom_token_ids")
        if isinstance(ids, list):
            out.update(x for x in ids if isinstance(x, int))
    return out


def adjudicate(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(rows)
    failures: list[str] = []
    by_split: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for i, row in enumerate(rows):
        split = row.get("split")
        if split not in SPLITS:
            failures.append(f"INVALID_SPLIT:{i}")
            continue
        by_split[split].append(row)

    missing = [s for s in SPLITS if not by_split.get(s)]
    if missing:
        failures.append("MISSING_SPLITS:" + ",".join(missing))

    semantic_hashes: dict[str, set[str]] = {s: set() for s in SPLITS}
    for split in SPLITS:
        for i, row in enumerate(by_split.get(split, [])):
            try:
                surface = model_visible_semantic_surface(row.get("prompt"))
            except Exception as exc:
                failures.append(f"SEMANTIC_SURFACE_PARSE_FAIL:{split}:{i}:{type(exc).__name__}")
                continue
            semantic_hashes[split].add(_sha(surface))

    pair_summaries: list[dict[str, Any]] = []
    for a, b in (("TRAIN", "VALIDATION"), ("TRAIN", "HOLDOUT"), ("VALIDATION", "HOLDOUT")):
        overlap = sorted(semantic_hashes[a] & semantic_hashes[b])
        if overlap:
            failures.append(f"MODEL_VISIBLE_SEMANTIC_OVERLAP:{a}:{b}:{len(overlap)}")
        templates_a = _set_from_meta(by_split.get(a, []), "template_family")
        templates_b = _set_from_meta(by_split.get(b, []), "template_family")
        template_overlap = sorted(templates_a & templates_b)
        if template_overlap:
            failures.append(f"TEMPLATE_FAMILY_OVERLAP:{a}:{b}:{','.join(template_overlap)}")
        fam_a = {str(r.get("family_id")) for r in by_split.get(a, []) if r.get("family_id")}
        fam_b = {str(r.get("family_id")) for r in by_split.get(b, []) if r.get("family_id")}
        fam_overlap = sorted(fam_a & fam_b)
        if fam_overlap:
            failures.append(f"FAMILY_ID_OVERLAP:{a}:{b}:{len(fam_overlap)}")
        prov_a = {str(r.get("provenance_ancestry_id")) for r in by_split.get(a, []) if r.get("provenance_ancestry_id")}
        prov_b = {str(r.get("provenance_ancestry_id")) for r in by_split.get(b, []) if r.get("provenance_ancestry_id")}
        prov_overlap = sorted(prov_a & prov_b)
        if prov_overlap:
            failures.append(f"PROVENANCE_ANCESTRY_ID_OVERLAP:{a}:{b}:{len(prov_overlap)}")
        pair_summaries.append({
            "pair": [a, b],
            "semantic_surface_overlap_count": len(overlap),
            "template_family_overlap": template_overlap,
            "family_id_overlap_count": len(fam_overlap),
            "provenance_ancestry_id_overlap_count": len(prov_overlap),
        })

    holdout_atoms = _atom_ids(by_split.get("HOLDOUT", []))
    for prior in ("TRAIN", "VALIDATION"):
        overlap = sorted(holdout_atoms & _atom_ids(by_split.get(prior, [])))
        if overlap:
            failures.append(f"HOLDOUT_ATOM_REUSE:{prior}:HOLDOUT:{len(overlap)}")

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "rows_by_split": {s: len(by_split.get(s, [])) for s in SPLITS},
        "semantic_surface_hashes_by_split": {s: len(semantic_hashes[s]) for s in SPLITS},
        "pair_summaries": pair_summaries,
        "holdout_atom_count": len(holdout_atoms),
        "canonical_dataset_write_performed": False,
        "independence_credit_minted": False,
        "training_credit_minted": False,
        "evidence_boundary": (
            "Cross-split leakage guard only. PASS rejects several obvious leakage modes but does not prove "
            "statistical independence, unseen-template validity, tokenizer/ABI correctness, model behavior, or training readiness."
        ),
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"row {lineno} is not an object")
        out.append(obj)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--audit-out", type=Path)
    args = p.parse_args()
    rows: list[dict[str, Any]] = []
    for path in args.paths:
        rows.extend(load_jsonl(path))
    result = adjudicate(rows)
    encoded = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True)
    if args.audit_out:
        args.audit_out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
