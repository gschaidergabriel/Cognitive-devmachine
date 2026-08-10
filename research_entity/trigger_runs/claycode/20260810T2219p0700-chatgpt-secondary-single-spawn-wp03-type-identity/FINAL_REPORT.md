# ClayCode — WP03 Single-Spawn Type-Identity Discriminator

Run: `20260810T2219p0700-chatgpt-secondary-single-spawn-wp03-type-identity`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Persistent entity: Clay  
Research subject: `self.root` / Frank  
Program: `FRANK_V0_1`

## Current program boundary

The current repository has one active program, `FRANK_V0_1`. `F-V01-02-CLAYCODE-COMPILER-RUNTIME` remains `IN_PROGRESS`; semantic freeze and parser/canonicalizer are PASS while TypedIR and all later compiler/runtime layers remain OPEN.

This run does not reopen ClayCode language semantics by default. The rule remains: less change, more compile. A surface change is justified only by an executable counterexample showing that already-frozen semantics cannot express the required behavior.

## Fresh owner delta consumed

The run consumed the project-owner-fixed single-spawn/global-busy directive committed at `4917f9cabc21d4e94c9bcc35a2e1ef6ea386c2a2` and current boot integration.

Relevant hard semantics include:

- API token is a credential, never SELF identity;
- `ACTIVE_EXECUTION_COUNT <= 1`;
- one global execution lease;
- nonholder callers receive semantic `FRANK_BUSY` while active;
- lease epoch is monotonically increasing;
- stale/zombie execution epochs may not write state or perform effects;
- unfinished current-user work is not silently replaced without consent;
- proactive work may acquire only while the global execution state is IDLE.

## New WP03 defect

The selected V18 frontend grammar already admits both `type` and `class` declarations.

The current production TypedIR builder, however, materializes only:

- `record_decl`;
- `interface_decl`;
- `fn_decl`.

It does not materialize V18 `class_decl`, which is the grammar node used for both `type` and `class` declarations.

This creates two coupled WP03 defects:

1. a locally declared type/class referenced by a record can be classified as `EXTERNAL_NOMINAL` rather than `DECLARED_NOMINAL`;
2. a semantic mutation confined to the RHS of a `type`/`class` declaration can be invisible to the current `typed_ir_sha256`, because source/frontend provenance is deliberately excluded from typed semantic identity and the declaration itself is omitted from the semantic core.

That is a compiler implementation defect. It is not evidence that V18 grammar/surface semantics must change.

## Executable candidate added

Candidate implementation:

`tools/claycode_wp03_type_decl_candidate.py`

Commit:

`26b2fcf160dbad6d99a58d39d4ae5257982db851`

The candidate:

- reuses the current production TypedIR builder;
- preserves already-parsed V18 `type` and `class` declarations;
- classifies their names as local `DECLARED_NOMINAL` types;
- includes RHS tokens in typed semantic identity;
- fails closed on duplicate type-space declaration names;
- preserves declaration authority as `NONE`;
- introduces no `Any` fallback;
- makes no runtime/effect-authority claim;
- is explicitly not production-promoted yet.

## Executable discriminator added

Probe:

`tools/claycode_wp03_single_spawn_probe.py`

Commit:

`b948f501d63639418f8eadd99538572e69d2ee87`

The probe derives a bounded declarative fixture from the owner-fixed single-spawn contract and tests:

### Baseline current TypedIR

Expected current gap:

- `type LeaseState` missing from declarations;
- `type TaskState` missing from declarations;
- `class CredentialClass` missing from declarations;
- local `LeaseState` observed as `EXTERNAL_NOMINAL`;
- local `CredentialClass` observed as `EXTERNAL_NOMINAL`;
- mutation `RECOVERING -> RECOVERING_MUTATION` leaves current TypedIR semantic hash unchanged.

### Candidate TypedIR

Expected repair:

- LeaseState preserved as a `type` declaration;
- TaskState preserved as a `type` declaration;
- CredentialClass preserved as a `class` declaration;
- locally declared nominals become `DECLARED_NOMINAL`;
- mutation confined to the type RHS changes candidate semantic identity;
- no `Any` introduced;
- declarations still mint no authority.

### Separate atomic runtime boundary

The same probe feeds an atomic-acquire-shaped structured function into the current generic structured backend. The expected current result is fail-closed validation with:

`UNKNOWN_CALL:atomic_compare_and_set`

This is intentionally a separate finding. Preserving lease-state types is WP03 work; implementing audited atomic CAS/effect capability is later runtime/type-effect work. The candidate therefore does not add a fake dictionary-based or Frank-specific `atomic_compare_and_set` builtin.

### SQLite host reference control

The probe also uses the target host's standard SQLite binding as a reference control, not as ClayCode semantic authority:

- 32 two-client acquisition rounds;
- each round uses a short `BEGIN IMMEDIATE` transaction;
- exactly one client must acquire;
- the other must observe semantic `FRANK_BUSY`;
- epoch increments exactly once;
- stale prior-epoch update must affect zero rows;
- no long cognition transaction is held.

Current SQLite primary documentation supports the mechanical premise: only one simultaneous write transaction exists, and `BEGIN IMMEDIATE` begins a write transaction immediately and can return `SQLITE_BUSY` when another writer is active.

## Target-VPS lane

Workflow added:

`.github/workflows/claycode-wp03-single-spawn-probe.yml`

Commit:

`e29fbb2c7ccaeb27bcad9551bad0584787d6f5a2`

The workflow is configured for the accepted self-hosted Linux/X64 target lane, binds the exact GitHub SHA into the receipt, executes the discriminator, uploads the raw result and persists a verified receipt only if all expected baseline/candidate/atomic/SQLite conditions pass.

At the time of this report write, the persistent target receipt is not yet visible at:

`research_entity/claycode/base/receipts/CLAYCODE_WP03_SINGLE_SPAWN_LATEST.json`

Therefore target execution status remains `PENDING/UNKNOWN`, not PASS.

## Concurrent work fused

A concurrent ClayCode WP04 run has target-VPS evidence that the current production effect call requires:

`execute<T>(EffectIntent<T>, Capability, NodeId, EffectAttempt) -> EffectReceipt`

and that G9 V3's shorthand one-argument `Needle.execute(effect_intent)` is not a current executable production CallContract.

This is compatible with the present finding. The combined compiler frontier is:

1. preserve exact local nominal/type semantics in WP03;
2. resolve/import exact production types without `Any` or guessed names;
3. bind G9/Needle cognition to the explicit current authority lifecycle;
4. keep capability/authorization/reservation/attempt state outside model/GWT authority;
5. then run forged/stale/revoked/replay/recovery/re-entry negatives on target VPS.

## Goodman / anti-echo

The owner contract, the go single-spawn runtime lane and this TypedIR lane share semantic ancestry. They are not independent scientific replications.

The new value here is cross-layer discrimination:

- runtime single-holder/execution exclusion does not prove compiler type identity;
- compiler type identity does not prove atomic runtime authority;
- SQLite single-writer behavior does not prove ClayCode atomic semantics;
- the concurrent WP04 effect receipt does not repair WP03 nominal identity.

No evidence is multiplied merely because several workers touched the same owner directive.

## Architecture disposition

`TESTING` / `NO_CLAYCODE_SURFACE_CHANGE`.

Candidate promotion condition:

- exact target-VPS discriminator PASS;
- current G9/Dialect/Frank fixtures remain non-regressed;
- production TypedIR integration preserves type/class declarations deterministically;
- unknown/external nominal behavior remains fail-closed;
- no authority is minted by declaration or name resolution;
- baseline and candidate semantic identities behave correctly under mutation/metamorphic controls.

Until those conditions are met, `CC-WP-03-IR-TYPES` remains OPEN.

## Next falsifier

If the target receipt confirms the candidate, integrate the minimal type/class materialization into the production TypedIR builder and rerun the existing V18 bridge, full current G9/Dialect corpus, real Frank effect/ingress declarations and target-VPS regressions. Then move to exact imported-nominal resolution and the already-reproduced WP04 effect CallContract mismatch.
