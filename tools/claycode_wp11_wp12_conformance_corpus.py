#!/usr/bin/env python3
"""ClayCode BASE WP11/WP12 executable conformance + heldout corpus generator."""
from __future__ import annotations
import hashlib, json, random
from pathlib import Path
from claycode_base_pure_toolchain import compile_source, differential

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research_entity/claycode/corpus/base_v1'
CORPUS=OUT/'BASE_SEMANTIC_CORPUS_V1.jsonl'
MANIFEST=OUT/'BASE_SEMANTIC_CORPUS_V1_MANIFEST.json'
RECEIPT=ROOT/'research_entity/claycode/autonomous/WP11_WP12_CONFORMANCE_CORPUS_RECEIPT.json'
SEED=20260809
OPS=['+','-','*','>','<','>=','<=','==','!=']
SPLITS=('train','validation','test')

def sha(x):
    if isinstance(x,str): x=x.encode()
    return hashlib.sha256(x).hexdigest()

def split_for(eid):
    n=int(sha('ClayCodeCorpusSplit/v1\0'+eid)[:8],16)%100
    return 'train' if n<70 else 'validation' if n<85 else 'test'

def pos(i):
    op=OPS[i%len(OPS)]; ret='Bool' if op in {'>','<','>=','<=','==','!='} else 'Int'
    src=f'module corpus.pos_{i}\nfn helper(a:Int,b:Int)->{ret}=a{op}b\nfn main(a:Int,b:Int)->{ret}=helper(a,b)\n'
    return {'example_id':f'POS-{i:05d}','class':'POSITIVE','source':src,'expected':'ACCEPT','operator':op}

def neg(i):
    rows=[
      ('RETURN_MISMATCH','fn main(a:Int)->Bool=a+1\n'),
      ('UNKNOWN_NAME','fn main(a:Int)->Int=missing+1\n'),
      ('UNKNOWN_FUNCTION','fn main(a:Int)->Int=nope(a)\n'),
      ('ARITY_MISMATCH','fn f(a:Int)->Int=a\nfn main(a:Int)->Int=f(a,a)\n'),
      ('DUPLICATE_FUNCTION','fn f(a:Int)->Int=a\nfn f(a:Int)->Int=a\n'),
      ('DUPLICATE_PARAM','fn main(a:Int,a:Int)->Int=a\n'),
      ('UNTYPED_PARAM','fn main(a)->Int=a\n'),
      ('BOOL_ARITHMETIC','fn main(a:Bool,b:Bool)->Bool=a+b\n')]
    name,body=rows[i%len(rows)]
    return {'example_id':f'NEG-{i:05d}','class':'NEGATIVE','source':f'module corpus.neg_{i}\n{body}','expected':'REJECT','negative_class':name}

def run_row(row,rng):
    r=dict(row); r['source_sha256']=sha(r['source']); r['split']=split_for(r['example_id'])
    try:
        c=compile_source(r['source']); r['observed']='ACCEPT'; r['semantic_hash']=c['semantic_hash']
        if r['class']=='POSITIVE':
            args=[rng.randint(-1000,1000),rng.randint(-1000,1000)]
            d=differential(c,'main',args)
            r['native_differential']={'args':args,'match':bool(d['match']),'generated_c_sha256':d['generated_c_sha256']}
        else: r['unexpected_accept']=True
    except Exception as e:
        r['observed']='REJECT'; r['error_type']=type(e).__name__; r['error']=str(e)[:500]
    r['pass']=r['observed']==r['expected'] and (not r.get('native_differential') or r['native_differential']['match'])
    return r

def mutations():
    out=[]
    for name,a,b in [('ADD_SUB','+','-'),('GT_LT','>','<'),('GE_LE','>=','<='),('EQ_NE','==','!=')]:
        ret='Int' if a in {'+','-','*'} else 'Bool'
        sa=f'module mutation.{name.lower()}\nfn main(a:Int,b:Int)->{ret}=a{a}b\n'
        sb=f'module mutation.{name.lower()}\nfn main(a:Int,b:Int)->{ret}=a{b}b\n'
        ca,cb=compile_source(sa),compile_source(sb)
        out.append({'name':name,'left':a,'right':b,'left_semantic_hash':ca['semantic_hash'],'right_semantic_hash':cb['semantic_hash'],'pass':ca['semantic_hash']!=cb['semantic_hash']})
    return out

def main():
    rng=random.Random(SEED)
    base=[pos(i) for i in range(180)]+[neg(i) for i in range(180)]; rng.shuffle(base)
    rows=[run_row(x,rng) for x in base]
    fails=[x['example_id'] for x in rows if not x['pass']]
    muts=mutations(); mf=[x['name'] for x in muts if not x['pass']]
    src={s:{x['source_sha256'] for x in rows if x['split']==s} for s in SPLITS}
    sem={s:{x['semantic_hash'] for x in rows if x['split']==s and x.get('semantic_hash')} for s in SPLITS}
    so={f'{a}:{b}':sorted(src[a]&src[b]) for i,a in enumerate(SPLITS) for b in SPLITS[i+1:]}
    se={f'{a}:{b}':sorted(sem[a]&sem[b]) for i,a in enumerate(SPLITS) for b in SPLITS[i+1:]}
    leak=not any(so.values()) and not any(se.values())
    OUT.mkdir(parents=True,exist_ok=True)
    CORPUS.write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in rows))
    ch=sha(CORPUS.read_bytes())
    counts={s:{'total':sum(x['split']==s for x in rows),'positive':sum(x['split']==s and x['class']=='POSITIVE' for x in rows),'negative':sum(x['split']==s and x['class']=='NEGATIVE' for x in rows)} for s in SPLITS}
    manifest={'schema_version':'1.0','corpus':str(CORPUS.relative_to(ROOT)),'corpus_sha256':ch,'generator':'tools/claycode_wp11_wp12_conformance_corpus.py','generator_seed':SEED,'split_method':'sha256(example_id) deterministic 70/15/15','counts':counts,'source_overlap':so,'semantic_overlap':se,'leak_audit_pass':leak,'negative_classes':sorted({x.get('negative_class') for x in rows if x.get('negative_class')})}
    MANIFEST.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    ok=not fails and not mf and leak
    receipt={'schema_version':'1.0','experiment':'ClayCode BASE WP11/WP12 conformance and heldout corpus','evidence_class':'HOSTED_OR_LOCAL_LINUX_CONFORMANCE_NOT_ANDREAS_TARGET_ACCEPTANCE','pass':ok,'examples':len(rows),'failures':fails,'mutation_checks':muts,'mutation_failures':mf,'corpus_sha256':ch,'leak_audit_pass':leak,'source_overlap':so,'semantic_overlap':se,'counts_as_work_package_pass':False,'counts_as_target_acceptance':False,'supports':['CC-WP-11-FUZZ-CONFORMANCE','CC-WP-12-CORPUS-HELDOUT'],'next_required':'Expand to full frozen semantic/effect/runtime surface and rerun heldout fixtures on Andreas Ubuntu target before promotion.'}
    RECEIPT.parent.mkdir(parents=True,exist_ok=True); RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'pass':ok,'examples':len(rows),'failures':len(fails),'mutation_failures':len(mf),'leak_free':leak}))
    return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
