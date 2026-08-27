"""Build the run-4 Together fine-tune upload dataset (item 2 / gap-list bias fix, 2026-08-27).

Additive over run 3, same precedent as runs 1->2->3 (nothing that already worked is removed):
  run-3 dataset (10,216 TRAIN rows: v2-patched B0-B6 curriculum + Hyperposition expansion)
  PLUS the new TRIGGER2_B6_HYPERPOSITION_BIAS_FIX_CANDIDATE_V1.jsonl TRAIN rows (275)
  = run-4 dataset.

Source-of-truth family file selection (V2 where a patched version exists, else V1) mirrors
exactly what RUN3_PREPARATION_20260827.json documents was used for run 3's "v2-patched" 9544 rows,
reconstructed here from the committed source family files since the derived upload JSONL itself
was never committed (documented precedent -- only source families are committed, not the
Together-upload artifact).

Converts each row to Together's conversational fine-tune schema (same as runs 1-3):
  {"messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": target}]}
Only split=="TRAIN" rows are included (matches runs 1-3; VALIDATION/HOLDOUT_FROZEN rows are for
local evaluation only and must never be uploaded for training).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parents[1] / "research_entity/claycode/training"
OUT_PATH = TRAINING_DIR / "TRIGGER2_RUN4_TOGETHER_UPLOAD_V1.jsonl"

# Family file selection: prefer *_V2.jsonl if present, else the family's only/base file.
# This list is the full family-file set found in research_entity/claycode/training/*.jsonl at
# time of writing (2026-08-27), excluding *_AUDIT_REPORT*/*_REPORT* (non-training metadata files)
# and excluding the bias-fix file itself (added separately below, explicitly, for clarity).
FAMILY_FILES_V1_OR_V2 = [
    "TRIGGER2_A_WORK_SELECTION_CANDIDATE_V1.jsonl",
    "TRIGGER2_B0_READ_BASELINE_CANDIDATE_V1.jsonl",
    "TRIGGER2_B0_WRITE_BASELINE_CANDIDATE_V1.jsonl",
    # NOTE: TRIGGER2_B1_BINDING_MATERIALIZED_CANDIDATE_V1.jsonl is deliberately EXCLUDED.
    # Verified this session: it shares all 2304 TRAIN ids with B1_TRAIN_BALANCED_2ORDER_V2 but
    # ZERO overlapping prompt text (same episodes, pre-balance/pre-patch raw rendering) -- i.e. it
    # is the superseded intermediate that TRAIN_BALANCED_2ORDER (note the name: "SELECTION") was
    # built FROM, not a distinct additional family. Including both would silently reintroduce
    # 6912 stale, un-patched B1 rows (from before this session's regex-boundary prompt fixes) on
    # top of the corrected ones -- exactly the kind of thing this session's discipline exists to
    # catch rather than assume away.
    "TRIGGER2_B1_TRAIN_BALANCED_2ORDER_V2.jsonl",  # V2 supersedes V1
    "TRIGGER2_B2_MID_EPISODE_REMAP_CANDIDATE_V2.jsonl",  # V2 supersedes V1
    "TRIGGER2_B2_PRIOR_OVERRIDE_CANDIDATE_V2.jsonl",  # V2 supersedes V1
    "TRIGGER2_B2_STALE_BINDING_REJECTION_CANDIDATE_V1.jsonl",
    "TRIGGER2_B3_MULTI_HOP_DEREF_CANDIDATE_V2.jsonl",  # V2 supersedes V1
    "TRIGGER2_B3_UNRESOLVABLE_CHAIN_REJECTION_CANDIDATE_V2.jsonl",  # V2 supersedes V1
    "TRIGGER2_B4_CAPACITY_INTERFERENCE_CANDIDATE_V2.jsonl",  # V2 supersedes V1
    "TRIGGER2_B5_VARIABLE_N_EQUIVARIANCE_CANDIDATE_V2.jsonl",  # V2 supersedes V1
    "TRIGGER2_B6_CLAUDE_HANDOFF_REENTRY_CANDIDATE_V1.jsonl",
    "TRIGGER2_B6_DB_VS_SIM_CANDIDATE_V1.jsonl",
    "TRIGGER2_B6_GWT_CAUSAL_REENTRY_CANDIDATE_V1.jsonl",
    "TRIGGER2_B6_GWT_COMPETITION_BROADCAST_CANDIDATE_V1.jsonl",
    "TRIGGER2_B6_GWT_UPTAKE_CANDIDATE_V1.jsonl",
    "TRIGGER2_B6_HYPERPOSITION_EVIDENCE_AUTHORITY_CANDIDATE_V1.jsonl",
    "TRIGGER2_B6_HYPERPOSITION_EXPANSION_CANDIDATE_V1.jsonl",
    "TRIGGER2_G_REF_UNION_PRESERVATION_CANDIDATE_V1.jsonl",
    "TRIGGER2_G_TOPOLOGY_AND_UNKNOWN_PRESERVATION_CANDIDATE_V1.jsonl",
]
NEW_FOR_RUN4 = "TRIGGER2_B6_HYPERPOSITION_BIAS_FIX_CANDIDATE_V1.jsonl"


def load_train_rows(filename: str) -> list[dict]:
    path = TRAINING_DIR / filename
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("split") == "TRAIN":
                rows.append(row)
    return rows


def to_together_message_row(row: dict) -> dict:
    prompt = row.get("prompt")
    target = row.get("target")
    if prompt is None or target is None:
        raise ValueError(f"row missing prompt/target: {row.get('id')}")
    return {"messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": target}]}


def build():
    all_source_files = FAMILY_FILES_V1_OR_V2 + [NEW_FOR_RUN4]
    per_file_counts = {}
    all_rows = []
    id_to_files: dict[str, list[str]] = {}
    prompt_to_files: dict[str, list[str]] = {}
    for fname in all_source_files:
        rows = load_train_rows(fname)
        per_file_counts[fname] = len(rows)
        all_rows.extend(rows)
        for r in rows:
            id_to_files.setdefault(r["id"], []).append(fname)
            prompt_to_files.setdefault(r["prompt"], []).append(fname)

    prompts = [r["prompt"] for r in all_rows]
    dup_count = len(prompts) - len(set(prompts))
    cross_file_id_collisions = sum(1 for files in id_to_files.values() if len(set(files)) > 1)
    cross_file_prompt_collisions = sum(1 for files in prompt_to_files.values() if len(set(files)) > 1)
    assert dup_count == 0, f"{dup_count} duplicate prompts across the combined dataset"
    assert cross_file_id_collisions == 0, f"{cross_file_id_collisions} ids appear in more than one source file (likely a superseded/duplicate family file, as B1_BINDING_MATERIALIZED was)"
    assert cross_file_prompt_collisions == 0, f"{cross_file_prompt_collisions} prompts appear in more than one source file"

    together_rows = [to_together_message_row(r) for r in all_rows]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        for r in together_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "output_path": str(OUT_PATH),
        "n_source_files": len(all_source_files),
        "per_file_train_row_counts": per_file_counts,
        "total_train_rows": len(all_rows),
        "duplicate_prompt_count_across_all_files": dup_count,
        "new_for_run4_file": NEW_FOR_RUN4,
        "new_for_run4_row_count": per_file_counts[NEW_FOR_RUN4],
        "cross_file_id_collisions": cross_file_id_collisions,
        "cross_file_prompt_collisions": cross_file_prompt_collisions,
        "honest_note_on_count_vs_run3_doc": (
            "RUN3_PREPARATION_20260827.json documented run 3's base as '9544 TRAIN rows' (v2-patched) "
            "+ 672 hyperposition-expansion = 10216. Reconstructing from the currently committed source "
            "family files (after correctly excluding B1_BINDING_MATERIALIZED as a superseded intermediate, "
            "verified this session via id/prompt overlap) gives a different total for the non-bias-fix "
            "portion -- the exact prior number was not independently re-derivable from committed files "
            "alone (the actual uploaded run-3 JSONL was never committed, per documented precedent). This "
            "reconstruction is reported as internally consistent (0 duplicate prompts, 0 cross-file id/prompt "
            "collisions) rather than asserted to numerically match the undocumented historical figure."
        ),
        "output_sha256": None,
    }
    summary["output_sha256"] = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    build()
