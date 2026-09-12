#!/usr/bin/env python3
"""Scratch-only final-display shoulder residual calibration on real body assets.

Finds the smallest residual amplitude that survives the actual 620x414 render
without touching the neck-lock ROI or creating silhouette holes. This does not
change the live avatar and does not claim perceptual superiority.
"""
from __future__ import annotations
import argparse, json, pathlib, subprocess, tempfile, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

FRAMES=[f'atmen__atmen_{i:03d}.png' for i in (0,3,6,9)]
SCALES=[0.5,1.0,1.5,2.0,2.5,3.0,4.0,5.0,6.0,8.0]
TIMES=[0.0,1.225,2.45,3.675,4.9,7.35]
PAGE=r'''<!doctype html><canvas id=c width=620 height=414></canvas><pre id=o></pre><script>
const FRAMES=__FRAMES__,SCALES=__SCALES__,TIMES=__TIMES__,W=620,H=414,SW=1536,SH=1024,cv=document.getElementById('c'),out=document.getElementById('o');
function load(p){return new Promise((r,j)=>{let i=new Image;i.onload=()=>r(i);i.onerror=()=>j(Error(p));i.src='/asset/'+p})}
function sh(g,t,s){let x=g.createShader(t);g.shaderSource(x,s);g.compileShader(x);if(!g.getShaderParameter(x,g.COMPILE_STATUS))throw Error(g.getShaderInfoLog(x));return x}
(async()=>{let imgs=new Map;for(const p of FRAMES)imgs.set(p,await load(p));let g=cv.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:true,premultipliedAlpha:false});if(!g)throw Error('no webgl');let dbg=g.getExtension('WEBGL_debug_renderer_info'),renderer=dbg?g.getParameter(dbg.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER);
let vs=`precision highp float;const float SW=1536.0,SH=1024.0;attribute vec2 p;uniform float shoulderScale,t;varying vec2 uv;float G(vec2 q,vec2 c,vec2 z){vec2 d=(q-c)/z;return exp(-.5*dot(d,d));}void main(){vec2 q=p;float bw=1306.,bh=519.,x0=117.,y0=505.;float b=sin(6.2831853*t/4.9),l=sin(6.2831853*t/8.7+.83),r=sin(6.2831853*t/11.3+2.14);float ld=shoulderScale*(-.46*b+.12*l),rd=shoulderScale*(-.42*b+.09*r),lr=radians(shoulderScale*(.085*l+.025*b)),rr=radians(shoulderScale*(-.070*r-.018*b));float lx=x0+.27*bw,rx=x0+.73*bw,sy=y0+.19*bh;float wl=G(q,vec2(lx,sy),vec2(.18*bw,.115*bh)),wr=G(q,vec2(rx,sy),vec2(.18*bw,.115*bh));float c0=y0+.38*bh,c1=y0+.62*bh,lo=q.y<=c0?1.:(q.y>=c1?0.:.5+.5*cos(3.14159265*(q.y-c0)/(c1-c0)));wl*=lo;wr*=lo;float dx=wl*(-lr*(q.y-sy))+wr*(-rr*(q.y-sy)),dy=wl*(ld+lr*(q.x-lx))+wr*(rd+rr*(q.x-rx));vec2 d=max(max(vec2(561.,505.)-q,q-vec2(977.,618.)),vec2(0.));float mv=clamp(length(d)/36.,0.,1.);q+=vec2(dx,dy)*mv;gl_Position=vec4(q.x/SW*2.-1.,1.-q.y/SH*2.,0,1);uv=p/vec2(SW,SH);}`;
let fs=`precision mediump float;varying vec2 uv;uniform sampler2D tex;void main(){gl_FragColor=texture2D(tex,uv);}`;let pr=g.createProgram();g.attachShader(pr,sh(g,g.VERTEX_SHADER,vs));g.attachShader(pr,sh(g,g.FRAGMENT_SHADER,fs));g.linkProgram(pr);if(!g.getProgramParameter(pr,g.LINK_STATUS))throw Error(g.getProgramInfoLog(pr));g.useProgram(pr);
function coords(M,st,e){let a=[];for(let x=0;x<=M;x+=st)a.push(Math.min(M,x));a.push(M,...e);return [...new Set(a)].sort((a,b)=>a-b)}let xs=coords(1536,96,[117,561,978,1423]),ys=coords(1024,64,[505,619]),v=[],ix=[];for(let y of ys)for(let x of xs)v.push(x,y);let nx=xs.length;for(let y=0;y<ys.length-1;y++)for(let x=0;x<xs.length-1;x++){let A=y*nx+x,B=A+1,C=A+nx,D=C+1;ix.push(A,C,B,B,C,D)}let vb=g.createBuffer();g.bindBuffer(g.ARRAY_BUFFER,vb);g.bufferData(g.ARRAY_BUFFER,new Float32Array(v),g.STATIC_DRAW);let a=g.getAttribLocation(pr,'p');g.enableVertexAttribArray(a);g.vertexAttribPointer(a,2,g.FLOAT,false,0,0);let ib=g.createBuffer();g.bindBuffer(g.ELEMENT_ARRAY_BUFFER,ib);g.bufferData(g.ELEMENT_ARRAY_BUFFER,new Uint16Array(ix),g.STATIC_DRAW);let us=g.getUniformLocation(pr,'shoulderScale'),ut=g.getUniformLocation(pr,'t');g.uniform1i(g.getUniformLocation(pr,'tex'),0);g.viewport(0,0,W,H);
let resize=document.createElement('canvas');resize.width=W;resize.height=H;let rc=resize.getContext('2d'),tex=new Map;for(const p of FRAMES){rc.clearRect(0,0,W,H);rc.drawImage(imgs.get(p),0,0,W,H);let x=g.createTexture();g.bindTexture(g.TEXTURE_2D,x);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MIN_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MAG_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_S,g.CLAMP_TO_EDGE);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_T,g.CLAMP_TO_EDGE);g.pixelStorei(g.UNPACK_FLIP_Y_WEBGL,1);g.texImage2D(g.TEXTURE_2D,0,g.RGBA,g.RGBA,g.UNSIGNED_BYTE,resize);tex.set(p,x)}
function draw(p,s,t){g.activeTexture(g.TEXTURE0);g.bindTexture(g.TEXTURE_2D,tex.get(p));g.uniform1f(us,s);g.uniform1f(ut,t);g.clear(g.COLOR_BUFFER_BIT);g.drawElements(g.TRIANGLES,ix.length,g.UNSIGNED_SHORT,0);g.finish();let q=new Uint8Array(W*H*4);g.readPixels(0,0,W,H,g.RGBA,g.UNSIGNED_BYTE,q);let top=new Uint8Array(q.length),row=W*4;for(let y=0;y<H;y++)top.set(q.subarray((H-1-y)*row,(H-y)*row),y*row);return top}
const neck={x0:Math.floor(561/SW*W),x1:Math.ceil(977/SW*W),y0:Math.floor(505/SH*H),y1:Math.ceil(618/SH*H)};
function met(A,B){let mae=0,mx=0,deep=0,inter=0,uni=0,c1=0,c3=0,c8=0,neckMax=0;for(let y=0;y<H;y++)for(let x=0;x<W;x++){let z=(y*W+x)*4,pm=0;for(let q=0;q<4;q++){let d=Math.abs(A[z+q]-B[z+q]);mae+=d;mx=Math.max(mx,d);pm=Math.max(pm,d);if(x>=neck.x0&&x<neck.x1&&y>=neck.y0&&y<neck.y1)neckMax=Math.max(neckMax,d)}if(pm>=1)c1++;if(pm>=3)c3++;if(pm>=8)c8++;let aa=A[z+3],bb=B[z+3];if(aa>=64&&bb<32)deep++;let av=aa>=16,bv=bb>=16;if(av&&bv)inter++;if(av||bv)uni++}return {rgba_mae:mae/(W*H*4),rgba_max:mx,changed_px_ge1:c1,changed_px_ge3:c3,changed_px_ge8:c8,changed_frac_ge3:c3/(W*H),neck_max_delta:neckMax,deep_hole_px:deep,jaccard:inter/Math.max(1,uni)}}
let rows=[],summary={};for(const s of SCALES){let rs=[];for(const p of FRAMES)for(const t of TIMES){let A=draw(p,0,t),B=draw(p,s,t),m=met(A,B);m.frame=p;m.t=t;rs.push(m);rows.push({scale:s,...m})}summary[String(s)]={tests:rs.length,max_changed_px_ge3:Math.max(...rs.map(x=>x.changed_px_ge3)),median_changed_px_ge3:[...rs].sort((a,b)=>a.changed_px_ge3-b.changed_px_ge3)[Math.floor(rs.length/2)].changed_px_ge3,max_changed_frac_ge3:Math.max(...rs.map(x=>x.changed_frac_ge3)),max_rgba_mae:Math.max(...rs.map(x=>x.rgba_mae)),max_neck_delta:Math.max(...rs.map(x=>x.neck_max_delta)),max_deep_hole_px:Math.max(...rs.map(x=>x.deep_hole_px)),min_jaccard:Math.min(...rs.map(x=>x.jaccard)),analytical_peak_vertical_display_px:s*.58*(H/SH)}}
let selected=null;for(const s of SCALES){let x=summary[String(s)];if(x.median_changed_px_ge3>=24&&x.max_changed_frac_ge3<=.03&&x.max_neck_delta===0&&x.max_deep_hole_px===0&&x.min_jaccard>=.9995&&x.analytical_peak_vertical_display_px>=.25&&x.analytical_peak_vertical_display_px<=1.0){selected=s;break}}
let R={schema:'BODY_SHOULDER_FINAL_DISPLAY_SIGNAL_SWEEP/v1',renderer,canvas:[W,H],source_canvas:[SW,SH],frames:FRAMES,times:TIMES,scales:SCALES,neck_display_box:neck,selection_rule:{median_changed_px_ge3_min:24,max_changed_frac_ge3:.03,max_neck_delta:0,max_deep_hole_px:0,min_jaccard:.9995,analytical_peak_vertical_display_px:[.25,1.0]},summary,selected_scale:selected,gl_error:g.getError(),live_mutation:false};out.textContent=JSON.stringify(R);await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(R)})})().catch(async e=>{await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({error:String(e),stack:e.stack})})})</script>'''
class S: report=None; event=threading.Event()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--timeout',type=float,default=100);a=ap.parse_args();body=(pathlib.Path(a.visual_root).resolve()/'koerper_rgba');miss=[p for p in FRAMES if not (body/p).is_file()]
 if miss:print(json.dumps({'missing':miss}));return 3
 with tempfile.TemporaryDirectory(prefix='body-signal-') as td:
  td=pathlib.Path(td);(td/'index.html').write_text(PAGE.replace('__FRAMES__',json.dumps(FRAMES)).replace('__SCALES__',json.dumps(SCALES)).replace('__TIMES__',json.dumps(TIMES)))
  class H(BaseHTTPRequestHandler):
   def log_message(self,*x):pass
   def do_GET(self):
    u=urlparse(self.path).path
    if u in ('/','/index.html'):p=td/'index.html';c='text/html'
    elif u.startswith('/asset/'):
     rel=pathlib.PurePosixPath(unquote(u[7:]));
     if '..' in rel.parts:self.send_response(403);self.end_headers();return
     p=body/pathlib.Path(*rel.parts);c='image/png'
    else:self.send_response(404);self.end_headers();return
    if not p.is_file():self.send_response(404);self.end_headers();return
    b=p.read_bytes();self.send_response(200);self.send_header('Content-Type',c);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
   def do_POST(self):
    S.report=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))));S.event.set();self.send_response(204);self.end_headers()
  srv=ThreadingHTTPServer(('127.0.0.1',0),H);threading.Thread(target=srv.serve_forever,daemon=True).start();p=subprocess.Popen([a.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run',f'--user-data-dir={td/"profile"}',f'http://127.0.0.1:{srv.server_address[1]}/'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True);ok=S.event.wait(a.timeout)
  try:p.terminate();err=p.communicate(timeout=5)[1]
  except Exception:p.kill();err=p.communicate()[1]
  srv.shutdown();r=S.report if ok else {'status':'NO_REPORT','stderr_tail':err[-1200:]};print(json.dumps(r,sort_keys=True));return 0 if ok and not r.get('error') else 2
if __name__=='__main__':raise SystemExit(main())
