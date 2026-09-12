#!/usr/bin/env python3
"""Whole-scene BASE vs hidden residual-body shadow load A/B.

The live file is never modified. A temporary HTTP server serves the exact live
buehne.html twice: BASE plus measurement injection, then SHADOW plus the same
measurement injection and an additional off-DOM WebGL body compositor called
from the page's existing requestAnimationFrame loop immediately after
koerperSchritt(t). The original body remains visible in SHADOW, so this measures
conservative additive cost instead of replacing existing rendering.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, statistics, subprocess, tempfile, threading, time, urllib.request
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

MEASURE = r'''<script>
(()=>{let n=0;setInterval(()=>{n++;fetch('/api/test_fps',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({n,fps:window.__buehneFps||0,t:performance.now(),shadow_ready:window.__bodyMicroShadowReady||0,shadow_draws:window.__bodyMicroShadowDraws||0,heap:(performance.memory&&performance.memory.usedJSHeapSize)||0})}).catch(()=>{})},1000)})();
</script>'''

SHADOW = r'''<script>
(()=>{
window.__bodyMicroShadowReady=0;window.__bodyMicroShadowDraws=0;
function _sh(p){let x=this.createShader(p[0]);this.shaderSource(x,p[1]);this.compileShader(x);if(!this.getShaderParameter(x,this.COMPILE_STATUS))throw Error(this.getShaderInfoLog(x));return x}
async function initBodyMicroShadow(){
 const t0=performance.now();
 const paths=[...new Set([...(typeof ATMEN_BILDER!=='undefined'?ATMEN_BILDER:[]),...(typeof KOERPER_AKTIONEN!=='undefined'?KOERPER_AKTIONEN.flatMap(a=>a.bilder):[])])];
 const W=620,H=414,SW=1536,SH=1024,cv=document.createElement('canvas');cv.width=W;cv.height=H;
 const gl=cv.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:false,premultipliedAlpha:false});if(!gl)throw Error('no shadow webgl');
 const dbg=gl.getExtension('WEBGL_debug_renderer_info');
 const VS=`precision highp float;const float SW=1536.0,SH=1024.0;attribute vec2 p;uniform float shoulderScale,t;varying vec2 uv;float G(vec2 q,vec2 c,vec2 z){vec2 d=(q-c)/z;return exp(-.5*dot(d,d));}void main(){vec2 q=p;float bw=1306.,bh=519.,x0=117.,y0=505.;float b=sin(6.2831853*t/4.9),l=sin(6.2831853*t/8.7+.83),r=sin(6.2831853*t/11.3+2.14);float ld=shoulderScale*(-.46*b+.12*l),rd=shoulderScale*(-.42*b+.09*r),lr=radians(shoulderScale*(.085*l+.025*b)),rr=radians(shoulderScale*(-.070*r-.018*b));float lx=x0+.27*bw,rx=x0+.73*bw,sy=y0+.19*bh;float wl=G(q,vec2(lx,sy),vec2(.18*bw,.115*bh)),wr=G(q,vec2(rx,sy),vec2(.18*bw,.115*bh));float c0=y0+.38*bh,c1=y0+.62*bh,lo=q.y<=c0?1.:(q.y>=c1?0.:.5+.5*cos(3.14159265*(q.y-c0)/(c1-c0)));wl*=lo;wr*=lo;float dx=wl*(-lr*(q.y-sy))+wr*(-rr*(q.y-sy)),dy=wl*(ld+lr*(q.x-lx))+wr*(rd+rr*(q.x-rx));vec2 d=max(max(vec2(561.,505.)-q,q-vec2(977.,618.)),vec2(0.));float mv=clamp(length(d)/36.,0.,1.);q+=vec2(dx,dy)*mv;gl_Position=vec4(q.x/SW*2.-1.,1.-q.y/SH*2.,0,1);uv=p/vec2(SW,SH);}`;
 const FS=`precision mediump float;varying vec2 uv;uniform sampler2D a,b;void main(){vec4 A=texture2D(a,uv),B=texture2D(b,uv);vec4 Ap=vec4(A.rgb*A.a,A.a),Bp=vec4(B.rgb*B.a,B.a);vec4 P=Bp+Ap*(1.-Bp.a);gl_FragColor=P.a>0.?vec4(P.rgb/P.a,P.a):vec4(0.);}`;
 let pr=gl.createProgram(),v=_sh.call(gl,[gl.VERTEX_SHADER,VS]),f=_sh.call(gl,[gl.FRAGMENT_SHADER,FS]);gl.attachShader(pr,v);gl.attachShader(pr,f);gl.linkProgram(pr);if(!gl.getProgramParameter(pr,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(pr));gl.useProgram(pr);
 function coords(M,st,e){let a=[];for(let x=0;x<=M;x+=st)a.push(Math.min(M,x));a.push(M,...e);return [...new Set(a)].sort((a,b)=>a-b)}let xs=coords(SW,96,[117,561,978,1423]),ys=coords(SH,64,[505,619]),verts=[],ix=[];for(let y of ys)for(let x of xs)verts.push(x,y);let nx=xs.length;for(let y=0;y<ys.length-1;y++)for(let x=0;x<xs.length-1;x++){let A=y*nx+x,B=A+1,C=A+nx,D=C+1;ix.push(A,C,B,B,C,D)}
 let vb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(verts),gl.STATIC_DRAW);let al=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(al);gl.vertexAttribPointer(al,2,gl.FLOAT,false,0,0);let ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(ix),gl.STATIC_DRAW);let us=gl.getUniformLocation(pr,'shoulderScale'),ut=gl.getUniformLocation(pr,'t');gl.uniform1i(gl.getUniformLocation(pr,'a'),0);gl.uniform1i(gl.getUniformLocation(pr,'b'),1);gl.viewport(0,0,W,H);
 const resize=document.createElement('canvas');resize.width=W;resize.height=H;const rc=resize.getContext('2d',{alpha:true}),textures=new Map();
 async function image(p){let im=new Image();im.src=p;await im.decode();return im}
 for(const p of paths){let im=await image(p);rc.clearRect(0,0,W,H);rc.drawImage(im,0,0,W,H);let x=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,x);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,resize);textures.set(new URL(p,location.href).pathname,x)}gl.flush();
 let last=[null,null];function bind(unit,p){if(!textures.has(p))return false;if(last[unit]===p)return true;gl.activeTexture(gl.TEXTURE0+unit);gl.bindTexture(gl.TEXTURE_2D,textures.get(p));last[unit]=p;return true}
 window.__bodyMicroShadowStep=function(ms){let p1=new URL(document.getElementById('koerper-schicht').src,location.href).pathname,p2=new URL(document.getElementById('koerper-schicht2').src,location.href).pathname;if(!bind(0,p1)||!bind(1,p2))return;gl.uniform1f(us,4.0);gl.uniform1f(ut,ms/1000);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawElements(gl.TRIANGLES,ix.length,gl.UNSIGNED_SHORT,0);gl.flush();window.__bodyMicroShadowDraws++};
 window.__bodyMicroShadowReady=performance.now();
 fetch('/api/shadow_meta',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({renderer:dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),version:gl.getParameter(gl.VERSION),textures:textures.size,estimated_gpu_rgba_bytes:textures.size*W*H*4,vertices:verts.length/2,triangles:ix.length/3,prewarm_ms:performance.now()-t0,gl_error:gl.getError()})}).catch(()=>{});
}
setTimeout(()=>initBodyMicroShadow().catch(e=>fetch('/api/shadow_meta',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({error:String(e),stack:e.stack})}).catch(()=>{})),500);
})();
</script>'''


def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def inject(html:str,shadow:bool)->str:
    marker='  koerperSchritt(t);\n'
    if shadow:
        if html.count(marker)!=1: raise RuntimeError(f'koerperSchritt marker count={html.count(marker)}')
        html=html.replace(marker,marker+'  if(window.__bodyMicroShadowStep) window.__bodyMicroShadowStep(t);\n')
    payload=(SHADOW if shadow else '')+MEASURE
    if '</body>' in html:return html.replace('</body>',payload+'</body>',1)
    return html+payload

class State:
    mode='base'; t0=0.0; samples=[]; meta=None

def summarize(samples,mode):
    valid=[x for x in samples if x.get('fps',0)>0]
    if mode=='shadow': valid=[x for x in valid if x.get('shadow_ready',0)>0 and x.get('shadow_draws',0)>30]
    valid=valid[2:] if len(valid)>4 else valid
    fps=[float(x['fps']) for x in valid]
    heaps=[int(x.get('heap',0)) for x in valid if x.get('heap',0)]
    return {'samples':len(fps),'fps_mean':statistics.mean(fps) if fps else None,'fps_median':statistics.median(fps) if fps else None,'fps_min':min(fps) if fps else None,'fps_max':max(fps) if fps else None,'heap_max':max(heaps) if heaps else None,'last_shadow_draws':max((int(x.get('shadow_draws',0)) for x in valid),default=0)}

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--duration',type=float,default=15);a=ap.parse_args();root=pathlib.Path(a.visual_root).resolve();live=(root/'buehne.html').read_bytes();html=live.decode(errors='replace');pages={'base':inject(html,False).encode(),'shadow':inject(html,True).encode()}
    class H(BaseHTTPRequestHandler):
        def log_message(self,*x):pass
        def _json(self,obj,status=200):
            b=json.dumps(obj).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
        def do_GET(self):
            u=urlparse(self.path).path
            if u in ('/','/index.html'):
                b=pages[State.mode];self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
            if u=='/api/status':
                try:
                    with urllib.request.urlopen('http://127.0.0.1:8000/api/status',timeout=2) as r:b=r.read();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
                except Exception:self._json({'buehne':{'broadcast_value':1.0,'ueberraschung':0.0},'zuschauer':0})
                return
            rel=pathlib.PurePosixPath(unquote(u.lstrip('/')))
            if '..' in rel.parts:self.send_response(403);self.end_headers();return
            p=(root/pathlib.Path(*rel.parts)).resolve()
            if root not in p.parents and p!=root:self.send_response(403);self.end_headers();return
            if not p.is_file():self.send_response(404);self.end_headers();return
            b=p.read_bytes();ctype='application/javascript' if p.suffix=='.js' else ('image/png' if p.suffix=='.png' else ('image/jpeg' if p.suffix.lower() in ('.jpg','.jpeg') else 'application/octet-stream'));self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
        def do_POST(self):
            u=urlparse(self.path).path;n=int(self.headers.get('Content-Length','0'));b=self.rfile.read(n)
            if u=='/api/test_fps':
                try:x=json.loads(b);x['_server_elapsed']=time.monotonic()-State.t0;State.samples.append(x)
                except Exception:pass
                self.send_response(204);self.end_headers();return
            if u=='/api/shadow_meta':
                try:State.meta=json.loads(b)
                except Exception:State.meta={'decode_error':True}
                self.send_response(204);self.end_headers();return
            if u=='/api/fps':self.send_response(204);self.end_headers();return
            self.send_response(204);self.end_headers()
    srv=ThreadingHTTPServer(('127.0.0.1',0),H);threading.Thread(target=srv.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{srv.server_address[1]}/';runs={}
    for mode in ('base','shadow'):
        State.mode=mode;State.samples=[];State.meta=None;State.t0=time.monotonic();p=subprocess.Popen([a.chrome,'--headless=new','--no-sandbox','--use-gl=angle','--disable-background-networking','--no-first-run','--window-size=620,414',f'--user-data-dir={tempfile.mkdtemp(prefix="body-fullscene-chrome-")}',url],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True);time.sleep(a.duration)
        try:p.terminate();err=p.communicate(timeout=5)[1]
        except Exception:p.kill();err=p.communicate()[1]
        runs[mode]={'summary':summarize(State.samples,mode),'samples':State.samples,'meta':State.meta,'stderr_tail':err[-1000:]}
    srv.shutdown();r={'schema':'BODY_FULLSCENE_SHADOW_AB/v1','live_html_sha256':sha(live),'base_html_sha256':sha(pages['base']),'shadow_html_sha256':sha(pages['shadow']),'duration_s':a.duration,'runs':runs,'live_mutation':False};print(json.dumps(r,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
