#!/usr/bin/env python3
"""Generate a same-run upload-vs-preuploaded-texture-cache A/B gate.

Reviewer/falsifier utility only. It patches the accepted body performance attribution
harness without touching the live avatar source. The benchmark stays on the same
atmen image family and same residual mesh/warp; only per-transition texImage2D upload
versus bind-only cached textures changes.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def one(s: str, old: str, new: str) -> str:
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"PATCH_COUNT expected 1 got {n}: {old!r}")
    return s.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("out")
    a = ap.parse_args()
    s = Path(a.base).read_text()

    marker = "let tex=[gl.createTexture(),gl.createTexture()],bound=[null,null],uploads=0;"
    s = one(s, marker, marker + "let cache=new Map(),cache_uploads=0,cache_build_ms=0;")

    old = "function put(i,im){if(bound[i]===im)return;gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,tex[i]);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im);bound[i]=im;uploads++}"
    new = "function cacheOne(im){let x=gl.createTexture();gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,x);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im);cache.set(im,x);cache_uploads++}let ct0=performance.now();for(const im of all['atmen'])cacheOne(im);gl.finish();cache_build_ms=performance.now()-ct0;function put(i,im,cached){if(cached){gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,cache.get(im));return}if(bound[i]===im)return;gl.activeTexture(gl.TEXTURE0+i);gl.bindTexture(gl.TEXTURE_2D,tex[i]);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,1);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im);bound[i]=im;uploads++}"
    s = one(s, old, new)

    s = one(
        s,
        "function draw(name,i,j,m,t,warp){put(0,all[name][i]);put(1,all[name][j]);",
        "function draw(name,i,j,m,t,warp,cached){put(0,all[name][i],cached);put(1,all[name][j],cached);",
    )
    s = one(
        s,
        "async function run(mode,rep){let dynamic=mode.startsWith('player_'),warp=mode.endsWith('_warp'),names=Object.keys(all),frame=0,namei=0,ai=0,ts=[];",
        "async function run(mode,rep){let dynamic=true,warp=true,cached=mode.startsWith('cached_'),names=['atmen'],frame=0,namei=0,ai=0,ts=[];",
    )
    s = one(s, "draw(name,0,1,.5,warm/60,warp);r()", "draw(name,0,1,.5,warm/60,warp,cached);r()")
    s = one(s, "draw(name,i,j,.5,n/60,warp);frame++;r()", "draw(name,i,j,.5,n/60,warp,cached);frame++;r()")

    s = one(
        s,
        "const order=['static_base','player_base','player_warp','static_warp','static_warp','player_warp','player_base','static_base'],rows=[];let reps={};for(const mode of order){reps[mode]=(reps[mode]||0)+1;rows.push(await run(mode,reps[mode]))}",
        "const order=['upload_warp','cached_warp','cached_warp','upload_warp'],rows=[];let reps={};for(const mode of order){reps[mode]=(reps[mode]||0)+1;rows.push(await run(mode,reps[mode]))}",
    )
    s = one(
        s,
        "let A={};for(const m of ['static_base','static_warp','player_base','player_warp'])A[m]=agg(m);A.warp_overhead_static_ms=A.static_warp.mean_ms-A.static_base.mean_ms;A.warp_overhead_player_ms=A.player_warp.mean_ms-A.player_base.mean_ms;A.player_overhead_base_ms=A.player_base.mean_ms-A.static_base.mean_ms;A.player_overhead_warp_ms=A.player_warp.mean_ms-A.static_warp.mean_ms;",
        "let A={};for(const m of ['upload_warp','cached_warp'])A[m]=agg(m);A.cache_minus_upload_mean_ms=A.cached_warp.mean_ms-A.upload_warp.mean_ms;A.cache_minus_upload_p95_ms=A.cached_warp.p95_ms_max-A.upload_warp.p95_ms_max;A.slow20_delta=A.cached_warp.over20_total-A.upload_warp.over20_total;A.uploads_delta=A.cached_warp.measured_uploads_total-A.upload_warp.measured_uploads_total;",
    )
    s = one(
        s,
        "schema:'BODY_PLAYER_PERF_ATTRIBUTION_AB/v1'",
        "schema:'BODY_TEXTURE_CACHE_AB/v1',cache_build_ms,cache_uploads",
    )

    Path(a.out).write_text(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
