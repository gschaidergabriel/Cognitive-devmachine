#!/usr/bin/env python3
"""Reproduce the exact-v1 train/validation fingerprint leakage without model execution."""
import hashlib, json
from generate_sft_v1 import build

def fp(row):
    raw=json.dumps(row["messages"],ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()

def main():
    rows=build(); train=rows[:1485]; valid=rows[1485:]
    tf=[fp(x) for x in train]; vf=[fp(x) for x in valid]
    ts=set(tf); vs=set(vf)
    valid_rows_seen_in_train=sum(x in ts for x in vf)
    by={}
    for family in sorted({x["family"] for x in rows}):
        fam=[x for x in rows if x["family"]==family]
        by[family]={"rows":len(fam),"unique_messages":len({fp(x) for x in fam})}
    report={
      "schema":"claycog-v1-leakage-audit/v1",
      "total_rows":len(rows),"total_unique_messages":len({fp(x) for x in rows}),
      "train_rows":len(train),"train_unique_messages":len(ts),"train_duplicate_rows":len(train)-len(ts),
      "validation_rows":len(valid),"validation_unique_messages":len(vs),"validation_duplicate_rows":len(valid)-len(vs),
      "train_validation_unique_overlap":len(ts & vs),
      "validation_rows_exactly_seen_in_train":valid_rows_seen_in_train,
      "validation_independent":valid_rows_seen_in_train==0,
      "by_family":by,
    }
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0 if report["validation_independent"] else 2

if __name__=="__main__": raise SystemExit(main())
