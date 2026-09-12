#!/usr/bin/env python3
"""Read-only continuity audit for existing photographed body-action frames."""
from pathlib import Path
from PIL import Image
import argparse, hashlib, json
import numpy as np


def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return np.asarray(Image.open(p).convert('RGBA'),dtype=np.uint8)
def pair(a,b):
    A=load(a); B=load(b)
    if A.shape!=B.shape: return {'shape_match':False,'a':list(A.shape),'b':list(B.shape)}
    aa=A[:,:,3]; ba=B[:,:,3]; am=aa>=16; bm=ba>=16
    inter=int(np.count_nonzero(am&bm)); uni=int(np.count_nonzero(am|bm)); deep=int(np.count_nonzero((aa>=64)&(ba<32)))
    d=np.abs(A.astype(np.int16)-B.astype(np.int16)); ov=am&bm
    rgb=float(np.mean(d[:,:,:3][ov])) if np.any(ov) else None
    return {'shape_match':True,'alpha_jaccard':inter/max(1,uni),'deep_lost_px':deep,'rgba_mae':float(d.mean()),'overlap_rgb_mae':rgb,'max_delta':int(d.max())}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');a=ap.parse_args();r=Path(a.root)
    seq={
      'atmen':[r/f'koerper_rgba/atmen__atmen_{i:03d}.png' for i in range(12)],
      'schulterzucken':[r/f'koerper_rgba/schulterzucken/zucken_{i:03d}.png' for i in range(8)],
      'aufrichten':[r/f'koerper_rgba/aufrichten/aufrichten_{i:03d}.png' for i in range(8)],
      'lehnen':[r/f'koerper_rgba/lehnen/lehnen_{x}.png' for x in ['+00','+05','+10','+15','+20','+15','+10','+05','+00']],
      'gewicht':[r/f'koerper_rgba/gewicht/gewicht_{x}.png' for x in ['+00','+05','+10','+15','+10','+05','+00','-05','-10','-05','+00']],
      'schulterdrehung':[r/f'koerper_rgba/schulterdrehung/schulter_{x}.png' for x in ['+00','+05','+10','+15','+10','+05','+00','-05','-10','-05','+00']],
    }
    out={'schema':'BODY_ACTION_CONTINUITY/v1','actions':{},'missing':[]}
    for name,paths in seq.items():
      miss=[str(p) for p in paths if not p.exists()]
      if miss: out['missing']+=miss; continue
      rows=[]
      for i,(x,y) in enumerate(zip(paths,paths[1:])):
        m=pair(x,y);m.update({'i':i,'a':str(x.relative_to(r)),'b':str(y.relative_to(r))});rows.append(m)
      out['actions'][name]={'frames':len(paths),'unique_files':len(set(map(str,paths))),'first_sha256':h(paths[0]),'pairs':rows,
        'worst':{'min_alpha_jaccard':min(x['alpha_jaccard'] for x in rows),'max_deep_lost_px':max(x['deep_lost_px'] for x in rows),'max_rgba_mae':max(x['rgba_mae'] for x in rows),'max_overlap_rgb_mae':max(x['overlap_rgb_mae'] for x in rows)}}
    print(json.dumps(out,sort_keys=True))
if __name__=='__main__': main()
