#!/usr/bin/env python3
"""BODY_CROSSFADE_SOURCEOVER_IDENTITY/v3 edge-fidelity diagnostic.

v2 showed tiny whole-frame alpha error but a hypersensitive alpha>=16 Jaccard
failure on antialiased silhouette fringes. v3 leaves the compositor equations
unchanged and changes only diagnostics: premultiplied RGBA error plus alpha>=64
silhouette Jaccard. This prevents undefined RGB under near-transparent pixels and
one-level fringe rounding from masquerading as a ghost-silhouette failure.
"""
from __future__ import annotations
import pathlib

HERE=pathlib.Path(__file__).resolve().parent
V1=HERE/'body_crossfade_sourceover_identity.py'
src=V1.read_text()
old_uv='uv=vec2(p.x,1.-p.y);'
old_schema='BODY_CROSSFADE_SOURCEOVER_IDENTITY/v1'
old_met="function met(A,B){let mae=0,am=0,mx=0,deep=0,inter=0,uni=0;for(let i=0;i<W*H;i++){let z=i*4;for(let q=0;q<4;q++){let d=Math.abs(A[z+q]-B[z+q]);mae+=d;mx=Math.max(mx,d)}let x=A[z+3],y=B[z+3];am+=Math.abs(x-y);if(x>=64&&y<32)deep++;let xa=x>=16,ya=y>=16;if(xa&&ya)inter++;if(xa||ya)uni++}return {rgba_mae:mae/(W*H*4),rgba_max:mx,alpha_mae:am/(W*H),deep_hole_px:deep,jaccard:inter/Math.max(1,uni)}}"
new_met="function met(A,B){let mae=0,am=0,mx=0,deep=0,inter=0,uni=0;for(let i=0;i<W*H;i++){let z=i*4,aa=A[z+3],ba=B[z+3];am+=Math.abs(aa-ba);for(let q=0;q<3;q++){let ap=A[z+q]*aa/255,bp=B[z+q]*ba/255,d=Math.abs(ap-bp);mae+=d;mx=Math.max(mx,d)}let ad=Math.abs(aa-ba);mae+=ad;mx=Math.max(mx,ad);if(aa>=64&&ba<32)deep++;let xa=aa>=64,ya=ba>=64;if(xa&&ya)inter++;if(xa||ya)uni++}return {rgba_mae:mae/(W*H*4),rgba_max:mx,alpha_mae:am/(W*H),deep_hole_px:deep,jaccard:inter/Math.max(1,uni)}}"
assert src.count(old_uv)==1
assert src.count(old_schema)==1
assert src.count(old_met)==1
patched=src.replace(old_uv,'uv=p;').replace(old_schema,'BODY_CROSSFADE_SOURCEOVER_IDENTITY/v3').replace(old_met,new_met)
ns={'__name__':'__main__','__file__':str(V1),'__package__':None}
exec(compile(patched,str(V1)+'#v3_edge_metrics','exec'),ns,ns)
