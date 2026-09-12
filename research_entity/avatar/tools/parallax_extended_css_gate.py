#!/usr/bin/env python3
"""Extended real-Chrome parallax integrity gate.

Scratch-only measurement tool. It never edits the avatar runtime or assets.
It renders the exact four depth slices through Chrome Canvas2D `lighter` at
several source-pixel amplitudes, then reports silhouette and eye-registration
metrics translated into real CSS-pixel units.
"""
from __future__ import annotations

import argparse
import html as htmlmod
import json
import pathlib
import re
import subprocess
import tempfile


def build_html(root: pathlib.Path, anchors: dict[str, dict[str, float]], scale: float) -> str:
    root_uri = root.as_uri().rstrip("/") + "/"
    anchors_json = json.dumps(anchors, separators=(",", ":"))
    return r'''<!doctype html><meta charset=utf-8><canvas id=c width=1536 height=1024></canvas><script>
const ROOT=__ROOT__;
const rolls=['-25','-20','-15','-10','-05','+00','+05','+10','+15','+20','+25'];
const co=[1,1/3,-1/3,-1];
const amps=[.75,1,1.25,1.5,2];
const scale=__SCALE__;
const anchors=__ANCHORS__;
const cvs=document.getElementById('c');
const ctx=cvs.getContext('2d',{willReadFrequently:true});
function img(u){return new Promise((res,rej)=>{let x=new Image();x.onload=()=>res(x);x.onerror=()=>rej(Error(u));x.src=u})}
function rn(r){return String(parseInt(r,10))}
function dir(r){return 'kopf_rgba_parallax/gier_+00_nick_+00_roll_'+r+'/'}
async function files(r){let n=['slice_0_front_nase.png','slice_1_mitte_gesicht.png','slice_2_seite_ohren.png','slice_3_hinten_haar.png'];return Promise.all(n.map(x=>img(ROOT+dir(r)+x)))}
function render(ss,A){ctx.globalCompositeOperation='source-over';ctx.clearRect(0,0,1536,1024);ctx.globalCompositeOperation='lighter';for(let i=0;i<4;i++)ctx.drawImage(ss[i],co[i]*A,0);ctx.globalCompositeOperation='source-over';return ctx.getImageData(0,0,1536,1024).data.slice()}
function lum(d,p){return .2126*d[p]+.7152*d[p+1]+.0722*d[p+2]}
function bilum(d,x,y){let x0=Math.floor(x),x1=x0+1,f=x-x0;if(x0<0||x1>1535||y<0||y>1023)return 0;let p0=(y*1536+x0)*4,p1=(y*1536+x1)*4;return lum(d,p0)*(1-f)+lum(d,p1)*f}
function metrics(ref,v,a){
 let n=1536*1024,as=0,lost=0,gain=0,inter=0,uni=0,deep=0,maxA=0;
 for(let q=0;q<n;q++){let p=q*4,x=ref[p+3],y=v[p+3],d=Math.abs(x-y);as+=d;if(d>maxA)maxA=d;let mx=x>=16,my=y>=16;if(mx&&my)inter++;if(mx||my)uni++;if(mx&&!my)lost++;if(!mx&&my)gain++;if(x>=64&&y<32)deep++}
 let cx=610+(a.dx_px||0),cy=207+(a.dy_px||0),x0=Math.max(3,Math.round(cx-207)),x1=Math.min(1532,Math.round(cx+207)),y0=Math.max(0,Math.round(cy-113)),y1=Math.min(1023,Math.round(cy+114));
 let best={shift_x:0,mae:1e99};
 for(let si=-50;si<=50;si++){let s=si*.05,err=0,w=0;for(let y=y0;y<y1;y+=5)for(let x=x0;x<x1;x+=5){let p=(y*1536+x)*4;if(ref[p+3]<16&&v[p+3]<16)continue;err+=Math.abs(lum(v,p)-bilum(ref,x-s,y));w++}let e=err/Math.max(w,1);if(e<best.mae)best={shift_x:+s.toFixed(2),mae:+e.toFixed(4),samples:w}}
 return {alpha_mae:+(as/n).toFixed(6),alpha_max:maxA,jaccard:+(inter/Math.max(uni,1)).toFixed(8),lost_px:lost,gain_px:gain,deep_hole_px:deep,eye_shift_src:best.shift_x,eye_shift_css:+(Math.abs(best.shift_x)*scale).toFixed(4),eye_mae:best.mae};
}
(async()=>{
 let out={schema:'PARALLAX_EXTENDED_CSS_GATE/v1',compositor:'Chrome Canvas2D lighter',scale_source_to_css:scale,amps:{}};
 for(const A of amps)out.amps[String(A)]={css_max_layer_shift:+(A*scale).toFixed(4),rows:{}};
 for(const r of rolls){let ss=await files(r),z=render(ss,0);for(const A of amps)out.amps[String(A)].rows[r]=metrics(z,render(ss,A),anchors[rn(r)])}
 for(const A of amps){let x=out.amps[String(A)],rs=Object.values(x.rows);x.worst={alpha_mae:Math.max(...rs.map(q=>q.alpha_mae)),min_jaccard:Math.min(...rs.map(q=>q.jaccard)),lost_px:Math.max(...rs.map(q=>q.lost_px)),gain_px:Math.max(...rs.map(q=>q.gain_px)),deep_hole_px:Math.max(...rs.map(q=>q.deep_hole_px)),eye_shift_src:Math.max(...rs.map(q=>Math.abs(q.eye_shift_src))),eye_shift_css:Math.max(...rs.map(q=>q.eye_shift_css)),eye_mae:Math.max(...rs.map(q=>q.eye_mae))}}
 document.body.innerText='RESULT_JSON '+JSON.stringify(out)
})().catch(e=>document.body.innerText='ERROR '+e.stack)
</script>'''.replace('__ROOT__', json.dumps(root_uri)).replace('__SCALE__', repr(scale)).replace('__ANCHORS__', anchors_json)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--visual-root', default='/home/ai-core-node/.claude/star/visual')
    ap.add_argument('--chrome', default='/usr/bin/google-chrome')
    ap.add_argument('--scale', type=float, default=0.4036458333333333)
    args = ap.parse_args()

    root = pathlib.Path(args.visual_root).resolve()
    anchors = json.loads((root / 'rig2/augen_anker_exakt.json').read_text())['werte']
    with tempfile.TemporaryDirectory(prefix='parallax-ext-') as td:
        gate = pathlib.Path(td) / 'gate.html'
        gate.write_text(build_html(root, anchors, args.scale))
        p = subprocess.run([
            args.chrome,
            '--headless=new',
            '--no-sandbox',
            '--allow-file-access-from-files',
            '--virtual-time-budget=90000',
            '--dump-dom',
            gate.as_uri(),
        ], capture_output=True, text=True, timeout=190)
        m = re.search(r'RESULT_JSON (\{.*?\})</body>', p.stdout, re.S)
        if not m:
            print(json.dumps({'status':'ERROR','chrome_rc':p.returncode,'stdout_tail':p.stdout[-2000:],'stderr_tail':p.stderr[-2000:]}, sort_keys=True))
            return 2
        data = json.loads(htmlmod.unescape(m.group(1)))
        print('PARALLAX_EXTENDED_CSS_GATE/v1')
        for amp, row in data['amps'].items():
            print('AMP', amp, 'css_max_layer_shift', row['css_max_layer_shift'], 'WORST', json.dumps(row['worst'], sort_keys=True))
        print('CHROME_RC', p.returncode)
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
