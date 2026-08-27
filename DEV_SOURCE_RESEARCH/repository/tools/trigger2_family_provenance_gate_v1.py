#!/usr/bin/env python3
"""Trigger-2 causal-family provenance / anti-echo gate v1.

Fail-closed component for train/calibration/holdout lineage separation. It collapses
repackaged-history/model/checkpoint echoes into one lineage root and rejects cross-split
family/ancestry overlap. PASS mints no dataset/training/runtime/HCU/EntityOS credit.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

SCHEMA = "CLAY_TRIGGER2_FAMILY_PROVENANCE_GATE/v1"
REQUIRED_SPLITS = {"TRAIN", "CALIBRATION", "HOLDOUT"}


def _canon(v: Any) -> bytes:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _digest(v: Any) -> str:
    return sha256(_canon(v)).hexdigest()


def _s(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _hex64(v: Any) -> bool:
    return isinstance(v, str) and len(v) == 64 and all(c in "0123456789abcdef" for c in v.lower())


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "family_provenance_pass": not failures,
        "failures": failures,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
    }
    out.update(extra)
    return out


def _root(p: dict[str, Any]) -> tuple[str, ...]:
    return (
        p["model_family"], p["checkpoint_sha256"].lower(), p["generator_family_id"],
        p["source_episode_root_id"], p["repackaged_history_root_id"],
    )


def adjudicate(bundle: Any) -> dict[str, Any]:
    """Validate one admission microbatch.

    Each row must expose evaluator-only provenance:
      row_id, split, causal_family_id,
      family_provenance_evaluator_only = {
        model_family, checkpoint_sha256, generator_family_id,
        source_episode_root_id, repackaged_history_root_id,
        parent_family_ids, lineage_digest
      }

    lineage_digest is recomputed from the other provenance fields. Cross-split overlap is
    rejected both by causal_family_id and by the anti-echo root, so renaming/repacking cannot
    manufacture independence. Missing/ambiguous ancestry fails closed.
    """
    if not isinstance(bundle, dict) or not isinstance(bundle.get("rows"), list):
        return _result(["BUNDLE_ROWS_LIST_REQUIRED"])
    rows = bundle["rows"]
    if not rows:
        return _result(["NONEMPTY_ROWS_REQUIRED"])

    failures: list[str] = []
    by_family: dict[str, set[str]] = {}
    by_root: dict[tuple[str, ...], set[str]] = {}
    parents_by_family: dict[str, set[str]] = {}
    seen_rows: set[str] = set()
    normalized: list[dict[str, Any]] = []

    for i, row in enumerate(rows):
        tag = f"ROW[{i}]"
        if not isinstance(row, dict):
            failures.append(tag + ":OBJECT_REQUIRED")
            continue
        rid, split, fid = row.get("row_id"), row.get("split"), row.get("causal_family_id")
        p = row.get("family_provenance_evaluator_only")
        if not _s(rid): failures.append(tag + ":ROW_ID_REQUIRED")
        elif rid in seen_rows: failures.append(tag + ":DUPLICATE_ROW_ID")
        else: seen_rows.add(rid)
        if split not in REQUIRED_SPLITS: failures.append(tag + ":SPLIT_INVALID")
        if not _s(fid): failures.append(tag + ":CAUSAL_FAMILY_ID_REQUIRED")
        if not isinstance(p, dict):
            failures.append(tag + ":PROVENANCE_OBJECT_REQUIRED")
            continue

        required = (
            "model_family", "checkpoint_sha256", "generator_family_id",
            "source_episode_root_id", "repackaged_history_root_id",
            "parent_family_ids", "lineage_digest",
        )
        for k in required:
            if k not in p: failures.append(tag + ":MISSING_" + k.upper())
        if not _s(p.get("model_family")): failures.append(tag + ":MODEL_FAMILY_REQUIRED")
        if not _hex64(p.get("checkpoint_sha256")): failures.append(tag + ":CHECKPOINT_SHA256_INVALID")
        for k in ("generator_family_id", "source_episode_root_id", "repackaged_history_root_id"):
            if not _s(p.get(k)): failures.append(tag + ":" + k.upper() + "_REQUIRED")
        parents = p.get("parent_family_ids")
        if not isinstance(parents, list) or any(not _s(x) for x in parents):
            failures.append(tag + ":PARENT_FAMILY_IDS_INVALID")
            parents = []
        if _s(fid) and fid in parents: failures.append(tag + ":SELF_PARENT_FORBIDDEN")

        subject = {k: p.get(k) for k in required if k != "lineage_digest"}
        expected = _digest(subject)
        if p.get("lineage_digest") != expected:
            failures.append(tag + ":LINEAGE_DIGEST_MISMATCH")

        valid_root = (
            split in REQUIRED_SPLITS and _s(fid) and _s(p.get("model_family")) and
            _hex64(p.get("checkpoint_sha256")) and
            all(_s(p.get(k)) for k in ("generator_family_id", "source_episode_root_id", "repackaged_history_root_id"))
        )
        if valid_root:
            root = _root(p)
            by_family.setdefault(fid, set()).add(split)
            by_root.setdefault(root, set()).add(split)
            parents_by_family.setdefault(fid, set()).update(parents)
            normalized.append({"row_id": rid, "split": split, "causal_family_id": fid,
                               "anti_echo_root_digest": _digest(root), "lineage_digest": expected})

    present = {x["split"] for x in normalized}
    for split in sorted(REQUIRED_SPLITS - present): failures.append("MISSING_SPLIT:" + split)
    for fid, splits in by_family.items():
        if len(splits) > 1: failures.append("CAUSAL_FAMILY_CROSS_SPLIT:" + fid)
    for root, splits in by_root.items():
        if len(splits) > 1: failures.append("ANTI_ECHO_ROOT_CROSS_SPLIT:" + _digest(root))

    split_by_family = {fid: next(iter(s)) for fid, s in by_family.items() if len(s) == 1}
    for child, parents in parents_by_family.items():
        csplit = split_by_family.get(child)
        if csplit is None: continue
        for parent in parents:
            psplit = split_by_family.get(parent)
            if psplit is not None and psplit != csplit:
                failures.append(f"ANCESTRY_CROSS_SPLIT:{child}->{parent}")

    return _result(
        failures,
        rows_checked=len(rows),
        normalized_rows=len(normalized),
        required_splits=sorted(REQUIRED_SPLITS),
        present_splits=sorted(present),
        unique_causal_families=len(by_family),
        unique_anti_echo_roots=len(by_root),
        normalized_lineage=normalized,
        goodman_collapse_dimensions=["model_family", "checkpoint_sha256", "generator_family_id",
                                     "source_episode_root_id", "repackaged_history_root_id"],
        ambiguous_ancestry_fail_closed=True,
    )


if __name__ == "__main__":
    print(json.dumps({"schema": SCHEMA, "status": "SOURCE_COMPONENT_READY", "credit_minted": 0}, sort_keys=True))
