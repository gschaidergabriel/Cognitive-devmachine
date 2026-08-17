from __future__ import annotations
import hashlib, json, random

SEEDS = range(20)
PAIRS = 10000
KEYS = tuple(f"subject:{i}" for i in range(64))
KINDS = (
    ('claim_append', 0.65, True),
    ('retract', 0.10, False),
    ('resolve_single', 0.10, False),
    ('external_effect', 0.10, False),
    ('unknown', 0.05, False),
)

def draw_kind(rng):
    x=rng.random(); c=0
    for name,p,mono in KINDS:
        c += p
        if x <= c: return name,mono
    return KINDS[-1][0],KINDS[-1][2]

def run(seed):
    rng=random.Random(seed)
    names=['no_coord','session_generation','resource_lock_all','occ_context_witness','mca_typed_aperture','random_same_budget','mca_1pct_misclassification']
    out={n:{'pairs':0,'unsafe':0,'violation':0,'coordinate':0,'false_coordinate':0,'safe':0,'safe_parallel':0} for n in names}
    for _ in range(PAIRS):
        k1=rng.choice(KEYS)
        # 35% deliberate same-subject pressure, else random key.
        k2=k1 if rng.random()<0.35 else rng.choice(KEYS)
        kind1,mono1=draw_kind(rng); kind2,mono2=draw_kind(rng)
        same_session = rng.random()<0.25
        same_key = k1==k2
        unsafe = same_key and not (mono1 and mono2)
        safe = not unsafe
        # Current-generation style approximation: any same-session concurrent change trips;
        # cross-session semantic conflicts are invisible.
        session_coord = same_session
        resource_coord = same_key
        occ_coord = same_key  # write/write or read/write witness collision
        mca_coord = same_key and not (mono1 and mono2)
        # Resource-matched randomized control: same global coordination budget as MCA in expectation,
        # but independent of semantics.
        random_coord = rng.random() < (0.35 * (1 - 0.65*0.65))
        # One bounded adversarial ablation: a 1% false MONOTONE classification on each nonmonotone op.
        seen_mono1 = mono1 or ((not mono1) and rng.random()<0.01)
        seen_mono2 = mono2 or ((not mono2) and rng.random()<0.01)
        mca_bad = same_key and not (seen_mono1 and seen_mono2)
        coords={
            'no_coord':False,
            'session_generation':session_coord,
            'resource_lock_all':resource_coord,
            'occ_context_witness':occ_coord,
            'mca_typed_aperture':mca_coord,
            'random_same_budget':random_coord,
            'mca_1pct_misclassification':mca_bad,
        }
        for n,c in coords.items():
            d=out[n]; d['pairs']+=1; d['unsafe']+=int(unsafe); d['safe']+=int(safe); d['coordinate']+=int(c)
            d['violation']+=int(unsafe and not c)
            d['false_coordinate']+=int(safe and c)
            d['safe_parallel']+=int(safe and not c)
    return out

raw=[run(s) for s in SEEDS]
summary={}
for n in raw[0]:
    a={k:sum(r[n][k] for r in raw) for k in raw[0][n]}
    summary[n]={
        'pairs':a['pairs'],
        'unsafe_pairs':a['unsafe'],
        'coordination_rate':round(a['coordinate']/a['pairs'],6),
        'violation_rate_on_unsafe':round(a['violation']/a['unsafe'],6) if a['unsafe'] else 0,
        'false_coordination_rate_on_safe':round(a['false_coordinate']/a['safe'],6) if a['safe'] else 0,
        'safe_parallelization_rate':round(a['safe_parallel']/a['safe'],6) if a['safe'] else 0,
    }
payload={
    'experiment':'MCA-001 typed antimonotone aperture pairwise discriminator',
    'seeds':list(SEEDS),'pairs_per_seed':PAIRS,'total_pairs':PAIRS*len(list(SEEDS)),
    'model':{
        'same_subject_pressure':0.35,
        'same_session_probability':0.25,
        'operation_mix':{name:p for name,p,_ in KINDS},
        'typed_law':'claim_append is monotone; retract/resolve/effect/unknown require aperture; unknown fails closed',
        'safety_truth':'same subject + at least one nonmonotone operation requires coordination',
    },
    'results':summary,
    'bounded_adversarial_ablation':'mca_1pct_misclassification flips 1% of nonmonotone typed operations to monotone',
}
base=json.dumps(payload,sort_keys=True,separators=(',',':')).encode(); payload['receipt_sha256']=hashlib.sha256(base).hexdigest()
print(json.dumps(payload,indent=2,sort_keys=True))
