#!/usr/bin/env python3
"""Compare fixed-DOM two-image CSS/source-over semantics with WebGL source-over.

The live DOM always paints koerper-schicht2 over koerper-schicht at equal z-index.
Which layer is old/new alternates. This gate models both directions explicitly and
proves the zero-residual WebGL compositor can preserve that ordering. Read-only.
"""
from __future__ import annotations
import argparse,json,pathlib,subprocess,tempfile,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,unquote

F={
'atmen':[f'atmen__atmen_{i:03d}.png' for i in range(12)],
'schulterzucken':[f'schulterzucken/zucken_{i:03d}.png' for i in range(8)],
'aufrichten':[f'aufrichten/aufrichten_{i:03d}.png' for i in range(8)],
'lehnen':[f'lehnen/lehnen_{x}.png' for x in ['+00','+05','+10','+15','+20','+15','+10','+05','+00']],
'gewicht':[f'gewicht/gewicht_{x}.png' for x in ['+00','+05','+10','+15','+10','+05','+00','-05','-10','-05','+00']],
'schulterdrehung':[f'schulterdrehung/schulter_{x}.png' for x in ['+00','+05','+10','+15','+10','+05','+00','-05','-10','-05','+00']]}

PAGE=r'''<!doctype html><canvas id=ref width=620 height=414></canvas><canvas id=glc width=620 height=414></canvas><pre id=o></pre><script>
const F=__F__,W=620,H=414,ref=document.getElementById('ref'),rc=ref.getContext('2d',{alpha:true}),cv=document.getElementById('glc'),out=document.getElementById('o');
const paths=[...new Set(Object.values(F).flat())];function load(p){return new Promise((r,j)=>{let i=new Image;i.onload=()=>r(i);i.onerror=()=>j(Error(p));i.src='/asset/'+p})}function sh(g,t,s){let x=g.createShader(t);g.shaderSource(x,s);g.compileShader(x);if(!g.getShaderParameter(x,g.COMPILE_STATUS))throw Error(g.getShaderInfoLog(x));return x}
(async()=>{let imgs=new Map;for(const p of paths)imgs.set(p,await load(p));let g=cv.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:true,premultipliedAlpha:false});if(!g)throw Error('no webgl');let dbg=g.getExtension('WEBGL_debug_renderer_info'),renderer=dbg?g.getParameter(dbg.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER);
let vs=`attribute vec2 p;varying vec2 uv;void main(){gl_Position=vec4(p*2.-1.,0.,1.);uv=vec2(p.x,1.-p.y);}`,fs=`precision mediump float;varying vec2 uv;uniform sampler2D layer1,layer2;uniform float o1,o2;void main(){vec4 A=texture2D(layer1,uv),B=texture2D(layer2,uv);vec4 Ap=vec4(A.rgb*A.a*o1,A.a*o1),Bp=vec4(B.rgb*B.a*o2,B.a*o2);vec4 P=Bp+Ap*(1.-Bp.a);gl_FragColor=P.a>0.?vec4(P.rgb/P.a,P.a):vec4(0.);}`;let pr=g.createProgram();g.attachShader(pr,sh(g,g.VERTEX_SHADER,vs));g.attachShader(pr,sh(g,g.FRAGMENT_SHADER,fs));g.linkProgram(pr);if(!g.getProgramParameter(pr,g.LINK_STATUS))throw Error(g.getProgramInfoLog(pr));g.useProgram(pr);let vb=g.createBuffer();g.bindBuffer(g.ARRAY_BUFFER,vb);g.bufferData(g.ARRAY_BUFFER,new Float32Array([0,0,1,0,0,1,0,1,1,0,1,1]),g.STATIC_DRAW);let a=g.getAttribLocation(pr,'p');g.enableVertexAttribArray(a);g.vertexAttribPointer(a,2,g.FLOAT,false,0,0);let tex=[g.createTexture(),g.createTexture()];tex.forEach((t,i)=>{g.activeTexture(g.TEXTURE0+i);g.bindTexture(g.TEXTURE_2D,t);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MIN_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MAG_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_S,g.CLAMP_TO_EDGE);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_T,g.CLAMP_TO_EDGE)});g.uniform1i(g.getUniformLocation(pr,'layer1'),0);g.uniform1i(g.getUniformLocation(pr,'layer2'),1);let u1=g.getUniformLocation(pr,'o1'),u2=g.getUniformLocation(pr,'o2');g.viewport(0,0,W,H);let bound=[null,null],resize=document.createElement('canvas');resize.width=W;resize.height=H;let xc=resize.getContext('2d');function bind(i,p){if(bound[i]===p)return;xc.clearRect(0,0,W,H);xc.drawImage(imgs.get(p),0,0,W,H);g.activeTexture(g.TEXTURE0+i);g.bindTexture(g.TEXTURE_2D,tex[i]);g.pixelStorei(g.UNPACK_FLIP_Y_WEBGL,1);g.texImage2D(g.TEXTURE_2D,0,g.RGBA,g.RGBA,g.UNSIGNED_BYTE,resize);bound[i]=p}
function webgl(layer1,layer2,o1,o2){bind(0,layer1);bind(1,layer2);g.uniform1f(u1,o1);g.uniform1f(u2,o2);g.clear(g.COLOR_BUFFER_BIT);g.drawArrays(g.TRIANGLES,0,6);g.finish();let p=new Uint8Array(W*H*4);g.readPixels(0,0,W,H,g.RGBA,g.UNSIGNED_BYTE,p);let top=new Uint8Array(p.length),row=W*4;for(let y=0;y<H;y++)top.set(p.subarray((H-1-y)*row,(H-y)*row),y*row);return top}
function css(layer1,layer2,o1,o2){rc.clearRect(0,0,W,H);rc.globalCompositeOperation='source-over';rc.globalAlpha=o1;rc.drawImage(imgs.get(layer1),0,0,W,H);rc.globalAlpha=o2;rc.drawImage(imgs.get(layer2),0,0,W,H);rc.globalAlpha=1;return new Uint8Array(rc.getImageData(0,0,W,H).data)}
function met(A,B){let mae=0,am=0,mx=0,deep=0,inter=0,uni=0;for(let i=0;i<W*H;i++){let z=i*4;for(let q=0;q<4;q++){let d=Math.abs(A[z+q]-B[z+q]);mae+=d;mx=Math.max(mx,d)}let x=A[z+3],y=B[z+3];am+=Math.abs(x-y);if(x>=64&&y<32)deep++;let xa=x>=16,ya=y>=16;if(xa&&ya)inter++;if(xa||ya)uni++}return {rgba_mae:mae/(W*H*4),rgba_max:mx,alpha_mae:am/(W*H),deep_hole_px:deep,jaccard:inter/Math.max(1,uni)}}
let R={schema:'BODY_CROSSFADE_SOURCEOVER_IDENTITY/v1',renderer,gl_error:null,families:{},directions:{layer1_to_layer2:{},layer2_to_layer1:{}}};for(const [name,arr] of Object.entries(F)){for(const dir of ['layer1_to_layer2','layer2_to_layer1']){let rows=[];for(let i=0;i<arr.length-1;i++)for(const m of [0,.25,.5,.75,1]){let l1,l2,o1,o2;if(dir==='layer1_to_layer2'){l1=arr[i];l2=arr[i+1];o1=1-m;o2=m}else{l1=arr[i+1];l2=arr[i];o1=m;o2=1-m}let A=css(l1,l2,o1,o2),B=webgl(l1,l2,o1,o2);rows.push(met(A,B))}R.directions[dir][name]={tests:rows.length,max_rgba_mae:Math.max(...rows.map(x=>x.rgba_mae)),max_rgba_max:Math.max(...rows.map(x=>x.rgba_max)),max_alpha_mae:Math.max(...rows.map(x=>x.alpha_mae)),max_deep_hole_px:Math.max(...rows.map(x=>x.deep_hole_px)),min_jaccard:Math.min(...rows.map(x=>x.jaccard))}}}R.gl_error=g.getError();out.textContent=JSON.stringify(R);await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(R)})})().catch(async e=>{await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({error:String(e),stack:e.stack})})})</script>'''
class S:report=None;event=threading.Event()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--timeout',type=float,default=80);a=ap.parse_args();body=(pathlib.Path(a.visual_root).resolve()/'koerper_rgba');miss=[p for arr in F.values() for p in arr if not (body/p).is_file()]
 if miss:print(json.dumps({'missing':miss}));return 3
 with tempfile.TemporaryDirectory(prefix='body-sourceover-') as td:
  td=pathlib.Path(td);(td/'index.html').write_text(PAGE.replace('__F__',json.dumps(F)))
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
