#!/usr/bin/env python3
"""Matched, frozen A/B for the canonical eye identity layer.

This discriminator exists because temporally separated screenshots of the live
avatar confound eye-compositing deltas with camera shake, breathing, expression
animation and other requestAnimationFrame-driven motion.

The test serves the already-built semantic shadow only, uses the live daemon as
asset authority through <base>, enters one real special expression, then pauses
Chrome virtual time. While time is frozen it captures the exact same rendered
state twice with only #augen-blink opacity toggled 0 -> 1. The resulting pixel
delta is therefore attributable to the canonical eye layer itself.

No live source or asset is written.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import tempfile
import threading
import time
from typing import Any

import numpy as np
from PIL import Image
import requests
import websocket

EXPECTED_LIVE_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
EXPECTED_OPEN_PLATE_SHA256 = "8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9"
EXPECTED_SHADOW_SHA256 = "4fb62046e650f993edb89be24c40262fb8e7202e2c7cda14df7aa0113cfbfb4d"
VIEWPORT_W = 1536
VIEWPORT_H = 1024


def sha256_file(path: Path) -> str:
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
            {"expression": expression, "returnByValue": True, "awaitPromise": False},
            timeout=10,
        )
        obj = result.get("result", {})
        if obj.get("subtype") == "error" or result.get("exceptionDetails"):
            raise RuntimeError(str(result))
        return obj.get("value")

    def screenshot(self, path: Path) -> np.ndarray:
        result = self.call(
            "Page.captureScreenshot",
            {"format": "png", "fromSurface": True, "captureBeyondViewport": False},
            timeout=30,
        )
        data = base64.b64decode(result["data"])
        path.write_bytes(data)
        return np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))


def diff_metrics(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    if a.shape != b.shape:
        raise RuntimeError(f"shape mismatch {a.shape} != {b.shape}")
    delta = np.max(np.abs(a.astype(np.int16) - b.astype(np.int16)), axis=2)
    changed = delta >= 3
    n = int(changed.sum())
    if n:
        ys, xs = np.where(changed)
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        q = [round(float(x), 3) for x in np.quantile(delta[changed], [0.5, 0.95, 0.99, 1.0])]
    else:
        bbox, q = None, []
    return {
        "diff_pixels": n,
        "diff_fraction_full_canvas": float(changed.mean()),
        "bbox": bbox,
        "delta_quantiles": q,
    }


def edge_energy(im: np.ndarray, region: tuple[int, int, int, int]) -> float:
    x0, y0, x1, y1 = region
    crop = im[y0:y1, x0:x1].astype(np.float32).mean(axis=2)
    if crop.size == 0 or crop.shape[0] < 3 or crop.shape[1] < 3:
        return 0.0
    gx = np.abs(np.diff(crop, axis=1))
    gy = np.abs(np.diff(crop, axis=0))
    return float((gx.mean() + gy.mean()) * 0.5)


def bbox_expand(bbox: list[int], pad: int, w: int, h: int) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return max(0, x0-pad), max(0, y0-pad), min(w, x1+pad), min(h, y1+pad)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", type=Path, required=True)
    ap.add_argument("--shadow", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--http-port", type=int, default=9260)
    ap.add_argument("--cdp-port", type=int, default=9261)
    ap.add_argument("--expression-register", default="anime_90s")
    ap.add_argument("--expression", default="anime_fassungslos")
    args = ap.parse_args()

    visual = args.visual_root.resolve()
    live = visual / "buehne.html"
    open_plate = visual / "augen_blink_relief2" / "blink_000.png"
    shadow = args.shadow.resolve()
    out = args.out.resolve()

    got_live = sha256_file(live)
    got_open = sha256_file(open_plate)
    got_shadow = sha256_file(shadow)
    if got_live != EXPECTED_LIVE_SHA256:
        raise SystemExit(f"FAIL live subject drift {got_live}")
    if got_open != EXPECTED_OPEN_PLATE_SHA256:
        raise SystemExit(f"FAIL open plate drift {got_open}")
    if got_shadow != EXPECTED_SHADOW_SHA256:
        raise SystemExit(f"FAIL shadow drift {got_shadow}")
    out.mkdir(parents=True, exist_ok=False)

    html = shadow.read_text(encoding="utf-8")
    if html.count("<head>") != 1:
        raise SystemExit("FAIL shadow head count")
    served = html.replace(
        "<head>", '<head>\n<base href="http://127.0.0.1:8788/">', 1
    ).encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path.split("?", 1)[0] in ("/", "/buehne.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(served)))
                self.end_headers()
                self.wfile.write(served)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, fmt: str, *items: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", args.http_port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    tmp = Path(tempfile.mkdtemp(prefix="f2-eye-matched-ab-"))
    stdout_f = (tmp / "chrome.stdout").open("wb")
    stderr_f = (tmp / "chrome.stderr").open("wb")
    proc = subprocess.Popen(
        [
            "google-chrome", "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-web-security", f"--remote-debugging-port={args.cdp_port}",
            "--remote-allow-origins=*", f"--user-data-dir={tmp / 'profile'}",
            f"--window-size={VIEWPORT_W},{VIEWPORT_H}", f"http://127.0.0.1:{args.http_port}/",
        ],
        stdout=stdout_f,
        stderr=stderr_f,
    )
    cdp: CDP | None = None
    try:
        target = None
        for _ in range(150):
            try:
                tabs = requests.get(f"http://127.0.0.1:{args.cdp_port}/json/list", timeout=0.5).json()
                target = next((t for t in tabs if t.get("type") == "page" and f"127.0.0.1:{args.http_port}" in t.get("url", "")), None)
                if target:
                    break
            except Exception:
                pass
            time.sleep(0.1)
        if not target:
            raise SystemExit("TARGET_PAGE_NOT_FOUND")
        cdp = CDP(target["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call("Emulation.setVirtualTimePolicy", {"policy": "advance", "budget": 1000.0})

        ready = False
        for _ in range(120):
            try:
                ready = bool(cdp.eval(
                    "document.readyState==='complete' && typeof sonderausdruckZeigen==='function' && "
                    "!!document.getElementById('augen-blink')"
                ))
            except Exception:
                ready = False
            if ready:
                break
            time.sleep(0.1)
        if not ready:
            raise SystemExit("SHADOW_RUNTIME_NOT_READY")

        cdp.eval(
            f"(()=>{{sonderausdruckZeigen({json.dumps(args.expression_register)},"
            f"{json.dumps(args.expression)},15000);return true}})()"
        )
        time.sleep(0.25)
        if cdp.eval("_sonderLaeuft===true") is not True:
            raise SystemExit("SPECIAL_EXPRESSION_NOT_ACTIVE")

        # Freeze JS timers/rAF at one exact state. DOM changes and screenshots
        # remain available through CDP while page virtual time is paused.
        cdp.call("Emulation.setVirtualTimePolicy", {"policy": "pause"})
        geometry = json.loads(cdp.eval(
            "JSON.stringify((()=>{const e=document.getElementById('augen-blink');"
            "const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,"
            "src:e.src,transform:getComputedStyle(e).transform,z:getComputedStyle(e).zIndex}})())"
        ))

        # Baseline: exact same frozen special-expression state, canonical eye off.
        cdp.eval("document.getElementById('augen-blink').style.opacity='0';true")
        eye_off = cdp.screenshot(out / "01_frozen_eye_off.png")

        # Candidate: only eye opacity changes. Route/src/geometry are unchanged.
        cdp.eval(
            "(()=>{const e=document.getElementById('augen-blink');"
            "e.src='/augen_blink/blink_000.png';e.style.opacity='1';return true})()"
        )
        eye_on = cdp.screenshot(out / "02_frozen_eye_on.png")

        # Repeat off to detect any residual non-eye instability while paused.
        cdp.eval("document.getElementById('augen-blink').style.opacity='0';true")
        eye_off_repeat = cdp.screenshot(out / "03_frozen_eye_off_repeat.png")

        ab = diff_metrics(eye_off, eye_on)
        stability = diff_metrics(eye_off, eye_off_repeat)
        if ab["bbox"] is None:
            raise SystemExit("FAIL eye layer produced zero matched delta")
        ring = bbox_expand(ab["bbox"], 6, VIEWPORT_W, VIEWPORT_H)
        off_edge = edge_energy(eye_off, ring)
        on_edge = edge_energy(eye_on, ring)
        ratio = on_edge / max(off_edge, 1e-9)

        # Relief2's mapped nonzero mask is ~0.9863% of full canvas. Allow a
        # conservative envelope for CSS resampling/antialiasing but reject any
        # old near-rectangular full-patch behavior.
        checks = {
            "virtual_time_frozen_stable": stability["diff_pixels"] == 0,
            "eye_delta_present": ab["diff_pixels"] > 100,
            "eye_delta_fraction_below_2pct": ab["diff_fraction_full_canvas"] < 0.02,
            "eye_delta_fraction_above_noise": ab["diff_fraction_full_canvas"] > 0.001,
            "edge_energy_ratio_below_1_35": ratio < 1.35,
            "canonical_route_retained": geometry["src"].endswith("/augen_blink/blink_000.png"),
            "live_source_unchanged": sha256_file(live) == got_live,
        }
        report = {
            "schema": "GO_AVATAR_EYE_MATCHED_FROZEN_AB/v1",
            "scope": "ISOLATED_REAL_BROWSER_VIRTUAL_TIME_FROZEN_NO_LIVE_SOURCE_WRITE",
            "live_sha256": got_live,
            "shadow_sha256": got_shadow,
            "open_plate_sha256": got_open,
            "expression": {"register": args.expression_register, "name": args.expression},
            "geometry": geometry,
            "eye_off_to_on": ab,
            "eye_off_repeat_stability": stability,
            "edge_ring": list(ring),
            "edge_energy": {"off": off_edge, "on": on_edge, "ratio": ratio},
            "checks": checks,
            "source_mutation": False,
        }
        (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True))
        if not all(checks.values()):
            raise SystemExit("MATCHED_EYE_AB_GATE_FAIL")
        print("MATCHED_EYE_AB_GATE=PASS")
        return 0
    finally:
        if cdp is not None:
            try: cdp.close()
            except Exception: pass
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill()
        stdout_f.close(); stderr_f.close(); server.shutdown(); server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
