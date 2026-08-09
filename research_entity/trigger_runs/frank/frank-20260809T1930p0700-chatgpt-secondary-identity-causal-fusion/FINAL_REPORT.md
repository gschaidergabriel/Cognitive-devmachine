# FRANK Trigger Run — Identity Integrity, Causal-Spine Fusion, Concurrent CAS Adjudication

**run_id:** `frank-20260809T1930p0700-chatgpt-secondary-identity-causal-fusion`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**identity:** temporary Clay Research Entity worker; not FRANK  
**target:** Frank v0.1 on Ubuntu Linux developer system  
**scientific promotion:** NONE  
**research/implementation write:** COMMITTED

## 1. Dynamic boot and why this run did not repeat the previous FRANK report

This run booted from the current GitHub canonical state and then repeatedly re-read main while research and implementation continued concurrently. The previous deep FRANK run had already reduced the architecture to a semantic spine:

`canonical state -> dependency-maintained views -> bounded ActiveAssembly -> explicit workspace causality -> local 4B -> typed peer backflow -> deterministic effect authority -> verified re-entry`.

The correct task was therefore not to invent more organs. It was to attack the executable interfaces that could silently corrupt identity, conflict visibility, causality or recovery as these slices are joined.

The formal program gate remains `BASE_CLAYCODE_RELEASE`. The ClayCode release workspace still credits only WP-01 as PASS; WP-02..14 remain OPEN because candidate/proxy execution does not equal production/target-Ubuntu acceptance. H1 also remains NOT_PASS.

## 2. First new defect: ActiveAssembly packet-ID collision ambiguity

The current ordinary-code ActiveAssembly reference compiler already protected several important invariants:

- deterministic score/rank order;
- bounded context budget;
- ancestry-family caps against duplicated-support flooding;
- explicit counterevidence preservation;
- stale-epoch exclusion;
- re-expansion references for omitted detail;
- cognitive packet visibility without execution authority.

But the initial executable code used `selected_ids` as a silent deduplication mechanism without first proving that a `packet_id` identified exactly one semantic/provenance payload. Two non-identical packets carrying the same `packet_id` could therefore enter the candidate set and be collapsed according to ranking/order rather than failing as an identity contradiction.

This is not a cosmetic issue. In the current FRANK target, packet identity may participate in:

- peer backflow and duplicate suppression;
- provenance/ancestry accounting;
- replay and re-expansion;
- contradiction retention;
- causal trace binding;
- H1/H2 differential comparison.

A silent collision can make two distinct pieces of evidence appear to be one object or make one overwrite the observational visibility of the other.

### Implemented repair

This worker committed a fail-closed identity check:

- exact duplicate deliveries with identical complete packet payload remain idempotent;
- the same `packet_id` with different payload fails with `PACKET_ID_COLLISION` before ranking/selection;
- malformed empty packet identity fails closed;
- existing authority, score, stale-epoch and budget checks remain active.

Commits:

- `5e93e99e13aa8b544203ff795c767c5884274167`
- `605f57d6c5c20b620b9b2584e0cfca4895b8c218`

Hosted Linux reference validation before later concurrent edits:

- 13/13 unit/regression tests PASS;
- 10,000 randomized same-ID mutated payload attacks;
- 0 silent collision acceptances;
- original 5,000-trial ancestry/echo fixture retained.

This is component evidence only. It is not target-Ubuntu evidence and does not close H1.

## 3. Second-order negative result: the content fingerprint cannot silently become the H1/H2 semantic hash

The first repair required a deterministic local payload fingerprint so that duplicate delivery can be distinguished from divergent same-ID content. That exposed a more subtle transfer risk.

The H1 implementation used Python `json.dumps(... sort_keys=True ...)` as a local deterministic serialization. A direct Python-versus-ECMAScript probe showed different textual number representations for valid values including:

- `1.0` versus `1`;
- `1e-07` versus `1e-7`;
- `1e+20` versus an expanded integer form;
- `-0.0` versus `0`.

RFC 8785 exists precisely because hashing/signing JSON across implementations requires an explicit canonical representation. Therefore:

**local deterministic fingerprint != automatically language-independent semantic identity**.

This matters because H2 will eventually reproduce H1 semantics in ClayCode. An unversioned Python-specific serialization hash must not be treated as evidence that two implementations disagree semantically.

Working decision:

- retain collision hardening;
- keep cross-language fingerprint normativity OPEN;
- require a frozen canonicalization fixture/contract before H1/H2 raw hash equivalence is used as a release oracle;
- semantic/version/trace identity must remain explicitly distinguishable.

## 4. CAS conflict became useful evidence instead of lost work

After the cross-language result, this worker attempted to narrow the fingerprint to an internal implementation detail and preserve the older output schema. GitHub rejected the write with a CAS/contents conflict (`409`) because another worker had modified the same file after this worker's re-read.

The stale write was not forced.

Main was re-read. The concurrent worker had:

1. preserved the same-ID payload collision repair from this run;
2. added a separate red-team repair for same-ancestry contradictory propositions.

This is exactly the repository behavior the Research Entity needs: stale local intent does not outrank current shared state.

## 5. Concurrent ActiveAssembly red-team result: evidence diversity and conflict visibility are not the same variable

The concurrent red-team found that the ancestry cap itself could hide explicit opposite propositions when both opposites shared the same ancestry family.

This revealed a distinction that should remain in FRANK:

`duplicate-support suppression != contradiction suppression`.

The current mainline ActiveAssembly now permits conflict representatives to bypass the ancestry-family replication cap when total item budget permits, while:

- preserving the hard total context budget;
- marking such items `CONFLICT_VISIBILITY`;
- assigning `independent_replication_credit=false`;
- retaining re-expansion references when the total budget is too small.

The corresponding receipt records both same-ancestry opposites as visible under budget 2 and the total budget remaining hard under budget 1.

This is a high-value Hyperposition/ClayGraph/FRANK transfer: set-valued contradiction visibility need not be implemented as a separate persistent service, and visibility must not be misread as independent evidential replication.

## 6. Concurrent GWT result: receiver-causal stages are now executable

A parallel FRANK worker added an ordinary-code `WorkspaceEpisode` reference slice with 17/17 hosted-container tests. It explicitly distinguishes:

- candidate competition;
- GWT ignition versus conventional EVENT_BUS admission;
- broadcast addressability;
- delivery;
- reconstruction;
- uptake;
- local causal use;
- outcome;
- provenance-bound re-entry.

It also provides receiver diagnostic failure classes, intervention points, truthful versus shuffled re-entry and explicit closure states.

This is an important architecture change in evidence quality, not a scientific GWT promotion. The required null remains a conventional event bus with equivalent receipts. The next discriminating question is whether the additional stage distinctions improve causal diagnosis, correction and outcome-per-compute on matched H1 tasks.

## 7. Loop-of-loops research after current external evidence

The owner-directed FRANK loop-of-loops hypothesis remains OPEN, not promoted.

Current project proxy experiments already showed why a state-delta-only convergence test is unsafe: a stalled system can have a small state delta while residual error remains high. The current loop-quality gate therefore includes estimator identity/version, uncertainty and measurement age.

Recent external preprints strengthen the *research question* without proving FRANK's architecture:

- `Adaptive Depth in Looped Transformers: Diagnosing Learned Halting Gates and Trajectory Readouts` (arXiv:2607.20519) separates trajectory formation from exit readout and finds simple post-hoc readouts can match or beat learned gates on some evaluated trajectories.
- `DeepLoop: Depth Scaling for Looped Transformers` (arXiv:2607.13491) shows that recurrent depth has stability constraints tied to repeated parameter visits; deeper looping is not just free extra depth.
- `The Recurrent Transformer: Greater Effective Depth and Efficient Decoding` (arXiv:2604.21215) provides further evidence that recurrence can trade parameters/depth/memory differently from ordinary feed-forward depth.

FRANK should therefore not use `more loops = better` or `fixed point = cognition solved` as a law. The correct H1 comparison remains:

- event-driven baseline;
- fixed recurrence budget;
- typed adaptive recurrence;
- truthful/shuffled/no re-entry;
- lesion/rescue;
- outcome, latency, correction time, instability and false-halt metrics.

## 8. Effect authority/recovery: capability validity is not enough

ClayCode's concurrent runtime work is converging on opaque, runtime-minted, policy-bound capability handles. That supports the fixed project law:

`model/peer/Needle/Retina output = proposal/observation, not bearer authority`.

A new FRANK mainline probe now targets a different failure class: crash after external effect but before durable receipt/re-entry. This can leave the world changed while local semantic state is ambiguous.

The hypothesis under test is that recovery needs explicit lineage across:

`intent -> authorization -> reservation -> commit -> external effect -> outcome receipt -> durable re-entry`.

An Ubuntu CI workflow has been added to reproduce/probe this mainline ambiguity. At the time of this report, the final receipt from that workflow had not yet been observed by this worker, so no PASS is claimed.

## 9. UnifiedDB: external evidence supports testing, not physical monolithism

SQLite remains a useful H1 reference mechanism because WAL gives concurrent readers stable read snapshots while a writer appends changes. But the same official documentation supplies the counterevidence that must remain alive:

- only one WAL writer at a time;
- readers retain their end mark for a transaction;
- long/overlapping readers can inhibit checkpoint completion;
- WAL growth can degrade read performance;
- the WAL file is part of persistent database state and cannot be casually separated from the database.

Therefore the target law remains:

`one logical UnifiedDB semantic identity plane != proof that one physical file/layout is always optimal`.

Target-Ubuntu workload, checkpoint, crash and recovery measurements must decide physical placement.

## 10. Local 4B role: still open, but the model slot is technically real

Official Qwen model material confirms current dense 4B-class local candidates remain available. Qwen3-4B-Thinking-2507 is 4.0B with 36 layers, 32 query heads / 8 KV heads and native 262,144 context. Qwen3-4B-Instruct-2507 has standard local Transformers/vLLM usage paths.

This does not establish that it is the correct FRANK model. It only prevents the architecture discussion from treating the local-4B slot as hypothetical.

Community LocalLLaMA reports continue to show how dramatically local inference depends on backend, quantization, memory topology and context, but these reports are implementation anecdotes, not acceptance evidence.

Required decision remains a target-host benchmark on the actual Ubuntu developer system with the frozen FRANK task/ActiveAssembly workload.

## 11. Second fusion — what FRANK now appears to need next

The architecture is beginning to transition from independent semantic slices to an integration problem.

Executable or near-executable pieces now include:

- StateLedger/replay work under an already claimed package;
- ActiveAssembly with ancestry/conflict/identity hardening;
- receiver-causal WorkspaceEpisode;
- loop dynamics/readout quality gate;
- Needle component boundary evidence;
- ClayCode authority/runtime candidates;
- effect-recovery lineage probe.

The largest remaining information gain is therefore not another organ. It is a **single integrated ordinary-code Golden Trace** with explicit shared identities across those slices.

Candidate integrated trace:

`input/percept`
`-> StateLedger semantic_epoch/basis`
`-> dependency-prepared candidate packets`
`-> ActiveAssembly`
`-> WorkspaceEpisode competition/ignition-or-event-bus`
`-> receiver delivery/reconstruction/uptake/causal-use`
`-> loop continue/halt/route decision`
`-> model/peer proposal`
`-> EffectIntent + capability/resource closure`
`-> reserve/commit/external effect`
`-> OutcomeReceipt`
`-> provenance-bound re-entry`
`-> durable StateLedger delta`
`-> replay/counterfactual identity`

The same trace must be runnable under:

- GWT versus EVENT_BUS;
- fixed versus adaptive recurrence;
- truthful versus shuffled versus no re-entry;
- receiver lesions/corruption;
- stale/duplicate/conflicting packet injection;
- crash cut points around effect commit/receipt;
- instrumentation arms;
- eventual H2 ClayCode differential translation.

This would test the most important current invariant:

**multiple individually correct modules must never expose a mixed partial semantic epoch as one coherent FRANK state**.

## 12. Second-generation hypothesis result

Nine second-generation hypotheses were persisted in `HYPOTHESIS_MATRIX.json`.

Strongest component-supported results:

1. same-ID divergent ActiveAssembly payloads should fail closed;
2. duplicate evidence caps and contradiction visibility must be separate;
3. state-delta-only halting is insufficient in stalled regimes.

Strongest open architecture questions:

1. whether the current packet fingerprint should become a normative cross-language identity at all, and under what canonicalization;
2. whether receiver-causal GWT stages beat an equally instrumented event-bus null;
3. whether effect recovery needs additional durable lineage semantics after crash-fault injection;
4. which UnifiedDB physical placement survives target workload/recovery tests;
5. whether the 4B role meets frozen target-host thresholds;
6. whether shared integrated trace identity exposes defects invisible in isolated components.

## 13. Branch feedback

A whole-mesh feedback manifest was written.

Key transfers:

- **ClayCode:** add a cross-language canonicalization/identity fixture; do not silently inherit Python JSON hashing semantics.
- **Harness:** prioritize integrated Golden Trace identity over another standalone module.
- **GWT:** preserve EVENT_BUS null and receiver-stage separation.
- **Emergenz:** use these stages as intervention instrumentation, not an emergence score.
- **Hyperposition:** same-ancestry opposites are a concrete conflict-visibility case; no separate service is required.
- **ClayGraph:** conflict visibility must not create independent replication credit.
- **UnifiedDB:** bind replay identity across assembly/GWT/effect lineage; benchmark physical WAL/checkpoint behavior.

## 14. Negative results preserved

- Python deterministic JSON serialization is not automatically cross-language canonical JSON.
- A stale GitHub write was rejected by CAS; no stale overwrite was forced.
- Candidate/proxy ClayCode work has not closed the formal BASE packages.
- ActiveAssembly component success does not close H1.
- WorkspaceEpisode component success does not prove GWT superiority.
- Recurrence proxy success does not prove organism-level FRANK benefit or emergence.
- No target-Ubuntu 4B benchmark was run by this worker.
- No target-Ubuntu UnifiedDB workload benchmark was run by this worker.
- The effect-recovery Ubuntu CI workflow exists, but this worker had not yet observed its final receipt at report freeze.
- No scientific generation/revision promotion is justified.

## 15. Final synthesis

The deepest change from this run is a shift in the research bottleneck.

Earlier FRANK work needed to determine *what semantic distinctions the organism must contain*. Current work increasingly needs to determine *whether those distinctions remain coherent when executable slices are connected under concurrency, replay, peer backflow, crashes and H1/H2 language translation*.

The target architecture remains:

`ONE_CLAY_BINARY + ONE_LOCAL_UNIFIEDDB + ONE_CLAY_NATIVE_4B`

but H1 should stay diagnostically decomposed long enough to falsify incorrect coupling.

The immediate research law after this run is:

`freeze shared identity -> connect executable slices -> run matched null/intervention/crash traces -> preserve negatives -> transfer semantics to ClayCode -> consolidate last`.

No new conceptual organ is warranted from the evidence examined here.
