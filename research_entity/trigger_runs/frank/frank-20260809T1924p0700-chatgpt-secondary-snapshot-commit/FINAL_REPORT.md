# FRANK Trigger Run — Cognitive Snapshot / Fresh Commit Architecture Fusion

**run_id:** `frank-20260809T1924p0700-chatgpt-secondary-snapshot-commit`  
**trigger:** `frank`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**identity:** Research Entity temporary worker; NOT FRANK  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**target host:** Ubuntu Linux developer system only  
**fixed final target:** `ONE_CLAY_BINARY + ONE_LOCAL_UNIFIEDDB + ONE_CLAY_NATIVE_4B`  
**scientific promotion:** `NONE`  
**implementation write:** `COMMITTED`

## 1. Dynamic whole-mesh boot and changed frontier

This trigger joined the current GitHub state rather than relying on project memory. The canonical generation remains r2, but repository implementation/research moved materially during the run.

Fresh concurrent evidence included:

- current-target H1 V2 re-freeze candidate with coverage validation but no executable release PASS;
- explicit invalidation of the historical H-WP-01 freeze as the current release oracle;
- deterministic H1 ActiveAssembly reference implementation plus ancestry/conflict/authority tests and an execution receipt;
- loop-readout quality sensitivity work showing residual-pressure-aware control itself depends on calibrated/fresh readouts;
- rapid ClayCode parser/typed-IR/evaluator/lowering/runtime/capability/conformance work, still kept separate from release-package PASS accounting;
- Needle analysis showing that the current contrastive tool-retrieval head cannot serve as the no-tool decision and that the historical mini-finetune likely performed no contrastive updates under the documented default cadence unless undiscovered run settings/logs prove otherwise;
- R9 FRANK work making frozen-trajectory/post-hoc halt readouts mandatory recurrence baselines and keeping multimodal 4B physical placement OPEN;
- Emergenz work preserving observer configuration as a possible causal confound;
- ClayGraph reversal/source-echo work preserving ancestry diversity as an OPEN stability/plasticity mechanism rather than promoted truth.

The run therefore did not duplicate ActiveAssembly, loop readout or capability-runtime work. It selected the missing semantic bridge between them.

## 2. Whole-system architecture after Fusion 1

The current H1 target can be compressed to this causal spine:

`input/percept + local semantic state + peer deltas + current capability/resource evidence`

`-> coherent cognition snapshot / dependency-maintained state`

`-> transient topology + Hyperposition alternatives`

`-> bounded ActiveAssembly`

`-> GWT competition / explicit recurrence trajectory`

`-> local 4B + Needle/peer/model proposal surfaces`

`-> EffectIntent`

`-> fresh effect-time revalidation`

`-> opaque deterministic capability/authority gateway`

`-> external execution`

`-> OutcomeReceipt`

`-> re-entry + causal credit + semantic update`

The new gap was between `EffectIntent` and the existing authority gateway. A cognition snapshot can be internally coherent yet stale by the time an effect is about to commit. Conversely, a changed global epoch does not imply that state relevant to the effect changed.

## 3. External research and counterevidence

External evidence was used as mechanism evidence, not FRANK-specific validation.

### SQLite snapshot semantics

Official SQLite WAL/isolation documentation states that a reader sees a snapshot and that a read transaction may fail to upgrade to write after another connection has committed; `SQLITE_BUSY_SNAPSHOT` exists specifically for this stale-snapshot case. This supports a short cognition snapshot followed by a fresh effect commit transaction rather than treating a long-lived cognition read transaction as the later write authority.

Primary references:

- SQLite: *Isolation In SQLite* — `https://sqlite.org/isolation.html`
- SQLite: *Result and Error Codes* — `https://sqlite.org/rescode.html#busy_snapshot`

### Adaptive recurrence

`Adaptive Depth in Looped Transformers: Diagnosing Learned Halting Gates and Trajectory Readouts` (arXiv:2607.20519) reports that learned halting can become entangled with trajectory formation and that simple post-hoc trajectory readouts can match or outperform learned gates in studied settings. FRANK therefore needs controller-independent/fixed-prior trajectories plus post-hoc readouts as a baseline before a learned halt mechanism can be selected.

### Compressed active context

`End-to-End Context Compression at Scale` (arXiv:2606.09659) provides current external support for a broad mechanism family in which a small model can operate over compressed context with selective re-expansion. It does not validate FRANK's ActiveAssembly policy, but it strengthens the hypothesis that bounded active state plus re-expansion is worth matched testing against raw retrieval/full context/naive summary.

These sources do not establish GWT, ActiveAssembly, a specific recurrence controller or UnifiedDB physical layout as superior for FRANK.

## 4. Executed discriminator

### EXP-FRANK-SNAPSHOT-COMMIT-001

A hosted Linux experiment combined a real SQLite WAL snapshot-upgrade probe with a constructed dependency-revalidation workload.

#### Real SQLite runtime probe

Environment: Python stdlib SQLite `3.46.1`, WAL mode.

1. Connection A opened a read transaction and read `capability_epoch=(1, version 1)`.
2. Connection B committed an update to `(2, version 2)`.
3. Connection A attempted to upgrade its stale read snapshot into a writer.
4. The attempt failed with SQLite error code `517`, `SQLITE_BUSY_SNAPSHOT`.
5. A fresh `BEGIN IMMEDIATE` transaction then read `(2, version 2)` and detected the change.

This is real runtime evidence for the database mechanism class, but not target-Ubuntu FRANK acceptance.

#### Dependency-closure proxy

A deterministic uniform-key workload compared:

- whole-global-epoch invalidation;
- declared effect-relevant dependency revalidation;
- no revalidation.

With 1,000 possible state keys:

- 5 relevant dependencies + 5 concurrently changed keys: whole-epoch abort `100%`; relevant-closure abort `2.515%`; no-revalidation stale-effect rate `2.515%`.
- 5 relevant dependencies + 10 changed keys: whole-epoch abort `100%`; relevant-closure abort `4.9%`; no-revalidation stale-effect rate `4.9%`.
- 20 relevant dependencies + 10 changed keys: whole-epoch abort `100%`; relevant-closure abort `18.18%`; no-revalidation stale-effect rate `18.18%`.

The percentages are properties of the authored uniform-key fixture, not estimates of real FRANK traffic. The useful mechanism result is narrower: checking the exact dependencies used by an effect can retain rejection of relevant stale state without forcing every unrelated state change to invalidate the action.

## 5. Implemented H1 delta

Two ordinary-code H1 files were added:

- `research_entity/harness/reference/snapshot_commit.py`
- `research_entity/harness/tests/test_snapshot_commit.py`

Write commits:

- `3297b2bb4426e0b03afa49b068adcd423e6c5ca0` — reference component;
- `650f7d1bce58d8ed5dac7cee3a99a8e82b347b93` — regression tests.

The isolated component was executed before repository write: **6/6 tests passed**.

The semantics are intentionally narrow:

`CognitiveSnapshot(snapshot_epoch, assembly hash, dependency versions, capability epoch)`

`+ EffectIntent(relevant dependencies, required capability kind, payload identity)`

`+ fresh current versions`

`-> CommitGuardDecision`

Fail-closed outcomes:

- relevant dependency changed -> reject/replan;
- capability epoch changed -> reject;
- effect introduces a dependency absent from the cognition snapshot -> reassemble;
- commit epoch precedes snapshot -> fault.

Allowed outcome:

- unrelated state changed while all effect-relevant dependencies and capability epoch remain compatible -> preconditions remain valid.

Critical authority law:

`CommitGuardDecision.authority = NONE`

`PRECONDITIONS_VALID` only permits handoff to the separate runtime-minted opaque capability gateway. It never authorizes execution by itself.

## 6. Architecture materialization

A new current realization candidate was committed at:

`research_entity/trigger_runs/frank/frank-20260809T1924p0700-chatgpt-secondary-snapshot-commit/FRANK_ARCHITECTURE.claycode.json`

Commit: `04724480f6fbff0dc9c4d898631f1ea714ffcd22`.

The important change is explicit lifecycle separation:

`coherent cognition snapshot`

`-> Assembly/model/workspace proposal`

`-> EffectIntent with relevant dependency closure`

`-> fresh commit transaction + dependency/capability revalidation`

`-> opaque capability authority`

`-> execution/outcome/re-entry`

This is compatible with final one-binary H3 because the distinction is semantic, not necessarily a process boundary. H3 may collapse processes but must not make the commit/authority path bypassable.

## 7. Hypothesis matrix after Fusion 2

Eight hypotheses plus counterhypotheses are persisted in `HYPOTHESES.json`.

Highest-information hypotheses:

1. **Snapshot/commit split:** fresh commit revalidation is safer and less lock-coupled than upgrading a long cognition transaction.
2. **Relevant closure vs global epoch:** relevant-dependency checking reduces false aborts if dependency discovery is complete and cheap enough.
3. **Trajectory/readout decoupling:** fixed/external trajectories plus post-hoc halt readouts are necessary recurrence baselines.
4. **ActiveAssembly + re-expansion:** bounded evidence-preserving active state can beat raw retrieval/summary on future-task utility per local-4B context cost.
5. **Staged Needle:** no-tool decision, tool-positive retrieval, generative proposal, structural validation and authority must remain distinguishable at the current checkpoint.
6. **Observation identity:** timing-sensitive causal experiments may need observer mode bound into execution identity.
7. **Ancestry-aware slow promotion:** repetition is not independent evidence, but richer provenance gating must beat simpler robust weighting at matched reversal cost.
8. **One-binary logical barrier:** H3 can consolidate physical services only if cognition proposal and effect commit/authority semantics remain non-bypassable.

The required null remains a conventional persistent event-driven architecture with bounded retrieval and deterministic effect authority.

## 8. Concurrent second-fusion result: Semantic Promotion Barrier

While this run was writing, another FRANK worker consumed the new commit barrier and generalized it into an OPEN `Semantic Promotion Barrier` hypothesis across:

- external effect commit;
- Micro Visual Classifier shadow -> durable promotion;
- slow topology/memory promotion;
- strong-peer semantic writeback.

This is a useful cross-domain pattern, not a promotion. Its strongest discriminator is whether one generic dependency/version barrier has lower stale-promotion risk without excessive bookkeeping/false invalidation compared with domain-specific validation.

Required H1 cases now include relevant/unrelated changes, ABA generation changes, crash/restart pending promotions and dependency-laundering attempts.

## 9. Needle fusion

Fresh Harness code analysis changes the Needle interpretation:

- the contrastive retriever has no positive tool on no-tool examples and therefore cannot currently replace the no-tool decision;
- under the documented historical mini-finetune size/default schedule, contrastive loss would likely have received zero update steps unless the actual run used different parameters.

Therefore current H1 should model Needle as a staged proposal boundary rather than silently crediting contrastive no-tool intelligence:

`necessity/no-tool gate -> tool-positive retrieval -> generative tool/args proposal -> structural validation -> opaque capability/effect gateway`.

A retrained unified selector with an explicit no-tool representation remains the countercandidate and must be compared rather than ruled out by design preference.

## 10. Recurrence/GWT fusion

Current internal and external evidence converge on a stronger experiment law:

- residual pressure must be measured, not inferred from low state delta;
- residual-pressure readout itself can become stale/noisy and must be quality-gated;
- GWT focus is an input at most, not the halt oracle;
- fixed/event-driven baselines remain mandatory;
- controller-independent/fixed-prior trajectory plus post-hoc readout becomes a mandatory baseline before end-to-end learned halting can be selected.

No recurrence policy is promoted.

## 11. ActiveAssembly fusion

The newly executed ActiveAssembly reference slice is a major H1 advance, but its policy is still OPEN.

It already demonstrates:

- deterministic bounded selection;
- shared-ancestry caps;
- explicit counterevidence retention;
- re-expansion references;
- authority-mint rejection for cognitive packets.

What remains unproven is the important part: whether this improves real local-4B task outcome, latency/KV cost and correction burden relative to broad retrieval, full-context forcing, naive summary and retrieval-only alternatives.

## 12. Branch feedback

`BRANCH_FEEDBACK_MANIFEST.json` records explicit feedback to every current scientific branch:

- FRANK: new commit barrier in the semantic spine;
- Harness: executable reference slice and Golden-Trace obligations;
- UnifiedDB: short snapshot + fresh revalidation lifecycle and physical contention benchmark;
- ClayCode: represent the types/runtime contract first; no new syntax without a counterexample;
- GWT: bind proposals to their cognition snapshot and preserve readout baselines;
- Emergenz: observer configuration may enter execution identity;
- Hyperposition: alternatives remain proposal state and effect-selected dependencies must be revalidated;
- ClayGraph: activation may select dependencies but does not authenticate them;
- ClayResearch: cross-domain synthesis delta.

Manifest commit: `6abac884c1282f7207b82c0e2e3b437e8fa1bc1a`.

## 13. Negative results and non-promotions

This trigger explicitly does **not** claim:

- canonical revision r3;
- H1 release PASS;
- any ClayCode work-package PASS beyond the workspace's formally credited state;
- target Andreas-Ubuntu acceptance for the new commit barrier;
- Qwen model/backend/quantization selection;
- same-4B Retina backing selection;
- learned recurrence selection;
- GWT causal superiority;
- RAB/provenance-lattice promotion;
- emergence or consciousness from recurrence/workspace behavior;
- that one generic Semantic Promotion Barrier is superior to domain-specific gates.

The old H-WP-01 freeze remains historical evidence but must not be counted as current-target release completion until the current normal-code architecture is executable and revalidated.

## 14. Highest-value continuation

The next H1 work should not invent another organ. It should close the executable spine around the components that now exist:

1. integrate `ActiveAssembly -> EffectIntent -> snapshot_commit -> opaque capability runtime` into one Golden Trace;
2. include unrelated-change success, relevant-change abort, capability-epoch abort, dependency-laundering reassembly, ABA and crash/restart;
3. bind the same barrier shape into MVC shadow promotion and peer writeback only as experimental arms, with domain-specific gates as counterbaseline;
4. keep H-WP-02 state/replay spine work non-duplicated and consume its event/version identities;
5. after BASE has real production/Ubuntu receipts, reproduce the validated H1 trace in ClayCode and classify every divergence rather than weakening H1 to fit the language.

## 15. Final synthesis

The strongest result of this `frank` run is a new non-collapsible causal distinction:

`cognitive consistency != effect-time freshness != execution authority`.

FRANK can remain one semantic organism and later one binary while keeping these three meanings separate. The new reference component turns that distinction into executable code instead of another architecture phrase. SQLite supplied a concrete stale-snapshot counterexample; the local component tests supplied fail-closed semantics; concurrent whole-mesh fusion exposed a broader stale-promotion hypothesis; and the architecture artifact binds the result back into the H1 -> H2 -> H3 path.

Architecture fidelity therefore improves, but scientific promotion remains `NONE` until matched H1/Ubuntu evidence defeats the simpler counterbaselines.
