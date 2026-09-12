#!/usr/bin/env python3
"""Read-only discriminator for the remaining DOM/WebGL source-over residual.

This does NOT relax the failed raw-transparent v2 gate. It separates three causes:
1) one-layer texture/raster roundtrip,
2) transparent-buffer manual source-over,
3) final visible source-over over opaque backgrounds using fixed-function GL blending.
No live avatar file is modified.
"""
from __future__ import annotations
import argparse,json,pathlib,subprocess,tempfile,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,unquote

PAIRS={
'atmen':('atmen__atmen_000.png','atmen__atmen_001.png'),
'schulterzucken':('schulterzucken/zucken_003.png','schulterzucken/zucken_004.png'),
'aufrichten':('aufrichten/aufrichten_003.png','aufrichten/aufrichten_004.png'),
'lehnen':('lehnen/lehnen_+10.png','lehnen/lehnen_+15.png'),
'gewicht':('gewicht/gewicht_+10.png','gewicht/gewicht_+15.png'),
'schulterdrehung':('schulterdrehung/schulter_+10.png','schulterdrehung/schulter_+15.png'),
}
PAGE=r'''<!doctype html><meta charset=utf-8><canvas id=r width=620 height=414></canvas><canvas id=g width=620 height=414></canvas><pre id=o></pre><script>
const P=__PAIRS__,W=620,H=414,rc=document.getElementById('r').getContext('2d',{alpha:true}),cv=document.getElementById('g'),out=document.getElementById('o');
const paths=[...new Set(Object.values(P).flat())];function load(p){return new Promise((R,J)=>{let i=new Image;i.onload=()=>R(i);i.onerror=()=>J(Error('load '+p));i.src='/asset/'+p})}function sh(g,t,s){let x=g.createShader(t);g.shaderSource(x,s);g.compileShader(x);if(!g.getShaderParameter(x,g.COMPILE_STATUS))throw Error(g.getShaderInfoLog(x));return x}
function met(A,B,rgbOnly=false){let sum=0,n=0,mx=0,alpha=0,deep=0,inter=0,uni=0;for(let i=0;i<W*H;i++){let z=i*4;for(let q=0;q<(rgbOnly?3:4);q++){let d=Math.abs(A[z+q]-B[z+q]);sum+=d;n++;mx=Math.max(mx,d)}let a=A[z+3],b=B[z+3];alpha+=Math.abs(a-b);if(a>=64&&b<32)deep++;let x=a>=16,y=b>=16;if(x&&y)inter++;if(x||y)uni++}return {mae:sum/n,max:mx,alpha_mae:alpha/(W*H),deep_hole_px:deep,jaccard:inter/Math.max(1,uni)}}
(async()=>{let I=new Map;for(const p of paths)I.set(p,await load(p));let gl=cv.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:true,premultipliedAlpha:false});if(!gl)throw Error('no webgl');let dbg=gl.getExtension('WEBGL_debug_renderer_info'),renderer=dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
let vs=`attribute vec2 p;varying vec2 uv;void main(){gl_Position=vec4(p*2.-1.,0.,1.);uv=p;}`,fs=`precision mediump float;varying vec2 uv;uniform sampler2D tex;uniform float op;void main(){vec4 T=texture2D(tex,uv);gl_FragColor=vec4(T.rgb,T.a*op);}`;let pr=gl.createProgram();gl.attachShader(pr,sh(gl,gl.VERTEX_SHADER,vs));gl.attachShader(pr,sh(gl,gl.FRAGMENT_SHADER,fs));gl.linkProgram(pr);if(!gl.getProgramParameter(pr,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(pr));gl.useProgram(pr);let vb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([0,0,1,0,0,1,0,1,1,0,1,1]),gl.STATIC_DRAW);let a=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,2,gl.FLOAT,false,0,0);let uop=gl.getUniformLocation(pr,'op');gl.uniform1i(gl.getUniformLocation(pr,'tex'),0);gl.viewport(0,0,W,H);
let rs=document.createElement('canvas');rs.width=W;rs.height=H;let xc=rs.getContext('2d',{alpha:true}),tex=new Map;for(const p of paths){xc.clearRect(0,0,W,H);xc.drawImage(I.get(p),0,0,W,H);let t=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,t);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,rs);tex.set(p,t)}
function read(){let p=new Uint8Array(W*H*4),q=new Uint8Array(p.length),row=W*4;gl.readPixels(0,0,W,H,gl.RGBA,gl.UNSIGNED_BYTE,p);for(let y=0;y<H;y++)q.set(p.subarray((H-1-y)*row,(H-y)*row),y*row);return q}function bind(p){gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,tex.get(p))}function draw(p,op){bind(p);gl.uniform1f(uop,op);gl.drawArrays(gl.TRIANGLES,0,6)}function refPix(){return new Uint8Array(rc.getImageData(0,0,W,H).data)}
function refOne(p,bg){rc.save();rc.globalCompositeOperation='copy';rc.fillStyle=bg;rc.globalAlpha=1;rc.fillRect(0,0,W,H);rc.globalCompositeOperation='source-over';rc.drawImage(I.get(p),0,0,W,H);rc.restore();return refPix()}function glOne(p,bg){let c=bg==='black'?0:bg==='gray'?.5:1;gl.disable(gl.BLEND);gl.clearColor(c,c,c,1);gl.clear(gl.COLOR_BUFFER_BIT);gl.enable(gl.BLEND);gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA);draw(p,1);gl.finish();return read()}
function refPair(p1,p2,m,bg){rc.save();rc.globalCompositeOperation='copy';rc.fillStyle=bg;rc.globalAlpha=1;rc.fillRect(0,0,W,H);rc.globalCompositeOperation='source-over';rc.globalAlpha=1-m;rc.drawImage(I.get(p1),0,0,W,H);rc.globalAlpha=m;rc.drawImage(I.get(p2),0,0,W,H);rc.restore();return refPix()}function glPair(p1,p2,m,bg){let c=bg==='black'?0:bg==='gray'?.5:1;gl.disable(gl.BLEND);gl.clearColor(c,c,c,1);gl.clear(gl.COLOR_BUFFER_BIT);gl.enable(gl.BLEND);gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA);draw(p1,1-m);draw(p2,m);gl.finish();return read()}
let R={schema:'BODY_SOURCEOVER_RESIDUAL_DIAGNOSTIC/v1',renderer,single:{},pair:{},gl_error:null};for(const [name,[p1,p2]] of Object.entries(P)){R.single[name]={};R.pair[name]={};for(const [bg,css] of [['black','#000'],['gray','#808080'],['white','#fff']]){R.single[name][bg]=met(refOne(p1,css),glOne(p1,bg),true);let rows=[];for(const m of [.25,.5,.75])rows.push(met(refPair(p1,p2,m,css),glPair(p1,p2,m,bg),true));R.pair[name][bg]={max_rgb_mae:Math.max(...rows.map(x=>x.mae)),max_rgb_max:Math.max(...rows.map(x=>x.max)),max_alpha_mae:Math.max(...rows.map(x=>x.alpha_mae)),min_jaccard:Math.min(...rows.map(x=>x.jaccard)),max_deep_hole_px:Math.max(...rows.map(x=>x.deep_hole_px))}}}R.gl_error=gl.getError();out.textContent=JSON.stringify(R);await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(R)})})().catch(async e=>{try{await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({error:String(e),stack:e.stack})})}catch(_){}})</script>'''
class S: report=None; event=threading.Event()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--timeout',type=float,default=90);a=ap.parse_args();body=(pathlib.Path(a.visual_root).resolve()/'koerper_rgba');miss=[p for pair in PAIRS.values() for p in pair if not (body/p).is_file()]
 if miss:print(json.dumps({'status':'MISSING_ASSETS','missing':miss}));return 3
 with tempfile.TemporaryDirectory(prefix='body-residual-') as td:
  td=pathlib.Path(td);(td/'index.html').write_text(PAGE.replace('__PAIRS__',json.dumps(PAIRS)))
  class H(BaseHTTPRequestHandler):
   def log_message(self,*x):pass
   def do_GET(self):
    u=urlparse(self.path).path
    if u in ('/','/index.html'):p=td/'index.html';c='text/html'
    elif u.startswith('/asset/'):
     rel=pathlib.PurePosixPath(unquote(u[len('/asset/'):]))
     if '..' in rel.parts:self.send_response(403);self.end_headers();return
     p=body/pathlib.Path(*rel.parts);c='image/png'
    else:self.send_response(404);self.end_headers();return
    if not p.is_file():self.send_response(404);self.end_headers();return
    b=p.read_bytes();self.send_response(200);self.send_header('Content-Type',c);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
   def do_POST(self):
    if urlparse(self.path).path!='/report':self.send_response(404);self.end_headers();return
    S.report=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))));S.event.set();self.send_response(204);self.end_headers()
  srv=ThreadingHTTPServer(('127.0.0.1',0),H);threading.Thread(target=srv.serve_forever,daemon=True).start();p=subprocess.Popen([a.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run',f'--user-data-dir={td/"profile"}',f'http://127.0.0.1:{srv.server_address[1]}/'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True);ok=S.event.wait(a.timeout)
  try:p.terminate();err=p.communicate(timeout=5)[1]
  except Exception:p.kill();err=p.communicate()[1]
  srv.shutdown();r=S.report if ok else {'status':'NO_REPORT','stderr_tail':err[-1600:]};print(json.dumps(r,sort_keys=True));return 0 if ok and not r.get('error') else 2
if __name__=='__main__':raise SystemExit(main())
