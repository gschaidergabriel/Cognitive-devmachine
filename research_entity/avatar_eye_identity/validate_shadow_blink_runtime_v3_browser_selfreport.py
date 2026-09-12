#!/usr/bin/env python3
"""CDP-free real-browser runtime discriminator for canonical-eye shadow.

V1/V2 exercised the right browser behavior but sampled DOM state through many
Chrome DevTools websocket round-trips while the blink was running.  Real-host
runs twice timed out in websocket.recv(), so transport scheduling could
masquerade as a product negative.

V3 moves the entire temporal discriminator into the served browser page.  The
browser samples its own blink/special-expression state and rAF cadence, then
POSTs one bounded JSON report back to the local harness.  There are zero CDP
round-trips during the discriminator and no live source writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import tempfile
import threading
import time

EXPECTED_LIVE_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
EXPECTED_OPEN_PLATE_SHA256 = "8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9"
EXPECTED_SHADOW_SHA256 = "4fb62046e650f993edb89be24c40262fb8e7202e2c7cda14df7aa0113cfbfb4d"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def instrument(post_url: str, expression_register: str, expression: str) -> str:
    # Deliberately self-contained: no external harness library and no websocket.
    return f"""
<script id="go-eye-browser-selfreport-v3">
(async()=>{{
  const POST={json.dumps(post_url)};
  const REG={json.dumps(expression_register)};
  const EXPR={json.dumps(expression)};
  const sleep=(ms)=>new Promise(r=>setTimeout(r,ms));
  const state=()=>({{
    special: window._sonderLaeuft,
    phase: window.blinzelPhase,
    blinkOpacity: getComputedStyle(document.getElementById('augen-blink')).opacity,
    blinkSrc: document.getElementById('augen-blink').src,
    glowOpacity: getComputedStyle(document.getElementById('pupillen-glow')).opacity
  }});
  async function post(obj){{
    try {{
      await fetch(POST, {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(obj)}});
    }} catch(e) {{ console.error('GO_POST_FAIL',e); }}
  }}
  try {{
    let ready=false;
    for(let i=0;i<180;i++){{
      ready=document.readyState==='complete' &&
        typeof window.sonderausdruckZeigen==='function' &&
        typeof window.blinzeln==='function' &&
        !!document.getElementById('augen-blink') &&
        !!document.getElementById('pupillen-glow');
      if(ready) break;
      await sleep(50);
    }}
    if(!ready) return post({{schema:'GO_AVATAR_EYE_SHADOW_RUNTIME/v3',error:'SHADOW_RUNTIME_NOT_READY'}});

    window.sonderausdruckZeigen(REG,EXPR,15000);
    for(let i=0;i<120 && window._sonderLaeuft!==true;i++) await sleep(25);
    if(window._sonderLaeuft!==true) return post({{schema:'GO_AVATAR_EYE_SHADOW_RUNTIME/v3',error:'SPECIAL_EXPRESSION_NOT_ACTIVE'}});

    const pre=state();
    const raf=[]; let last=null, rafDone=false;
    function rf(t){{
      if(last!==null) raf.push(t-last); last=t;
      if(raf.length>=240){{rafDone=true;return;}}
      requestAnimationFrame(rf);
    }}
    requestAnimationFrame(rf);

    const samples=[]; let seenActive=false, seenClosed=false;
    const t0=performance.now();
    window.blinzeln(false);
    while(performance.now()-t0<2800){{
      const row=state(); row.wall_ms=performance.now()-t0; samples.push(row);
      if(row.phase!==null && row.phase!==undefined) seenActive=true;
      if(row.phase==='zu') seenClosed=true;
      if(seenActive && (row.phase===null || row.phase===undefined) && performance.now()-t0>450) break;
      await sleep(8);
    }}
    const postState=state();
    for(let i=0;i<400 && !rafDone;i++) await sleep(10);

    const phases=[...new Set(samples.filter(x=>x.phase!==null&&x.phase!==undefined).map(x=>String(x.phase)))].sort();
    const frames=[...new Set(samples.map(x=>String(x.blinkSrc||'').split('/').pop()).filter(x=>x.startsWith('blink_'))) ].sort();
    const active=samples.filter(x=>x.phase!==null&&x.phase!==undefined);
    const opacityBad=active.filter(x=>String(x.blinkOpacity)!=='1').length;
    const glowBad=active.filter(x=>String(x.glowOpacity)!=='0').length;
    const specialBad=samples.filter(x=>x.special!==true).length;
    const rs=raf.map(Number).filter(Number.isFinite).sort((a,b)=>a-b);
    const mean=rs.length?rs.reduce((a,b)=>a+b,0)/rs.length:Infinity;
    const fps=1000/mean;
    const p95=rs.length?rs[Math.floor(.95*(rs.length-1))]:Infinity;
    const checks={{
      special_active_before: pre.special===true,
      special_active_after: postState.special===true,
      closed_phase_observed: phases.includes('zu'),
      opening_phase_observed: phases.includes('halb2'),
      closing_phase_observed: phases.includes('halb1'),
      enough_distinct_blink_frames: frames.length>=9,
      eye_layer_opaque_while_blinking: opacityBad===0,
      glow_hidden_while_lid_active: glowBad===0,
      special_never_dropped: specialBad===0,
      restored_frame_zero: String(postState.blinkSrc||'').endsWith('/augen_blink/blink_000.png'),
      restored_open_opacity: String(postState.blinkOpacity)==='1',
      blink_phase_cleared: postState.phase===null || postState.phase===undefined,
      closed_phase_observed_during_sampling: seenClosed,
      raf_samples_ge_120: rs.length>=120,
      raf_fps_ge_58: fps>=58,
      raf_p95_le_18ms: p95<=18
    }};
    return post({{
      schema:'GO_AVATAR_EYE_SHADOW_RUNTIME/v3',
      scope:'ISOLATED_REAL_BROWSER_SHADOW_BROWSER_SELFREPORT_NO_LIVE_SOURCE_WRITE',
      expression:{{register:REG,name:EXPR}}, pre, post:postState,
      sample_count:samples.length, active_sample_count:active.length,
      phases, frame_names:frames, opacity_bad_count:opacityBad,
      glow_bad_count:glowBad, special_bad_count:specialBad,
      raf:{{samples:rs.length,done:rafDone,fps,p95_ms:p95,max_ms:rs.length?rs[rs.length-1]:null}},
      checks
    }});
  }} catch(e) {{
    return post({{schema:'GO_AVATAR_EYE_SHADOW_RUNTIME/v3',error:String(e),stack:String(e&&e.stack||'')}});
  }}
}})();
</script>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", type=Path, required=True)
    ap.add_argument("--shadow", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--http-port", type=int, default=9274)
    ap.add_argument("--expression-register", default="anime_90s")
    ap.add_argument("--expression", default="anime_fassungslos")
    ap.add_argument("--timeout", type=float, default=20.0)
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

    report_box: dict[str, object] = {}
    report_event = threading.Event()
    post_url = f"http://127.0.0.1:{args.http_port}/report"
    html = shadow.read_text(encoding="utf-8")
    if html.count("<head>") != 1:
        raise SystemExit("FAIL shadow head count")
    html = html.replace("<head>", '<head>\n<base href="http://127.0.0.1:8788/">', 1)
    probe = instrument(post_url, args.expression_register, args.expression)
    marker = "</body>" if "</body>" in html else "</html>"
    if marker not in html:
        raise SystemExit("FAIL no injection anchor")
    served = html.replace(marker, probe + "\n" + marker, 1).encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            p = self.path.split("?", 1)[0]
            if p in ("/", "/buehne.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(served)))
                self.end_headers(); self.wfile.write(served); return
            self.send_response(404); self.end_headers()

        def do_POST(self) -> None:  # noqa: N802
            if self.path.split("?", 1)[0] != "/report":
                self.send_response(404); self.end_headers(); return
            n = int(self.headers.get("Content-Length", "0"))
            try:
                obj = json.loads(self.rfile.read(n))
                report_box["report"] = obj
                report_event.set()
                self.send_response(204); self.end_headers()
            except Exception as exc:
                report_box["decode_error"] = repr(exc)
                report_event.set()
                self.send_response(400); self.end_headers()

        def log_message(self, fmt: str, *items: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", args.http_port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    tmp = Path(tempfile.mkdtemp(prefix="f2-eye-shadow-runtime-v3-"))
    stdout_f = (tmp / "chrome.stdout").open("wb")
    stderr_f = (tmp / "chrome.stderr").open("wb")
    proc = subprocess.Popen([
        "google-chrome", "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
        "--disable-web-security", f"--user-data-dir={tmp / 'profile'}", "--window-size=1536,1024",
        f"http://127.0.0.1:{args.http_port}/",
    ], stdout=stdout_f, stderr=stderr_f)
    try:
        if not report_event.wait(args.timeout):
            raise SystemExit("BROWSER_SELFREPORT_TIMEOUT")
        if "decode_error" in report_box:
            raise SystemExit(f"BROWSER_REPORT_DECODE_FAIL {report_box['decode_error']}")
        report = report_box.get("report")
        if not isinstance(report, dict):
            raise SystemExit("BROWSER_REPORT_MISSING")
        report["live_sha256"] = got_live
        report["shadow_sha256"] = got_shadow
        report["open_plate_sha256"] = got_open
        report["live_source_unchanged"] = sha256_file(live) == got_live
        report["source_mutation"] = False
        checks = report.get("checks")
        if isinstance(checks, dict):
            checks["live_source_unchanged"] = report["live_source_unchanged"]
        (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
        if report.get("error"):
            raise SystemExit(f"BROWSER_SELFREPORT_ERROR {report['error']}")
        if not isinstance(checks, dict) or not all(checks.values()):
            raise SystemExit("SHADOW_RUNTIME_GATE_V3_FAIL")
        print("EYE_SHADOW_RUNTIME_GATE_V3=PASS")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait(timeout=5)
        stdout_f.close(); stderr_f.close(); server.shutdown(); server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
