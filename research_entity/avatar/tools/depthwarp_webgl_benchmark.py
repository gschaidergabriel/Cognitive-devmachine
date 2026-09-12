#!/usr/bin/env python3
"""Build and run a scratch WebGL benchmark for the guarded single-texture depth warp.

This is deliberately production-shaped but read-only:
- original live head PNG is the only colour texture;
- a precomputed signed R8 control map encodes depth * alpha-edge guard * eye guard;
- fragment shader samples one control texel plus base colour at original + warped UV;
- output alpha always comes from the unwarped base sample;
- no live HTML/assets/services are modified.

The generated HTML is meant to be executed with Chrome/ANGLE on the real AMD GPU.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import tempfile

import cv2
import numpy as np
from PIL import Image

COEFF=np.array([1.0,1/3,-1/3,-1.0],np.float32)


def smoothstep(e0,e1,x):
    t=np.clip((x-e0)/max(e1-e0,1e-9),0,1)
    return t*t*(3-2*t)


def control_map(root:Path, roll:str, eye:tuple[float,float], rx=220., ry=125.):
    base=np.array(Image.open(root/f'kopf_rgba/roll/gier_+00_nick_+00_roll_{roll}.png').convert('RGBA'),np.uint8)
    d=root/f'kopf_rgba_parallax/gier_+00_nick_+00_roll_{roll}'
    slices=[np.array(Image.open(next(d.glob(f'slice_{i}_*.png'))).convert('RGBA'),np.uint8) for i in range(4)]
    aa=np.stack([s[:,:,3].astype(np.float32)/255 for s in slices],axis=0)
    den=np.maximum(aa.sum(axis=0),1e-6)
    depth=(aa*COEFF[:,None,None]).sum(axis=0)/den
    depth[den<.02]=0
    depth=cv2.GaussianBlur(depth,(0,0),1.0,borderType=cv2.BORDER_REPLICATE)
    a=base[:,:,3].astype(np.float32)/255
    opaque=smoothstep(.70,.97,a)
    gx=cv2.Sobel(a,cv2.CV_32F,1,0,ksize=3); gy=cv2.Sobel(a,cv2.CV_32F,0,1,ksize=3)
    grad=np.sqrt(gx*gx+gy*gy); edge=1-smoothstep(.015,.10,grad)
    yy,xx=np.mgrid[0:a.shape[0],0:a.shape[1]].astype(np.float32)
    ell=((xx-eye[0])/rx)**2+((yy-eye[1])/ry)**2
    eye_allow=smoothstep(1.0,1.55,ell)
    ctrl=np.clip(depth*opaque*edge*eye_allow,-1,1)
    # Signed R8: zero is exactly integer 128. Decode in shader as (byte-128)/127.
    enc=np.clip(np.rint(ctrl*127+128),1,255).astype(np.uint8)
    return base,enc,ctrl


def html_text(base_uri:str, ctrl_uri:str, widths:list[tuple[int,int]], source_w:int, source_h:int):
    return r'''<!doctype html><meta charset=utf-8><body><pre id=o>boot</pre><script>
const OUT=document.getElementById('o');
const CASES=__CASES__; const SW=__SW__, SH=__SH__;
function load(u){return new Promise((res,rej)=>{let i=new Image();i.onload=()=>res(i);i.onerror=()=>rej(Error('load '+u));i.src=u})}
function shader(gl,t,s){let x=gl.createShader(t);gl.shaderSource(x,s);gl.compileShader(x);if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(x));return x}
function program(gl){let p=gl.createProgram();gl.attachShader(p,shader(gl,gl.VERTEX_SHADER,'attribute vec2 p;varying vec2 uv;void main(){uv=p*.5+.5;gl_Position=vec4(p,0.,1.);}'));gl.attachShader(p,shader(gl,gl.FRAGMENT_SHADER,'precision highp float;varying vec2 uv;uniform sampler2D b;uniform sampler2D c;uniform float amp;uniform float sw;void main(){vec4 q=texture2D(b,uv);float by=texture2D(c,uv).r*255.0;float ctrl=(by-128.0)/127.0;vec2 u=uv-vec2((amp/sw)*ctrl,0.0);vec4 w=texture2D(b,u);gl_FragColor=vec4(w.rgb,q.a);}'));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));return p}
function tex(gl,img,linear=true){let t=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,t);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,linear?gl.LINEAR:gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,linear?gl.LINEAR:gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,img);return t}
(async()=>{
 let [bi,ci]=await Promise.all([load(__BASE__),load(__CTRL__)]); let results=[];
 for(const cs of CASES){
  let cv=document.createElement('canvas');cv.width=cs[0];cv.height=cs[1];let gl=cv.getContext('webgl',{alpha:true,antialias:false,depth:false,stencil:false,preserveDrawingBuffer:false});if(!gl)throw Error('no webgl');
  const dbg=gl.getExtension('WEBGL_debug_renderer_info'); const renderer=dbg?gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);
  let p=program(gl);gl.useProgram(p);let buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);let loc=gl.getAttribLocation(p,'p');gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);
  let bt=tex(gl,bi,true), ct=tex(gl,ci,true);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,bt);gl.uniform1i(gl.getUniformLocation(p,'b'),0);gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,ct);gl.uniform1i(gl.getUniformLocation(p,'c'),1);gl.uniform1f(gl.getUniformLocation(p,'sw'),SW);let al=gl.getUniformLocation(p,'amp');gl.viewport(0,0,cv.width,cv.height);
  // warm-up
  for(let i=0;i<120;i++){gl.uniform1f(al,1.0+0.25*Math.sin(i*.071));gl.drawArrays(gl.TRIANGLE_STRIP,0,4)} gl.finish();
  let reps=[]; for(let k=0;k<7;k++){let t0=performance.now();for(let i=0;i<600;i++){gl.uniform1f(al,1.0+0.25*Math.sin((i+k*600)*.071));gl.drawArrays(gl.TRIANGLE_STRIP,0,4)}gl.finish();let dt=performance.now()-t0;reps.push(dt/600)}
  reps.sort((a,b)=>a-b); results.push({size:cs,renderer,ms_per_frame_median:reps[3],ms_per_frame_min:reps[0],ms_per_frame_max:reps[6],fps_equivalent:1000/reps[3],gl_error:gl.getError()});
 }
 OUT.textContent='RESULT_JSON '+JSON.stringify({schema:'DEPTHWARP_WEBGL_BENCH/v1',source:[SW,SH],cases:results});
})().catch(e=>OUT.textContent='ERROR '+e.stack)
</script>'''.replace('__CASES__',json.dumps(widths)).replace('__SW__',str(source_w)).replace('__SH__',str(source_h)).replace('__BASE__',json.dumps(base_uri)).replace('__CTRL__',json.dumps(ctrl_uri))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual')
    ap.add_argument('--roll',default='+00')
    ap.add_argument('--out-dir',required=True)
    args=ap.parse_args(); root=Path(args.visual_root).resolve(); out=Path(args.out_dir).resolve(); out.mkdir(parents=True,exist_ok=True)
    anchors=json.loads((root/'rig2/augen_anker_exakt.json').read_text()); a0=np.array([anchors['augen_anker_roll0']['x'],anchors['augen_anker_roll0']['y']],float); off=anchors['werte'][str(int(args.roll))]; eye=tuple(a0+np.array([off['dx_px'],off['dy_px']],float))
    base,enc,ctrl=control_map(root,args.roll,eye)
    ctrl_rgba=np.dstack([enc,enc,enc,np.full(enc.shape,255,np.uint8)])
    cp=out/'control.png'; Image.fromarray(ctrl_rgba,'RGBA').save(cp,optimize=True)
    bp=(root/f'kopf_rgba/roll/gier_+00_nick_+00_roll_{args.roll}.png').resolve()
    hp=out/'bench.html'; hp.write_text(html_text(bp.as_uri(),cp.as_uri(),[(620,414),(746,449),(1536,1024)],base.shape[1],base.shape[0]))
    print('BENCH_HTML',hp)
    print('CONTROL_PNG',cp,'bytes',cp.stat().st_size,'ctrl_min',float(ctrl.min()),'ctrl_max',float(ctrl.max()),'eye',eye)
    return 0
if __name__=='__main__': raise SystemExit(main())
