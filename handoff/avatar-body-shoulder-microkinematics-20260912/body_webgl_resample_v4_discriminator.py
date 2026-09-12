#!/usr/bin/env python3
"""Robust per-case discriminator for final Canvas2D/WebGL residual.

Each real body-family case gets independent 620x414 canvases, avoiding the old
stacked-viewport confounder. Compare Canvas2D source-over against WebGL with:
  RAW: original 1536x1024 <img> textures sampled down by GL.LINEAR
  PRE: each source first resized to 620x414 by Canvas2D, then sampled 1:1 by GL
Correct upload Y orientation (UNPACK_FLIP_Y_WEBGL=1 + uv=p). Read-only.
"""
from __future__ import annotations
import argparse,json,pathlib,subprocess,tempfile,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,unquote
from PIL import Image
import numpy as np
W,H=620,414
F={'atmen':['atmen__atmen_000.png','atmen__atmen_001.png'],'schulterzucken':['schulterzucken/zucken_000.png','schulterzucken/zucken_001.png'],'aufrichten':['aufrichten/aufrichten_000.png','aufrichten/aufrichten_001.png'],'lehnen':['lehnen/lehnen_+00.png','lehnen/lehnen_+05.png'],'gewicht':['gewicht/gewicht_+00.png','gewicht/gewicht_+05.png'],'schulterdrehung':['schulterdrehung/schulter_+00.png','schulterdrehung/schulter_+05.png']}
CASES=[{'family':k,'a':v[0],'b':v[1]} for k,v in F.items()]
PAGE=r'''<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:#111;overflow:hidden}.cell{position:absolute;width:620px;height:414px;background:#111;overflow:hidden}.cell canvas{display:block;width:620px;height:414px}</style><div id=root></div><script>
const C=__CASES__,W=620,H=414,R=document.getElementById('root');function load(p){return new Promise((r,j)=>{let x=new Image;x.onload=()=>r(x);x.onerror=()=>j(Error(p));x.src='/asset/'+p})}function cell(x,y){let d=document.createElement('div');d.className='cell';d.style.left=x+'px';d.style.top=y+'px';let c=document.createElement('canvas');c.width=W;c.height=H;d.append(c);R.append(d);return c}function sh(g,t,s){let x=g.createShader(t);g.shaderSource(x,s);g.compileShader(x);if(!g.getShaderParameter(x,g.COMPILE_STATUS))throw Error(g.getShaderInfoLog(x));return x}
function glDraw(cv,A,B,pre){let g=cv.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:true,premultipliedAlpha:false});let vs=`attribute vec2 p;varying vec2 uv;void main(){gl_Position=vec4(p*2.-1.,0.,1.);uv=p;}`,fs=`precision highp float;varying vec2 uv;uniform sampler2D a,b;void main(){vec4 A=texture2D(a,uv),B=texture2D(b,uv);vec4 Ap=vec4(A.rgb*A.a*.5,A.a*.5),Bp=vec4(B.rgb*B.a*.5,B.a*.5);vec4 P=Bp+Ap*(1.-Bp.a);gl_FragColor=P.a>0.?vec4(P.rgb/P.a,P.a):vec4(0.);}`;let pr=g.createProgram();g.attachShader(pr,sh(g,g.VERTEX_SHADER,vs));g.attachShader(pr,sh(g,g.FRAGMENT_SHADER,fs));g.linkProgram(pr);g.useProgram(pr);let vb=g.createBuffer();g.bindBuffer(g.ARRAY_BUFFER,vb);g.bufferData(g.ARRAY_BUFFER,new Float32Array([0,0,1,0,0,1,0,1,1,0,1,1]),g.STATIC_DRAW);let p=g.getAttribLocation(pr,'p');g.enableVertexAttribArray(p);g.vertexAttribPointer(p,2,g.FLOAT,false,0,0);function src(img){if(!pre)return img;let c=document.createElement('canvas');c.width=W;c.height=H;c.getContext('2d',{alpha:true}).drawImage(img,0,0,W,H);return c}function tex(unit,img){let t=g.createTexture();g.activeTexture(g.TEXTURE0+unit);g.bindTexture(g.TEXTURE_2D,t);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MIN_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MAG_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_S,g.CLAMP_TO_EDGE);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_T,g.CLAMP_TO_EDGE);g.pixelStorei(g.UNPACK_FLIP_Y_WEBGL,1);g.texImage2D(g.TEXTURE_2D,0,g.RGBA,g.RGBA,g.UNSIGNED_BYTE,src(img))}tex(0,A);tex(1,B);g.uniform1i(g.getUniformLocation(pr,'a'),0);g.uniform1i(g.getUniformLocation(pr,'b'),1);g.viewport(0,0,W,H);g.drawArrays(g.TRIANGLES,0,6);g.finish()}
(async()=>{let paths=[...new Set(C.flatMap(c=>[c.a,c.b]))],I=new Map;for(const p of paths)I.set(p,await load(p));for(let i=0;i<C.length;i++){let o=C[i],y=i*H,c2=cell(0,y),raw=cell(630,y),pre=cell(1260,y),x=c2.getContext('2d',{alpha:true});x.globalAlpha=.5;x.drawImage(I.get(o.a),0,0,W,H);x.globalAlpha=.5;x.drawImage(I.get(o.b),0,0,W,H);glDraw(raw,I.get(o.a),I.get(o.b),false);glDraw(pre,I.get(o.a),I.get(o.b),true)}await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));document.title='READY'})().catch(e=>document.title='ERROR:'+e)</script>'''
def met(a,b):
 d=np.abs(a.astype(np.int16)-b.astype(np.int16));pm=d.max(axis=2);return {'mae':float(d.mean()),'p99':float(np.percentile(d,99)),'max':int(d.max()),'changed_frac_ge3':float((pm>=3).mean()),'changed_px_ge8':int((pm>=8).sum())}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--budget-ms',type=int,default=7000);q=ap.parse_args();body=(pathlib.Path(q.visual_root).resolve()/'koerper_rgba')
 with tempfile.TemporaryDirectory(prefix='body-resample-v4-') as td:
  td=pathlib.Path(td);(td/'index.html').write_text(PAGE.replace('__CASES__',json.dumps(CASES)))
  class S(BaseHTTPRequestHandler):
   def log_message(self,*x):pass
   def do_GET(self):
    u=urlparse(self.path).path
    if u in ('/','/index.html'):p=td/'index.html';ct='text/html'
    elif u.startswith('/asset/'):
     rel=pathlib.PurePosixPath(unquote(u[7:]));p=body/pathlib.Path(*rel.parts);ct='image/png'
    else:self.send_response(404);self.end_headers();return
    if not p.is_file():self.send_response(404);self.end_headers();return
    z=p.read_bytes();self.send_response(200);self.send_header('Content-Type',ct);self.send_header('Content-Length',str(len(z)));self.end_headers();self.wfile.write(z)
  srv=ThreadingHTTPServer(('127.0.0.1',0),S);threading.Thread(target=srv.serve_forever,daemon=True).start();shot=td/'s.png';p=subprocess.run([q.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run','--force-device-scale-factor=1',f'--window-size=1880,{len(CASES)*H}',f'--virtual-time-budget={q.budget_ms}',f'--screenshot={shot}',f'http://127.0.0.1:{srv.server_address[1]}/'],capture_output=True,text=True,timeout=40);srv.shutdown()
  if p.returncode or not shot.is_file():print(json.dumps({'error':'chrome','stderr':p.stderr[-1000:]}));return 2
  im=np.asarray(Image.open(shot).convert('RGB'));rows=[]
  for i,o in enumerate(CASES):
   y=i*H;c2=im[y:y+H,0:W];raw=im[y:y+H,630:1250];pre=im[y:y+H,1260:1880];rows.append({'family':o['family'],'c2_raw':met(c2,raw),'c2_pre':met(c2,pre),'raw_pre':met(raw,pre)})
  agg={}
  for k in ['c2_raw','c2_pre','raw_pre']:
   rr=[r[k] for r in rows];agg[k]={'max_mae':max(x['mae'] for x in rr),'max_p99':max(x['p99'] for x in rr),'max_changed_frac_ge3':max(x['changed_frac_ge3'] for x in rr),'max_changed_px_ge8':max(x['changed_px_ge8'] for x in rr)}
  print(json.dumps({'schema':'BODY_WEBGL_RESAMPLE_V4/v1','aggregate':agg,'rows':rows,'live_mutation':False},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
