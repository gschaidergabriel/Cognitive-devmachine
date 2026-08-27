# FRANK C9 — ClayCode Architecture Mapping

Run: `20260809T0130p0700-chatgpt-secondary-r5`  
Candidate: **FRANK C9 — Typed Causal Admission & Effect Fabric (TCAEF)**

## 1. Mapping rule

`FRANK_ARCHITECTURE.claycode.json` is the semantic architecture source. Host Python/Rust/C/C++/SQL, graph engines, model tensors/KV, Android/JNI and wire formats are lowerings of declared Clay semantics rather than independent semantic authorities. Needle remains the sole intentional non-Clay semantic subsystem and enters through a typed route certificate.

C9 preserves the C8 separation:

`semantic organ boundary != process boundary != storage boundary != authority boundary`.

It adds a further runtime rule:

`presence != admissibility != selection != authority`.

A value may exist in memory, be authentic, be retrievable, be selected by GWT and influence the model while still lacking permission to cause a real external effect.

## 2. C8 -> C9 delta

C8 SCRF established selective cognition, explicit memory lifecycles, a Salience Governor, a Cognitive Resource Governor and system-workspace/model-internal-workspace separation.

C9 keeps those structures and adds four connected contracts:

1. **Causal Admission Compiler** — assigns collection kind, epistemic/admissibility role, causal stage, source/basis epochs and authorized use before a value enters a consequential cognitive path.
2. **Required Context Closure** — computes operation-scoped evidence that must remain available as candidates. Required inclusion is not a forced workspace winner. Overflow broadens/escalates rather than silently truncating effect-critical evidence.
3. **EffectIntent / EffectPermit split** — model output can construct an intent, but the authority object is an opaque host-minted handle bound to exact scope and current state.
4. **Release-time Effect Commit Context** — current basis/source epochs, selection, revocation, causal closure, recovery witness and resource budget are revalidated immediately before commit.

The strongest corrected rule is:

`constructive_only != harmless`.

Removing direct destructive syntax is useful only as one component. A constructive program can still activate a harmful replacement, misuse stale state, exploit a wrong selection, exhaust resources or delegate to foreign code with ambient OS authority.

## 3. Clay / CACC / Safe-Effect mapping

CACC remains the continuity base:

`certified continuity != cognitive correctness != authority`.

The permanent Safe-Effect Geometry axis maps into C9 as:

- protected state/effect classes;
- recovery witnesses;
- no model-constructible irreversible protected-state effect constructor;
- external irreversible/effect broker;
- authority non-amplification;
- explicit resource budgets;
- child-effect closure across generated code and tools.

The real target is not a word ban. It is a mediated reachable-effect space in which compromised intent cannot automatically expand authority.

## 4. ClayCode / CC13 MCAAT mapping

CC13's correction is first-class in C9:

- `EffectIntent` is serializable and non-authoritative;
- `EffectPermit` is opaque, host-issued and non-model-constructible;
- information role, causal stage and authority are independent types;
- `SET`, `ORDERED`, `MULTISET`, `WEIGHTED` remain semantic collection kinds rather than host-container metadata.

C9 adds these distinctions to query/admission, candidate formation, reader projection and effect release. No implicit cast is permitted from:

`EXTERNAL_EVIDENCE -> AUTHORITATIVE_EXACT`,
`SALIENCE_ONLY -> FACT`,
`MODEL_INTERNAL_ONLY -> EFFECT_AUTHORITY`,
or
`EffectIntent -> EffectPermit`.

## 5. ClayGraph G2a mapping

CASAR remains the associative route controller:

`BYPASS | SUPPLEMENT | ESCALATE | QUARANTINE`.

C9 makes route and admissibility explicitly orthogonal. A memory can be:

- route-worthy but inadmissible for a consequential use;
- admissible but bypassed on an exact/high-confidence path;
- authentic but quarantined because its role/time/context is invalid;
- cognitively useful without becoming canonical truth.

`ActivationUtilityReceipt` carries `ITEM | PATH | ASSEMBLY | UNKNOWN` credit scope. `UNKNOWN` credit is bounded and cannot reward every surfaced memory. This is the C9 answer to the G2a frequent-attractor failure mode.

## 6. UnifiedDB U2 mapping

C9 retains U2's `UnifiedQueryIR` and result-admissibility distinction. Logical semantic unity does not make values epistemically interchangeable.

The physical decision remains a vector:

`transaction domain × data placement × index placement × compute placement × process domain × fault domain × rebuild policy`.

C9 adds effect-envelope constraints before physical optimization. A cheaper plan cannot weaken:

- source/basis epoch correctness;
- collection semantics;
- authorized search space;
- selection integrity;
- recovery/replay obligations;
- effect authority isolation.

Record authenticity and selection integrity remain separate. A perfectly authentic record chosen by a manipulated selector is still a bad causal input.

## 7. Required context semantics

A global permanently pinned prompt is not the C9 design.

`S.REQUIRED_CONTEXT_CLOSURE_C9` is operation-scoped. It means that identified effect-critical evidence must remain in the candidate domain or cause explicit escalation/recomputation. It does **not** mean:

- it must be serialized in every model call;
- it must win the system workspace;
- it must become privileged model-internal state;
- it can mint an EffectPermit.

This preserves GWT competition while preventing a resource optimizer from silently removing known-required evidence.

## 8. GWT R5 mapping

The causal path is:

`admitted candidate domain -> candidate formation -> system competition -> WorkspaceEpisode -> reader projection -> model-internal uptake -> proposal`.

C9 adds effect authority only after those stages:

`proposal -> EffectIntent -> host permit resolution -> release-time revalidation -> effect commit`.

Therefore:

`system workspace != internal workspace != effect authority`.

A system winner can fail to enter the internal workspace; internal privileged state can exist without system selection; neither is a capability.

## 9. Hyperposition H5 mapping

C9 preserves H5's topology separation:

- semantic relation topology;
- active propagation topology;
- dependency/invalidation topology;
- selection/workspace topology;
- physical topology;
- authority topology.

The new C9 admission plane compiles operation-specific slices across these topologies. `UNKNOWN` dependency closure does not silently cast to valid. Consequential operations broaden, instrument, recompute, escalate or deny/defer.

## 10. Emergenz mapping

C9 makes emergence attribution stricter, not easier. Recurrence, persistent salience and coherent re-entry can be artifacts of an adaptive memory attractor. E-CERT2 therefore receives explicit receipts for:

- route/admission;
- candidate topology;
- workspace selection;
- internal uptake;
- effect release;
- re-entry;
- utility-credit scope.

No emergence or consciousness promotion follows from C9 itself.

## 11. Effect safety / foreign-code closure

C9 proposes the compositional runtime condition:

`EffectiveEffects(child_program) subseteq Effects(parent_Clay_contract)`.

This applies to generated Python, Bash, C/C++, Rust, WASM, FFI, plugins, interpreters and tools. The current preferred *candidate* host lowering is a no-ambient-authority capability sandbox, because foreign code should receive only explicit imports/handles. This is not a mandate that the final implementation must use WASI; it is an experimentally attractive enforcement class.

The broker must separately enforce:

- opaque permit issuance;
- current revocation state;
- current source/basis/selection identity;
- recovery constraints;
- resource quotas;
- idempotent effect receipts.

## 12. Linux / Android lowering

### Linux

Linux remains the reference host. C9 should first benchmark real FRANK traces across PlacementVectors, then decide which cognitive modules share an address space or storage engine.

### Android

Android is a secondary semantic/resource conformance laboratory. R1 established a live virtual ARM lane and passed the current constructed instrumentation suite, but did not run full FRANK/Qwen inference.

C9 therefore gates scarce Android device work:

1. CI builds the target Android/JNI/model package;
2. CI proves the quantized Qwen-class artifact can be packaged/loaded as far as possible without a device;
3. device runs measure model load, peak memory, cold start, prefill, decode, total latency, process-death recovery and resource pressure;
4. any general optimization requires matched Linux replication.

## 13. Full-model Clay training mapping

C9 retains full-model adaptation rather than LoRA-only semantic ownership. The curriculum must train more than compact syntax. It should include:

- typed collection and admissibility classes;
- role/time/source-epoch validity;
- CASAR route vs consequential admissibility;
- required-candidate vs workspace-winner distinctions;
- system workspace vs internal uptake;
- EffectIntent generation without self-authorizing EffectPermit behavior;
- prompt-injection and foreign-code effect-closure negatives;
- recovery/resource/authority-aware proposals;
- retained natural/external language capability and OOD composition.

A checkpoint does not pass merely because it emits valid Clay.

## 14. Reversible migration from C8

1. add C9 admission and effect receipts in shadow mode;
2. classify existing UnifiedDB/ClayGraph outputs by collection/admissibility/causal-stage types;
3. compute required-context closure without changing current model context;
4. compare predicted omissions/escalations against current C8 decisions;
5. add EffectIntent objects while keeping the current broker behavior authoritative;
6. add opaque host permits and release-time revalidation in audit mode;
7. run the cross-language effect-escape matrix and normal programming utility suite;
8. enable C9 admission decisions only after target-trace parity/safety tests;
9. enable scoped utility adaptation only after oracle-free anti-attractor tests;
10. retain C8 rollback and authoritative event-spine replay throughout.

## 15. Main empirical status

The new C9 property fuzz demonstrates a mechanism distinction, not production safety. In 500,000 seeded constructed cases:

- syntax-only admitted 227,517 oracle-unsafe effects;
- syntax + capability admitted 144,780 oracle-unsafe effects;
- the complete declared C9 gate matched the oracle with 0 unsafe accepts;
- omitting any single gate dimension produced unsafe accepts.

The next falsifier must move from a declared oracle to real runtime containment: WASI/Wasmtime or equivalent capability sandbox, real child languages/FFI, filesystem/database targets, crash/restart, prompt injection and a matched utility benchmark.
