#!/usr/bin/env python3
"""Real-wall-clock A/B for the body shoulder mesh on the admitted AMD WebGL path.
Scratch-only: temporary localhost server + temporary Chrome profile, no live writes.
"""
from __future__ import annotations
import argparse,json,pathlib,subprocess,tempfile,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse

PAGE=r'''<!doctype html><meta charset=utf-8><canvas id=c width=620 height=414></canvas><pre id=o>running</pre><script>
const cv=document.getElementById('c'),out=document.getElementById('o');
function load(u){return new Promise((r,j)=>{let i=new Image;i.onload=()=>r(i);i.onerror=()=>j(Error(u));i.src=u})}
function sh(gl,t,s){let x=gl.createShader(t);gl.shaderSource(x,s);gl.compileShader(x);if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(x));return x}
function pct(a,p){let x=[...a].sort((u,v)=>u-v);return x[Math.min(x.length-1,Math.floor((x.length-1)*p))]}
function stats(a){let m=a.reduce((x,y)=>x+y,0)/a.length;return {n:a.length,mean:m,p50:pct(a,.5),p95:pct(a,.95),p99:pct(a,.99),max:Math.max(...a),over20:a.filter(x=>x>20).length,over25:a.filter(x=>x>25).length,over33:a.filter(x=>x>33).length,fps:1000/m}}
(async()=>{const im=await load('/body.png');const gl=cv.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:false});if(!gl)throw Error('no webgl');
const dbg=gl.getExtension('WEBGL_debug_renderer_info');const renderer=dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
const VS=`precision highp float;const float SW=1536.0,SH=1024.0;attribute vec2 p;uniform float s,t;varying vec2 uv;float G(vec2 q,vec2 c,vec2 z){vec2 d=(q-c)/z;return exp(-.5*dot(d,d));}void main(){vec2 q=p;float bw=1306.,bh=519.,x0=117.,y0=505.;float b=sin(6.2831853*t/4.9),l=sin(6.2831853*t/8.7+.83),r=sin(6.2831853*t/11.3+2.14);float ld=s*(-.46*b+.12*l),rd=s*(-.42*b+.09*r),lr=radians(s*(.085*l+.025*b)),rr=radians(s*(-.070*r-.018*b)),cd=s*(-.18*b);float lx=x0+.27*bw,rx=x0+.73*bw,sy=y0+.19*bh;float wl=G(q,vec2(lx,sy),vec2(.18*bw,.115*bh)),wr=G(q,vec2(rx,sy),vec2(.18*bw,.115*bh)),wc=G(q,vec2(x0+.5*bw,y0+.31*bh),vec2(.25*bw,.13*bh));float c0=y0+.38*bh,c1=y0+.62*bh,lo=q.y<=c0?1.:(q.y>=c1?0.:.5+.5*cos(3.14159265*(q.y-c0)/(c1-c0)));wl*=lo;wr*=lo;wc*=lo;float dx=wl*(-lr*(q.y-sy))+wr*(-rr*(q.y-sy)),dy=wl*(ld+lr*(q.x-lx))+wr*(rd+rr*(q.x-rx))+wc*cd;vec2 d=max(max(vec2(561.,505.)-q,q-vec2(977.,618.)),vec2(0.));float mv=clamp(length(d)/36.,0.,1.);q+=vec2(dx,dy)*mv;gl_Position=vec4(q.x/SW*2.-1.,1.-q.y/SH*2.,0,1);uv=p/vec2(SW,SH);}`;
const FS=`precision mediump float;varying vec2 uv;uniform sampler2D tex;void main(){gl_FragColor=texture2D(tex,uv);}`;
let pr=gl.createProgram();gl.attachShader(pr,sh(gl,gl.VERTEX_SHADER,VS));gl.attachShader(pr,sh(gl,gl.FRAGMENT_SHADER,FS));gl.linkProgram(pr);if(!gl.getProgramParameter(pr,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(pr));gl.useProgram(pr);
function coords(M,st,e){let a=[];for(let x=0;x<=M;x+=st)a.push(Math.min(M,x));a.push(M,...e);return [...new Set(a)].sort((a,b)=>a-b)}let xs=coords(1536,96,[117,561,978,1423]),ys=coords(1024,64,[505,619]),v=[],ix=[];for(let y of ys)for(let x of xs)v.push(x,y);let nx=xs.length;for(let y=0;y<ys.length-1;y++)for(let x=0;x<xs.length-1;x++){let a=y*nx+x,b=a+1,c=a+nx,d=c+1;ix.push(a,c,b,b,c,d)}
let vb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(v),gl.STATIC_DRAW);let al=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(al);gl.vertexAttribPointer(al,2,gl.FLOAT,false,0,0);let ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(ix),gl.STATIC_DRAW);let us=gl.getUniformLocation(pr,'s'),ut=gl.getUniformLocation(pr,'t');let tx=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tx);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);for(let n of [gl.TEXTURE_MIN_FILTER,gl.TEXTURE_MAG_FILTER])gl.texParameteri(gl.TEXTURE_2D,n,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im);gl.viewport(0,0,620,414);
function draw(mode,i){gl.uniform1f(us,mode==='warp'?1.5:0);gl.uniform1f(ut,i/60);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawElements(gl.TRIANGLES,ix.length,gl.UNSIGNED_SHORT,0)}async function raf(mode,n=300,w=45){for(let i=0;i<w;i++)await new Promise(r=>requestAnimationFrame(()=>{draw(mode,i);r()}));let ts=[];for(let i=0;i<n;i++)await new Promise(r=>requestAnimationFrame(t=>{ts.push(t);draw(mode,i+w);r()}));let d=[];for(let i=1;i<ts.length;i++)d.push(ts[i]-ts[i-1]);return stats(d)}function force(mode,n=160){let a=[];for(let i=0;i<20;i++){draw(mode,i);gl.finish()}for(let i=0;i<n;i++){let t=performance.now();draw(mode,i);gl.finish();a.push(performance.now()-t)}return stats(a)}let seq=[];for(const m of ['base','warp','warp','base'])seq.push({mode:m,raf:await raf(m),forced:force(m)});let R={schema:'BODY_WEBGL_REALTIME_AB/v1',renderer,version:gl.getParameter(gl.VERSION),size:[620,414],vertices:v.length/2,triangles:ix.length/3,seq,gl_error:gl.getError()};out.textContent=JSON.stringify(R);await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(R)});
})().catch(async e=>{out.textContent='ERROR '+e.stack;try{await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({error:String(e),stack:e.stack})})}catch(_){}})</script>'''
class S: report=None; ev=threading.Event()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--timeout',type=float,default=45);a=ap.parse_args();root=pathlib.Path(a.root).resolve()
 with tempfile.TemporaryDirectory(prefix='body-rtab-') as td:
  td=pathlib.Path(td);(td/'body.png').write_bytes((root/'koerper_rgba/koerper_zero.png').read_bytes());(td/'index.html').write_text(PAGE)
  class H(BaseHTTPRequestHandler):
   def log_message(self,*x): pass
   def do_GET(self):
    n={'/':'index.html','/index.html':'index.html','/body.png':'body.png'}.get(urlparse(self.path).path)
    if not n:self.send_response(404);self.end_headers();return
    b=(td/n).read_bytes();self.send_response(200);self.send_header('Content-Type','image/png' if n.endswith('png') else 'text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
   def do_POST(self):
    if urlparse(self.path).path!='/report':self.send_response(404);self.end_headers();return
    S.report=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))));S.ev.set();self.send_response(204);self.end_headers()
  srv=ThreadingHTTPServer(('127.0.0.1',0),H);threading.Thread(target=srv.serve_forever,daemon=True).start();p=subprocess.Popen([a.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run',f'--user-data-dir={td/"profile"}',f'http://127.0.0.1:{srv.server_address[1]}/'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True);ok=S.ev.wait(a.timeout)
  try:p.terminate();err=p.communicate(timeout=5)[1]
  except Exception:p.kill();err=p.communicate()[1]
  srv.shutdown();print(json.dumps(S.report if ok else {'status':'NO_REPORT','stderr_tail':err[-1600:]},sort_keys=True));return 0 if ok and not S.report.get('error') else 2
if __name__=='__main__':raise SystemExit(main())
