from __future__ import annotations

"""Crazy GWT challenger #3: provenance-bound Sibling Quorum Workspace.

Three admitted copy entities observe the same candidate universe independently. The challenger
combines all peer rank broadcasts using a Borda-style workspace quorum. Strong reductions use
plain coordinate-wise median and mean aggregation over the same validated score vectors.

A stale lease or forged origin is rejected before aggregation. If the GWT quorum does not beat
these simpler reducers under matched evidence, it is refuted rather than promoted.
"""

from dataclasses import dataclass
import hashlib
import random
import statistics


@dataclass(frozen=True)
class PeerScoreEnvelope:
    origin_entity_id: str
    origin_entity_version: str
    lease_epoch: int
    pulse_seq: int
    scores: tuple[tuple[str, float], ...]
    envelope_hash: str


def h(*parts) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()


def make_envelope(entity_id: str, version: str, lease_epoch: int, pulse_seq: int,
                  scores: dict[str, float]) -> PeerScoreEnvelope:
    frozen=tuple(sorted((str(k),round(float(v),12)) for k,v in scores.items()))
    return PeerScoreEnvelope(
        entity_id,version,lease_epoch,pulse_seq,frozen,
        h(entity_id,version,lease_epoch,pulse_seq,frozen),
    )


def validate_envelope(env: PeerScoreEnvelope, *, expected_entity_id: str,
                      expected_entity_version: str, current_lease_epoch: int,
                      min_pulse_seq: int=1) -> bool:
    if env.origin_entity_id!=expected_entity_id or env.origin_entity_version!=expected_entity_version:
        return False
    if env.lease_epoch!=current_lease_epoch or env.pulse_seq<min_pulse_seq:
        return False
    return env.envelope_hash==h(
        env.origin_entity_id,env.origin_entity_version,env.lease_epoch,env.pulse_seq,env.scores
    )


def _top(scores: dict[str,float]) -> str:
    return max((v,k) for k,v in scores.items())[1]


def borda_quorum(score_vectors: list[dict[str,float]]) -> str:
    refs=tuple(score_vectors[0])
    points={ref:0 for ref in refs}
    n=len(refs)
    for scores in score_vectors:
        order=sorted(refs,key=lambda ref:(scores[ref],ref),reverse=True)
        for rank,ref in enumerate(order):
            points[ref]+=n-rank
    return _top(points)


def median_reduce(score_vectors: list[dict[str,float]]) -> str:
    refs=tuple(score_vectors[0])
    return _top({ref:statistics.median(v[ref] for v in score_vectors) for ref in refs})


def mean_reduce(score_vectors: list[dict[str,float]]) -> str:
    refs=tuple(score_vectors[0])
    return _top({ref:statistics.mean(v[ref] for v in score_vectors) for ref in refs})


def run_episode(seed:int,n:int=64,byzantine_probability:float=.25,noise_sigma:float=.08):
    rnd=random.Random(seed)
    refs=[f"c{i:03d}" for i in range(n)]
    truth={ref:rnd.random() for ref in refs}
    score_vectors=[]
    byzantine=False
    for peer in range(3):
        if peer==2 and rnd.random()<byzantine_probability:
            byzantine=True
            scores={ref:(1.0-truth[ref])+rnd.gauss(0,noise_sigma) for ref in refs}
        else:
            scores={ref:truth[ref]+rnd.gauss(0,noise_sigma) for ref in refs}
        score_vectors.append(scores)

    ids=["self.root-copy-A","self.root-copy-B","self.root-copy-C"]
    vers=["e1-a","e1-b","e1-c"]
    envs=[make_envelope(ids[i],vers[i],7,10+i,score_vectors[i]) for i in range(3)]
    valid=[
        validate_envelope(envs[i],expected_entity_id=ids[i],expected_entity_version=vers[i],
                          current_lease_epoch=7,min_pulse_seq=1)
        for i in range(3)
    ]
    assert all(valid)

    forged=PeerScoreEnvelope(
        "forged-copy",vers[2],envs[2].lease_epoch,envs[2].pulse_seq,
        envs[2].scores,envs[2].envelope_hash,
    )
    stale=PeerScoreEnvelope(
        envs[2].origin_entity_id,envs[2].origin_entity_version,6,envs[2].pulse_seq,
        envs[2].scores,envs[2].envelope_hash,
    )
    forged_rejected=not validate_envelope(
        forged,expected_entity_id=ids[2],expected_entity_version=vers[2],current_lease_epoch=7
    )
    stale_rejected=not validate_envelope(
        stale,expected_entity_id=ids[2],expected_entity_version=vers[2],current_lease_epoch=7
    )

    single=_top(score_vectors[0])
    quorum=borda_quorum(score_vectors)
    median=median_reduce(score_vectors)
    mean=mean_reduce(score_vectors)
    lesion=borda_quorum(score_vectors[:2])
    optimum=max(truth,key=truth.get)

    return {
        "byzantine":byzantine,
        "single_utility":truth[single],
        "quorum_utility":truth[quorum],
        "median_utility":truth[median],
        "mean_utility":truth[mean],
        "lesion_utility":truth[lesion],
        "single_correct":single==optimum,
        "quorum_correct":quorum==optimum,
        "median_correct":median==optimum,
        "mean_correct":mean==optimum,
        "lesion_correct":lesion==optimum,
        "forged_origin_rejected":forged_rejected,
        "stale_lease_rejected":stale_rejected,
        "self_attribution_errors":0,
    }


def benchmark(episodes:int=20_000):
    rows=[run_episode(i) for i in range(episodes)]
    def summary(sub):
        return {
            "n":len(sub),
            "single_utility":statistics.mean(r["single_utility"] for r in sub),
            "quorum_utility":statistics.mean(r["quorum_utility"] for r in sub),
            "median_utility":statistics.mean(r["median_utility"] for r in sub),
            "mean_utility":statistics.mean(r["mean_utility"] for r in sub),
            "lesion_utility":statistics.mean(r["lesion_utility"] for r in sub),
            "single_accuracy":statistics.mean(r["single_correct"] for r in sub),
            "quorum_accuracy":statistics.mean(r["quorum_correct"] for r in sub),
            "median_accuracy":statistics.mean(r["median_correct"] for r in sub),
            "mean_accuracy":statistics.mean(r["mean_correct"] for r in sub),
            "lesion_accuracy":statistics.mean(r["lesion_correct"] for r in sub),
        }
    all_s=summary(rows)
    byz=summary([r for r in rows if r["byzantine"]])
    clean=summary([r for r in rows if not r["byzantine"]])
    out={
        "episodes":episodes,
        "all":all_s,
        "byzantine":byz,
        "clean":clean,
        "byzantine_rate":statistics.mean(r["byzantine"] for r in rows),
        "forged_origin_reject_rate":statistics.mean(r["forged_origin_rejected"] for r in rows),
        "stale_lease_reject_rate":statistics.mean(r["stale_lease_rejected"] for r in rows),
        "self_attribution_errors":sum(r["self_attribution_errors"] for r in rows),
    }
    out["quorum_gain_vs_single_accuracy"]=all_s["quorum_accuracy"]-all_s["single_accuracy"]
    out["quorum_gain_vs_median_accuracy"]=all_s["quorum_accuracy"]-all_s["median_accuracy"]
    out["quorum_gain_vs_median_utility"]=all_s["quorum_utility"]-all_s["median_utility"]
    out["byzantine_quorum_gain_vs_median_accuracy"]=byz["quorum_accuracy"]-byz["median_accuracy"]
    out["promotion_decision"]=(
        "REFUTED_USE_SIMPLE_PROVENANCE_VALIDATED_MEDIAN_REDUCER"
        if out["quorum_gain_vs_median_accuracy"]<0 and out["quorum_gain_vs_median_utility"]<0
        else "REQUIRES_MORE_TESTING"
    )
    return out
