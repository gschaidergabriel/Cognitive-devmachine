import json, itertools, hashlib, re

classes=['ALLOW','DENY','ABSTAIN']
atoms=['ABI_ATOM_SLOT_00','ABI_ATOM_SLOT_01','ABI_ATOM_SLOT_02']
perms=list(itertools.permutations(atoms))
# Four train template families; a fifth is explicitly reserved for frozen holdout and not generated here.
templates={
'T1_LEASE':{
 'ALLOW':'A coordinator lease has the same epoch as S1, the task is inside its declared scope, and its policy binding is current.',
 'DENY':'A coordinator lease was issued for an earlier S1 epoch and has not been deterministically rebased.',
 'ABSTAIN':'A coordinator lease is present, but the evidence packet does not contain the policy version needed to verify its validity.'},
'T2_EFFECT':{
 'ALLOW':'A typed effect request has a verified capability, a current generation, and a deterministic EffectGate approval already recorded before execution.',
 'DENY':'A model output attempts to invoke an external state-changing action directly without passing through EffectGate.',
 'ABSTAIN':'An external submission timed out after transmission and there is no verified outcome receipt yet.'},
'T3_RESULT':{
 'ALLOW':'A NODE_RESULT matches the coordinator epoch, is inside scope, has a fresh causal identity, and passes provenance checks.',
 'DENY':'The same causal NODE_RESULT is delivered a second time with an identical event identity.',
 'ABSTAIN':'A NODE_RESULT has valid transport metadata, but the payload reference cannot currently be resolved to the claimed content digest.'},
'T4_HYPER':{
 'ALLOW':'A preregistered discriminator separates two previously live alternatives and the winning branch is supported by the new evidence while the other is contradicted.',
 'DENY':'Eight of ten workers prefer one branch, but no new evidence distinguishes it from its surviving alternative.',
 'ABSTAIN':'Two alternatives remain compatible with every admitted observation and the planned discriminator has not executed.'},
}

rows=[]
for tid, cases in templates.items():
    for pidx, perm in enumerate(perms):
        mapping=dict(zip(classes,perm))
        display_order=[classes[(pidx+i)%3] for i in range(3)]
        codebook=' | '.join(f'{c}=>{mapping[c]}' for c in display_order)
        for cls in classes:
            prompt=(f'CODEBOOK[{codebook}]\n'
                    f'CASE[{cases[cls]}]\n'
                    f'QUERY[Return exactly one symbol from this episode codebook.]')
            row={
              'schema':'ENTITYOS_HCU_DYNAMIC_BINDING_CANDIDATE/v2',
              'evidence_class':'METHOD_ONLY_SYNTHETIC_BINDING',
              'reality_level':'R2',
              'family_id':f'BIND_{tid}_F01',
              'provenance_ancestry_id':'trigger2-binding-v2-synthetic-swarm',
              'canonical_truth_allowed':False,
              'direct_effect_authority':False,
              'fact_status':'NOT_APPLICABLE',
              'target_type':'EPISODE_LOCAL_CODEBOOK_BINDING',
              'split':'TRAIN_CANDIDATE',
              'split_unit':'CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY',
              'selected_using_holdout':False,
              'template_id':tid,
              'permutation_id':f'S3_{pidx}',
              'semantic_class_internal':cls,
              'codebook_display_order':display_order,
              'codebook_mapping':mapping,
              'prompt':prompt,
              'target':mapping[cls],
              'abi_compile_status':'PLACEHOLDER_ONLY_REQUIRES_VERIFIED_46_ATOM_TABLE',
              'model_feed_ready':False,
            }
            rows.append(row)

neg=[]
neg.append({
 'id':'NEG_PERM_METADATA_ONLY','expected':'REJECT_GENERATOR',
 'description':'Permutation metadata says S3_1 but target is derived from the unpermuted mapping.',
 'reason':'Permutation must causally construct class-to-symbol mapping; metadata-only permutation recreates the known critical generator defect.'})
neg.append({
 'id':'NEG_TARGET_LABEL_LEAK','expected':'REJECT_ROW',
 'description':'CASE text literally contains the target class token outside the CODEBOOK span.',
 'reason':'Class labels are allowed only in the preregistered codebook span for this v2 interpretation.'})
neg.append({
 'id':'NEG_DUP_ANCESTRY_SPLIT','expected':'REJECT_SPLIT',
 'description':'Rows sharing one provenance ancestry are divided across train and frozen holdout.',
 'reason':'Family/provenance ancestry is the split unit; this would leak causal ancestry.'})
neg.append({
 'id':'NEG_COUNTERBALANCE','expected':'REJECT_DATASET',
 'description':'One class-symbol pair occurs more often than another within a template family.',
 'reason':'This microseed requires exact class-symbol counterbalance under full S3 coverage.'})
neg.append({
 'id':'NEG_HOLDOUT_TEMPLATE_REUSE','expected':'REJECT_SELECTION',
 'description':'The frozen fifth template is used during validation or prompt iteration.',
 'reason':'Frozen unseen-template family must remain absent from train and validation/hyperparameter selection.'})

pair_counts={}
for r in rows:
    k=(r['template_id'],r['semantic_class_internal'],r['target'])
    pair_counts[k]=pair_counts.get(k,0)+1
expected_pair_count=2
balance_ok=all(v==expected_pair_count for v in pair_counts.values()) and len(pair_counts)==len(templates)*9
full_s3_ok=all({r['permutation_id'] for r in rows if r['template_id']==tid}=={f'S3_{i}' for i in range(6)} for tid in templates)
leak_ok=True
leaks=[]
for i,r in enumerate(rows):
    case=r['prompt'].split('CASE[',1)[1].split(']\nQUERY[',1)[0]
    for c in classes:
        if re.search(rf'\b{c}\b',case,flags=re.I):
            leak_ok=False; leaks.append((i,c))

bundle={
 'schema':'CLAY_TRIGGER2_DYNAMIC_BINDING_SWARM_MICROSEED/v2',
 'date':'2026-08-25',
 'purpose':'Install the measured missing computation: semantic decision -> episode-local codebook lookup -> symbol emission, without retraining already-present semantic read/symbol write/carrier binding as the primary objective.',
 'source_evidence_scope':{
   'measured_model':'Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1@591852bda6e1979f59e4b0f5ee2919697b12e936',
   'binding_baseline':0.3611111111111111,
   'context_transfer_baseline':0.5254629629629629,
   'target_acceptance':0.90,
   'known_measurement_boundary':'Model-specific numerical claims only; this synthetic seed grants no training/J-Space/HCU runtime credit.'},
 'preregistered_class_word_resolution':'ALLOW/DENY/ABSTAIN may appear only inside the explicit CODEBOOK span. CASE and QUERY text must not contain these class tokens. A separately versioned label-free variant may be studied later but is not silently mixed here.',
 'swarm_roles':[
   {'role':'GENERATOR','job':'Generate full-S3 episode-local remapping examples across four structurally distinct context families.'},
   {'role':'PERMUTATION_ADVERSARY','job':'Recompute target from realized mapping; reject metadata-only permutations.'},
   {'role':'LEAK_AUDITOR','job':'Reject target-class tokens outside CODEBOOK and provenance/template split leakage.'},
   {'role':'EPISTEMIC_REVIEWER','job':'Check that case semantics preserve EntityOS/HCU authority and UNKNOWN boundaries.'},
   {'role':'STATISTICAL_REVIEWER','job':'Check exact class-symbol counterbalance and full S3 coverage.'},
   {'role':'DISTILLER','job':'Keep only rows passing all reviewers; do not promote placeholders to model-feed-ready data.'}],
 'train_candidate_rows':len(rows),
 'templates_train':list(templates),
 'frozen_holdout_template_policy':'A fifth structurally novel template family is reserved and MUST NOT be generated, viewed, or tuned against in this microseed.',
 'audit':{
   'full_s3_per_template':full_s3_ok,
   'exact_class_symbol_counterbalance':balance_ok,
   'class_token_leak_outside_codebook':not leak_ok,
   'leak_locations':leaks,
   'expected_pair_count_per_template_class_atom':expected_pair_count,
   'model_feed_ready':False,
   'reason_not_feed_ready':'Exact 46 accepted ABI atom strings/row identities are not present in current canonical repo context; placeholders must be compiled only after manifest-bound atom-table verification.'},
 'hard_negative_reviews':neg,
 'external_method_hypothesis':{
   'claim':'Attention-mediated routing is a plausible mechanism for the missing dynamic binding, but this is not yet a model-specific fact for the target checkpoint.',
   'support':'Recent variable-binding work reports learned attention-mediated routing and residual-stream addressable memory in symbolic programs.',
   'falsifier':'Matched post-training causal tests show equivalent binding without the implicated pathways, or a different module is necessary/sufficient.'},
 'credits':{'training_executed':False,'training_credit':0,'qwen35_jspace_runtime_credit':0,'whole_hcu_runtime_credit':0,'whole_entityos_hcu_runtime_credit':0}
}

with open('trigger2_binding_microseed_v2.jsonl','w') as f:
    for r in rows:
        f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
with open('trigger2_binding_swarm_audit_v2.json','w') as f:
    json.dump(bundle,f,ensure_ascii=False,indent=2)
print(json.dumps({'rows':len(rows),'full_s3_ok':full_s3_ok,'balance_ok':balance_ok,'leak_ok':leak_ok,'seed_sha256':hashlib.sha256(open('trigger2_binding_microseed_v2.jsonl','rb').read()).hexdigest(),'audit_sha256':hashlib.sha256(open('trigger2_binding_swarm_audit_v2.json','rb').read()).hexdigest()},indent=2))
