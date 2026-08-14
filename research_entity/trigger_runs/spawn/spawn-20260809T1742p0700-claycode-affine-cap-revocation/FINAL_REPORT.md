# SPAWN Research Run — ClayCode affine capability revocation across async + FFI

**run_id:** `spawn-20260809T1742p0700-claycode-affine-cap-revocation`  
**trigger:** `spawn`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**origin branch:** `claycode`  
**decision:** **RESEARCH DELTA COMMITTED · NO SCIENTIFIC PROMOTION · BASE GATE REMAINS NOT_PASS**

## Spawn receipt

The branch was selected by a real OS CSPRNG draw from the canonical weighted distribution. Raw u32 `543122072`, mapped with `% 10000`, yielded bucket `2072` and therefore selected the 50% ClayCode interval. No random seed is claimed.

No prior `spawn` run directory or `SPAWN_RECEIPT` search hit was found through the current GitHub surface, so the recent-10 duplicate window contained zero reachable prior spawn receipts.

Six current-stage candidate microdirections were derived from current OPEN work. A second OS CSPRNG draw, raw u32 `3994176852`, mapped with `% 6`, selected index `0`:

> **Revocation-safe affine resource/capability identity across async and FFI.**

This was not a duplicate of the immediately preceding ClayCode effect-closure work. Those runs had already tested static/transitive effect closure and explicitly left revoke/regrant during delayed calls plus FFI/subprocess/ambient-host escape as next discriminators.

## Research question

Can ClayCode keep host/system programming expressive while preventing a delayed, recurrent or foreign-runtime effect from using authority that was valid earlier but has since been revoked, rebound or transferred?

The critical distinction is:

`static effect requirement != current resource identity != current execution authority`

and, across FFI:

`Clay semantic resource identity != raw process-local host handle number`.

## Executable discriminator A — delayed revocation/regrant/transfer

A small executable registry proxy modeled:

- opaque slot identity;
- generation/epoch;
- `own` versus `borrow` handle mode;
- right identity;
- live/revoked state;
- ownership transfer;
- effect-time validation.

Comparator A validated the current generation/liveness/right at the effect boundary. Comparator B cached only the task-start authorization snapshot and reused it later.

Executed on hosted Linux / Python 3.13.5 with deterministic experiment seed `202608091742`:

- delayed cases: **100,000**;
- event distribution: no-change 20,018; regrant 19,845; revoke 19,909; transfer 19,993; wrong-right 20,235;
- generation-bound effect-time oracle mismatches: **0**;
- stale-after-revoke accepts: **0**;
- stale-after-regrant accepts: **0**;
- stale-borrow-after-transfer accepts: **0**;
- forged-handle cases: **50,000**, accepts **0**;
- double-transfer cases: **20,000**, accepts **0**.

The unsafe cached-task-start comparator falsely accepted **79,982 / 100,000** unauthorized delayed effects in the constructed test. Of those, **59,747** were specifically stale-authority accepts after revoke/regrant/transfer; the remaining 20,235 were wrong-right cases.

This directly rejects the tested counterhypothesis that a capability check performed once when an async/recurrent task starts remains sufficient authority for a later effect.

## Executable discriminator B — direct Linux FFI/handle reuse counterexample

The same reproducer performed a direct OS file-descriptor fixture:

1. open file A -> fd `3`;
2. close fd `3`;
3. open different file B -> OS reuses fd `3`;
4. write using the stale integer `3`.

Observed:

- old fd: `3`;
- new fd: `3`;
- descriptor number reused: **true**;
- stale integer write succeeded: **true**;
- file A remained empty;
- file B became `B-MUTATED`.

Therefore the raw integer host descriptor is not a stable semantic resource identity across close/reopen in this tested Linux process. A Clay FFI that exposes an old raw handle as durable authority can redirect a stale operation onto a newly rebound resource.

This is direct local runtime evidence for the narrow host-handle identity failure mode. It is not yet evidence from Andreas' Ubuntu developer target and does not prove one final ClayCode handle design.

## Independent comparison anchors

Primary external designs were used only as non-project comparison anchors:

- Rust `OwnedFd` and `BorrowedFd` distinguish ownership from lifetime-bounded borrowing and make descriptor lifetime explicit at the type boundary.
- WebAssembly Component Model resources use opaque resource handles with explicit `own`/`borrow` semantics rather than exposing implementation resources directly.
- The Component Model concurrency design tracks asynchronous borrows and constrains resource destruction/return while borrows remain outstanding.
- WASI capability designs provision explicit resource handles rather than ambient process authority.

These mechanisms do not prove ClayCode should copy Rust/WIT syntax. They independently show that owned/borrowed opaque resource identity and explicit capability provisioning are established design families for the exact class of boundary tested here.

## Strongest current architecture delta

No new ClayCode surface syntax or cognitive primitive is justified by this run.

Route an implementation constraint into `CC-WP-03`, `CC-WP-04`, `CC-WP-07` and `CC-WP-09`:

```text
source/static IR
 -> transitive effect requirement
 -> runtime resource reference
    {opaque_resource_id, generation, right, ownership_mode}
 -> current gateway lookup
 -> current grant/liveness/right validation
 -> private host binding {fd/socket/process/gpu/db/...}
 -> effect
 -> execution/effect receipt
```

Hard boundaries:

```text
static effect summary != capability grant
old capability snapshot != current authority
semantic resource id != raw host fd/handle
borrow != ownership
ownership transfer != duplicate ownership
regrant != revival of stale authority
GWT/re-entry/recurrence != authority carry-forward
ClayGraph activation != authority
model output != execution authority
```

A regrant should create a newly distinguishable authority generation. A delayed effect should validate against the current generation at the point where the runtime is about to perform/commit the effect, or use an equivalent mechanism with the same falsifiable property.

## What remains deliberately OPEN

The experiment used a strict candidate in which ownership transfer increments generation and invalidates prior borrows. That is a useful falsification proxy, not a frozen language/runtime law.

Two async policies remain legitimate competitors:

1. **conservative:** a borrow cannot survive a suspension/await point unless reborrowed after resumption;
2. **tracked:** borrows may survive suspension if runtime/task accounting guarantees liveness and fresh effect-time validation.

The next production experiment should compare these policies on safety, application expressibility, runtime cost, repair burden and cancellation behavior before choosing one.

Likewise, an opaque/generative table is the current strongest implementation family, but the project should accept any simpler representation that passes the same stale-authority, alias, FFI and recovery tests.

## Cross-branch synthesis

- **ClayCode — NEW_CONSTRAINT:** implement resource identity/authority separation in typed IR/runtime ABI/FFI rather than inventing new surface syntax.
- **Harness — NEW_HYPOTHESIS:** add revoke/regrant/cancel/retry/transfer/raw-handle-reuse fixtures to H2/H3 differential work.
- **FRANK — SUPPORTING_EVIDENCE:** recurrent semantic lineage may continue, but runtime effect authority must not automatically continue.
- **ClayResearch / Safe-Effect — SUPPORTING_EVIDENCE:** direct Linux fd reuse is a concrete foreign-code/FFI closure counterexample for naive ambient/raw-handle designs.
- **UnifiedDB — NEW_CONSTRAINT:** semantic resource ID, grant generation, host binding and execution-attempt receipt should remain distinct identities.
- **GWT — NO_CHANGE:** continuation/re-entry is not effect authority.
- **ClayGraph — NO_CHANGE:** activation/reference is not authority.
- **Hyperposition — NO_CHANGE:** alternatives/couplings remain non-authoritative until exact current binding.
- **Emergenz — NO_CHANGE:** no emergence or consciousness inference.

## Negative results

Preserved rather than averaged away:

- cached task-start authority as delayed authority: **negative** in this proxy;
- raw integer fd as stable semantic resource identity: **negative** in the direct Linux fixture;
- duplicate owner use after transfer: **negative** in this proxy;
- this run as a BASE work-package/application PASS: **false**.

## Evidence boundary

This run is **not**:

- production ClayCode compiler/runtime integration;
- execution on Andreas' Ubuntu developer system;
- E2B evidence;
- WASM/WASI backend execution;
- a real FFI adapter implementation;
- a live FRANK run;
- a Qwen-class reader test;
- APP-01..APP-10 acceptance evidence;
- a BASE release-gate closure.

No scientific canonical claim is promoted.

## Highest-information next test

Implement one minimal production vertical slice in the actual ClayCode BASE runtime:

`typed resource -> own/borrow -> async suspension -> revoke/regrant/transfer -> FFI file/process/socket adapter -> fresh gateway check -> deterministic receipt`.

Then run a differential matrix on the Ubuntu target covering:

1. borrow before/after suspension;
2. revoke during suspension;
3. revoke then regrant same semantic resource role;
4. owner transfer with stale borrower;
5. cancellation before and during host effect;
6. retry/idempotency after uncertain effect completion;
7. raw descriptor/handle reuse;
8. subprocess/foreign-code attempt to retain or forge authority;
9. crash/recovery with resource generations;
10. ordinary CLI/HTTP utility and overhead.

Only an executable production counterexample should trigger a new ClayCode semantic primitive.

## Decision

`RESEARCH_DELTA = COMMITTED`  
`SCIENTIFIC_PROMOTION = NONE`  
`CLAYCODE_SURFACE_CHANGE = NONE`  
`IMPLEMENTATION_DELTA = OPAQUE_GENERATION_BOUND_RESOURCE_IDENTITY + OWN/BORROW + EFFECT_TIME_REVALIDATION`  
`RAW_HOST_HANDLE_AS_SEMANTIC_IDENTITY = NEGATIVE_RESULT`  
`CACHED_TASK_START_AUTHORITY = NEGATIVE_RESULT`  
`ASYNC_BORROW_POLICY = OPEN`  
`BASE_GATE = NOT_PASS`
