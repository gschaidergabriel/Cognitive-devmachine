#!/usr/bin/env python3
"""Real-browser compositor discriminator for the remaining DOM/WebGL mismatch.

At production body geometry (620x414), compare the same 50/50 body transition
for each family across four screenshot paths:
  DOM          real two-<img> CSS opacity source-over reference
  Canvas2D     drawImage + globalAlpha source-over
  GL_STRAIGHT  WebGL context premultipliedAlpha=false, straight-alpha output
  GL_PREMUL    WebGL context premultipliedAlpha=true, premultiplied output

If DOM ~= Canvas2D and GL_PREMUL beats GL_STRAIGHT, the mismatch is the WebGL
canvas premultiplication/compositor contract, not body assets, animation, or
sampling. Scratch/read-only only; live avatar source is never modified.
"""
from __future__ import annotations
import argparse, json, pathlib, subprocess, tempfile, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote
from PIL import Image
import numpy as np

W,H=620,414
F={
'atmen':['atmen__atmen_000.png','atmen__atmen_001.png'],
'schulterzucken':['schulterzucken/zucken_000.png','schulterzucken/zucken_001.png'],
'aufrichten':['aufrichten/aufrichten_000.png','aufrichten/aufrichten_001.png'],
'lehnen':['lehnen/lehnen_+00.png','lehnen/lehnen_+05.png'],
'gewicht':['gewicht/gewicht_+00.png','gewicht/gewicht_+05.png'],
'schulterdrehung':['schulterdrehung/schulter_+00.png','schulterdrehung/schulter_+05.png'],
}
CASES=[{'family':k,'l1':v[0],'l2':v[1]} for k,v in F.items()]

PAGE=r'''<!doctype html><meta charset=utf-8><style>
html,body{margin:0;padding:0;background:#111;overflow:hidden}.ref{position:absolute;left:0;width:620px;height:414px;background:#111;overflow:hidden}.ref img{position:absolute;inset:0;width:620px;height:414px;display:block}canvas{position:absolute;top:0;width:620px}#c2{left:630px}#gs{left:1260px}#gp{left:1890px}
</style><div id=refs></div><canvas id=c2></canvas><canvas id=gs></canvas><canvas id=gp></canvas><script>
const CASES=__CASES__,W=620,H=414,ROW=414,TOTAL=CASES.length*ROW,refs=document.getElementById('refs'),c2=document.getElementById('c2'),gs=document.getElementById('gs'),gp=document.getElementById('gp');for(const c of [c2,gs,gp]){c.width=W;c.height=TOTAL;c.style.height=TOTAL+'px'}
for(let i=0;i<CASES.length;i++){let c=CASES[i],d=document.createElement('div');d.className='ref';d.style.top=(i*ROW)+'px';let a=document.createElement('img'),b=document.createElement('img');a.src='/asset/'+c.l1;b.src='/asset/'+c.l2;a.style.opacity='.5';b.style.opacity='.5';d.append(a,b);refs.append(d)}
function load(p){return new Promise((r,j)=>{let i=new Image;i.onload=()=>r(i);i.onerror=()=>j(Error(p));i.src='/asset/'+p})}
function sh(g,t,s){let x=g.createShader(t);g.shaderSource(x,s);g.compileShader(x);if(!g.getShaderParameter(x,g.COMPILE_STATUS))throw Error(g.getShaderInfoLog(x));return x}
function setup(cv,premul,outPremul){let g=cv.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:true,premultipliedAlpha:premul});if(!g)throw Error('no webgl');let vs=`attribute vec2 p;varying vec2 uv;void main(){gl_Position=vec4(p*2.-1.,0.,1.);uv=p;}`;let tail=outPremul?'gl_FragColor=P;':'gl_FragColor=P.a>0.?vec4(P.rgb/P.a,P.a):vec4(0.);';let fs=`precision highp float;varying vec2 uv;uniform sampler2D a,b;void main(){vec4 A=texture2D(a,uv),B=texture2D(b,uv);vec4 Ap=vec4(A.rgb*A.a*.5,A.a*.5),Bp=vec4(B.rgb*B.a*.5,B.a*.5);vec4 P=Bp+Ap*(1.-Bp.a);${tail}}`;let pr=g.createProgram();g.attachShader(pr,sh(g,g.VERTEX_SHADER,vs));g.attachShader(pr,sh(g,g.FRAGMENT_SHADER,fs));g.linkProgram(pr);if(!g.getProgramParameter(pr,g.LINK_STATUS))throw Error(g.getProgramInfoLog(pr));g.useProgram(pr);let vb=g.createBuffer();g.bindBuffer(g.ARRAY_BUFFER,vb);g.bufferData(g.ARRAY_BUFFER,new Float32Array([0,0,1,0,0,1,0,1,1,0,1,1]),g.STATIC_DRAW);let ap=g.getAttribLocation(pr,'p');g.enableVertexAttribArray(ap);g.vertexAttribPointer(ap,2,g.FLOAT,false,0,0);g.uniform1i(g.getUniformLocation(pr,'a'),0);g.uniform1i(g.getUniformLocation(pr,'b'),1);return g}
function tex(g,img){let t=g.createTexture();g.bindTexture(g.TEXTURE_2D,t);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MIN_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MAG_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_S,g.CLAMP_TO_EDGE);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_T,g.CLAMP_TO_EDGE);g.pixelStorei(g.UNPACK_FLIP_Y_WEBGL,1);g.texImage2D(g.TEXTURE_2D,0,g.RGBA,g.RGBA,g.UNSIGNED_BYTE,img);return t}
(async()=>{const paths=[...new Set(CASES.flatMap(c=>[c.l1,c.l2]))],imgs=new Map;for(const p of paths)imgs.set(p,await load(p));await Promise.all([...document.images].map(i=>i.decode()));let x=c2.getContext('2d',{alpha:true}),gS=setup(gs,false,false),gP=setup(gp,true,true);
function gd(g,i,c){let a=tex(g,imgs.get(c.l1)),b=tex(g,imgs.get(c.l2));g.viewport(0,TOTAL-(i+1)*ROW,W,H);g.activeTexture(g.TEXTURE0);g.bindTexture(g.TEXTURE_2D,a);g.activeTexture(g.TEXTURE1);g.bindTexture(g.TEXTURE_2D,b);g.drawArrays(g.TRIANGLES,0,6);g.deleteTexture(a);g.deleteTexture(b)}
for(let i=0;i<CASES.length;i++){let c=CASES[i];x.save();x.translate(0,i*ROW);x.globalCompositeOperation='source-over';x.globalAlpha=.5;x.drawImage(imgs.get(c.l1),0,0,W,H);x.globalAlpha=.5;x.drawImage(imgs.get(c.l2),0,0,W,H);x.restore();gd(gS,i,c);gd(gP,i,c)}gS.finish();gP.finish();document.title='READY';document.body.dataset.ready='1'})().catch(e=>{document.title='ERROR:'+e;document.body.dataset.error=String(e)})
</script>'''

def met(a,b):
 d=np.abs(a.astype(np.int16)-b.astype(np.int16));pm=d.max(axis=2)
 return {'rgb_mae':float(d.mean()),'rgb_p99':float(np.percentile(d,99)),'rgb_max':int(d.max()),'changed_frac_ge3':float((pm>=3).mean()),'changed_px_ge8':int((pm>=8).sum())}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--budget-ms',type=int,default=7000);a=ap.parse_args();root=pathlib.Path(a.visual_root).resolve();body=root/'koerper_rgba';missing=[p for v in F.values() for p in v if not (body/p).is_file()]
 if missing:print(json.dumps({'error':'missing','files':missing}));return 3
 with tempfile.TemporaryDirectory(prefix='dom-webgl-premul-') as td:
  td=pathlib.Path(td);(td/'index.html').write_text(PAGE.replace('__CASES__',json.dumps(CASES)))
  class Hdl(BaseHTTPRequestHandler):
   def log_message(self,*x):pass
   def do_GET(self):
    u=urlparse(self.path).path
    if u in ('/','/index.html'):p=td/'index.html';ctype='text/html'
    elif u.startswith('/asset/'):
     rel=pathlib.PurePosixPath(unquote(u[7:]));
     if '..' in rel.parts:self.send_response(403);self.end_headers();return
     p=body/pathlib.Path(*rel.parts);ctype='image/png'
    else:self.send_response(404);self.end_headers();return
    if not p.is_file():self.send_response(404);self.end_headers();return
    b=p.read_bytes();self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  srv=ThreadingHTTPServer(('127.0.0.1',0),Hdl);threading.Thread(target=srv.serve_forever,daemon=True).start();shot=td/'shot.png';url=f'http://127.0.0.1:{srv.server_address[1]}/';cmd=[a.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run','--force-device-scale-factor=1',f'--window-size=2510,{len(CASES)*H}',f'--virtual-time-budget={a.budget_ms}',f'--screenshot={shot}',url];p=subprocess.run(cmd,capture_output=True,text=True,timeout=40);srv.shutdown()
  if p.returncode or not shot.is_file():print(json.dumps({'error':'chrome','returncode':p.returncode,'stderr':p.stderr[-1200:]}));return 2
  im=np.asarray(Image.open(shot).convert('RGB'));rows=[]
  for i,c in enumerate(CASES):
   y=i*H;dom=im[y:y+H,0:W];c2=im[y:y+H,630:1250];gs=im[y:y+H,1260:1880];gp=im[y:y+H,1890:2510];rows.append({'family':c['family'],'dom_canvas2d':met(dom,c2),'dom_gl_straight':met(dom,gs),'dom_gl_premul':met(dom,gp),'canvas2d_gl_straight':met(c2,gs),'canvas2d_gl_premul':met(c2,gp)})
  keys=['dom_canvas2d','dom_gl_straight','dom_gl_premul','canvas2d_gl_straight','canvas2d_gl_premul'];agg={}
  for k in keys:
   rr=[x[k] for x in rows];agg[k]={'max_rgb_mae':max(x['rgb_mae'] for x in rr),'max_rgb_p99':max(x['rgb_p99'] for x in rr),'max_changed_frac_ge3':max(x['changed_frac_ge3'] for x in rr),'max_changed_px_ge8':max(x['changed_px_ge8'] for x in rr)}
  print(json.dumps({'schema':'BODY_DOM_WEBGL_PREMULTIPLY_DISCRIMINATOR/v1','geometry':[W,H],'cases':len(rows),'aggregate':agg,'rows':rows,'live_mutation':False},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
