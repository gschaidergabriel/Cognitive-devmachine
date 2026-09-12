#!/usr/bin/env python3
"""Robust isolated runtime discriminator for the canonical-eye shadow.

V2 intentionally avoids long CDP awaitPromise calls. Browser state is sampled
with short synchronous Runtime.evaluate calls against wall-clock time so a
transport timeout cannot masquerade as a product failure.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import tempfile
import threading
import time
from typing import Any

import requests
import websocket

EXPECTED_LIVE_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
EXPECTED_OPEN_PLATE_SHA256 = "8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9"
EXPECTED_SHADOW_SHA256 = "4fb62046e650f993edb89be24c40262fb8e7202e2c7cda14df7aa0113cfbfb4d"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CDP:
    def __init__(self, ws_url: str, timeout: float = 20.0):
        self.ws = websocket.create_connection(ws_url, timeout=timeout, origin="http://localhost")
        self.seq = 0

    def close(self) -> None:
        self.ws.close()

    def call(self, method: str, params: dict[str, Any] | None = None, timeout: float = 8.0) -> dict[str, Any]:
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

    def eval(self, expression: str, timeout: float = 8.0) -> Any:
        result = self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": False},
            timeout=timeout,
        )
        obj = result.get("result", {})
        if obj.get("subtype") == "error" or result.get("exceptionDetails"):
            raise RuntimeError(str(result))
        return obj.get("value")

    def screenshot(self, path: Path) -> None:
        result = self.call(
            "Page.captureScreenshot",
            {"format": "png", "fromSurface": True, "captureBeyondViewport": False},
            timeout=30,
        )
        path.write_bytes(base64.b64decode(result["data"]))


def state(cdp: CDP) -> dict[str, Any]:
    value = cdp.eval(
        "JSON.stringify({special:_sonderLaeuft,phase:blinzelPhase,"
        "blinkOpacity:getComputedStyle(document.getElementById('augen-blink')).opacity,"
        "blinkSrc:document.getElementById('augen-blink').src,"
        "glowOpacity:getComputedStyle(document.getElementById('pupillen-glow')).opacity})"
    )
    return json.loads(value)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", type=Path, required=True)
    ap.add_argument("--shadow", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--http-port", type=int, default=9254)
    ap.add_argument("--cdp-port", type=int, default=9255)
    ap.add_argument("--expression-register", default="anime_90s")
    ap.add_argument("--expression", default="anime_fassungslos")
    args = ap.parse_args()

    visual = args.visual_root.resolve()
    live = visual / "buehne.html"
    open_plate = visual / "augen_blink_relief2" / "blink_000.png"
    shadow = args.shadow.resolve()
    out = args.out.resolve()
    got_live, got_open, got_shadow = map(sha256_file, (live, open_plate, shadow))
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

    tmp = Path(tempfile.mkdtemp(prefix="f2-eye-shadow-runtime-v2-"))
    stdout_f = (tmp / "chrome.stdout").open("wb")
    stderr_f = (tmp / "chrome.stderr").open("wb")
    proc = subprocess.Popen(
        [
            "google-chrome", "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-web-security", f"--remote-debugging-port={args.cdp_port}",
            "--remote-allow-origins=*", f"--user-data-dir={tmp / 'profile'}",
            "--window-size=1536,1024", f"http://127.0.0.1:{args.http_port}/",
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

        ready = False
        for _ in range(120):
            try:
                ready = bool(cdp.eval(
                    "document.readyState==='complete' && typeof sonderausdruckZeigen==='function' && "
                    "typeof blinzeln==='function' && !!document.getElementById('augen-blink')"
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
        for _ in range(100):
            if cdp.eval("_sonderLaeuft===true"):
                break
            time.sleep(0.05)
        else:
            raise SystemExit("SPECIAL_EXPRESSION_NOT_ACTIVE")

        pre = state(cdp)
        cdp.screenshot(out / "01_special_expression_open.png")

        # Start a non-blocking rAF collector. Retrieval happens later through a
        # separate short Runtime.evaluate call.
        cdp.eval(
            "(()=>{window.__goRaf=[];window.__goRafLast=null;window.__goRafDone=false;"
            "function f(t){if(window.__goRafLast!==null)window.__goRaf.push(t-window.__goRafLast);"
            "window.__goRafLast=t;if(window.__goRaf.length>=240){window.__goRafDone=true;return;}"
            "requestAnimationFrame(f)}requestAnimationFrame(f);return true})()"
        )
        cdp.eval("(()=>{blinzeln(false);return true})()")

        samples: list[dict[str, Any]] = []
        t0 = time.monotonic()
        closed_captured = False
        seen_active = False
        while time.monotonic() - t0 < 2.8:
            row = state(cdp)
            row["wall_ms"] = (time.monotonic() - t0) * 1000.0
            samples.append(row)
            if row.get("phase") is not None:
                seen_active = True
            if row.get("phase") == "zu" and not closed_captured:
                cdp.screenshot(out / "02_special_expression_closed.png")
                closed_captured = True
            if seen_active and row.get("phase") is None and (time.monotonic() - t0) > 0.45:
                break
            time.sleep(0.012)
        post = state(cdp)
        cdp.screenshot(out / "03_special_expression_after_blink.png")

        raf_done = False
        for _ in range(300):
            raf_done = bool(cdp.eval("window.__goRafDone===true"))
            if raf_done:
                break
            time.sleep(0.02)
        raf = cdp.eval("window.__goRaf")
        if not isinstance(raf, list) or len(raf) < 120:
            raise SystemExit(f"INSUFFICIENT_RAF_SAMPLES {len(raf) if isinstance(raf,list) else -1}")

        phases = sorted({str(r.get("phase")) for r in samples if r.get("phase") is not None})
        frame_names = sorted({str(r.get("blinkSrc", "")).rsplit("/", 1)[-1] for r in samples if "blink_" in str(r.get("blinkSrc", ""))})
        active = [r for r in samples if r.get("phase") is not None]
        opacity_bad = [r for r in active if str(r.get("blinkOpacity")) != "1"]
        glow_bad = [r for r in active if str(r.get("glowOpacity")) != "0"]
        special_bad = [r for r in samples if r.get("special") is not True]
        raf_sorted = sorted(float(x) for x in raf)
        p95 = raf_sorted[int(0.95 * (len(raf_sorted) - 1))]
        fps = 1000.0 / (sum(raf_sorted) / len(raf_sorted))

        checks = {
            "special_active_before": pre["special"] is True,
            "special_active_after": post["special"] is True,
            "closed_phase_observed": "zu" in phases,
            "opening_phase_observed": "halb2" in phases,
            "closing_phase_observed": "halb1" in phases,
            "enough_distinct_blink_frames": len(frame_names) >= 9,
            "eye_layer_opaque_while_blinking": not opacity_bad,
            "glow_hidden_while_lid_active": not glow_bad,
            "special_never_dropped": not special_bad,
            "restored_frame_zero": post["blinkSrc"].endswith("/augen_blink/blink_000.png"),
            "restored_open_opacity": post["blinkOpacity"] == "1",
            "blink_phase_cleared": post["phase"] is None,
            "closed_screenshot_captured": closed_captured,
            "raf_fps_ge_58": fps >= 58.0,
            "raf_p95_le_18ms": p95 <= 18.0,
            "live_source_unchanged": sha256_file(live) == got_live,
        }
        report = {
            "schema": "GO_AVATAR_EYE_SHADOW_RUNTIME/v2",
            "scope": "ISOLATED_REAL_BROWSER_SHADOW_NO_LIVE_SOURCE_WRITE",
            "live_sha256": got_live,
            "shadow_sha256": got_shadow,
            "open_plate_sha256": got_open,
            "expression": {"register": args.expression_register, "name": args.expression},
            "pre": pre, "post": post,
            "sample_count": len(samples), "phases": phases, "frame_names": frame_names,
            "active_sample_count": len(active), "opacity_bad_count": len(opacity_bad),
            "glow_bad_count": len(glow_bad), "special_bad_count": len(special_bad),
            "raf": {"samples": len(raf_sorted), "done": raf_done, "fps": fps, "p95_ms": p95, "max_ms": max(raf_sorted)},
            "checks": checks, "source_mutation": False,
        }
        (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True))
        if not all(checks.values()):
            raise SystemExit("SHADOW_RUNTIME_GATE_FAIL")
        print("EYE_SHADOW_RUNTIME_GATE_V2=PASS")
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
