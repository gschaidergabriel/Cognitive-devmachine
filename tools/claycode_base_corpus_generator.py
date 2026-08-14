#!/usr/bin/env python3
"""Deterministic semantics-derived ClayCode BASE train/heldout corpus generator.

Split policy is family-first, never random-example-first: heldout semantic families are
not emitted into training. Exact, normalized and family leakage are audited.
"""
from __future__ import annotations
import hashlib,json,random,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUTDIR=ROOT/'research_entity/claycode/corpus/base_v1'
SEED=20260809
TRAIN_FAMILIES=('arith_add','arith_sub','arith_mul','negative_return','negative_unknown')
HELDOUT_FAMILIES=('compare_gt','compare_eq','call_composition','negative_argtype')

def h(s):return hashlib.sha256(s.encode()).hexdigest()
def norm(s):return re.sub(r'\s+','',re.sub(r'//[^\n]*','',s))
def make(fam,i,rng):
 a=rng.randint(-99,99);b=rng.randint(-99,99)
 if fam=='arith_add':src=f'module corpus.train.add{i}\nfn main(a:Int,b:Int)->Int=a+b\n';label={'kind':'positive','result':a+b,'args':[a,b]}
 elif fam=='arith_sub':src=f'module corpus.train.sub{i}\nfn main(a:Int,b:Int)->Int=a-b\n';label={'kind':'positive','result':a-b,'args':[a,b]}
 elif fam=='arith_mul':src=f'module corpus.train.mul{i}\nfn main(a:Int,b:Int)->Int=a*b\n';label={'kind':'positive','result':a*b,'args':[a,b]}
 elif fam=='compare_gt':src=f'module corpus.eval.gt{i}\nfn main(a:Int,b:Int)->Bool=a>b\n';label={'kind':'positive','result':a>b,'args':[a,b]}
 elif fam=='compare_eq':src=f'module corpus.eval.eq{i}\nfn main(a:Int,b:Int)->Bool=a==b\n';label={'kind':'positive','result':a==b,'args':[a,b]}
 elif fam=='call_composition':src=f'module corpus.eval.call{i}\nfn inc(x:Int)->Int=x+1\nfn main(a:Int)->Int=inc(a)*2\n';label={'kind':'positive','result':(a+1)*2,'args':[a]}
 elif fam=='negative_return':src=f'module corpus.train.badret{i}\nfn bad(a:Int)->Bool=a+1\n';label={'kind':'negative','diagnostic_class':'RETURN_TYPE_MISMATCH'}
 elif fam=='negative_unknown':src=f'module corpus.train.unknown{i}\nfn bad(a:Int)->Int=a+missing{i}\n';label={'kind':'negative','diagnostic_class':'UNKNOWN_NAME'}
 elif fam=='negative_argtype':src=f'module corpus.eval.arg{i}\nfn id(a:Int)->Int=a\nfn bad(b:Bool)->Int=id(b)\n';label={'kind':'negative','diagnostic_class':'ARGUMENT_TYPE_MISMATCH'}
 else:raise KeyError(fam)
 return {'family':fam,'source':src,'source_sha256':h(src),'normalized_sha256':h(norm(src)),'label':label}
def main():
 rng=random.Random(SEED);train=[];held=[]
 for fam in TRAIN_FAMILIES:
  for i in range(40):train.append(make(fam,i,rng))
 for fam in HELDOUT_FAMILIES:
  for i in range(30):held.append(make(fam,i,rng))
 ts={x['source_sha256'] for x in train};hs={x['source_sha256'] for x in held};tn={x['normalized_sha256'] for x in train};hn={x['normalized_sha256'] for x in held};tf={x['family'] for x in train};hf={x['family'] for x in held}
 leak={'exact_source_overlap':sorted(ts&hs),'normalized_source_overlap':sorted(tn&hn),'family_overlap':sorted(tf&hf),'pass':not(ts&hs or tn&hn or tf&hf)}
 OUTDIR.mkdir(parents=True,exist_ok=True)
 for name,rows in [('train.jsonl',train),('heldout.jsonl',held)]:
  (OUTDIR/name).write_text(''.join(json.dumps(x,sort_keys=True,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8')
 manifest={'schema_version':'1.0','seed':SEED,'split_policy':'SEMANTIC_FAMILY_FIRST','training_families':TRAIN_FAMILIES,'heldout_families':HELDOUT_FAMILIES,'train_count':len(train),'heldout_count':len(held),'train_file_sha256':hashlib.sha256((OUTDIR/'train.jsonl').read_bytes()).hexdigest(),'heldout_file_sha256':hashlib.sha256((OUTDIR/'heldout.jsonl').read_bytes()).hexdigest(),'leak_audit':leak,'pass':leak['pass']}
 (OUTDIR/'CORPUS_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');print(json.dumps(manifest));return 0 if manifest['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
