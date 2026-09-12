#!/usr/bin/env python3
"""Build a deterministic, scratch-only blind parallax benefit stimulus.

The tool does not edit the live Avatar. It binds the exact production buehne.html
hash, uses the already-admitted four-slice Canvas2D `lighter` compositor, keeps the
canonical eye plate fixed in the established eye-patch geometry, and renders three
coded conditions: A=0, A=.25 source px, A=.50 source px.

Outputs:
  manifest.json                 blinded code -> amplitude mapping + subject hashes
  blind_phase_neg.png           synchronized maximum negative excursion
  blind_phase_zero.png          zero-displacement control (all heads should match)
  blind_phase_pos.png           synchronized maximum positive excursion
  blind_contact_sheet.jpg       three phase rows for quick visual falsification
  blind_animated.html           synchronized animation for human temporal A/B
  metrics.json                  crop-only control/delta metrics

No production browser/service is started or restarted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import random
import shutil
import subprocess
import tempfile
from typing import Iterable

LIVE_HTML_SHA = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
SCALE = 0.4036458333333333
SOURCE_W, SOURCE_H = 1536, 1024
CSS_W = 620
CSS_H = round(SOURCE_H * SCALE)  # 413
ROLL = "+00"
AMPS = [0.0, 0.25, 0.50]
COEFF = [1.0, 1.0 / 3.0, -1.0 / 3.0, -1.0]
SLICE_NAMES = [
    "slice_0_front_nase.png",
    "slice_1_mitte_gesicht.png",
    "slice_2_seite_ohren.png",
    "slice_3_hinten_haar.png",
]
EYE_LEFT_PCT = 31.0
EYE_TOP_PCT = 12.0
EYE_WIDTH_PCT = 27.0


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_file(path: pathlib.Path) -> pathlib.Path:
    if not path.is_file():
        raise SystemExit(f"missing required file: {path}")
    return path


def deterministic_conditions(seed_text: str) -> list[dict]:
    rng = random.Random(int(hashlib.sha256(seed_text.encode()).hexdigest()[:16], 16))
    codes = ["K7", "M4", "R2"]
    amps = AMPS[:]
    rng.shuffle(amps)
    return [{"code": c, "amp": a} for c, a in zip(codes, amps)]


def file_uri(path: pathlib.Path) -> str:
    return path.resolve().as_uri()


def html_doc(root: pathlib.Path, conditions: list[dict], phase: float | None) -> str:
    pdir = root / f"kopf_rgba_parallax/gier_+00_nick_+00_roll_{ROLL}"
    slices = [file_uri(require_file(pdir / n)) for n in SLICE_NAMES]
    eye = file_uri(require_file(root / "augen_blink_relief2/blink_000.png"))
    payload = json.dumps({"conditions": conditions, "slices": slices, "eye": eye, "phase": phase})
    animated = phase is None
    return f'''<!doctype html><meta charset="utf-8"><title>blind parallax benefit A/B</title>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;background:#0d0d10;color:#ddd;font:14px monospace;overflow:hidden}}
#row{{display:flex;gap:12px;padding:8px}}
.panel{{width:{CSS_W}px}}
.code{{height:20px;text-align:center;line-height:20px;letter-spacing:.18em;color:#aaa}}
.stage{{position:relative;width:{CSS_W}px;height:{CSS_H}px;background:#09090b;overflow:hidden}}
.head{{position:absolute;inset:0;width:{CSS_W}px;height:{CSS_H}px}}
.eye{{position:absolute;left:{EYE_LEFT_PCT}%;top:{EYE_TOP_PCT}%;width:{EYE_WIDTH_PCT}%;height:auto;pointer-events:none}}
</style><div id=row></div><script>
const P={payload};
const W={SOURCE_W}, H={SOURCE_H};
const coeff={json.dumps(COEFF)};
function load(src){{return new Promise((ok,bad)=>{{const i=new Image();i.onload=()=>ok(i);i.onerror=()=>bad(new Error(src));i.src=src}})}}
(async()=>{{
 const imgs=await Promise.all(P.slices.map(load));
 const eye=await load(P.eye);
 const row=document.getElementById('row');
 const panels=[];
 for(const cond of P.conditions){{
   const wrap=document.createElement('div');wrap.className='panel';
   const code=document.createElement('div');code.className='code';code.textContent=cond.code;wrap.appendChild(code);
   const stage=document.createElement('div');stage.className='stage';wrap.appendChild(stage);
   const c=document.createElement('canvas');c.className='head';c.width=W;c.height=H;stage.appendChild(c);
   const e=document.createElement('img');e.className='eye';e.src=P.eye;stage.appendChild(e);
   row.appendChild(wrap);panels.push({{cond,c,ctx:c.getContext('2d')}});
 }}
 function draw(panel, phase){{
   const x=panel.ctx;x.globalCompositeOperation='source-over';x.clearRect(0,0,W,H);x.globalCompositeOperation='lighter';
   for(let i=0;i<imgs.length;i++) x.drawImage(imgs[i],coeff[i]*panel.cond.amp*phase,0);
   x.globalCompositeOperation='source-over';
 }}
 function render(phase){{for(const p of panels)draw(p,phase);document.documentElement.dataset.ready='1';document.documentElement.dataset.phase=String(phase)}}
 if(P.phase===null){{
   const t0=performance.now();
   function tick(t){{render(Math.sin((t-t0)*2*Math.PI/1800));requestAnimationFrame(tick)}} requestAnimationFrame(tick);
 }} else render(P.phase);
 window.__stimulus={{conditions:P.conditions,render}};
}})().catch(e=>{{document.body.textContent='ERROR '+e.stack;document.documentElement.dataset.error='1'}});
</script>'''


def chrome_capture(chrome: str, html: pathlib.Path, out: pathlib.Path) -> None:
    width = 8 * 2 + 3 * CSS_W + 2 * 12
    height = 8 * 2 + 20 + CSS_H
    cmd = [
        chrome, "--headless=new", "--no-sandbox", "--allow-file-access-from-files",
        "--hide-scrollbars", f"--window-size={width},{height}",
        "--virtual-time-budget=2500", f"--screenshot={out}", html.as_uri(),
    ]
    p = subprocess.run(cmd, text=True, capture_output=True, timeout=90)
    if p.returncode != 0 or not out.is_file() or out.stat().st_size < 1000:
        raise SystemExit(f"chrome capture failed rc={p.returncode} stderr={p.stderr[-2000:]}")


def crop_boxes() -> list[tuple[int, int, int, int]]:
    # Screenshot content origin: row padding 8; code line 20; stage begins at y=28.
    return [
        (8 + i * (CSS_W + 12), 28, 8 + i * (CSS_W + 12) + CSS_W, 28 + CSS_H)
        for i in range(3)
    ]


def mean_abs_rgb(a, b) -> float:
    import numpy as np
    aa = np.asarray(a.convert("RGB"), dtype=np.int16)
    bb = np.asarray(b.convert("RGB"), dtype=np.int16)
    return float(np.abs(aa - bb).mean())


def p99_abs_rgb(a, b) -> float:
    import numpy as np
    aa = np.asarray(a.convert("RGB"), dtype=np.int16)
    bb = np.asarray(b.convert("RGB"), dtype=np.int16)
    return float(np.quantile(np.abs(aa - bb), 0.99))


def contact_sheet(paths: Iterable[pathlib.Path], out: pathlib.Path) -> dict:
    try:
        from PIL import Image, ImageDraw
    except Exception as e:
        return {"created": False, "reason": f"Pillow unavailable: {e}"}
    ims = [Image.open(p).convert("RGB") for p in paths]
    w = max(i.width for i in ims); h = sum(i.height for i in ims)
    sheet = Image.new("RGB", (w, h))
    y = 0
    for im in ims:
        sheet.paste(im, (0, y)); y += im.height
    sheet.save(out, quality=91, optimize=True)
    return {"created": True, "sha256": sha256(out), "bytes": out.stat().st_size}


def metrics_for_image(path: pathlib.Path, conditions: list[dict]) -> dict:
    try:
        from PIL import Image
    except Exception as e:
        return {"error": f"Pillow unavailable: {e}"}
    im = Image.open(path).convert("RGB")
    crops = [im.crop(b) for b in crop_boxes()]
    baseline_i = next(i for i,c in enumerate(conditions) if c["amp"] == 0.0)
    out = {"image": path.name, "sha256": sha256(path), "baseline_code": conditions[baseline_i]["code"], "pairs": {}}
    for i,c in enumerate(conditions):
        if i == baseline_i: continue
        out["pairs"][c["code"]] = {
            "amp": c["amp"],
            "rgb_mae_vs_baseline": mean_abs_rgb(crops[baseline_i], crops[i]),
            "rgb_p99_vs_baseline": p99_abs_rgb(crops[baseline_i], crops[i]),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", default="/home/ai-core-node/.claude/star/visual")
    ap.add_argument("--chrome", default="/usr/bin/google-chrome")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = pathlib.Path(args.visual_root).resolve(); out = pathlib.Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    live = require_file(root / "buehne.html")
    live_sha = sha256(live)
    if live_sha != LIVE_HTML_SHA:
        raise SystemExit(f"SUBJECT_DRIFT live buehne.html {live_sha} != {LIVE_HTML_SHA}")
    conditions = deterministic_conditions(live_sha + "|parallax-benefit-v1")
    manifest = {
        "schema": "PARALLAX_BLIND_BENEFIT_STIMULUS/v1",
        "live_buehne_sha256": live_sha,
        "scale_source_to_css": SCALE,
        "source_size": [SOURCE_W, SOURCE_H],
        "css_stage_size": [CSS_W, CSS_H],
        "roll": ROLL,
        "compositor": "Chrome Canvas2D lighter",
        "coefficients": COEFF,
        "eye_asset": "augen_blink_relief2/blink_000.png",
        "eye_asset_sha256": sha256(require_file(root / "augen_blink_relief2/blink_000.png")),
        "eye_geometry_percent": {"left":EYE_LEFT_PCT,"top":EYE_TOP_PCT,"width":EYE_WIDTH_PCT},
        "conditions": conditions,
        "production_mutation": False,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n")
    # Persistent animated page for human temporal evaluation.
    (out / "blind_animated.html").write_text(html_doc(root, conditions, None))
    phase_paths=[]
    for tag, phase in [("neg",-1.0),("zero",0.0),("pos",1.0)]:
        page = out / f"_phase_{tag}.html"; page.write_text(html_doc(root, conditions, phase))
        png = out / f"blind_phase_{tag}.png"; chrome_capture(args.chrome, page, png); phase_paths.append(png); page.unlink()
    metrics={
        "schema":"PARALLAX_BLIND_BENEFIT_METRICS/v1",
        "conditions":conditions,
        "phase_neg":metrics_for_image(phase_paths[0],conditions),
        "phase_zero":metrics_for_image(phase_paths[1],conditions),
        "phase_pos":metrics_for_image(phase_paths[2],conditions),
    }
    # Zero-phase is a renderer control: all three head crops should be effectively identical.
    metrics["contact_sheet"] = contact_sheet(phase_paths, out / "blind_contact_sheet.jpg")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True)+"\n")
    post_sha=sha256(live)
    if post_sha != live_sha:
        raise SystemExit("LIVE_MUTATION_DETECTED")
    print("PARALLAX_BLIND_BENEFIT_STIMULUS/v1")
    print("LIVE_PRE_SHA", live_sha)
    print("LIVE_POST_SHA", post_sha)
    print("LIVE_MUTATION", 0)
    print("CONDITIONS", json.dumps(conditions, sort_keys=True))
    print("METRICS", json.dumps(metrics, sort_keys=True))
    print("OUT", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
