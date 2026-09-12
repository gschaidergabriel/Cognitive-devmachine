#!/usr/bin/env python3
"""Post-install live browser gate for canonical eye identity.

Run only after promote_semantic_shadow.py reports
INSTALLED_PENDING_POST_LIVE_GATE. This validator performs no source writes. It
binds both filesystem and HTTP page bytes to the exact accepted candidate, then
exercises the real live special-expression + blink path and records bounded
runtime evidence.

Failure means the installation is NOT accepted. Use the promotion manifest's
rollback artifact; do not claim live credit from a merely installed candidate.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any
from urllib.request import Request, urlopen

import requests
import websocket

EXPECTED_LIVE_SHA256 = "4fb62046e650f993edb89be24c40262fb8e7202e2c7cda14df7aa0113cfbfb4d"
EXPECTED_OPEN_PLATE_SHA256 = "8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9"
URL = "http://127.0.0.1:8788/"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def http_sha(url: str) -> tuple[str, int, str | None]:
    req = Request(url, headers={"Cache-Control": "no-cache", "Pragma": "no-cache"})
    with urlopen(req, timeout=10) as response:
        body = response.read()
        return hashlib.sha256(body).hexdigest(), int(response.status), response.headers.get("Content-Type")


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
    return json.loads(
        cdp.eval(
            "JSON.stringify({special:_sonderLaeuft,phase:blinzelPhase,"
            "blinkOpacity:getComputedStyle(document.getElementById('augen-blink')).opacity,"
            "blinkSrc:document.getElementById('augen-blink').src,"
            "glowOpacity:getComputedStyle(document.getElementById('pupillen-glow')).opacity,"
            "shadowMarker:document.querySelector('meta[name=go-eye-shadow]')?.content||null})"
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--cdp-port", type=int, default=9264)
    ap.add_argument("--expression-register", default="anime_90s")
    ap.add_argument("--expression", default="anime_fassungslos")
    args = ap.parse_args()

    visual = args.visual_root.resolve()
    live = visual / "buehne.html"
    open_plate = visual / "augen_blink_relief2" / "blink_000.png"
    out = args.out.resolve()
    got_live = sha256_file(live)
    got_open = sha256_file(open_plate)
    served_sha, served_status, served_type = http_sha(URL)
    if got_live != EXPECTED_LIVE_SHA256:
        raise SystemExit(f"FAIL live filesystem subject {got_live}")
    if got_open != EXPECTED_OPEN_PLATE_SHA256:
        raise SystemExit(f"FAIL open-eye subject {got_open}")
    if served_status != 200 or served_sha != EXPECTED_LIVE_SHA256:
        raise SystemExit(f"FAIL live HTTP subject status={served_status} sha={served_sha}")
    out.mkdir(parents=True, exist_ok=False)

    tmp = Path(tempfile.mkdtemp(prefix="f2-eye-postlive-"))
    stdout_f = (tmp / "chrome.stdout").open("wb")
    stderr_f = (tmp / "chrome.stderr").open("wb")
    proc = subprocess.Popen(
        [
            "google-chrome", "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
            f"--remote-debugging-port={args.cdp_port}", "--remote-allow-origins=*",
            f"--user-data-dir={tmp / 'profile'}", "--window-size=1536,1024", URL,
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
                target = next((t for t in tabs if t.get("type") == "page" and "127.0.0.1:8788" in t.get("url", "")), None)
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
            raise SystemExit("LIVE_RUNTIME_NOT_READY")

        initial = state(cdp)
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
        cdp.screenshot(out / "01_live_special_open.png")

        cdp.eval(
            "(()=>{window.__goRaf=[];window.__goRafLast=null;window.__goRafDone=false;"
            "function f(t){if(window.__goRafLast!==null)window.__goRaf.push(t-window.__goRafLast);"
            "window.__goRafLast=t;if(window.__goRaf.length>=240){window.__goRafDone=true;return;}"
            "requestAnimationFrame(f)}requestAnimationFrame(f);blinzeln(false);return true})()"
        )

        samples: list[dict[str, Any]] = []
        t0 = time.monotonic()
        closed_capture = False
        seen_active = False
        while time.monotonic() - t0 < 2.8:
            row = state(cdp)
            row["wall_ms"] = (time.monotonic() - t0) * 1000.0
            samples.append(row)
            if row.get("phase") is not None:
                seen_active = True
            if row.get("phase") == "zu" and not closed_capture:
                cdp.screenshot(out / "02_live_special_closed.png")
                closed_capture = True
            if seen_active and row.get("phase") is None and time.monotonic() - t0 > 0.45:
                break
            time.sleep(0.012)
        post = state(cdp)
        cdp.screenshot(out / "03_live_special_after_blink.png")

        for _ in range(300):
            if cdp.eval("window.__goRafDone===true"):
                break
            time.sleep(0.02)
        raf = cdp.eval("window.__goRaf")
        if not isinstance(raf, list) or len(raf) < 120:
            raise SystemExit(f"INSUFFICIENT_RAF_SAMPLES {len(raf) if isinstance(raf,list) else -1}")

        phases = sorted({str(r.get("phase")) for r in samples if r.get("phase") is not None})
        frames = sorted({str(r.get("blinkSrc", "")).rsplit("/", 1)[-1] for r in samples if "blink_" in str(r.get("blinkSrc", ""))})
        active = [r for r in samples if r.get("phase") is not None]
        opacity_bad = [r for r in active if str(r.get("blinkOpacity")) != "1"]
        glow_bad = [r for r in active if str(r.get("glowOpacity")) != "0"]
        special_bad = [r for r in samples if r.get("special") is not True]
        raf_values = [float(x) for x in raf]
        raf_sorted = sorted(raf_values)
        p95 = raf_sorted[int(0.95 * (len(raf_sorted) - 1))]
        fps = 1000.0 / (sum(raf_values) / len(raf_values))
        final_fs = sha256_file(live)
        final_http, final_status, _ = http_sha(URL)

        checks = {
            "shadow_marker_present": bool(initial.get("shadowMarker")),
            "special_active_before_blink": pre.get("special") is True,
            "special_active_after_blink": post.get("special") is True,
            "closing_phase_observed": "halb1" in phases,
            "closed_phase_observed": "zu" in phases,
            "opening_phase_observed": "halb2" in phases,
            "enough_distinct_blink_frames": len(frames) >= 9,
            "canonical_eye_opaque_during_blink": not opacity_bad,
            "glow_hidden_during_lid_activity": not glow_bad,
            "special_expression_never_dropped": not special_bad,
            "restored_frame_zero": str(post.get("blinkSrc", "")).endswith("/augen_blink/blink_000.png"),
            "restored_open_opacity": post.get("blinkOpacity") == "1",
            "blink_phase_cleared": post.get("phase") is None,
            "closed_capture_observed": closed_capture,
            "raf_fps_ge_58": fps >= 58.0,
            "raf_p95_le_18ms": p95 <= 18.0,
            "filesystem_subject_stable": final_fs == EXPECTED_LIVE_SHA256,
            "http_subject_stable": final_status == 200 and final_http == EXPECTED_LIVE_SHA256,
        }
        report = {
            "schema": "GO_AVATAR_EYE_POST_LIVE_RUNTIME/v1",
            "scope": "REAL_LIVE_BROWSER_POST_INSTALL_READBACK",
            "live_sha256": final_fs,
            "http_sha256": final_http,
            "http_content_type": served_type,
            "open_plate_sha256": got_open,
            "expression": {"register": args.expression_register, "name": args.expression},
            "initial": initial, "pre": pre, "post": post,
            "phases": phases, "frame_names": frames, "sample_count": len(samples),
            "active_sample_count": len(active), "opacity_bad_count": len(opacity_bad),
            "glow_bad_count": len(glow_bad), "special_bad_count": len(special_bad),
            "raf": {"samples": len(raf_values), "fps": fps, "p95_ms": p95, "max_ms": max(raf_values)},
            "checks": checks,
            "source_mutation": False,
        }
        (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
        if not all(checks.values()):
            raise SystemExit("POST_LIVE_EYE_GATE_FAIL")
        print("POST_LIVE_EYE_GATE=PASS")
        return 0
    finally:
        if cdp is not None:
            try: cdp.close()
            except Exception: pass
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill()
        stdout_f.close(); stderr_f.close()


if __name__ == "__main__":
    raise SystemExit(main())
