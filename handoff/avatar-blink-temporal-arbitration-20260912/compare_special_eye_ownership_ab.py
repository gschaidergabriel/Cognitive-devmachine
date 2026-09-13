#!/usr/bin/env python3
"""Matched non-live A/B discriminator for special-expression eye ownership.

A = exact live Contract A semantics: special expression owns its eyes; blinzeln()
    keeps the current _sonderLaeuft guard.
B = minimal isolated Contract B semantics: remove only that one guard, allowing
    a one-shot blink while the special expression is already at its plateau.

The experiment never writes the production source and never opens/reuses the
production browser. It launches isolated headless scratch Chrome instances.
It intentionally does NOT decide which semantic is better; it produces matched
runtime/pixel evidence for coordinator/owner review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import requests
import websocket

EXPECTED_SOURCE_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_braced_region(text: str, open_brace: int) -> tuple[int, int]:
    depth = 0
    for i in range(open_brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return open_brace, i + 1
    raise RuntimeError("unterminated block")


def build_b(source: str) -> tuple[str, str]:
    sig = "function blinzeln(zeitplanNeu = true){"
    start = source.find(sig)
    if start < 0:
        raise RuntimeError("blinzeln signature missing")
    open_brace = source.find("{", start)
    _, end = find_braced_region(source, open_brace)
    fn = source[start:end]
    m = re.search(r"if\s*\(\s*_sonderLaeuft\s*\)\s*\{", fn)
    if not m:
        raise RuntimeError("special-expression guard missing")
    guard_open = fn.find("{", m.start())
    _, guard_end = find_braced_region(fn, guard_open)
    removed = fn[m.start():guard_end]
    if "return" not in removed or "blinzelWeiterPlanen" not in removed:
        raise RuntimeError(f"unexpected guard: {removed!r}")
    rewritten_fn = fn[:m.start()] + fn[guard_end:]
    candidate = source[:start] + rewritten_fn + source[end:]
    # Exact one-change roundtrip.
    if candidate == source:
        raise RuntimeError("B candidate no-op")
    restored_fn = rewritten_fn[:m.start()] + removed + rewritten_fn[m.start():]
    restored = candidate[:start] + restored_fn + candidate[start + len(rewritten_fn):]
    if restored != source:
        raise RuntimeError("B candidate roundtrip mismatch")
    return candidate, sha256(removed.encode())


class CDP:
    def __init__(self, url: str, timeout: float = 20.0):
        self.ws = websocket.create_connection(url, timeout=timeout)
        self.next_id = 0

    def call(self, method: str, params: dict[str, Any] | None = None, timeout: float = 20.0) -> dict[str, Any]:
        self.next_id += 1
        ident = self.next_id
        self.ws.settimeout(timeout)
        self.ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == ident:
                if "error" in msg:
                    raise RuntimeError(f"CDP {method}: {msg['error']}")
                return msg.get("result", {})

    def eval(self, expr: str, timeout: float = 20.0) -> Any:
        result = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True}, timeout)
        return result.get("result", {}).get("value")

    def screenshot(self, path: Path) -> None:
        import base64
        data = self.call("Page.captureScreenshot", {"format": "png", "fromSurface": True}, 20.0)["data"]
        path.write_bytes(base64.b64decode(data))

    def close(self) -> None:
        self.ws.close()


def serve_bytes(payload: bytes, port: int) -> tuple[ThreadingHTTPServer, threading.Thread]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path.split("?", 1)[0] in ("/", "/buehne.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            else:
                self.send_response(404)
                self.end_headers()
        def log_message(self, fmt: str, *args: object) -> None:
            return
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    return srv, th


def browser_binary() -> str:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p:
            return p
    raise RuntimeError("no Chrome/Chromium binary")


def wait_target(cdp_port: int, http_port: int) -> dict[str, Any]:
    for _ in range(160):
        try:
            tabs = requests.get(f"http://127.0.0.1:{cdp_port}/json/list", timeout=0.5).json()
            for t in tabs:
                if t.get("type") == "page" and f"127.0.0.1:{http_port}" in t.get("url", ""):
                    return t
        except Exception:
            pass
        time.sleep(0.1)
    raise RuntimeError("scratch browser target not found")


def run_condition(name: str, html: str, out: Path, http_port: int, cdp_port: int) -> dict[str, Any]:
    # Assets/API remain bound to the real existing service, but HTML is served
    # from this isolated scratch origin. <base> does not mutate production.
    if html.count("<head>") != 1:
        raise RuntimeError("unexpected head count")
    served = html.replace("<head>", '<head>\n<base href="http://127.0.0.1:8788/">', 1).encode()
    srv, _ = serve_bytes(served, http_port)
    tmp = Path(tempfile.mkdtemp(prefix=f"avatar-eye-{name.lower()}-"))
    stdout_f = (tmp / "chrome.stdout").open("wb")
    stderr_f = (tmp / "chrome.stderr").open("wb")
    proc = subprocess.Popen([
        browser_binary(), "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
        "--disable-web-security", "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows",
        f"--remote-debugging-port={cdp_port}", "--remote-allow-origins=*",
        f"--user-data-dir={tmp/'profile'}", "--window-size=1536,1024",
        f"http://127.0.0.1:{http_port}/",
    ], stdout=stdout_f, stderr=stderr_f)
    cdp: CDP | None = None
    try:
        target = wait_target(cdp_port, http_port)
        cdp = CDP(target["webSocketDebuggerUrl"], timeout=20.0)
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        ready = False
        for _ in range(160):
            try:
                ready = bool(cdp.eval("document.readyState==='complete' && typeof sonderausdruckZeigen==='function' && typeof blinzeln==='function' && !!document.getElementById('augen-blink')"))
            except Exception:
                ready = False
            if ready:
                break
            time.sleep(0.1)
        if not ready:
            raise RuntimeError("scratch page not ready")

        # Freeze recursive rAF and CSS animation/transition activity. Existing
        # scheduled rAF may fire once more; then recursive users receive 0.
        cdp.eval("""
        (()=>{
          window.requestAnimationFrame = function(){ return 0; };
          const st=document.createElement('style');
          st.textContent='*{animation:none!important;transition:none!important}';
          document.head.appendChild(st);
          return true;
        })()
        """)
        time.sleep(0.15)

        # Establish the same special-expression plateau in both conditions.
        cdp.eval("sonderausdruckZeigen('anime_90s','anime_fassungslos',5000); true")
        time.sleep(0.75)
        pre = out / f"{name}_01_special_plateau_preblink.png"
        cdp.screenshot(pre)
        pre_state = cdp.eval("""
        (()=>{const b=document.getElementById('augen-blink');const r=b.getBoundingClientRect();return {
          special:_sonderLaeuft,phase:blinzelPhase,opacity:getComputedStyle(b).opacity,src:b.src,
          rect:{x:r.x,y:r.y,w:r.width,h:r.height}
        }})()
        """)

        # One-shot only: no scheduler/fan-out. A must suppress; B may play.
        cdp.eval("blinzeln(false); true")
        samples = []
        closed_shot = None
        for _ in range(60):
            row = cdp.eval("""
            (()=>{const b=document.getElementById('augen-blink');return {
              ms:performance.now(),special:_sonderLaeuft,phase:blinzelPhase,
              opacity:getComputedStyle(b).opacity,src:b.src
            }})()
            """)
            samples.append(row)
            if closed_shot is None and row.get("phase") == "zu":
                closed_shot = out / f"{name}_02_special_during_closed_blink.png"
                cdp.screenshot(closed_shot)
            time.sleep(0.008)

        post = out / f"{name}_03_special_postblink.png"
        cdp.screenshot(post)
        post_state = cdp.eval("""
        (()=>{const b=document.getElementById('augen-blink');return {
          special:_sonderLaeuft,phase:blinzelPhase,opacity:getComputedStyle(b).opacity,src:b.src
        }})()
        """)
        return {
            "condition": name,
            "pre_state": pre_state,
            "post_state": post_state,
            "sample_count": len(samples),
            "phases": sorted({str(r.get('phase')) for r in samples if r.get('phase') is not None}),
            "distinct_blink_frames": sorted({str(r.get('src','')).rsplit('/',1)[-1] for r in samples if 'blink_' in str(r.get('src',''))}),
            "blink_activity_observed": any(r.get("phase") is not None for r in samples),
            "special_never_dropped": all(r.get("special") is True for r in samples),
            "closed_shot": str(closed_shot) if closed_shot else None,
            "pre_shot": str(pre),
            "post_shot": str(post),
        }
    finally:
        if cdp:
            try: cdp.close()
            except Exception: pass
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill()
        stdout_f.close(); stderr_f.close()
        srv.shutdown(); srv.server_close()


def pixel_metrics(a_path: Path, b_path: Path, rect: dict[str, Any]) -> dict[str, Any]:
    try:
        from PIL import Image, ImageChops, ImageStat
    except Exception as exc:
        return {"available": False, "reason": repr(exc)}
    a = Image.open(a_path).convert("RGB")
    b = Image.open(b_path).convert("RGB")
    if a.size != b.size:
        raise RuntimeError(f"screenshot size mismatch {a.size} != {b.size}")
    diff = ImageChops.difference(a, b)
    stat = ImageStat.Stat(diff)
    full_mae = sum(stat.mean) / 3.0
    x0 = max(0, int(rect["x"])); y0 = max(0, int(rect["y"]));
    x1 = min(a.width, int(rect["x"] + rect["w"] + 1)); y1 = min(a.height, int(rect["y"] + rect["h"] + 1))
    roi = diff.crop((x0, y0, x1, y1))
    roi_stat = ImageStat.Stat(roi)
    roi_mae = sum(roi_stat.mean) / 3.0
    # Changed fraction in ROI at any RGB delta > 3.
    px = list(roi.getdata())
    changed = sum(1 for p in px if max(p) > 3)
    return {
        "available": True,
        "full_mae": full_mae,
        "eye_box_mae": roi_mae,
        "eye_box_changed_fraction_gt3": changed / len(px) if px else None,
        "eye_box": [x0, y0, x1, y1],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--http-port-a", type=int, default=9392)
    ap.add_argument("--cdp-port-a", type=int, default=9393)
    ap.add_argument("--http-port-b", type=int, default=9394)
    ap.add_argument("--cdp-port-b", type=int, default=9395)
    args = ap.parse_args()

    raw = args.source.read_bytes()
    got = sha256(raw)
    if got != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"SOURCE_DRIFT expected={EXPECTED_SOURCE_SHA256} observed={got}")
    source = raw.decode("utf-8")
    condition_b, removed_guard_sha = build_b(source)
    args.out.mkdir(parents=True, exist_ok=False)

    a = run_condition("A", source, args.out, args.http_port_a, args.cdp_port_a)
    b = run_condition("B", condition_b, args.out, args.http_port_b, args.cdp_port_b)

    metrics = None
    if a.get("pre_shot") and b.get("closed_shot"):
        metrics = pixel_metrics(Path(a["pre_shot"]), Path(b["closed_shot"]), a["pre_state"]["rect"])

    checks = {
        "A_special_active": a["pre_state"].get("special") is True,
        "A_suppresses_forced_blink": a["blink_activity_observed"] is False,
        "B_special_active": b["pre_state"].get("special") is True,
        "B_runs_forced_blink": b["blink_activity_observed"] is True,
        "B_closed_phase_observed": "zu" in b["phases"],
        "special_never_dropped_A": a["special_never_dropped"],
        "special_never_dropped_B": b["special_never_dropped"],
        "source_unchanged": sha256(args.source.read_bytes()) == got,
    }
    report = {
        "schema": "FRANK_AVATAR_SPECIAL_EYE_OWNERSHIP_AB/v1",
        "scope": "MATCHED_SHADOW_SEMANTIC_DISCRIMINATOR_NO_LIVE_WRITE",
        "source_sha256": got,
        "condition_A_sha256": got,
        "condition_B_sha256": sha256(condition_b.encode()),
        "condition_B_removed_guard_sha256": removed_guard_sha,
        "condition_A": a,
        "condition_B": b,
        "pixel_metrics_A_pre_vs_B_closed": metrics,
        "checks": checks,
        "mechanical_gate": "PASS" if all(checks.values()) else "FAIL",
        "semantic_winner": "UNDECIDED_REQUIRES_PERCEPTUAL_COORDINATOR_OWNER_EVIDENCE",
        "live_mutation": False,
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
