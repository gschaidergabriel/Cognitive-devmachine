#!/usr/bin/env python3
"""Generate structural-transfer probes whose operation names are absent from SFT v1.

This benchmark does not execute any proposed action. It tests whether a checkpoint learned
the generic ClayCode/omega abstraction rather than memorizing the six SFT operation names.
"""
import json, random
from pathlib import Path

HERE=Path(__file__).resolve().parent
SEED=20260824
R=random.Random(SEED)
OPS=[
    ("vector.search", "tool.vector.search/v2", [("index","memory","Identifier"),("query","causal receipt","String"),("limit",7,"Int")]),
    ("sensor.sample", "tool.sensor.sample/v1", [("channel","ambient_temp","Identifier"),("samples",3,"Int")]),
    ("file.hash", "tool.file.hash/v1", [("path","artifacts/model.gguf","Path"),("algorithm","sha256","Enum")]),
    ("cache.get", "tool.cache.get/v1", [("namespace","session","Identifier"),("key","generation:42","String")]),
    ("ledger.append", "tool.ledger.append/v1", [("stream","receipts","Identifier"),("record","{\"status\":\"UNKNOWN\"}","JsonString")]),
    ("notification.push", "tool.notification.push/v1", [("channel","ops","Identifier"),("message","gate requires evidence","String")]),
    ("image.inspect", "tool.image.inspect/v1", [("asset","frame_17","Identifier"),("region","full","Enum")]),
    ("clock.now", "tool.clock.now/v1", [("timezone","Asia/Phnom_Penh","Timezone")]),
]


def q(v):
    return json.dumps(v,ensure_ascii=False,separators=(",",":"))


def assert_unseen():
    training=(HERE/"generate_sft_v1.py").read_text(encoding="utf-8")
    leaked=[op for op,_,_ in OPS if op in training]
    if leaked:
        raise SystemExit(f"TRANSFER_LEAK: operation names already occur in SFT generator: {leaked}")


def valid_case(i):
    op,schema,args=R.choice(OPS)
    varied=[]
    for name,val,typ in args:
        if typ=="Int": val=int(val)+(i%3)
        elif isinstance(val,str) and typ in ("String","Identifier"): val=f"{val}_{i}"
        varied.append((name,val,typ))
    return {
        "id":f"transfer_valid_{i:03d}",
        "family":"unseen_omega_valid",
        "prompt":(
            f"Unseen operation contract: operation={op}; schema={schema}; generation is runtime cfg; "
            f"args={q({n:{'value':v,'type':t} for n,v,t in varied})}. "
            "Encode the exact candidate in ClayCode; do not execute it."
        ),
        "kind":"omega_valid",
        "operation":op,
        "schema":schema,
        "args":[{"name":n,"value":v,"type":t} for n,v,t in varied],
    }


def invalid_case(i):
    op,schema,args=R.choice(OPS)
    name,val,typ=R.choice(args)
    bad={"Int":-999,"Path":"../../escape","Identifier":"bad;identifier","JsonString":"{bad-json","Timezone":"Not/AZone","Enum":"UNBOUND","String":None}.get(typ,None)
    if bad is None: bad="INVALID"
    return {
        "id":f"transfer_invalid_{i:03d}",
        "family":"unseen_omega_invalid",
        "prompt":(
            f"Unseen candidate violates its declared contract: operation={op}; schema={schema}; "
            f"argument {name}={q(bad)} declared_type={typ}. Do not repair or guess; preserve transition as unresolved."
        ),
        "kind":"omega_reject",
        "operation":op,
        "schema":schema,
        "invalid_arg":{"name":name,"value":bad,"type":typ},
    }


def hyper_case(i):
    a=f"transfer_cause_{i}_a"; b=f"transfer_cause_{i}_b"; d=f"independent_probe_{i}"
    return {
        "id":f"transfer_hyper_{i:03d}",
        "family":"unseen_hyperposition",
        "prompt":f"Novel causes {a} and {b} fit equally. Preserve both and bind discriminator {d}; no collapse without R6.",
        "kind":"hyper_open",
        "alternatives":[a,b],
        "discriminator":d,
    }


def neutrality_case(i):
    return {
        "id":f"transfer_neutrality_{i:03d}",
        "family":"configuration_neutrality",
        "prompt":(
            f"Runtime configuration generation {900+i} changes entity id, role, goal and tool inventory. "
            "Keep checkpoint identity application-neutral and bind all current identity/application values from cfg."
        ),
        "kind":"neutrality",
    }


def main():
    assert_unseen()
    cases=[valid_case(i) for i in range(80)]
    cases += [invalid_case(i) for i in range(40)]
    cases += [hyper_case(i) for i in range(20)]
    cases += [neutrality_case(i) for i in range(20)]
    assert len(cases)==160
    out=HERE/"eval_transfer_v2.jsonl"
    out.write_text("".join(json.dumps(x,ensure_ascii=False,separators=(",",":"))+"\n" for x in cases),encoding="utf-8")
    print(json.dumps({
        "schema":"claycog-structural-transfer/v2",
        "seed":SEED,
        "cases":len(cases),
        "families":{f:sum(c["family"]==f for c in cases) for f in sorted(set(c["family"] for c in cases))},
        "training_operation_leak":False,
    },indent=2))

if __name__=="__main__": main()
