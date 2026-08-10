# UnifiedDB / Database Pulse V6.4 — GO-cycle evidence freeze

Date: 2026-08-10 (+07:00)
Actor: temporary ChatGPT Clay research worker
Status: ACTIVE RESEARCH / V6.4 PHYSICAL CANDIDATE / NO PROMOTION

## Current convergence

The strongest current architecture separates two clocks and two authority planes:

1. **StateLedger / UnifiedDB semantic clock** — sole semantic/provenance authority and sole
   authoritative semantic event stream.
2. **Database Pulse execution clock** — physical endogenous cognition bookkeeping, source cursor,
   receipts, control transitions and recovery evidence. It does not write ordinary idle Pulse
   bookkeeping back into semantic StateLedger.

Candidate progression retained as falsification ancestry:

- V1 semantic Pulse exposed lexicographic pre-limit starvation and semantic self-churn.
- ActiveField V2 repaired starvation but introduced a second candidate projection.
- authoritative RankIndex V3 removed that second candidate table for deterministic scalar score.
- adaptive RankPath V4/V5 separated semantic ranking from physical index economics and then made
  index maintenance explicit/two-phase/CAS-receipted.
- execution-plane V6 removed semantic Pulse self-write and consumes whole StateLedger events.
- V6.1 hardened receipt hashing and explicit UNKNOWN model-envelope semantics.
- V6.2 added one total-order execution transition journal covering Pulse and control transitions.
- V6.3 made control ids strict and automatic recovery lineage-preserving: repair the trusted head,
  never silently rewind receipted execution history.
- **V6.4** retains every Pulse/control receipt but sparsifies full Pulse checkpoints and rebuilds
  trusted execution state by verified receipt/control replay.

## V6/V6.3 topology evidence on Hostinger

A self-contained execution-topology mechanism probe was run on the real self-hosted runner in
`gschaidergabriel/Dr.-Unterweger` because that is where the current Hostinger runner is attached.
This probe is deliberately weaker than exact Clay integration and is labelled accordingly.

Observed environment:

- runner/host: `clay` / `digital-retina`
- Ubuntu/Linux x86_64
- Python 3.12.3
- SQLite 3.45.1

Observed bounded mechanism results:

- 500 endogenous execution-plane idle Pulses: semantic epoch delta = 0.
- matched semantic-bookkeeping counterarm: semantic epoch delta = 500.
- a prepared semantic receipt survived the execution-plane idle sequence.
- one StateLedger-style transaction containing 180 operations remained one source event.
- 75 separate events were consumed on complete event boundaries as 32 / 32 / 11.
- Pulse + control transition journal remained contiguous.

This is engineering topology evidence only. It is not exact Clay integration, ClayGraph evidence,
or Andreas target acceptance.

## V6.4 checkpoint result

V6.3 wrote a full execution-state checkpoint on every Pulse in addition to state, receipt and
transition log. The first V6.4 mechanism differential compared interval 1 vs 32 for 1,000 Pulse
transitions each.

Correctness held in both arms:

- 1,000 receipts each;
- 1,000 transition-log rows each;
- semantic epoch unchanged;
- trusted head replay reconstructed successfully;
- injected raw execution-state corruption was detected;
- SQLite `quick_check` returned `ok`.

Physical difference:

- interval 1: 1,000 Pulse checkpoints;
- interval 32: 31 Pulse checkpoints;
- checkpoint-row reduction: 96.9%.

A first run showed lower p50 latency for sparse checkpoints, but an independent PR rerun did not:
full ~0.563 ms p50 vs sparse ~0.571 ms p50. **Therefore no robust hot-latency gain is claimed.**
The robust measured improvement is lower full-checkpoint/write amplification while retaining the
receipt/transition evidence surface.

## Replicated interval sweep

Three rounds × 750 Pulses were run for checkpoint intervals 1, 8, 32 and 128. Every arm retained
receipt/transition cardinality, zero semantic churn, replay reconstruction and SQLite quick-check.
Speed remained descriptive, never a PASS criterion.

Median round p50 observations were approximately:

- interval 1: 0.637 ms; 750 Pulse checkpoints / round;
- interval 8: 0.643 ms; 93 checkpoints / round;
- interval 32: 0.582 ms; 23 checkpoints / round;
- interval 128: 0.582 ms; 5 checkpoints / round.

Interval 32 is retained only as a **Pareto hypothesis** for the exact candidate: it removes most
full snapshots without selecting the longest candidate replay interval. Current V6.4 replay code
still reconstructs from bootstrap; do not misstate `interval-1` as an already implemented bounded
replay cost. A future optimization may start replay from the latest trusted periodic checkpoint,
but that requires separate evidence.

## SQLite release constraint

The observed Hostinger Python runtime uses SQLite 3.45.1. Current SQLite upstream documentation
identifies a rare WAL-reset corruption bug under simultaneous write/checkpoint conditions and
lists fixed release families newer than this environment. Therefore this research cycle does not
run or claim the concurrent writer + checkpoint WAL release stress on Hostinger 3.45.1.

Single-writer/event-atomic mechanism results remain useful, but multiwriter release acceptance is
blocked until a fixed SQLite family or another validated storage configuration is used.

## Exact-source transport breakthrough

Direct cross-private-repository checkout from the Hostinger runner failed because the VPS has no
Clay-repo credential usable from Dr.-Unterweger. HTTPS clone had no token/username; SSH had no
matching public key.

A credential-free exact-source path was therefore built through GitHub's object API:

1. fetch a Clay branch blob;
2. create the same byte sequence as a blob in Dr.-Unterweger;
3. require identical Git blob SHA;
4. construct a **rootless/hermetic tree with no Dr base tree** containing only the declared Clay
   dependency closure plus SHA manifest and workflow;
5. on Hostinger, run `git hash-object` over every source file and require exact equality before
   compilation/import.

The snapshot is pinned to Clay branch
`chatgpt/unifieddb-pulse-v6-current-main-20260810` at source head
`12a1536dc9c2f46bdb8da455ba9d71bf4bdb16fd`.

The bounded exact closure includes StateLedger, QueryPlane, auth shadow/focus guard,
RankIndex/RankPath V3/V4/V5, compile economics/horizon, the older semantic Runtime V4 dependency,
V6→V6.4 and the minimal V6.4 integration test. ClayGraph and unrelated Clay files are explicitly
outside this snapshot.

GitHub accepted the rootless tree, proving all declared object ids exist in the target repository.
The Hostinger exact-source run then passed these gates:

- checkout;
- exact Clay blob-manifest verification;
- environment capture;
- `py_compile` over the declared closure.

The actual minimal V6.4 integration unittest then failed. Therefore **V6.4 exact-source integration
is NOT PASS**. A diagnostic lane now persists the exact traceback separately. No mechanism PASS,
compile PASS or byte-identity PASS is promoted into an integration PASS.

## Negative results retained

1. Sparse checkpoints do not yet have a robust latency advantage; rerun erased the first p50 gain.
2. Hostinger SQLite 3.45.1 cannot support the intended concurrent writer/checkpoint release claim.
3. Direct private Clay checkout from the VPS is authentication-blocked.
4. Cross-repo reuse of a Clay blob SHA in a Dr tree is rejected by GitHub; objects are repo-scoped.
5. Manual text mirroring is unsafe for exact evidence: a QueryPlane comment omission changed the
   blob SHA and was caught. Only exact SHA-equal blobs are admissible for the hermetic snapshot.
6. Exact byte-verified V6.4 integration currently fails at unittest execution and must remain a
   hard blocker for promotion.

## Current promotion law

V6.4 may not be promoted until all of the following are true:

- exact-source minimal integration is green on Hostinger or another real Ubuntu lane;
- failure traceback is localized and repaired in the Clay source branch, not patched only in the
  mirrored runner snapshot;
- the repaired source is re-snapshotted with new exact blob hashes and rerun;
- a fixed SQLite family passes the intended multi-connection WAL writer/checkpoint stress or the
  release storage topology is changed and revalidated;
- full Clay/Frank target integration and Andreas-target acceptance remain separately executed.

The measured checkpoint reduction is retained as a promising physical optimization, not as proof
of cognitive quality or database superiority.
