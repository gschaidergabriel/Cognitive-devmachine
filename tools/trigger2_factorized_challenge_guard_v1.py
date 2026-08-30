#!/usr/bin/env python3
"""Policy-aware factorized holdout guard for Trigger-2 binding datasets.

The guard distinguishes single-factor OOD challenges from joint OOD. A blanket
"no template overlap across splits" rule cannot validate symbol-only generalization,
because symbol-only evaluation intentionally keeps higher-level template and lexical
families familiar while changing only the atom identities.

This tool checks metadata relationships only. PASS does not mint dataset, model,
J-Space, HCU, EntityOS, or training credit.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_FACTORIZED_CHALLENGE_GUARD/v1"
SPLITS = ("TRAIN", "VALIDATION", "HOLDOUT")
AXES = ("SYMBOL_ONLY", "TEMPLATE_ONLY", "LEXICON_ONLY", "JOINT_OOD")


def _curriculum(row: dict[str, Any]) -> dict[str, Any]:
    c = row.get("curriculum")
    if not isinstance(c, dict):
        raise ValueError("curriculum metadata required")
    return c


def _str(c: dict[str, Any], key: str) -> str:
    v = c.get(key)
    if not isinstance(v, str) or not v:
        raise ValueError(f"curriculum.{key} required")
    return v


def _atoms(c: dict[str, Any]) -> frozenset[int]:
    v = c.get("atom_token_ids")
    if not isinstance(v, list) or not v or any(not isinstance(x, int) for x in v):
        raise ValueError("curriculum.atom_token_ids must be a nonempty integer list")
    if len(v) != len(set(v)):
        raise ValueError("curriculum.atom_token_ids must be unique")
    return frozenset(v)


def _surface(c: dict[str, Any]) -> str:
    v = _str(c, "semantic_surface_sha256").lower()
    if len(v) != 64 or any(ch not in "0123456789abcdef" for ch in v):
        raise ValueError("curriculum.semantic_surface_sha256 must be 64 lowercase hex chars")
    return v


def _meta(rows: Iterable[dict[str, Any]]) -> dict[str, set[Any]]:
    out: dict[str, set[Any]] = {
        "template_family": set(),
        "lexical_family": set(),
        "atom_token_ids": set(),
        "semantic_surface_sha256": set(),
        "family_id": set(),
        "provenance_ancestry_id": set(),
    }
    for row in rows:
        c = _curriculum(row)
        out["template_family"].add(_str(c, "template_family"))
        out["lexical_family"].add(_str(c, "lexical_family"))
        out["atom_token_ids"].update(_atoms(c))
        out["semantic_surface_sha256"].add(_surface(c))
        family = row.get("family_id")
        prov = row.get("provenance_ancestry_id")
        if not isinstance(family, str) or not family:
            raise ValueError("family_id required")
        if not isinstance(prov, str) or not prov:
            raise ValueError("provenance_ancestry_id required")
        out["family_id"].add(family)
        out["provenance_ancestry_id"].add(prov)
    return out


def _empty_meta() -> dict[str, set[Any]]:
    return {
        "template_family": set(),
        "lexical_family": set(),
        "atom_token_ids": set(),
        "semantic_surface_sha256": set(),
        "family_id": set(),
        "provenance_ancestry_id": set(),
    }


def _require_subset(name: str, got: set[Any], reference: set[Any], failures: list[str]) -> None:
    extra = got - reference
    if extra:
        failures.append(f"{name}_MUST_BE_FAMILIAR:{len(extra)}")


def _require_disjoint(name: str, got: set[Any], reference: set[Any], failures: list[str]) -> None:
    overlap = got & reference
    if overlap:
        failures.append(f"{name}_MUST_BE_UNSEEN:{len(overlap)}")


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
        axis = row.get("challenge_axis")
        if split == "HOLDOUT":
            if axis not in AXES:
                failures.append(f"HOLDOUT_AXIS_REQUIRED:{i}")
        elif axis not in (None, "", "REFERENCE"):
            failures.append(f"CHALLENGE_AXIS_OUTSIDE_HOLDOUT:{i}")

    if not by_split["TRAIN"]:
        failures.append("MISSING_SPLIT:TRAIN")
    if not by_split["HOLDOUT"]:
        failures.append("MISSING_SPLIT:HOLDOUT")

    parsed_meta: dict[str, dict[str, set[Any]]] = {}
    for split in SPLITS:
        try:
            parsed_meta[split] = _meta(by_split[split]) if by_split[split] else _empty_meta()
        except Exception as exc:
            failures.append(f"META_PARSE_FAIL:{split}:{type(exc).__name__}:{exc}")
            parsed_meta[split] = _empty_meta()

    # Exact semantic episodes and family/provenance identities never cross splits.
    for a, b in (("TRAIN", "VALIDATION"), ("TRAIN", "HOLDOUT"), ("VALIDATION", "HOLDOUT")):
        if parsed_meta[a]["semantic_surface_sha256"] & parsed_meta[b]["semantic_surface_sha256"]:
            failures.append(f"EXACT_SEMANTIC_SURFACE_OVERLAP:{a}:{b}")
        if parsed_meta[a]["family_id"] & parsed_meta[b]["family_id"]:
            failures.append(f"FAMILY_ID_OVERLAP:{a}:{b}")
        if parsed_meta[a]["provenance_ancestry_id"] & parsed_meta[b]["provenance_ancestry_id"]:
            failures.append(f"PROVENANCE_ANCESTRY_OVERLAP:{a}:{b}")

    train = parsed_meta["TRAIN"]
    preholdout = {
        k: parsed_meta["TRAIN"][k] | parsed_meta["VALIDATION"][k]
        for k in ("template_family", "lexical_family", "atom_token_ids")
    }

    axis_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in by_split["HOLDOUT"]:
        axis = row.get("challenge_axis")
        if axis in AXES:
            axis_rows[axis].append(row)

    axis_summary: dict[str, Any] = {}
    for axis, subset in sorted(axis_rows.items()):
        try:
            m = _meta(subset)
        except Exception as exc:
            failures.append(f"AXIS_META_PARSE_FAIL:{axis}:{type(exc).__name__}:{exc}")
            continue
        local_failures: list[str] = []
        if axis == "SYMBOL_ONLY":
            _require_subset("TEMPLATE", m["template_family"], train["template_family"], local_failures)
            _require_subset("LEXICON", m["lexical_family"], train["lexical_family"], local_failures)
            _require_disjoint("ATOM", m["atom_token_ids"], preholdout["atom_token_ids"], local_failures)
        elif axis == "TEMPLATE_ONLY":
            _require_disjoint("TEMPLATE", m["template_family"], preholdout["template_family"], local_failures)
            _require_subset("LEXICON", m["lexical_family"], train["lexical_family"], local_failures)
            _require_subset("ATOM", m["atom_token_ids"], train["atom_token_ids"], local_failures)
        elif axis == "LEXICON_ONLY":
            _require_subset("TEMPLATE", m["template_family"], train["template_family"], local_failures)
            _require_disjoint("LEXICON", m["lexical_family"], preholdout["lexical_family"], local_failures)
            _require_subset("ATOM", m["atom_token_ids"], train["atom_token_ids"], local_failures)
        elif axis == "JOINT_OOD":
            _require_disjoint("TEMPLATE", m["template_family"], preholdout["template_family"], local_failures)
            _require_disjoint("LEXICON", m["lexical_family"], preholdout["lexical_family"], local_failures)
            _require_disjoint("ATOM", m["atom_token_ids"], preholdout["atom_token_ids"], local_failures)
        failures.extend(f"{axis}:{x}" for x in local_failures)
        axis_summary[axis] = {
            "rows": len(subset),
            "template_families": sorted(m["template_family"]),
            "lexical_families": sorted(m["lexical_family"]),
            "atom_token_ids": sorted(m["atom_token_ids"]),
            "policy_failures": local_failures,
        }

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "rows_by_split": {s: len(by_split[s]) for s in SPLITS},
        "challenge_axes_present": sorted(axis_rows),
        "axis_summary": axis_summary,
        "dataset_credit_minted": False,
        "training_credit_minted": False,
        "jspace_credit_minted": False,
        "runtime_credit_minted": False,
        "evidence_boundary": (
            "Metadata-level factor-isolation guard only. PASS does not prove statistical independence, "
            "tokenizer/ABI correctness, model behavior, causal J-Space control, or training readiness."
        ),
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"{path}:{lineno}: object required")
        rows.append(obj)
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--audit-out", type=Path)
    args = p.parse_args()
    rows: list[dict[str, Any]] = []
    for path in args.paths:
        rows.extend(load_jsonl(path))
    result = adjudicate(rows)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.audit_out:
        args.audit_out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
