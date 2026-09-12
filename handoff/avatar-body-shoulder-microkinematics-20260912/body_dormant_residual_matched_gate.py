#!/usr/bin/env python3
"""Dormant shoulder-residual integration + deterministic matched display gate.

Never mutates the live Avatar. It derives an in-memory candidate from the exact
live buehne.html, keeps the feature OFF by default, and runs BASE/OFF vs ON in
isolated headless Chrome against the same fixed breathing plate.

Scope: implementation-integrity / display-locality / scheduler-reuse gate.
This is deliberately NOT a subjective perceptual-superiority claim.
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

EXPECTED_LIVE_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
W, H = 620, 414
SW, SH = 1536.0, 1024.0

CSS_ANCHOR = '#koerper-schicht2{opacity:0}'
CSS_INSERT = '''#koerper-schicht2{opacity:0}\n  /* Dormant candidate. OFF unless ?body_residual=1; production URL has no flag. */\n  #koerper-residual-canvas{position:absolute;inset:0;width:100%;height:100%;display:none;\n    pointer-events:none;z-index:1;transform-origin:50% 50%}'''
DOM_ANCHOR = '<div id="koerper-dreh"><img id="koerper-schicht" src="/koerper_rgba/koerper_zero.png" alt=""><img id="koerper-schicht2" src="/koerper_rgba/koerper_zero.png" alt=""></div>'
DOM_INSERT = '<div id="koerper-dreh"><img id="koerper-schicht" src="/koerper_rgba/koerper_zero.png" alt=""><img id="koerper-schicht2" src="/koerper_rgba/koerper_zero.png" alt=""><canvas id="koerper-residual-canvas" width="620" height="414"></canvas></div>'
STATE_ANCHOR = 'let atmenAktivSchicht = "koerper-schicht";'
LOOP_ANCHOR = '  koerperSchritt(t);\n'
LOOP_INSERT = '  koerperSchritt(t);\n  if(window.__bodyResidualDormant) window.__bodyResidualDormant.step(t);\n'

SEED_MODULE = r'''<script>
(()=>{if(new URLSearchParams(location.search).get('body_test_lock')!=='1')return;
let s=0x9e3779b9;Math.random=()=>{s=(Math.imul(s,1664525)+1013904223)>>>0;return s/4294967296};})();
</script>'''

MODULE = r'''

// ── Dormant shoulder residual candidate: existing scheduler remains sole authority ──
(() => {
  const Q=new URLSearchParams(location.search);
  const enabled=Q.get('body_residual')==='1';
  const testLock=Q.get('body_test_lock')==='1';
  const cv=$("koerper-residual-canvas"), A=$("koerper-schicht"), B=$("koerper-schicht2");
  const S={schema:'BODY_RESIDUAL_DORMANT/v1',enabled,ready:false,error:null,frames:0,draws:0,
    uploads:0,scale:0,target:0,policy:'off',renderer:null,glError:null,lastT:null,cache:new Map(),bound:[null,null]};
  window.__bodyResidualDormant=S;
  function report(){if(!testLock)return;fetch('/__body_residual_report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
    schema:S.schema,enabled:S.enabled,ready:S.ready,error:S.error,frames:S.frames,draws:S.draws,uploads:S.uploads,
    scale:S.scale,target:S.target,policy:S.policy,renderer:S.renderer,gl_error:S.glError,fps:window.__buehneFps||0
  })}).catch(()=>{})}
  setInterval(report,500);
  function fixedPlate(){
    if(!testLock || typeof ATMEN_BILDER==='undefined' || !ATMEN_BILDER.length)return;
    const src=ATMEN_BILDER[Math.min(3,ATMEN_BILDER.length-1)];
    if(new URL(A.src,location.href).pathname!==new URL(src,location.href).pathname)A.src=src;
    A.style.opacity='1';B.style.opacity='0';
  }
  function classify(path){
    path=(path||'').toLowerCase();
    if(/schulter.?zuck|schulter.?dreh/.test(path))return ['blocked',0.0];
    if(/aufricht|lehn|gewicht/.test(path))return ['mild',1.5];
    if(/atmen|breath/.test(path))return ['breathing',4.0];
    return ['unknown',0.0];
  }
  function choose(){
    const oa=Math.max(0,Math.min(1,parseFloat(getComputedStyle(A).opacity)||0));
    const ob=Math.max(0,Math.min(1,parseFloat(getComputedStyle(B).opacity)||0));
    const ca=classify(new URL(A.src,location.href).pathname), cb=classify(new URL(B.src,location.href).pathname);
    const visible=[];if(oa>.01)visible.push(ca);if(ob>.01)visible.push(cb);
    if(visible.some(x=>x[0]==='blocked'))return ['blocked',0.0];
    if(visible.some(x=>x[0]==='mild'))return ['mild',1.5];
    if(visible.length && visible.every(x=>x[0]==='breathing'))return ['breathing',4.0];
    return ['unknown',0.0];
  }
  fixedPlate();
  if(!enabled){
    S.step=(t)=>{S.frames++;fixedPlate();S.policy='off';S.target=0;S.scale=0};
    return;
  }
  try{
    const gl=cv.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:true,premultipliedAlpha:false});
    if(!gl)throw Error('no-webgl');
    const dbg=gl.getExtension('WEBGL_debug_renderer_info');
    S.renderer=dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
    function sh(type,src){const x=gl.createShader(type);gl.shaderSource(x,src);gl.compileShader(x);if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(x));return x}
    const VS=`precision highp float;const float SW=1536.0,SH=1024.0;attribute vec2 p;uniform float shoulderScale,t;varying vec2 uv;float G(vec2 q,vec2 c,vec2 z){vec2 d=(q-c)/z;return exp(-.5*dot(d,d));}void main(){vec2 q=p;float bw=1306.,bh=519.,x0=117.,y0=505.;float b=sin(6.2831853*t/4.9),l=sin(6.2831853*t/8.7+.83),r=sin(6.2831853*t/11.3+2.14);float ld=shoulderScale*(-.46*b+.12*l),rd=shoulderScale*(-.42*b+.09*r),lr=radians(shoulderScale*(.085*l+.025*b)),rr=radians(shoulderScale*(-.070*r-.018*b));float lx=x0+.27*bw,rx=x0+.73*bw,sy=y0+.19*bh;float wl=G(q,vec2(lx,sy),vec2(.18*bw,.115*bh)),wr=G(q,vec2(rx,sy),vec2(.18*bw,.115*bh));float c0=y0+.38*bh,c1=y0+.62*bh,lo=q.y<=c0?1.:(q.y>=c1?0.:.5+.5*cos(3.14159265*(q.y-c0)/(c1-c0)));wl*=lo;wr*=lo;float dx=wl*(-lr*(q.y-sy))+wr*(-rr*(q.y-sy)),dy=wl*(ld+lr*(q.x-lx))+wr*(rd+rr*(q.x-rx));vec2 d=max(max(vec2(561.,505.)-q,q-vec2(977.,618.)),vec2(0.));float mv=clamp(length(d)/36.,0.,1.);q+=vec2(dx,dy)*mv;gl_Position=vec4(q.x/SW*2.-1.,1.-q.y/SH*2.,0,1);uv=p/vec2(SW,SH);}`;
    const FS=`precision mediump float;varying vec2 uv;uniform sampler2D a,b;uniform float oa,ob;void main(){vec4 A=texture2D(a,uv),B=texture2D(b,uv);vec4 Ap=vec4(A.rgb*A.a*oa,A.a*oa),Bp=vec4(B.rgb*B.a*ob,B.a*ob);vec4 P=Bp+Ap*(1.-Bp.a);gl_FragColor=P.a>0.?vec4(P.rgb/P.a,P.a):vec4(0.);}`;
    const pr=gl.createProgram(),vs=sh(gl.VERTEX_SHADER,VS),fs=sh(gl.FRAGMENT_SHADER,FS);gl.attachShader(pr,vs);gl.attachShader(pr,fs);gl.linkProgram(pr);if(!gl.getProgramParameter(pr,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(pr));gl.useProgram(pr);
    function coords(M,st,edges){let a=[];for(let x=0;x<=M;x+=st)a.push(Math.min(M,x));a.push(M,...edges);return [...new Set(a)].sort((a,b)=>a-b)}
    const xs=coords(1536,96,[117,561,978,1423]),ys=coords(1024,64,[505,619]),verts=[],ix=[];
    for(const y of ys)for(const x of xs)verts.push(x,y);const nx=xs.length;
    for(let y=0;y<ys.length-1;y++)for(let x=0;x<xs.length-1;x++){const a=y*nx+x,b=a+1,c=a+nx,d=c+1;ix.push(a,c,b,b,c,d)}
    const vb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(verts),gl.STATIC_DRAW);const al=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(al);gl.vertexAttribPointer(al,2,gl.FLOAT,false,0,0);
    const ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(ix),gl.STATIC_DRAW);
    const U={scale:gl.getUniformLocation(pr,'shoulderScale'),t:gl.getUniformLocation(pr,'t'),oa:gl.getUniformLocation(pr,'oa'),ob:gl.getUniformLocation(pr,'ob')};gl.uniform1i(gl.getUniformLocation(pr,'a'),0);gl.uniform1i(gl.getUniformLocation(pr,'b'),1);gl.viewport(0,0,620,414);gl.disable(gl.BLEND);
    const resize=document.createElement('canvas');resize.width=620;resize.height=414;const rc=resize.getContext('2d',{alpha:true}),tex=[gl.createTexture(),gl.createTexture()];
    tex.forEach((x,i)=>{gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,x);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE)});
    function load(path){let e=S.cache.get(path);if(e)return e;e={ok:false,err:false,canvas:null};S.cache.set(path,e);const im=new Image();im.onload=()=>{try{const c=document.createElement('canvas');c.width=620;c.height=414;const x=c.getContext('2d',{alpha:true});x.drawImage(im,0,0,620,414);e.canvas=c;e.ok=true}catch(z){e.err=true;S.error='resize:'+z}};im.onerror=()=>{e.err=true;S.error='load:'+path};im.src=path;return e}
    function put(i,path){if(S.bound[i]===path)return true;const e=load(path);if(!e.ok)return false;gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,tex[i]);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,e.canvas);S.bound[i]=path;S.uploads++;return true}
    S.step=(ms)=>{
      S.frames++;fixedPlate();const pa=new URL(A.src,location.href).pathname,pb=new URL(B.src,location.href).pathname;if(!put(0,pa)||!put(1,pb))return;
      const [policy,target]=choose();S.policy=policy;S.target=target;const dt=S.lastT==null?16.67:Math.max(0,Math.min(100,ms-S.lastT));S.lastT=ms;
      const tau=target>S.scale?120:180,maxStep=4*dt/tau;S.scale+=Math.max(-maxStep,Math.min(maxStep,target-S.scale));
      const oa=Math.max(0,Math.min(1,parseFloat(getComputedStyle(A).opacity)||0)),ob=Math.max(0,Math.min(1,parseFloat(getComputedStyle(B).opacity)||0));
      cv.style.transform=(typeof _atmenTransform!=='undefined'?_atmenTransform:'');cv.style.filter=(typeof _atmenFilter!=='undefined'?_atmenFilter:'');
      gl.uniform1f(U.scale,S.scale);gl.uniform1f(U.t,ms/1000);gl.uniform1f(U.oa,oa);gl.uniform1f(U.ob,ob);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawElements(gl.TRIANGLES,ix.length,gl.UNSIGNED_SHORT,0);gl.flush();S.glError=gl.getError();S.draws++;
      if(!S.ready&&S.draws>3){S.ready=true;cv.style.display='block';A.style.visibility='hidden';B.style.visibility='hidden'}
    };
  }catch(err){S.error=String(err);S.enabled=false;cv.style.display='none';A.style.visibility='visible';B.style.visibility='visible';S.step=(t)=>{S.frames++;fixedPlate()}}
})();
'''


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def once(s: str, old: str, new: str, label: str) -> str:
    n=s.count(old)
    if n!=1: raise RuntimeError(f'{label}: expected exactly one anchor, got {n}')
    return s.replace(old,new,1)


def patch(src: str) -> str:
    src=src.replace('<head>','<head>'+SEED_MODULE,1) if '<head>' in src else SEED_MODULE+src
    src=once(src,CSS_ANCHOR,CSS_INSERT,'css')
    src=once(src,DOM_ANCHOR,DOM_INSERT,'dom')
    src=once(src,STATE_ANCHOR,STATE_ANCHOR+MODULE,'state')
    src=once(src,LOOP_ANCHOR,LOOP_INSERT,'loop')
    return src


class State:
    reports={False:[],True:[]}


def run_chrome(chrome: str, url: str, out: pathlib.Path, budget_ms: int) -> dict:
    prof=tempfile.mkdtemp(prefix='body-residual-profile-')
    cmd=[chrome,'--headless=new','--no-sandbox','--use-gl=angle','--ignore-gpu-blocklist','--enable-gpu-rasterization','--disable-background-networking','--no-first-run','--hide-scrollbars','--force-device-scale-factor=1',f'--window-size={W},{H}',f'--virtual-time-budget={budget_ms}',f'--user-data-dir={prof}',f'--screenshot={out}',url]
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=max(30,budget_ms/1000+20))
    return {'rc':p.returncode,'stderr_tail':p.stderr[-1200:]}


def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--budget-ms',type=int,default=6500);a=ap.parse_args()
    root=pathlib.Path(a.visual_root).resolve();live=(root/'buehne.html').read_bytes();live_sha=sha(live)
    if live_sha!=EXPECTED_LIVE_SHA256:
        print(json.dumps({'schema':'BODY_DORMANT_RESIDUAL_MATCHED_GATE/v1','status':'SOURCE_MISMATCH','expected':EXPECTED_LIVE_SHA256,'observed':live_sha}));return 5
    candidate=patch(live.decode('utf-8')).encode()
    with tempfile.TemporaryDirectory(prefix='body-dormant-gate-') as td_s:
        td=pathlib.Path(td_s);(td/'buehne.html').write_bytes(candidate)
        class H(BaseHTTPRequestHandler):
            def log_message(self,*x): pass
            def do_GET(self):
                u=urlparse(self.path).path
                if u in ('/','/buehne.html'):
                    b=(td/'buehne.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
                if u=='/api/status':
                    b=json.dumps({'buehne':{'broadcast_value':1.0,'ueberraschung':0.0},'zuschauer':0}).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
                rel=pathlib.PurePosixPath(unquote(u.lstrip('/')))
                if '..' in rel.parts:self.send_response(403);self.end_headers();return
                p=(root/pathlib.Path(*rel.parts)).resolve()
                if root not in p.parents and p!=root:self.send_response(403);self.end_headers();return
                if not p.is_file():self.send_response(404);self.end_headers();return
                b=p.read_bytes();ctype='image/png' if p.suffix.lower()=='.png' else ('image/jpeg' if p.suffix.lower() in ('.jpg','.jpeg') else 'application/octet-stream');self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
            def do_POST(self):
                u=urlparse(self.path).path;n=int(self.headers.get('Content-Length','0'));b=self.rfile.read(n)
                if u=='/__body_residual_report':
                    try:r=json.loads(b);State.reports[bool(r.get('enabled'))].append(r)
                    except Exception:pass
                self.send_response(204);self.end_headers()
        srv=ThreadingHTTPServer(('127.0.0.1',0),H);threading.Thread(target=srv.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{srv.server_address[1]}/?body_test_lock=1'
        off=td/'off.png';on=td/'on.png';ro=run_chrome(a.chrome,base+'&body_residual=0',off,a.budget_ms);rn=run_chrome(a.chrome,base+'&body_residual=1',on,a.budget_ms);srv.shutdown()
        try:
            import cv2, numpy as np
            I0=cv2.imread(str(off),cv2.IMREAD_COLOR);I1=cv2.imread(str(on),cv2.IMREAD_COLOR)
            if I0 is None or I1 is None or I0.shape!=I1.shape: raise RuntimeError(f'screenshot decode/shape {None if I0 is None else I0.shape} {None if I1 is None else I1.shape}')
            d=np.abs(I0.astype(np.int16)-I1.astype(np.int16)).max(axis=2);changed=d>=3
            x0,x1=round(561/SW*W),round(977/SW*W);y0,y1=round(505/SH*H),round(618/SH*H)
            neck=d[y0:y1+1,x0:x1+1]
            sy0,sy1=round(505/SH*H),round(760/SH*H);sx0,sx1=round(117/SW*W),round(1423/SW*W)
            shoulder=changed[sy0:sy1+1,sx0:sx1+1].copy();shoulder[max(0,y0-sy0):max(0,y1-sy0+1),max(0,x0-sx0):max(0,x1-sx0+1)]=False
            metrics={'shape':list(I0.shape),'changed_px_ge3':int(changed.sum()),'changed_fraction_ge3':float(changed.mean()),'max_channel_delta':int(d.max()),'neck_max_delta':int(neck.max()) if neck.size else None,'shoulder_changed_px_ge3':int(shoulder.sum())}
        except Exception as e:
            metrics={'analysis_error':str(e)}
        after_sha=sha((root/'buehne.html').read_bytes());offrep=State.reports[False][-1] if State.reports[False] else None;onrep=State.reports[True][-1] if State.reports[True] else None
        checks={'chrome_off_rc0':ro['rc']==0,'chrome_on_rc0':rn['rc']==0,'live_sha_invariant':after_sha==live_sha,'off_report':bool(offrep and not offrep.get('enabled')),'on_ready':bool(onrep and onrep.get('ready')),'on_gl_zero':bool(onrep and onrep.get('gl_error')==0),'on_breathing_policy':bool(onrep and onrep.get('policy')=='breathing' and float(onrep.get('scale',0))>=3.9),'display_signal':bool('changed_px_ge3' in metrics and metrics['changed_px_ge3']>=24 and metrics['changed_fraction_ge3']<=0.03),'neck_lock':bool(metrics.get('neck_max_delta') is not None and metrics['neck_max_delta']<=2),'shoulder_locality':bool(metrics.get('shoulder_changed_px_ge3',0)>=24)}
        ok=all(checks.values());out={'schema':'BODY_DORMANT_RESIDUAL_MATCHED_GATE/v1','status':'PASS' if ok else 'FAIL','scope':'dormant-candidate matched display integrity; NOT perceptual superiority; NOT production activation','live_html_sha256_before':live_sha,'live_html_sha256_after':after_sha,'candidate_html_sha256':sha(candidate),'feature_default':'OFF','test_lock':'breathing plate ATMEN_BILDER[3]','off_report':offrep,'on_report':onrep,'metrics':metrics,'checks':checks,'chrome':{'off':ro,'on':rn}};print(json.dumps(out,sort_keys=True));return 0 if ok else 1

if __name__=='__main__': raise SystemExit(main())
