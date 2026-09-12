#!/usr/bin/env python3
"""Real-wall-clock WebGL A/B for the guarded avatar depth warp.

Runs entirely in a temporary localhost scratch server + temporary Chrome profile.
No virtual-time flags are used.  The page compares a one-texture pass-through
shader to the production-shaped depth-warp shader on the same canvas, renderer
and source/control textures.  requestAnimationFrame cadence and forced-finish
per-draw wall times are reported separately.

No live avatar source, assets, profile or service are modified.
"""
from __future__ import annotations
import argparse, json, os, pathlib, subprocess, tempfile, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import cv2, numpy as np
from PIL import Image

COEFF=np.array([1.,1/3,-1/3,-1.],np.float32)

def ss(e0,e1,x):
    t=np.clip((x-e0)/(e1-e0),0,1); return t*t*(3-2*t)

def make_control(root:pathlib.Path, roll='+00'):
    anc=json.loads((root/'rig2/augen_anker_exakt.json').read_text()); a0=np.array([anc['augen_anker_roll0']['x'],anc['augen_anker_roll0']['y']],float); o=anc['werte'][str(int(roll))]; eye=tuple(a0+np.array([o['dx_px'],o['dy_px']]))
    base=np.array(Image.open(root/f'kopf_rgba/roll/gier_+00_nick_+00_roll_{roll}.png').convert('RGBA'),np.uint8)
    d=root/f'kopf_rgba_parallax/gier_+00_nick_+00_roll_{roll}'
    sl=[np.array(Image.open(next(d.glob(f'slice_{i}_*.png'))).convert('RGBA'),np.uint8) for i in range(4)]
    aa=np.stack([s[:,:,3].astype(np.float32)/255 for s in sl]); den=np.maximum(aa.sum(0),1e-6); depth=(aa*COEFF[:,None,None]).sum(0)/den;depth[den<.02]=0;depth=cv2.GaussianBlur(depth,(0,0),1)
    a=base[:,:,3].astype(np.float32)/255;gx=cv2.Sobel(a,cv2.CV_32F,1,0,ksize=3);gy=cv2.Sobel(a,cv2.CV_32F,0,1,ksize=3);grad=np.sqrt(gx*gx+gy*gy);yy,xx=np.mgrid[0:a.shape[0],0:a.shape[1]].astype(np.float32);ell=((xx-eye[0])/220)**2+((yy-eye[1])/125)**2;gate=ss(.70,.97,a)*(1-ss(.015,.10,grad))*ss(1.,1.55,ell);ctrl=np.clip(depth*gate,-1,1);enc=np.clip(np.rint(ctrl*127+128),1,255).astype(np.uint8);return enc,eye

PAGE=r'''<!doctype html><meta charset=utf-8><canvas id=c width=620 height=414></canvas><pre id=o>running</pre><script>
const out=document.getElementById('o'),cv=document.getElementById('c');
function load(u){return new Promise((res,rej)=>{let i=new Image();i.onload=()=>res(i);i.onerror=()=>rej(Error(u));i.src=u})}
function sh(gl,t,s){let x=gl.createShader(t);gl.shaderSource(x,s);gl.compileShader(x);if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(x));return x}
function prog(gl,frag){let p=gl.createProgram();gl.attachShader(p,sh(gl,gl.VERTEX_SHADER,'attribute vec2 p;varying vec2 uv;void main(){uv=p*.5+.5;gl_Position=vec4(p,0.,1.);}'));gl.attachShader(p,sh(gl,gl.FRAGMENT_SHADER,frag));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));return p}
function tex(gl,img){let t=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,t);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,img);return t}
function pct(a,p){let x=[...a].sort((u,v)=>u-v);return x[Math.min(x.length-1,Math.floor((x.length-1)*p))]}
function stats(a){let mean=a.reduce((x,y)=>x+y,0)/a.length;return {n:a.length,mean,p50:pct(a,.5),p95:pct(a,.95),p99:pct(a,.99),max:Math.max(...a),over20:a.filter(x=>x>20).length,over25:a.filter(x=>x>25).length,over33:a.filter(x=>x>33).length,fps:1000/mean}}
(async()=>{
 const [bi,ci]=await Promise.all([load('/base.png'),load('/ctrl.png')]);
 const gl=cv.getContext('webgl',{alpha:true,antialias:false,depth:false,stencil:false,preserveDrawingBuffer:false});if(!gl)throw Error('no webgl');
 const dbg=gl.getExtension('WEBGL_debug_renderer_info'); const renderer=dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
 const vbuf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vbuf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
 const baseFrag='precision highp float;varying vec2 uv;uniform sampler2D b;void main(){gl_FragColor=texture2D(b,uv);}';
 const warpFrag='precision highp float;varying vec2 uv;uniform sampler2D b;uniform sampler2D c;uniform float amp;void main(){vec4 q=texture2D(b,uv);float ctrl=(texture2D(c,uv).r*255.0-128.0)/127.0;vec4 w=texture2D(b,uv-vec2((amp/1536.0)*ctrl,0.0));gl_FragColor=vec4(w.rgb,q.a);}';
 const P={base:prog(gl,baseFrag),warp:prog(gl,warpFrag)};
 const bt=tex(gl,bi),ct=tex(gl,ci);gl.viewport(0,0,cv.width,cv.height);
 function bind(mode,idx){let p=P[mode];gl.useProgram(p);let loc=gl.getAttribLocation(p,'p');gl.bindBuffer(gl.ARRAY_BUFFER,vbuf);gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,bt);gl.uniform1i(gl.getUniformLocation(p,'b'),0);if(mode==='warp'){gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,ct);gl.uniform1i(gl.getUniformLocation(p,'c'),1);gl.uniform1f(gl.getUniformLocation(p,'amp'),1.0+0.25*Math.sin(idx*.071));}}
 function draw(mode,idx){bind(mode,idx);gl.drawArrays(gl.TRIANGLE_STRIP,0,4)}
 async function rafStage(mode,n=300,warm=45){for(let i=0;i<warm;i++)await new Promise(r=>requestAnimationFrame(t=>{draw(mode,i);r()}));let ts=[];for(let i=0;i<n;i++)await new Promise(r=>requestAnimationFrame(t=>{ts.push(t);draw(mode,i+warm);r()}));let d=[];for(let i=1;i<ts.length;i++)d.push(ts[i]-ts[i-1]);return stats(d)}
 function forcedStage(mode,n=160){let a=[];for(let i=0;i<20;i++){draw(mode,i);gl.finish()}for(let i=0;i<n;i++){let t=performance.now();draw(mode,i);gl.finish();a.push(performance.now()-t)}return stats(a)}
 let seq=[];for(const mode of ['base','warp','warp','base'])seq.push({mode,raf:await rafStage(mode),forced:forcedStage(mode)});
 const report={schema:'DEPTHWARP_WEBGL_REALTIME_AB/v1',renderer,version:gl.getParameter(gl.VERSION),size:[cv.width,cv.height],devicePixelRatio,seq,gl_error:gl.getError()};out.textContent=JSON.stringify(report);await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(report)});
})().catch(async e=>{out.textContent='ERROR '+e.stack;try{await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({error:String(e),stack:e.stack})})}catch(_){}})
</script>'''

class State:
    report=None; event=threading.Event()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--timeout',type=float,default=45);args=ap.parse_args();root=pathlib.Path(args.visual_root).resolve();enc,eye=make_control(root)
    with tempfile.TemporaryDirectory(prefix='depthwarp-rtab-') as td:
        td=pathlib.Path(td); Image.fromarray(np.dstack([enc,enc,enc,np.full(enc.shape,255,np.uint8)]),'RGBA').save(td/'ctrl.png',optimize=True); base=(root/'kopf_rgba/roll/gier_+00_nick_+00_roll_+00.png').read_bytes(); (td/'base.png').write_bytes(base); (td/'index.html').write_text(PAGE)
        class H(BaseHTTPRequestHandler):
            def log_message(self,*a): pass
            def do_GET(self):
                p=urlparse(self.path).path; mp={'/':'index.html','/index.html':'index.html','/base.png':'base.png','/ctrl.png':'ctrl.png'}; name=mp.get(p)
                if not name:self.send_response(404);self.end_headers();return
                data=(td/name).read_bytes(); typ='text/html' if name.endswith('html') else 'image/png';self.send_response(200);self.send_header('Content-Type',typ);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
            def do_POST(self):
                if urlparse(self.path).path!='/report':self.send_response(404);self.end_headers();return
                n=int(self.headers.get('Content-Length','0'));State.report=json.loads(self.rfile.read(n));State.event.set();self.send_response(204);self.end_headers()
        srv=ThreadingHTTPServer(('127.0.0.1',0),H);threading.Thread(target=srv.serve_forever,daemon=True).start();port=srv.server_address[1]
        prof=td/'profile'; cmd=[args.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run',f'--user-data-dir={prof}',f'http://127.0.0.1:{port}/'];p=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        ok=State.event.wait(args.timeout);stderr=''
        try:p.terminate();stderr=p.communicate(timeout=5)[1]
        except Exception:
            p.kill();stderr=p.communicate()[1]
        srv.shutdown();
        print('DEPTHWARP_WEBGL_REALTIME_AB/v1')
        print('EYE',eye,'CONTROL_BYTES',(td/'ctrl.png').stat().st_size)
        if not ok or State.report is None:
            print(json.dumps({'status':'NO_REPORT','chrome_rc':p.returncode,'stderr_tail':stderr[-2000:]},sort_keys=True));return 2
        print(json.dumps(State.report,sort_keys=True))
        print('CHROME_RC_AFTER_TERMINATE',p.returncode)
        if stderr.strip():print('CHROME_STDERR_TAIL',stderr[-2000:])
        return 0
if __name__=='__main__':raise SystemExit(main())
