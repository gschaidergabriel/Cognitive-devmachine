#!/usr/bin/env python3
"""Deterministic closure audit for ClayCode Cognition v1 training targets.

Builds the in-memory SFT corpus from the canonical generator and requires every assistant
call to be accepted by validate_sft_v1, which in turn binds to intrinsics_v1.py. This is
independent of Together and never executes an omega/effect candidate.
"""
import json
from collections import Counter
from generate_sft_v1 import build
from validate_sft_v1 import iter_calls, outside_strings, validate_code
from intrinsics_v1 import ALLOWED_INTRINSICS

def main():
    rows=build(); bad=[]; calls=Counter(); unknown=Counter()
    for idx,row in enumerate(rows):
        out=row["messages"][-1]["content"]
        errors=validate_code(out)
        if errors: bad.append({"index":idx,"family":row["family"],"errors":errors})
        for name,_arity in iter_calls(outside_strings(out)):
            calls[name]+=1
            if name not in ALLOWED_INTRINSICS: unknown[name]+=1
    report={"schema":"claycog-intrinsic-closure/v1","examples":len(rows),"unique_intrinsics_used":sorted(calls),"intrinsic_call_counts":dict(sorted(calls.items())),"unknown_intrinsics":dict(sorted(unknown.items())),"invalid_examples":len(bad),"sample_failures":bad[:20],"ok":not bad and not unknown}
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0 if report["ok"] else 1

if __name__=="__main__": raise SystemExit(main())
