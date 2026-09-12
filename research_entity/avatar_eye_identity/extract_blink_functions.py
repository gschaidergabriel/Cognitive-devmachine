#!/usr/bin/env python3
"""Read-only forensic extractor for the exact avatar blink functions."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from build_semantic_shadow_html import extract_function


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--source',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); args=ap.parse_args()
    text=args.source.read_text(encoding='utf-8')
    funcs={}
    for name,sig in {
        'blinzeln':'function blinzeln(zeitplanNeu = true){',
        'blinzelAbspielen':'function blinzelAbspielen(schritte, idx, zeitplanNeu){',
        'blinzelWeiterPlanen':'function blinzelWeiterPlanen(){',
    }.items():
        try:
            _,_,body=extract_function(text,sig,name)
            funcs[name]={'sha256':hashlib.sha256(body.encode()).hexdigest(),'body':body}
        except Exception as exc:
            funcs[name]={'error':repr(exc)}
    rows=[]
    for i,line in enumerate(text.splitlines(),1):
        if any(k in line for k in ('BLINK_','blinzelPhase','blinzelTimeout')):
            rows.append({'line':i,'text':line})
    report={'schema':'GO_AVATAR_EYE_BLINK_FUNCTION_FORENSICS/v1','source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'functions':funcs,'anchors':rows}
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
