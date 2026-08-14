# ATOMIC deep run — CCW-001 Causal Closure Witness

## Final verdict

**CCW-001 is killed as a distinct default physical runtime architecture.**

The candidate asked whether Frank v0.1 should stop storing terminal `DONE` as independently writable semantic authority and instead expose terminality only as a read-only derived proposition over exact canonical causal support.

The strongest conventional baseline survived: canonical support references + one closure predicate/trigger + `REENTERED` and immutable DONE receipt in one SQLite transaction matched the candidate's encoded correctness/recovery while delivering much faster point reads. CCW therefore does not justify replacing the ordinary runtime shape.

However, one architectural law survives and should be carried into the conventional V17 repair:

> **A persisted DONE receipt may be cache/audit evidence, but it is not sufficient semantic authority. Terminal causal closure must remain independently re-derivable and revalidatable from exact canonical support.**

## Why this problem was selected

Fresh accepted-target evidence at `f649ce7ab8249c9dbc61ad7018804204ade53cb5` reproduced a V17 support-binding failure on the self-hosted Hostinger Ubuntu lane. The candidate verifier could report terminal DONE while V15 remained IDLE, V16 was unbound, canonical GWT/causal/delta support rows were absent and support identifiers were fabricated.

Current source explains the failure shape: the V17 candidate table contains episode/signal/causal/delta identifiers as text-like identities with nonempty checks, while its main canonical trigger verifies the V14 effect attempt/outcome relation but does not prove one coherent execution/GWT-use/credit/delta support chain.

Direct implementation repair was already occupied by PR279/PR280, so this run did not create another target branch. Instead it attacked the ontology of terminality itself.

## Search space

Fourteen hypotheses from seven families were generated: deletion of DONE authority; deletion of terminal receipts; factored terminality; a typed support hyperedge; event-sourced closure; bitemporal validity; Merkle-style closure hashes; non-authoritative caching; provenance expressions; typed proof objects; linear typestate/session progression; proof-carrying completion; monotone outcome/non-monotone causal separation; and the strongest ordinary persisted-receipt baseline.

External research then destroyed broad novelty claims. SQLite already supplies read-only derived views. Database research supplies incremental/materialized view maintenance. Proof-Carrying Code supplies proof validation. Provenance research supplies derivational explanations of query results. W3C PROV formalizes consistency constraints over provenance histories. Session/refinement/linear types supply typed protocol/resource progression.

CCW therefore retained only a Frank-specific semantic-deletion novelty class, not a general invention claim.

## Candidate semantics

`CausalClosureSupport` binds:

`effect + exact execution generation + verified outcome + workspace episode + reconstructed/used receiver path + causal credit + admitted semantic delta OR explicit typed no-learning + provenance-bound re-entry`.

`derive_causal_done()` is pure and returns a `CausalDoneProjection` only if every support relation is current, canonical and coherent.

A physical `DoneCache` is permitted for speed, but its laws explicitly declare it rebuildable and non-authoritative. Stale cache is ignored/rebuilt. Invalid support removes causal closure without creating effect retry authority. Verified external outcome remains durable independently.

## Executable discriminator

A deterministic local Python/SQLite model compared:

1. strongest conventional persisted DONE receipt using the same closure predicate and a trigger;
2. CCW using the same support tables and a read-only closure view with no DONE table.

The real current-V17 failure itself was not replaced by a local proxy; accepted-target negative evidence remained the baseline for that claim.

Local environment: Python 3.13.5, Linux 6.18.35 x86_64, SQLite 3.46.1. No real provider effect, target state mutation or training occurred.

### Mutation corpus

Fourteen cases were tested: one valid chain plus fabricated episode, wrong execution, wrong causal chain, wrong credit chain, invalid/not-admitted execution, unused/invalid GWT support, unused causal support, invalid credit, invalid delta, unverified outcome and not-REENTERED state.

Result under the shared strong closure predicate:

- conventional receipt: valid 1/1 accepted; invalid 0/13 accepted;
- CCW view: valid 1/1 visible; invalid 0/13 visible.

**Correctness tie.** This is the main result against CCW's distinctness.

### Atomic crash control

The conventional baseline was strengthened further: state transition, re-entry binding and DONE insert were placed in one explicit transaction. A fault was injected after REENTERED/re-entry writes but before DONE insert.

After rollback:

- effect state returned to VERIFIED;
- re-entry rows = 0;
- DONE rows = 0;
- closure rows = 0.

This kills the naive argument that a stored receipt necessarily creates an unavoidable crash window.

### Write protection

A direct INSERT into the CCW SQLite view failed because the view is read-only. This is a real mechanical benefit: terminal truth cannot be inserted through the ordinary table-write path unless somebody deliberately adds a write bridge such as an INSTEAD OF trigger.

### Support invalidation control

A valid terminal receipt and derived closure were first established. One admitted support delta was then invalidated in the research model.

Before invalidation:

- persisted receipt = present;
- derived closure = present.

After invalidation:

- persisted receipt = still present;
- derived closure = absent.

This is CCW's strongest surviving semantic property. A conventional design can match it, but only by revalidating the receipt against current support or explicitly maintaining invalidation/revocation state. Once it does that, the receipt is no longer sufficient semantic authority by itself — exactly the retained design law.

## Performance

Single scaling runs at N=1,000 / 5,000 / 20,000 showed the same direction: omitting the DONE table reduced build work/storage but made terminal point queries slower because the view must traverse the support chain.

The matched benchmark at N=10,000 used six alternating architecture orders and 3,000 deterministic random point queries per repetition.

Median across repetitions:

Conventional receipt:
- population: ~0.3477 s;
- DB size: 7,774,208 bytes;
- point median: ~3.911 us;
- point p95: ~4.262 us;
- point p99: ~5.348 us.

CCW:
- population: ~0.2496 s;
- DB size: 6,918,144 bytes;
- point median: ~15.606 us;
- point p95: ~21.907 us;
- point p99: ~33.986 us.

Ratios CCW/conventional:
- population time: 0.7158x;
- storage: 0.8899x;
- median point-read latency: 3.9896x;
- p95 point-read latency: 5.1337x.

The absolute read times remain microseconds in this local synthetic model, but the relative penalty is large and must not be hand-waved away. Full closure scans were even more unfavorable to the derived view. Production viability would require actual workload evidence and likely a non-authoritative incremental/materialized cache.

## Counterhypothesis decision

The strongest counterhypothesis is **substantially supported**.

A conventional persisted terminal receipt can match CCW's encoded correctness and atomic fault behavior while winning point-read latency. Therefore CCW fails the bar for a distinct default physical architecture.

The only property that does not collapse completely is dynamic support validity. But the minimal answer is not necessarily 'delete the receipt'. It is:

- keep exact canonical support;
- keep the receipt/cache if useful;
- bind it to support identity/epoch/hash;
- never accept the receipt alone as proof of current causal closure;
- revalidate when verifier/recovery/consequential logic depends on closure;
- preserve verified external outcome even when causal-learning support is quarantined;
- never mint retry authority from causal invalidation.

That is simpler than promoting CCW as a new runtime organ.

## Relationship to active V17 work

PR279/PR280 already own the direct current repair: bind V17 terminalization to durable execution-generation evidence and canonical GWT/use/outcome/causal-credit/delta-or-no-learning support. This ATOMIC run intentionally creates no competing target branch.

CCW contributes one review/falsification obligation to that work: after a historical DONE receipt exists, invalidate/quarantine one required support witness. The verifier/recovery path must not report causally closed from the receipt alone. It must preserve verified provider outcome, downgrade/rebuild causal closure, and mint zero effect-retry authority.

## Prior-art verdict

No world-first claim survives. CCW is best classified as:

`PROJECT_SPECIFIC_SEMANTIC_DELETION_CANDIDATE -> REFUTED_AS_DISTINCT_DEFAULT_RUNTIME -> RETAINED_SEMANTIC/TEST_LAW`

## Final architecture delta

No new organ. No target code promotion. No new effect authority. No change to GWT truth semantics, Needle authority, Hyperposition epistemics, Retina/MVC, memory/reward/goals, or final training authorization.

The durable delta is one sentence:

**DONE receipt != current causal closure authority.**

Or more operationally:

`terminal cache/receipt + independently valid canonical support closure -> trusted current causal completion`

not:

`terminal receipt exists -> trusted current causal completion`.

This is the result routed back into F-V01-04 / F-V01-05 / F-V01-09 / F-V01-13 and into review of PR279/PR280.

## Next highest-information falsifier

Wait for the conventional V17 support-binding candidate to reach accepted-target evidence. Then run exactly one additional matched post-terminal support-quarantine control. If the conventional verifier already revalidates exact support and fails closed without retrying the external effect, CCW contributes no further runtime architecture and remains closed as a useful negative result/design law. If the verifier trusts a stale DONE receipt, the retained CCW law has found a real recovery bug and should become a direct test obligation.
