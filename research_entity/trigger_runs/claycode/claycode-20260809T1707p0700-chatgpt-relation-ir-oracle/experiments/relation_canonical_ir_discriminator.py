from __future__ import annotations
from lark import Lark, Transformer
import hashlib, json, random, time

RELATIONS = {
    'depends': {'arity': 2, 'class': 'semantic_relation'},
    'may_reference': {'arity': 2, 'class': 'semantic_relation'},
    '4B_emits': {'arity': 2, 'class': 'semantic_relation'},
}

GRAMMARS = {
'declared_bare': r'''
?start: expr
?expr: atom REL atom -> binrel
?atom: REF -> ref | IDENT -> sym
REL: "depends"|"may_reference"|"4B_emits"
REF: /@[A-Za-z_][A-Za-z0-9_\.\/-]*/
IDENT: /[A-Za-z_][A-Za-z0-9_.-]*/
%import common.WS
%ignore WS
''',
'disjoint_sigil': r'''
?start: expr
?expr: atom REL atom -> binrel
?atom: REF -> ref | IDENT -> sym
REL: /\^(depends|may_reference|4B_emits)/
REF: /@[A-Za-z_][A-Za-z0-9_\.\/-]*/
IDENT: /[A-Za-z_][A-Za-z0-9_.-]*/
%import common.WS
%ignore WS
''',
'generic_call': r'''
?start: relation_call
relation_call: "relation" "(" STRING "," atom "," atom ")" -> callrel
?atom: REF -> ref | IDENT -> sym
REF: /@[A-Za-z_][A-Za-z0-9_\.\/-]*/
IDENT: /[A-Za-z_][A-Za-z0-9_.-]*/
%import common.ESCAPED_STRING -> STRING
%import common.WS
%ignore WS
'''
}

class Lower(Transformer):
    def ref(self, xs): return {'kind':'ref','id':str(xs[0])}
    def sym(self, xs): return {'kind':'symbol','id':str(xs[0])}
    def binrel(self, xs):
        lhs, rel, rhs = xs
        rid = str(rel)
        if rid.startswith('^'): rid = rid[1:]
        return canonical_relation(rid, lhs, rhs)
    def callrel(self, xs):
        raw, lhs, rhs = xs
        return canonical_relation(json.loads(str(raw)), lhs, rhs)

def canonical_relation(rid, lhs, rhs):
    decl = RELATIONS.get(rid)
    if decl is None: raise ValueError('undeclared_relation:'+rid)
    return {'node':'Relation','relation_id':rid,'relation_class':decl['class'],'arity':decl['arity'],'operands':[lhs,rhs],'authority':'NONE','semantic_version':1}

def semantic_hash(ast):
    payload=json.dumps(ast,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()

PARSERS={k:Lark(g,parser='lalr',lexer='contextual',start='start') for k,g in GRAMMARS.items()}
LOWER=Lower()
CASES=[
 ('depends_symbols','x depends y','x ^depends y','relation("depends",x,y)'),
 ('depends_ref_rhs','x depends @foo','x ^depends @foo','relation("depends",x,@foo)'),
 ('may_reference','effect.Intent may_reference capability_id','effect.Intent ^may_reference capability_id','relation("may_reference",effect.Intent,capability_id)'),
 ('digit_relation','model4B 4B_emits EffectIntent','model4B ^4B_emits EffectIntent','relation("4B_emits",model4B,EffectIntent)'),
]
rows=[]
for name,d,s,g in CASES:
    hashes={}; asts={}
    for candidate,src in [('declared_bare',d),('disjoint_sigil',s),('generic_call',g)]:
        ast=LOWER.transform(PARSERS[candidate].parse(src)); asts[candidate]=ast; hashes[candidate]=semantic_hash(ast)
    rows.append({'case':name,'hashes':hashes,'equal':len(set(hashes.values()))==1,'ast':asts['generic_call']})
unknown={'declared_bare':'x invented_relation y','disjoint_sigil':'x ^invented_relation y','generic_call':'relation("invented_relation",x,y)'}
fail_closed={}
for candidate,src in unknown.items():
    try: fail_closed[candidate]={'rejected':False,'ast':LOWER.transform(PARSERS[candidate].parse(src))}
    except Exception as e: fail_closed[candidate]={'rejected':True,'error':type(e).__name__}
refs={'declared_bare':'x depends @research_entity/global/x','disjoint_sigil':'x ^depends @research_entity/global/x','generic_call':'relation("depends",x,@research_entity/global/x)'}
ref_ok={}
for candidate,src in refs.items():
    try: ref_ok[candidate]=LOWER.transform(PARSERS[candidate].parse(src))['operands'][1]['kind']=='ref'
    except Exception: ref_ok[candidate]=False
random.seed(20260809); ws_trials=3000; ws_pass={k:0 for k in PARSERS}
base={'declared_bare':'x depends y','disjoint_sigil':'x ^depends y','generic_call':'relation("depends",x,y)'}
base_hash={k:semantic_hash(LOWER.transform(PARSERS[k].parse(v))) for k,v in base.items()}
for _ in range(ws_trials):
    a=' '*random.randint(1,4); b=' '*random.randint(1,4)
    variants={'declared_bare':f'x{a}depends{b}y','disjoint_sigil':f'x{a}^depends{b}y','generic_call':f'relation({a}"depends"{b},{a}x{b},{a}y{b})'}
    for k,src in variants.items():
        try: ws_pass[k]+=semantic_hash(LOWER.transform(PARSERS[k].parse(src)))==base_hash[k]
        except Exception: pass
bench_n=5000; latency={}
for k,src in base.items():
    t0=time.perf_counter_ns()
    for _ in range(bench_n): LOWER.transform(PARSERS[k].parse(src))
    latency[k]={'iterations':bench_n,'mean_us':(time.perf_counter_ns()-t0)/bench_n/1000}
result={'experiment':'typed-canonical-relation-ir-discriminator','evidence_class':'local_executable_proxy','oracle':'surface -> typed canonical Relation IR -> semantic_hash','equivalence_cases':rows,'equivalence_pass':sum(r['equal'] for r in rows),'equivalence_total':len(rows),'unknown_relation_fail_closed':fail_closed,'existing_ref_operand_preserved':ref_ok,'whitespace_trials_per_candidate':ws_trials,'whitespace_hash_preservation':ws_pass,'latency_proxy':latency,'surface_bytes':{k:len(v.encode()) for k,v in base.items()},'semantic_boundary':'Relation resolution creates semantic identity only; authority remains NONE and external capability/commit checks remain separate.','limitations':['not full 86-chunk N/S/D corpus','not production BASE parser','not Qwen-4B reader-cost test','not Ubuntu target-host receipt','no E2B execution in this session']}
print(json.dumps(result,indent=2,sort_keys=True))
