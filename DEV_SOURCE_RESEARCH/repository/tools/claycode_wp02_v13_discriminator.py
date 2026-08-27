#!/usr/bin/env python3
"""WP-02 discriminator for V13 generic call-safe dotted relation grammar.

This is a parser/canonicalization research gate, not a BASE release gate. It:
- reproduces the V10 horizontal-whitespace semantic counterexample;
- requires exact G9 V3 + Dialect V3 acceptance;
- checks V10/V13 semantic equivalence on the current admitted corpus;
- exercises generic dotted relations and call whitespace invariance;
- preserves the admitted bare-owns / rejected bare-lowers boundary;
- runs parser-level canonical equivalence/discrimination checks and bounded lexical overlap scan.

Use --require-strict on the Ubuntu/current-main executor. Without interegular, a sandbox
may report STRICT_DEPENDENCY_MISSING only if strict LALR reaches that lexer dependency
without first raising a GrammarError.
"""
from __future__ import annotations
import argparse, hashlib, json, random, re, string, sys
from datetime import datetime, timezone
from pathlib import Path
from lark import Lark, Token
from lark.exceptions import GrammarError, LexError

ROOT=Path(__file__).resolve().parents[1]
V10=ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V10_OPERATOR_FN_DOTTED.lark'
V13=ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V13_GENERIC_DOTTED_CALLSAFE.lark'
G9=ROOT/'research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay'
DIALECT=ROOT/'research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay'
STRUCT={"{","}","(",")","[","]",",",";",":"}

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def canon(n):
    if n is None:return None
    if isinstance(n,Token):
        v=str(n)
        if n.type=='NEWLINE' or v in STRUCT:return None
        return {'token':n.type,'value':v}
    out=[]
    for c in n.children:
        x=canon(c)
        if x is not None:out.append(x)
    return {'node':str(n.data),'children':out}
def stable(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sem(p,s):return sha(stable(canon(p.parse(s))))
def parser(g):return Lark(g,parser='lalr',lexer='contextual',start='start',keep_all_tokens=True)

def run(require_strict:bool=False):
    g10=V10.read_text(encoding='utf-8');g13=V13.read_text(encoding='utf-8')
    p10=parser(g10);p13=parser(g13)
    checks=[]
    def ck(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
    try:
        Lark(g13,parser='lalr',lexer='contextual',start='start',strict=True)
        strict_state='STRICT_PASS'
    except GrammarError as e:
        strict_state='GRAMMAR_ERROR:'+str(e)
    except LexError as e:
        if 'interegular must be installed' in str(e):strict_state='STRICT_DEPENDENCY_MISSING:'+str(e)
        else:strict_state='LEXER_ERROR:'+str(e)
    except Exception as e:strict_state=type(e).__name__+':'+str(e)
    ck('strict_parser_table_state',strict_state=='STRICT_PASS' or strict_state.startswith('STRICT_DEPENDENCY_MISSING:'),strict_state)
    if require_strict:ck('strict_required',strict_state=='STRICT_PASS',strict_state)
    for path in (G9,DIALECT):
        s=path.read_text(encoding='utf-8')
        try:p13.parse(s);ok=True;detail='accepted'
        except Exception as e:ok=False;detail=f'{type(e).__name__}:{getattr(e,"line",None)}:{getattr(e,"column",None)}'
        ck('parse_'+path.name,ok,detail)
        if ok:ck('v10_v13_semantic_equivalence_'+path.name,sem(p10,s)==sem(p13,s),{'v10':sem(p10,s),'v13':sem(p13,s)})
    positive={
      'bare_needle_owns_operand':'rule 4B_need_not_learn Needle.owns\n',
      'dotted_prefix_owns':'rule Needle.owns X\n',
      'dotted_prefix_lowers_chain':'rule Needle.lowers X -> Y\n',
      'typed_fn_add':'fn add(a:Int,b:Int)->Int=a+b\n',
      'typed_fn_call':'fn add(a:Int,b:Int)->Int=a+b\nfn twice(x:Int)->Int=add(x,x)\n',
      'exact_operator_gt':'rule x>0\n',
      'record_semicolon_block':'record X { a:Int; b:Int }\n',
    }
    for n,s in positive.items():
        try:p13.parse(s);ok=True
        except Exception:ok=False
        ck('legacy_'+n,ok)
    try:p13.parse('rule Needle.lowers\n');ok=False
    except Exception:ok=True
    ck('legacy_bare_needle_lowers',ok)
    tight='rule Needle.owns(X)\n';spaced='rule Needle.owns (X)\n'
    ck('v10_whitespace_counterexample_reproduced',sem(p10,tight)!=sem(p10,spaced),{'tight':sem(p10,tight),'spaced':sem(p10,spaced)})
    for q in ['Needle','Foo','alpha.beta','x_y.Z9']:
        hs=[sem(p13,f'rule {q}.owns{ws}(X)\n') for ws in ('',' ','    ')]
        ck('v13_call_whitespace_'+q,len(set(hs))==1,hs)
    rng=random.Random(130013)
    def seg():return rng.choice(string.ascii_letters+'_')+''.join(rng.choice(string.ascii_letters+string.digits+'_') for _ in range(rng.randrange(0,9)))
    bad=None
    for i in range(2500):
        q='.'.join(seg() for _ in range(rng.randrange(1,5)))
        for rel in ('owns','lowers'):
            try:p13.parse(f'rule {q}.{rel} X\n')
            except Exception as e:bad={'i':i,'qid':q,'rel':rel,'error':type(e).__name__};break
        if bad:break
    ck('fuzz_generic_relations_2500x2',bad is None,bad)
    bad=None
    for i in range(1000):
        q='.'.join(seg() for _ in range(rng.randrange(1,5)))
        try:hs=[sem(p13,f'rule {q}.owns{ws}(X)\n') for ws in ('',' ','    ')];ok=len(set(hs))==1
        except Exception:ok=False
        if not ok:bad={'i':i,'qid':q};break
    ck('fuzz_owns_call_whitespace_1000',bad is None,bad)
    for q in ['Foo','alpha.beta','Needle','x_y.Z9']:
        try:p13.parse(f'rule {q}.owns\n');owns=True
        except Exception:owns=False
        try:p13.parse(f'rule {q}.lowers\n');lowers_rejected=False
        except Exception:lowers_rejected=True
        ck('bare_owns_admitted_'+q,owns);ck('bare_lowers_rejected_'+q,lowers_rejected)
    eq=[
      ('space_comment','rule x>0\n','rule   x > 0 // ignored\n'),
      ('blank_lines','record X {\na:Int\nb:Int\n}\n','record X {\n\na:Int\n\nb:Int\n\n}\n'),
      ('separator','record X {\na:Int\nb:Int\n}\n','record X { a:Int; b:Int }\n'),
    ]
    diff=[
      ('gt_lt','rule x>0\n','rule x<0\n'),('plus_minus','rule x+1\n','rule x-1\n'),
      ('true_false','rule true\n','rule false\n'),('arg_order','rule f(a,b)\n','rule f(b,a)\n'),
      ('dotted_rel','rule Needle.lowers X\n','rule Needle.owns X\n'),
    ]
    for n,a,b in eq:ck('canonical_eq_'+n,sem(p13,a)==sem(p13,b))
    for n,a,b in diff:ck('canonical_diff_'+n,sem(p13,a)!=sem(p13,b))
    pt=Lark(g13,parser='lalr',lexer='basic',start='start')
    terms=[]
    for t in pt.terminals:
        try:rx=re.compile('^(?:'+t.pattern.to_regexp()+')$')
        except re.error:continue
        terms.append((t.name,t.priority,rx))
    candidates={'module','version','status','parent','import','interface','dialect','law','rule','invariant','class','type','record','tensor','codec','surface','metric','hash','needle','cycle','if','or','iff','requires','in','subset_of','lowers','true','false','owns','Foo','alpha_1','Needle','0','-1','1.25','@a/b','Needle.owns','Needle.lowers','Foo.owns','Foo.lowers','alpha.beta.owns','alpha.beta.lowers','4B_emits','4B_need_not_learn','never_implies','is_explanation_of_derivation',' ','\n'}
    for _ in range(2000):
        q='.'.join(seg() for _ in range(rng.randrange(1,4)));candidates.update([q,q+'.owns',q+'.lowers'])
    collisions=[]
    for s in candidates:
        by={}
        for n,pr,rx in terms:
            if rx.fullmatch(s):by.setdefault(pr,[]).append(n)
        for pr,names in by.items():
            if len(names)>1:collisions.append({'s':s,'priority':pr,'tokens':sorted(names)})
    ck('bounded_same_priority_lexical_collision_scan',not collisions,collisions[:20])
    return {
      'schema_version':'1.1','experiment':'CC-WP02 V13 generic dotted-prefix call-safe discriminator',
      'created_at':datetime.now(timezone.utc).isoformat(),'candidate_path':str(V13.relative_to(ROOT)),
      'candidate_sha256':sha(V13.read_bytes()),'candidate_bytes':len(V13.read_bytes()),
      'source_refs':{
        'v10_path':str(V10.relative_to(ROOT)),'v10_sha256':sha(V10.read_bytes()),
        'g9_path':str(G9.relative_to(ROOT)),'g9_sha256':sha(G9.read_bytes()),
        'dialect_path':str(DIALECT.relative_to(ROOT)),'dialect_sha256':sha(DIALECT.read_bytes())},
      'runtime':{'python':sys.version.split()[0],'lark':__import__('lark').__version__,'interegular':strict_state=='STRICT_PASS'},
      'strict_state':strict_state,'require_strict':require_strict,
      'checks':checks,'passed':sum(x['pass'] for x in checks),'total':len(checks),'pass':all(x['pass'] for x in checks),
      'counts_as_wp02_pass':False,'counts_as_target_acceptance':False,'promotion_allowed':False,
      'counterexample':'V10 makes horizontal whitespace semantically active for Needle.owns(X) vs Needle.owns (X): call versus dotted-prefix relation.',
      'candidate_delta':'Generic qualified-id dotted relation token plus call-safe lookahead; removes Needle-specific lexical hardcoding while preserving current corpus semantics and avoiding the qid/DOT LALR conflict.',
      'authority_invariant':'model output != execution authority'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--require-strict',action='store_true');ap.add_argument('--output');a=ap.parse_args()
    r=run(a.require_strict);text=json.dumps(r,indent=2,ensure_ascii=False)+'\n';print(text,end='')
    if a.output:Path(a.output).write_text(text,encoding='utf-8')
    if not r['pass']:raise SystemExit(1)
if __name__=='__main__':main()
