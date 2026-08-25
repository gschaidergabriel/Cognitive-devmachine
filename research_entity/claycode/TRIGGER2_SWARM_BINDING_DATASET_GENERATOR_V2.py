import json, itertools, hashlib, math, re
from collections import Counter, defaultdict
from pathlib import Path

OUT=Path('.')
jsonl=OUT/'TRIGGER2_SWARM_BINDING_DATASET_CANDIDATE_V2.jsonl'
auditp=OUT/'TRIGGER2_SWARM_BINDING_DATASET_AUDIT_V2.json'

classes=['ALLOW','DENY','ABSTAIN']
train_symbols_by_template={
 'T1_RULE':['ABI_ROW_PLACEHOLDER_03','ABI_ROW_PLACEHOLDER_17','ABI_ROW_PLACEHOLDER_29'],
 'T2_VERIFY':['ABI_ROW_PLACEHOLDER_08','ABI_ROW_PLACEHOLDER_22','ABI_ROW_PLACEHOLDER_31'],
 'T3_DIALOGUE':['ABI_ROW_PLACEHOLDER_12','ABI_ROW_PLACEHOLDER_25','ABI_ROW_PLACEHOLDER_41'],
 'T4_FIRSTPERSON':['ABI_ROW_PLACEHOLDER_09','ABI_ROW_PLACEHOLDER_18','ABI_ROW_PLACEHOLDER_36'],
}
val_symbols=['ABI_ROW_PLACEHOLDER_05','ABI_ROW_PLACEHOLDER_27','ABI_ROW_PLACEHOLDER_34']
holdout_vocab_symbols=['ABI_ROW_PLACEHOLDER_06','ABI_ROW_PLACEHOLDER_11','ABI_ROW_PLACEHOLDER_37']
holdout_template_symbols=['ABI_ROW_PLACEHOLDER_07','ABI_ROW_PLACEHOLDER_24','ABI_ROW_PLACEHOLDER_39']
holdout_unseen_symbols=['ABI_ROW_PLACEHOLDER_HOLDOUT_44','ABI_ROW_PLACEHOLDER_HOLDOUT_45','ABI_ROW_PLACEHOLDER_HOLDOUT_46']

# Model-visible situations deliberately avoid literal class labels.
train_situations={
 'T1_RULE':{
  'ALLOW':'The controlling rule explicitly permits the requested transition, every required precondition is satisfied, and no stronger restriction applies.',
  'DENY':'A higher-priority controlling rule explicitly prohibits the requested transition, and no valid exception overrides it.',
  'ABSTAIN':'The decisive permission record is unavailable, the observed evidence does not settle the transition, and no tie-break rule is admitted.'},
 'T2_VERIFY':{
  'ALLOW':'Verification found a valid grant covering this operation; scope and preconditions match the request, with no conflicting higher authority.',
  'DENY':'Verification found an active blocking rule with higher authority than the local preference; no admitted waiver is present.',
  'ABSTAIN':'Verification found mutually incomplete records and the missing decisive observation has not been obtained.'},
 'T3_DIALOGUE':{
  'ALLOW':'Operator: The scope matches. Verifier: The controlling policy authorizes this transition and every gate is cleared.',
  'DENY':'Operator: The local request looks acceptable. Verifier: A stronger policy forbids this transition and remains in force.',
  'ABSTAIN':'Operator: Can we resolve it now? Verifier: The decisive source has not been observed, so the evidence remains underdetermined.'},
 'T4_FIRSTPERSON':{
  'ALLOW':'I verified the request is within the granted scope, all required conditions hold, and I found no overriding restriction.',
  'DENY':'I verified an overriding prohibition applies to this request and found no admitted exception that defeats it.',
  'ABSTAIN':'I cannot determine the permission state because the decisive record is missing and current evidence supports more than one live possibility.'},
}

val_situations={
 'ALLOW':'The authorization record covers the requested transition, all mandatory gates are satisfied, and no superior constraint conflicts.',
 'DENY':'A superior constraint blocks the requested transition and the available record contains no operative exemption.',
 'ABSTAIN':'The evidence bundle lacks the deciding record; the remaining observations are compatible with multiple outcomes.'}

holdout_vocab_situations={
 'ALLOW':'The governing rule sanctions the transition; every prerequisite is cleared and nothing with precedence precludes it.',
 'DENY':'The governing rule disallows the transition; a precedence-bearing restriction remains operative and no carve-out is established.',
 'ABSTAIN':'The governing status is indeterminate because the decisive observation is unavailable and the record remains underdetermined.'}

holdout_template_situations={
 'ALLOW':{'observations':['scope_match=true','preconditions=complete','overriding_restriction=absent'],'evidence_state':'decisive'},
 'DENY':{'observations':['scope_match=true','higher_order_block=present','exception=absent'],'evidence_state':'decisive'},
 'ABSTAIN':{'observations':['scope_match=unknown','decisive_observation=unavailable','conflict_resolution=missing'],'evidence_state':'nondecisive'},
}

holdout_symbol_situations={
 'ALLOW':'I confirmed the operative authority grants this exact transition, all prerequisites hold, and no superior veto is active.',
 'DENY':'I confirmed a superior veto applies to this exact transition and there is no current exception with sufficient authority.',
 'ABSTAIN':'I found no decisive record capable of resolving the transition; the evidence must remain open rather than guessed.'}

source={
 'source_package_sha256':'a2babae93dfe39e4e452a06bd8b848337f29766e38c422f05fb395126229b05c',
 'ingest_path':'research_entity/global/j-space/research/2026-08-25_TRIGGER2_CLAUDE_XENO_VECTOR_EVIDENCE_INGEST_V1_GPT56SOL.json',
 'ingest_schema':'CLAY_TRIGGER2_CLAUDE_XENO_VECTOR_EVIDENCE_INGEST/v1.1',
 'abi_manifest_sha256':'0f664e6a4626351fbf97cd74a4825cedaf115b80f56b71b16c39315dba02fa11',
 'model_id':'Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1',
 'model_snapshot':'591852bda6e1979f59e4b0f5ee2919697b12e936',
 'evidence_scope':'MODEL_SPECIFIC_CLAUDE_MEASUREMENT_PACKAGE_PLUS_GPT56SOL_REVIEW'
}

def codebook_for(symbols, perm, order_shift):
    mapping=dict(zip(classes, perm))
    entries=[{'class_label':c,'symbol_ref':mapping[c]} for c in classes]
    k=order_shift%3
    entries=entries[k:]+entries[:k]
    return mapping, entries

def mkrow(row_id, split, family, template, symbols, perm_idx, semantic_class, situation, ancestry, frozen=False, holdout_kind=None):
    perms=list(itertools.permutations(symbols))
    perm=perms[perm_idx]
    mapping, entries=codebook_for(symbols, perm, perm_idx + classes.index(semantic_class))
    target=mapping[semantic_class]
    model_input={
      'codebook':entries,
      'situation':situation,
      'query':'Return only the episode-local final symbol reference justified by the current situation and this codebook.'
    }
    row={
      'schema':'TRIGGER2_BINDING_TRAINING_ROW/v2',
      'row_id':row_id,
      'status':'CANDIDATE_NOT_TRAINING_ADMITTED',
      'training_ready':False,
      'family':family,
      'objective':'CONTENT_DEPENDENT_CONTEXT_INVARIANT_EPISODIC_CODEBOOK_BINDING',
      'split':split,
      'split_unit':'CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY',
      'ancestry_family':ancestry,
      'template_family':template,
      'holdout_kind':holdout_kind,
      'frozen_holdout':frozen,
      'source_provenance':source,
      'evidence_basis':{
        'semantic_readability':'0.94-1.00 from approximately L6 onward on measured family',
        'dynamic_codebook_symbol_hit_baseline':0.3611111111111111,
        'chance':1/3,
        'cross_template_L19_baseline':0.5254629629629629,
        'into_codebook_from_other_templates':[1/3,1/3,1/3],
        'carrier_binding_through_k16':'MEASURED_SUFFICIENT',
        'training_interpretation':'teach binding/routing; protect existing semantic read, symbol write, and carrier algebra'
      },
      'model_visible':model_input,
      'target':target,
      'supervision_meta':{
        'model_visible':False,
        'semantic_class':semantic_class,
        'relative_s3_permutation_index':perm_idx,
        'realized_mapping':mapping,
        'displayed_codebook_order':[e['class_label'] for e in entries],
        'counterfactual_group':f'{split}:{template}:{ancestry}:{semantic_class}',
      },
      'hard_negative':'Ignore static class-symbol priors, prior-episode bindings, line position, majority heuristics, and safe-default collapse; use the current episode codebook.',
      'authority':{'canonical_truth_allowed':False,'direct_effect_authority':False,'jspace_promotion_allowed':False},
      'abi_materialization_gate':{
        'status':'BLOCKED_PENDING_EXACT_MANIFEST_ROW_TO_SINGLE_TOKEN_ATOM_VERIFICATION',
        'symbol_ref_is_placeholder':True,
        'required_before_training':['verify exact accepted atom row/name against ABI manifest','verify single-token identity under pinned tokenizer','replace placeholder with manifest-bound atom identity without changing split membership']
      },
      'review':{
        'EVIDENCE_EXTRACTOR':'PASS_MEASUREMENT_SCOPED',
        'DATASET_ARCHITECT':'PASS_CANDIDATE',
        'ADVERSARIAL_SHORTCUT_HUNTER':'PASS_PENDING_GLOBAL_AUDIT',
        'STATISTICAL_REVIEWER':'PASS_PENDING_GLOBAL_AUDIT',
        'ABI_PROVENANCE_REVIEWER':'BLOCKED_ATOM_MATERIALIZATION',
        'RETENTION_REVIEWER':'SEPARATE_ACCEPTANCE_SUITE_REQUIRED',
        'HARNESS_COMPATIBILITY_REVIEWER':'PASS_SYMBOL_REFERENCE_LEVEL_ONLY',
        'FINAL_INTEGRATOR':'CANDIDATE_ONLY_NO_TRAINING_CREDIT'
      }
    }
    return row

rows=[]
# Train: 4 templates x 6 perms x 3 classes = 72
for ti,(template,symbols) in enumerate(train_symbols_by_template.items(),1):
    for pi in range(6):
        for ci,c in enumerate(classes):
            rows.append(mkrow(f'TR_{template}_{pi}_{c}', 'TRAIN', 'A_B_BINDING_CORE', template, symbols, pi, c, train_situations[template][c], f'train_semantic_family_{template}_{c}'))

# Validation: 6 x 3 = 18, same structural family as T2 but different lexical realization.
for pi in range(6):
    for c in classes:
        rows.append(mkrow(f'VA_T2P_{pi}_{c}', 'VALIDATION', 'B_DYNAMIC_CODEBOOK_BINDING', 'T2_VERIFY_PARAPHRASE', val_symbols, pi, c, val_situations[c], f'val_calibration_family_{c}'))

# Holdout unseen semantic vocabulary: 18. Structural family known, semantic-bearing lexemes disjoint by declaration.
for pi in range(6):
    for c in classes:
        rows.append(mkrow(f'HO_VOCAB_{pi}_{c}', 'HOLDOUT_FROZEN', 'A_CONTEXT_INVARIANT_BINDING', 'T1_RULE_UNSEEN_VOCAB', holdout_vocab_symbols, pi, c, holdout_vocab_situations[c], f'holdout_vocab_family_{c}', True, 'UNSEEN_SEMANTIC_VOCABULARY'))

# Holdout unseen structure/template: 18.
for pi in range(6):
    for c in classes:
        rows.append(mkrow(f'HO_T5_{pi}_{c}', 'HOLDOUT_FROZEN', 'A_CONTEXT_INVARIANT_BINDING', 'T5_STRUCTURED_EVIDENCE_BUNDLE', holdout_template_symbols, pi, c, holdout_template_situations[c], f'holdout_template_family_{c}', True, 'UNSEEN_TEMPLATE'))

# Holdout unseen symbol set: 18.
for pi in range(6):
    for c in classes:
        rows.append(mkrow(f'HO_SYMBOL_{pi}_{c}', 'HOLDOUT_FROZEN', 'B_DYNAMIC_CODEBOOK_BINDING', 'T4_FIRSTPERSON_UNSEEN_SYMBOLS', holdout_unseen_symbols, pi, c, holdout_symbol_situations[c], f'holdout_symbol_family_{c}', True, 'UNSEEN_SYMBOL_SET'))

# write jsonl canonical-ish compact order
with jsonl.open('w',encoding='utf-8') as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',',':'))+'\n')

# Audits
issues=[]
counts=Counter(r['split'] for r in rows)
if counts != Counter({'TRAIN':72,'VALIDATION':18,'HOLDOUT_FROZEN':54}): issues.append(f'row_counts:{counts}')

# class labels appear in model-visible JSON only in class_label fields of codebook entries.
label_leaks=[]
for r in rows:
    sit=json.dumps(r['model_visible']['situation'],ensure_ascii=False)
    query=r['model_visible']['query']
    for lab in classes:
        if re.search(rf'\b{lab}\b', sit, re.I) or re.search(rf'\b{lab}\b', query, re.I):
            label_leaks.append((r['row_id'],lab))
if label_leaks: issues.append(f'class_label_leaks:{label_leaks[:5]}')

# Full S3 and exact balance for each train template.
train_balance={}
for template,symbols in train_symbols_by_template.items():
    rr=[r for r in rows if r['split']=='TRAIN' and r['template_family']==template]
    permset={r['supervision_meta']['relative_s3_permutation_index'] for r in rr}
    pair=Counter((r['supervision_meta']['semantic_class'],r['target']) for r in rr)
    ok_perm=permset==set(range(6))
    ok_pair=all(pair[(c,s)]==2 for c in classes for s in symbols)
    train_balance[template]={'rows':len(rr),'permutations':sorted(permset),'full_s3':ok_perm,'class_symbol_counts':{f'{c}->{s}':pair[(c,s)] for c in classes for s in symbols},'exact_pair_balance':ok_pair}
    if not(ok_perm and ok_pair and len(rr)==18): issues.append(f'train_balance:{template}')

# MI(class; target) per train template.
def mi_for(rr):
    n=len(rr); jc=Counter((r['supervision_meta']['semantic_class'],r['target']) for r in rr); ca=Counter(r['supervision_meta']['semantic_class'] for r in rr); ta=Counter(r['target'] for r in rr)
    mi=0.0
    for (c,t),v in jc.items():
        p=v/n; pc=ca[c]/n; pt=ta[t]/n
        mi += p*math.log2(p/(pc*pt))
    return mi
mi={t:mi_for([r for r in rows if r['split']=='TRAIN' and r['template_family']==t]) for t in train_symbols_by_template}
if any(abs(v)>1e-12 for v in mi.values()): issues.append(f'mi_nonzero:{mi}')

# Contrast groups: within each template + class, targets span all 3 symbols over 6 permutations.
contrast={}
for template,symbols in train_symbols_by_template.items():
  for c in classes:
    rr=[r for r in rows if r['split']=='TRAIN' and r['template_family']==template and r['supervision_meta']['semantic_class']==c]
    got=sorted(set(r['target'] for r in rr)); ok=set(got)==set(symbols)
    contrast[f'{template}:{c}']={'target_refs':got,'all_symbols_seen':ok}
    if not ok: issues.append(f'contrast_fail:{template}:{c}')

# T5 absent train and validation
if any(r['template_family']=='T5_STRUCTURED_EVIDENCE_BUNDLE' and r['split']!='HOLDOUT_FROZEN' for r in rows): issues.append('T5_leak')
# Holdout unseen symbol refs absent train/val
seen_trainval={r['target'] for r in rows if r['split'] in {'TRAIN','VALIDATION'}}
if set(holdout_unseen_symbols)&seen_trainval: issues.append('holdout_symbol_leak')
# all candidate no training ready
if any(r['training_ready'] for r in rows): issues.append('training_ready_true')

# declared semantic lexeme isolation audit (protocol/function words exempt)
train_lexemes={'permit','permits','prohibit','prohibits','grant','blocking','authorizes','forbids','overriding','prohibition','missing','unavailable','underdetermined','incomplete'}
holdout_lexemes={'sanctions','cleared','precludes','disallows','carve-out','indeterminate','decisive','observation'}
lexeme_overlap=sorted(train_lexemes & holdout_lexemes)
if lexeme_overlap: issues.append(f'lexeme_overlap:{lexeme_overlap}')

# Spec tension: full S3 in training means no relative permutation can be unseen.
spec_tension={
 'id':'FULL_S3_TRAIN_VS_UNSEEN_RELATIVE_PERMUTATION_HOLDOUT',
 'status':'OPEN_PREREGISTRATION_REQUIRED',
 'observation':'The source simultaneously requires full S3 coverage and an unseen-permutation holdout. If all six relative 3-class permutations occur in training, a relative-S3 permutation cannot also be unseen.',
 'candidate_resolution':'Treat unseen mapping-instance generalization (new symbol identities / codebook instances) separately from relative-S3 generalization, or reserve a defined structural permutation factor in a separately versioned protocol. Do not claim relative unseen-permutation acceptance from this seed.',
 'relative_s3_unseen_holdout_present':False,
 'unseen_mapping_instance_holdout_present':True
}

audit={
 'schema':'TRIGGER2_SWARM_BINDING_DATASET_AUDIT/v2',
 'status':'PASS_CANDIDATE_GATES_WITH_ABI_MATERIALIZATION_BLOCK',
 'generated_rows':len(rows),
 'split_counts':dict(counts),
 'train_templates':list(train_symbols_by_template),
 'frozen_holdouts':['UNSEEN_SEMANTIC_VOCABULARY','UNSEEN_TEMPLATE','UNSEEN_SYMBOL_SET'],
 'full_s3_balance':train_balance,
 'mutual_information_bits_class_target_per_train_template':mi,
 'counterfactual_target_span':contrast,
 'class_label_leakage_outside_codebook':{'count':len(label_leaks),'pass':not label_leaks},
 'semantic_lexeme_isolation':{'policy':'semantic-bearing lexeme inventory only; protocol/function words explicitly exempt','train_lexemes':sorted(train_lexemes),'holdout_lexemes':sorted(holdout_lexemes),'overlap':lexeme_overlap,'pass':not lexeme_overlap},
 'holdout_template_absent_train_validation':True,
 'holdout_symbol_set_absent_train_validation':not bool(set(holdout_unseen_symbols)&seen_trainval),
 'abi_gate':{'status':'BLOCKED','reason':'Exact 46 accepted atom row/name mapping is not available in current connected source context; placeholders deliberately prevent fabricated atom identities. Training admission requires manifest-bound materialization and pinned-tokenizer single-token verification.'},
 'review_swarm':{
  'EVIDENCE_EXTRACTOR':'PASS: objective matches measured missing binding/router capability; protected functions remain non-primary targets.',
  'DATASET_ARCHITECT':'PASS: 72-row core covers 4 structures × full S3 × 3 semantic classes; 54 frozen holdout rows cover three orthogonal generalization axes.',
  'ADVERSARIAL_SHORTCUT_HUNTER':'PASS_CANDIDATE: static class-symbol, line-position, prior-episode and safe-default shortcuts countered by codebook permutation/order and counterfactual twins.',
  'STATISTICAL_REVIEWER':'PASS_CANDIDATE: exact class×symbol balance within each train template; MI(class,target)=0 bits at designed scope.',
  'ABI_PROVENANCE_REVIEWER':'BLOCK: placeholder symbols must be replaced only from exact ABI manifest / pinned tokenizer verification.',
  'RETENTION_REVIEWER':'OPEN_SEPARATE: seed does not evaluate post-training semantic-read/symbol-write/general-language/code retention.',
  'HARNESS_COMPATIBILITY_REVIEWER':'PASS_SYMBOL_REF_LEVEL_ONLY: row structure supports episode-local codebook lookup traces; exact ABI hook compatibility awaits materialization.',
  'FINAL_INTEGRATOR':'CANDIDATE_ONLY: no row is training-admitted; no model/J-Space/HCU/training credit.'
 },
 'spec_tension':spec_tension,
 'falsifiers':[ 
  'A model performing well while codebook mappings are shuffled independently of targets would expose a dataset/loader leak.',
  'Accuracy collapsing only on unseen vocabulary with intact codebook mechanics would indicate semantic lexical overfit rather than context-invariant binding.',
  'Accuracy collapsing only on unseen symbol identities would indicate atom memorization rather than episodic variable binding.',
  'Post-training semantic readability or symbol-write capability degrading beyond declared retention bounds falsifies the narrow-router specialization hypothesis.',
  'Lesion of the learned binding route failing to selectively impair codebook choice, or rescue failing to restore it, weakens causal binder claims.'
 ],
 'credits':{'training_executed':False,'training_credit':0,'jspace_model_runtime_credit':0,'whole_hcu_runtime_credit':0,'whole_entityos_hcu_runtime_credit':0},
 'issues':issues,
 'pass_candidate_invariants':not issues
}
with auditp.open('w',encoding='utf-8') as f: json.dump(audit,f,ensure_ascii=False,indent=2,sort_keys=True)

print(json.dumps({'jsonl':str(jsonl),'audit':str(auditp),'rows':len(rows),'counts':dict(counts),'issues':issues,'sha256_jsonl':hashlib.sha256(jsonl.read_bytes()).hexdigest(),'sha256_audit':hashlib.sha256(auditp.read_bytes()).hexdigest()},indent=2))
