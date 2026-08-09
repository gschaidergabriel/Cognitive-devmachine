# SPAWN FINAL REPORT — ClayCode HTTP + SQLite Vertical Acceptance Slice

Run: `spawn-20260809T1814p0700-claycode-http-sqlite-0a7066`  
Trigger: `spawn`  
Origin branch: `claycode`  
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Canonical parent: r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`

## Executive result

A recent duplicate microdirection was rejected, then the reroll selected a fresh question:

> Can a minimal ClayCode semantic slice realize a real HTTP CRUD service with SQLite transactions using the existing semantic architecture, or does execution expose a genuine missing core-language primitive?

The run produced a **positive local host proxy** but **no production ClayCode pass**.

A deterministic narrow semantic-spec -> Python lowering witness launched a standalone loopback HTTP service with SQLite and passed **17/17** tests covering create/read/update/delete, validation, uniqueness conflict, status behavior, not-found behavior and injected rollback paths.

Four deliberate semantic mutations were then tested:

- commit-before-failure on create;
- wrong create status;
- removed database uniqueness;
- commit-before-failure on update.

All four were detected by the full oracle suite.

This supports a narrow implementation hypothesis:

> **HTTP + database application behavior does not yet justify new ClayCode core syntax. First attempt typed standard-library/FFI adapters over the existing state/effect/outcome/rollback/resource architecture.**

It does **not** prove that the current production ClayCode compiler can do this.

## Stochastic provenance and novelty

Canonical branch distribution was sampled with Python `secrets` / OS CSPRNG.

- branch draw: `0/99` -> **ClayCode** (50% interval);
- first microdirection draw: index `1/7` -> translation-validation / FFI receipts;
- that direction was rejected as a recent duplicate after reading the foreign-effect-closure spawn finalized at commit `903cda18856936a1485d5d47945d9fa9ea7e24ef`;
- fresh candidate set: seven nonduplicate current-stage directions;
- reroll draw: index `0/7` -> **HTTP+SQLite vertical acceptance slice**.

Recent finalized spawn directions checked included async replay, adaptive recurrence, adaptive lesion/rescue, reversal-aware binding, foreign effect closure, FRANK loop lowering, callable identity, adaptive learner state, delta equivalence, affine capability revocation, Harness lowering semantics and effect authority. Searches for recent `spawn HTTP`, `spawn SQLite` and `spawn database` returned no match.

The connector cannot enumerate the spawn directory directly, so this is a commit-linked recent-run audit, not a claim that ten raw `SPAWN_RECEIPT.json` files were directory-enumerated.

Spawn randomness has zero evidential weight.

## Internal architecture fit

Current G9 already separates model intent from execution authority and provides typed `EffectIntent`, desired outcomes, constraints, optional rollback, capability-bearing effects and a deterministic Needle lowering boundary.

The current FRANK projection already treats UnifiedDB as a logical identity/query/transaction/replay plane and the effect gateway as an independent authorization boundary.

The ClayCode BASE acceptance contract is explicitly in compile/realize mode and requires real HTTP/website and database application proofs before release.

Therefore the correct research move is not to invent an `http` or `transaction` keyword immediately. The highest-information move is to attempt the application vertically and let an executable counterexample decide whether the core semantics are insufficient.

## External triangulation

External primary sources support the adapter-first hypothesis without proving it:

1. **RFC 9110** defines stable HTTP request/response semantics separately from version-specific messaging syntax. This supports treating HTTP method/target/status/representation behavior as an interface contract rather than baking transport syntax into ClayCode core semantics.
2. **WASI HTTP** exposes incoming and outgoing HTTP through typed component interfaces/resources and result values. That is a concrete precedent for typed host adaptation.
3. **SQLite** documents explicit BEGIN/COMMIT/ROLLBACK behavior, non-nested BEGIN transactions, SAVEPOINT for nesting and retry-relevant `SQLITE_BUSY` behavior. Clay must preserve these semantics truthfully when SQLite is the physical adapter.

These are architecture comparisons, not ClayCode correctness evidence.

Primary refs:

- `https://www.rfc-editor.org/rfc/rfc9110.html`
- `https://github.com/WebAssembly/wasi-http/blob/main/wit/handler.wit`
- `https://www.sqlite.org/lang_transaction.html`

## Executed experiment

Experiment: `EXP-SPAWN-F1-HTTPDB-001`

Class: `LOCAL_HOST_PROXY_NOT_PRODUCTION_CLAYCODE`

Probe SHA-256: `c041569143b840a7f604061bc1d70a3517badee2b89e087e1c6399b8c55458b3`  
Semantic spec SHA-256: `e9eb1d810277aa733d1f4d98aa21fc0f3ba1ec533d45a4c5ff8e3d1f388090b7`  
Generated target SHA-256: `a6ed8f5ec1ad4a4a0445d29aef51fdbb325faed1251e3b4db097469b2a4eec78`  
Runtime: Python `3.13.5` / SQLite `3.46.1`

Base oracle:

- tests: **17**
- passed: **17**
- final persisted rows: `[(1, "alpha2")]`

Mutation discrimination:

- commit-before-failure / create: detected;
- wrong create HTTP status: detected;
- removed unique constraint: detected;
- commit-before-failure / update: detected.

The injected failure tests are important because a CRUD demo that only returns correct happy-path JSON could hide incorrect commit order. The oracle checks durable state after failure.

## What the experiment supports

### H-SPAWN-F1-01 — OPEN_PROXY_SUPPORTED

A minimal HTTP+SQLite vertical slice is compatible with an adapter-first ClayCode architecture.

### H-SPAWN-F1-02 — OPEN_PROXY_SUPPORTED

Transaction atomicity can initially be attempted as a typed adapter/runtime contract if transaction identity, commit/rollback outcome, partial-effect state and retry semantics are explicit and receipted.

### H-SPAWN-F1-03 — OPEN_INFERENCE

HTTP domain semantics should be tested as standard-library/FFI contracts before any core-language change.

## What it does not support

- no production ClayCode parser/typechecker/compiler/runtime was executed;
- no real ClayCode APP-02/APP-03 acceptance is passed;
- no Andreas Ubuntu target-host evidence was produced;
- no general FFI ownership/lifetime/concurrency proof was produced;
- no capability/effect-closure proof is repeated here;
- no BASE work package is marked complete;
- no scientific canonical promotion is justified.

A key remaining counterhypothesis is that Python/SQLite hides transaction/error/resource semantics that production ClayCode will have to model explicitly. That remains open.

## Architectural decision

**Do not change ClayCode core semantics from this spawn.**

Instead, the production implementation should attempt a typed adapter contract containing at least:

- stable HTTP route/method/request/response value identities;
- explicit DB resource/connection/transaction identity;
- transaction lifecycle and commit/rollback outcome;
- partial-effect/unknown outcome state;
- retryability and conflict classification;
- provenance and generated-target/runtime hashes;
- capability/effect authority checked outside model text;
- deterministic execution receipt linked back to semantic intent.

If the real compiler cannot express one of these without an untyped escape hatch, that becomes the executable semantic counterexample required by the BASE acceptance law.

## Cross-branch feedback

- ClayCode: **SUPPORTING_EVIDENCE** — adapter-first path deserves production test; no core redesign yet.
- Harness: **NEW_CONSTRAINT** — H-WP-03 must eventually include the vertical HTTP+DB fault-injection fixture.
- UnifiedDB: **NEW_HYPOTHESIS** — logical transaction semantics can remain unified while SQLite remains a specialized physical store.
- FRANK: **SUPPORTING_EVIDENCE** — current logical transaction/effect-gateway split is compatible; no FRANK promotion.
- ClayResearch: **NEW_HYPOTHESIS** — test domain capability through typed libraries/adapters before increasing core language surface.
- GWT / ClayGraph / Hyperposition / Emergenz: **NO_CHANGE** for this run.

## Next discriminating action

A dynamic work event was created:

`WORK-SPAWN-CLAYCODE-HTTP-SQLITE-UBUNTU-20260809-0a7066`

It asks the local Ubuntu execution organ to run the same slice through the **production current ClayCode pipeline**:

`source -> parser -> canonical IR -> type/effect -> compiler/lowering -> runtime/FFI -> HTTP+SQLite -> receipt`

The completion verdict must be one of:

- `EXISTING_SEMANTICS_SUFFICIENT`, or
- `EXECUTABLE_SEMANTIC_COUNTEREXAMPLE`.

Only the second outcome justifies reopening core language design, and even then the change must be minimal and falsifiable.

## Durable artifacts and exact commits

- stochastic receipt: `125ae155c35c380322a225da29cadf626d71c80c`
- interconnect manifest: `7a0ce699be942f629aa1c47320f8fe85d98ed74d`
- hypotheses/counterhypotheses: `82d9938359c3fd4108ae66b4864bc5d84b31b648`
- evidence/negative-results manifest: `e4496d92f7250427076f486550cb8d11f7be8987`
- execution receipt: `20b261770937061b1792cfa2af30d8074b8713d9`
- executable probe source: `aa893dfe5a0e9596c8c4e7219cb9f3b9643631cb`
- branch feedback manifest: `f4e5d6d145c21a2e4e44bd7e77c833b9cb4062fd`
- dynamic Ubuntu discriminator work event: `d2b53dde5b0b58606eb9fb15ff9d9e0cce5656b8`

A GitHub `409` occurred while writing the dynamic work event because another worker advanced `main`. Canonical r2/hash was re-read, no existing file was overwritten, and the new append-only event was retried successfully.

## Final scientific state

`RESEARCH_DELTA = COMMITTED`  
`SCIENTIFIC_PROMOTION = NONE`  
`CLAYCODE_CORE_CHANGE = NO`  
`PROXY_RESULT = PASS_17_OF_17_PLUS_4_OF_4_MUTATION_DETECTION`  
`BASE_GATE = NOT_PASS`
