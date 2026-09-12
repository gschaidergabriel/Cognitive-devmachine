#!/usr/bin/env python3
"""Production-shaped scratch A/B for existing photographed body player + residual mesh.

Read-only with respect to the live avatar. It reuses the exact current body assets,
models the existing two-layer crossfade as two textures, applies the residual mesh
only after image selection, and measures real-wall-clock rAF cadence on real Chrome.
"""
from __future__ import annotations
import argparse, json, pathlib, subprocess, tempfile, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

SEQS = {
    'atmen': [f'atmen__atmen_{i:03d}.png' for i in range(12)],
    'schulterzucken': [f'schulterzucken/zucken_{i:03d}.png' for i in range(8)],
    'aufrichten': [f'aufrichten/aufrichten_{i:03d}.png' for i in range(8)],
    'lehnen': [f'lehnen/lehnen_{x}.png' for x in ['+00','+05','+10','+15','+20','+15','+10','+05','+00']],
    'gewicht': [f'gewicht/gewicht_{x}.png' for x in ['+00','+05','+10','+15','+10','+05','+00','-05','-10','-05','+00']],
    'schulterdrehung': [f'schulterdrehung/schulter_{x}.png' for x in ['+00','+05','+10','+15','+10','+05','+00','-05','-10','-05','+00']],
}

PAGE = r'''<!doctype html><meta charset=utf-8><canvas id=c width=620 height=414></canvas><pre id=o>running</pre><script>
const SEQS=__SEQS__, cv=document.getElementById('c'), out=document.getElementById('o');
function load(u){return new Promise((r,j)=>{let i=new Image;i.onload=()=>r(i);i.onerror=()=>j(Error(u));i.src='/asset/'+u})}
function sh(gl,t,s){let x=gl.createShader(t);gl.shaderSource(x,s);gl.compileShader(x);if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(x));return x}
function pct(a,p){let x=[...a].sort((u,v)=>u-v);return x[Math.min(x.length-1,Math.floor((x.length-1)*p))]}
function stats(a){let m=a.reduce((x,y)=>x+y,0)/a.length;return {n:a.length,mean:m,p50:pct(a,.5),p95:pct(a,.95),p99:pct(a,.99),max:Math.max(...a),over20:a.filter(x=>x>20).length,over25:a.filter(x=>x>25).length,over33:a.filter(x=>x>33).length,fps:1000/m}}
function kin(t,s){let b=Math.sin(6.2831853*t/4.9),l=Math.sin(6.2831853*t/8.7+.83),r=Math.sin(6.2831853*t/11.3+2.14);return [s*(-.46*b+.12*l),s*(-.42*b+.09*r),s*(.085*l+.025*b),s*(-.070*r-.018*b),s*(-.18*b)]}
function env(name){if(name==='schulterzucken'||name==='schulterdrehung')return [0,.10];if(name==='aufrichten'||name==='lehnen'||name==='gewicht')return [.15,.15];return [.35,.15]}
(async()=>{
 const all={};for(const [k,arr] of Object.entries(SEQS))all[k]=await Promise.all(arr.map(load));
 const gl=cv.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:true,premultipliedAlpha:false});if(!gl)throw Error('no webgl');
 const dbg=gl.getExtension('WEBGL_debug_renderer_info'),renderer=dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
 const VS=`precision highp float;const float SW=1536.0,SH=1024.0;attribute vec2 p;uniform vec2 shoulderScale;uniform float chestScale,t;varying vec2 uv;float G(vec2 q,vec2 c,vec2 z){vec2 d=(q-c)/z;return exp(-.5*dot(d,d));}void main(){vec2 q=p;float bw=1306.,bh=519.,x0=117.,y0=505.;float b=sin(6.2831853*t/4.9),l=sin(6.2831853*t/8.7+.83),r=sin(6.2831853*t/11.3+2.14);float ld=shoulderScale.x*(-.46*b+.12*l),rd=shoulderScale.y*(-.42*b+.09*r),lr=radians(shoulderScale.x*(.085*l+.025*b)),rr=radians(shoulderScale.y*(-.070*r-.018*b)),cd=chestScale*(-.18*b);float lx=x0+.27*bw,rx=x0+.73*bw,sy=y0+.19*bh;float wl=G(q,vec2(lx,sy),vec2(.18*bw,.115*bh)),wr=G(q,vec2(rx,sy),vec2(.18*bw,.115*bh)),wc=G(q,vec2(x0+.5*bw,y0+.31*bh),vec2(.25*bw,.13*bh));float c0=y0+.38*bh,c1=y0+.62*bh,lo=q.y<=c0?1.:(q.y>=c1?0.:.5+.5*cos(3.14159265*(q.y-c0)/(c1-c0)));wl*=lo;wr*=lo;wc*=lo;float dx=wl*(-lr*(q.y-sy))+wr*(-rr*(q.y-sy)),dy=wl*(ld+lr*(q.x-lx))+wr*(rd+rr*(q.x-rx))+wc*cd;vec2 d=max(max(vec2(561.,505.)-q,q-vec2(977.,618.)),vec2(0.));float mv=clamp(length(d)/36.,0.,1.);q+=vec2(dx,dy)*mv;gl_Position=vec4(q.x/SW*2.-1.,1.-q.y/SH*2.,0,1);uv=p/vec2(SW,SH);}`;
 const FS=`precision mediump float;varying vec2 uv;uniform sampler2D a,b;uniform float mixv;void main(){vec4 A=texture2D(a,uv),B=texture2D(b,uv);vec4 Ap=vec4(A.rgb*A.a,A.a),Bp=vec4(B.rgb*B.a,B.a);vec4 P=mix(Ap,Bp,mixv);gl_FragColor=P.a>0.?vec4(P.rgb/P.a,P.a):vec4(0.);}`;
 let pr=gl.createProgram();gl.attachShader(pr,sh(gl,gl.VERTEX_SHADER,VS));gl.attachShader(pr,sh(gl,gl.FRAGMENT_SHADER,FS));gl.linkProgram(pr);if(!gl.getProgramParameter(pr,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(pr));gl.useProgram(pr);
 function coords(M,st,e){let a=[];for(let x=0;x<=M;x+=st)a.push(Math.min(M,x));a.push(M,...e);return [...new Set(a)].sort((a,b)=>a-b)}let xs=coords(1536,96,[117,561,978,1423]),ys=coords(1024,64,[505,619]),v=[],ix=[];for(let y of ys)for(let x of xs)v.push(x,y);let nx=xs.length;for(let y=0;y<ys.length-1;y++)for(let x=0;x<xs.length-1;x++){let A=y*nx+x,B=A+1,C=A+nx,D=C+1;ix.push(A,C,B,B,C,D)}
 let vb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(v),gl.STATIC_DRAW);let al=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(al);gl.vertexAttribPointer(al,2,gl.FLOAT,false,0,0);let ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(ix),gl.STATIC_DRAW);
 const U={ss:gl.getUniformLocation(pr,'shoulderScale'),cs:gl.getUniformLocation(pr,'chestScale'),t:gl.getUniformLocation(pr,'t'),m:gl.getUniformLocation(pr,'mixv')};let tex=[gl.createTexture(),gl.createTexture()];tex.forEach((x,i)=>{gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,x);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE)});gl.uniform1i(gl.getUniformLocation(pr,'a'),0);gl.uniform1i(gl.getUniformLocation(pr,'b'),1);gl.viewport(0,0,620,414);gl.disable(gl.BLEND);
 function put(i,im){gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,tex[i]);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im)}
 function draw(name,i,j,m,t,warp){put(0,all[name][i]);put(1,all[name][j]);let e=env(name);gl.uniform2f(U.ss,warp?e[0]:0,warp?e[0]:0);gl.uniform1f(U.cs,warp?e[1]:0);gl.uniform1f(U.t,t);gl.uniform1f(U.m,m);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawElements(gl.TRIANGLES,ix.length,gl.UNSIGNED_SHORT,0)}
 function pix(){let p=new Uint8Array(620*414*4);gl.readPixels(0,0,620,414,gl.RGBA,gl.UNSIGNED_BYTE,p);return p}
 function metrics(A,B){let ad=0,deep=0,inter=0,uni=0,mae=0,mx=0;for(let i=0;i<620*414;i++){let p=i*4;for(let q=0;q<4;q++){let d=Math.abs(A[p+q]-B[p+q]);mae+=d;mx=Math.max(mx,d)}let a=A[p+3],b=B[p+3];ad+=Math.abs(a-b);if(a>=64&&b<32)deep++;let x=a>=16,y=b>=16;if(x&&y)inter++;if(x||y)uni++}return {rgba_mae:mae/(620*414*4),rgba_max:mx,alpha_mae:ad/(620*414),deep_hole_px:deep,jaccard:inter/Math.max(1,uni)}}
 let composition={};for(const [name,arr] of Object.entries(all)){let rows=[];for(let i=0;i<arr.length-1;i++){for(const m of [0,.5,1]){draw(name,i,i+1,m,3.675,false);gl.finish();let z=pix();draw(name,i,i+1,m,3.675,true);gl.finish();let w=pix();rows.push({i,m,...metrics(z,w)})}}composition[name]={pairs:arr.length-1,tests:rows.length,max_deep_hole_px:Math.max(...rows.map(x=>x.deep_hole_px)),min_jaccard:Math.min(...rows.map(x=>x.jaccard)),max_alpha_mae:Math.max(...rows.map(x=>x.alpha_mae)),max_rgba_mae:Math.max(...rows.map(x=>x.rgba_mae))}}
 async function cadence(warp){let names=Object.keys(all),ts=[],frame=0,namei=0,ai=0;for(let warm=0;warm<45;warm++)await new Promise(r=>requestAnimationFrame(()=>{draw(names[0],0,1,.5,warm/60,warp);r()}));for(let n=0;n<420;n++)await new Promise(r=>requestAnimationFrame(t=>{ts.push(t);let name=names[namei],arr=all[name],hold=name==='schulterzucken'?7:name==='schulterdrehung'?10:18;if(frame%hold===0){ai=(ai+1)%arr.length;if(ai===0)namei=(namei+1)%names.length}draw(name,ai,(ai+1)%arr.length,.5,n/60,warp);frame++;r()}));let d=[];for(let i=1;i<ts.length;i++)d.push(ts[i]-ts[i-1]);return stats(d)}
 let base=await cadence(false),warp=await cadence(true);let R={schema:'BODY_EXISTING_PLAYER_COMPOSITION_AB/v1',renderer,version:gl.getParameter(gl.VERSION),canvas:[620,414],vertices:v.length/2,triangles:ix.length/3,asset_families:Object.fromEntries(Object.entries(all).map(([k,v])=>[k,v.length])),composition,base,warp,gl_error:gl.getError(),live_mutation:false};out.textContent=JSON.stringify(R);await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(R)});
})().catch(async e=>{out.textContent='ERROR '+e.stack;try{await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({error:String(e),stack:e.stack})})}catch(_){}})</script>'''

class State:
    report = None
    event = threading.Event()


def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--timeout',type=float,default=70);a=ap.parse_args()
    root=pathlib.Path(a.visual_root).resolve(); body=(root/'koerper_rgba').resolve()
    missing=[x for arr in SEQS.values() for x in arr if not (body/x).is_file()]
    if missing: print(json.dumps({'status':'MISSING_ASSETS','missing':missing}));return 3
    with tempfile.TemporaryDirectory(prefix='body-player-ab-') as td:
        td=pathlib.Path(td);(td/'index.html').write_text(PAGE.replace('__SEQS__',json.dumps(SEQS)))
        class H(BaseHTTPRequestHandler):
            def log_message(self,*x): pass
            def do_GET(self):
                u=urlparse(self.path).path
                if u in ('/','/index.html'): p=td/'index.html'; c='text/html'
                elif u.startswith('/asset/'):
                    rel=pathlib.PurePosixPath(unquote(u[len('/asset/'):]))
                    if '..' in rel.parts: self.send_response(403);self.end_headers();return
                    p=body/pathlib.Path(*rel.parts);c='image/png'
                else: self.send_response(404);self.end_headers();return
                if not p.is_file(): self.send_response(404);self.end_headers();return
                b=p.read_bytes();self.send_response(200);self.send_header('Content-Type',c);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
            def do_POST(self):
                if urlparse(self.path).path!='/report': self.send_response(404);self.end_headers();return
                State.report=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))));State.event.set();self.send_response(204);self.end_headers()
        srv=ThreadingHTTPServer(('127.0.0.1',0),H);threading.Thread(target=srv.serve_forever,daemon=True).start()
        p=subprocess.Popen([a.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run',f'--user-data-dir={td/"profile"}',f'http://127.0.0.1:{srv.server_address[1]}/'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
        ok=State.event.wait(a.timeout)
        try:p.terminate();err=p.communicate(timeout=5)[1]
        except Exception:p.kill();err=p.communicate()[1]
        srv.shutdown();report=State.report if ok else {'status':'NO_REPORT','stderr_tail':err[-1600:]};print(json.dumps(report,sort_keys=True))
        if not ok or report.get('error'): return 2
        return 0

if __name__=='__main__': raise SystemExit(main())
