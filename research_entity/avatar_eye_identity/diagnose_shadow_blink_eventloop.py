#!/usr/bin/env python3
"""Three-condition causal discriminator for the semantic-shadow event-loop stall.

The transport-decoupled runtime gate v3 produced only two in-page timer samples.
This script asks whether that is caused by the shadow generally, by blinking in
normal mode, or specifically by blink playback while a special expression is
active. Each condition gets a fresh Chromium process and the exact same shadow
subject. No live source bytes are written.
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import tempfile
import threading
import time
from typing import Any

import requests

from validate_shadow_blink_runtime_v2 import CDP, sha256_file

EXPECTED_LIVE_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
EXPECTED_OPEN_PLATE_SHA256 = "8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9"
EXPECTED_SHADOW_SHA256 = "4fb62046e650f993edb89be24c40262fb8e7202e2c7cda14df7aa0113cfbfb4d"


def run_condition(url: str, cdp_port: int, mode: str, expression_register: str, expression: str) -> dict[str, Any]:
    tmp = Path(tempfile.mkdtemp(prefix=f"eye-eventloop-{mode}-"))
    stdout_f = (tmp / "chrome.stdout").open("wb")
    stderr_f = (tmp / "chrome.stderr").open("wb")
    proc = subprocess.Popen([
        "google-chrome", "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
        "--disable-web-security", f"--remote-debugging-port={cdp_port}",
        "--remote-allow-origins=*", f"--user-data-dir={tmp / 'profile'}",
        "--window-size=1536,1024", url,
    ], stdout=stdout_f, stderr=stderr_f)
    cdp: CDP | None = None
    result: dict[str, Any] = {"mode": mode, "final_read": False}
    try:
        target = None
        for _ in range(150):
            try:
                tabs = requests.get(f"http://127.0.0.1:{cdp_port}/json/list", timeout=0.5).json()
                target = next((t for t in tabs if t.get("type") == "page" and url in t.get("url", "")), None)
                if target:
                    break
            except Exception:
                pass
            time.sleep(0.1)
        if not target:
            result["error"] = "TARGET_PAGE_NOT_FOUND"
            return result
        cdp = CDP(target["webSocketDebuggerUrl"], timeout=10.0)
        cdp.call("Runtime.enable", timeout=10.0)
        ready = False
        for _ in range(100):
            try:
                ready = bool(cdp.eval(
                    "document.readyState==='complete' && typeof blinzeln==='function' && "
                    "typeof sonderausdruckZeigen==='function'", timeout=2.0))
            except Exception:
                ready = False
            if ready:
                break
            time.sleep(0.1)
        if not ready:
            result["error"] = "RUNTIME_NOT_READY"
            return result

        if mode.startswith("special"):
            cdp.eval(
                f"(()=>{{sonderausdruckZeigen({json.dumps(expression_register)},{json.dumps(expression)},15000);return true}})()",
                timeout=5.0,
            )
            active = False
            for _ in range(60):
                try:
                    active = bool(cdp.eval("_sonderLaeuft===true", timeout=1.0))
                except Exception:
                    active = False
                if active:
                    break
                time.sleep(0.05)
            if not active:
                result["error"] = "SPECIAL_NOT_ACTIVE"
                return result

        trigger_blink = mode.endswith("blink")
        js = f"""
(()=>{{
  const R=window.__goEventLoopDiag={{started:performance.now(),timerTicks:0,rafTicks:0,lastRaf:null,rafDeltas:[]}};
  R.interval=setInterval(()=>{{R.timerTicks++;}},10);
  function rf(t){{R.rafTicks++;if(R.lastRaf!==null)R.rafDeltas.push(t-R.lastRaf);R.lastRaf=t;requestAnimationFrame(rf);}}
  requestAnimationFrame(rf);
  {"blinzeln(false);" if trigger_blink else ""}
  return {{special:_sonderLaeuft===true,phase:blinzelPhase}};
}})()
"""
        result["start"] = cdp.eval(js, timeout=5.0)
        time.sleep(2.5)
        try:
            final_text = cdp.eval(
                "JSON.stringify((()=>{const R=window.__goEventLoopDiag||{};return {"
                "elapsed:performance.now()-(R.started||performance.now()),timerTicks:R.timerTicks||0,"
                "rafTicks:R.rafTicks||0,rafDeltas:R.rafDeltas||[],special:_sonderLaeuft===true,"
                "phase:blinzelPhase,blinkSrc:document.getElementById('augen-blink')?.src||null}})())",
                timeout=5.0,
            )
            final = json.loads(final_text)
            deltas = [float(x) for x in final.pop("rafDeltas", [])]
            final["raf_samples"] = len(deltas)
            if deltas:
                ds = sorted(deltas)
                final["raf_mean_ms"] = sum(ds)/len(ds)
                final["raf_p95_ms"] = ds[int(0.95*(len(ds)-1))]
            result["final"] = final
            result["final_read"] = True
        except Exception as exc:
            result["error"] = f"FINAL_READ_{type(exc).__name__}:{exc}"
        return result
    finally:
        if cdp is not None:
            try: cdp.close()
            except Exception: pass
        proc.terminate()
        try: proc.wait(timeout=3)
        except subprocess.TimeoutExpired: proc.kill()
        stdout_f.close(); stderr_f.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", type=Path, required=True)
    ap.add_argument("--shadow", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--http-port", type=int, default=9282)
    ap.add_argument("--cdp-port-base", type=int, default=9283)
    ap.add_argument("--expression-register", default="anime_90s")
    ap.add_argument("--expression", default="anime_fassungslos")
    args = ap.parse_args()

    visual = args.visual_root.resolve()
    live = visual / "buehne.html"
    open_plate = visual / "augen_blink_relief2" / "blink_000.png"
    shadow = args.shadow.resolve()
    out = args.out.resolve()
    got_live, got_open, got_shadow = map(sha256_file, (live, open_plate, shadow))
    if got_live != EXPECTED_LIVE_SHA256: raise SystemExit(f"LIVE_DRIFT {got_live}")
    if got_open != EXPECTED_OPEN_PLATE_SHA256: raise SystemExit(f"OPEN_DRIFT {got_open}")
    if got_shadow != EXPECTED_SHADOW_SHA256: raise SystemExit(f"SHADOW_DRIFT {got_shadow}")
    out.mkdir(parents=True, exist_ok=False)

    html = shadow.read_text(encoding="utf-8")
    served = html.replace("<head>", '<head>\n<base href="http://127.0.0.1:8788/">', 1).encode()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path.split("?",1)[0] in ("/","/buehne.html"):
                self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
                self.send_header("Content-Length",str(len(served))); self.end_headers(); self.wfile.write(served)
            else:
                self.send_response(404); self.end_headers()
        def log_message(self, fmt: str, *items: object) -> None: return
    server = ThreadingHTTPServer(("127.0.0.1",args.http_port),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        url=f"http://127.0.0.1:{args.http_port}/"
        modes=("special_no_blink","normal_blink","special_blink")
        rows=[run_condition(url,args.cdp_port_base+i,m,args.expression_register,args.expression) for i,m in enumerate(modes)]
        report={
            "schema":"GO_AVATAR_EYE_EVENTLOOP_CAUSAL_DIAG/v1",
            "scope":"EXACT_SHADOW_THREE_FRESH_BROWSER_CONDITIONS_NO_LIVE_WRITE",
            "live_sha256":got_live,"shadow_sha256":got_shadow,"open_plate_sha256":got_open,
            "rows":rows,"live_source_unchanged":sha256_file(live)==got_live,
        }
        (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,sort_keys=True))
        # This is a diagnostic, not a promotion gate. Successful execution means
        # all three conditions produced a readable causal record.
        if not all(r.get("final_read") is True for r in rows):
            raise SystemExit("EVENTLOOP_DIAG_INCOMPLETE")
        print("EYE_EVENTLOOP_DIAG=PASS")
        return 0
    finally:
        server.shutdown(); server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
