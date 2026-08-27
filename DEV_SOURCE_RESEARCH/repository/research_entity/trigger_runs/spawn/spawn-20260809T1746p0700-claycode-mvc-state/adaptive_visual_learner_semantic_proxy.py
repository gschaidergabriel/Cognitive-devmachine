from __future__ import annotations
from dataclasses import dataclass, replace
from enum import Enum
import random

class Tier(str, Enum):
    GOLD='GOLD'; SILVER='SILVER'; BRONZE='BRONZE'
class Result(str, Enum):
    KNOWN_HIGH_CONFIDENCE='KNOWN_HIGH_CONFIDENCE'
    KNOWN_NEEDS_CONFIRMATION='KNOWN_NEEDS_CONFIRMATION'
    AMBIGUOUS='AMBIGUOUS'; UNKNOWN='UNKNOWN'; CONFLICT='CONFLICT'

@dataclass(frozen=True)
class LearnerState:
    current_version: int
    candidate_version: int | None
    last_known_good: int
    backbone_version: int
    candidate_backbone_version: int | None
    admitted_examples: int
    bronze_seen: int
    training_paused: bool
    perception_enabled: bool
    budget_ms: int
    used_ms: int
    last_result: Result
    epoch: int

INIT = LearnerState(1, None, 1, 1, None, 0, 0, False, True, 10, 0, Result.UNKNOWN, 0)

def step(s: LearnerState, event: tuple) -> LearnerState:
    kind, *a = event
    e = s.epoch + 1
    if kind == 'observe':
        tier, result = Tier(a[0]), Result(a[1])
        if tier is Tier.BRONZE:
            return replace(s, bronze_seen=s.bronze_seen+1, last_result=result, epoch=e)
        return replace(s, admitted_examples=s.admitted_examples+1, last_result=result, epoch=e)
    if kind == 'budget':
        cost = int(a[0])
        used = s.used_ms + cost
        return replace(s, used_ms=used, training_paused=used > s.budget_ms, perception_enabled=True, epoch=e)
    if kind == 'candidate':
        version, backbone = int(a[0]), int(a[1])
        if s.training_paused or backbone != s.backbone_version:
            return replace(s, epoch=e)
        return replace(s, candidate_version=version, candidate_backbone_version=backbone, epoch=e)
    if kind == 'promote':
        gates_ok = bool(a[0])
        if (not gates_ok or s.candidate_version is None or
            s.candidate_backbone_version != s.backbone_version):
            return replace(s, epoch=e)
        return replace(s, last_known_good=s.current_version,
                       current_version=s.candidate_version,
                       candidate_version=None, candidate_backbone_version=None, epoch=e)
    if kind == 'rollback':
        return replace(s, current_version=s.last_known_good,
                       candidate_version=None, candidate_backbone_version=None, epoch=e)
    if kind == 'backbone':
        new = int(a[0])
        return replace(s, backbone_version=new, candidate_version=None,
                       candidate_backbone_version=None, epoch=e)
    raise AssertionError(kind)

def assert_invariants(prev: LearnerState, new: LearnerState, event: tuple):
    kind, *a = event
    assert new.perception_enabled, 'learning budget/failure must not disable perception'
    if kind == 'observe' and Tier(a[0]) is Tier.BRONZE:
        assert new.admitted_examples == prev.admitted_examples, 'BRONZE trained autonomously'
    if kind == 'candidate' and (prev.training_paused or int(a[1]) != prev.backbone_version):
        assert (new.candidate_version, new.candidate_backbone_version) == (prev.candidate_version, prev.candidate_backbone_version), 'rejected candidate request changed candidate state'
    if new.last_result in {Result.UNKNOWN, Result.AMBIGUOUS, Result.CONFLICT}:
        assert new.last_result == Result(a[1]) if kind == 'observe' else True
    if kind == 'budget' and new.used_ms > new.budget_ms:
        assert new.training_paused and new.perception_enabled
    if kind == 'promote' and bool(a[0]) and prev.candidate_version is not None and prev.candidate_backbone_version == prev.backbone_version:
        assert new.current_version == prev.candidate_version
        assert new.last_known_good == prev.current_version

def stream(seed: int, n: int=100):
    r = random.Random(seed)
    s = INIT
    out=[]
    results=list(Result)
    tiers=list(Tier)
    for _ in range(n):
        k=r.randrange(6)
        if k==0: ev=('observe', r.choice(tiers).value, r.choice(results).value)
        elif k==1: ev=('budget', r.randrange(0,8))
        elif k==2: ev=('candidate', r.randrange(2,20), r.choice([s.backbone_version, s.backbone_version+1]))
        elif k==3: ev=('promote', bool(r.randrange(2)))
        elif k==4: ev=('rollback',)
        else: ev=('backbone', r.randrange(1,4))
        ns=step(s,ev); assert_invariants(s,ns,ev); out.append(ns); s=ns
    return out

for seed in range(1000):
    a=stream(seed); b=stream(seed)
    assert a==b

s=INIT
b=step(s,('observe','BRONZE','KNOWN_HIGH_CONFIDENCE')); assert b.admitted_examples==0 and b.bronze_seen==1
stale=step(s,('candidate',2,2)); assert stale.candidate_version is None
for rr in ['UNKNOWN','AMBIGUOUS','CONFLICT']:
    x=step(s,('observe','SILVER',rr)); assert x.last_result.value==rr
p=step(s,('budget',11)); assert p.training_paused and p.perception_enabled
c=step(s,('candidate',2,1)); q=step(c,('promote',True)); assert q.current_version==2 and q.last_known_good==1
rb=step(q,('rollback',)); assert rb.current_version==1

mutations=0
try:
    bad=replace(b, admitted_examples=1); assert_invariants(s,bad,('observe','BRONZE','KNOWN_HIGH_CONFIDENCE'))
except AssertionError: mutations+=1
try:
    bad=replace(stale, candidate_version=2, candidate_backbone_version=2); assert_invariants(s,bad,('candidate',2,2))
except AssertionError: mutations+=1
try:
    bad=replace(p, training_paused=False); assert_invariants(s,bad,('budget',11))
except AssertionError: mutations+=1
try:
    bad=replace(q, last_known_good=2); assert_invariants(c,bad,('promote',True))
except AssertionError: mutations+=1
assert mutations==4

import json
print(json.dumps({
  'result':'PASS',
  'deterministic_streams':1000,
  'transitions_per_stream':100,
  'total_replayed_transitions':100000,
  'bronze_autotraining_guard':'PASS',
  'stale_backbone_guard':'PASS',
  'open_set_conflict_guard':'PASS',
  'budget_pause_preserves_perception':'PASS',
  'atomic_promotion_last_known_good':'PASS',
  'rollback':'PASS',
  'mutation_controls_killed':'4/4',
  'scope':'semantic proxy, not live FRANK/H1/H2 evidence'
}, indent=2))
