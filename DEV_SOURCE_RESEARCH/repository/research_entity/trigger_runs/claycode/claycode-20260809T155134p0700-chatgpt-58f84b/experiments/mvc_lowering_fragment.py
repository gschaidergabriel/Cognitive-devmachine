from __future__ import annotations
from lark import Lark
import json, hashlib, pathlib, subprocess, tempfile, sys, re

GRAMMAR = r'''
start: statement+
?statement: module_decl | record_decl | rule_decl
module_decl: "module" qid
record_decl: "record" IDENT [type_params] "{" field* "}"
field: IDENT ":" type_expr [";"]
type_params: "<" type_expr ("," type_expr)* ">"
?type_expr: union_type ["?"]
?union_type: type_atom ("|" type_atom)*
?type_atom: qid [type_params] | "Set" "<" type_expr ">" | "Ordered" "<" type_expr ">" | "Map" "<" type_expr "," type_expr ">"
rule_decl: "rule" bool_expr "=>" qid
?bool_expr: or_expr
?or_expr: and_expr ("||" and_expr)*
?and_expr: rel_expr ("&&" rel_expr)*
?rel_expr: atom (("in"|"="|"=="|"!="|">"|"<") atom)?
?atom: qid | list | SIGNED_NUMBER | STRING | BOOLEAN | "(" bool_expr ")"
list: "[" [atom ("," atom)*] "]"
qid: IDENT ("." IDENT)*
BOOLEAN: "true" | "false"
IDENT: /[A-Za-z_][A-Za-z0-9_-]*/
%import common.ESCAPED_STRING -> STRING
%import common.SIGNED_NUMBER
%import common.WS
%ignore WS
'''

SOURCE = r'''
module claycode.exp.mvc.v1
record TrainingExample {tier:GOLD|SILVER|BRONZE; trusted:Boolean;}
record LearnerBudget {cpu_ms:Int; ram_bytes:Int; over_budget:Boolean;}
record Candidate {eval_pass:Boolean; eval_fail:Boolean; within_budget:Boolean; open_set_ok:Boolean;}
record RollbackState {request:Boolean; lkg_available:Boolean;}
record EffectGate {request:Boolean; capability_valid:Boolean; capability_missing:Boolean; witness_aw:Boolean; witness_cw:Boolean;}
rule example.tier in [GOLD,SILVER] && example.trusted = true => ADMIT
rule example.tier in [BRONZE] => REJECT
rule candidate.eval_pass = true && candidate.within_budget = true && candidate.open_set_ok = true => PROMOTE
rule candidate.eval_fail = true || budget.over_budget = true => KEEP_CURRENT
rule rollback.request = true && rollback.lkg_available = true => ROLLBACK
rule effect.request = true && effect.capability_valid = true && effect.witness_aw = true && effect.witness_cw = true => COMMIT
rule effect.request = true && effect.capability_missing = true => DENY
'''.strip()

Lark(GRAMMAR, parser="lalr", start="start").parse(SOURCE)
rule_lines=[ln.strip()[5:] for ln in SOURCE.splitlines() if ln.strip().startswith("rule ")]

def split_top(s, op):
    parts=[]; depth=0; start=0; i=0
    while i <= len(s)-len(op):
        ch=s[i]
        if ch in '([': depth += 1
        elif ch in ')]': depth -= 1
        if depth==0 and s.startswith(op,i): parts.append(s[start:i].strip()); start=i+len(op); i += len(op); continue
        i += 1
    parts.append(s[start:].strip()); return parts

def qid_py(tok):
    tok=tok.strip()
    if tok=='true': return 'True'
    if tok=='false': return 'False'
    if re.fullmatch(r'-?\d+(?:\.\d+)?',tok): return tok
    if tok.startswith('"') and tok.endswith('"'): return tok
    if tok.startswith('[') and tok.endswith(']'):
        inside=tok[1:-1].strip(); return '['+','.join(qid_py(x) for x in split_top(inside,','))+']' if inside else '[]'
    if re.fullmatch(r'[A-Z][A-Z0-9_-]*',tok): return repr(tok)
    return f"env.get({tok!r})"

def expr_py(expr):
    expr=expr.strip(); parts=split_top(expr,'||')
    if len(parts)>1: return '('+' or '.join(expr_py(p) for p in parts)+')'
    parts=split_top(expr,'&&')
    if len(parts)>1: return '('+' and '.join(expr_py(p) for p in parts)+')'
    for op,pyop in [(' in ',' in '),(' != ',' != '),(' == ',' == '),(' = ',' == '),(' > ',' > '),(' < ',' < ')]:
        parts=split_top(expr,op)
        if len(parts)==2: return f"({qid_py(parts[0])}{pyop}{qid_py(parts[1])})"
    return qid_py(expr)

compiled=[]
for line in rule_lines:
    lhs_rhs=split_top(line,'=>')
    if len(lhs_rhs)!=2: raise ValueError(line)
    compiled.append((expr_py(lhs_rhs[0]),lhs_rhs[1].strip()))

canonical={"module":"claycode.exp.mvc.v1","rules":[{"predicate_py":p,"action":a} for p,a in compiled],"source_sha256":hashlib.sha256(SOURCE.encode()).hexdigest()}
semantic_hash=hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(',',':')).encode()).hexdigest()
generated=["import json,sys","env=json.loads(sys.stdin.read())","out=[]"]
for pred,action in compiled: generated.append(f"if {pred}: out.append({action!r})")
generated.append("print(json.dumps(out,sort_keys=True))")
generated_code='\n'.join(generated)+'\n'; generated_hash=hashlib.sha256(generated_code.encode()).hexdigest()

cases=[
 ({"example.tier":"GOLD","example.trusted":True},["ADMIT"]),
 ({"example.tier":"SILVER","example.trusted":False},[]),
 ({"example.tier":"BRONZE","example.trusted":True},["REJECT"]),
 ({"candidate.eval_pass":True,"candidate.within_budget":True,"candidate.open_set_ok":True,"candidate.eval_fail":False,"budget.over_budget":False},["PROMOTE"]),
 ({"candidate.eval_pass":True,"candidate.within_budget":False,"candidate.open_set_ok":True,"candidate.eval_fail":False,"budget.over_budget":True},["KEEP_CURRENT"]),
 ({"rollback.request":True,"rollback.lkg_available":True},["ROLLBACK"]),
 ({"effect.request":True,"effect.capability_valid":True,"effect.witness_aw":True,"effect.witness_cw":True,"effect.capability_missing":False},["COMMIT"]),
 ({"effect.request":True,"effect.capability_valid":True,"effect.witness_aw":True,"effect.witness_cw":False,"effect.capability_missing":False},[]),
 ({"effect.request":True,"effect.capability_valid":False,"effect.witness_aw":False,"effect.witness_cw":False,"effect.capability_missing":True},["DENY"]),
]
with tempfile.TemporaryDirectory() as td:
    p=pathlib.Path(td)/'generated.py'; p.write_text(generated_code)
    results=[]
    for i,(env,expected) in enumerate(cases,1):
        cp=subprocess.run([sys.executable,str(p)],input=json.dumps(env),text=True,capture_output=True)
        observed=json.loads(cp.stdout) if cp.returncode==0 else None
        results.append({"case":i,"expected":expected,"observed":observed,"ok":observed==expected and cp.returncode==0,"exit":cp.returncode,"stderr":cp.stderr})
print(json.dumps({"experiment":"ClayCode MVC compiler/lowering fragment","source_sha256":hashlib.sha256(SOURCE.encode()).hexdigest(),"canonical_semantic_hash":semantic_hash,"generated_python_sha256":generated_hash,"tests":results,"passed":sum(r['ok'] for r in results),"total":len(results),"all_pass":all(r['ok'] for r in results),"boundary":"prototype compiler fragment only; not full ClayCode compiler/runtime conformance"},indent=2))
