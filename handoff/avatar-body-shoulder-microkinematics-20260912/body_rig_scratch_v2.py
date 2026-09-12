#!/usr/bin/env python3
"""Scratch-only body/shoulder rig v2: neck-locked, zero-exact, amplitude sweep.

No production write. This is a causal geometry discriminator for selecting a future
low-cost runtime body mesh/layer implementation.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw


def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()


def body_src(html: str) -> str:
    m=re.search(r'<img[^>]+id=["\']koerper-schicht["\'][^>]*>',html,re.I)
    if not m: raise RuntimeError('#koerper-schicht img not found')
    s=re.search(r'src=["\']([^"\']+)',m.group(0),re.I)
    if not s: raise RuntimeError('#koerper-schicht src not found')
    return s.group(1)


def alpha_bbox(a: np.ndarray):
    ys,xs=np.where(a>0)
    if not len(xs): raise RuntimeError('empty body alpha')
    return int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1


def gauss(xx,yy,cx,cy,sx,sy):
    return np.exp(-0.5*(((xx-cx)/sx)**2+((yy-cy)/sy)**2))


def kin(t: float, scale: float=1.0):
    b=math.sin(2*math.pi*t/4.9)
    l=math.sin(2*math.pi*t/8.7+0.83)
    r=math.sin(2*math.pi*t/11.3+2.14)
    return {
      'left_dy':scale*(-0.46*b+0.12*l),
      'right_dy':scale*(-0.42*b+0.09*r),
      'left_rot_deg':scale*(0.085*l+0.025*b),
      'right_rot_deg':scale*(-0.070*r-0.018*b),
      'chest_dy':scale*(-0.18*b),
    }


def field(shape,bbox,k,neck_box):
    h,w=shape; x0,y0,x1,y1=bbox; bw=x1-x0; bh=y1-y0
    yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
    lcx,rcx=x0+.27*bw,x0+.73*bw; scy=y0+.19*bh
    wl=gauss(xx,yy,lcx,scy,.18*bw,.115*bh)
    wr=gauss(xx,yy,rcx,scy,.18*bw,.115*bh)
    wc=gauss(xx,yy,x0+.5*bw,y0+.31*bh,.25*bw,.13*bh)

    # Lower-body anchor: deformation fades to zero below upper torso.
    c0,c1=y0+.38*bh,y0+.62*bh
    low=np.ones_like(yy); low[yy>=c1]=0
    mid=(yy>c0)&(yy<c1)
    low[mid]=.5+.5*np.cos(math.pi*(yy[mid]-c0)/(c1-c0))
    wl*=low; wr*=low; wc*=low

    lr=math.radians(k['left_rot_deg']); rr=math.radians(k['right_rot_deg'])
    dx=wl*(-lr*(yy-scy))+wr*(-rr*(yy-scy))
    dy=wl*(k['left_dy']+lr*(xx-lcx))+wr*(k['right_dy']+rr*(xx-rcx))+wc*k['chest_dy']

    # Exact neck lock inside preregistered ROI, with a 36px smooth ramp outside.
    nx0,ny0,nx1,ny1=neck_box; feather=36.0
    ox=np.maximum(np.maximum(nx0-xx,0),np.maximum(xx-(nx1-1),0))
    oy=np.maximum(np.maximum(ny0-yy,0),np.maximum(yy-(ny1-1),0))
    outside=np.sqrt(ox*ox+oy*oy)
    move=np.clip(outside/feather,0,1)
    dx*=move; dy*=move
    return dx.astype(np.float32),dy.astype(np.float32),wl,wr,wc,move


def warp(src,dx,dy):
    # Correct boundary-preserving inverse bilinear map: zero field must be byte-exact,
    # including final row/column (v1 incorrectly invalidated border pixels).
    h,w,_=src.shape; yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
    sx=xx-dx; sy=yy-dy
    valid=(sx>=0)&(sx<=w-1)&(sy>=0)&(sy<=h-1)
    x0=np.floor(sx).astype(np.int32); y0=np.floor(sy).astype(np.int32)
    x0c=np.clip(x0,0,w-1); y0c=np.clip(y0,0,h-1)
    x1c=np.clip(x0+1,0,w-1); y1c=np.clip(y0+1,0,h-1)
    fx=(sx-x0)[...,None]; fy=(sy-y0)[...,None]
    a=src[y0c,x0c].astype(np.float32); b=src[y0c,x1c].astype(np.float32)
    c=src[y1c,x0c].astype(np.float32); d=src[y1c,x1c].astype(np.float32)
    out=(a*(1-fx)+b*fx)*(1-fy)+(c*(1-fx)+d*fx)*fy
    out[~valid]=0
    return np.clip(np.rint(out),0,255).astype(np.uint8)


def edge(g):
    g=g.astype(np.float32)
    return float(np.abs(np.diff(g,axis=1)).mean()+np.abs(np.diff(g,axis=0)).mean())


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--visual-root',default='.'); ap.add_argument('--out',required=True)
    ap.add_argument('--seconds',type=float,default=18); ap.add_argument('--fps',type=int,default=60)
    a=ap.parse_args(); root=Path(a.visual_root).resolve(); out=Path(a.out); out.mkdir(parents=True,exist_ok=False)
    hp=root/'buehne.html'; html=hp.read_text(errors='replace'); rel=body_src(html); bp=root/rel.lstrip('/')
    im=Image.open(bp).convert('RGBA'); src=np.asarray(im,dtype=np.uint8); alpha=src[:,:,3]; bbox=alpha_bbox(alpha)
    x0,y0,x1,y1=bbox; bw=x1-x0; bh=y1-y0
    neck=(max(0,int(x0+.34*bw)),max(0,int(y0)),min(src.shape[1],int(x0+.66*bw)),min(src.shape[0],int(y0+.22*bh)))
    nx0,ny0,nx1,ny1=neck

    z=np.zeros(alpha.shape,dtype=np.float32); zero=warp(src,z,z)
    zero_equal=bool(np.array_equal(zero,src)); zero_max=int(np.abs(zero.astype(np.int16)-src.astype(np.int16)).max())

    # Full temporal trace for smoothness/independence at nominal scale.
    traces=[]; max_px=max_deg=0.0; prev=None
    for i in range(max(2,int(a.seconds*a.fps))):
        t=i/a.fps; k=kin(t,1); traces.append(k)
        if prev:
            max_px=max(max_px,abs(k['left_dy']-prev['left_dy']),abs(k['right_dy']-prev['right_dy']))
            max_deg=max(max_deg,abs(k['left_rot_deg']-prev['left_rot_deg']),abs(k['right_rot_deg']-prev['right_rot_deg']))
        prev=k
    lv=np.array([q['left_dy'] for q in traces]); rv=np.array([q['right_dy'] for q in traces]); corr=float(np.corrcoef(lv,rv)[0,1])

    basegray=np.asarray(im.convert('L')); base_neck=edge(basegray[ny0:ny1,nx0:nx1])
    support=(alpha>0).astype(np.float32)
    support=np.maximum.reduce([support,np.roll(support,1,0),np.roll(support,-1,0),np.roll(support,1,1),np.roll(support,-1,1)])
    times=[0,1.225,2.45,3.675,4.9,7.35]
    scales=[0.5,1.0,1.5]
    sweeps={}; nominal=[]
    for scale in scales:
        rows=[]
        for j,t in enumerate(times):
            k=kin(t,scale); dx,dy,wl,wr,wc,mv=field(alpha.shape,bbox,k,neck); dx*=support; dy*=support
            warped=warp(src,dx,dy); diff=np.abs(warped.astype(np.int16)-src.astype(np.int16))
            neckdiff=np.abs(warped[ny0:ny1,nx0:nx1].astype(np.int16)-src[ny0:ny1,nx0:nx1].astype(np.int16))
            gray=np.asarray(Image.fromarray(warped,'RGBA').convert('L')); ne=edge(gray[ny0:ny1,nx0:nx1])
            row={'t':t,'max_abs_dx':float(np.max(np.abs(dx))),'max_abs_dy':float(np.max(np.abs(dy))),
                 'rgba_mae':float(diff.mean()),'rgba_p99':float(np.percentile(diff,99)),
                 'neck_pixel_max_delta':int(neckdiff.max()),'neck_edge_ratio_vs_base':ne/base_neck if base_neck else None}
            rows.append(row)
            if scale==1.0:
                p=out/f'body_v2_{j:02d}_{t:.3f}s.png'; Image.fromarray(warped,'RGBA').save(p); nominal.append(p)
        sweeps[str(scale)]={'frames':rows,'worst_neck_pixel_delta':max(r['neck_pixel_max_delta'] for r in rows),
                            'neck_ratio_min':min(r['neck_edge_ratio_vs_base'] for r in rows),
                            'neck_ratio_max':max(r['neck_edge_ratio_vs_base'] for r in rows),
                            'rgba_mae_max':max(r['rgba_mae'] for r in rows),'max_abs_dy':max(r['max_abs_dy'] for r in rows)}

    # Contact sheet only for nominal candidate.
    tw=420; th=max(1,round(im.height*tw/im.width)); sheet=Image.new('RGB',(tw*3,th*2),'#202020'); dr=ImageDraw.Draw(sheet); s=20
    for yy in range(0,sheet.height,s):
      for xx in range(0,sheet.width,s):
        if ((xx//s)+(yy//s))%2: dr.rectangle((xx,yy,xx+s-1,yy+s-1),fill='#303030')
    for i,p in enumerate(nominal):
      tile=Image.open(p).convert('RGBA').resize((tw,th),Image.Resampling.LANCZOS); x=(i%3)*tw; y=(i//3)*th; sheet.paste(tile,(x,y),tile)
    contact=out/'contact_sheet_v2.jpg'; sheet.save(contact,quality=92)

    report={'schema':'FRANK_AVATAR_BODY_SHOULDER_SCRATCH/v2','status':'SCRATCH_ONLY_NOT_LIVE',
      'html_sha256':sha256(hp),'body_src':rel,'body_sha256':sha256(bp),'body_size':list(im.size),'alpha_bbox':list(bbox),'neck_box':list(neck),
      'zero_reconstruction':{'byte_exact':zero_equal,'max_delta':zero_max},
      'temporal':{'fps':a.fps,'seconds':a.seconds,'samples':len(traces),'max_frame_step_px':max_px,'max_frame_step_deg':max_deg,'left_right_vertical_corr':corr},
      'amplitude_sweep':sweeps,'contact_sheet':str(contact),
      'acceptance':{'zero_byte_exact':zero_equal,'neck_locked_all_nominal':sweeps['1.0']['worst_neck_pixel_delta']==0,
                    'temporal_step_px_le_0_35':max_px<=.35,'temporal_step_deg_le_0_12':max_deg<=.12,'not_mirror_locked':corr<.999},
      'runtime_credit':0,'live_mutation':False}
    rp=out/'report.json'; rp.write_text(json.dumps(report,indent=2,sort_keys=True)); print(json.dumps(report,indent=2,sort_keys=True))

if __name__=='__main__': main()
