#!/usr/bin/env python3
"""Scratch-only interior-residual parallax falsifier.

Keeps the exact live head alpha and baseline RGB.  Depth slices only contribute
an additive *difference* between shifted and zero-offset premultiplied colour,
gated away from semi-transparent silhouette pixels.  This tests whether useful
sub-pixel depth motion can be made visible without silhouette holes or the blur
introduced by normalized fixed-alpha reconstruction.

No production files are modified.
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
COEFF = [1.0, 1/3, -1/3, -1.0]
AMPS = [0.75, 1.0, 1.25, 1.5, 2.0]
VARIANTS = {
    # (alpha start, alpha full, residual gain)
    'soft75': (0.75, 0.97, 1.0),
    'soft85': (0.85, 0.985, 1.0),
    'soft85_g075': (0.85, 0.985, 0.75),
}


def smoothstep(e0: float, e1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - e0) / max(e1 - e0, 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def warp(arr: np.ndarray, dx: float) -> np.ndarray:
    h, w = arr.shape[:2]
    M = np.float32([[1, 0, dx], [0, 1, 0]])
    border = 0 if arr.ndim == 2 else (0, 0, 0)
    return cv2.warpAffine(arr, M, (w, h), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=border)


def gray(rgb: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(np.clip(rgb,0,255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)


def edge_energy(g: np.ndarray, mask: np.ndarray) -> float:
    lap = np.abs(cv2.Laplacian(g, cv2.CV_32F))
    return float(lap[mask].mean()) if np.any(mask) else 0.0


def phase_shift(a: np.ndarray, b: np.ndarray, cx: float, cy: float) -> tuple[float,float,float]:
    x0=max(0,int(round(cx-110))); x1=min(a.shape[1],int(round(cx+110)))
    y0=max(0,int(round(cy-70))); y1=min(a.shape[0],int(round(cy+70)))
    ra=a[y0:y1,x0:x1]; rb=b[y0:y1,x0:x1]
    if ra.shape[0]<20 or ra.shape[1]<20: return 0.0,0.0,0.0
    (sx,sy),resp=cv2.phaseCorrelate(ra,rb)
    return float(sx),float(sy),float(resp)


def build(base: np.ndarray, slices: list[np.ndarray], amp: float,
          e0: float, e1: float, gain: float) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    a0 = base[:,:,3].astype(np.float32)/255.0
    # Premultiplied colour fields are additive because the source slices form
    # an exact alpha partition of the live image at zero offset.
    p_zero=np.zeros(base.shape[:2]+(3,),np.float32)
    p_shift=np.zeros_like(p_zero)
    for s,k in zip(slices,COEFF):
        af=s[:,:,3].astype(np.float32)/255.0
        p=s[:,:,:3].astype(np.float32)*af[:,:,None]
        p_zero += p
        p_shift += warp(p,k*amp)
    residual=p_shift-p_zero
    interior=smoothstep(e0,e1,a0)
    # Also fade residual where local alpha gradient is large.  This freezes
    # silhouette/hair-edge geometry while retaining fully opaque facial detail.
    gx=cv2.Sobel(a0,cv2.CV_32F,1,0,ksize=3)
    gy=cv2.Sobel(a0,cv2.CV_32F,0,1,ksize=3)
    grad=np.sqrt(gx*gx+gy*gy)
    edge_guard=1.0-smoothstep(0.02,0.15,grad)
    w=(interior*edge_guard*gain).astype(np.float32)
    rgb=base[:,:,:3].astype(np.float32)+residual*w[:,:,None]/np.maximum(a0[:,:,None],0.92)
    out=np.dstack([np.clip(rgb,0,255),base[:,:,3].astype(np.float32)])
    return out,w,residual


def metric_row(base: np.ndarray,out: np.ndarray,w: np.ndarray,residual: np.ndarray,
               anchor: tuple[float,float], scale: float) -> dict:
    a=base[:,:,3]
    opaque=a>=245
    core=(a>=245)&(w>0.5)
    g0=gray(base[:,:,:3]); g1=gray(out[:,:,:3])
    diff=np.abs(out[:,:,:3]-base[:,:,:3].astype(np.float32))
    sx,sy,resp=phase_shift(g0,g1,*anchor)
    clip=((out[:,:,:3]<=0.001)|(out[:,:,:3]>=254.999))&core[:,:,None]
    return {
        'alpha_exact': bool(np.array_equal(base[:,:,3],np.clip(out[:,:,3],0,255).astype(np.uint8))),
        'core_fraction': float(core.mean()),
        'changed_fraction_core': float((np.max(diff,axis=2)[core]>0.5).mean()) if np.any(core) else 0.0,
        'rgb_mae_core': float(diff[core].mean()) if np.any(core) else 0.0,
        'rgb_p99_core': float(np.quantile(diff[core],0.99)) if np.any(core) else 0.0,
        'rgb_max_core': float(diff[core].max()) if np.any(core) else 0.0,
        'lap_ratio_opaque': (edge_energy(g1,opaque)+1e-9)/(edge_energy(g0,opaque)+1e-9),
        'lap_ratio_core': (edge_energy(g1,core)+1e-9)/(edge_energy(g0,core)+1e-9),
        'eye_shift_src': float(math.hypot(sx,sy)),
        'eye_shift_css': float(math.hypot(sx,sy)*scale),
        'eye_phase_resp': resp,
        'clip_fraction_core_channels': float(clip.mean()) if np.any(core) else 0.0,
        'residual_abs_p99_core': float(np.quantile(np.abs(residual[core]),0.99)) if np.any(core) else 0.0,
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual')
    ap.add_argument('--scale',type=float,default=0.4036458333333333)
    args=ap.parse_args()
    root=Path(args.visual_root)
    anchors=json.loads((root/'rig2/augen_anker_exakt.json').read_text())
    a0=np.array([anchors['augen_anker_roll0']['x'],anchors['augen_anker_roll0']['y']],float)
    results={}
    for v,(e0,e1,gain) in VARIANTS.items():
        results[v]={}
        for amp in AMPS:
            rows=[]
            for r in ROLLS:
                base=np.array(Image.open(root/f'kopf_rgba/roll/gier_+00_nick_+00_roll_{r}.png').convert('RGBA'),dtype=np.uint8)
                d=root/f'kopf_rgba_parallax/gier_+00_nick_+00_roll_{r}'
                slices=[np.array(Image.open(next(d.glob(f'slice_{i}_*.png'))).convert('RGBA'),dtype=np.uint8) for i in range(4)]
                off=anchors['werte'][str(int(r))]
                anchor=tuple(a0+np.array([off['dx_px'],off['dy_px']],float))
                out,w,res=build(base,slices,amp,e0,e1,gain)
                rows.append(metric_row(base,out,w,res,anchor,args.scale))
            results[v][str(amp)]={
                'css_max_layer_shift': amp*args.scale,
                'all_alpha_exact': all(x['alpha_exact'] for x in rows),
                'core_fraction_min': min(x['core_fraction'] for x in rows),
                'changed_fraction_core_min': min(x['changed_fraction_core'] for x in rows),
                'rgb_mae_core_max': max(x['rgb_mae_core'] for x in rows),
                'rgb_p99_core_max': max(x['rgb_p99_core'] for x in rows),
                'lap_ratio_opaque_range': [min(x['lap_ratio_opaque'] for x in rows),max(x['lap_ratio_opaque'] for x in rows)],
                'lap_ratio_core_range': [min(x['lap_ratio_core'] for x in rows),max(x['lap_ratio_core'] for x in rows)],
                'eye_shift_css_max': max(x['eye_shift_css'] for x in rows),
                'eye_shift_src_max': max(x['eye_shift_src'] for x in rows),
                'eye_phase_resp_min': min(x['eye_phase_resp'] for x in rows),
                'clip_fraction_core_channels_max': max(x['clip_fraction_core_channels'] for x in rows),
                'residual_abs_p99_core_max': max(x['residual_abs_p99_core'] for x in rows),
            }
    print('PARALLAX_INTERIOR_RESIDUAL_GATE/v1')
    for v in VARIANTS:
        for amp in map(str,AMPS):
            print('VARIANT',v,'AMP',amp,json.dumps(results[v][amp],sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
