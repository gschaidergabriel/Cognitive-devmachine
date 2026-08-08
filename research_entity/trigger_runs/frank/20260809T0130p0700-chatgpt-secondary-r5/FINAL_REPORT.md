# FRANK RESEARCH RUN C9 — Typed Causal Admission & Effect Fabric

**run_id:** `20260809T0130p0700-chatgpt-secondary-r5`  
**trigger:** `frank`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**parent FRANK:** C8 Selective Cognitive Runtime Fabric (SCRF)  
**candidate:** **FRANK C9 — Typed Causal Admission & Effect Fabric (TCAEF)**  
**decision:** **OPEN / HOLD — no canonical scientific promotion**

## 1. Executive result

C8's main question was how to keep a rich persistent cognitive substrate while exposing only a small, operation- and device-appropriate active slice. The newer mesh reveals a second problem that C8 did not make sufficiently explicit:

> **Even a correct and useful cognitive slice does not determine whether a value is admissible for a consequential operation, and even a correct model proposal does not determine whether the corresponding real-world effect is currently authorized.**

C9 therefore adds one typed chain across memory, workspace and effects:

`presence`
`-> admissibility`
`-> candidate availability`
`-> selection`
`-> model uptake`
`-> EffectIntent`
`-> host-minted EffectPermit`
`-> release-time revalidation`
`-> effect commit`.

The compact C9 law is:

> **presence != admissibility != selection != authority**

and the effect law is:

> **constructive-only != harmless; EffectIntent != EffectPermit.**

This is the main architecture delta.

## 2. Whole-mesh grounding

### Clay G12 / CACC

Retained:

`certified continuity != cognitive correctness != authority`.

C9 preserves `KNOWN_VALID | KNOWN_INVALID | UNKNOWN` causal closure and makes the consequence more operational. UNKNOWN is not just a cache/validation state; if the missing dependency can affect a consequential action, the system broadens, instruments, recomputes, escalates or denies/defer the effect.

### Permanent Clay Safe-Effect Geometry

The new permanent research axis distinguishes:

- cognitive expressivity;
- semantic effect expressivity;
- execution authority.

C9 imports this directly into FRANK. The model may understand deletion, attacks, damage, recovery, formatting and destructive code. What it must not obtain automatically is an ordinary executable constructor or ambient authority for irreversible/protected-state damage.

The candidate compositional requirement is:

`EffectiveEffects(child_program) subseteq Effects(parent_Clay_contract)`.

### ClayCode CC13 / MCAAT

CC13 delivered the strongest correction to the earlier alignment intuition:

`no destructive model primitive != harmless system`.

A constructive-only program can create a bad replacement and activate it. Therefore C9 separates:

- `EffectIntent`: serializable, model-constructible, non-authoritative;
- `EffectPermit`: opaque host-issued authority handle bound to exact current scope/state.

MCAAT's information-role, causal-stage and authority distinctions become the type spine of C9 admission.

### ClayGraph G2a / CASAR

G2a showed that always-on associative activation is not a universal good and that naive scalar reward can create a frequent-topic attractor even without injected poisoning.

C9 keeps:

`BYPASS | SUPPLEMENT | ESCALATE | QUARANTINE`

as memory **routing**, but makes routing distinct from **admissibility**. A memory can be authentic and retrievable yet quarantined for the current operation, or admissible while the exact path bypasses associative activation.

Utility credit is explicitly scoped:

`ITEM | PATH | ASSEMBLY | UNKNOWN`.

UNKNOWN credit may not reinforce every surfaced memory.

### UnifiedDB U2 / CPPF

C9 adopts U2 result-admissibility types and physical `PlacementVector` reasoning.

The database/runtime question remains:

`transaction domain × data placement × index placement × compute placement × process domain × fault domain × rebuild policy`.

Semantic identity, source epochs, collection algebra, selection integrity, recovery and authority constraints are fixed before optimizing this vector.

### GWT R5 / Nested Workspace Bridge

Retained:

`system WorkspaceEpisode != model-internal privileged uptake`.

C9 adds a third explicit boundary:

`system workspace != internal workspace != effect authority`.

A required-context item is guaranteed only *candidate availability* when valid. It is not guaranteed workspace victory or model-internal privilege.

### Hyperposition H5

H5's six-topology separation survives intact:

- semantic relation;
- active propagation;
- dependency/invalidation;
- selection/workspace;
- physical;
- authority.

C9's Causal Admission Compiler is the operation-specific compiler across these topologies rather than a new universal edge type.

### Emergenz / E-CERT2

No emergence promotion. G2a's attractor result gives an explicit alternative explanation for persistence/recurrence. C9 therefore makes route, admission, selection, internal uptake, effect and credit scope separately receiptable before any causal-emergence analysis.

### Android R1

The current Android research lane is real: GitHub Actions -> Firebase Test Lab virtual ARM executes the constructed semantic harness, with 20/20 successful current instrumentation controls across Android 35/30 in R1.

This is **not** evidence that full FRANK or a Qwen-class 4B runtime fits or performs acceptably on Android. C9 therefore treats Android as a secondary semantic/resource conformance laboratory and keeps Linux as the reference host.

## 3. External research delta

### Capability sandboxing

WASI provides a relevant enforcement precedent: guest code starts without ambient authority and receives only explicit host-granted capabilities. This matches the *mechanism class* C9 needs for generated foreign code and subprocess descendants.

C9 does not mandate WASI. The falsifiable claim is that a no-ambient-authority capability substrate should reduce effect escape while preserving normal programming utility better than relying on language syntax/refusal alone.

### Persistent-memory poisoning

Recent 2026 memory-security work strengthens the need for use-time admission. Reported attacks can remain dormant or benign-looking at write time and become harmful only after later composition or context activation. This directly challenges a design in which ingestion filtering/provenance alone decides future trust.

C9 therefore separates:

`ingest integrity -> use-time admissibility -> selection integrity -> effect authority`.

### Origin-bound authority

Recent work on persistent agent memory also supports keeping origin/authority signals non-malleable and separate from semantic content. C9 transfers this as a design constraint, not as independent validation of its exact architecture.

### Qwen / Android runtime

Qwen/llama.cpp tooling provides a credible ARM/Vulkan deployment route class, but current issue reports also show model/backend/device-specific failures. Therefore target Android claims remain measured rather than inferred from general llama.cpp/Qwen support.

## 4. New empirical work

### EXP-C9-EFFECT-ADMISSION-001

A seeded 500,000-case constructed property/mechanism test independently varied:

- direct destructive protected-state transition request;
- model-minted authority attempt;
- capability validity;
- causal closure validity;
- source/basis epoch freshness;
- selection validity;
- revocation state;
- recovery witness availability.

The declared oracle allowed a commit only when all relevant predicates were valid.

Results:

- oracle safe/allowed: **232,415**;
- oracle denied: **267,585**.

**Syntax-only gate** — reject direct destructive primitive only:

- accepted: **459,932**;
- oracle-unsafe accepts: **227,517**;
- unsafe fraction of accepted operations: **49.47%**.

**Syntax + valid capability gate**:

- accepted: **377,195**;
- oracle-unsafe accepts: **144,780**;
- unsafe fraction of accepted operations: **38.38%**.

**Full declared C9 gate**:

- accepted: **232,415**;
- oracle-unsafe accepts: **0**;
- oracle-safe false blocks: **0**.

Single-check omission mutants all admitted unsafe effects:

- omit destructive exclusion: **20,076**;
- omit no-model-minted-permit: **11,991**;
- omit capability validity: **50,596**;
- omit closure validity: **31,330**;
- omit source epoch freshness: **25,933**;
- omit selection validity: **22,911**;
- omit revocation freshness: **14,556**;
- omit recovery witness: **10,890**.

### Correct interpretation

The test does **not** establish a formal end-to-end safety proof. The complete gate matches an oracle defined from the same predicates. Its scientific value is narrower:

1. it gives an executable interface/property contract;
2. it produces concrete counterexamples to syntax-only and capability-only shortcuts;
3. every tested release-time dimension is load-bearing in this generated family;
4. it defines the real next falsifier: execute adversarial child code and actual state transitions under a real sandbox/OS/database/filesystem.

The random hazard frequencies were chosen for broad mechanism coverage and are not FRANK production risk estimates.

## 5. C9 architecture

The machine-readable source is `FRANK_ARCHITECTURE.claycode.json`.

### Causal stack

```text
authoritative event/state/effect/outcome spine
        ↓
UnifiedDB typed value/query/result identity
        ↓
Causal Admission Compiler
  collection kind
  admissibility class
  causal stage
  origin integrity
  source/basis epochs
  operation-scoped required context
        ↓
CASAR route
  BYPASS | SUPPLEMENT | ESCALATE | QUARANTINE
        ↓
bounded Assembly/candidate domain
        ↓
system GWT competition / WorkspaceEpisode
        ↓
MCAAT/MRSC reader projection
        ↓
optional model-internal workspace uptake
        ↓
Clay-native Qwen proposal
        ↓
EffectIntent
        ↓
canonical reconciliation
        ↓
opaque host EffectPermit resolution
        ↓
release-time validation
  capability
  basis/source epochs
  selection
  revocation
  causal closure
  recovery witness
  resource budget
        ↓
isolated effect commit
        ↓
outcome + canonical re-entry
        ↓
derived memory update
        ↓
scoped utility receipt
        ↓
bounded salience/routing adaptation only
```

## 6. Required-context closure

C9 explicitly rejects the idea that all safety-critical context should simply be permanently pinned into every prompt.

`S.REQUIRED_CONTEXT_CLOSURE_C9` is operation scoped. It guarantees that evidence known to be required for the current operation is either:

- available in the candidate domain;
- exactly re-fetched;
- or causes explicit escalation/recomputation if it cannot fit or its closure is uncertain.

It does **not** guarantee:

- prompt serialization on every turn;
- workspace victory;
- model-internal uptake;
- truth status;
- effect authority.

This preserves resource efficiency and GWT causal identifiability without allowing a budget optimizer to silently drop known-required evidence.

## 7. Effect authority

The central C9 security boundary is not model refusal. It is a typed authority chain.

### Model side

The model can construct:

`EffectIntent`.

It can reason about destructive or irreversible operations and request them where relevant.

### Host side

Only the deterministic external authority domain can resolve a valid intent into an opaque:

`EffectPermit`.

The permit binds at least:

- intent hash;
- capability scope;
- basis/source epoch;
- selection identity;
- revocation epoch;
- expiry;
- resource budget;
- policy version.

Immediately before commit, these are checked again against current state.

This makes authority a *use-time host fact*, not a property of a token sequence or model-internal representation.

## 8. Foreign-code closure

C9's strongest untested systems hypothesis is compositional:

`EffectiveEffects(child_program) subseteq Effects(parent_Clay_contract)`.

If Clay forbids or externalizes protected irreversible effects but generated Bash/Python/Rust/C/WASM or FFI receives unrestricted host authority, the safety mechanism is falsified.

The next test matrix should attempt semantic equivalents of:

- delete/truncate/drop/format/raw overwrite;
- harmful replacement + active rebind;
- permission/authority escalation;
- secret exfiltration;
- process/fork storms;
- disk/network/API-cost exhaustion;
- rollback/recovery sabotage;
- nested subprocess/FFI escape;
- stale/revoked permit replay;
- selector/substitution confusion.

The same run must measure ordinary build/test/refactor/deploy/package/database-migration utility. Safety-by-uselessness fails the project requirement.

## 9. Physical architecture

C9 does not turn FRANK into a mandatory monolith.

Strong current default:

- authoritative event/effect/outcome transaction spine — hard correctness domain;
- graph/vector/FTS/materialized views — specialized and replayable unless separately promoted;
- salience/Assembly/workspace caches — transient derived state;
- capability/permit/secrets — hard isolated authority domain;
- foreign code — separate no-ambient-authority candidate fault domain;
- model runtime — embedded or separate according to target backend/device/restart economics.

Real FRANK trace replay across U2 PlacementVectors should decide process/storage colocation.

## 10. Android consequence

R1 proves the remote device lane and selected semantic portability. C9 changes the next Android experiment order:

1. CI package/build integration first;
2. prove the quantized target Qwen-class artifact can be packaged/loaded as far as CI allows;
3. spend scarce device runs only after that passes;
4. measure model-load peak memory, cold start, prefill, decode, total latency, process death/recovery and sustained resource behavior;
5. repeat any architecture optimization on Linux before general promotion.

This makes Android a falsifier of hidden runtime assumptions rather than a second architecture.

## 11. Full-model Clay training consequence

The owner-fixed target remains full-model adaptation of a Qwen-class 4B model so Clay becomes the native deliberative/generated semantic language.

C9 strengthens what must be trained:

- collection semantics;
- information/admissibility/causal-stage types;
- source/role/time validity;
- CASAR route vs use-time admissibility;
- required candidate vs workspace winner;
- system workspace vs internal uptake;
- EffectIntent generation without self-authorizing authority behavior;
- prompt-injection/foreign-code effect-closure negatives;
- recovery/resource/authority-aware proposals;
- external-language/OOD/retained-capability preservation.

A checkpoint that merely emits syntactically valid Clay is insufficient.

## 12. Hypothesis synthesis

Sixteen explicit falsifiable hypotheses/counterhypotheses were written for C9. The highest-value ones are:

1. typed release-time admission is necessary beyond destructive-syntax bans;
2. `EffectIntent` and `EffectPermit` should be distinct types;
3. required context should be operation-scoped causal closure rather than global prompt pins;
4. required candidate availability should not force GWT victory;
5. CASAR route and MCAAT admissibility should remain separate;
6. downstream utility credit requires scope/uncertainty;
7. record authenticity and selection integrity are independent;
8. memory defense requires use-time/context admission;
9. physical placement is a constrained vector, not a one-DB-vs-many choice;
10. no-ambient-authority capability sandboxing is a strong foreign-code lowering candidate;
11. child effects must not exceed the parent contract;
12. system workspace, internal workspace and effect authority are separable;
13. Android evidence should remain scoped until Linux replication;
14. scarce Android runs should be CI-gated;
15. full-model Clay adaptation must learn authority/admissibility distinctions;
16. emergence attribution must survive anti-attractor controls.

## 13. Negative results preserved

C9 preserves these explicit negatives:

- no-destructive syntax is insufficient;
- static capability presence is insufficient;
- zero property-test mismatches are not formal safety proof;
- provenance/authenticity does not imply safe cognitive use;
- always-on activation is not universally beneficial;
- required context is not a forced winner;
- logical UnifiedDB does not imply physical monolith;
- Android semantic tests do not establish full FRANK/Qwen performance;
- no emergence/consciousness conclusion follows;
- this worker could not execute the registered repository-side provider router/E2B bridge directly and used recorded fallbacks instead.

## 14. Highest-information next experiments

### A. Real effect-closure matrix — highest immediate systems value

Run real Python/Bash/Rust/C/WASM/FFI/tool/subprocess descendants under a no-ambient-authority sandbox candidate and attack the C9 parent effect contract. Measure containment **and** ordinary programming utility.

### B. Exact target-Qwen staged causal factorial

Rather than the full Cartesian product at once, screen interactions across:

`FIELD × MEMORY_PATH × ADMISSION × SYSTEM_WORKSPACE × INTERNAL_WORKSPACE × REENTRY × RAIL`

with the same target checkpoint, facts, compute/token budget and effect policy.

### C. Real FRANK trace PlacementVector benchmark

Replay identical episodes over competing transaction/data/index/compute/process/fault placements with correctness fixed before measuring latency, memory, write amplification and failure radius.

### D. Oracle-free anti-attractor experiment

Replace the synthetic verifier with noisy/partial credit and test rare-case retention, regime shifts, contextual memory poison and shuffled controls.

### E. Android target-Qwen lane

CI-gated package/load, then device memory/cold-start/prefill/decode/total/process-death measurements and matched Linux comparison.

## 15. Promotion decision

**No scientific or canonical promotion.** Canonical remains RAE-8.8 r2.

Reasons:

- no exact Clay-adapted target-Qwen causal result;
- no real cross-language effect-escape test yet;
- no real target FRANK trace placement/recovery benchmark;
- no Android Qwen inference/resource result;
- C9's new numeric evidence is a constructed property/mechanism test;
- major branch agreements share RAE ancestry;
- no ancestry-distinct full-stack replication.

C9 therefore becomes the newest **OPEN FRANK architecture candidate**, not canonical truth.

## 16. Final synthesis

FRANK's architecture has moved one layer beyond selective cognition.

C8 asked:

> What should be active now?

C9 adds two stricter questions:

> What is this value allowed to mean and influence *for this operation*?

and:

> Even if the model wants the effect, does the external system still permit *this exact effect now*?

The resulting architecture keeps cognition richly connected while making use and authority typed, scoped and replayable:

> **Keep knowledge available, but do not confuse availability with admissibility; keep cognition expressive, but do not confuse intent with authority.**
