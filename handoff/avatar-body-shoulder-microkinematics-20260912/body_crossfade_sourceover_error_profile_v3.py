#!/usr/bin/env python3
"""Diagnostic successor to source-over v2; never relaxes the v2 gate.

Runs the exact corrected v2 experiment and adds error-shape measurements needed
to distinguish transparent-edge/raw-RGB noise from visible premultiplied color
or alpha disagreement. Read-only; no production mutation or promotion.
"""
from __future__ import annotations

import pathlib

src = pathlib.Path(__file__).with_name("body_crossfade_sourceover_identity.py")
code = src.read_text()
old_uv = "uv=vec2(p.x,1.-p.y);"
if code.count(old_uv) != 1:
    raise SystemExit("HARNESS_SOURCE_DRIFT: orientation expression")
code = code.replace(old_uv, "uv=p;", 1)

start = code.index("function met(A,B){")
end = code.index("let R=", start)
metric_fn = r'''function met(A,B){
 let mae=0,am=0,mx=0,amax=0,deep=0,pm=0,vispm=0,visraw=0,visn=0,ad=[];
 let th=[1,4,16,32,64],ji={};for(const t of th)ji[t]=[0,0];
 for(let i=0;i<W*H;i++){
  let z=i*4,aa=A[z+3],ba=B[z+3],da=Math.abs(aa-ba);am+=da;amax=Math.max(amax,da);ad.push(da);
  if(aa>=64&&ba<32)deep++;
  for(const t of th){let xa=aa>=t,ya=ba>=t;if(xa&&ya)ji[t][0]++;if(xa||ya)ji[t][1]++}
  let visible=Math.max(aa,ba)>=16;if(visible)visn++;
  for(let q=0;q<4;q++){let d=Math.abs(A[z+q]-B[z+q]);mae+=d;mx=Math.max(mx,d)}
  for(let q=0;q<3;q++){
   let pa=A[z+q]*aa/255,pb=B[z+q]*ba/255;pm+=Math.abs(pa-pb);
   if(visible){vispm+=Math.abs(pa-pb);visraw+=Math.abs(A[z+q]-B[z+q])}
  }
 }
 ad.sort((a,b)=>a-b);let pct=p=>ad[Math.min(ad.length-1,Math.floor((ad.length-1)*p))];
 return {rgba_mae:mae/(W*H*4),rgba_max:mx,alpha_mae:am/(W*H),alpha_max:amax,
  alpha_p95:pct(.95),alpha_p99:pct(.99),deep_hole_px:deep,
  premul_rgb_mae:pm/(W*H*3),premul_visible_rgb_mae:vispm/Math.max(1,visn*3),
  raw_visible_rgb_mae:visraw/Math.max(1,visn*3),visible_px:visn,
  jaccard_t1:ji[1][0]/Math.max(1,ji[1][1]),jaccard_t4:ji[4][0]/Math.max(1,ji[4][1]),
  jaccard_t16:ji[16][0]/Math.max(1,ji[16][1]),jaccard_t32:ji[32][0]/Math.max(1,ji[32][1]),
  jaccard_t64:ji[64][0]/Math.max(1,ji[64][1])};}
'''
code = code[:start] + metric_fn + code[end:]
old = "R.directions[dir][name]={tests:rows.length,max_rgba_mae:Math.max(...rows.map(x=>x.rgba_mae)),max_rgba_max:Math.max(...rows.map(x=>x.rgba_max)),max_alpha_mae:Math.max(...rows.map(x=>x.alpha_mae)),max_deep_hole_px:Math.max(...rows.map(x=>x.deep_hole_px)),min_jaccard:Math.min(...rows.map(x=>x.jaccard))}"
new = "R.directions[dir][name]={tests:rows.length,max_rgba_mae:Math.max(...rows.map(x=>x.rgba_mae)),max_rgba_max:Math.max(...rows.map(x=>x.rgba_max)),max_alpha_mae:Math.max(...rows.map(x=>x.alpha_mae)),max_alpha_max:Math.max(...rows.map(x=>x.alpha_max)),max_alpha_p95:Math.max(...rows.map(x=>x.alpha_p95)),max_alpha_p99:Math.max(...rows.map(x=>x.alpha_p99)),max_deep_hole_px:Math.max(...rows.map(x=>x.deep_hole_px)),max_premul_rgb_mae:Math.max(...rows.map(x=>x.premul_rgb_mae)),max_premul_visible_rgb_mae:Math.max(...rows.map(x=>x.premul_visible_rgb_mae)),max_raw_visible_rgb_mae:Math.max(...rows.map(x=>x.raw_visible_rgb_mae)),min_jaccard_t1:Math.min(...rows.map(x=>x.jaccard_t1)),min_jaccard_t4:Math.min(...rows.map(x=>x.jaccard_t4)),min_jaccard_t16:Math.min(...rows.map(x=>x.jaccard_t16)),min_jaccard_t32:Math.min(...rows.map(x=>x.jaccard_t32)),min_jaccard_t64:Math.min(...rows.map(x=>x.jaccard_t64))}"
if code.count(old) != 1:
    raise SystemExit(f"HARNESS_SOURCE_DRIFT: aggregation count={code.count(old)}")
code = code.replace(old, new, 1)
code = code.replace("BODY_CROSSFADE_SOURCEOVER_IDENTITY/v1", "BODY_CROSSFADE_SOURCEOVER_ERROR_PROFILE/v3", 1)
ns = {"__name__": "__main__", "__file__": str(src) + "#error-profile-v3", "__package__": None}
exec(compile(code, str(src) + "#error-profile-v3", "exec"), ns, ns)
