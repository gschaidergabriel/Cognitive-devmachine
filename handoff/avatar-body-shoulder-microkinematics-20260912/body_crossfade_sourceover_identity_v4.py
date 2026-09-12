#!/usr/bin/env python3
"""BODY_CROSSFADE_SOURCEOVER_IDENTITY/v4 — identical-raster discriminator.

v1-v3 mixed two questions: the Canvas2D reference resized original 1536x1024
images directly while WebGL first cached them as 620x414 textures. v4 forces both
reference and GPU compositor to consume the exact same pre-rasterized 620x414
Canvas2D plates, then restores the original strict metrics. This isolates only the
source-over/compositor math and fixed DOM layer ordering.
"""
from __future__ import annotations
import pathlib
HERE=pathlib.Path(__file__).resolve().parent
V1=HERE/'body_crossfade_sourceover_identity.py'
src=V1.read_text()
old_uv='uv=vec2(p.x,1.-p.y);'
old_schema='BODY_CROSSFADE_SOURCEOVER_IDENTITY/v1'
old_cache="let bound=[null,null],resize=document.createElement('canvas');resize.width=W;resize.height=H;let xc=resize.getContext('2d');function bind(i,p){if(bound[i]===p)return;xc.clearRect(0,0,W,H);xc.drawImage(imgs.get(p),0,0,W,H);g.activeTexture(g.TEXTURE0+i);g.bindTexture(g.TEXTURE_2D,tex[i]);g.pixelStorei(g.UNPACK_FLIP_Y_WEBGL,1);g.texImage2D(g.TEXTURE_2D,0,g.RGBA,g.RGBA,g.UNSIGNED_BYTE,resize);bound[i]=p}"
new_cache="let raster=new Map();for(const p of paths){let c=document.createElement('canvas');c.width=W;c.height=H;let x=c.getContext('2d',{alpha:true});x.clearRect(0,0,W,H);x.drawImage(imgs.get(p),0,0,W,H);raster.set(p,c)}let bound=[null,null];function bind(i,p){if(bound[i]===p)return;g.activeTexture(g.TEXTURE0+i);g.bindTexture(g.TEXTURE_2D,tex[i]);g.pixelStorei(g.UNPACK_FLIP_Y_WEBGL,1);g.texImage2D(g.TEXTURE_2D,0,g.RGBA,g.RGBA,g.UNSIGNED_BYTE,raster.get(p));bound[i]=p}"
old_css="function css(layer1,layer2,o1,o2){rc.clearRect(0,0,W,H);rc.globalCompositeOperation='source-over';rc.globalAlpha=o1;rc.drawImage(imgs.get(layer1),0,0,W,H);rc.globalAlpha=o2;rc.drawImage(imgs.get(layer2),0,0,W,H);rc.globalAlpha=1;return new Uint8Array(rc.getImageData(0,0,W,H).data)}"
new_css="function css(layer1,layer2,o1,o2){rc.clearRect(0,0,W,H);rc.globalCompositeOperation='source-over';rc.globalAlpha=o1;rc.drawImage(raster.get(layer1),0,0);rc.globalAlpha=o2;rc.drawImage(raster.get(layer2),0,0);rc.globalAlpha=1;return new Uint8Array(rc.getImageData(0,0,W,H).data)}"
for old in (old_uv,old_schema,old_cache,old_css): assert src.count(old)==1,(old[:80],src.count(old))
patched=(src.replace(old_uv,'uv=p;')
            .replace(old_schema,'BODY_CROSSFADE_SOURCEOVER_IDENTITY/v4')
            .replace(old_cache,new_cache)
            .replace(old_css,new_css))
ns={'__name__':'__main__','__file__':str(V1),'__package__':None}
exec(compile(patched,str(V1)+'#v4_identical_raster','exec'),ns,ns)
