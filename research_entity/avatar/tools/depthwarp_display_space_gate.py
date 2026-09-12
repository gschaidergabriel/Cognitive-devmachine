#!/usr/bin/env python3
"""Display-space quality/signal gate for the guarded single-texture depth warp.

The source-space candidate is rendered exactly as in the accepted scratch gate,
then baseline and candidate are downsampled to the measured live head-canvas
pixel footprint (default 620x414 at DPR1).  This answers two separate questions:
1) does the warp's signal survive final display resampling?
2) does final display detail/eye identity remain bounded?
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import cv2, numpy as np
from PIL import Image

COEFF=np.array([1.,1/3,-1/3,-1.],np.float32)
ROLLS=['-25','-20','-15','-10','-05','+00','+05','+10','+15','+20','+25']
AMPS=[0.75,1.0,1.25,1.5]

def ss(e0,e1,x):
 t=np.clip((x-e0)/(e1-e0),0,1); return t*t*(3-2*t)

def build(root,r,eye,amp):
 base=np.array(Image.open(root/f'kopf_rgba/roll/gier_+00_nick_+00_roll_{r}.png').convert('RGBA'),np.uint8)
 d=root/f'kopf_rgba_parallax/gier_+00_nick_+00_roll_{r}'
 sl=[np.array(Image.open(next(d.glob(f'slice_{i}_*.png'))).convert('RGBA'),np.uint8) for i in range(4)]
 aa=np.stack([s[:,:,3].astype(np.float32)/255 for s in sl]); den=np.maximum(aa.sum(0),1e-6); depth=(aa*COEFF[:,None,None]).sum(0)/den; depth[den<.02]=0; depth=cv2.GaussianBlur(depth,(0,0),1)
 a=base[:,:,3].astype(np.float32)/255; gx=cv2.Sobel(a,cv2.CV_32F,1,0,ksize=3);gy=cv2.Sobel(a,cv2.CV_32F,0,1,ksize=3); grad=np.sqrt(gx*gx+gy*gy)
 yy,xx=np.mgrid[0:a.shape[0],0:a.shape[1]].astype(np.float32); ell=((xx-eye[0])/220)**2+((yy-eye[1])/125)**2
 gate=ss(.70,.97,a)*(1-ss(.015,.10,grad))*ss(1.,1.55,ell)
 dx=amp*depth*gate
 # OpenCV remap requires CV_32FC1/CV_32FC2 or CV_16SC2 maps.  NumPy may
 # promote xx-dx to float64 when amp/eye arrive as Python/np.float64 scalars,
 # so pin the executable map ABI explicitly instead of relying on promotion.
 mapx=np.ascontiguousarray(xx-dx,dtype=np.float32)
 mapy=np.ascontiguousarray(yy,dtype=np.float32)
 rgb=cv2.remap(base[:,:,:3],mapx,mapy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
 out=np.dstack([rgb,base[:,:,3]])
 return base,out,gate,dx

def gray(x):return cv2.cvtColor(x[:,:,:3],cv2.COLOR_RGB2GRAY).astype(np.float32)
def lap(g,m):
 v=np.abs(cv2.Laplacian(g,cv2.CV_32F)); return float(v[m].mean()) if m.any() else 0.
def phase(a,b,cx,cy,rx=48,ry=32):
 x0=max(0,int(cx-rx));x1=min(a.shape[1],int(cx+rx));y0=max(0,int(cy-ry));y1=min(a.shape[0],int(cy+ry)); A=a[y0:y1,x0:x1];B=b[y0:y1,x0:x1];
 if min(A.shape)<10:return 0,0,0
 (x,y),r=cv2.phaseCorrelate(A,B);return float(x),float(y),float(r)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--visual-root',default='/home/ai-core-node/.claude/star/visual');ap.add_argument('--width',type=int,default=620);ap.add_argument('--height',type=int,default=414);args=ap.parse_args();root=Path(args.visual_root)
 anc=json.loads((root/'rig2/augen_anker_exakt.json').read_text());a0=np.array([anc['augen_anker_roll0']['x'],anc['augen_anker_roll0']['y']],float)
 by={str(a):[] for a in AMPS}
 sx=args.width/1536; sy=args.height/1024
 for r in ROLLS:
  o=anc['werte'][str(int(r))]; eye=tuple(a0+np.array([o['dx_px'],o['dy_px']]))
  for amp in AMPS:
   b,w,g,dx=build(root,r,eye,amp)
   # Use INTER_AREA for final high-quality minification; both baseline and candidate identical path.
   bd=cv2.resize(b,(args.width,args.height),interpolation=cv2.INTER_AREA); wd=cv2.resize(w,(args.width,args.height),interpolation=cv2.INTER_AREA)
   gd=cv2.resize(g.astype(np.float32),(args.width,args.height),interpolation=cv2.INTER_AREA); dxd=cv2.resize(dx.astype(np.float32),(args.width,args.height),interpolation=cv2.INTER_AREA)
   diff=np.abs(wd[:,:,:3].astype(np.float32)-bd[:,:,:3].astype(np.float32)); opaque=bd[:,:,3]>=245; active=gd>.05
   g0=gray(bd);g1=gray(wd); ex=eye[0]*sx;ey=eye[1]*sy;px,py,pr=phase(g0,g1,ex,ey)
   # Difference fractions at final display pixels are the signal-survival metric.
   mx=diff.max(2)
   by[str(amp)].append({'alpha_exact':bool(np.array_equal(bd[:,:,3],wd[:,:,3])),'active_frac':float(active.mean()),'changed_gt1_active':float((mx[active]>1).mean()) if active.any() else 0,'changed_gt3_active':float((mx[active]>3).mean()) if active.any() else 0,'rgb_mae_active':float(diff[active].mean()) if active.any() else 0,'rgb_p99_active':float(np.quantile(diff[active],.99)) if active.any() else 0,'lap_ratio':(lap(g1,opaque)+1e-9)/(lap(g0,opaque)+1e-9),'eye_shift_px':float(math.hypot(px,py)),'eye_resp':pr,'max_shift_display_from_field':float(np.max(np.abs(dxd))*sx),'p95_shift_display':float(np.quantile(np.abs(dxd[active]),.95)*sx) if active.any() else 0})
 print('DEPTHWARP_DISPLAY_SPACE_GATE/v1',args.width,args.height)
 for amp in AMPS:
  R=by[str(amp)];print('AMP',amp,json.dumps({'all_alpha_exact':all(x['alpha_exact'] for x in R),'active_frac_min':min(x['active_frac'] for x in R),'changed_gt1_active_min':min(x['changed_gt1_active'] for x in R),'changed_gt3_active_min':min(x['changed_gt3_active'] for x in R),'rgb_mae_active_range':[min(x['rgb_mae_active'] for x in R),max(x['rgb_mae_active'] for x in R)],'rgb_p99_active_max':max(x['rgb_p99_active'] for x in R),'lap_ratio_range':[min(x['lap_ratio'] for x in R),max(x['lap_ratio'] for x in R)],'eye_shift_px_max':max(x['eye_shift_px'] for x in R),'eye_resp_min':min(x['eye_resp'] for x in R),'max_shift_display':max(x['max_shift_display_from_field'] for x in R),'p95_shift_display_max':max(x['p95_shift_display'] for x in R)},sort_keys=True))
if __name__=='__main__':main()
