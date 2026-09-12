#!/usr/bin/env python3
"""Exact-live shadow integration gate for the cached 620x414 body GPU backend.

This NEVER mutates live buehne.html. It verifies the exact live SHA, derives a
shadow HTML in memory with four narrowly-scoped edits, serves the untouched
visual asset root, and runs the real page scheduler in Chrome.

The shadow backend intentionally does NOT add residual shoulder warp yet. This
gate asks one question only: can the existing single body scheduler drive a
pre-resized WebGL source-over backend without duplicate animation authority,
while preserving the existing body transform/filter chain and real rAF cadence?

Promotion of residual shoulder mesh remains a subsequent bounded gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

EXPECTED_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"

CSS_ANCHOR = '#koerper-schicht2{opacity:0}'
CSS_INSERT = '''#koerper-schicht2{opacity:0}\n  /* GO shadow candidate: same stacking level as the photographed body pair. */\n  #koerper-gpu-shadow{position:absolute;inset:0;width:100%;height:100%;display:none;\n    pointer-events:none;z-index:1;transform-origin:50% 50%}'''

DOM_ANCHOR = '<div id="koerper-dreh"><img id="koerper-schicht" src="/koerper_rgba/koerper_zero.png" alt=""><img id="koerper-schicht2" src="/koerper_rgba/koerper_zero.png" alt=""></div>'
DOM_INSERT = '<div id="koerper-dreh"><img id="koerper-schicht" src="/koerper_rgba/koerper_zero.png" alt=""><img id="koerper-schicht2" src="/koerper_rgba/koerper_zero.png" alt=""><canvas id="koerper-gpu-shadow" width="620" height="414"></canvas></div>'

PRELOAD_ANCHOR = 'ATMEN_BILDER.forEach(src => { const vorlade = new Image(); vorlade.src = src; });'
PRELOAD_INSERT = '/* GO shadow: breathing source preload is owned by __bodyGpuShadow below. */'

STATE_ANCHOR = 'let atmenAktivSchicht = "koerper-schicht";'

CROSSFADE_OLD = '''function koerperCrossfade(src){
  const naechsteSchicht = atmenAktivSchicht === "koerper-schicht" ? "koerper-schicht2" : "koerper-schicht";
  $(naechsteSchicht).src = src;
  // ⭐⭐ PERF-FIX 2026-09-11: gleiche Vor-Synchronisation wie bei
  // kopfRollTick()/sonderausdruckZeigen() -- atmen() schreibt Transform/
  // Filter nur noch auf atmenAktivSchicht (die aktuell sichtbare Koerper-
  // Ebene). Bevor die naechste Ebene sichtbar wird, bekommt sie hier den
  // brandaktuellen Wert -- sonst Pop beim Umschalten.
  $(naechsteSchicht).style.transform = _atmenTransform;
  $(naechsteSchicht).style.filter = _atmenFilter;
  $(naechsteSchicht).style.opacity = 1;
  $(atmenAktivSchicht).style.opacity = 0;
  atmenAktivSchicht = naechsteSchicht;
}'''

CROSSFADE_NEW = '''function koerperCrossfade(src){
  const naechsteSchicht = atmenAktivSchicht === "koerper-schicht" ? "koerper-schicht2" : "koerper-schicht";
  const gpu = window.__bodyGpuShadow;
  if(gpu && gpu.enabled && gpu.assign(naechsteSchicht, src)){
    // Preserve the existing state-carrier transition + transform authority.
    // The hidden IMG no longer receives the expensive full-resolution src.
    $(naechsteSchicht).style.transform = _atmenTransform;
    $(naechsteSchicht).style.filter = _atmenFilter;
    $(naechsteSchicht).style.opacity = 1;
    $(atmenAktivSchicht).style.opacity = 0;
    atmenAktivSchicht = naechsteSchicht;
    gpu.crossfades++;
    return;
  }
  // Fail-open fallback: byte-for-byte legacy behavior if GPU/cache is unavailable.
  $(naechsteSchicht).src = src;
  $(naechsteSchicht).style.transform = _atmenTransform;
  $(naechsteSchicht).style.filter = _atmenFilter;
  $(naechsteSchicht).style.opacity = 1;
  $(atmenAktivSchicht).style.opacity = 0;
  atmenAktivSchicht = naechsteSchicht;
  if(gpu){ gpu.fallbackCrossfades++; gpu.load(src); }
}'''

GPU_MODULE = r'''

// ── GO exact-live shadow body backend: single scheduler, alternate renderer ──
(() => {
  const W=620,H=414;
  const cv=$("koerper-gpu-shadow"), a=$("koerper-schicht"), b=$("koerper-schicht2");
  const S={enabled:false,ready:false,error:null,crossfades:0,fallbackCrossfades:0,
    frames:0,textureUploads:0,intermediateBlendFrames:0,cache:new Map(),bound:[null,null],
    renderer:null,glError:null,started:performance.now()};
  window.__bodyGpuShadow=S;
  a.dataset.bodySrc=a.getAttribute("src")||"/koerper_rgba/koerper_zero.png";
  b.dataset.bodySrc=b.getAttribute("src")||"/koerper_rgba/koerper_zero.png";
  function load(src){
    let e=S.cache.get(src);
    if(e) return e;
    e={ok:false,err:false,canvas:null};S.cache.set(src,e);
    const im=new Image();
    im.onload=()=>{
      try{
        const c=document.createElement("canvas");c.width=W;c.height=H;
        const x=c.getContext("2d",{alpha:true});x.drawImage(im,0,0,W,H);
        e.canvas=c;e.ok=true;
      }catch(err){e.err=true;S.error="resize:"+err}
    };
    im.onerror=()=>{e.err=true;S.error="load:"+src};
    im.src=src;return e;
  }
  S.load=load;
  S.assign=(id,src)=>{const e=load(src);if(!e.ok)return false;$(id).dataset.bodySrc=src;return true};
  try{
    const gl=cv.getContext("webgl",{alpha:true,antialias:false,preserveDrawingBuffer:true,premultipliedAlpha:false});
    if(!gl) throw Error("no-webgl");
    const dbg=gl.getExtension("WEBGL_debug_renderer_info");
    S.renderer=dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
    function sh(t,s){const x=gl.createShader(t);gl.shaderSource(x,s);gl.compileShader(x);if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(x));return x}
    const vs=sh(gl.VERTEX_SHADER,`attribute vec2 p;varying vec2 uv;void main(){gl_Position=vec4(p*2.-1.,0.,1.);uv=p;}`);
    const fs=sh(gl.FRAGMENT_SHADER,`precision highp float;varying vec2 uv;uniform sampler2D ta,tb;uniform float oa,ob;void main(){vec4 A=texture2D(ta,uv),B=texture2D(tb,uv);vec4 Ap=vec4(A.rgb*A.a*oa,A.a*oa),Bp=vec4(B.rgb*B.a*ob,B.a*ob);vec4 P=Bp+Ap*(1.-Bp.a);gl_FragColor=P.a>0.?vec4(P.rgb/P.a,P.a):vec4(0.);}`);
    const pr=gl.createProgram();gl.attachShader(pr,vs);gl.attachShader(pr,fs);gl.linkProgram(pr);if(!gl.getProgramParameter(pr,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(pr));gl.useProgram(pr);
    const vb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([0,0,1,0,0,1,0,1,1,0,1,1]),gl.STATIC_DRAW);
    const p=gl.getAttribLocation(pr,"p");gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
    const U={oa:gl.getUniformLocation(pr,"oa"),ob:gl.getUniformLocation(pr,"ob")};
    const tex=[gl.createTexture(),gl.createTexture()];
    tex.forEach((t,i)=>{gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,t);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE)});
    gl.uniform1i(gl.getUniformLocation(pr,"ta"),0);gl.uniform1i(gl.getUniformLocation(pr,"tb"),1);gl.viewport(0,0,W,H);gl.disable(gl.BLEND);
    function put(i,src){if(S.bound[i]===src)return true;const e=load(src);if(!e.ok)return false;gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,tex[i]);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,e.canvas);S.bound[i]=src;S.textureUploads++;return true}
    function draw(){
      S.frames++;
      const sa=a.dataset.bodySrc||a.getAttribute("src"), sb=b.dataset.bodySrc||b.getAttribute("src");
      if(!put(0,sa)||!put(1,sb)){requestAnimationFrame(draw);return}
      const oa=Math.max(0,Math.min(1,parseFloat(getComputedStyle(a).opacity)||0));
      const ob=Math.max(0,Math.min(1,parseFloat(getComputedStyle(b).opacity)||0));
      if((oa>0.01&&oa<0.99)||(ob>0.01&&ob<0.99))S.intermediateBlendFrames++;
      // Preserve the exact existing breathing transform/filter authority.
      if(cv.style.transform!==_atmenTransform)cv.style.transform=_atmenTransform;
      if(cv.style.filter!==_atmenFilter)cv.style.filter=_atmenFilter;
      gl.uniform1f(U.oa,oa);gl.uniform1f(U.ob,ob);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawArrays(gl.TRIANGLES,0,6);
      S.glError=gl.getError();requestAnimationFrame(draw);
    }
    // Pre-resize breathing frames and the current neutral body once, outside the hot path.
    [a.dataset.bodySrc,b.dataset.bodySrc,...ATMEN_BILDER].forEach(load);
    const arm=()=>{
      const ea=load(a.dataset.bodySrc),eb=load(b.dataset.bodySrc);
      if(ea.err||eb.err){S.error="initial-cache-failed";return}
      if(!ea.ok||!eb.ok){setTimeout(arm,20);return}
      S.enabled=true;S.ready=true;cv.style.display="block";a.style.visibility="hidden";b.style.visibility="hidden";
      requestAnimationFrame(draw);
    };
    arm();
  }catch(err){S.error=String(err);S.enabled=false;cv.style.display="none"}
})();
'''

REPORT_MODULE = r'''
<script>
setTimeout(()=>{
  const s=window.__bodyGpuShadow||{};
  const r={schema:'BODY_LIVE_GPU_SHADOW/v1',enabled:!!s.enabled,ready:!!s.ready,error:s.error||null,
    renderer:s.renderer||null,frames:s.frames||0,texture_uploads:s.textureUploads||0,
    crossfades:s.crossfades||0,fallback_crossfades:s.fallbackCrossfades||0,
    intermediate_blend_frames:s.intermediateBlendFrames||0,gl_error:s.glError,
    fps:window.__buehneFps||0,canvas:[document.getElementById('koerper-gpu-shadow')?.width||0,document.getElementById('koerper-gpu-shadow')?.height||0],
    canvas_display:getComputedStyle(document.getElementById('koerper-gpu-shadow')).display,
    body_a_visibility:getComputedStyle(document.getElementById('koerper-schicht')).visibility,
    body_b_visibility:getComputedStyle(document.getElementById('koerper-schicht2')).visibility,
    body_a_state:document.getElementById('koerper-schicht').dataset.bodySrc||null,
    body_b_state:document.getElementById('koerper-schicht2').dataset.bodySrc||null};
  fetch('/__body_gpu_report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(r)}).catch(()=>{});
},10000);
</script>
'''


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def replace_once(s: str, old: str, new: str, label: str) -> str:
    n = s.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, got {n}")
    return s.replace(old, new, 1)


def patch_source(src: str) -> str:
    src = replace_once(src, CSS_ANCHOR, CSS_INSERT, "css")
    src = replace_once(src, DOM_ANCHOR, DOM_INSERT, "dom")
    src = replace_once(src, PRELOAD_ANCHOR, PRELOAD_INSERT, "preload")
    src = replace_once(src, STATE_ANCHOR, STATE_ANCHOR + GPU_MODULE, "state")
    src = replace_once(src, CROSSFADE_OLD, CROSSFADE_NEW, "crossfade")
    # Add the bounded report before the final body close tag when possible.
    if '</body>' in src:
        src = src.replace('</body>', REPORT_MODULE + '</body>', 1)
    else:
        src += REPORT_MODULE
    return src


class RunState:
    report = None
    event = threading.Event()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--visual-root', default='/home/ai-core-node/.claude/star/visual')
    ap.add_argument('--chrome', default='/usr/bin/google-chrome')
    ap.add_argument('--timeout', type=float, default=25.0)
    a = ap.parse_args()
    root = pathlib.Path(a.visual_root).resolve()
    live = root / 'buehne.html'
    before = live.read_bytes()
    live_sha = sha256_bytes(before)
    if live_sha != EXPECTED_SHA256:
        print(json.dumps({'schema':'BODY_LIVE_GPU_SHADOW/v1','status':'SOURCE_MISMATCH','expected':EXPECTED_SHA256,'observed':live_sha}))
        return 5
    shadow = patch_source(before.decode('utf-8'))
    shadow_sha = sha256_bytes(shadow.encode())

    with tempfile.TemporaryDirectory(prefix='body-live-gpu-shadow-') as td_s:
        td = pathlib.Path(td_s)
        (td/'buehne.html').write_text(shadow)

        class H(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def send_bytes(self, p: pathlib.Path, ctype: str):
                if not p.is_file():
                    self.send_response(404);self.end_headers();return
                b=p.read_bytes();self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
            def do_GET(self):
                u=urlparse(self.path).path
                if u in ('/','/buehne.html'):
                    return self.send_bytes(td/'buehne.html','text/html; charset=utf-8')
                if u == '/api/status':
                    b=json.dumps({'buehne':{'broadcast_value':1.0,'ueberraschung':0.0}}).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
                rel=pathlib.PurePosixPath(unquote(u.lstrip('/')))
                if '..' in rel.parts:
                    self.send_response(403);self.end_headers();return
                p=root/pathlib.Path(*rel.parts)
                ext=p.suffix.lower();ctype={'png':'image/png','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.js':'application/javascript','.json':'application/json','.css':'text/css','.wav':'audio/wav','.mp3':'audio/mpeg'}.get(ext,'application/octet-stream')
                return self.send_bytes(p,ctype)
            def do_POST(self):
                u=urlparse(self.path).path
                if u == '/__body_gpu_report':
                    try: RunState.report=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
                    except Exception as e: RunState.report={'error':'report-decode:'+str(e)}
                    RunState.event.set();self.send_response(204);self.end_headers();return
                if u == '/api/fps':
                    _=self.rfile.read(int(self.headers.get('Content-Length','0')));self.send_response(204);self.end_headers();return
                self.send_response(204);self.end_headers()

        srv=ThreadingHTTPServer(('127.0.0.1',0),H)
        threading.Thread(target=srv.serve_forever,daemon=True).start()
        cmd=[a.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run',f'--user-data-dir={td/"profile"}',f'--window-size=900,700',f'http://127.0.0.1:{srv.server_address[1]}/buehne.html']
        p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        ok=RunState.event.wait(a.timeout)
        try:
            p.terminate();err=p.communicate(timeout=5)[1]
        except Exception:
            p.kill();err=p.communicate()[1]
        srv.shutdown()

    after_sha=sha256_bytes(live.read_bytes())
    report=RunState.report if ok else {'schema':'BODY_LIVE_GPU_SHADOW/v1','status':'NO_REPORT','stderr_tail':err[-1800:]}
    report['live_sha256']=live_sha
    report['shadow_sha256']=shadow_sha
    report['live_source_unchanged']=(after_sha==live_sha)
    checks={
        'report_received':ok,
        'enabled':bool(report.get('enabled')),
        'ready':bool(report.get('ready')),
        'no_backend_error':report.get('error') in (None,''),
        'gl_error_zero':report.get('gl_error') in (0,None) and bool(report.get('enabled')),
        'frames_ge_300':int(report.get('frames',0))>=300,
        'crossfades_ge_12':int(report.get('crossfades',0))>=12,
        'intermediate_blend_frames_ge_12':int(report.get('intermediate_blend_frames',0))>=12,
        'texture_uploads_ge_6':int(report.get('texture_uploads',0))>=6,
        'fps_ge_55':float(report.get('fps',0))>=55.0,
        'gpu_canvas_visible':report.get('canvas_display')!='none',
        'legacy_body_hidden':report.get('body_a_visibility')=='hidden' and report.get('body_b_visibility')=='hidden',
        'live_source_unchanged':after_sha==live_sha,
    }
    report['acceptance']=checks
    report['pass']=all(checks.values())
    print(json.dumps(report,sort_keys=True))
    return 0 if report['pass'] else 2


if __name__=='__main__':
    raise SystemExit(main())
