#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, hashlib, json, random, sys, time
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = next((p for p in HERE.parents if (p / "tools" / "claycode_base_frontend.py").exists()), None)
if ROOT is None:
    raise SystemExit("repo root not found")
sys.path.insert(0, str(ROOT / "tools"))
import claycode_base_frontend as front  # type: ignore

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
CANDIDATE = HERE.parent / "WP03_TYPED_IR_CANDIDATE.clay"
TYPED_DOMAIN = b"ClayCodeTypedIR/v0.1\x00"

class CCTypeError(ValueError):
    pass

def require(cond, msg):
    if not cond:
        raise CCTypeError(msg)

def jbytes(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def typed_normalize(node):
    if isinstance(node, list):
        return [typed_normalize(x) for x in node]
    if not isinstance(node, dict):
        return node
    if "token" in node:
        if node["token"] in {"COMMA","LBRACE","RBRACE","COLON"}:
            return None
        return node
    kind = node.get("kind")
    children = [typed_normalize(x) for x in node.get("children", [])]
    children = [x for x in children if x is not None]
    if kind == "record_block":
        fields = [x for x in children if isinstance(x, dict) and x.get("kind") == "field"]
        fields.sort(key=jbytes)
        return {"kind": "record_block", "fields": fields}
    if kind == "set":
        elems = [x for x in children if not (isinstance(x, dict) and x.get("token") in {"COMMA","LBRACE","RBRACE"})]
        elems.sort(key=jbytes)
        return {"kind": "set", "elements": elems}
    return {"kind": kind, "children": children}

def typed_hash(ast):
    return hashlib.sha256(TYPED_DOMAIN + jbytes(typed_normalize(ast))).hexdigest()

def compile_source(src, grammar):
    return front.compile_frontend(src, grammar, strict=False)

def validate(name, x):
    if name == "InitiativePulse":
        require(0 <= x["amplitude"] <= 0.12, "initiative.amplitude")
    elif name == "WebEvidenceClay":
        require(x["authority"] == "UNTRUSTED_EXTERNAL_DATA", "web.authority")
        require(x["instruction_authority"] == "NONE", "web.instruction_authority")
        require(x["effect_authority"] == "NONE", "web.effect_authority")
        require(x["executable"] is False, "web.executable")
    elif name == "AuthenticatedDirectMessage":
        require(x["authority"] == "AUTHENTICATED_DIRECT_MESSAGE", "direct.authority")
        require(bool(x["token_scope"]), "direct.token_scope")
    elif name == "SemanticRuntimeIdentity":
        require(x["semantic_id"] != x["runtime_version_id"], "identity.separation")
    elif name == "HyperRelation":
        require(len(x["roles"]) >= 2 and len(set(x["roles"])) == len(x["roles"]), "hyperrelation.roles")
        require(x["topology_kind"] in {"SEMANTIC","ACTIVE","COORDINATION","PHYSICAL"}, "hyperrelation.topology")
    elif name == "MeasurementReceipt":
        require(x["stage"] in {"CANDIDATE","COMPETITION","IGNITION","BROADCAST","DELIVERY","RECONSTRUCTION","UPTAKE","CAUSAL_USE","OUTCOME","REENTRY"}, "measurement.stage")
        require(bool(x["provenance_refs"]), "measurement.provenance")
    elif name == "CapabilityToken":
        require(x["runtime_representation"] in {"OWNED_HANDLE","BORROWED_HANDLE","OPAQUE_HOST_REF"}, "capability.runtime_representation")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output")
    args = ap.parse_args()
    started = time.perf_counter_ns()
    grammar = GRAMMAR.read_text(encoding="utf-8")
    source = CANDIDATE.read_text(encoding="utf-8")
    candidate = compile_source(source, grammar)

    record_a = "module clay.test\nrecord X {\n a:Int\n b:Ref\n}\n"
    record_b = "module clay.test\nrecord X {\n b:Ref\n a:Int\n}\n"
    set_a = "module clay.test\nrecord X { s:Set<Ref> }\nrule X.s={A,B}\n"
    set_b = "module clay.test\nrecord X { s:Set<Ref> }\nrule X.s={B,A}\n"
    ra, rb = compile_source(record_a, grammar), compile_source(record_b, grammar)
    sa, sb = compile_source(set_a, grammar), compile_source(set_b, grammar)

    fixtures = {
        "InitiativePulse":{"amplitude":0.12},
        "WebEvidenceClay":{"authority":"UNTRUSTED_EXTERNAL_DATA","instruction_authority":"NONE","effect_authority":"NONE","executable":False},
        "AuthenticatedDirectMessage":{"authority":"AUTHENTICATED_DIRECT_MESSAGE","token_scope":["chat"]},
        "SemanticRuntimeIdentity":{"semantic_id":"goal:a","runtime_version_id":"goal:a@42"},
        "HyperRelation":{"roles":["source","context","target"],"topology_kind":"SEMANTIC"},
        "MeasurementReceipt":{"stage":"CAUSAL_USE","provenance_refs":["e:1"]},
        "CapabilityToken":{"runtime_representation":"OWNED_HANDLE"},
    }
    mutations = {
        "InitiativePulse":lambda x:x.update(amplitude=0.121),
        "WebEvidenceClay":lambda x:x.update(effect_authority="ALLOW"),
        "AuthenticatedDirectMessage":lambda x:x.update(authority="UNTRUSTED_EXTERNAL_DATA"),
        "SemanticRuntimeIdentity":lambda x:x.update(runtime_version_id=x["semantic_id"]),
        "HyperRelation":lambda x:x.update(roles=["same","same"]),
        "MeasurementReceipt":lambda x:x.update(stage="MAGIC"),
        "CapabilityToken":lambda x:x.update(runtime_representation="COPYABLE_TEXT"),
    }

    pos=neg=0
    failures=[]
    for name, fx in fixtures.items():
        try:
            validate(name, copy.deepcopy(fx)); pos += 1
        except Exception as e:
            failures.append({"case":"positive:"+name,"error":str(e)})
        bad=copy.deepcopy(fx); mutations[name](bad)
        try:
            validate(name,bad)
            failures.append({"case":"negative:"+name,"error":"accepted"})
        except CCTypeError:
            neg += 1

    rng=random.Random(230810)
    fuzz_n=2000
    fuzz_rejected=0
    for _ in range(fuzz_n):
        x=copy.deepcopy(fixtures["WebEvidenceClay"])
        field=rng.choice(["authority","instruction_authority","effect_authority","executable"])
        if field=="authority": x[field]=rng.choice(["AUTHENTICATED_DIRECT_MESSAGE","TRUSTED_INTERNAL_STATE","ROOT"])
        elif field=="instruction_authority": x[field]=rng.choice(["USER","SYSTEM","ALLOW"])
        elif field=="effect_authority": x[field]=rng.choice(["ALLOW","WRITE","EXECUTE"])
        else: x[field]=True
        try: validate("WebEvidenceClay",x)
        except CCTypeError: fuzz_rejected += 1

    result = {
        "schema_version":"1.0",
        "experiment":"CC-WP03 typed IR normalization + owner-fixed type expressibility",
        "candidate_frontend_semantic_hash":candidate["semantic_hash"],
        "candidate_contract_hash":candidate["contract_hash"],
        "record_field_order_frontend_hash_equal":ra["semantic_hash"] == rb["semantic_hash"],
        "record_field_order_typed_hash_equal":typed_hash(ra["canonical_ast"]) == typed_hash(rb["canonical_ast"]),
        "set_order_frontend_hash_equal":sa["semantic_hash"] == sb["semantic_hash"],
        "set_order_typed_hash_equal":typed_hash(sa["canonical_ast"]) == typed_hash(sb["canonical_ast"]),
        "positive_typed_cases_passed":pos,
        "positive_typed_cases_total":len(fixtures),
        "negative_typed_cases_rejected":neg,
        "negative_typed_cases_total":len(fixtures),
        "web_authority_fuzz_rejected":fuzz_rejected,
        "web_authority_fuzz_total":fuzz_n,
        "elapsed_ns":time.perf_counter_ns()-started,
        "scope_guard":"LOCAL/PROXY research discriminator only. Does not close CC-WP03; target-VPS production typed-IR/checker receipts remain mandatory.",
        "failures":failures,
    }
    result["pass"] = (
        not result["record_field_order_frontend_hash_equal"]
        and result["record_field_order_typed_hash_equal"]
        and not result["set_order_frontend_hash_equal"]
        and result["set_order_typed_hash_equal"]
        and pos==len(fixtures) and neg==len(fixtures)
        and fuzz_rejected==fuzz_n and not failures
    )
    text=json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text,encoding="utf-8")
    print(text,end="")
    return 0 if result["pass"] else 1

if __name__=="__main__":
    raise SystemExit(main())
