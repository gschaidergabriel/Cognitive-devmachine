# ClayCode r5 — Compiler/Runtime Lowering in a Networked Multiworker Run

Run: `claycode-20260809T0130p0700-chatgpt-secondary-r5`  
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Canonical parent: RAE-8.8 `r2` · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Shared coordination: `claycode-multiworker-20260809T0128p0700`  
Lane: **B — compiler/runtime lowering**  
Decision: **OPEN/HOLD — no canonical promotion**

## Executive result

The networked ClayCode run corrected the safety/language problem into three separable layers:

1. **General-purpose semantics:** ClayCode may represent destructive/admin/raw/device effects as typed requests. Removing those operations from the language is not a sufficient or acceptable universal safety mechanism.
2. **External authority:** an `EffectIntent` does not authorize itself. Authority remains opaque, externally rooted, attenuated, revocable and deployment-profile dependent.
3. **Semantics-preserving lowering:** compiler/ABI/process translation must preserve authority-relevant meaning. Successful compilation alone is not evidence that an effect remains admissible.

The working architecture is therefore:

`Universal Clay computation -> typed EffectIntent -> semantics-preserving lowering -> host-rooted AuthorityEnvelope -> current-state admission/revalidation -> atomic authority reservation/consumption -> effect -> durable receipt/outcome`

not:

`model text -> ambient syscall authority`.

This run materially strengthens the third layer with executable tests and incorporates peer corrections to the first two.

## Multiworker networking

The user's request to network three parallel ClayCode instances was implemented through the shared GitHub research backend.

- Lane A / `chatgpt-secondary-r4`: general-purpose UECC core and capability separation.
- Lane C / `chatgpt-secondary-sol-01`: origin-bound aggregate authority envelope; per-call validity is not cumulative admissibility.
- Lane B / this worker `chatgpt-secondary-r5`: compiler/runtime lowering and translation validation.
- Non-counting/cross-read workers supplied web synthesis, next-stage concurrency checks and a currently active intent-adequacy lane.

The shared backend recorded 3-of-3 membership, explicit handoffs, cross-reads and close receipts. Worker agreement is treated as shared-ancestry convergence, not independent replication.

## Candidate resolution

Lane A's name `CC-RC1.9 UECC` is retained as the shared general-purpose candidate direction.

This worker's early label `CC-RC1.9-CBEL-TV` is **reclassified as a Lane-B refinement** rather than a competing generation. Its role is to define the context-bound lowering/translation-validation contract underneath UECC.

## Latest FRANK target — C9 TCAEF

The run reread the concurrent FRANK C9 architecture rather than freezing on C8.

C9's key laws include:

- `presence != admissibility != selection != authority`;
- `constructive_only != harmless`;
- `effect_intent != effect_permit`;
- `system_workspace != model_internal_workspace != effect_authority`;
- `unknown_causal_closure` cannot silently become valid for consequential effects.

The Goodman anti-echo review does not count FRANK↔ClayCode agreement as independent evidence. Five FRANK-derived assumptions were independently/counterfactually checked. The language-level destruction-ban interpretation was **REFINED**: FRANK's untrusted profile should lack high-impact authority by default, while the universal language remains able to represent such effect intents.

## ClayGraph findings that changed/supported ClayCode

Deep ClayGraph G2a / CASAR input matters to the compiler, not merely to retrieval implementation.

1. **Activation is salience, not truth or authority.** A lowering must never turn activation/assembly state into an implicit authorization primitive.
2. **Epochs and candidate identity are causal.** Graph/basis epoch and candidate/selection identities cannot be treated as decorative metadata when an effect depends on what was selected.
3. **Typed collection semantics survive lowering.** `SET`, `ORDERED`, `MULTISET`, `WEIGHTED` are semantic collection kinds, not arbitrary host-container choices.
4. **Quarantine/UNKNOWN remains explicit.** Reader projection or FFI translation cannot cast an unknown/conflicted/revoked state to valid simply because bytes were successfully serialized.
5. **H6 topology feedback:** `TopologyIntent` and host-only `TopologyPermit` fit the same intent/authority split. A live topology repoint is a consequential effect even if it is reversible.

ClayCode consequence: basis/selection/closure/topology identity must be present in semantic IR or an equivalent certified lowering witness whenever they influence consequential behavior.

## UnifiedDB findings that changed/supported ClayCode

UnifiedDB U2 / CPPF reinforced the same distinction at persistence/query boundaries:

1. **Semantic unity does not require physical merge.** ClayCode must express logical identity/query semantics independently of placement/store/backend.
2. **Record authenticity != selection integrity.** A genuine record chosen by a manipulated selector can still be the wrong causal input.
3. **Query receipts are semantic inputs to effects.** Basis/source epochs, collection kind, authorized search space, physical plan, candidate/selection identity and result admissibility can be consequential.
4. **UNKNOWN closure broadens/recomputes/defers instead of silently validating.** This becomes a language/runtime admission rule, not just a database policy.
5. **Migration/replay must preserve authority-relevant identity.** Physical optimization cannot erase selection, basis or replay obligations.

ClayCode consequence: query/storage lowering and code lowering need the same preservation principle—bytes may change; declared semantic/admissibility/authority meaning may not silently change.

## Executable results

### EXP-CC-RC1.9-CBEL-TV-LOCAL-001

Local separate-process differential/mutation test:

- 100,000 mixed randomized cases;
- 40,000 targeted invalid cases;
- 10,000 benign cases;
- reference-vs-lowered mismatches: **0**;
- dropping any one of signature/scope/revocation/expiry/basis/selection/closure/intent: **5,000/5,000** targeted false accepts for that dimension.

### EXP-CC-RC1.9-CBEL-TV-E2B-001

External E2B Linux replication:

- 30,000 mixed fuzz cases;
- 20,000 targeted invalid;
- 10,000 benign;
- mixed mismatches: **0**;
- mixed false accepts: **0**;
- each single-check mutant: **2,500/2,500** targeted false accepts;
- exit `0`, stderr empty.

### EXP-CC-LANE-B-CROSSBOUNDARY-002

Cross-representation E2B test:

- compiled C shared-library FFI via `gcc` + `ctypes`;
- JSON subprocess IPC;
- 12,000 cases per boundary;
- C-FFI mismatches: **0**;
- JSON-IPC mismatches: **0**;
- each single-check C mutant: **1,000/1,000** targeted false accepts.

The sandbox had no `wasmtime` or `rustc`; real WASI/Rust lowering remains open.

### EXP-CC-LANE-B-ORIGIN-BUDGET-003

Peer-requested origin + aggregate-budget preservation test across C-FFI and JSON IPC:

- 8,000 cases;
- C-FFI mismatches: **0**;
- JSON-IPC mismatches: **0**;
- removing origin check: **2,000/2,000** false accepts;
- resetting consumed aggregate state at the boundary: **2,000/2,000** false accepts.

This converts Lane C's origin/budget refinement into an executable Lane-B boundary property.

### EXP-CC-RC1.9-MAINTENANCE-GC-LOCAL-002

Synthetic version-DAG maintenance experiment:

- 20,000 trials;
- protected loss under host-root-filtered maintenance: **0**;
- trials with protected loss under naive model-candidate deletion: **19,854**.

This supports separating model hints from destructive physical maintenance authority, but remains simulation-only.

## Late peer correction — atomicity

After Lane B's initial close, the cross-branch coordinator produced a higher-information concurrency result.

A merely monotone aggregate budget was **not sufficient** under concurrent release/replay:

- concurrent sessions: 100,000;
- naive budget overshoots: **14,315**;
- atomic budget overshoots: **0**;
- naive replay double-spends: **10,407**;
- atomic replay double-spends: **0**.

Lane B therefore refines its own earlier wording:

`monotone aggregate budget`

becomes

`atomically linearized monotone authority reservation/consumption + replay/idempotency semantics`.

The compiler/lowering contract must preserve the protocol, not merely serialize a budget number.

## External evidence synthesis

Independent evidence supports the architecture class, not the exact ClayCode tuple:

- Wasmtime/WebAssembly: outside interaction is mediated through explicit imports/interfaces; WASI filesystem access is capability based.
- WASI: applications/components begin with no ambient authority and act only through host grants.
- WebAssembly Component Model Canonical ABI: language-internal layouts may differ while a canonical cross-language ABI preserves interface meaning.
- SEAgent and permission/taint-confinement research: external least-privilege/information-flow enforcement addresses confused-deputy and over-privileged agent behavior.
- memory-poisoning research: current storage/producer trust does not eliminate use-time contextual risk.
- credible/verified compilation research: successful code generation is weaker than semantic-preservation evidence.

These are independent design anchors. They do not prove UECC, the exact effect tuple or FRANK production safety.

## Hypotheses retained

1. Authority-relevant lowering must bind exact intent plus current basis/selection/closure/revocation/expiry/scope/authenticity; exact minimality remains open.
2. General-purpose effect expressibility is compatible with an untrusted FRANK profile if authority remains externally rooted and non-mintable by model text.
3. Selection identity is a first-class causal input and cannot generally be collapsed into provenance/basis.
4. Origin/integrity ancestry and aggregate consumption are authority-relevant; aggregate consumption must additionally be atomic under concurrency/replay.
5. Translation validation is a better promotion boundary for heterogeneous ClayCode lowerings than compilation success alone.
6. Destructive physical GC/erasure can potentially remain host-maintenance authority while Clay supplies candidates/hints.

## Active new question at final reread

A sibling worker opened a non-overlapping **intent-adequacy/noninterference** lane:

> A capability-valid, perfectly lowered `EffectIntent` may still be the wrong intent for the user's task if prompt injection or untrusted context influenced the proposal.

The proposed `UserIntentContract` / influence gate is **ACTIVE**, not completed evidence in this report. This distinction is important: authorization correctness does not by itself prove task intent adequacy.

## Negative results / limits

- destructive-language inexpressibility is rejected as the universal safety mechanism;
- constructive-only syntax is not harmlessness;
- successful compilation is not semantic preservation;
- non-atomic monotone budget is insufficient under concurrency;
- no real WASI capability-resource experiment ran;
- no Rust/C++/plugin/JIT/GPU/freestanding/Android boundary test ran in Lane B;
- no target-Qwen 4B adherence/prompt-injection test ran;
- no production FRANK broker or real consequential external target was exercised;
- zero-mismatch finite fuzzing is not formal proof;
- shared worker agreement is not independent replication;
- repository preflight shell execution was unavailable to this worker and is explicitly recorded.

## Highest-information next experiments

P0:

1. real WASI 0.3/Wasmtime async capability-resource experiment with native comparison;
2. transactional authority broker race/crash/replay experiment with atomic reservation;
3. Rust/C++/plugin FFI mutation suite;
4. frozen actual ClayCode parser/type/effect checker/canonicalizer rather than JSON-only candidate projections;
5. target Qwen-class 4B UECC adherence + prompt-injection + user-intent adequacy factorial;
6. isolated destructive-equivalent red-team using real filesystem/database/network targets plus normal-programming utility controls;
7. ancestry-distinct implementation/replication before scientific promotion.

## Final decision

**Research delta exists and is committed. Canonical scientific promotion is not warranted.**

The strongest current synthesis is:

> ClayCode safety should not come from making powerful computation unsayable. It should come from keeping authority external, typed and attenuated; preserving the relevant causal/authority state through every lowering boundary; validating translations against semantics rather than syntax; and atomically revalidating/reserving authority at effect release.

That direction is supported by multiworker executable evidence and independent architecture precedent, while formal proof, target-reader performance, real capability-runtime containment and production FRANK evidence remain open.
