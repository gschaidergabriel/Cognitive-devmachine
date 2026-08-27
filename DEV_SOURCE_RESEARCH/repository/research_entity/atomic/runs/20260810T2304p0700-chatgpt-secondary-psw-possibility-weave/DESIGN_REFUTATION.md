# PSW-001 design refutation

## Decision

`Possibility State Weave` is **not promoted** as a new Frank v0.1 organ or new Hyperposition semantics.

The candidate successfully demonstrated that unresolved alternatives can be much cheaper than N fully materialized worlds when divergence and transition read-signature diversity are low. It did **not** demonstrate that PSW is the mechanism uniquely responsible for those gains.

## Why the candidate loses

The strongest conventional baseline was not FULL_COPY. It was:

`immutable base + sparse branch overlay + exact branch identity metadata + pure transition memoization keyed by exact read signature`.

For every one of 168 scaling cells, this baseline and PSW produced:

- the same exact branch reconstruction;
- the same pure outputs;
- the same number of unique read signatures;
- therefore the same number of required pure transition evaluations.

PSW's median local time was 1.00937x the overlay-memo baseline and its wire proxy was 1.01518x the ordinary overlay metadata. Which side was slightly faster varied cell by cell, indicating implementation constant-factor/noise differences rather than a PSW-specific computational advantage.

## What is real

Two mechanisms are strongly supported **as conventional implementation techniques**:

1. sparse shared state is extremely effective when alternatives differ little;
2. pure computation can be reused across alternatives when an exact current transition contract proves identical material read signatures.

Neither mechanism needs a new PSW semantic object.

## Where sharing stops paying

In a six-seed representative F=1024, N=256, read-set=16 series:

- divergence 0%: 1 unique signature; sharing factor 256x; overlay-memo ~0.239x FULL_COPY time;
- 1%: median 37.5 signatures; ~6.83x sharing; ~0.403x time;
- 5%: ~145.5 signatures; ~1.76x sharing; ~0.751x time;
- 10%: ~213 signatures; ~1.20x sharing; ~0.979x time;
- 25%: ~253 signatures; ~1.01x sharing; ~1.169x time;
- 50%: 256 signatures; 1x sharing; ~1.194x time.

Thus a universal shared-alternative representation is not justified. There is a workload crossover.

## Strong positive salvage: adaptive physical representation

A simple synthetic policy using read-signature density to choose between `OVERLAY_MEMO` and `FULL_COPY` tracked the faster measured path closely. On a 48-cell separately seeded held-out set, threshold 0.8 yielded mean time regret 1.000829 relative to an oracle selecting the faster measured path per cell, with 95.8% of cells exactly selecting that measured winner.

This does **not** establish 0.8 as a production threshold. It establishes a more general implementation hypothesis:

> Hyperposition/ACEF branch state should not hard-code one physical representation. Measure divergence/signature density and choose or adapt representation under a semantic identity-preserving conversion contract.

## Critical safety lesion

The performance mechanism depends on read-set correctness.

Two branches were constructed with equal field `a`, different field `b`, and a transition that actually reads both. A deliberately incomplete signature that declared only `a` merged their computation. One branch received the wrong output. Restoring the exact read set eliminated the mismatch.

Therefore:

`PURE` alone is insufficient.

Cross-branch reuse requires an exact/conservative material read/effect contract. If the compiler/runtime cannot prove or conservatively determine the read set, sharing must fall back to separate execution.

This directly links the useful result to current ClayCode typed IR/type-effect/runtime work, but it does not justify changing ClayCode semantics in this ATOMIC run.

## Epistemic identity lesion

Two alternatives with exactly equal materialized state but different `hypothesis_id` and `provenance_root` were deliberately compared.

Payload-only deduplication would merge them. Exact branch identity correctly preserves them as distinct.

Physical storage may deduplicate identical immutable values, but epistemic identity/provenance cannot be discarded merely because current payload is equal.

## Effect boundary

PSW shared execution is restricted to exact PURE internal transitions. Unknown read sets, external reads/writes and security-sensitive operations fail closed for multi-branch lifting in the reference semantics.

Unresolved branches may produce effect proposals, but no external effect is executed for multiple hypothetical worlds. Normal Frank actor/capability/policy/reservation/attempt/outcome verification remains authoritative.

## Concurrent ACEF collision

During the run a concurrent ATOMIC candidate `ACEF` appeared. ACEF already represents hypothesis branches as sets of epoch/identity/lease-bound `SemanticDelta` objects inside cognitive transactions. This increases the architecture-duplication penalty for PSW. PSW should not become a second branch-state substrate.

The benchmark result is still useful as a **physical representation/runtime policy** that ACEF/Hyperposition could consume if those semantics are later admitted.

## Final candidate status

`REFUTED_AS_DISTINCT_ARCHITECTURE / USEFUL_IMPLEMENTATION_ENVELOPE`

No architecture promotion.
No truth promotion.
No effect authority.
No Harness mutation.
No training.
