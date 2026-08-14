#!/usr/bin/env python3
import itertools, json, hashlib
from collections import Counter


def relation(invert=False):
    rows=[]
    for a,b,c in itertools.product([0,1], repeat=3):
        y=(a^b^c) ^ int(invert)
        rows.append((a,b,c,y))
    return rows


def pair_marginals(rows):
    names=['A','B','C','Y']
    out={}
    for i in range(4):
        for j in range(i+1,4):
            cnt=Counter((r[i],r[j]) for r in rows)
            out[f'{names[i]}-{names[j]}']={f'{x}{y}':cnt[(x,y)] for x,y in itertools.product([0,1],repeat=2)}
    return out


def tuple_truth(rows):
    return {f'{a}{b}{c}':y for a,b,c,y in rows}


def sha(obj):
    b=json.dumps(obj, sort_keys=True, separators=(',',':')).encode()
    return hashlib.sha256(b).hexdigest()


r0=relation(False)
r1=relation(True)
pm0=pair_marginals(r0)
pm1=pair_marginals(r1)
assert pm0==pm1
assert tuple_truth(r0)!=tuple_truth(r1)


def reified(rows, relation_id):
    return {
      'relation_id': relation_id,
      'roles': ['A','B','C','Y'],
      'incidence_edges': [[relation_id, role] for role in ['A','B','C','Y']],
      'tuples': [list(r) for r in rows],
    }

inc0=reified(r0,'R_PARITY')
inc1=reified(r1,'R_INV_PARITY')
assert sha(inc0)!=sha(inc1)

facets=[
  {'value':'route_A','context':'low_risk','status':'CANDIDATE'},
  {'value':'route_B','context':'high_risk','status':'CANDIDATE'},
]
queries=['low_risk','high_risk']*50
collapsed=facets[-1]
acc_collapsed=sum(collapsed['value']==('route_A' if q=='low_risk' else 'route_B') for q in queries)/len(queries)
acc_hp=sum(next(f['value'] for f in facets if f['context']==q)==('route_A' if q=='low_risk' else 'route_B') for q in queries)/len(queries)

correct=0
for a,b,c,y in r0:
    h=a^b
    yp=h^c
    correct += yp==y
latent_pairwise_accuracy=correct/len(r0)

result={
  'experiment':'HP-PAIRWISE-REDUCTION-FALSIFIER-V1',
  'rows_per_relation':len(r0),
  'pairwise_projection_collision':pm0==pm1,
  'pairwise_projection_hash':sha(pm0),
  'full_relation_hash_parity':sha(tuple_truth(r0)),
  'full_relation_hash_inverted':sha(tuple_truth(r1)),
  'reified_incidence_distinguishes_relations':sha(inc0)!=sha(inc1),
  'contextual_projection_accuracy_collapsed':acc_collapsed,
  'contextual_projection_accuracy_hyperposition':acc_hp,
  'latent_pairwise_state_machine_accuracy':latent_pairwise_accuracy,
  'conclusions':[
    'naive pairwise projection can destroy higher-order relation identity',
    'pairwise physical incidence with a reified relation identity can preserve n-ary semantics exactly',
    'contextual facets prevent destructive collapse under context swaps',
    'finite higher-order semantics remain computable by pairwise/state-machine decomposition with auxiliary state; Hyperposition is not a hypercomputation proof',
    'irreducibility must be scoped to comparator class and resource/intervention budget, not asserted absolutely'
  ]
}
print(json.dumps(result, indent=2, sort_keys=True))
