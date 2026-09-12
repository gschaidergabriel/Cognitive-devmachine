#!/usr/bin/env python3
"""Scratch-only single-texture depth-warp gate for the live avatar head.

Goal: test a representation that cannot create slice-separation holes.
The exact live head image remains the only colour source and the authoritative
alpha/silhouette.  The four accepted parallax slice alpha fields are used only
to infer a continuous signed depth coefficient.  Each output pixel performs one
bilinear lookup into the original head texture.

Identity constraints:
- output alpha is byte-identical to the live source;
- displacement fades to zero at alpha/silhouette edges;
- displacement fades to zero around the exact per-roll eye anchor, because the
  live gaze/blink overlays must retain their existing registration authority;
- no production file is modified.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROLLS = ['-25','-20','-15','-10','-05','+00','+05','+10','+15','+20','+25']
COEFF = np.array([1.0, 1/3, -1/3, -1.0], dtype=np.float32)
AMPS = [0.75, 1.0, 1.25, 1.5, 2.0, 2.5]
VARIANTS = {
    # eye protection ellipse radii in source pixels; edge gradient cutoff
    'eye180x105': (180.0, 105.0, 0.10),
    'eye220x125': (220.0, 125.0, 0.10),
}


def smoothstep(e0: float, e1: float, x: np.ndarray) -> np.ndarray:
    t=np.clip((x-e0)/max(e1-e0,1e-9),0.0,1.0)
    return t*t*(3.0-2.0*t)


def depth_field(slices: list[np.ndarray]) -> np.ndarray:
    aa=np.stack([s[:,:,3].astype(np.float32)/255.0 for s in slices],axis=0)
    denom=np.maximum(aa.sum(axis=0),1e-6)
    d=(aa*COEFF[:,None,None]).sum(axis=0)/denom
    d[denom<0.02]=0.0
    # one gentle spatial regularization of the *control field*, not the RGB.
    # This avoids discontinuous UV derivatives without touching image detail.
    d=cv2.GaussianBlur(d,(0,0),sigmaX=1.0,sigmaY=1.0,borderType=cv2.BORDER_REPLICATE)
    return d.astype(np.float32)


def guards(alpha: np.ndarray, eye: tuple[float,float], rx: float, ry: float, grad_end: float) -> np.ndarray:
    a=alpha.astype(np.float32)/255.0
    opaque=smoothstep(0.70,0.97,a)
    gx=cv2.Sobel(a,cv2.CV_32F,1,0,ksize=3); gy=cv2.Sobel(a,cv2.CV_32F,0,1,ksize=3)
    grad=np.sqrt(gx*gx+gy*gy)
    edge=1.0-smoothstep(0.015,grad_end,grad)
    yy,xx=np.mgrid[0:a.shape[0],0:a.shape[1]].astype(np.float32)
    ex=((xx-eye[0])/rx)**2+((yy-eye[1])/ry)**2
    # zero at/inside eye ellipse, smooth return from ellipse radius 1 to 1.55
    eye_allow=smoothstep(1.0,1.55,ex)
    return np.clip(opaque*edge*eye_allow,0.0,1.0).astype(np.float32)


def warp_once(base: np.ndarray, depth: np.ndarray, gate: np.ndarray, amp: float) -> tuple[np.ndarray,np.ndarray]:
    h,w=depth.shape
    yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
    dx=(amp*depth*gate).astype(np.float32)
    # inverse map: positive depth samples from the left, so perceived content moves right.
    mapx=xx-dx; mapy=yy
    rgb=cv2.remap(base[:,:,:3],mapx,mapy,interpolation=cv2.INTER_LINEAR,
                  borderMode=cv2.BORDER_REFLECT_101)
    out=np.dstack([rgb,base[:,:,3]])
    return out,dx


def gray(rgb: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(rgb.astype(np.uint8),cv2.COLOR_RGB2GRAY).astype(np.float32)


def lap_energy(g: np.ndarray,mask: np.ndarray) -> float:
    v=np.abs(cv2.Laplacian(g,cv2.CV_32F))
    return float(v[mask].mean()) if np.any(mask) else 0.0


def phase(a: np.ndarray,b: np.ndarray,cx: float,cy: float,rx=115,ry=75):
    x0=max(0,int(round(cx-rx))); x1=min(a.shape[1],int(round(cx+rx)))
    y0=max(0,int(round(cy-ry))); y1=min(a.shape[0],int(round(cy+ry)))
    ra=a[y0:y1,x0:x1]; rb=b[y0:y1,x0:x1]
    if min(ra.shape)<20:return 0.0,0.0,0.0
    (sx,sy),resp=cv2.phaseCorrelate(ra,rb)
    return float(sx),float(sy),float(resp)


def metrics(base,out,dx,depth,gate,eye,scale):
    a=base[:,:,3]; opaque=a>=245
    g0=gray(base[:,:,:3]); g1=gray(out[:,:,:3])
    diff=np.abs(out[:,:,:3].astype(np.float32)-base[:,:,:3].astype(np.float32))
    sx,sy,resp=phase(g0,g1,*eye)
    # Local mapping x' = x + dx(x); fold risk if derivative <= 0.
    deriv=1.0+cv2.Sobel(dx,cv2.CV_32F,1,0,ksize=3)/8.0
    active=gate>0.05
    eye_y0=max(0,int(eye[1]-75)); eye_y1=min(a.shape[0],int(eye[1]+75))
    eye_x0=max(0,int(eye[0]-115)); eye_x1=min(a.shape[1],int(eye[0]+115))
    eye_diff=diff[eye_y0:eye_y1,eye_x0:eye_x1]
    return {
        'alpha_exact':bool(np.array_equal(base[:,:,3],out[:,:,3])),
        'active_fraction':float(active.mean()),
        'max_abs_shift_src':float(np.max(np.abs(dx))),
        'max_abs_shift_css':float(np.max(np.abs(dx))*scale),
        'p95_abs_shift_css':float(np.quantile(np.abs(dx[active]),.95)*scale) if np.any(active) else 0.0,
        'min_mapping_derivative':float(deriv[active].min()) if np.any(active) else 1.0,
        'rgb_mae_opaque':float(diff[opaque].mean()) if np.any(opaque) else 0.0,
        'rgb_p99_opaque':float(np.quantile(diff[opaque],.99)) if np.any(opaque) else 0.0,
        'lap_ratio_opaque':(lap_energy(g1,opaque)+1e-9)/(lap_energy(g0,opaque)+1e-9),
        'eye_shift_src':float(math.hypot(sx,sy)),
        'eye_shift_css':float(math.hypot(sx,sy)*scale),
        'eye_phase_resp':resp,
        'eye_rgb_mae':float(eye_diff.mean()),
        'depth_min':float(depth[opaque].min()) if np.any(opaque) else 0.0,
        'depth_max':float(depth[opaque].max()) if np.any(opaque) else 0.0,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual')
    ap.add_argument('--scale',type=float,default=0.4036458333333333)
    args=ap.parse_args(); root=Path(args.visual_root)
    anchors=json.loads((root/'rig2/augen_anker_exakt.json').read_text())
    a0=np.array([anchors['augen_anker_roll0']['x'],anchors['augen_anker_roll0']['y']],float)
    print('PARALLAX_SINGLE_TEXTURE_DEPTHWARP_GATE/v1')
    for v,(rx,ry,grad_end) in VARIANTS.items():
        by_amp={str(a):[] for a in AMPS}
        for r in ROLLS:
            base=np.array(Image.open(root/f'kopf_rgba/roll/gier_+00_nick_+00_roll_{r}.png').convert('RGBA'),dtype=np.uint8)
            ddir=root/f'kopf_rgba_parallax/gier_+00_nick_+00_roll_{r}'
            slices=[np.array(Image.open(next(ddir.glob(f'slice_{i}_*.png'))).convert('RGBA'),dtype=np.uint8) for i in range(4)]
            off=anchors['werte'][str(int(r))]; eye=tuple(a0+np.array([off['dx_px'],off['dy_px']],float))
            depth=depth_field(slices); gate=guards(base[:,:,3],eye,rx,ry,grad_end)
            for amp in AMPS:
                out,dx=warp_once(base,depth,gate,amp)
                by_amp[str(amp)].append(metrics(base,out,dx,depth,gate,eye,args.scale))
        for amp in AMPS:
            rows=by_amp[str(amp)]
            summary={
                'all_alpha_exact':all(x['alpha_exact'] for x in rows),
                'active_fraction_min':min(x['active_fraction'] for x in rows),
                'max_abs_shift_css':max(x['max_abs_shift_css'] for x in rows),
                'p95_abs_shift_css_max':max(x['p95_abs_shift_css'] for x in rows),
                'min_mapping_derivative':min(x['min_mapping_derivative'] for x in rows),
                'rgb_mae_opaque_max':max(x['rgb_mae_opaque'] for x in rows),
                'rgb_p99_opaque_max':max(x['rgb_p99_opaque'] for x in rows),
                'lap_ratio_opaque_range':[min(x['lap_ratio_opaque'] for x in rows),max(x['lap_ratio_opaque'] for x in rows)],
                'eye_shift_css_max':max(x['eye_shift_css'] for x in rows),
                'eye_shift_src_max':max(x['eye_shift_src'] for x in rows),
                'eye_rgb_mae_max':max(x['eye_rgb_mae'] for x in rows),
                'eye_phase_resp_min':min(x['eye_phase_resp'] for x in rows),
                'depth_range':[min(x['depth_min'] for x in rows),max(x['depth_max'] for x in rows)],
            }
            print('VARIANT',v,'AMP',amp,json.dumps(summary,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
