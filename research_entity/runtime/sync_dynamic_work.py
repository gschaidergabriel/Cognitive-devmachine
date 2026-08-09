#!/usr/bin/env python3
"""One Clay cognition-boundary sync: capabilities -> work -> local probe -> schedule -> remote projections."""
from __future__ import annotations
import argparse,subprocess,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'research_entity/runtime/dynamic_work_runtime_v2.py';CAP=ROOT/'research_entity/runtime/system_capability_event_runtime.py';PUB=ROOT/'research_entity/runtime/publish_work_projection.py'
def run(path,*args,timeout=100):
    p=subprocess.run([sys.executable,str(path),*args],cwd=ROOT,text=True,capture_output=True,timeout=timeout);return {'rc':p.returncode,'out':p.stdout[-4000:],'err':p.stderr[-1000:]}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('cmd',nargs='?',default='sync');ap.add_argument('--observe-local',action='store_true');a=ap.parse_args()
    if a.cmd!='sync':raise SystemExit('only sync supported')
    out={'capabilities':run(CAP,'ingest'),'work_ingest':run(WORK,'ingest')}
    if a.observe_local:out['local']=run(WORK,'observe-local')
    out['recompute']=run(WORK,'recompute');out['projection']=run(PUB)
    print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
