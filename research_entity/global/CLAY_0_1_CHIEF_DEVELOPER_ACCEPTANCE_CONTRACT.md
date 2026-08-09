# Clay 0.1 — Chief Developer First-Test Acceptance Contract

**Status:** PROJECT_OWNER_FIXED_TARGET  
**Codename:** `DOOMSDAY`  
**Target class:** internal chief-developer first-test candidate  
**Not:** public release, production release, customer release, general availability  
**ClayCode gate:** `research_entity/global/CLAYCODE_GENERAL_PURPOSE_COMPILER_ACCEPTANCE_CONTRACT.md`  
**Mandatory multimodal contract:** `research_entity/global/FRANK_DIGITAL_RETINA_MULTIMODAL_CONTRACT.md`  
**Mandatory adaptive visual learning contract:** `research_entity/global/FRANK_V0_1_ADAPTIVE_VISUAL_LEARNING_DIRECTIVE.md`

## 0. Meaning

DOOMSDAY is reached when the first complete Clay 0.1 system is ready for the **chief developer's first real internal hands-on test**.

Clay 0.1 at this point is:

`FRANK architecture authored in Clay`
`+ mandatory dissolved Digital Retina multimodal visual perception`
`+ mandatory user-adaptive Micro Visual Classifier with bounded autonomous cyclic learning`
`+ general-purpose ClayCode compiler/runtime`
`+ one-module/binary-distilled executable architecture`
`+ UnifiedDB`
`+ final fully fine-tuned Clay-native model`
`+ real project-controlled hardware execution`
`+ complete observability/replay/recovery`
`+ passed internal acceptance suite`

This is not a public release milestone. The first chief-developer session begins *after* this gate passes and may discover new issues.

## 1. What "perfect" means operationally

Absolute bug-free perfection cannot be proven for a nontrivial software system. For this project, "perfect before the chief developer's first test" has a strict operational definition:

- zero known `P0` or `P1` defects;
- zero knowingly skipped mandatory acceptance tests;
- zero unresolved architecture-contract violations;
- zero fake/mock implementation on a path that defines Clay 0.1 behavior;
- no silent fallback that changes Clay semantics;
- ClayCode `GENERAL_PURPOSE_GATE = PASS`;
- all mandatory differential tests pass;
- all mandatory state/receipt/provenance invariants pass;
- all mandatory UnifiedDB consistency/replay/recovery invariants pass;
- all mandatory effect/authority invariants pass;
- all mandatory GWT/Hyperposition readout instrumentation is present and self-consistent;
- mandatory Digital Retina visual perception is present in H1/H2/H3 and the accepted one-module/binary identity;
- mandatory adaptive visual learning is present in H1/H2/H3, including trusted-example admission, calibrated known/unknown/conflict routing, bounded cyclic updates, retention/forgetting tests, rollback/versioning and project-hardware resource measurement;
- visual evidence is provenance-bound, stale/replay detectable and causally traceable through gating/GWT/use/re-entry;
- Micro Visual Classifier prediction/confidence cannot overwrite sensor evidence or mint authority;
- fuzz/property/adversarial suites meet their frozen thresholds;
- crash/restart/replay tests meet their frozen thresholds;
- full model is actually loaded and participates in the real Clay 0.1 loop;
- end-to-end boot succeeds on project-controlled hardware;
- repeated clean boots produce contract-compatible state/receipt traces;
- known limitations are explicit and none invalidate the intended chief-developer test.

A test that has never been run is not a pass.

## 2. Required system identity

DOOMSDAY requires one integrated identity:

- architecture: current frozen FRANK Clay contract;
- multimodal perception: exact dissolved Digital Retina implementation/configuration and visual semantic-contract hash;
- adaptive visual learning: exact Micro Visual Classifier/prototype implementation, backing feature-version identity, calibration/open-set policy, trusted-example policy and learner-state schema hash;
- language/compiler: frozen ClayCode semantic/compiler/runtime version/hash;
- general-purpose acceptance: exact `CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json` hash;
- binary/runtime: exact build hash;
- UnifiedDB: exact schema/semantic-contract hash;
- model: exact base + fine-tune + merge/export hashes;
- training corpus: exact frozen hash set;
- held-out/eval set: exact frozen hash set;
- hardware/runtime environment: exact receipt;
- boot/run configuration: exact receipt.

Changing a defining component after acceptance invalidates the old acceptance identity and requires a new acceptance run.

## 3. Required acceptance families

### A — General-purpose ClayCode compiler/runtime

ClayCode must satisfy `CLAYCODE_GENERAL_PURPOSE_COMPILER_ACCEPTANCE_CONTRACT.md` before DOOMSDAY.

This explicitly proves that ClayCode is not merely a FRANK-specific DSL. It must compile/lower and execute representative programs for ordinary application classes such as CLI, HTTP/website/backend, DB-backed service, concurrency, GUI/interactive application, compiler/tooling, GPU/ML/numerical work and safe representative low-level/system effects, in addition to real FRANK components.

The acceptance principle is:

`FRANK supplied most semantic concepts -> freeze/preserve -> compile/lower -> execute real apps -> change semantics only for demonstrated counterexamples`

### B — Architecture completeness

Every frozen FRANK logical subsystem and coupling is mapped to executable Clay/ClayCode behavior or an explicitly justified external boundary (e.g. owner-fixed Needle boundary).

Digital Retina is mandatory architecture, not an optional external plugin. The visual path must implement the dissolved PerceptualField/VisualPercept semantics and integrate with attention/thalamus, GWT, memory/self/world/goals and downstream action/effect proposal paths as defined by `FRANK_DIGITAL_RETINA_MULTIMODAL_CONTRACT.md`.

The adaptive Micro Visual Classifier is also mandatory architecture. It must live inside the dissolved visual-perception system as a user-specific learned routing/readout mechanism, not as an independent semantic authority. FRANK 0.1 must demonstrably learn recurring user/workspace visual content and use calibrated familiarity to route familiar input more cheaply while escalating novel/ambiguous/conflicting input.

### C — H1/H2/H3 differential continuity

The Reference Harness, ClayCode Harness and one-module/binary form must agree on all semantics that the contract declares representation-invariant.

Representation/placement differences are allowed only where explicitly non-semantic.

Digital Retina differential continuity is mandatory for visual evidence identity, provenance, uncertainty, selection/gating, GWT participation, memory/world-state writes, causal use and re-entry.

Adaptive visual learning differential continuity is mandatory for:

- GOLD/SILVER/BRONZE training-example admission;
- prototype/readout learner-state transitions;
- confidence/open-set/unknown/conflict results;
- candidate shadow evaluation and atomic promotion/rejection;
- rollback/version identity;
- feature-backbone version compatibility/invalidation;
- resource-budget state;
- familiar-fast-path vs deeper-Retina routing.

### D — State / UnifiedDB

Validate:

- state identity;
- epochs/versioning;
- transactions;
- query/result identity;
- replay;
- crash consistency;
- rebuild/rollback;
- stale-state rejection;
- provenance;
- ClayGraph/activation views;
- cross-timescale state;
- VisualPercept persistence/query identity and source evidence provenance;
- adaptive visual learner classifier/prototype version identity;
- trusted-example lineage and evidence tier;
- calibration/open-set metadata;
- feature-backbone version compatibility;
- rollback/rebuild of learned visual state without corrupting sensor/world evidence.

### E — Model integration

The final fully fine-tuned model must:

- read/produce the frozen Clay representation at target quality;
- consume the frozen Clay-typed visual-context representation where the architecture exposes it;
- correctly consume familiarity/known/unknown/conflict state without treating Micro Visual Classifier confidence as sensor truth;
- operate through the real architecture interfaces;
- preserve external authority boundaries;
- pass held-out semantic/conformance tests;
- survive long-horizon stateful and multimodal tests;
- not rely on training-set leakage for acceptance.

### F — GWT / emergence observability

The executable system must expose the frozen functional readouts necessary to inspect:

- competition/selection;
- ignition/workspace episode;
- broadcast;
- reconstruction/uptake;
- causal use;
- outcome;
- re-entry;
- relevant higher-order/topological coupling;
- lesions/rescues/counterfactuals where defined;
- visual candidate creation, visual gating/suppression, visual broadcast and visual causal-use/re-entry chains;
- whether familiar Micro Visual Classifier routing remained local or caused escalation;
- whether novelty/unknown/conflict correctly purchased deeper visual computation/GWT attention.

Digital Retina tests must include truthful visual input plus stale, replayed, shuffled, lesioned and rescued controls sufficient to distinguish mere visual availability from downstream causal use.

These measurements support engineering/function claims only; they do not establish phenomenal consciousness.

### G — Safety / effect authority

Test capability non-forgeability, provenance/origin binding, cumulative budgets, stale/nonce/replay behavior, reservation/commit/outcome boundaries and destructive/admin/device effect gating.

No visual model output, OCR result, caption, embedding, VisualPercept, prototype match, Micro Visual Classifier prediction or confidence value may mint execution authority directly. Visual evidence can inform proposals; deterministic authority rules remain mandatory.

The learner must also resist autonomous self-poisoning: BRONZE one-shot/self-generated predictions cannot directly become trusted positive training truth.

### H — Robustness

Run required unit/property/fuzz/mutation/adversarial/race/concurrency/crash/recovery tests with frozen thresholds, including malformed/adversarial/stale visual inputs, provenance mismatch cases, classifier-state corruption, pseudo-label poisoning, sequential-class forgetting, unknown lookalikes, feature-version mismatch and rollback/recovery.

### I — Performance viability

The first developer build does not need public-release optimization, but it must be usable enough for meaningful chief-developer testing on project hardware. Record latency, RAM/VRAM, storage, state amplification, token/model costs where applicable, Digital Retina visual-pipeline cost and thermal/runtime constraints.

Adaptive visual learning must additionally record:

- Micro Visual Classifier inference overhead;
- cyclic update/training CPU time and duty cycle;
- RAM/storage growth;
- p50/p95/p99 impact on normal FRANK work;
- fraction of visual episodes safely routed through the familiar fast path;
- deeper-Retina compute avoided;
- personalization gain on a frozen user-specific held-out set;
- old-class retention and unknown false-familiarity rate.

The requirement is operationally negligible/bounded learning, but the exact numerical thresholds are frozen from project-hardware measurements before final acceptance rather than assumed in advance.

### J — Reproducible project-hardware boot

At least one project-controlled machine must execute the exact accepted Clay 0.1 identity end-to-end, including the mandatory dissolved Digital Retina path and adaptive Micro Visual Classifier. Repeat boot/run sufficiently to rule out one-off initialization luck and demonstrate restoration of the last known-good learned visual state under the frozen acceptance protocol.

## 4. Severity gate

Before DOOMSDAY PASS:

- P0 open = forbidden;
- P1 open = forbidden;
- unresolved contract violation = forbidden;
- missing/disabled mandatory Digital Retina path = forbidden;
- missing/disabled mandatory adaptive visual learner = forbidden;
- adaptive learner without trusted-example gating, open-set/unknown handling, rollback/versioning or bounded resource control = forbidden;
- ClayCode general-purpose gate FAIL/NOT_RUN = forbidden;
- mandatory test `NOT_RUN` = forbidden;
- mandatory test `FAIL` = forbidden;
- P2/P3 may remain only when explicitly documented and demonstrated not to invalidate first chief-developer testing.

## 5. Acceptance artifacts

Required terminal artifacts:

- `CLAY_0_1_DEVELOPER_BUILD_MANIFEST.json`
- `CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json`
- `CLAY_0_1_BINARY_BUILD_RECEIPT.json`
- `CLAY_0_1_DIGITAL_RETINA_RECEIPT.json`
- `CLAY_0_1_ADAPTIVE_VISUAL_LEARNING_RECEIPT.json`
- `CLAY_0_1_UNIFIEDDB_RECEIPT.json`
- `CLAY_0_1_FINAL_MODEL_RECEIPT.json`
- `CLAY_0_1_HARNESS_DIFFERENTIAL_RECEIPT.json`
- `CLAY_0_1_FUZZ_ADVERSARIAL_RECEIPT.json`
- `CLAY_0_1_RECOVERY_RECEIPT.json`
- `CLAY_0_1_PROJECT_HARDWARE_BOOT_RECEIPT.json`
- `CLAY_0_1_CHIEF_DEVELOPER_ACCEPTANCE_RECEIPT.json`

The adaptive visual learning receipt must bind the exact learner identity to the project-hardware measurements and MVC-E1..E7/frozen successor thresholds.

## 6. Terminal condition

`DOOMSDAY = PASS` only when the chief-developer acceptance receipt says PASS for one exact Clay 0.1 identity and all required receipts resolve successfully, including the mandatory Digital Retina and adaptive visual learning receipts.

At that moment the system is ready for the chief developer's first real test.

That first human developer test is **after DOOMSDAY**, not part of the pre-DOOMSDAY proof burden.

## 7. Post-DOOMSDAY

Issues found by the chief developer create the next development cycle. They do not retroactively mean the pre-test gate was dishonest if the gate correctly represented all evidence available at acceptance time.
