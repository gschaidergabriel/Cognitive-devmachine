#!/usr/bin/env python3
"""V15 WP-02 discriminator: V13 gates plus comment/EOL trivia safety.

V13 fixed the V10 call-whitespace counterexample and removed Needle-specific lexer
hardcoding. V15 additionally requires that dotted-prefix recognition not activate from
trailing horizontal whitespace or a `//` comment. This remains research evidence only;
--require-strict is mandatory for the Ubuntu/current-main acceptance run.
"""
from __future__ import annotations
import argparse, json, random, string
from datetime import datetime, timezone
from pathlib import Path
from lark import Lark, Token
import claycode_wp02_v13_discriminator as base

ROOT=Path(__file__).resolve().parents[1]
V15=ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V15_GENERIC_DOTTED_TRIVIA_SAFE.lark'
STRUCT={"{","}","(",")","[","]",",",";",":"}

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

def run(require_strict=False):
    base.V13=V15
    result=base.run(require_strict)
    g=V15.read_text(encoding='utf-8')
    p=Lark(g,parser='lalr',lexer='contextual',start='start',keep_all_tokens=True)
    def sem(s):return base.sha(base.stable(canon(p.parse(s))))
    extra=[]
    def ck(name,ok,detail=None):extra.append({'name':name,'pass':bool(ok),'detail':detail})
    cases=[
      ('owns_comment','rule Foo.owns // comment\n',True),
      ('needle_owns_comment','rule Needle.owns // comment\n',True),
      ('owns_tab_comment','rule Foo.owns\t// comment\n',True),
      ('lowers_comment','rule Foo.lowers // comment\n',False),
      ('relation_comment','rule Foo.owns X // comment\n',True),
      ('call_comment','rule Foo.owns (X) // comment\n',True),
      ('owns_spaces_eol','rule Foo.owns    \n',True),
      ('lowers_spaces_eol','rule Foo.lowers    \n',False),
      ('owns_tabs_eol','rule Foo.owns\t\t\n',True),
      ('lowers_tabs_eol','rule Foo.lowers\t\t\n',False),
    ]
    for name,source,want in cases:
        try:p.parse(source);got=True
        except Exception:got=False
        ck('trivia_'+name,got==want,{'got':got,'want':want})
    for q in ['Foo','Needle','alpha.beta','x_y.Z9','module.type']:
        values=[];ok=True
        for suffix in ('',' ','    ','\t','\t\t',' //comment','\t//comment'):
            try:values.append(sem(f'rule {q}.owns{suffix}\n'))
            except Exception as exc:ok=False;values.append(type(exc).__name__)
        ck('bare_owns_trivia_semantic_'+q,ok and len(set(values))==1,values)
    rng=random.Random(150015)
    def seg():return rng.choice(string.ascii_letters+'_')+''.join(rng.choice(string.ascii_letters+string.digits+'_') for _ in range(rng.randrange(0,9)))
    fuzz_specs=[
      ('bare_owns_trivia_3000',lambda q:(f'rule {q}.owns\n',f'rule {q}.owns   // c\n')),
      ('call_trivia_3000',lambda q:(f'rule {q}.owns(X)\n',f'rule {q}.owns   (X) // c\n')),
      ('relation_comment_3000',lambda q:(f'rule {q}.owns X\n',f'rule {q}.owns X // c\n')),
    ]
    for label,make in fuzz_specs:
        bad=[]
        for i in range(3000):
            q='.'.join(seg() for _ in range(rng.randrange(1,5)));a,b=make(q)
            try:
                if sem(a)!=sem(b):bad.append({'i':i,'qid':q,'error':'semantic_hash_mismatch'})
            except Exception as exc:bad.append({'i':i,'qid':q,'error':type(exc).__name__})
            if bad:break
        ck('fuzz_'+label,not bad,bad[:1])
    result['schema_version']='1.2'
    result['experiment']='CC-WP02 V15 generic dotted-prefix trivia-safe discriminator'
    result['created_at']=datetime.now(timezone.utc).isoformat()
    result['candidate_path']=str(V15.relative_to(ROOT))
    result['candidate_sha256']=base.sha(V15.read_bytes())
    result['candidate_bytes']=len(V15.read_bytes())
    result['predecessor_candidate']='V13_GENERIC_DOTTED_CALLSAFE'
    result['supersedes_v13_reason']='V13 still activated dotted-prefix lexing from horizontal whitespace followed only by // comment or line end, making trivia affect parse acceptance.'
    result['checks'].extend(extra)
    result['passed']=sum(x['pass'] for x in result['checks'])
    result['total']=len(result['checks'])
    result['pass']=all(x['pass'] for x in result['checks'])
    result['candidate_delta']='V13 generic call-safe relation token plus trivia-safe RHS lookahead requiring a real same-line nonspace RHS and excluding call/comment starts.'
    result['counts_as_wp02_pass']=False
    result['counts_as_target_acceptance']=False
    result['promotion_allowed']=False
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--require-strict',action='store_true');ap.add_argument('--output');args=ap.parse_args()
    result=run(args.require_strict);text=json.dumps(result,indent=2,ensure_ascii=False)+'\n';print(text,end='')
    if args.output:Path(args.output).write_text(text,encoding='utf-8')
    if not result['pass']:raise SystemExit(1)
if __name__=='__main__':main()
