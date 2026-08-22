#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path

def load(path):
    rows=[]
    for n,line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(),1):
        row=json.loads(line); rows.append((n,row['messages']))
    return rows

def fp(ms): return hashlib.sha256(json.dumps(ms,ensure_ascii=False,separators=(',',':'),sort_keys=True).encode()).hexdigest()
def user(ms): return ms[1]['content']

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('train'); ap.add_argument('validation'); args=ap.parse_args()
    tr,va=load(args.train),load(args.validation); tf=[fp(ms) for _,ms in tr]; vf=[fp(ms) for _,ms in va]; tu=[user(ms) for _,ms in tr]; vu=[user(ms) for _,ms in va]
    report={'schema':'claycog-corpus-split-gate/v2','train_rows':len(tr),'validation_rows':len(va),'train_unique_rows':len(set(tf)),'validation_unique_rows':len(set(vf)),'exact_row_overlap':len(set(tf)&set(vf)),'exact_user_overlap':len(set(tu)&set(vu)),'train_duplicate_rows':len(tf)-len(set(tf)),'validation_duplicate_rows':len(vf)-len(set(vf))}
    report['ok']=(len(tr)==1620 and len(va)==180 and report['train_duplicate_rows']==0 and report['validation_duplicate_rows']==0 and report['exact_row_overlap']==0 and report['exact_user_overlap']==0)
    print(json.dumps(report,indent=2)); return 0 if report['ok'] else 1
if __name__=='__main__': raise SystemExit(main())
