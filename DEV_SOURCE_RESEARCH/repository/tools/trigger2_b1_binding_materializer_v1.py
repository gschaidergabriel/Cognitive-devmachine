#!/usr/bin/env python3
"""Trigger-2 B1 candidate materializer: arbitrary episode-local binding, full S3 /
counterbalanced nuisance crossing.

Context: research_entity/global/TRIGGERWORT_2_CURRENT_TRAINING_COURSE_XENO_HARNESS_2026-08-26.md,
Training map section "B1: arbitrary episode-local binding with full S3/counterbalanced
nuisance crossing" -- and section 4/5's binding hard-negative laws:

  - never train global ALLOW -> fixed atom, DENY -> fixed atom, ABSTAIN -> fixed atom
    mappings;
  - use full mapping permutations / episode-local codebooks;
  - do not name role vectors permanently;
  - include family-disjoint unseen mappings/templates/symbol combinations;
  - train current-codebook binding and context invariance;
  - no direct-SFT promotion from lexically shortcut-prone wording.

tools/trigger2_dynamic_binding_blueprint_v2.py (the "strongest existing binding-generator
donor", per TRIGGERWORT_2_TRAINING_COURSE_DELTA_V35_SUPERVISOR_8_81_2026-08-26.md's
explicit "rebase/audit the strongest existing donor rather than creating a competing
generator" guidance) IS this B1 generator: it already implements the exact S3
mapping x codebook-order x layout x class x polarity full factorial crossing, across
family-disjoint TRAIN/VALIDATION/HOLDOUT_FROZEN templates and symbol pools.

This tool does not fork a new generator. It MATERIALIZES (renders full prompt bytes
for) that existing, already-leakage-audited donor -- reusing
tools/trigger2_dynamic_binding_blueprint_v2_leakage_audit_v1.py's render_prompt() and
its corrected (2026-08-26, post chatgpt-secondary review) leakage checks as a
fail-closed gate: this tool REFUSES to write output if the audit does not pass. No
row here is training-eligible (placeholder ABI_ACCEPTED_ORDINAL atoms; real
tokenizer/atom-manifest binding remains a separate, later gate). All rows are
candidate/quarantined, evidence_class=METHOD_ONLY, per TRIGGERWORT_2 course Step 6.

Deliberately did NOT inject section 2.B's S0/S1/S2 hard negatives (model-output-becomes-
S0-fact, S1-majority-becomes-truth, etc.) into these rows: that is a different capability
family (closest to B6, "DB-vs-simulation, ... Hyperposition/evidence authority" in the
same B0-B6 list), and mixing it into a pure symbol-binding/routing task risks exactly the
kind of confound this course repeatedly warns against ("no aggregate checkpoint score may
hide a mandatory-axis failure"). Recorded here explicitly rather than silently narrowing
scope.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trigger2_dynamic_binding_blueprint_v2 as bp  # noqa: E402
import trigger2_dynamic_binding_blueprint_v2_leakage_audit_v1 as audit  # noqa: E402

SCHEMA = "CLAY_TRIGGER2_B1_BINDING_MATERIALIZED_CANDIDATE/v1"
ANCESTRY = "trigger2-20260826-b1-binding-materialized-v1"


def materialize_row(row: dict) -> dict:
    eq_text, full_prompt = audit.render_prompt(row)
    out = dict(row)
    out.update({
        "schema": SCHEMA,
        "curriculum_phase": "B1_ARBITRARY_EPISODE_LOCAL_BINDING",
        "provenance_ancestry_id": ANCESTRY,
        "source_blueprint_schema": bp.SCHEMA,
        "prompt": full_prompt,
        "eq_text_only": eq_text,
        "evidence_class": "METHOD_ONLY",
        "canonical_truth_allowed": False,
        "positive_jspace_label": False,
        "selected_using_holdout": False,
        "training_eligible": False,
        "render_status": "PROMPT_RENDERED_CANDIDATE_PLACEHOLDER_ATOMS",
    })
    return out


def run(fail_closed: bool = True) -> tuple[list[dict], dict]:
    audit_report = audit.run()
    if fail_closed and not audit_report["overall_pass"]:
        raise SystemExit(
            "REFUSING to materialize B1 rows: leakage audit did not pass. "
            "See audit_report for details. Fix the audited generator first."
        )
    rows = bp.build_rows()
    materialized = [materialize_row(r) for r in rows]
    return materialized, audit_report


def self_check(materialized: list[dict]) -> dict:
    """Cheap structural sanity check independent of the leakage audit: every
    materialized row's target must still be reachable from its own realized_mapping
    fields (perm/triple/class), and no two rows may render to an identical full
    prompt with a different target (which would make the task ill-posed)."""
    failures = []
    by_prompt: dict[str, set[str]] = {}
    for r in materialized:
        by_prompt.setdefault(r["prompt"], set()).add(r["target"])
        ci = bp.CLASSES.index(r["c"])
        expected = r["sym"][r["perm"][ci]]
        if r["target"] != expected:
            failures.append(f"TARGET_MISMATCH:{r['id']}")
    contradictory = {p: t for p, t in by_prompt.items() if len(t) > 1}
    if contradictory:
        failures.append(f"CONTRADICTORY_PROMPT_TARGETS:{len(contradictory)}")
    return {"pass": not failures, "failures": failures, "unique_prompts": len(by_prompt)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--audit-out", type=Path)
    ap.add_argument("--report-out", type=Path)
    ap.add_argument("--no-fail-closed", action="store_true")
    args = ap.parse_args()

    materialized, audit_report = run(fail_closed=not args.no_fail_closed)
    check = self_check(materialized)
    if not check["pass"]:
        print(json.dumps({"self_check": check}, indent=2))
        return 3

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as f:
        for r in materialized:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
    output_sha256 = hashlib.sha256(args.out.read_bytes()).hexdigest()

    report = {
        "schema": SCHEMA,
        "rows_materialized": len(materialized),
        "split_counts": dict(Counter(r["split"] for r in materialized)),
        "output_path": str(args.out),
        "output_sha256": output_sha256,
        "output_bytes": args.out.stat().st_size,
        "self_check": check,
        "leakage_audit_overall_pass": audit_report["overall_pass"],
        "training_eligible": False,
        "reason_training_eligible_false": "placeholder ABI_ACCEPTED_ORDINAL atoms, no real tokenizer/atom-manifest binding, no admission gate run -- candidate/quarantined only per TRIGGERWORT_2 course Step 6.",
    }
    if args.audit_out:
        args.audit_out.write_text(json.dumps(audit_report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)
    if args.report_out:
        args.report_out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
