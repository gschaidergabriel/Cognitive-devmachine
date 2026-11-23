#!/usr/bin/env python3
"""Generate blinded, confound-controlled final-display A/B material for depth-warp review.

This is an evidence generator, not a perceptual-benefit oracle. It keeps the
answer key separate from the blind manifest and refuses objective eligibility
when alpha/eye/detail/signal controls fail. Human blind judgments are required
before any perceptual or production promotion credit.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from depthwarp_display_space_gate import ROLLS, build, gray, lap, phase

SCHEMA = "GO_AVATAR_DEPTHWARP_BLIND_PERCEPTUAL_GATE/v1"
DEFAULT_AMPS = (1.0, 1.25)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resize_rgba(x: np.ndarray, width: int, height: int) -> np.ndarray:
    return cv2.resize(x, (width, height), interpolation=cv2.INTER_AREA)


def save_rgba(path: Path, x: np.ndarray) -> None:
    Image.fromarray(x.astype(np.uint8), "RGBA").save(path)


def metrics(
    baseline: np.ndarray,
    candidate: np.ndarray,
    gate: np.ndarray,
    eye_xy: tuple[float, float],
    source_size: tuple[int, int],
) -> dict[str, float | bool]:
    h, w = baseline.shape[:2]
    src_w, src_h = source_size
    sx, sy = w / src_w, h / src_h
    active = gate > 0.05
    opaque = baseline[:, :, 3] >= 245
    diff = candidate[:, :, :3].astype(np.float32) - baseline[:, :, :3].astype(np.float32)
    absdiff = np.abs(diff)
    rgb_mae = float(absdiff[active].mean()) if active.any() else 0.0
    rgb_p99 = float(np.quantile(absdiff[active], 0.99)) if active.any() else 0.0
    luma_delta = gray(candidate) - gray(baseline)
    luma_bias = float(abs(luma_delta[active].mean())) if active.any() else 0.0
    g0, g1 = gray(baseline), gray(candidate)
    px, py, response = phase(g0, g1, eye_xy[0] * sx, eye_xy[1] * sy)
    return {
        "alpha_exact": bool(np.array_equal(baseline[:, :, 3], candidate[:, :, 3])),
        "active_frac": float(active.mean()),
        "rgb_mae_active": rgb_mae,
        "rgb_p99_active": rgb_p99,
        "mean_luma_bias_active": luma_bias,
        "brightness_share_of_rgb_mae": float(luma_bias / max(rgb_mae, 1e-9)),
        "lap_ratio": float((lap(g1, opaque) + 1e-9) / (lap(g0, opaque) + 1e-9)),
        "eye_shift_px": float((px * px + py * py) ** 0.5),
        "eye_response": float(response),
    }


def public_case(case: dict) -> dict:
    # Deliberately excludes condition labels and the RNG bit assigning A/B.
    return {
        "case_id": case["case_id"],
        "kind": case["kind"],
        "roll": case["roll"],
        "amp": case["amp"],
        "A": case["A"],
        "B": case["B"],
        "objective_eligible": case["objective_eligible"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", default="/home/ai-core-node/.claude/star/visual")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=620)
    ap.add_argument("--height", type=int, default=414)
    ap.add_argument("--seed", type=int, default=560912)
    ap.add_argument("--amps", nargs="+", type=float, default=list(DEFAULT_AMPS))
    ap.add_argument("--shams", type=int, default=6)
    ap.add_argument("--min-signal-mae", type=float, default=0.20)
    ap.add_argument("--null-factor", type=float, default=3.0)
    ap.add_argument("--min-lap-ratio", type=float, default=0.90)
    ap.add_argument("--max-eye-shift-px", type=float, default=0.25)
    ap.add_argument("--max-brightness-share", type=float, default=0.50)
    args = ap.parse_args()

    root = Path(args.visual_root).resolve()
    out = Path(args.out).resolve()
    pairs = out / "pairs"
    pairs.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    anchor_path = root / "rig2/augen_anker_exakt.json"
    anchors = json.loads(anchor_path.read_text(encoding="utf-8"))
    eye0 = np.array(
        [anchors["augen_anker_roll0"]["x"], anchors["augen_anker_roll0"]["y"]],
        dtype=float,
    )

    cases: list[dict] = []
    objective_rows: list[dict] = []
    source_hashes: dict[str, str] = {str(anchor_path.relative_to(root)): sha256_file(anchor_path)}
    sham_pool: list[tuple[str, np.ndarray, np.ndarray, tuple[float, float], dict]] = []

    for roll in ROLLS:
        anchor = anchors["werte"][str(int(roll))]
        eye = tuple(eye0 + np.array([anchor["dx_px"], anchor["dy_px"]], dtype=float))
        base, null_full, null_gate, _ = build(root, roll, eye, 0.0)
        src_h, src_w = base.shape[:2]
        baseline = resize_rgba(base, args.width, args.height)
        null = resize_rgba(null_full, args.width, args.height)
        null_gate_d = cv2.resize(
            null_gate.astype(np.float32),
            (args.width, args.height),
            interpolation=cv2.INTER_AREA,
        )
        null_m = metrics(baseline, null, null_gate_d, eye, (src_w, src_h))

        base_path = root / f"kopf_rgba/roll/gier_+00_nick_+00_roll_{roll}.png"
        source_hashes[str(base_path.relative_to(root))] = sha256_file(base_path)
        for slice_path in sorted((root / f"kopf_rgba_parallax/gier_+00_nick_+00_roll_{roll}").glob("slice_*.png")):
            source_hashes[str(slice_path.relative_to(root))] = sha256_file(slice_path)

        sham_pool.append((roll, baseline, null, eye, null_m))

        for amp in args.amps:
            _, warp_full, warp_gate, _ = build(root, roll, eye, amp)
            warp = resize_rgba(warp_full, args.width, args.height)
            warp_gate_d = cv2.resize(
                warp_gate.astype(np.float32),
                (args.width, args.height),
                interpolation=cv2.INTER_AREA,
            )
            wm = metrics(baseline, warp, warp_gate_d, eye, (src_w, src_h))
            signal_floor = max(args.min_signal_mae, args.null_factor * float(null_m["rgb_mae_active"]))
            eligible = bool(
                wm["alpha_exact"]
                and wm["lap_ratio"] >= args.min_lap_ratio
                and wm["eye_shift_px"] <= args.max_eye_shift_px
                and wm["rgb_mae_active"] >= signal_floor
                and wm["brightness_share_of_rgb_mae"] <= args.max_brightness_share
            )

            case_id = f"R{int(roll):+03d}_A{amp:.2f}".replace("+", "p").replace("-", "m").replace(".", "p")
            first_is_warp = bool(rng.getrandbits(1))
            a_img, b_img = (warp, baseline) if first_is_warp else (baseline, warp)
            a_name, b_name = f"{case_id}_A.png", f"{case_id}_B.png"
            save_rgba(pairs / a_name, a_img)
            save_rgba(pairs / b_name, b_img)
            cases.append(
                {
                    "case_id": case_id,
                    "kind": "BASE_VS_WARP",
                    "roll": int(roll),
                    "amp": amp,
                    "A": f"pairs/{a_name}",
                    "B": f"pairs/{b_name}",
                    "A_label": "WARP" if first_is_warp else "BASE",
                    "B_label": "BASE" if first_is_warp else "WARP",
                    "objective_eligible": eligible,
                }
            )
            objective_rows.append(
                {
                    "case_id": case_id,
                    "roll": int(roll),
                    "amp": amp,
                    "objective_eligible": eligible,
                    "null_rgb_mae_active": null_m["rgb_mae_active"],
                    "null_lap_ratio": null_m["lap_ratio"],
                    **{f"warp_{k}": v for k, v in wm.items()},
                    "signal_floor": signal_floor,
                }
            )

    # Sham trials estimate A/B position bias and expectation effects. BASE-vs-NULL
    # uses the exact identity-remap pipeline with zero displacement.
    sham_n = min(max(args.shams, 0), len(sham_pool))
    for idx, (roll, baseline, null, _eye, null_m) in enumerate(rng.sample(sham_pool, sham_n), 1):
        case_id = f"SHAM_{idx:02d}_R{int(roll):+03d}".replace("+", "p").replace("-", "m")
        first_is_null = bool(rng.getrandbits(1))
        a_img, b_img = (null, baseline) if first_is_null else (baseline, null)
        a_name, b_name = f"{case_id}_A.png", f"{case_id}_B.png"
        save_rgba(pairs / a_name, a_img)
        save_rgba(pairs / b_name, b_img)
        cases.append(
            {
                "case_id": case_id,
                "kind": "SHAM_BASE_VS_NULL_REMAP",
                "roll": int(roll),
                "amp": 0.0,
                "A": f"pairs/{a_name}",
                "B": f"pairs/{b_name}",
                "A_label": "NULL_REMAP" if first_is_null else "BASE",
                "B_label": "BASE" if first_is_null else "NULL_REMAP",
                "objective_eligible": bool(null_m["alpha_exact"]),
            }
        )

    rng.shuffle(cases)
    manifest = {
        "schema": SCHEMA,
        "purpose": "BLINDED_REVIEW_ONLY_NO_PERCEPTUAL_OR_PRODUCTION_CREDIT",
        "seed_commitment_sha256": hashlib.sha256(str(args.seed).encode()).hexdigest(),
        "display_size": [args.width, args.height],
        "case_count": len(cases),
        "instructions": {
            "primary_question": "Which image has stronger coherent 3D depth while preserving the same identity?",
            "choice": ["A", "B", "INDISTINGUISHABLE"],
            "identity_artifact": "0 none, 1 slight, 2 clear, 3 severe",
            "do_not_open_answer_key_before_scoring": True,
        },
        "cases": [public_case(x) for x in cases],
    }
    answer_key = {
        "schema": f"{SCHEMA}:ANSWER_KEY",
        "seed": args.seed,
        "source_hashes_sha256": source_hashes,
        "cases": [
            {
                "case_id": x["case_id"],
                "kind": x["kind"],
                "A_label": x["A_label"],
                "B_label": x["B_label"],
            }
            for x in cases
        ],
    }
    report = {
        "schema": f"{SCHEMA}:OBJECTIVE_REPORT",
        "credit": {
            "source_tool_credit": 1,
            "objective_identity_eligibility_only": 1,
            "perceptual_benefit_credit": 0,
            "production_credit": 0,
        },
        "thresholds": {
            "min_signal_mae": args.min_signal_mae,
            "null_factor": args.null_factor,
            "min_lap_ratio": args.min_lap_ratio,
            "max_eye_shift_px": args.max_eye_shift_px,
            "max_brightness_share": args.max_brightness_share,
        },
        "candidate_cases": len(objective_rows),
        "eligible_cases": sum(bool(x["objective_eligible"]) for x in objective_rows),
        "rows": objective_rows,
    }

    (out / "blind_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "answer_key.json").write_text(json.dumps(answer_key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "objective_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (out / "blind_scores.csv").open("w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        wr.writerow(["case_id", "choice_A_B_INDISTINGUISHABLE", "depth_confidence_0_3", "identity_artifact_0_3", "notes"])
        for case in cases:
            wr.writerow([case["case_id"], "", "", "", ""])

    manifest_sha = sha256_file(out / "blind_manifest.json")
    answer_sha = sha256_file(out / "answer_key.json")
    print(
        json.dumps(
            {
                "schema": SCHEMA,
                "out": str(out),
                "candidate_cases": len(objective_rows),
                "eligible_cases": report["eligible_cases"],
                "sham_cases": sham_n,
                "blind_manifest_sha256": manifest_sha,
                "answer_key_sha256": answer_sha,
                "perceptual_benefit_credit": 0,
                "production_credit": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
