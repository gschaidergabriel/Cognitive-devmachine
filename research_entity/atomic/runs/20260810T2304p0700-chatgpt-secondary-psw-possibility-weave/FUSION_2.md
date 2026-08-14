# Fusion 2 — PSW novelty collapses into a measurable Frank-specific composition

## External collision result

The broad mechanism is not novel.

- Persistent data structures already preserve multiple versions by structural sharing.
- Variational execution already executes many alternative configurations together, tracks alternative concrete values and shares execution where configurations behave alike.
- Faceted execution already represents conditional/guarded alternative values.
- Self-adjusting computation already tracks dependencies and propagates only the effects of changed inputs/decisions.

Therefore the phrases `shared alternative state`, `guarded values`, `execute similar branches together`, `lazy divergence`, `dependency-driven recomputation` and `persistent versions` cannot carry a novelty claim for PSW.

## What survives as a Frank-specific candidate

The only potentially useful composition is a deliberately narrow semantic package for **epistemic Hyperposition alternatives** rather than software configurations or access-control views:

1. every branch remains an unresolved hypothesis/proposal, never truth or authority;
2. branch identity is bound to `self.root`, exact base/state epoch, branch revision, hypothesis identity and provenance root;
3. equal payload does not imply merge when provenance/entity/version distinctions are materially different;
4. shared execution is legal only for transitions certified `PURE` with an exact admitted read-set; unknown/dynamic read-set disables sharing;
5. branches may be grouped by exact read signature for a pure transition; one execution result may be lifted to all members only if the transition result/write-set is deterministic under that signature;
6. any external/effectful/authority-sensitive transition is not lifted across unresolved branches; it remains a proposal and must later execute only through the ordinary single-current authority path;
7. restart cannot invent branch transitions that were not executed/persisted;
8. collapse requires admitted evidence/policy and records discarded alternatives as historical alternatives rather than rewriting them as never having existed.

## Revised candidate status

`PSW-001` remains testable but its novelty ceiling is:

`PROJECT_SPECIFIC_COMBINATION_ONLY`

before benchmarking.

## Hypotheses retired or demoted

- H3 persistent DAG: known method; baseline only.
- H4 guarded values: near-equivalent to faceted/variational values; baseline only.
- H5 lazy fork: known lazy/variational technique; retained only as a PSW operational feature.
- H6 causal influence slicing: established change-propagation/dependence analogue; baseline/ablation axis.
- H9 genome analogy: collapses to sparse overlay + lineage, no independent mechanism.
- H10 quantum/deferred measurement analogy: collapses to symbolic/lazy execution; retired.
- H12 SIMD-over-worlds: ordinary vectorization/variational execution; implementation optimization only.
- H13 branch-epoch braid: ordinary epoch/generation/provenance fencing; required safety baseline, not novelty.

## Hypotheses still scientifically useful

- H2 PSW as the full project-specific semantic composition.
- H8 adaptive representation selector: likely more useful than fixing PSW globally if regimes differ strongly.
- H14 factorized possibility graph: remains a separate future alternative when uncertainties form combinatorial cross-products; not selected this run because it risks a much larger solver/query architecture.

## Strongest counterhypothesis after research

`SPARSE_OVERLAY_MEMO` — immutable base + ordinary per-branch overrides + exact epoch/provenance metadata + memoization keyed by `(transition_identity, exact_read_signature)` — should reproduce the useful storage and pure-transition sharing of PSW with less architecture.

This baseline is intentionally strong. If it matches PSW on correctness and operation count and is equal/faster/smaller, PSW must be rejected as architecture.

## Benchmark focus after novelty collapse

Do not ask whether PSW beats FULL_COPY; that is too easy and scientifically weak.

Ask:

1. Does PSW beat `SPARSE_OVERLAY_MEMO` in any regime?
2. Is any difference caused by a defining PSW mechanism rather than implementation accident?
3. Does exact provenance/epoch safety cost enough to erase sharing gains?
4. At what branch-count/divergence/read-write regime does sharing stop paying?
5. Can an adaptive selector use simple measured features to choose a representation without semantic drift?

A negative candidate result may still yield a valuable Frank runtime rule: use conventional overlays and read-signature memoization only under measured low-divergence/pure-read regimes, and materialize otherwise.
