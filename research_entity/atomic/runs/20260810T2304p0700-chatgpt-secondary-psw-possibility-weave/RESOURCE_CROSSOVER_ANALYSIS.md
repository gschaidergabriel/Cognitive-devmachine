# Resource crossover analysis

## Why the crossover matters

Sparse sharing is not universally faster. It trades repeated state/compute for indirection, signature construction, cache lookup and metadata.

The representative six-seed F=1024/N=256/read16 series shows the transition clearly:

| divergence | median unique signatures | sharing factor | overlay wire / full | overlay-memo time / full | PSW time / full |
|---:|---:|---:|---:|---:|---:|
| 0% | 1.0 | 256.00x | 0.00784 | 0.2385 | 0.2468 |
| 1% | 37.5 | 6.83x | 0.01755 | 0.4033 | 0.4065 |
| 5% | 145.5 | 1.76x | 0.05751 | 0.7507 | 0.7401 |
| 10% | 213.0 | 1.20x | 0.10733 | 0.9786 | 0.9522 |
| 25% | 253.0 | 1.01x | 0.25776 | 1.1691 | 1.1222 |
| 50% | 256.0 | 1.00x | 0.50769 | 1.1942 | 1.1802 |

The storage proxy remains favorable to overlay even at high divergence because the common base and repeated field keys are not serialized N times. Compute sharing, however, disappears much earlier: once nearly every branch has a unique read signature, signature construction/cache lookup is pure overhead.

## Important distinction: state divergence != read-signature divergence

The physically relevant quantity for a particular pure transition is not total branch-state difference by itself. A branch can differ in 25% of all state fields while a transition reads only four invariant fields. Then compute reuse may still be high.

Conversely, only 1% global state divergence can destroy sharing for a transition whose 16 material reads happen to intersect those differences.

Therefore a production selector should observe or estimate at least:

- branch count;
- sparse delta density;
- exact material read-set size;
- read-signature diversity for the current transition;
- cost of constructing that signature;
- transition compute cost;
- conversion/materialization cost;
- recent measured cache hit rate.

## Why a fixed divergence threshold is insufficient

A rule such as `divergence <= 10% -> share` is only a synthetic convenience. It fails when divergence lies outside a transition's read-set, or when a cheap transition costs less than signature bookkeeping.

The signature-density probe is closer to the mechanism. In the synthetic main grid, choosing overlay memo when `unique_read_signatures / branches <= 0.8` tracked the measured per-cell winner closely; the same rule retained low regret on a separately seeded held-out grid. That numeric threshold is not portable and must not be owner-fixed as architecture.

## Future target measurement

A real Frank trace should record, for PURE candidate transitions only:

`(branches, delta_density, read_set_size, unique_read_signatures, transition_cost, signature_cost, materialized_cost, sparse_cost, current representation)`

Then periodically run resource-matched counterfactual samples rather than assuming one representation is universally superior.

The representation policy must be observational: it may optimize physical execution but may never alter which alternatives exist, their truth status, provenance, or authority.
