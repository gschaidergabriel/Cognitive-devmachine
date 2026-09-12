#!/usr/bin/env python3
"""Visible non-headless scratch A/B for the shoulder residual compositor.

Never mutates the production files or production browser.  It serves the exact
live buehne.html from a temporary HTTP server, launches an isolated visible
Chrome window on the left/non-production X11 monitor, captures BASE and
CANDIDATE screenshots, and verifies the production browser identity survived.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import statistics
import subprocess
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

EXPECTED_LIVE_SHA = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
TITLE = "FRANK_SHOULDER_AB_SCRATCH"

MEASURE = r'''<script>
(()=>{
 document.title='FRANK_SHOULDER_AB_SCRATCH';
 let n=0;
 setInterval(()=>{
   n++;
   fetch('/api/test_fps',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
     n, fps:window.__buehneFps||0, t:performance.now(),
     phase:window.__bodyVisiblePhase||'base',
     ready:window.__bodyVisibleReady||0,
     draws:window.__bodyVisibleDraws||0
   })}).catch(()=>{});
 },500);
})();
</script>'''

VISIBLE = r'''<script>
(()=>{
window.__bodyVisiblePhase='base';
window.__bodyVisibleReady=0;
window.__bodyVisibleDraws=0;
window.__bodyVisibleMeta={};
function _shader(gl,type,src){let s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
async function initBodyVisible(){
 const t0=performance.now();
 const bodyWrap=document.getElementById('koerper-dreh');
 const aEl=document.getElementById('koerper-schicht'), bEl=document.getElementById('koerper-schicht2');
 if(!bodyWrap||!aEl||!bEl) throw Error('body DOM anchors missing');
 const paths=[...new Set([...(typeof ATMEN_BILDER!=='undefined'?ATMEN_BILDER:[]),...(typeof KOERPER_AKTIONEN!=='undefined'?KOERPER_AKTIONEN.flatMap(x=>x.bilder):[])])];
 const W=620,H=414,SW=1536,SH=1024;
 const cv=document.createElement('canvas'); cv.width=W; cv.height=H; cv.id='body-residual-visible-scratch';
 cv.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none;opacity:0;z-index:3';
 bodyWrap.appendChild(cv);
 const gl=cv.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:false,premultipliedAlpha:false});
 if(!gl) throw Error('no webgl');
 const dbg=gl.getExtension('WEBGL_debug_renderer_info');
 const VS=`precision highp float;const float SW=1536.0,SH=1024.0;attribute vec2 p;uniform float shoulderScale,t;varying vec2 uv;float G(vec2 q,vec2 c,vec2 z){vec2 d=(q-c)/z;return exp(-.5*dot(d,d));}void main(){vec2 q=p;float bw=1306.,bh=519.,x0=117.,y0=505.;float br=sin(6.2831853*t/4.9),l=sin(6.2831853*t/8.7+.83),r=sin(6.2831853*t/11.3+2.14);float ld=shoulderScale*(-.46*br+.12*l),rd=shoulderScale*(-.42*br+.09*r),lr=radians(shoulderScale*(.085*l+.025*br)),rr=radians(shoulderScale*(-.070*r-.018*br));float lx=x0+.27*bw,rx=x0+.73*bw,sy=y0+.19*bh;float wl=G(q,vec2(lx,sy),vec2(.18*bw,.115*bh)),wr=G(q,vec2(rx,sy),vec2(.18*bw,.115*bh));float c0=y0+.38*bh,c1=y0+.62*bh,lo=q.y<=c0?1.:(q.y>=c1?0.:.5+.5*cos(3.14159265*(q.y-c0)/(c1-c0)));wl*=lo;wr*=lo;float dx=wl*(-lr*(q.y-sy))+wr*(-rr*(q.y-sy)),dy=wl*(ld+lr*(q.x-lx))+wr*(rd+rr*(q.x-rx));vec2 d=max(max(vec2(561.,505.)-q,q-vec2(977.,618.)),vec2(0.));float mv=clamp(length(d)/36.,0.,1.);q+=vec2(dx,dy)*mv;gl_Position=vec4(q.x/SW*2.-1.,1.-q.y/SH*2.,0,1);uv=p/vec2(SW,SH);}`;
 const FS=`precision mediump float;varying vec2 uv;uniform sampler2D a,b;uniform float oa,ob;void main(){vec4 A=texture2D(a,uv),B=texture2D(b,uv);A.a*=oa;B.a*=ob;vec4 Ap=vec4(A.rgb*A.a,A.a),Bp=vec4(B.rgb*B.a,B.a);vec4 P=Bp+Ap*(1.-Bp.a);gl_FragColor=P.a>0.?vec4(P.rgb/P.a,P.a):vec4(0.);}`;
 let pr=gl.createProgram(),vs=_shader(gl,gl.VERTEX_SHADER,VS),fs=_shader(gl,gl.FRAGMENT_SHADER,FS); gl.attachShader(pr,vs);gl.attachShader(pr,fs);gl.linkProgram(pr);if(!gl.getProgramParameter(pr,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(pr));gl.useProgram(pr);
 function coords(M,st,e){let z=[];for(let x=0;x<=M;x+=st)z.push(Math.min(M,x));z.push(M,...e);return [...new Set(z)].sort((x,y)=>x-y)}
 let xs=coords(SW,96,[117,561,978,1423]),ys=coords(SH,64,[505,619]),verts=[],ix=[];for(let y of ys)for(let x of xs)verts.push(x,y);let nx=xs.length;for(let y=0;y<ys.length-1;y++)for(let x=0;x<xs.length-1;x++){let A=y*nx+x,B=A+1,C=A+nx,D=C+1;ix.push(A,C,B,B,C,D)}
 let vb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(verts),gl.STATIC_DRAW);let al=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(al);gl.vertexAttribPointer(al,2,gl.FLOAT,false,0,0);let ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(ix),gl.STATIC_DRAW);
 let us=gl.getUniformLocation(pr,'shoulderScale'),ut=gl.getUniformLocation(pr,'t'),uoa=gl.getUniformLocation(pr,'oa'),uob=gl.getUniformLocation(pr,'ob');gl.uniform1i(gl.getUniformLocation(pr,'a'),0);gl.uniform1i(gl.getUniformLocation(pr,'b'),1);gl.viewport(0,0,W,H);
 const resize=document.createElement('canvas');resize.width=W;resize.height=H;const rc=resize.getContext('2d',{alpha:true}),textures=new Map();
 async function image(p){let im=new Image();im.src=p;await im.decode();return im}
 for(const p of paths){let im=await image(p);rc.clearRect(0,0,W,H);rc.drawImage(im,0,0,W,H);let x=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,x);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,resize);textures.set(new URL(p,location.href).pathname,x)}
 let last=[null,null];function bind(unit,p){if(!textures.has(p))return false;if(last[unit]===p)return true;gl.activeTexture(gl.TEXTURE0+unit);gl.bindTexture(gl.TEXTURE_2D,textures.get(p));last[unit]=p;return true}
 window.__bodyVisibleStep=function(ms){let p1=new URL(aEl.src,location.href).pathname,p2=new URL(bEl.src,location.href).pathname;if(!bind(0,p1)||!bind(1,p2))return;gl.uniform1f(us,4.0);gl.uniform1f(ut,ms/1000);gl.uniform1f(uoa,parseFloat(getComputedStyle(aEl).opacity)||0);gl.uniform1f(uob,parseFloat(getComputedStyle(bEl).opacity)||0);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawElements(gl.TRIANGLES,ix.length,gl.UNSIGNED_SHORT,0);gl.flush();window.__bodyVisibleDraws++};
 window.__bodyVisibleEnable=function(){cv.style.opacity='1';aEl.style.visibility='hidden';bEl.style.visibility='hidden';window.__bodyVisiblePhase='candidate'};
 window.__bodyVisibleDisable=function(){cv.style.opacity='0';aEl.style.visibility='visible';bEl.style.visibility='visible';window.__bodyVisiblePhase='base'};
 window.__bodyVisibleReady=performance.now();
 window.__bodyVisibleMeta={renderer:dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),version:gl.getParameter(gl.VERSION),textures:textures.size,vertices:verts.length/2,triangles:ix.length/3,prewarm_ms:performance.now()-t0,gl_error:gl.getError()};
 fetch('/api/meta',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(window.__bodyVisibleMeta)}).catch(()=>{});
 setTimeout(()=>window.__bodyVisibleEnable(),7000);
}
setTimeout(()=>initBodyVisible().catch(e=>fetch('/api/meta',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({error:String(e),stack:e.stack})}).catch(()=>{})),500);
})();
</script>'''


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def shell_lines(cmd: list[str]) -> list[str]:
    try:
        return [x.strip() for x in subprocess.check_output(cmd, text=True).splitlines() if x.strip()]
    except subprocess.CalledProcessError:
        return []


def production_subject() -> dict:
    pids = shell_lines(["pgrep", "-f", "/opt/google/chrome/chrome --app=http://127.0.0.1:8788/"])
    wins = shell_lines(["xdotool", "search", "--onlyvisible", "--name", "FranKenstein -- live"])
    return {"pids": pids, "windows": wins}


def x11_geometry(wid: str) -> dict:
    out = subprocess.check_output(["xdotool", "getwindowgeometry", "--shell", wid], text=True)
    d = {}
    for line in out.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            if k in {"X", "Y", "WIDTH", "HEIGHT", "SCREEN"}:
                d[k.lower()] = int(v)
    return d


def screenshot(wid: str, path: pathlib.Path) -> dict:
    subprocess.run(["import", "-window", wid, str(path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    b = path.read_bytes()
    identify = subprocess.check_output(["identify", "-format", "%w %h", str(path)], text=True).strip().split()
    return {"path": str(path), "sha256": sha_bytes(b), "bytes": len(b), "width": int(identify[0]), "height": int(identify[1])}


def summarize(samples: list[dict], phase: str) -> dict:
    xs = [x for x in samples if x.get("phase") == phase and float(x.get("fps", 0)) > 0]
    if phase == "candidate":
        xs = [x for x in xs if int(x.get("draws", 0)) > 30]
    if len(xs) > 4:
        xs = xs[2:]
    fps = [float(x["fps"]) for x in xs]
    return {
        "samples": len(fps),
        "fps_mean": statistics.mean(fps) if fps else None,
        "fps_median": statistics.median(fps) if fps else None,
        "fps_min": min(fps) if fps else None,
        "fps_max": max(fps) if fps else None,
        "last_draws": max((int(x.get("draws", 0)) for x in xs), default=0),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", default="/home/ai-core-node/.claude/star/visual")
    ap.add_argument("--chrome", default="/usr/bin/google-chrome")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    root = pathlib.Path(args.visual_root).resolve()
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    live_path = root / "buehne.html"
    live = live_path.read_bytes()
    live_sha_before = sha_bytes(live)
    if live_sha_before != EXPECTED_LIVE_SHA:
        raise SystemExit(f"LIVE_SHA_DRIFT {live_sha_before} != {EXPECTED_LIVE_SHA}")
    prod_before = production_subject()
    if not prod_before["pids"] or not prod_before["windows"]:
        raise SystemExit(f"PRODUCTION_SUBJECT_NOT_BOUND {prod_before}")

    html = live.decode("utf-8", errors="replace")
    marker = "  koerperSchritt(t);\n"
    if html.count(marker) != 1:
        raise SystemExit(f"KOERPER_MARKER_COUNT={html.count(marker)}")
    html = html.replace(marker, marker + "  if(window.__bodyVisibleStep) window.__bodyVisibleStep(t);\n", 1)
    payload = VISIBLE + MEASURE
    html = html.replace("</body>", payload + "</body>", 1) if "</body>" in html else html + payload
    page = html.encode()

    class State:
        samples: list[dict] = []
        meta: dict | None = None

    class H(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _json(self, obj, status=200):
            b = json.dumps(obj).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            u = urlparse(self.path).path
            if u in ("/", "/index.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(page)))
                self.end_headers()
                self.wfile.write(page)
                return
            if u == "/api/status":
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8000/api/status", timeout=2) as r:
                        b = r.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(b)))
                    self.end_headers()
                    self.wfile.write(b)
                except Exception:
                    self._json({"buehne": {"broadcast_value": 1.0, "ueberraschung": 0.0}, "zuschauer": 0})
                return
            rel = pathlib.PurePosixPath(unquote(u.lstrip("/")))
            if ".." in rel.parts:
                self.send_response(403); self.end_headers(); return
            p = (root / pathlib.Path(*rel.parts)).resolve()
            if root not in p.parents and p != root:
                self.send_response(403); self.end_headers(); return
            if not p.is_file():
                self.send_response(404); self.end_headers(); return
            b = p.read_bytes()
            ctype = "application/javascript" if p.suffix == ".js" else ("image/png" if p.suffix == ".png" else ("image/jpeg" if p.suffix.lower() in (".jpg", ".jpeg") else "application/octet-stream"))
            self.send_response(200); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

        def do_POST(self):
            u = urlparse(self.path).path
            n = int(self.headers.get("Content-Length", "0"))
            b = self.rfile.read(n)
            if u == "/api/test_fps":
                try: State.samples.append(json.loads(b))
                except Exception: pass
                self.send_response(204); self.end_headers(); return
            if u == "/api/meta":
                try: State.meta = json.loads(b)
                except Exception: State.meta = {"decode_error": True}
                self.send_response(204); self.end_headers(); return
            if u == "/api/fps":
                self.send_response(204); self.end_headers(); return
            self.send_response(204); self.end_headers()

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    profile = tempfile.mkdtemp(prefix="frank-visible-shoulder-")
    env = os.environ.copy(); env["DISPLAY"] = env.get("DISPLAY") or ":0"
    cmd = [args.chrome, f"--app={url}", "--window-position=100,100", "--window-size=746,449", f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--disable-sync", "--disable-background-networking", "--disable-features=Translate,TranslateUI"]
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    result = {"schema": "BODY_VISIBLE_SCRATCH_AB/v1", "url": url, "live_html_sha256_before": live_sha_before, "production_before": prod_before, "command": cmd}
    try:
        wid = ""
        deadline = time.time() + 8
        while time.time() < deadline and not wid:
            hits = shell_lines(["xdotool", "search", "--onlyvisible", "--name", TITLE])
            if hits: wid = hits[-1]
            else: time.sleep(.25)
        if not wid:
            raise RuntimeError("scratch X11 window not found")
        geom = x11_geometry(wid)
        result["scratch_window"] = {"id": wid, "geometry": geom}
        if geom.get("x", 99999) >= 1680 or geom.get("x", 0) + geom.get("width", 0) > 1680:
            raise RuntimeError(f"scratch window escaped non-production monitor: {geom}")
        time.sleep(4.5)
        result["base_screenshot"] = screenshot(wid, out / "base.png")
        time.sleep(5.0)
        result["candidate_screenshot"] = screenshot(wid, out / "candidate.png")
        time.sleep(2.0)
    finally:
        try: proc.terminate(); proc.communicate(timeout=5)
        except Exception:
            try: proc.kill(); proc.communicate(timeout=3)
            except Exception: pass
        srv.shutdown()
        shutil.rmtree(profile, ignore_errors=True)

    result["meta"] = State.meta
    result["base"] = summarize(State.samples, "base")
    result["candidate"] = summarize(State.samples, "candidate")
    result["sample_count"] = len(State.samples)
    result["live_html_sha256_after"] = sha_bytes(live_path.read_bytes())
    result["production_after"] = production_subject()

    checks = {
        "live_hash_unchanged": result["live_html_sha256_after"] == EXPECTED_LIVE_SHA == live_sha_before,
        "production_pids_unchanged": result["production_after"]["pids"] == prod_before["pids"],
        "production_windows_unchanged": result["production_after"]["windows"] == prod_before["windows"],
        "scratch_on_left_monitor": result["scratch_window"]["geometry"].get("x", 99999) < 1680 and result["scratch_window"]["geometry"].get("x", 0) + result["scratch_window"]["geometry"].get("width", 0) <= 1680,
        "screens_same_dimensions": result["base_screenshot"]["width"] == result["candidate_screenshot"]["width"] and result["base_screenshot"]["height"] == result["candidate_screenshot"]["height"],
        "screens_nonempty": result["base_screenshot"]["bytes"] > 10000 and result["candidate_screenshot"]["bytes"] > 10000,
        "meta_ok": isinstance(State.meta, dict) and not State.meta.get("error") and State.meta.get("gl_error") == 0,
        "amd_renderer": isinstance(State.meta, dict) and ("AMD" in str(State.meta.get("renderer", "")) or "Radeon" in str(State.meta.get("renderer", ""))),
        "textures": isinstance(State.meta, dict) and int(State.meta.get("textures", 0)) >= 12,
        "draws": int(result["candidate"].get("last_draws") or 0) > 100,
        "base_fps": result["base"]["fps_mean"] is not None and result["base"]["fps_mean"] >= 58 and result["base"]["fps_min"] >= 55,
        "candidate_fps": result["candidate"]["fps_mean"] is not None and result["candidate"]["fps_mean"] >= 58 and result["candidate"]["fps_min"] >= 55,
    }
    result["checks"] = checks
    result["pass"] = all(checks.values())
    (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
