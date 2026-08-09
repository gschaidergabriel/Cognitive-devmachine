# ClayCode Trigger Run — Semantic Publication Barrier / UnifiedDB↔ClayGraph Authority Boundary

Run: `claycode-20260809T1603p0700-chatgpt-semantic-publication`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` (`IN_PROGRESS`)  
Promotion: `NONE`

## Executive result

This run deliberately did **not** duplicate the active/completing strict parser/relation-surface lane. Its discriminator was narrower and cross-branch: can current G9-style semantic machinery represent the FRANK/UnifiedDB/ClayGraph requirement that canonical state, derived topology, replay, and effect authority remain coherent across partial failure without inventing another language keyword?

The executable proxy supports a **refined yes** in the tested scope.

A run-local semantic oracle represented:

- canonical UnifiedDB state commit with base-epoch validation and idempotency;
- derived ClayGraph projection bound to the exact committed source epoch;
- explicit projection/retraction closure;
- a reader-visible `PublishedSemanticEpoch` barrier;
- crash after canonical state commit but before graph publication;
- recovery/rebuild then publication;
- graph-derived relevance remaining non-authoritative;
- independent host capability validation and revocation.

Observed:

- fixed adversarial cases: **12/12 matched**;
- property/mutation rounds: **20,000**;
- mutation violations: **0**;
- clean replicated execution: `python -S`, exit `0`, stderr empty.

The main architecture delta is therefore **not a new syntax primitive**. It is a standard canonical-IR/runtime contract:

`SemanticPublicationReceipt + PublishedSemanticEpoch`

The canonical state may safely commit ahead of a derived graph rebuild **provided reader-visible CURRENT remains pinned to the previous coherent publication until the new state epoch, graph epoch, closure receipts, and authority/recovery checks validate together**. This is a publication-barrier design, not a requirement for one physical database.

This is only run-local executable evidence. It is **not** production ClayCode parser/type-checker/compiler evidence, not a split-store crash test, and not H1/H2/H3 acceptance.

## Why this lane was selected

The same-room ClayCode worker at `20260809T155804` was already testing strict declared relation resolution and fail-closed surface semantics. That lane later preserved `NR-CC-GENERIC-INFIX-NORESOLVER-20260809`: naïve arbitrary identifier-as-infix acceptance is unsafe without a typed resolver.

To avoid false replication and duplicate work, this run reused that result and selected a different unresolved boundary: atomic semantic publication and authority isolation across UnifiedDB and ClayGraph.

## Internal evidence

### ClayCode G9 V3

Current G9 already contains the ingredients needed for the proxy:

- `Delta<T>`;
- `IncrementalReceipt`;
- `ViewDelta<T>`;
- `GraphDelta` with `source_epoch`, `graph_epoch`, and `projection_receipt`;
- `CapabilityToken`;
- `effect.commit` guarded by a valid capability;
- `graph.derived_relation cannot_authorize effect`;
- hard invariants separating provenance/authority, state truth/graph relevance, and model intent/effect authority.

The current language surface is not production-frozen; parser work remains separate and open.

### UnifiedDB

Current UnifiedDB already has:

- `state_epochs`;
- `semantic_transactions`;
- unique idempotency keys;
- `base_epoch`;
- transaction operations with preconditions;
- authority scope;
- prompt-cycle state/graph epoch identities;
- snapshots carrying unified/graph hashes and recovery state.

The run interprets these as sufficient storage/runtime ingredients for a reader-visible publication pointer, without claiming that the current SQL already implements the final barrier.

### ClayGraph

Current ClayGraph has:

- graph epochs bound to source epochs;
- derived nodes/edges/hyperrelations;
- projection receipts;
- selection and receiver receipts;
- invalidation queue;
- rebuild recipes;
- explicit rule that graph activation/relevance is not semantic truth or effect authority.

This makes the graph a derived projection that can lag a canonical state commit while still being prevented from becoming CURRENT prematurely.

### FRANK fused target

The current fused target's P11 requirement is stronger than simple database atomicity:

- PATCH vs COMPLETE_SNAPSHOT/retraction closure;
- atomic semantic epoch publication;
- stale derived edges cannot remain CURRENT;
- failed partial publication cannot expose mixed CURRENT state.

P10 separately requires host-minted authority, release-time revalidation, idempotent receipts, and no ambient authority.

The experiment targeted exactly this P10/P11 boundary.

### GWT / Hyperposition / Emergenz / Harness

No new GWT or emergence mechanism is claimed.

The existing contracts still require:

- GWT readouts tied to exact state/graph/episode epochs;
- Hyperposition alternatives/higher-order relations preserved across coherent epochs;
- emergence claims to use interventions/lesions/rescue/shuffles;
- every Harness to produce and differentially validate its own static/dynamic ClayGraph.

The direct Harness implication is new Golden Trace fixtures for crash-between-state-commit-and-publication, stale graph projection, retraction incompleteness, and graph-only authority attempts.

## Executable experiment

Artifacts:

- `experiments/SEMANTIC_PUBLICATION_PROBE.clay`
- `experiments/semantic_epoch_publication_probe.py`
- `EXECUTABLE_RESEARCH_RECEIPT.json`

Important identity boundary:

- Clay contract SHA-256: `5680b75e2467fab674dcf800823539dc778632b99cd78728a4f573938a33904c`
- executable proxy SHA-256: `0b2bd40d0beb0d0365738be208b636ae4d14163be61c714267e1c24e03ee515c`
- clean stdout SHA-256: `d384e0115f09350f800ebf5ec4343adb0a175c42b12b5f90cde57e19a4b51f55`
- production canonical-IR semantic hash: **not available and intentionally not fabricated**.

### Fixed cases

1. coherent publish succeeds;
2. stale base epoch rejected;
3. graph projection from stale source epoch rejected;
4. incomplete projection closure rejected;
5. incomplete retraction closure rejected;
6. crash after canonical commit leaves prior reader-visible publication intact;
7. recovery graph rebuild can publish;
8. recovered reader state is epoch-coherent;
9. idempotency replay returns the same state epoch;
10. graph relation alone cannot authorize effect;
11. valid independent host capability authorizes;
12. revoked capability rejects.

Result: **12/12**.

### Mutation/property pass

Seed: `20260809`  
Rounds: `20,000`  
Admitted coherent publications: `10,809`  
Rejected invalid publications: `9,191`  
Invariant violations: **0**

The tested invariants were:

1. publication occurs iff source epoch + projection closure + retraction closure all match;
2. failed publication never changes reader-visible CURRENT;
3. graph presence never grants effect authority.

## External triangulation

External sources were used only as independent implementation-pattern checks, not as FRANK-specific evidence.

- SQLite's official atomic-commit documentation establishes the ordinary storage-level all-or-nothing transaction pattern under failure. This supports using a canonical transaction boundary but does not solve cross-store semantic publication by itself.
- MLIR's official dialect-conversion framework uses explicit legality plus staged/rollback conversion behavior. This independently supports the design pattern “build/validate derived form, expose only legal final form,” but is a compiler analogy rather than Clay proof.
- Bytecode Alliance WIT/Component Model documentation supports explicit typed interfaces/resources as a lowering boundary. It does not itself grant application authority, which is consistent with retaining Clay capability checks outside mere type/interface presence.
- Differential Dataflow/CIDR and the current differential-dataflow documentation provide a primary reference for maintaining computations via deltas as inputs change rather than globally recomputing, consistent with Clay's incremental dependency/materialization direction.

No external source promotes a FRANK/ClayCode claim by itself.

## Hypotheses

### H-CC-G9-PUBLICATION-CONTRACT-SUFFICIENCY-001

Status: `OPEN_REFINED_BY_EXECUTABLE_PROXY`

Existing G9 generic records/rules plus Delta/ViewDelta/GraphDelta and capability separation are sufficient to encode the tested semantic publication barrier without a dedicated transaction keyword.

Strongest counterhypothesis: a real type/effect checker or physically split state/graph deployment will expose partial-publication states that cannot be validated without first-class transaction/publication semantics.

Falsifier: the production BASE compiler or H1/H2 crash/replay differential cannot enforce the standard receipt contract without opaque host-only semantics or exposes mixed CURRENT.

### H-CC-PUBLICATION-PRIMITIVE-NECESSITY-002

Status: `NOT_SELECTED`

A new syntax primitive is required immediately.

The current proxy did not support that claim. It remains revivable if the production checker/runtime finds a concrete unrepresentable case.

## Negative result

`NR-CC-NEW-PUBLISH-SYNTAX-20260809`

The tested P10/P11 behavior did not require new ClayCode syntax. Adding a keyword now would violate the BASE “less change, more compile” policy without an executable counterexample.

This negative result is scoped. It does **not** prove that the production checker can enforce the contract.

## Goodman anti-echo

Two FRANK assumptions were reviewed with shared ancestry collapsed:

1. P11 atomic semantic publication — `REFINED`;
2. P10 graph relevance never grants effect authority — `REFINED`.

The refinement is important: **atomic semantic publication does not imply physically atomic co-location of UnifiedDB and ClayGraph**. It can be implemented as atomic publication of a validated epoch tuple/receipt while derived state is rebuilt behind the barrier.

The independent evidence contribution is this run's executable falsifier plus external systems/compiler boundary patterns. Repetition of FRANK/Clay/ClayCode prose was not counted as independent support.

## Cross-branch delta

### ClayCode
Freeze the semantic contract, not new syntax:
- `SemanticPublicationReceipt`
- `PublishedSemanticEpoch`
- type/effect rules tying publication to source epoch, projection/retraction closure, authority and recovery
- deterministic canonicalization and stable contract hashes

### UnifiedDB
Add/confirm a first-class reader-visible publication identity separate from “latest committed canonical state.” Keep idempotency/base-epoch/authority scope in the canonical transaction plane.

### ClayGraph
A graph epoch becomes reader-visible CURRENT only when its source epoch and closure receipt match the publication barrier. Graph topology/activation remain non-authoritative.

### FRANK
P11 can preserve semantic atomicity while allowing physically separate derived stores. P10 remains independent: graph/model proposals do not mint permits.

### Harness
Add crash/replay Golden Traces:
- state committed / graph absent;
- graph built / publication absent;
- stale graph source;
- incomplete retraction;
- duplicate replay;
- graph-only authority;
- revoked capability;
- recovery rebuild + publication.

### GWT
`NO_CHANGE`: readout chains should reference the coherent published state/graph epoch tuple.

### Hyperposition
`NO_CHANGE`: preserve alternatives/conflicts in the same coherent publication contract.

### Emergenz
`NO_CHANGE`: publication correctness is not emergence evidence.

### Clay integrated fabric
Concrete support for the fixed semantic-epoch barrier direction; no physical-monolith implication.

## Current BASE impact

This run does **not** PASS any BASE work package.

It sharpens implementation acceptance for:

- `CC-WP-03-IR-TYPES`;
- `CC-WP-04-TYPE-EFFECT`;
- `CC-WP-05-EVALUATOR`;
- `CC-WP-07-RUNTIME-ABI-FFI`;
- `CC-WP-09-CONCURRENCY-MEMORY`;
- `CC-WP-11-FUZZ-CONFORMANCE`;
- `CC-WP-13-HARNESS-HANDOFF`.

The immediate production discriminator remains: freeze/parser-normalize G9, implement canonical IR + checker, then compile this exact publication contract and inject real crashes across the chosen physical backend layout.

## Strongest limitation

The proxy uses one local SQLite connection and a hand-lowered Python oracle. It demonstrates semantic representability and catches several invariant classes, but it cannot establish:

- production ClayCode parse/type/effect behavior;
- cross-process or cross-store atomicity;
- real filesystem/power-loss durability;
- concurrent writers;
- distributed graph rebuild;
- H1/H2/H3 equivalence;
- live FRANK effect-gateway safety.

Those are the next evidence gates.

## Next discriminating experiment

Compile a frozen `SemanticPublicationReceipt` contract through the real BASE parser/canonical IR/type-effect checker and runtime, then run a crash matrix against physically separated canonical and derived stores:

`before state commit -> after state commit -> during graph rebuild -> after graph rebuild -> before publication -> after publication`

For every cut point verify:

- no mixed reader-visible CURRENT;
- exact replay/idempotency;
- complete retraction/invalidation closure;
- stable semantic hashes;
- no authority amplification;
- deterministic recovery;
- H1/H2 differential equivalence when Harness becomes available.

## Final synthesis

The best current design is **coherent publication by typed epoch receipt**, not “put everything in one DB” and not “invent a transaction keyword.”

ClayCode should make the boundary machine-checkable; UnifiedDB should remain canonical; ClayGraph should remain rebuildable and non-authoritative; the reader should see only a validated coherent epoch; and effect authority should continue to come from an independent host capability path.

That preserves the project's core architecture distinctions while giving BASE a concrete compiler/runtime target and a falsifiable crash/replay gate.
