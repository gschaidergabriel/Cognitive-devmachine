# ClayCode Trigger Run — FINAL REPORT

Run ID: `20260809T1607p0700_chatgpt`  
Trigger: `claycode`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2` / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` / `IN_PROGRESS`  
Promotion: **NONE**

## 1. Executive result

This run found a concrete executable ClayCode BASE blocker and did not invent new language semantics to solve it.

The CURRENT G9 V3 source uses syntax that the published `grammar.ebnf` does not accept. A run-local Lark transcription of the relevant published grammar failed immediately on `rule diff>0 => ...`; the CURRENT G9 V3 source also uses an `if` block while the published grammar has no conditional statement production. A minimal grammar-only repair adding comparison operators and `if/else` parsed the tested specimen.

Therefore the strongest current interpretation is:

> **The next BASE step is parser/grammar realization and whole-spec self-conformance, not broad semantic redesign.**

This is a negative result against the current grammar artifact, not against the larger G9 semantic model.

A second executable seed experiment implemented a small deterministic capability checker from current G9 rules. It matched 6/6 positive/negative oracle cases, including rejection of textual capability names, stale capabilities, wrong verbs, wrong actors and revoked capabilities. This supports retaining the existing `model output != authority` boundary while the real type/effect checker is built.

## 2. Canonical/current-state grounding

Verified before research:

- entity `frank-project-global-research-entity`, RAE-8.8;
- canonical revision `2`;
- canonical state hash `04234ef...f489346`;
- current organ `chatgpt-secondary`;
- current program stage `BASE_CLAYCODE_RELEASE`;
- ClayCode release workspace gate `NOT_PASS`;
- all CC-WP-01..14 were still OPEN in the workspace observed by this run;
- mandatory adaptive visual learning is now a fixed FRANK v0.1 requirement and BASE ClayCode must express its state/update/replay semantics.

Primary internal refs:

- `research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json`
- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
- `research_entity/global/RESEARCH_TRIGGER_REGISTRY.json`
- `research_entity/rooms/PROGRAM_STATE.json`
- `research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json`
- `research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay`

## 3. Mesh coverage / Fusion 1

All current scientific branch foundations were loaded for this run. Deep substrate inputs were explicitly loaded for ClayGraph and UnifiedDB.

### Clay / integrated stack

Current moving stack points to G9 V3, ClayGraph V2 hyperrelation selection, UnifiedDB V9 dynamic work, current GWT/Hyperposition measurement contracts and the BASE ClayCode stage.

### FRANK

The current FRANK research contract requires ClayCode to be the architecture/implementation IR while preserving a strict external authority boundary. The adaptive visual learning directive adds required version/provenance/open-set/promotion/rollback/resource/replay state semantics.

An exact repository search for `FRANK_ARCHITECTURE.claycode.json` returned no indexed result in this worker. This run therefore records the latest FRANK architecture artifact as unresolved/null locally and does **not** claim a global proof of absence.

### ClayGraph — deep input

Current schema separates:

- exact graph identity/version from activation;
- activation/salience from truth/authority;
- binary relations from explicit typed hyperrelations;
- projection receipts from selection receipts;
- source epoch from graph epoch.

Implication for ClayCode: parser/canonical IR/type checking must preserve n-ary role identity and must never compile activation/salience into authority.

### UnifiedDB — deep input

Current UnifiedDB exposes:

- semantic transactions with base epoch/idempotency/authority scope;
- exact semantic records with epistemic class and source hashes;
- query receipts and bounded state injections;
- snapshots/recovery;
- dynamic work spec revisions and execution receipts.

Implication for ClayCode: backend lowering must preserve semantic transaction and epoch identity. Physical backend choice cannot redefine semantic identity.

### GWT / Hyperposition / Emergenz

No semantic change is proposed. The compiler must eventually represent the required distinctions:

- GWT delivery != reconstruction != use != effect != outcome != re-entry;
- measured value != inferred claim != evidence status != architecture state;
- semantic vs active vs coordination vs physical topology;
- n-ary relation identity and intervention/readout semantics.

### Harness

The current Harness workspace correctly keeps the ClayCode adapter blocked on BASE release. The adaptive Micro Visual Classifier is mandatory in H1/H2/H3. The best future oracle for ClayCode adequacy is therefore a frozen H1 transition corpus replayed differentially in ClayCode.

## 4. Executable experiment A — grammar self-conformance

ID: `CC-EXP-20260809-G9-GRAMMAR-SELF-CONFORMANCE-01`

### Hypothesis

The published CURRENT G9 V3 specimen should parse under the published G9 grammar without semantic reinterpretation.

### Test specimen

Representative exact constructs from CURRENT G9 V3:

- `rule diff>0 => ADD_OR_STRENGTHEN`
- `rule diff<0 => RETRACT_OR_WEAKEN`
- `cycle(input,node){ ... if residual.effect { ... } }`

### Runtime

- OpenAI local Python sandbox
- Python 3.13.5
- Lark 1.3.1
- Linux x86_64

E2B is preferred by the project protocol but was not exposed in this worker's tool surface, so this run does **not** claim E2B evidence.

### Result

Original grammar subset: **PARSE FAIL**

First failure:

`UnexpectedCharacters`, line 2 column 10, token `>`.

Minimal grammar-only candidate repair:

- add `>`, `<`, `>=`, `<=` operators;
- add `if expr block [else block]` production.

Repaired grammar subset: **PARSE PASS** on the same specimen.

### Classification

`NEGATIVE_RESULT` against the published grammar for the tested constructs.

Scientific classes:

- `FALSIFICATION`
- `TOOLING_GAIN`

### Limit

This was not a whole-file parse of every G9 production. The repair candidate is not ready for merge or promotion. The full CURRENT G9 V3, parent V2, dialect registry and frozen FRANK/Harness fixtures must become regression inputs.

## 5. Executable experiment B — capability checker seed

ID: `CC-EXP-20260809-CAPABILITY-SEED-CHECKER-01`

A small deterministic checker implemented the current semantic constraints around capability possession, actor delegation, resource identity, verb permission, validity and revocation.

Cases: 6  
Oracle mismatches: **0**

Covered:

- valid write allowed;
- textual capability name without possession rejected;
- expired token rejected;
- wrong verb rejected;
- wrong actor/model output rejected;
- revoked token rejected.

This is only a seed for CC-WP-04. It does not yet implement full Witness `aw/cw`, nonce/replay protection, scope predicates, monotonic delegation proof or real gateway ABI.

## 6. External research / Fusion 2

Only primary technical sources were used.

### WASI 0.3 / Component Model

Primary sources:

- WASI.dev `https://wasi.dev/releases/wasi-p3`
- WASI.dev roadmap `https://wasi.dev/roadmap`
- WebAssembly/WASI releases `https://github.com/WebAssembly/WASI/releases`
- WIT specification `https://github.com/WebAssembly/component-model/blob/main/design/mvp/WIT.md`
- Wasmtime `https://github.com/bytecodealliance/wasmtime`

Findings:

1. WASI 0.3.0 was released on 2026-06-11.
2. Native async moved into the WebAssembly Component Model via `async func`, `stream<T>` and `future<T>`.
3. WASI.dev documents WASI 0.3 support in Wasmtime 43+.
4. The WIT model provides versioned packages/interfaces/worlds/imports/exports and resource types suitable for a typed host ABI.
5. Crucially, the representation of network access changed from WASI 0.2 to 0.3: 0.2 threaded a `network` capability resource through calls, while 0.3 grants network access via world imports.

### ClayCode implication

This is strong evidence **against** baking backend-specific capability representation into Clay semantics.

Keep:

`Clay semantic capability/authority identity -> target lowering -> backend-specific WIT/WASI/native authority mechanism`

Do not collapse:

`WASI import/world/resource presence == Clay authority`.

Current backend hypothesis:

> Use a version-parametric WebAssembly Component Model lowering with WASI 0.3/Wasmtime as the first current Ubuntu candidate, but compare it directly against a native Ubuntu lowering before promotion.

Reason: current Component Model/WASI now has the async/network/HTTP substrate needed for APP-02/APP-04, but target choice must still be decided by real Ubuntu execution receipts, latency, toolchain complexity and semantic-preservation cost.

## 7. Goodman anti-echo result

Three assumptions were reviewed.

### A. External authority boundary

Verdict: `SUPPORTED`

Why: current-run capability checker independently supports the boundary, and external WASI version evolution shows backend authority representation is not stable enough to be the semantic source of authority.

### B. Compile-first / preserve semantics

Verdict: `REFINED`

The strategy survives. However the published grammar is not yet self-conformant, so parser grammar repair is required before semantic freeze. This is implementation repair, not evidence for semantic reinvention.

### C. Adaptive visual learner expressibility

Verdict: `UNRESOLVED`

The generic representational ingredients appear present, but no H1→ClayCode differential learner execution was run. Do not add learner-specific syntax yet. Use the frozen H1 learner transition corpus as the discriminating oracle.

## 8. Hypotheses and counterhypotheses

### H-CC-20260809-01 — parser lag, not semantic failure

Hypothesis: immediate BASE blocker is parser/grammar realization lag.

Counterhypothesis: full-spec parsing exposes deeper control-flow/type semantics gaps.

Next falsifier: complete parser parses all current G9 artifacts and frozen FRANK fixtures with deterministic roundtrip.

### H-CC-20260809-02 — version-parametric Component Model backend

Hypothesis: ClayCode should support a version-parametric Component Model ABI and test WASI 0.3/Wasmtime first on Ubuntu.

Counterhypothesis: a native-only backend reaches APP-01..10 faster and with lower semantic translation risk.

Next falsifier: compile the same capability-bearing CLI+HTTP program to native and WASI 0.3; compare receipts, latency, binary/toolchain cost and authority mapping.

### H-CC-20260809-03 — adaptive learner needs no special language primitive

Hypothesis: existing generic version/provenance/transaction/effect semantics are sufficient for MVC state.

Counterhypothesis: promotion/rollback, trust-tier admission, open-set conflict or feature-version invalidation exposes a missing primitive.

Next falsifier: H1 learner transition corpus differential replay in ClayCode.

## 9. New negative result

`N-CC-20260809-01`

Claim refuted within tested scope:

> The published G9 grammar accepts representative syntax already used by CURRENT G9 V3.

Result: **REFUTED_FOR_TESTED_SPECIMEN**.

Preserve this until a full conforming parser/grammar supersedes it with executable evidence.

## 10. Architecture / implementation delta

No canonical ClayCode semantic promotion is justified.

Recommended immediate work order:

1. **CC-WP-02 parser/canonicalizer** — make current G9 artifacts self-parse; add full-spec grammar regression.
2. **CC-WP-04 type/effect checker seed** — extend capability checker into Witness/authority/freshness/replay semantics.
3. **CC-WP-03 typed IR freeze** — only after parser exposes real representational gaps.
4. **CC-WP-05 evaluator** — execute pure/deterministic core.
5. **CC-WP-06/07 lowering+ABI** — implement native and/or Component Model backend with target-version descriptor.
6. **APP-01 then APP-02** — CLI first, then HTTP website/service.
7. **H1 learner transition corpus** — make adaptive learner semantics a differential oracle, not a speculative syntax-design source.

## 11. ClayGraph and UnifiedDB findings that changed/supported/challenged ClayCode

### ClayGraph

Supported current ClayCode boundaries:

- n-ary/hyperrelation roles must be typed;
- graph projection/selection receipts remain separate;
- activation/salience cannot authorize effects;
- graph epoch/source epoch survive lowering.

Changed ClayCode action:

- full parser/type regression must include hyperrelation roles and graph receipt structures, not only simple records.

### UnifiedDB

Supported current ClayCode boundaries:

- semantic transaction identity and authority scope are first-class;
- exact semantic state and derived query/graph views remain distinct;
- dynamic work specs are revisioned and revalidated before execution.

Changed ClayCode action:

- backend ABI version must be metadata/lowering identity, not a semantic transaction identity change.

## 12. Stage impact

`BASE_CLAYCODE_RELEASE`: remains **IN_PROGRESS / NOT_PASS**.

No application proof has passed in the workspace observed by this run. No parser/canonicalizer release was promoted. No H1/H2 gate is unblocked yet.

However the run reduced uncertainty on the immediate blocker:

- one concrete grammar self-conformance failure is now reproducible;
- a minimal repair candidate exists;
- capability-checker implementation has a working seed;
- current WASI 0.3 backend research gives a version-aware lowering direction.

## 13. Required next discriminating execution

Highest-information next test:

> Build the real parser/canonicalizer against the complete CURRENT G9 V3 + parent V2 + dialect registry, then run deterministic parse→canonicalize→serialize→parse roundtrip and mutation/fuzz tests. Only when the full parser passes should APP-01 CLI lowering begin.

Parallel but secondary:

> Extend the capability seed checker into the full effect/Witness contract and compile the same harmless capability-bearing operation through native Ubuntu and WASI 0.3/Wasmtime lowerings.

## 14. Artifacts

- `INTERCONNECT_MANIFEST.json`
- `TOOL_EXECUTION_MANIFEST.json`
- `EXECUTABLE_RESEARCH_RECEIPT.json`
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `RESEARCH_DELTA.json`
- `GRAMMAR_PATCH_CANDIDATE.diff`
- `FINAL_REPORT.md`

## 15. Final synthesis

The run does **not** justify another ClayCode redesign cycle.

The best evidence-backed move is now to force ClayCode through its own parser. The first executable failure already appeared at the grammar boundary. Repair that boundary minimally, then let full-spec parsing, type/effect checking, real Ubuntu app execution and H1/H2 differential replay decide whether deeper language changes are actually necessary.

This is aligned with the current project law: **less change, more compile**.
