#!/usr/bin/env python3
"""Compact an existing DEPTHWARP_FINAL_VISUAL_READBACK/v1 report.

Read-only utility for bridge receipts: emits the full per-amplitude acceptance
envelope without transporting the large per-roll report or contact sheet.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report", type=Path)
    args = ap.parse_args()
    r = json.loads(args.report.read_text())
    out = {
        "schema": "DEPTHWARP_FINAL_VISUAL_READBACK_SUMMARY/v1",
        "source_unchanged": r["source_unchanged"],
        "whole_avatar_live_credit": r["whole_avatar_live_credit"],
        "perceptual_lifelikeness_verdict": r["perceptual_lifelikeness_verdict"],
        "contact_sha256": r["artifacts"]["all_rolls_contact_sheet_sha256"],
        "amplitudes": {},
    }
    for amp in ("A1.00", "A1.25"):
        rows = [(roll, vals[amp]) for roll, vals in r["results"].items()]
        out["amplitudes"][amp] = {
            "failed_rolls": sorted((roll for roll, x in rows if not x["mechanical_identity_guard_pass"]), key=int),
            "alpha_all_exact": all(x["alpha_exact"] for _, x in rows),
            "eye_shift_px_max": max(x["eye_shift_px"] for _, x in rows),
            "laplacian_detail_ratio_min": min(x["laplacian_detail_ratio"] for _, x in rows),
            "laplacian_detail_ratio_max": max(x["laplacian_detail_ratio"] for _, x in rows),
            "rgb_mae_active_max": max(x["rgb_mae_active"] for _, x in rows),
            "rgb_p99_active_max": max(x["rgb_p99_active"] for _, x in rows),
            "p95_abs_displacement_display_px_max": max(x["p95_abs_displacement_display_px"] for _, x in rows),
            "max_abs_displacement_display_px_max": max(x["max_abs_displacement_display_px"] for _, x in rows),
            "changed_gt1_active_frac_min": min(x["changed_gt1_active_frac"] for _, x in rows),
            "changed_gt3_active_frac_min": min(x["changed_gt3_active_frac"] for _, x in rows),
        }
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
