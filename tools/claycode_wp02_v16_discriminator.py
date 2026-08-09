#!/usr/bin/env python3
"""V16 WP-02 discriminator: V15 semantic/trivia gates plus regex scaling guard.

V16 simplifies the dotted-prefix lookahead so long trailing whitespace cannot induce the
V15 backtracking pathology. The Ubuntu release discriminator still requires --require-strict.
Sandbox timing is evidence, not target performance acceptance.
"""
from __future__ import annotations
import argparse, json, time
from datetime import datetime, timezone
from pathlib import Path
from lark import Lark, Token
import claycode_wp02_v15_discriminator as base

ROOT=Path(__file__).resolve().parents[1]
V16=ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V16_GENERIC_DOTTED_LINEAR_LOOKAHEAD.lark'
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
    base.V15=V16
    result=base.run(require_strict)
    grammar=V16.read_text(encoding='utf-8')
    parser=Lark(grammar,parser='lalr',lexer='contextual',start='start',keep_all_tokens=True)
    extra=[]
    def ck(name,ok,detail=None):extra.append({'name':name,'pass':bool(ok),'detail':detail})
    rhs=['X','x_y','3','-3','1.25','"X"','@a/b','[X]','{X}','f(X)','true','false']
    for item in rhs:
        try:parser.parse(f'rule Foo.owns {item}\n');ok=True
        except Exception:ok=False
        ck('rhs_start_'+item,ok)
    # Existing grammar intentionally allows this as ordinary division of qid Foo.owns by X.
    try:parser.parse('rule Foo.owns / X\n');slash_ok=True
    except Exception:slash_ok=False
    ck('ordinary_division_not_misclassified_as_relation',slash_ok)
    benchmarks={}
    for size in [100,500,1000,2000,5000,10000,20000,40000]:
        source='rule Foo.owns'+' '*size+'\n';samples=[]
        for _ in range(3):
            start=time.perf_counter();parser.parse(source);samples.append(time.perf_counter()-start)
        benchmarks[str(size)]=sorted(samples)[1]
    ratio=benchmarks['40000']/max(benchmarks['5000'],1e-12)
    ck('whitespace_scaling_40k_vs_5k_lt_20x',ratio<20.0,{'ratio':ratio,'seconds':benchmarks})
    result['schema_version']='1.3'
    result['experiment']='CC-WP02 V16 generic dotted-prefix linear-lookahead discriminator'
    result['created_at']=datetime.now(timezone.utc).isoformat()
    result['candidate_path']=str(V16.relative_to(ROOT))
    result['candidate_sha256']=base.base.sha(V16.read_bytes())
    result['candidate_bytes']=len(V16.read_bytes())
    result['predecessor_candidate']='V15_GENERIC_DOTTED_TRIVIA_SAFE'
    result['supersedes_v15_reason']='V15 semantic lookahead passed correctness gates but took about 1.23 s on a 10k-space bare-owns adversarial input in the sandbox; V16 reduces the lookahead to whitespace plus one admissible RHS-start character and shows near-linear scaling.'
    result['sandbox_timing_evidence']={'whitespace_median_seconds':benchmarks,'ratio_40k_vs_5k':ratio,'not_target_performance_acceptance':True}
    result['checks'].extend(extra)
    result['passed']=sum(x['pass'] for x in result['checks'])
    result['total']=len(result['checks'])
    result['pass']=all(x['pass'] for x in result['checks'])
    result['candidate_delta']='V15 semantics preserved with simpler linear-style RHS-start lookahead: horizontal whitespace followed by one nonspace, non-newline, non-semicolon, non-slash, non-call-paren character.'
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
