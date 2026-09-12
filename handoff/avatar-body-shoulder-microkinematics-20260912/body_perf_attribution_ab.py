#!/usr/bin/env python3
"""Read-only causal performance attribution for the existing body player + residual mesh.

This is a reviewer/falsifier gate, not a new body implementation.  It keeps the
same current assets, WebGL mesh and shader shape as body_player_composition_ab.py,
but separates two independent costs:

  static_base  = fixed already-bound textures, residual mesh disabled
  static_warp  = fixed already-bound textures, residual shoulder mesh enabled
  player_base  = real image-family/image changes + texture uploads, mesh disabled
  player_warp  = the same player changes + texture uploads, mesh enabled

The conditions run in a symmetric order so thermal/background drift is less able
to masquerade as a mesh effect.  No live avatar file is modified.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

SEQS = {
    "atmen": [f"atmen__atmen_{i:03d}.png" for i in range(12)],
    "schulterzucken": [f"schulterzucken/zucken_{i:03d}.png" for i in range(8)],
    "aufrichten": [f"aufrichten/aufrichten_{i:03d}.png" for i in range(8)],
    "lehnen": [f"lehnen/lehnen_{x}.png" for x in ["+00", "+05", "+10", "+15", "+20", "+15", "+10", "+05", "+00"]],
    "gewicht": [f"gewicht/gewicht_{x}.png" for x in ["+00", "+05", "+10", "+15", "+10", "+05", "+00", "-05", "-10", "-05", "+00"]],
    "schulterdrehung": [f"schulterdrehung/schulter_{x}.png" for x in ["+00", "+05", "+10", "+15", "+10", "+05", "+00", "-05", "-10", "-05", "+00"]],
}

PAGE = r'''<!doctype html><meta charset=utf-8><canvas id=c width=620 height=414></canvas><pre id=o>running</pre><script>
const SEQS=__SEQS__, cv=document.getElementById('c'), out=document.getElementById('o');
function load(u){return new Promise((r,j)=>{let i=new Image;i.onload=()=>r(i);i.onerror=()=>j(Error(u));i.src='/asset/'+u})}
function sh(gl,t,s){let x=gl.createShader(t);gl.shaderSource(x,s);gl.compileShader(x);if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(x));return x}
function pct(a,p){let x=[...a].sort((u,v)=>u-v);return x[Math.min(x.length-1,Math.floor((x.length-1)*p))]}
function stats(a){let m=a.reduce((x,y)=>x+y,0)/a.length;return {n:a.length,mean_ms:m,p50_ms:pct(a,.5),p95_ms:pct(a,.95),p99_ms:pct(a,.99),max_ms:Math.max(...a),over20:a.filter(x=>x>20).length,over25:a.filter(x=>x>25).length,over33:a.filter(x=>x>33).length,fps:1000/m}}
function env(name){if(name==='schulterzucken'||name==='schulterdrehung')return [0,0];if(name==='aufrichten'||name==='lehnen'||name==='gewicht')return [.15,0];return [.35,0]}
(async()=>{
 const all={};for(const [k,arr] of Object.entries(SEQS))all[k]=await Promise.all(arr.map(load));
 const gl=cv.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:false,premultipliedAlpha:false});if(!gl)throw Error('no webgl');
 const dbg=gl.getExtension('WEBGL_debug_renderer_info'),renderer=dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
 const VS=`precision highp float;const float SW=1536.0,SH=1024.0;attribute vec2 p;uniform vec2 shoulderScale;uniform float chestScale,t;varying vec2 uv;float G(vec2 q,vec2 c,vec2 z){vec2 d=(q-c)/z;return exp(-.5*dot(d,d));}void main(){vec2 q=p;float bw=1306.,bh=519.,x0=117.,y0=505.;float b=sin(6.2831853*t/4.9),l=sin(6.2831853*t/8.7+.83),r=sin(6.2831853*t/11.3+2.14);float ld=shoulderScale.x*(-.46*b+.12*l),rd=shoulderScale.y*(-.42*b+.09*r),lr=radians(shoulderScale.x*(.085*l+.025*b)),rr=radians(shoulderScale.y*(-.070*r-.018*b)),cd=chestScale*(-.18*b);float lx=x0+.27*bw,rx=x0+.73*bw,sy=y0+.19*bh;float wl=G(q,vec2(lx,sy),vec2(.18*bw,.115*bh)),wr=G(q,vec2(rx,sy),vec2(.18*bw,.115*bh)),wc=G(q,vec2(x0+.5*bw,y0+.31*bh),vec2(.25*bw,.13*bh));float c0=y0+.38*bh,c1=y0+.62*bh,lo=q.y<=c0?1.:(q.y>=c1?0.:.5+.5*cos(3.14159265*(q.y-c0)/(c1-c0)));wl*=lo;wr*=lo;wc*=lo;float dx=wl*(-lr*(q.y-sy))+wr*(-rr*(q.y-sy)),dy=wl*(ld+lr*(q.x-lx))+wr*(rd+rr*(q.x-rx))+wc*cd;vec2 d=max(max(vec2(561.,505.)-q,q-vec2(977.,618.)),vec2(0.));float mv=clamp(length(d)/36.,0.,1.);q+=vec2(dx,dy)*mv;gl_Position=vec4(q.x/SW*2.-1.,1.-q.y/SH*2.,0,1);uv=p/vec2(SW,SH);}`;
 const FS=`precision mediump float;varying vec2 uv;uniform sampler2D a,b;uniform float mixv;void main(){vec4 A=texture2D(a,uv),B=texture2D(b,uv);vec4 Ap=vec4(A.rgb*A.a,A.a),Bp=vec4(B.rgb*B.a,B.a);vec4 P=mix(Ap,Bp,mixv);gl_FragColor=P.a>0.?vec4(P.rgb/P.a,P.a):vec4(0.);}`;
 let pr=gl.createProgram();gl.attachShader(pr,sh(gl,gl.VERTEX_SHADER,VS));gl.attachShader(pr,sh(gl,gl.FRAGMENT_SHADER,FS));gl.linkProgram(pr);if(!gl.getProgramParameter(pr,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(pr));gl.useProgram(pr);
 function coords(M,st,e){let a=[];for(let x=0;x<=M;x+=st)a.push(Math.min(M,x));a.push(M,...e);return [...new Set(a)].sort((a,b)=>a-b)}
 let xs=coords(1536,96,[117,561,978,1423]),ys=coords(1024,64,[505,619]),v=[],ix=[];for(let y of ys)for(let x of xs)v.push(x,y);let nx=xs.length;for(let y=0;y<ys.length-1;y++)for(let x=0;x<xs.length-1;x++){let A=y*nx+x,B=A+1,C=A+nx,D=C+1;ix.push(A,C,B,B,C,D)}
 let vb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(v),gl.STATIC_DRAW);let al=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(al);gl.vertexAttribPointer(al,2,gl.FLOAT,false,0,0);let ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(ix),gl.STATIC_DRAW);
 const U={ss:gl.getUniformLocation(pr,'shoulderScale'),cs:gl.getUniformLocation(pr,'chestScale'),t:gl.getUniformLocation(pr,'t'),m:gl.getUniformLocation(pr,'mixv')};let tex=[gl.createTexture(),gl.createTexture()],bound=[null,null],uploads=0;tex.forEach((x,i)=>{gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,x);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE)});gl.uniform1i(gl.getUniformLocation(pr,'a'),0);gl.uniform1i(gl.getUniformLocation(pr,'b'),1);gl.viewport(0,0,620,414);gl.disable(gl.BLEND);
 function put(i,im){if(bound[i]===im)return;gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,tex[i]);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im);bound[i]=im;uploads++}
 function draw(name,i,j,m,t,warp){put(0,all[name][i]);put(1,all[name][j]);let e=env(name);gl.uniform2f(U.ss,warp?e[0]:0,warp?e[0]:0);gl.uniform1f(U.cs,warp?e[1]:0);gl.uniform1f(U.t,t);gl.uniform1f(U.m,m);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawElements(gl.TRIANGLES,ix.length,gl.UNSIGNED_SHORT,0)}
 async function run(mode,rep){let dynamic=mode.startsWith('player_'),warp=mode.endsWith('_warp'),names=Object.keys(all),frame=0,namei=0,ai=0,ts=[];bound=[null,null];uploads=0;for(let warm=0;warm<30;warm++)await new Promise(r=>requestAnimationFrame(()=>{let name=names[0];draw(name,0,1,.5,warm/60,warp);r()}));let warmUploads=uploads;for(let n=0;n<180;n++)await new Promise(r=>requestAnimationFrame(t=>{ts.push(t);let name=names[0],i=0,j=1;if(dynamic){name=names[namei];let arr=all[name],hold=name==='schulterzucken'?7:name==='schulterdrehung'?10:18;if(frame%hold===0){ai=(ai+1)%arr.length;if(ai===0)namei=(namei+1)%names.length}i=ai;j=(ai+1)%arr.length}draw(name,i,j,.5,n/60,warp);frame++;r()}));let d=[];for(let i=1;i<ts.length;i++)d.push(ts[i]-ts[i-1]);return {mode,rep,dynamic,warp,warm_uploads:warmUploads,measured_uploads:uploads-warmUploads,...stats(d)}}
 const order=['static_base','player_base','player_warp','static_warp','static_warp','player_warp','player_base','static_base'],rows=[];let reps={};for(const mode of order){reps[mode]=(reps[mode]||0)+1;rows.push(await run(mode,reps[mode]))}
 function agg(mode){let x=rows.filter(r=>r.mode===mode);return {runs:x.length,mean_ms:x.reduce((s,r)=>s+r.mean_ms,0)/x.length,fps:x.reduce((s,r)=>s+r.fps,0)/x.length,p95_ms_max:Math.max(...x.map(r=>r.p95_ms)),over20_total:x.reduce((s,r)=>s+r.over20,0),measured_uploads_total:x.reduce((s,r)=>s+r.measured_uploads,0)}}
 let A={};for(const m of ['static_base','static_warp','player_base','player_warp'])A[m]=agg(m);A.warp_overhead_static_ms=A.static_warp.mean_ms-A.static_base.mean_ms;A.warp_overhead_player_ms=A.player_warp.mean_ms-A.player_base.mean_ms;A.player_overhead_base_ms=A.player_base.mean_ms-A.static_base.mean_ms;A.player_overhead_warp_ms=A.player_warp.mean_ms-A.static_warp.mean_ms;
 let R={schema:'BODY_PLAYER_PERF_ATTRIBUTION_AB/v1',scope:'REAL_WALL_CLOCK_READ_ONLY_FOUR_CONDITION',renderer,version:gl.getParameter(gl.VERSION),canvas:[620,414],vertices:v.length/2,triangles:ix.length/3,order,rows,aggregate:A,gl_error:gl.getError(),live_mutation:false};out.textContent=JSON.stringify(R);await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(R)});
})().catch(async e=>{out.textContent='ERROR '+e.stack;try{await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({error:String(e),stack:e.stack})})}catch(_){}})</script>'''


class State:
    report = None
    event = threading.Event()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--visual-root", default="/home/ai-core-node/.claude/star/visual")
    ap.add_argument("--chrome", default="/usr/bin/google-chrome")
    ap.add_argument("--timeout", type=float, default=80)
    args = ap.parse_args()
    root = pathlib.Path(args.visual_root).resolve()
    body = (root / "koerper_rgba").resolve()
    missing = [x for arr in SEQS.values() for x in arr if not (body / x).is_file()]
    if missing:
        print(json.dumps({"status": "MISSING_ASSETS", "missing": missing}))
        return 3

    with tempfile.TemporaryDirectory(prefix="body-perf-attribution-") as td_raw:
        td = pathlib.Path(td_raw)
        (td / "index.html").write_text(PAGE.replace("__SEQS__", json.dumps(SEQS)))

        class H(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                u = urlparse(self.path).path
                if u in ("/", "/index.html"):
                    p, content_type = td / "index.html", "text/html"
                elif u.startswith("/asset/"):
                    rel = pathlib.PurePosixPath(unquote(u[len("/asset/") :]))
                    if ".." in rel.parts:
                        self.send_response(403); self.end_headers(); return
                    p, content_type = body / pathlib.Path(*rel.parts), "image/png"
                else:
                    self.send_response(404); self.end_headers(); return
                if not p.is_file():
                    self.send_response(404); self.end_headers(); return
                payload = p.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def do_POST(self):
                if urlparse(self.path).path != "/report":
                    self.send_response(404); self.end_headers(); return
                State.report = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
                State.event.set()
                self.send_response(204); self.end_headers()

        srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        proc = subprocess.Popen(
            [
                args.chrome,
                "--headless=new",
                "--no-sandbox",
                "--use-gl=angle",
                "--disable-background-networking",
                "--no-first-run",
                f"--user-data-dir={td / 'profile'}",
                f"http://127.0.0.1:{srv.server_address[1]}/",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        ok = State.event.wait(args.timeout)
        try:
            proc.terminate(); stderr = proc.communicate(timeout=5)[1]
        except Exception:
            proc.kill(); stderr = proc.communicate()[1]
        srv.shutdown()
        report = State.report if ok else {"status": "NO_REPORT", "stderr_tail": stderr[-1600:]}
        print(json.dumps(report, sort_keys=True))
        if not ok or report.get("error"):
            return 2
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
