#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path

def load(path):
    rows=[]
    for no,line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(),1):
        obj=json.loads(line); ms=obj['messages']
        if [m['role'] for m in ms] != ['system','user','assistant']:
            raise ValueError(f'{path}:{no}: role order')
        rows.append((ms[1]['content'],ms[2]['content']))
    return rows

def literals(text):
    return re.findall(r'"((?:\\.|[^"\\])*)"',text)

def metrics(train, valid):
    all_rows=train+valid
    pairs=set(all_rows); prompts={u for u,_ in all_rows}; outputs={a for _,a in all_rows}
    train_pairs=set(train); valid_pairs=set(valid)
    string_literals=set(); operations=set(); schemas=set()
    for _,a in all_rows:
        string_literals.update(literals(a))
        operations.update(re.findall(r'omega_bind\(w,"operation","([^"]+)"\)',a))
        schemas.update(re.findall(r'omega_schema\(w,"([^"]+)"\)',a))
    return {
      'rows':len(all_rows),'unique_pairs':len(pairs),'unique_pair_ratio':len(pairs)/max(1,len(all_rows)),
      'unique_prompts':len(prompts),'unique_outputs':len(outputs),
      'train_validation_pair_overlap':len(train_pairs & valid_pairs),
      'unique_string_literals':len(string_literals),'operations':sorted(operations),'schemas':sorted(schemas),
    }

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('train'); ap.add_argument('validation')
    ap.add_argument('--min-unique-ratio',type=float,default=0.95)
    ap.add_argument('--min-string-literals',type=int,default=500)
    args=ap.parse_args(); tr=load(args.train); va=load(args.validation); m=metrics(tr,va)
    failures=[]
    if m['unique_pair_ratio'] < args.min_unique_ratio: failures.append('unique_pair_ratio')
    if m['train_validation_pair_overlap'] != 0: failures.append('train_validation_pair_overlap')
    if m['unique_string_literals'] < args.min_string_literals: failures.append('unique_string_literals')
    if len(m['operations']) < 6: failures.append('operation_coverage')
    if len(m['schemas']) < 6: failures.append('schema_coverage')
    m['thresholds']={'min_unique_ratio':args.min_unique_ratio,'min_string_literals':args.min_string_literals,'min_operations':6,'min_schemas':6}
    m['failures']=failures; m['ok']=not failures
    print(json.dumps(m,indent=2,ensure_ascii=False))
    return 1 if failures else 0
if __name__=='__main__': raise SystemExit(main())
