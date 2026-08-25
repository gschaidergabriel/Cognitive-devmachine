#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, itertools, json, random, re
from collections import Counter
from pathlib import Path

ROW_SCHEMA='ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1'
SPLIT_UNIT='CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY'
CLASSES=('ALLOW','DENY','ABSTAIN')
REJECTED_ATOMS={'or'}
TRAIN_TEMPLATES={
'T1_POLICY':{
'ALLOW':'The requested operation satisfies every explicit precondition and conflicts with no stated restriction.',
'DENY':'The requested operation conflicts with an explicit restriction that applies to it.',
'ABSTAIN':'The available evidence is insufficient to determine whether the requested operation satisfies the governing conditions.'},
'T2_QUESTION':{
'ALLOW':'Given the stated rules and evidence, the request is fully supported with no unresolved conflict. Choose the mapped symbol.',
'DENY':'Given the stated rules and evidence, the request directly violates an applicable rule. Choose the mapped symbol.',
'ABSTAIN':'Given the stated rules and evidence, a required fact is unresolved, so a definitive decision is not justified. Choose the mapped symbol.'},
'T3_STATEMENT':{
'ALLOW':'All relevant conditions are met; no blocking condition is present.',
'DENY':'A blocking condition is present and applies directly.',
'ABSTAIN':'A necessary condition cannot be established from the available information.'},
'T4_FIRST_PERSON':{
'ALLOW':'I can establish every required condition from the supplied evidence and I see no applicable blocker.',
'DENY':'I can establish an applicable blocker from the supplied evidence.',
'ABSTAIN':'I cannot establish enough evidence to resolve the required condition.'}}
FROZEN_TEMPLATE_IDS={'T5_FROZEN_UNSEEN'}
CODEBOOK_OPEN='[CODEBOOK]'; CODEBOOK_CLOSE='[/CODEBOOK]'
CLASS_LEAK_RE=re.compile(r'\b(ALLOW|DENY|ABSTAIN)\b',re.I)

def validate_atom_inventory(atoms):
    if len(atoms)!=len(set(atoms)): raise ValueError('ATOM_DUPLICATE')
    if any(a in REJECTED_ATOMS for a in atoms): raise ValueError('REJECTED_ATOM_PRESENT')
    if len(atoms)<3: raise ValueError('AT_LEAST_THREE_ATOMS_REQUIRED')
    if any(not isinstance(a,str) or not a for a in atoms): raise ValueError('ATOM_INVALID')

def s3_permutations(atoms3):
    return [dict(zip(CLASSES,p)) for p in itertools.permutations(atoms3,3)]

def render_codebook(mapping,order):
    return CODEBOOK_OPEN+' '+' ; '.join(f'{c}={mapping[c]}' for c in order)+' '+CODEBOOK_CLOSE

def strip_codebook(prompt):
    s=prompt.find(CODEBOOK_OPEN); e=prompt.find(CODEBOOK_CLOSE)
    if s<0 or e<0 or e<s: raise ValueError('CODEBOOK_SPAN_MISSING')
    e+=len(CODEBOOK_CLOSE)
    return prompt[:s]+prompt[e:]

def assert_no_class_leak_outside_codebook(prompt):
    if CLASS_LEAK_RE.search(strip_codebook(prompt)):
        raise ValueError('CLASS_LABEL_LEAK_OUTSIDE_CODEBOOK')

def generate_rows(atoms3, seed=2, split='TRAIN', provenance_ancestry_id='trigger2-binding-generator-v1'):
    validate_atom_inventory(list(atoms3))
    rng=random.Random(seed); rows=[]; mappings=s3_permutations(atoms3)
    for pidx,mapping in enumerate(mappings):
        for cls in CLASSES:
            for template_id,texts in TRAIN_TEMPLATES.items():
                order=list(CLASSES); rng.shuffle(order)
                codebook=render_codebook(mapping,tuple(order))
                prompt=(f'{codebook}\n[SITUATION] {texts[cls]} [/SITUATION]\n'
                        '[QUERY] Return exactly the episode-local mapped symbol and nothing else. [/QUERY]')
                assert_no_class_leak_outside_codebook(prompt)
                target=mapping[cls]
                rows.append({
                    'schema':ROW_SCHEMA,'evidence_class':'METHOD_ONLY','reality_level':'R2',
                    'family_id':f'BIND_S3_{pidx}_{template_id}_{cls}',
                    'provenance_ancestry_id':provenance_ancestry_id,'canonical_truth_allowed':False,
                    'direct_effect_authority':False,'fact_status':'NOT_APPLICABLE',
                    'target_type':'DYNAMIC_CODEBOOK_BINDING','split':split,'split_unit':SPLIT_UNIT,
                    'selected_using_holdout':False,'template_id':template_id,'permutation_id':f'S3_{pidx}',
                    'codebook_mapping':mapping,'codebook_order':order,
                    'target_class_internal_generator_only':cls,'target_symbol':target,
                    'prompt':prompt,'target':target,'final_ft_eligible':False,
                    'placeholder_or_exact_abi_atoms':'STRUCTURAL_SEED_ONLY; OUTER PIPELINE MUST BIND EXACT 46-ATOM ABI AND FROZEN SYMBOL SPLITS'})
    return rows

def validate_rows(rows, expected_atoms3):
    failures=[]; expected={tuple((c,m[c]) for c in CLASSES) for m in s3_permutations(expected_atoms3)}
    realized=set(); pairs=Counter(); templates=set(); perm_ids=set()
    for row in rows:
        try: assert_no_class_leak_outside_codebook(row['prompt'])
        except Exception as e: failures.append(str(e))
        mapping=row.get('codebook_mapping') or {}
        if set(mapping)!=set(CLASSES): failures.append('MAPPING_CLASS_SET_INVALID'); continue
        realized.add(tuple((c,mapping[c]) for c in CLASSES)); perm_ids.add(row.get('permutation_id')); templates.add(row.get('template_id'))
        cls=row.get('target_class_internal_generator_only'); sym=row.get('target_symbol')
        if mapping.get(cls)!=sym or row.get('target')!=sym: failures.append('TARGET_NOT_DERIVED_FROM_REALIZED_MAPPING')
        pairs[(cls,sym)]+=1
        if row.get('template_id') in FROZEN_TEMPLATE_IDS: failures.append('FROZEN_TEMPLATE_VISIBLE')
    if realized!=expected: failures.append('FULL_S3_REALIZATION_REQUIRED')
    if len(perm_ids)!=6: failures.append('EXACT_SIX_PERMUTATION_IDS_REQUIRED')
    if set(TRAIN_TEMPLATES)-templates: failures.append('AT_LEAST_FOUR_TRAIN_TEMPLATES_REQUIRED')
    vals=list(pairs.values())
    if not vals or max(vals)-min(vals)!=0: failures.append('CLASS_SYMBOL_COUNTERBALANCE_NOT_EXACT')
    payload='\n'.join(json.dumps(r,sort_keys=True,separators=(',',':')) for r in rows)+'\n'
    return {'rows':len(rows),'failures':sorted(set(failures)),'pass':not failures,
            'pair_count_min':min(vals) if vals else 0,'pair_count_max':max(vals) if vals else 0,
            'realized_s3':len(realized),'templates':sorted(templates),
            'frozen_templates_seen':sorted(templates & FROZEN_TEMPLATE_IDS),
            'dataset_sha256':hashlib.sha256(payload.encode()).hexdigest()}

def write_jsonl(rows,path):
    Path(path).write_text('\n'.join(json.dumps(r,ensure_ascii=False,sort_keys=True) for r in rows)+'\n',encoding='utf-8')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--atoms',nargs=3,required=True); p.add_argument('--out',required=True); p.add_argument('--seed',type=int,default=2); a=p.parse_args()
    validate_atom_inventory(a.atoms)
    rows=generate_rows(tuple(a.atoms),seed=a.seed); report=validate_rows(rows,tuple(a.atoms))
    print(json.dumps(report,indent=2,sort_keys=True))
    if not report['pass']: return 2
    write_jsonl(rows,a.out); return 0
if __name__=='__main__': raise SystemExit(main())
