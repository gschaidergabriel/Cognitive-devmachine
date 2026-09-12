#!/usr/bin/env python3
"""Direct final-pixel DOM <img> crossfade vs WebGL source-over screenshot gate.

Uses one Chrome screenshot containing a left column of real DOM image-layer
crossfades and a right WebGL atlas rendered from the same original full-resolution
body textures. This avoids Canvas2D as a proxy for the live browser compositor.
Scratch-only; live files are read-only.
"""
from __future__ import annotations
import argparse, json, pathlib, subprocess, tempfile, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote
from PIL import Image
import numpy as np

F={
'atmen':[f'atmen__atmen_{i:03d}.png' for i in range(12)],
'schulterzucken':[f'schulterzucken/zucken_{i:03d}.png' for i in range(8)],
'aufrichten':[f'aufrichten/aufrichten_{i:03d}.png' for i in range(8)],
'lehnen':[f'lehnen/lehnen_{x}.png' for x in ['+00','+05','+10','+15','+20','+15','+10','+05','+00']],
'gewicht':[f'gewicht/gewicht_{x}.png' for x in ['+00','+05','+10','+15','+10','+05','+00','-05','-10','-05','+00']],
'schulterdrehung':[f'schulterdrehung/schulter_{x}.png' for x in ['+00','+05','+10','+15','+10','+05','+00','-05','-10','-05','+00']]}

def cases():
 out=[]
 for name,arr in F.items():
  pairs=sorted(set([0,max(0,(len(arr)-2)//2)]))
  for i in pairs:
   for direction in ('l1_to_l2','l2_to_l1'):
    for m in (.25,.5,.75):
     if direction=='l1_to_l2': l1,l2,o1,o2=arr[i],arr[i+1],1-m,m
     else: l1,l2,o1,o2=arr[i+1],arr[i],m,1-m
     out.append({'family':name,'pair':i,'direction':direction,'m':m,'l1':l1,'l2':l2,'o1':o1,'o2':o2})
 return out

PAGE=r'''<!doctype html><meta charset=utf-8><style>html,body{margin:0;padding:0;background:#111;overflow:hidden}.ref{position:absolute;left:0;width:120px;height:80px;background:#111;overflow:hidden}.ref img{position:absolute;inset:0;width:120px;height:80px;display:block}#gpu{position:absolute;left:130px;top:0;width:120px}</style><div id=refs></div><canvas id=gpu></canvas><script>
const CASES=__CASES__,ROW=80,W=120,H=80,TOTAL=CASES.length*ROW,refs=document.getElementById('refs'),cv=document.getElementById('gpu');cv.width=W;cv.height=TOTAL;cv.style.height=TOTAL+'px';
for(let i=0;i<CASES.length;i++){let c=CASES[i],d=document.createElement('div');d.className='ref';d.style.top=(i*ROW)+'px';let a=document.createElement('img'),b=document.createElement('img');a.src='/asset/'+c.l1;b.src='/asset/'+c.l2;a.style.opacity=String(c.o1);b.style.opacity=String(c.o2);d.append(a,b);refs.append(d)}
function load(p){return new Promise((r,j)=>{let i=new Image;i.onload=()=>r(i);i.onerror=()=>j(Error(p));i.src='/asset/'+p})}function sh(g,t,s){let x=g.createShader(t);g.shaderSource(x,s);g.compileShader(x);if(!g.getShaderParameter(x,g.COMPILE_STATUS))throw Error(g.getShaderInfoLog(x));return x}
(async()=>{const paths=[...new Set(CASES.flatMap(c=>[c.l1,c.l2]))],imgs=new Map;for(const p of paths)imgs.set(p,await load(p));await Promise.all([...document.images].map(i=>i.decode()));let g=cv.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:true,premultipliedAlpha:false});if(!g)throw Error('no webgl');let dbg=g.getExtension('WEBGL_debug_renderer_info'),renderer=dbg?g.getParameter(dbg.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER);let vs=`attribute vec2 p;varying vec2 uv;void main(){gl_Position=vec4(p*2.-1.,0.,1.);uv=vec2(p.x,1.-p.y);}`,fs=`precision highp float;varying vec2 uv;uniform sampler2D a,b;uniform float o1,o2;void main(){vec4 A=texture2D(a,uv),B=texture2D(b,uv);vec4 Ap=vec4(A.rgb*A.a*o1,A.a*o1),Bp=vec4(B.rgb*B.a*o2,B.a*o2);vec4 P=Bp+Ap*(1.-Bp.a);gl_FragColor=P.a>0.?vec4(P.rgb/P.a,P.a):vec4(0.);}`;let pr=g.createProgram();g.attachShader(pr,sh(g,g.VERTEX_SHADER,vs));g.attachShader(pr,sh(g,g.FRAGMENT_SHADER,fs));g.linkProgram(pr);if(!g.getProgramParameter(pr,g.LINK_STATUS))throw Error(g.getProgramInfoLog(pr));g.useProgram(pr);let vb=g.createBuffer();g.bindBuffer(g.ARRAY_BUFFER,vb);g.bufferData(g.ARRAY_BUFFER,new Float32Array([0,0,1,0,0,1,0,1,1,0,1,1]),g.STATIC_DRAW);let ap=g.getAttribLocation(pr,'p');g.enableVertexAttribArray(ap);g.vertexAttribPointer(ap,2,g.FLOAT,false,0,0);g.uniform1i(g.getUniformLocation(pr,'a'),0);g.uniform1i(g.getUniformLocation(pr,'b'),1);let u1=g.getUniformLocation(pr,'o1'),u2=g.getUniformLocation(pr,'o2'),textures=new Map;for(const p of paths){let t=g.createTexture();g.bindTexture(g.TEXTURE_2D,t);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MIN_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MAG_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_S,g.CLAMP_TO_EDGE);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_T,g.CLAMP_TO_EDGE);g.pixelStorei(g.UNPACK_FLIP_Y_WEBGL,1);g.texImage2D(g.TEXTURE_2D,0,g.RGBA,g.RGBA,g.UNSIGNED_BYTE,imgs.get(p));textures.set(p,t)}
for(let i=0;i<CASES.length;i++){let c=CASES[i];g.viewport(0,TOTAL-(i+1)*ROW,W,H);g.activeTexture(g.TEXTURE0);g.bindTexture(g.TEXTURE_2D,textures.get(c.l1));g.activeTexture(g.TEXTURE1);g.bindTexture(g.TEXTURE_2D,textures.get(c.l2));g.uniform1f(u1,c.o1);g.uniform1f(u2,c.o2);g.drawArrays(g.TRIANGLES,0,6)}g.finish();document.title='READY:'+renderer;document.body.dataset.ready='1'})().catch(e=>{document.title='ERROR:'+e;document.body.dataset.error=String(e)})</script>'''

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--budget-ms',type=int,default=7000);a=ap.parse_args();root=pathlib.Path(a.visual_root).resolve();cs=cases();height=len(cs)*80
 missing=[p for arr in F.values() for p in arr if not (root/'koerper_rgba'/p).is_file()]
 if missing:print(json.dumps({'error':'missing','files':missing}));return 3
 with tempfile.TemporaryDirectory(prefix='dom-webgl-crossfade-') as td:
  td=pathlib.Path(td);page=PAGE.replace('__CASES__',json.dumps(cs));(td/'index.html').write_text(page)
  class H(BaseHTTPRequestHandler):
   def log_message(self,*x):pass
   def do_GET(self):
    u=urlparse(self.path).path
    if u in ('/','/index.html'):p=td/'index.html';ctype='text/html'
    elif u.startswith('/asset/'):
     rel=pathlib.PurePosixPath(unquote(u[7:]));
     if '..' in rel.parts:self.send_response(403);self.end_headers();return
     p=root/'koerper_rgba'/pathlib.Path(*rel.parts);ctype='image/png'
    else:self.send_response(404);self.end_headers();return
    if not p.is_file():self.send_response(404);self.end_headers();return
    b=p.read_bytes();self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  srv=ThreadingHTTPServer(('127.0.0.1',0),H);threading.Thread(target=srv.serve_forever,daemon=True).start();shot=td/'shot.png';url=f'http://127.0.0.1:{srv.server_address[1]}/';cmd=[a.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run','--force-device-scale-factor=1',f'--window-size=250,{height}',f'--virtual-time-budget={a.budget_ms}',f'--screenshot={shot}',url];p=subprocess.run(cmd,capture_output=True,text=True,timeout=40);srv.shutdown()
  if p.returncode!=0 or not shot.is_file():print(json.dumps({'error':'chrome','returncode':p.returncode,'stderr':p.stderr[-1500:]}));return 2
  im=np.asarray(Image.open(shot).convert('RGB'));rows=[]
  for i,c in enumerate(cs):
   y=i*80;A=im[y:y+80,0:120].astype(np.int16);B=im[y:y+80,130:250].astype(np.int16);d=np.abs(A-B);pm=d.max(axis=2);rows.append({**c,'rgb_mae':float(d.mean()),'rgb_p99':float(np.percentile(d,99)),'rgb_max':int(d.max()),'changed_px_ge3':int((pm>=3).sum()),'changed_px_ge8':int((pm>=8).sum()),'changed_frac_ge3':float((pm>=3).mean())})
  by={}
  for name in F:
   rr=[x for x in rows if x['family']==name];by[name]={'tests':len(rr),'max_rgb_mae':max(x['rgb_mae'] for x in rr),'max_rgb_p99':max(x['rgb_p99'] for x in rr),'max_changed_frac_ge3':max(x['changed_frac_ge3'] for x in rr),'max_changed_px_ge8':max(x['changed_px_ge8'] for x in rr)}
  out={'schema':'BODY_DOM_WEBGL_CROSSFADE_SCREENSHOT/v1','renderer_path':'Chrome screenshot; DOM img opacity vs one WebGL atlas; original 1536x1024 textures','cases':len(cs),'viewport':[250,height],'families':by,'global':{'max_rgb_mae':max(x['rgb_mae'] for x in rows),'max_rgb_p99':max(x['rgb_p99'] for x in rows),'max_changed_frac_ge3':max(x['changed_frac_ge3'] for x in rows),'max_changed_px_ge8':max(x['changed_px_ge8'] for x in rows)},'live_mutation':False,'chrome_returncode':p.returncode}
  print(json.dumps(out,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
