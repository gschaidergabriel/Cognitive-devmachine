#!/usr/bin/env python3
"""No-source-write A/B harness for special-expression eye identity.

Purpose
-------
The first live-browser A/B reached the correct page and expression but timed out
inside CDP Page.captureScreenshot because the websocket socket itself was left
at a 5 second timeout. This harness gives CDP calls explicit longer deadlines,
retries screenshots, clips captures to the eye neighborhood, and uses the
already-live localized relief2 blink_000 as the ONE canonical open-eye plate.

This script changes only the isolated headless browser DOM. It does not write
buehne.html, buehne_daemon.py, or live assets. The forced glow phase is a
GEOMETRY/COMPOSITING discriminator only; it does not claim that gaze should be
visible when the real presence/face signal says otherwise.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any

import numpy as np
from PIL import Image
import requests
import websocket

EXPECTED_HTML_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
EXPECTED_OPEN_PLATE_SHA256 = "8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9"
URL = "http://127.0.0.1:8788/"
VIEWPORT_W = 1536
VIEWPORT_H = 1024


def sha256_file(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CDP:
    def __init__(self, ws_url: str, timeout: float = 20.0):
        self.ws = websocket.create_connection(ws_url, timeout=timeout, origin="http://localhost")
        self.seq = 0

    def close(self) -> None:
        self.ws.close()

    def call(self, method: str, params: dict[str, Any] | None = None, timeout: float = 20.0) -> dict[str, Any]:
        self.seq += 1
        ident = self.seq
        self.ws.settimeout(timeout)
        self.ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
        deadline = time.monotonic() + timeout
        while True:
            remain = deadline - time.monotonic()
            if remain <= 0:
                raise TimeoutError(f"CDP timeout method={method} id={ident}")
            self.ws.settimeout(remain)
            msg = json.loads(self.ws.recv())
            if msg.get("id") != ident:
                continue
            if "error" in msg:
                raise RuntimeError(f"CDP {method}: {msg['error']}")
            return msg.get("result", {})

    def eval(self, expression: str) -> Any:
        result = self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
            timeout=15,
        )
        obj = result.get("result", {})
        if obj.get("subtype") == "error" or result.get("exceptionDetails"):
            raise RuntimeError(str(result))
        return obj.get("value")

    def screenshot(self, path: Path, clip: dict[str, float], tries: int = 3) -> np.ndarray:
        last: Exception | None = None
        for attempt in range(1, tries + 1):
            try:
                self.call("Page.bringToFront", timeout=10)
                self.eval("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
                result = self.call(
                    "Page.captureScreenshot",
                    {
                        "format": "png",
                        "fromSurface": True,
                        "captureBeyondViewport": False,
                        "clip": clip,
                    },
                    timeout=30,
                )
                data = base64.b64decode(result["data"])
                path.write_bytes(data)
                return np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))
            except Exception as exc:  # bounded retry, with exact failure surfaced
                last = exc
                print(f"SCREENSHOT_RETRY attempt={attempt} error={type(exc).__name__}:{exc}", flush=True)
                time.sleep(0.7 * attempt)
        raise RuntimeError(f"screenshot failed after {tries} attempts: {last}")


def diff_metrics(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    d = np.max(np.abs(a.astype(np.int16) - b.astype(np.int16)), axis=2)
    m = d >= 3
    if m.any():
        ys, xs = np.where(m)
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        q = [round(float(v), 3) for v in np.quantile(d[m], [0.5, 0.95, 0.99, 1.0])]
    else:
        bbox, q = None, []
    return {
        "diff_pixels": int(m.sum()),
        "diff_fraction": float(m.mean()),
        "bbox": bbox,
        "delta_quantiles": q,
    }


def red_mask(im: np.ndarray) -> np.ndarray:
    r, g, b = (im[:, :, i].astype(np.float32) for i in range(3))
    return (r > 105) & (r > g * 1.28) & (r > b * 1.18)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--port", type=int, default=9238)
    ap.add_argument("--expression-register", default="anime_90s")
    ap.add_argument("--expression", default="anime_fassungslos")
    args = ap.parse_args()

    root = args.visual_root.resolve()
    html = root / "buehne.html"
    open_plate = root / "augen_blink_relief2" / "blink_000.png"
    got_html = sha256_file(html)
    got_open = sha256_file(open_plate)
    if got_html != EXPECTED_HTML_SHA256:
        raise SystemExit(f"FAIL HTML drift {got_html}")
    if got_open != EXPECTED_OPEN_PLATE_SHA256:
        raise SystemExit(f"FAIL open-plate drift {got_open}")

    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    before_html = got_html

    tmp = Path(tempfile.mkdtemp(prefix="f2-expression-eye-ab-"))
    stdout_f = (tmp / "chrome.stdout").open("wb")
    stderr_f = (tmp / "chrome.stderr").open("wb")
    proc = subprocess.Popen(
        [
            "google-chrome", "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
            f"--remote-debugging-port={args.port}", "--remote-allow-origins=*",
            f"--user-data-dir={tmp / 'profile'}", f"--window-size={VIEWPORT_W},{VIEWPORT_H}", URL,
        ],
        stdout=stdout_f,
        stderr=stderr_f,
    )
    cdp: CDP | None = None
    try:
        target = None
        for _ in range(120):
            try:
                tabs = requests.get(f"http://127.0.0.1:{args.port}/json/list", timeout=0.5).json()
                target = next((t for t in tabs if t.get("type") == "page" and "127.0.0.1:8788" in t.get("url", "")), None)
                if target:
                    break
            except Exception:
                pass
            time.sleep(0.1)
        if not target:
            raise SystemExit("TARGET_PAGE_NOT_FOUND")

        cdp = CDP(target["webSocketDebuggerUrl"], timeout=20)
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        for _ in range(100):
            if cdp.eval("document.readyState") == "complete" and cdp.eval("!!document.getElementById('pupillen-glow')"):
                break
            time.sleep(0.1)

        cdp.eval(
            f"(()=>{{sonderausdruckZeigen({json.dumps(args.expression_register)},"
            f"{json.dumps(args.expression)},15000); return true}})()"
        )
        time.sleep(1.0)
        if not cdp.eval("typeof _sonderLaeuft!=='undefined' && _sonderLaeuft===true"):
            raise SystemExit("FAIL expression did not enter _sonderLaeuft")

        rect = json.loads(cdp.eval(
            "JSON.stringify((()=>{const r=document.getElementById('pupillen-glow').getBoundingClientRect();"
            "return {x:r.x,y:r.y,width:r.width,height:r.height}})())"
        ))
        pad = 70.0
        x = max(0.0, float(rect["x"]) - pad)
        y = max(0.0, float(rect["y"]) - pad)
        want_w = float(rect["width"]) + 2 * pad
        want_h = float(rect["height"]) + 2 * pad
        clip = {
            "x": x,
            "y": y,
            "width": max(1.0, min(float(VIEWPORT_W) - x, want_w)),
            "height": max(1.0, min(float(VIEWPORT_H) - y, want_h)),
            "scale": 1.0,
        }

        phase = []
        base_opacity = cdp.eval("getComputedStyle(document.getElementById('pupillen-glow')).opacity")
        phase.append({"phase": "expression_native", "glow_opacity": base_opacity})
        native = cdp.screenshot(out / "01_expression_native.png", clip)

        # Candidate A: canonical open eye plate only. Reuse productive relief2
        # and the existing eye geometry; do not add a second eye DOM authority.
        cdp.eval(
            "(()=>{const e=document.getElementById('augen-blink');"
            "e.src='/augen_blink/blink_000.png';e.style.opacity='1';return true})()"
        )
        time.sleep(0.25)
        eye = cdp.screenshot(out / "02_expression_canonical_eye.png", clip)
        phase.append({"phase": "expression_canonical_eye", "blink_opacity": cdp.eval("getComputedStyle(document.getElementById('augen-blink')).opacity")})

        # Candidate B: same canonical eye plate plus existing measured gaze
        # geometry. Full opacity is forced only to make compositing measurable.
        cdp.eval(
            "(()=>{const s=document.createElement('style');s.id='gate-eye-glow';"
            "s.textContent='#pupillen-glow{opacity:1!important}';document.head.appendChild(s);return true})()"
        )
        time.sleep(0.25)
        eye_gaze = cdp.screenshot(out / "03_expression_canonical_eye_gaze.png", clip)
        phase.append({"phase": "expression_canonical_eye_gaze", "glow_opacity": cdp.eval("getComputedStyle(document.getElementById('pupillen-glow')).opacity")})

        m_eye = diff_metrics(native, eye)
        m_gaze = diff_metrics(eye, eye_gaze)
        r_eye, r_gaze = red_mask(eye), red_mask(eye_gaze)
        inter = int((r_eye & r_gaze).sum())
        union = int((r_eye | r_gaze).sum())

        report = {
            "schema": "FRANK_AVATAR_EXPRESSION_EYE_AB/v2",
            "scope": "ISOLATED_BROWSER_RUNTIME_DOM_AB_NO_SOURCE_WRITE",
            "gaze_phase_scope": "GEOMETRY_COMPOSITING_ONLY_NOT_PRESENCE_AUTHORITY",
            "live_subject": {
                "buehne_html_sha256": before_html,
                "productive_relief2_open_plate_sha256": got_open,
            },
            "expression": {"register": args.expression_register, "name": args.expression},
            "clip": clip,
            "phases": phase,
            "native_to_canonical_eye": m_eye,
            "canonical_eye_to_gaze": m_gaze,
            "red_mask_iou_eye_vs_gaze": float(inter / max(1, union)),
            "source_mutation": False,
        }
        (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

        after_html = sha256_file(html)
        if after_html != before_html:
            raise SystemExit(f"FAIL source mutation {before_html} -> {after_html}")
        if m_eye["diff_pixels"] == 0:
            raise SystemExit("FAIL canonical eye plate produced no visible delta")
        if m_gaze["diff_pixels"] == 0:
            raise SystemExit("FAIL gaze produced no visible delta")

        print(json.dumps(report, sort_keys=True))
        print("EXPRESSION_EYE_AB_HARNESS=PASS")
        return 0
    finally:
        if cdp is not None:
            try:
                cdp.close()
            except Exception:
                pass
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        stdout_f.close()
        stderr_f.close()


if __name__ == "__main__":
    raise SystemExit(main())
