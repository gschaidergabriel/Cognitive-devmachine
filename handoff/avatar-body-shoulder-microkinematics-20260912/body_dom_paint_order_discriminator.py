#!/usr/bin/env python3
"""Determine whether the remaining DOM-vs-GPU body delta is paint ordering.

At 620x414 for six real body families compare:
  DOM_AB      A then B, auto z-order (live-style assumption)
  DOM_AB_Z    A z=1, B z=2 (explicit B-over-A)
  DOM_BA_Z    B z=1, A z=2 (explicit A-over-B)
  C2_AB       Canvas2D A then B
  C2_BA       Canvas2D B then A
All layers use opacity/globalAlpha=.5. Read-only scratch evidence only.
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
PAGE=r'''<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:#111;overflow:hidden}.col{position:absolute;top:0;width:620px}.ref{position:absolute;width:620px;height:414px;background:#111;overflow:hidden}.ref img{position:absolute;inset:0;width:620px;height:414px;display:block;opacity:.5}canvas{position:absolute;top:0;width:620px}</style><div id=ab class=col style="left:0"></div><div id=abz class=col style="left:630px"></div><div id=baz class=col style="left:1260px"></div><canvas id=cab style="left:1890px"></canvas><canvas id=cba style="left:2520px"></canvas><script>
const C=__CASES__,W=620,H=414,T=C.length*H;for(const id of ['cab','cba']){let c=document.getElementById(id);c.width=W;c.height=T;c.style.height=T+'px'}
function mk(parent,i,c,mode){let d=document.createElement('div');d.className='ref';d.style.top=(i*H)+'px';let a=document.createElement('img'),b=document.createElement('img');a.src='/asset/'+c.a;b.src='/asset/'+c.b;if(mode==='abz'){a.style.zIndex='1';b.style.zIndex='2'}if(mode==='baz'){a.style.zIndex='2';b.style.zIndex='1'}d.append(a,b);parent.append(d)}for(let i=0;i<C.length;i++){mk(ab,i,C[i],'ab');mk(abz,i,C[i],'abz');mk(baz,i,C[i],'baz')}
function load(p){return new Promise((r,j)=>{let x=new Image;x.onload=()=>r(x);x.onerror=()=>j(Error(p));x.src='/asset/'+p})}
(async()=>{let paths=[...new Set(C.flatMap(c=>[c.a,c.b]))],im=new Map;for(const p of paths)im.set(p,await load(p));await Promise.all([...document.images].map(x=>x.decode()));function draw(id,rev){let x=document.getElementById(id).getContext('2d',{alpha:true});for(let i=0;i<C.length;i++){let c=C[i],p=rev?[c.b,c.a]:[c.a,c.b];x.save();x.translate(0,i*H);x.globalAlpha=.5;x.drawImage(im.get(p[0]),0,0,W,H);x.globalAlpha=.5;x.drawImage(im.get(p[1]),0,0,W,H);x.restore()}}draw('cab',false);draw('cba',true);document.title='READY'})().catch(e=>document.title='ERROR:'+e)</script>'''
def met(a,b):
 d=np.abs(a.astype(np.int16)-b.astype(np.int16));pm=d.max(axis=2);return {'mae':float(d.mean()),'p99':float(np.percentile(d,99)),'max':int(d.max()),'changed_frac_ge3':float((pm>=3).mean())}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--budget-ms',type=int,default=7000);q=ap.parse_args();root=pathlib.Path(q.visual_root).resolve();body=root/'koerper_rgba';missing=[p for v in F.values() for p in v if not (body/p).is_file()]
 if missing:print(json.dumps({'error':'missing','files':missing}));return 3
 with tempfile.TemporaryDirectory(prefix='dom-order-') as td:
  td=pathlib.Path(td);(td/'index.html').write_text(PAGE.replace('__CASES__',json.dumps(CASES)))
  class S(BaseHTTPRequestHandler):
   def log_message(self,*x):pass
   def do_GET(self):
    u=urlparse(self.path).path
    if u in ('/','/index.html'):p=td/'index.html';ct='text/html'
    elif u.startswith('/asset/'):
     rel=pathlib.PurePosixPath(unquote(u[7:]));
     if '..' in rel.parts:self.send_response(403);self.end_headers();return
     p=body/pathlib.Path(*rel.parts);ct='image/png'
    else:self.send_response(404);self.end_headers();return
    if not p.is_file():self.send_response(404);self.end_headers();return
    b=p.read_bytes();self.send_response(200);self.send_header('Content-Type',ct);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  srv=ThreadingHTTPServer(('127.0.0.1',0),S);threading.Thread(target=srv.serve_forever,daemon=True).start();shot=td/'s.png';url=f'http://127.0.0.1:{srv.server_address[1]}/';p=subprocess.run([q.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run','--force-device-scale-factor=1',f'--window-size=3140,{len(CASES)*H}',f'--virtual-time-budget={q.budget_ms}',f'--screenshot={shot}',url],capture_output=True,text=True,timeout=40);srv.shutdown()
  if p.returncode or not shot.is_file():print(json.dumps({'error':'chrome','returncode':p.returncode,'stderr':p.stderr[-1000:]}));return 2
  im=np.asarray(Image.open(shot).convert('RGB'));xs={'dom_ab':0,'dom_ab_z':630,'dom_ba_z':1260,'c2_ab':1890,'c2_ba':2520};pairs=[('dom_ab','c2_ab'),('dom_ab','c2_ba'),('dom_ab_z','c2_ab'),('dom_ab_z','c2_ba'),('dom_ba_z','c2_ab'),('dom_ba_z','c2_ba'),('dom_ab','dom_ab_z')];rows=[]
  for i,c in enumerate(CASES):
   y=i*H;crop={k:im[y:y+H,x:x+W] for k,x in xs.items()};r={'family':c['family']};r.update({a+'__'+b:met(crop[a],crop[b]) for a,b in pairs});rows.append(r)
  agg={}
  for a,b in pairs:
   k=a+'__'+b;rr=[r[k] for r in rows];agg[k]={'max_mae':max(x['mae'] for x in rr),'max_p99':max(x['p99'] for x in rr),'max_changed_frac_ge3':max(x['changed_frac_ge3'] for x in rr)}
  print(json.dumps({'schema':'BODY_DOM_PAINT_ORDER_DISCRIMINATOR/v1','aggregate':agg,'rows':rows,'live_mutation':False},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
