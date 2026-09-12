#!/usr/bin/env python3
"""Attribute semantic-shadow scheduler starvation without mutating live source.

Fresh Chromium per condition, exact live/shadow/open-eye identities.
Conditions:
  idle               exact shadow, no explicit blink/expression trigger
  normal_blink       exact shadow + one blinzeln(false)
  special_raw        exact shadow + one real sonderausdruckZeigen()
  special_predecoded preload the seven expression stages, then same special call

This is a diagnostic, not a promotion gate. It distinguishes a generally invalid
headless measurement surface from special-expression cold decode/raster pressure.
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


def wait_page(port: int, url: str) -> dict[str, Any] | None:
    for _ in range(160):
        try:
            tabs = requests.get(f"http://127.0.0.1:{port}/json/list", timeout=0.5).json()
            page = next((t for t in tabs if t.get("type") == "page" and url in t.get("url", "")), None)
            if page:
                return page
        except Exception:
            pass
        time.sleep(0.1)
    return None


def summarize_deltas(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"samples": 0, "fps": 0.0, "mean_ms": None, "p95_ms": None, "max_ms": None}
    ordered = sorted(values)
    mean = sum(values) / len(values)
    return {
        "samples": len(values),
        "fps": 1000.0 / mean if mean > 0 else 0.0,
        "mean_ms": mean,
        "p95_ms": ordered[int(0.95 * (len(ordered) - 1))],
        "max_ms": max(values),
    }


def run_condition(url: str, cdp_port: int, mode: str, register: str, expression: str) -> dict[str, Any]:
    tmp = Path(tempfile.mkdtemp(prefix=f"eye-scheduler-{mode}-"))
    stdout_f = (tmp / "chrome.stdout").open("wb")
    stderr_f = (tmp / "chrome.stderr").open("wb")
    proc = subprocess.Popen(
        [
            "google-chrome", "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
            "--disable-web-security", "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows",
            f"--remote-debugging-port={cdp_port}", "--remote-allow-origins=*",
            f"--user-data-dir={tmp / 'profile'}", "--window-size=1536,1024", url,
        ],
        stdout=stdout_f,
        stderr=stderr_f,
    )
    cdp: CDP | None = None
    row: dict[str, Any] = {"mode": mode, "final_read": False, "predecode_complete": None}
    try:
        target = wait_page(cdp_port, url)
        if not target:
            row["error"] = "TARGET_PAGE_NOT_FOUND"
            return row
        cdp = CDP(target["webSocketDebuggerUrl"], timeout=20.0)
        cdp.call("Runtime.enable", timeout=20.0)
        ready = False
        for _ in range(120):
            try:
                ready = bool(cdp.eval(
                    "document.readyState==='complete' && typeof blinzeln==='function' && "
                    "typeof sonderausdruckZeigen==='function' && typeof _sonderLaeuft!=='undefined'",
                    timeout=2.0,
                ))
            except Exception:
                ready = False
            if ready:
                break
            time.sleep(0.1)
        if not ready:
            row["error"] = "RUNTIME_NOT_READY"
            return row

        row["surface"] = cdp.eval(
            "(()=>({visibility:document.visibilityState,hidden:document.hidden,"
            "width:innerWidth,height:innerHeight,dpr:devicePixelRatio}))()",
            timeout=5.0,
        )

        if mode == "special_predecoded":
            urls = [f"/ausdruck_erweitert/{register}/{expression}/frontal/stufe_0{i}.png" for i in range(7)]
            cdp.eval(
                f"(()=>{{window.__goPredecode={json.dumps(urls)}.map(src=>{{const i=new Image();i.src=src;return i;}});return true}})()",
                timeout=5.0,
            )
            done = False
            for _ in range(300):
                try:
                    done = bool(cdp.eval(
                        "Array.isArray(window.__goPredecode)&&window.__goPredecode.length===7&&"
                        "window.__goPredecode.every(i=>i.complete&&i.naturalWidth>0)",
                        timeout=2.0,
                    ))
                except Exception:
                    done = False
                if done:
                    break
                time.sleep(0.05)
            row["predecode_complete"] = done
            if not done:
                row["error"] = "EXPRESSION_PREDECODE_INCOMPLETE"
                return row

        start_js = """
(()=>{
 const R=window.__goSchedulerAttrib={start:performance.now(),timerTicks:0,raf:[],last:null};
 R.interval=setInterval(()=>{R.timerTicks++;},10);
 function rf(t){if(R.last!==null)R.raf.push(t-R.last);R.last=t;requestAnimationFrame(rf);}
 requestAnimationFrame(rf);
 return {special:_sonderLaeuft===true,phase:blinzelPhase};
})()
"""
        row["before_trigger"] = cdp.eval(start_js, timeout=5.0)
        if mode == "normal_blink":
            row["trigger"] = cdp.eval("(()=>{blinzeln(false);return {special:_sonderLaeuft,phase:blinzelPhase}})()", timeout=5.0)
        elif mode in ("special_raw", "special_predecoded"):
            row["trigger"] = cdp.eval(
                f"(()=>{{sonderausdruckZeigen({json.dumps(register)},{json.dumps(expression)},15000);"
                "return {special:_sonderLaeuft,phase:blinzelPhase};}})()",
                timeout=5.0,
            )
        else:
            row["trigger"] = {"none": True}

        time.sleep(4.0)
        try:
            payload = json.loads(cdp.eval(
                "JSON.stringify((()=>{const R=window.__goSchedulerAttrib||{};if(R.interval){clearInterval(R.interval);R.interval=null;}"
                "return {elapsed:performance.now()-(R.start||performance.now()),timerTicks:R.timerTicks||0,raf:R.raf||[],"
                "special:_sonderLaeuft===true,phase:blinzelPhase,blinkSrc:document.getElementById('augen-blink')?.src||null};})())",
                timeout=20.0,
            ))
            raf = [float(x) for x in payload.pop("raf", [])]
            payload["raf_summary"] = summarize_deltas(raf)
            row["final"] = payload
            row["final_read"] = True
        except Exception as exc:
            row["error"] = f"FINAL_READ_{type(exc).__name__}:{exc}"
        return row
    finally:
        if cdp:
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", type=Path, required=True)
    ap.add_argument("--shadow", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--http-port", type=int, default=9294)
    ap.add_argument("--cdp-port-base", type=int, default=9295)
    ap.add_argument("--expression-register", default="anime_90s")
    ap.add_argument("--expression", default="anime_fassungslos")
    args = ap.parse_args()

    visual = args.visual_root.resolve()
    live = visual / "buehne.html"
    shadow = args.shadow.resolve()
    open_plate = visual / "augen_blink_relief2" / "blink_000.png"
    got_live, got_shadow, got_open = map(sha256_file, (live, shadow, open_plate))
    if got_live != EXPECTED_LIVE_SHA256:
        raise SystemExit(f"LIVE_SUBJECT_DRIFT {got_live}")
    if got_shadow != EXPECTED_SHADOW_SHA256:
        raise SystemExit(f"SHADOW_SUBJECT_DRIFT {got_shadow}")
    if got_open != EXPECTED_OPEN_PLATE_SHA256:
        raise SystemExit(f"OPEN_PLATE_DRIFT {got_open}")

    args.out.mkdir(parents=True, exist_ok=False)
    html = shadow.read_text(encoding="utf-8")
    if html.count("<head>") != 1:
        raise SystemExit("SHADOW_HEAD_COUNT_INVALID")
    served = html.replace("<head>", '<head>\n<base href="http://127.0.0.1:8788/">', 1).encode()

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
    try:
        url = f"http://127.0.0.1:{args.http_port}/"
        modes = ("idle", "normal_blink", "special_raw", "special_predecoded")
        rows = [
            run_condition(url, args.cdp_port_base + i, mode, args.expression_register, args.expression)
            for i, mode in enumerate(modes)
        ]
        report = {
            "schema": "GO_AVATAR_EYE_SCHEDULER_ATTRIBUTION/v2",
            "scope": "EXACT_SHADOW_FRESH_CHROMIUM_IDLE_BLINK_SPECIAL_PREDECODE_NO_LIVE_WRITE",
            "live_sha256": got_live,
            "shadow_sha256": got_shadow,
            "open_plate_sha256": got_open,
            "rows": rows,
            "live_source_unchanged": sha256_file(live) == got_live,
        }
        (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True))
        if not report["live_source_unchanged"]:
            raise SystemExit("LIVE_SOURCE_MUTATED")
        if not all(r.get("final_read") is True for r in rows):
            raise SystemExit("SCHEDULER_ATTRIBUTION_INCOMPLETE")
        print("EYE_SCHEDULER_ATTRIBUTION=COMPLETE")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
