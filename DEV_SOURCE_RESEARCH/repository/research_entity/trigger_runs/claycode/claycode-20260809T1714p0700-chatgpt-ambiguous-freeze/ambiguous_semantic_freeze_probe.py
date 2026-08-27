import json, hashlib, random

RELATIONS = {
    'lowers': {'arity': 3},
    'consumes': {'arity': 2},
    'writes': {'arity': 2},
    'personalizes_for_Andreas': {'arity': 1},
    'preserves_general_transfer_variants': {'arity': 1},
    'when': {'arity': 2},
    'and': {'arity': 2},
}

def H(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def validate(node):
    if not isinstance(node, dict): return False
    rel = node.get('rel')
    args = node.get('args')
    if rel not in RELATIONS or not isinstance(args, list): return False
    if len(args) != RELATIONS[rel]['arity']: return False
    return all(validate(a) if isinstance(a, dict) else isinstance(a, str) and bool(a) for a in args)

legacy = {
 'L1': 'Needle.lowers EffectIntent -> concrete_adapter_plan',
 'L2': 'Claude_only consumes latest stack + writes task receipts',
 'L3': 'training_data personalizes_for_Andreas_when_FRANK_target && preserves_general_transfer_variants'
}

plausible = {
 'L1': [
   {'rel':'lowers','args':['Needle','EffectIntent','concrete_adapter_plan']},
   {'rel':'when','args':[{'rel':'lowers','args':['Needle','EffectIntent','concrete_adapter_plan']},'arrow_as_implication_marker']},
 ],
 'L2': [
   {'rel':'and','args':[{'rel':'consumes','args':['Claude_only','latest_stack']},{'rel':'writes','args':['Claude_only','task_receipts']}]},
   {'rel':'writes','args':[{'rel':'consumes','args':['Claude_only','latest_stack']},'task_receipts']},
 ],
 'L3': [
   {'rel':'and','args':[{'rel':'when','args':['FRANK_target',{'rel':'personalizes_for_Andreas','args':['training_data']}]},{'rel':'preserves_general_transfer_variants','args':['training_data']}]},
   {'rel':'and','args':[{'rel':'personalizes_for_Andreas','args':['training_data']},{'rel':'preserves_general_transfer_variants','args':['FRANK_target']}]},
 ],
}

frozen_candidates = {
 'L1': {'rel':'lowers','args':['Needle','EffectIntent','concrete_adapter_plan']},
 'L2': {'rel':'and','args':[{'rel':'consumes','args':['Claude_only','latest_stack']},{'rel':'writes','args':['Claude_only','task_receipts']}]},
 'L3': {'rel':'and','args':[{'rel':'when','args':['FRANK_target',{'rel':'personalizes_for_Andreas','args':['training_data']}]},{'rel':'preserves_general_transfer_variants','args':['training_data']}]},
}

results = {'legacy': legacy, 'lines': {}, 'mutations': {}}
for k in legacy:
    hs = [H(x) for x in plausible[k]]
    results['lines'][k] = {
        'plausible_ast_count': len(plausible[k]),
        'plausible_hashes_distinct': len(set(hs)) == len(hs),
        'frozen_candidate_valid': validate(frozen_candidates[k]),
        'frozen_candidate_hash': H(frozen_candidates[k]),
        'auto_normalize_safe': False,
    }

rejected = 0
N = 10000
for i in range(N):
    bad = {'rel': f'unknown_rel_{i}_{random.randrange(1<<30)}', 'args':['a','b']}
    rejected += (not validate(bad))
results['mutations']['unknown_relation_rejected'] = f'{rejected}/{N}'

arity_rejected = 0
for i in range(N):
    rel = random.choice(list(RELATIONS))
    expected = RELATIONS[rel]['arity']
    n = expected + random.choice([-1,1])
    n = max(0,n)
    bad = {'rel': rel, 'args': ['x']*n}
    arity_rejected += (not validate(bad))
results['mutations']['wrong_arity_rejected'] = f'{arity_rejected}/{N}'

whitespace_stable = 0
for i in range(N):
    x = json.loads(json.dumps(frozen_candidates['L2']))
    raw = json.dumps(x, indent=(i%4)+1)
    reparsed = json.loads(raw)
    whitespace_stable += (H(reparsed) == H(frozen_candidates['L2']))
results['mutations']['surface_whitespace_semantic_hash_stable'] = f'{whitespace_stable}/{N}'

results['interpretation'] = (
  'All three legacy lines admit at least two materially different candidate ASTs, so automatic normalization is unsafe. '
  'After explicit semantic freeze into registry-gated n-ary PredicateIR, each selected candidate has one stable canonical hash; '
  'unknown relation names and wrong arities fail closed.'
)
print(json.dumps(results, indent=2, sort_keys=True))
