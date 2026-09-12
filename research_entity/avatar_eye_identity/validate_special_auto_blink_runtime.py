#!/usr/bin/env python3
"""Exact-subject runtime gate for the real special-expression auto-blink path.

Earlier validators activated a special expression, observed that it was already
in blink phase, and then called blinzeln(false) again. That can overlap two blink
players and is not the user-facing path. This gate arms all measurement first
and invokes sonderausdruckZeigen exactly once. It then observes the blink that
the product starts naturally, without any second blink trigger.
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", type=Path, required=True)
    ap.add_argument("--shadow", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--http-port", type=int, default=9292)
    ap.add_argument("--cdp-port", type=int, default=9293)
    ap.add_argument("--expression-register", default="anime_90s")
    ap.add_argument("--expression", default="anime_fassungslos")
    args = ap.parse_args()

    visual = args.visual_root.resolve()
    live = visual / "buehne.html"
    open_plate = visual / "augen_blink_relief2" / "blink_000.png"
    shadow = args.shadow.resolve()
    out = args.out.resolve()
    got_live, got_open, got_shadow = map(sha256_file, (live, open_plate, shadow))
    if got_live != EXPECTED_LIVE_SHA256: raise SystemExit(f"LIVE_SUBJECT_DRIFT {got_live}")
    if got_open != EXPECTED_OPEN_PLATE_SHA256: raise SystemExit(f"OPEN_PLATE_DRIFT {got_open}")
    if got_shadow != EXPECTED_SHADOW_SHA256: raise SystemExit(f"SHADOW_SUBJECT_DRIFT {got_shadow}")
    out.mkdir(parents=True, exist_ok=False)

    html = shadow.read_text(encoding="utf-8")
    if html.count("<head>") != 1: raise SystemExit("SHADOW_HEAD_COUNT_INVALID")
    served = html.replace("<head>", '<head>\n<base href="http://127.0.0.1:8788/">', 1).encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path.split("?",1)[0] in ("/","/buehne.html"):
                self.send_response(200)
                self.send_header("Content-Type","text/html; charset=utf-8")
                self.send_header("Cache-Control","no-store")
                self.send_header("Content-Length",str(len(served)))
                self.end_headers(); self.wfile.write(served)
            else:
                self.send_response(404); self.end_headers()
        def log_message(self, fmt: str, *items: object) -> None: return

    server = ThreadingHTTPServer(("127.0.0.1",args.http_port),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    tmp = Path(tempfile.mkdtemp(prefix="eye-special-auto-blink-"))
    stdout_f = (tmp/"chrome.stdout").open("wb"); stderr_f = (tmp/"chrome.stderr").open("wb")
    proc = subprocess.Popen([
        "google-chrome","--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-web-security",
        "--disable-background-timer-throttling","--disable-renderer-backgrounding","--disable-backgrounding-occluded-windows",
        f"--remote-debugging-port={args.cdp_port}","--remote-allow-origins=*",
        f"--user-data-dir={tmp/'profile'}","--window-size=1536,1024",
        f"http://127.0.0.1:{args.http_port}/",
    ],stdout=stdout_f,stderr=stderr_f)
    cdp: CDP|None=None
    try:
        target=None
        for _ in range(150):
            try:
                tabs=requests.get(f"http://127.0.0.1:{args.cdp_port}/json/list",timeout=0.5).json()
                target=next((t for t in tabs if t.get("type")=="page" and f"127.0.0.1:{args.http_port}" in t.get("url","")),None)
                if target: break
            except Exception: pass
            time.sleep(0.1)
        if not target: raise SystemExit("TARGET_PAGE_NOT_FOUND")
        cdp=CDP(target["webSocketDebuggerUrl"],timeout=20.0)
        cdp.call("Page.enable",timeout=20.0); cdp.call("Runtime.enable",timeout=20.0)
        ready=False
        for _ in range(120):
            try:
                ready=bool(cdp.eval("document.readyState==='complete' && typeof sonderausdruckZeigen==='function' && !!document.getElementById('augen-blink')",timeout=2.0))
            except Exception: ready=False
            if ready: break
            time.sleep(0.1)
        if not ready: raise SystemExit("RUNTIME_NOT_READY")
        cdp.screenshot(out/"01_before_special.png")

        js=f"""
(()=>{{
 const blink=document.getElementById('augen-blink');
 const glow=document.getElementById('pupillen-glow');
 const R=window.__goAutoBlink={{start:performance.now(),samples:[],raf:[],rafDone:false}};
 let last=null;
 function rf(t){{if(last!==null)R.raf.push(t-last);last=t;if(R.raf.length>=240){{R.rafDone=true;return;}}requestAnimationFrame(rf);}}
 function smp(){{const n=performance.now();R.samples.push({{ms:n-R.start,special:_sonderLaeuft,phase:blinzelPhase,blinkOpacity:getComputedStyle(blink).opacity,blinkSrc:blink.src,glowOpacity:getComputedStyle(glow).opacity}});}}
 sonderausdruckZeigen({json.dumps(args.expression_register)},{json.dumps(args.expression)},15000);
 R.specialImmediately=_sonderLaeuft===true;
 smp(); R.interval=setInterval(smp,8); requestAnimationFrame(rf);
 return {{special:R.specialImmediately,phase:blinzelPhase,src:blink.src}};
}})()
"""
        start=cdp.eval(js,timeout=10.0)
        time.sleep(5.0)
        payload_text=cdp.eval(
            "JSON.stringify((()=>{const R=window.__goAutoBlink||{};if(R.interval){clearInterval(R.interval);R.interval=null;}"
            "const b=document.getElementById('augen-blink'),g=document.getElementById('pupillen-glow');return {"
            "specialImmediately:R.specialImmediately===true,samples:R.samples||[],raf:R.raf||[],rafDone:R.rafDone===true,"
            "post:{special:_sonderLaeuft,phase:blinzelPhase,blinkOpacity:getComputedStyle(b).opacity,blinkSrc:b.src,glowOpacity:getComputedStyle(g).opacity}}})())",
            timeout=20.0)
        payload=json.loads(payload_text)
        cdp.screenshot(out/"02_after_auto_blink.png")

        samples=payload.get("samples") if isinstance(payload.get("samples"),list) else []
        raf=payload.get("raf") if isinstance(payload.get("raf"),list) else []
        post=payload.get("post") if isinstance(payload.get("post"),dict) else {}
        phases=sorted({str(r.get("phase")) for r in samples if r.get("phase") is not None})
        frames=sorted({str(r.get("blinkSrc","")).rsplit("/",1)[-1] for r in samples if "blink_" in str(r.get("blinkSrc",""))})
        active=[r for r in samples if r.get("phase") is not None]
        opacity_bad=[r for r in active if str(r.get("blinkOpacity"))!="1"]
        glow_bad=[r for r in active if str(r.get("glowOpacity"))!="0"]
        special_bad=[r for r in samples if r.get("special") is not True]
        rv=[float(x) for x in raf]; rs=sorted(rv)
        fps=(1000.0/(sum(rv)/len(rv))) if rv and sum(rv)>0 else 0.0
        p95=rs[int(0.95*(len(rs)-1))] if rs else float("inf")
        checks={
            "special_started_synchronously":payload.get("specialImmediately") is True,
            "sample_count_ge_80":len(samples)>=80,
            "closing_phase_observed":"halb1" in phases,
            "closed_phase_observed":"zu" in phases,
            "opening_phase_observed":"halb2" in phases,
            "enough_distinct_blink_frames":len(frames)>=9,
            "canonical_eye_opaque_during_blink":not opacity_bad,
            "glow_hidden_during_lid_activity":not glow_bad,
            "special_never_dropped":not special_bad,
            "special_active_after":post.get("special") is True,
            "blink_phase_cleared":post.get("phase") is None,
            "restored_frame_zero":str(post.get("blinkSrc","")).endswith("/augen_blink/blink_000.png"),
            "restored_open_opacity":post.get("blinkOpacity")=="1",
            "raf_samples_ge_120":len(rv)>=120,
            "raf_fps_ge_58":fps>=58.0,
            "raf_p95_le_18ms":p95<=18.0,
            "live_source_unchanged":sha256_file(live)==got_live,
        }
        report={
            "schema":"GO_AVATAR_EYE_SPECIAL_AUTO_BLINK_RUNTIME/v1",
            "scope":"EXACT_SHADOW_REAL_SPECIAL_EXPRESSION_AUTOBLINK_NO_MANUAL_SECOND_BLINK_NO_LIVE_WRITE",
            "live_sha256":got_live,"shadow_sha256":got_shadow,"open_plate_sha256":got_open,
            "start":start,"sample_count":len(samples),"active_sample_count":len(active),
            "phases":phases,"frame_names":frames,"opacity_bad_count":len(opacity_bad),
            "glow_bad_count":len(glow_bad),"special_bad_count":len(special_bad),"post":post,
            "raf":{"samples":len(rv),"done":payload.get("rafDone") is True,"fps":fps,"p95_ms":p95,"max_ms":max(rv) if rv else None},
            "checks":checks,"source_mutation":False,
        }
        (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,sort_keys=True))
        if not all(checks.values()): raise SystemExit("SPECIAL_AUTO_BLINK_GATE_FAIL")
        print("SPECIAL_AUTO_BLINK_GATE=PASS")
        return 0
    finally:
        if cdp:
            try: cdp.close()
            except Exception: pass
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill()
        stdout_f.close(); stderr_f.close(); server.shutdown(); server.server_close()


if __name__=="__main__": raise SystemExit(main())
