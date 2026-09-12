#!/usr/bin/env python3
"""Actual-asset Chromium A/B for the FranKenstein roll eye/blink overlay.

Read-only with respect to production. It serves the existing visual asset directory
and renders isolated 1536x1024 native-canvas scenes using the real rolled-head PNG
and real blink_000.png. It compares current full-displacement translation against
the residual translation candidate after the same CSS rotate(roll).

The hard geometric metric is the transformed manifest eye anchor. Pixel seam MAE
against the rolled head alone is reported as supportive visual evidence, not used
as the sole acceptance criterion.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

import apply_roll_overlay_residual_candidate as model

CANVAS_W = 1536
CANVAS_H = 1024
EYE_X, EYE_Y = model.EYE
ROI = (350, 50, 1050, 700)


def roll_token(deg: int) -> str:
    return f"{deg:+03d}"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def image_from_png(raw: bytes) -> Image.Image:
    return Image.open(io.BytesIO(raw)).convert("RGB")


def mae(a: Image.Image, b: Image.Image, crop=None) -> float:
    if crop:
        a, b = a.crop(crop), b.crop(crop)
    d = ImageChops.difference(a, b)
    means = ImageStat.Stat(d).mean[:3]
    return float(sum(means) / 3.0)


def scene_html(head_url: str, blink_url: str, dx: float | None, dy: float | None, roll: int) -> str:
    overlay = "" if dx is None else (
        f'<img id="blink" src="{blink_url}" '
        f'style="position:absolute;left:31%;top:12%;width:27%;height:auto;'
        f'transform-origin:70.38% 241.32%;'
        f'transform:translate({dx:.9f}px,{dy:.9f}px) rotate({roll}deg);z-index:2">'
    )
    return f'''<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;width:{CANVAS_W}px;height:{CANVAS_H}px;overflow:hidden;background:#fff}}
#c{{position:relative;width:{CANVAS_W}px;height:{CANVAS_H}px;overflow:hidden}}
#head{{position:absolute;inset:0;width:100%;height:100%;object-fit:fill;z-index:1}}
</style><div id="c"><img id="head" src="{head_url}">{overlay}</div>'''


def transformed_eye(page) -> tuple[float, float]:
    return tuple(page.eval_on_selector("#blink", """(e) => {
      const cs = getComputedStyle(e);
      const m = new DOMMatrix(cs.transform === 'none' ? undefined : cs.transform);
      const o = cs.transformOrigin.split(/\\s+/).map(parseFloat);
      const lx = 610 - e.offsetLeft;
      const ly = 207 - e.offsetTop;
      const q = new DOMPoint(lx-o[0], ly-o[1]).matrixTransform(m);
      return [e.offsetLeft + o[0] + q.x, e.offsetTop + o[1] + q.y];
    }"""))


def wait_imgs(page):
    page.wait_for_function("""[...document.images].every(i => i.complete && i.naturalWidth > 0)""")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("visual_root", type=Path)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    root = args.visual_root.resolve()
    if not (root / "augen_blink/blink_000.png").is_file():
        raise SystemExit("missing real blink_000.png")

    handler = lambda *a, **k: QuietHandler(*a, directory=str(root), **k)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_port
    base = f"http://127.0.0.1:{port}"
    residual = model.residual_table()
    results = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": CANVAS_W, "height": CANVAS_H}, device_scale_factor=1)
            for roll in sorted(model.FULL):
                head_rel = f"kopf_rgba/roll/gier_+00_nick_+00_roll_{roll_token(roll)}.png"
                if roll == 0 and not (root / head_rel).is_file():
                    # Current tree can keep neutral only in master; use production neutral source.
                    candidates = [
                        "kopf_rgba/master/kopf_zero_mit_augen.png",
                        "kopf/master/kopf_zero_mit_augen.png",
                    ]
                    head_rel = next((x for x in candidates if (root / x).is_file()), head_rel)
                if not (root / head_rel).is_file():
                    raise SystemExit(f"missing rolled head asset: {head_rel}")
                head_url = f"{base}/{head_rel}"
                blink_url = f"{base}/augen_blink/blink_000.png"

                page.set_content(scene_html(head_url, blink_url, None, None, roll), wait_until="load")
                wait_imgs(page)
                baseline = image_from_png(page.screenshot())

                target = model.FULL[roll]
                page.set_content(scene_html(head_url, blink_url, target[0], target[1], roll), wait_until="load")
                wait_imgs(page)
                current_eye = transformed_eye(page)
                current_img = image_from_png(page.screenshot())

                cand = residual[roll]
                page.set_content(scene_html(head_url, blink_url, cand[0], cand[1], roll), wait_until="load")
                wait_imgs(page)
                corrected_eye = transformed_eye(page)
                corrected_img = image_from_png(page.screenshot())

                expected_eye = (EYE_X + target[0], EYE_Y + target[1])
                ce = math.hypot(current_eye[0]-expected_eye[0], current_eye[1]-expected_eye[1])
                fe = math.hypot(corrected_eye[0]-expected_eye[0], corrected_eye[1]-expected_eye[1])
                rec = {
                    "roll": roll,
                    "head": head_rel,
                    "expected_eye": [round(x, 6) for x in expected_eye],
                    "current_eye": [round(x, 6) for x in current_eye],
                    "corrected_eye": [round(x, 6) for x in corrected_eye],
                    "current_anchor_error_px": ce,
                    "corrected_anchor_error_px": fe,
                    "current_seam_mae_full": mae(baseline, current_img),
                    "corrected_seam_mae_full": mae(baseline, corrected_img),
                    "current_seam_mae_roi": mae(baseline, current_img, ROI),
                    "corrected_seam_mae_roi": mae(baseline, corrected_img, ROI),
                }
                results.append(rec)
                print(json.dumps(rec, sort_keys=True))
            browser.close()
    finally:
        httpd.shutdown()
        thread.join(timeout=2)

    max_cur = max(x["current_anchor_error_px"] for x in results)
    max_fix = max(x["corrected_anchor_error_px"] for x in results)
    nonzero = [x for x in results if x["roll"] != 0]
    improved = sum(x["corrected_seam_mae_roi"] < x["current_seam_mae_roi"] for x in nonzero)
    summary = {
        "schema": "F2_AVATAR_ROLL_OVERLAY_ACTUAL_ASSET_GATE/v1",
        "max_current_anchor_error_px": max_cur,
        "max_corrected_anchor_error_px": max_fix,
        "pixel_roi_improved_states": improved,
        "pixel_roi_total_nonzero_states": len(nonzero),
        "geometry_pass": max_fix <= 0.35 and max_cur >= 30.0,
        "results": results,
    }
    print("SUMMARY", json.dumps(summary, sort_keys=True))
    if args.json_out:
        args.json_out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    if not summary["geometry_pass"]:
        raise SystemExit(2)
    print("PASS=GEOMETRY_ACTUAL_ASSET_BROWSER_GATE")
    print("SCOPE=SCRATCH_REAL_ASSETS_NO_PRODUCTION_BROWSER_NO_LIVE_MUTATION")


if __name__ == "__main__":
    main()
