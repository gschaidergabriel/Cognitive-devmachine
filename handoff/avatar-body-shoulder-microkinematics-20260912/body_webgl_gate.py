#!/usr/bin/env python3
"""Real-Chrome scratch WebGL gate for independent shoulder microkinematics.

Renders the exact current body texture through one low-dimensional textured mesh.
No production file is edited.  The gate measures candidate-vs-zero WebGL image
integrity plus forced draw cost at the current observed CSS render size.
"""
from __future__ import annotations
import argparse, html as htmlmod, json, pathlib, re, subprocess, tempfile


def html(root: pathlib.Path, scale: float) -> str:
    uri=(root/'koerper_rgba/koerper_zero.png').as_uri()
    return r'''<!doctype html><meta charset=utf-8><body><canvas id=c width=620 height=414></canvas><script>
const TEX=__TEX__, SCALE=__SCALE__;
const SW=1536.0, SH=1024.0, CW=620, CH=414;
const B=[117.0,505.0,1423.0,1024.0], N=[561.0,505.0,978.0,619.0];
const cvs=document.getElementById('c'), gl=cvs.getContext('webgl',{alpha:true,antialias:false,preserveDrawingBuffer:true,premultipliedAlpha:false});
if(!gl) throw Error('no webgl');
function shader(type,src){let s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
const vs=shader(gl.VERTEX_SHADER,`precision highp float;
attribute vec2 a_src; uniform float u_ldy,u_rdy,u_lr,u_rr,u_cdy; varying vec2 v_uv;
float G(vec2 p,vec2 c,vec2 s){vec2 q=(p-c)/s;return exp(-0.5*dot(q,q));}
void main(){vec2 p=a_src; float bw=${1423-117}.0,bh=${1024-505}.0; float x0=117.0,y0=505.0;
 float lcx=x0+.27*bw, rcx=x0+.73*bw, scy=y0+.19*bh;
 float wl=G(p,vec2(lcx,scy),vec2(.18*bw,.115*bh));
 float wr=G(p,vec2(rcx,scy),vec2(.18*bw,.115*bh));
 float wc=G(p,vec2(x0+.5*bw,y0+.31*bh),vec2(.25*bw,.13*bh));
 float c0=y0+.38*bh,c1=y0+.62*bh; float low=p.y<=c0?1.0:(p.y>=c1?0.0:.5+.5*cos(3.14159265*(p.y-c0)/(c1-c0)));
 wl*=low;wr*=low;wc*=low;
 float lr=radians(u_lr),rr=radians(u_rr);
 float dx=wl*(-lr*(p.y-scy))+wr*(-rr*(p.y-scy));
 float dy=wl*(u_ldy+lr*(p.x-lcx))+wr*(u_rdy+rr*(p.x-rcx))+wc*u_cdy;
 vec2 dlo=max(max(vec2(561.0,505.0)-p,p-vec2(977.0,618.0)),vec2(0.0)); float move=clamp(length(dlo)/36.0,0.0,1.0); dx*=move;dy*=move;
 vec2 q=p+vec2(dx,dy); vec2 ndc=vec2(q.x/SW*2.0-1.0,1.0-q.y/SH*2.0); gl_Position=vec4(ndc,0,1); v_uv=vec2(p.x/SW,p.y/SH);
}`);
const fs=shader(gl.FRAGMENT_SHADER,`precision mediump float;varying vec2 v_uv;uniform sampler2D u_tex;void main(){gl_FragColor=texture2D(u_tex,v_uv);}`);
let pr=gl.createProgram();gl.attachShader(pr,vs);gl.attachShader(pr,fs);gl.linkProgram(pr);if(!gl.getProgramParameter(pr,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(pr));gl.useProgram(pr);
function coords(max,step,extra){let a=[];for(let x=0;x<=max;x+=step)a.push(Math.min(max,x));a.push(max,...extra);return [...new Set(a.map(x=>+x.toFixed(4)))].sort((a,b)=>a-b)}
let xs=coords(1536,96,[117,561,978,1423]),ys=coords(1024,64,[505,619]);let verts=[],inds=[];
for(let y of ys)for(let x of xs)verts.push(x,y);let nx=xs.length;
for(let j=0;j<ys.length-1;j++)for(let i=0;i<xs.length-1;i++){let a=j*nx+i,b=a+1,c=a+nx,d=c+1;inds.push(a,c,b,b,c,d)}
let vb=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,vb);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(verts),gl.STATIC_DRAW);let loc=gl.getAttribLocation(pr,'a_src');gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);
let ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(inds),gl.STATIC_DRAW);
let U={};for(let n of ['u_ldy','u_rdy','u_lr','u_rr','u_cdy'])U[n]=gl.getUniformLocation(pr,n);
function K(t,s=1){let b=Math.sin(2*Math.PI*t/4.9),l=Math.sin(2*Math.PI*t/8.7+.83),r=Math.sin(2*Math.PI*t/11.3+2.14);return {u_ldy:s*(-.46*b+.12*l),u_rdy:s*(-.42*b+.09*r),u_lr:s*(.085*l+.025*b),u_rr:s*(-.070*r-.018*b),u_cdy:s*(-.18*b)}}
function draw(k){for(let n in U)gl.uniform1f(U[n],k[n]||0);gl.viewport(0,0,CW,CH);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.drawElements(gl.TRIANGLES,inds.length,gl.UNSIGNED_SHORT,0)}
function pix(){let p=new Uint8Array(CW*CH*4);gl.readPixels(0,0,CW,CH,gl.RGBA,gl.UNSIGNED_BYTE,p);return p}
function metrics(a,b){let mae=0,ad=0,deep=0,inter=0,uni=0,max=0;for(let i=0;i<CW*CH;i++){let p=i*4;for(let q=0;q<4;q++){let d=Math.abs(a[p+q]-b[p+q]);mae+=d;if(d>max)max=d}let aa=a[p+3],bb=b[p+3],d=Math.abs(aa-bb);ad+=d;if(aa>=64&&bb<32)deep++;let A=aa>=16,Bb=bb>=16;if(A&&Bb)inter++;if(A||Bb)uni++;}return {rgba_mae:mae/(CW*CH*4),rgba_max:max,alpha_mae:ad/(CW*CH),deep_hole_px:deep,jaccard:inter/Math.max(1,uni)}}
function neckDelta(a,b){let x0=Math.floor(561/SW*CW),x1=Math.ceil(978/SW*CW),yt=Math.floor(505/SH*CH),yb=Math.ceil(619/SH*CH),mx=0,mae=0,n=0;/* readPixels bottom-up */for(let y=CH-yb;y<CH-yt;y++)for(let x=x0;x<x1;x++){let p=(y*CW+x)*4;for(let q=0;q<4;q++){let d=Math.abs(a[p+q]-b[p+q]);mx=Math.max(mx,d);mae+=d;n++}}return {max_delta:mx,mae:mae/Math.max(1,n),box:[x0,yt,x1,yb]}}
let im=new Image();im.onload=()=>{let tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tex);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,0);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im);
 gl.disable(gl.BLEND);draw(K(0,0));gl.finish();let z=pix();draw(K(3.675,1));gl.finish();let v=pix();let m=metrics(z,v),n=neckDelta(z,v);
 let loops=900,t0=performance.now();for(let i=0;i<loops;i++){draw(K(i/60,1));gl.finish()}let ms=(performance.now()-t0)/loops;
 let out={schema:'BODY_WEBGL_GATE/v1',canvas:[CW,CH],source:[SW,SH],source_to_css:SCALE,grid:[xs.length,ys.length],vertices:verts.length/2,triangles:inds.length/3,peak_t:3.675,metrics:m,neck:n,forced_finish_ms_per_frame:ms,forced_finish_fps_equiv:1000/ms,scope:'SCRATCH_REAL_CHROME_NO_LIVE_MUTATION'};document.body.innerText='RESULT_JSON '+JSON.stringify(out)
};im.onerror=()=>{document.body.innerText='ERROR image'};im.src=TEX;
</script>'''.replace('__TEX__',json.dumps(uri)).replace('__SCALE__',repr(scale))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--chrome',default='/usr/bin/google-chrome');ap.add_argument('--scale',type=float,default=.4036458333333333);a=ap.parse_args()
    root=pathlib.Path(a.visual_root).resolve()
    with tempfile.TemporaryDirectory(prefix='body-webgl-') as td:
      p=pathlib.Path(td)/'gate.html';p.write_text(html(root,a.scale))
      r=subprocess.run([a.chrome,'--headless=new','--no-sandbox','--allow-file-access-from-files','--use-gl=angle','--virtual-time-budget=120000','--dump-dom',p.as_uri()],capture_output=True,text=True,timeout=190)
      m=re.search(r'RESULT_JSON (\{.*?\})</body>',r.stdout,re.S)
      if not m:
        print(json.dumps({'status':'ERROR','rc':r.returncode,'stdout_tail':r.stdout[-1500:],'stderr_tail':r.stderr[-1500:]},sort_keys=True));return 2
      d=json.loads(htmlmod.unescape(m.group(1)));print(json.dumps(d,sort_keys=True));print('CHROME_RC',r.returncode);return 0
if __name__=='__main__': raise SystemExit(main())
