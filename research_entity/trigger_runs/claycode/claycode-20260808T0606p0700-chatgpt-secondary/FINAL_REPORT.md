# CLAYCODE RESEARCH RUN — CC8 Observed Transition Closure / Predicate-Safe Effects

**run_id:** `claycode-20260808T0606p0700-chatgpt-secondary`  
**trigger:** `claycode`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**parent ClayCode run:** `claycode-20260808T0549p0700-chatgpt-secondary` (CC7)  
**interconnect preflight:** `INTERCONNECT_MANIFEST.json`  
**boundary:** local numeric work and Judge0 replication are constructed runtime proxies. No live-FRANK, target-Qwen or production-security claim is promoted.

## Executive synthesis

CC7 established the `CC-RC1.2 Transition Closure Capsule`: semantic operation identity, compiler-derived read/write/invariant/effect/capability closure, scoped freshness and an external authority gateway. CC8 finds one remaining semantic hole:

> **Even an exact set of existing object reads/writes is not a complete dependency model. A transition may depend on the absence of an object, a predicate/range, a cross-object invariant, a temporal/environment value, or a causal workspace/regime state.**

The CC8 OPEN candidate is therefore:

# CC-RC1.3 — Observed Transition Closure Capsule (OTCC)

`canonical semantic operation`
`→ trusted compiler derives conservative static dependency/effect envelope`
`→ reader/model projection + Gamma(basis state)`
`→ execution under complete access/effect interposition`
`→ observed did-depend/did-effect trace`
`→ prove observed_trace ⊆ static_envelope`
`→ validate typed freshness/invariant/capability witnesses`
`→ commit internal state OR atomically commit durable external-effect intent`
`→ external capability-gated idempotent release`
`→ effect receipt → outcome → re-entry`

The critical trust rule is now sharper:

**The model proposes an operation and arguments. Trusted semantics derive what the operation may depend on or affect. Runtime observation may narrow that trusted envelope, but may never expand beyond it silently and may never self-authorize execution.**

This makes ClayCode less dependent on one syntax and more like a versioned semantic transition machine with explicit proof/receipt surfaces.

---

## 1. Mandatory interconnected research grounding

CC8 executed the new research-mesh preflight before Fusion 1. The materialized manifest is `INTERCONNECT_MANIFEST.json`.

### Clay G7

G7's Hierarchical Semantic Causal Kernel independently converged on:
- typed change propagation rather than one scalar coupling measure;
- asymmetric coordination compiled from dependencies/invariants;
- dependency-scoped Gamma;
- fail-closed behavior when invariant coverage is unknown;
- adaptive semantic resolution rather than universal global work.

G7's synthetic dependency-Gamma proxy reported 0 current-invalid references under an exact dependency map while rebuilding only 9.58% of masks; deliberately stale Gamma produced 47.875% invalid references. Its pair-sensitive coordination proxy achieved much lower coordination than broad class-level closure with zero misses **only because the constructed dependency semantics were exact**.

### FRANK

The latest completed FRANK cycle corrected an earlier optimization priority: a class named `GlobalWorkspace` is not evidence that competition/broadcast is causally operational. Live reachability/competition/effect/outcome/re-entry should be proven before transport optimization.

A newer FRANK Cycle 3 was still in progress during CC8 and therefore was included as fresh incomplete evidence. It identifies `workspace_broadcast.py` persisted via `consciousness.db` as the current live GWT path and proposes hybrid freshness: 60 s heartbeat plus semantic-dirty/query refresh and high-salience refresh. Its OPEN question — *which channel revisions form a sound dependency scope for workspace validity?* — directly becomes a CC8 use case for typed temporal/channel witnesses.

### GWT R2

GWT R2 separates logical global availability from all-to-all physical push and reframes re-entry freshness as **value/freshness at use time**, not a fixed TTL. It proposes episode/source-state/regime/age/predictive-value receipts. CC8 treats those as temporal/causal dependency witnesses rather than as authority by themselves.

### Hyperposition H2

H2 separates:
- semantic dependency topology `S`;
- invariant-interference/coordination topology `C`;
- physical locality topology `P`.

It also separates signed delta semantics (`ADD`, `RETRACT`, `REPLACE`, `COMPENSATE`) from concurrency policy and authority. Its deliberate mis-scope proxy was slightly faster while violating invariants, making scope soundness a hard tripwire for CC8.

### Emergenz

No dedicated current Emergenz branch run was discoverable in the repository during the preflight. CC8 therefore does **not** invent one. It retains only the integrated Clay evidence boundary: higher-order causal/PID/PEID metrics are complementary diagnostics; emergence claims require intervention, lesion/rescue, recurrence/OOD/robustness and must not collapse to one scalar or to consciousness claims.

### Shared ancestry warning

These branches share substantial actor, literature and proxy ancestry. Their convergence is architecture-level corroboration, **not independent replication**.

---

## 2. Fusion 1 — the CC7 boundary that needed falsification

CC7's strongest invariant survives:

`model proposal != execution authority`

and its main architecture survives:
- canonical semantic IR;
- reader-specific disposable projections;
- `state_root` as basis-snapshot identity/provenance;
- trusted op semantics derive safety-relevant fields;
- external capability/root/nonce/revocation/rollback/effect receipts.

But CC7's derived closure still centered on object-oriented `read_set/write_set` language. CC8 asked whether that is semantically complete.

The strongest counterexample is a **negative predicate**:

`CREATE_IF_ABSENT(predicate = "no active reservation exists for slot S")`

Two concurrent transitions can both read an empty predicate and then create **different object IDs**. Ordinary object-version overlap can therefore be empty even though both operations jointly violate uniqueness. This is the classic phantom/write-skew shape at the semantic-contract level.

CC8's first hypothesis was consequently that ClayCode needs typed dependency witnesses, not only object IDs.

---

## 3. External research fusion

### PostgreSQL Serializable / Serializable Snapshot Isolation

Current PostgreSQL Serializable isolation explicitly monitors conditions that could make concurrent execution inconsistent with every serial order. PostgreSQL documents predicate locking and notes that predicate lock granularity can affect serialization-failure rates. Ports & Grittner's production SSI paper describes PostgreSQL's implementation and the need to track read dependencies/predicate conflicts.

**Transfer to ClayCode:** an operation can semantically read a *set defined by a predicate*, including an empty set. Freshness/coordination must therefore be able to witness that predicate or the invariant it protects, not only rows/objects that happened to exist.

### Type-and-effect systems

Koka demonstrates a mature implementation where function effects are inferred/tracked in types rather than supplied as informal annotations. Current 2026 work `arXiv:2607.27074` extends this idea to **temporal dependency effects**, explicitly targeting stale reads, ordering and feedback behavior.

**Transfer:** ClayCode's trusted op semantics can statically infer a conservative `may-depend/may-effect` envelope including temporal dependencies.

### Dynamic dependency tracking / self-adjusting computation

Self-adjusting computation records dynamic dependence graphs during execution and reuses them for change propagation. The key transferable mechanism is path sensitivity: one static computation may depend on a large possible set, while a specific execution touches a much smaller actual dependency trace.

**Transfer:** runtime observation can reduce revalidation cost — but only if every relevant access is interposed and the observed trace is checked against a trusted static upper bound.

### WIT / Component Model capability boundary

WIT defines typed interfaces/contracts rather than behavior, and resources cross component boundaries as handles with ownership/borrowing semantics. Component worlds explicitly enumerate imports/exports.

**Transfer:** ClayCode can expose opaque capability/resource handles to cognition without exposing credentials. Interface availability and resource handles still do not replace application-level freshness/invariant/authority checks.

### Transactional outbox

Azure and AWS both document the transactional-outbox pattern: persist business state plus an outgoing event/intent in one local transaction, then relay later. Delivery is typically at-least-once, so idempotency/deduplication remains necessary.

**Transfer:** an irreversible ClayCode `EFFECT_PROPOSAL` should not execute while the internal state transaction is still speculative. Commit state + durable effect intent first; then release through the external capability gateway with idempotency and receipts.

### RAE registered provider evidence

CC8 directly executed the registered providers through the repository bridge:
- OpenAlex: SUCCESS;
- arXiv: SUCCESS and returned *Serializable Snapshot Isolation in PostgreSQL*;
- Tavily: SUCCESS and surfaced predicate-lock/SSI/outbox sources;
- Exa: SUCCESS and surfaced transactional/predicate dependency work including isolation checkers;
- Judge0: SUCCESS for independent runtime replication.

Semantic Scholar remained health-cached `RATE_LIMITED`; E2B remained credential-unavailable. Hugging Face target-model inference remained `QUOTA_EXHAUSTED_CACHED` until 2026-09-01 UTC. Covering fallbacks and evidence boundaries are recorded in `TOOL_EXECUTION_MANIFEST.json`.

---

## 4. Empirical work

Full machine-readable results: `EXPERIMENT_RESULTS.json`. Reference semantics: `CC_RC1_3_REFERENCE.py`.

### EXP-CC8-PREDICATE-001 — object-only vs predicate-aware freshness

100,000 constructed concurrent pairs. About 30% targeted the same logical uniqueness predicate while inserting different object IDs.

Results:
- true predicate conflict rate: **0.30019**;
- object-only conflict miss rate given a true conflict: **1.00000**;
- predicate/invariant witness detection given a true conflict: **1.00000**;
- whole-root second-transaction reject rate: **1.00000**;
- predicate-scoped second-transaction reject rate: **0.30019**.

This is a counterexample to universal object-only closure, not a measurement of FRANK's real conflict frequency.

### Independent Judge0 replication

50,000 independently executed pairs in Judge0/Python 3.8.1:
- true predicate conflicts: **15,088**;
- object-only misses: **15,088 / 15,088**;
- predicate detection: **15,088 / 15,088**;
- whole-root second reject rate: **1.00000**;
- predicate-scoped second reject rate: **0.30176**.

The replication confirms the constructed mechanism on another runtime. It does not make the workload realistic by itself.

### EXP-CC8-HYBRID-TRACE-002 — static envelope vs observed trace

100,000 operations over a 10,000-item synthetic state:
- mean conservative static envelope width: **59.83494** dependencies;
- mean actual observed trace width: **5.98355**;
- static/observed width ratio: ~**10.0x**;
- exact-observed conflict misses with complete monitoring: **0**;
- deliberately injected monitor escapes: **2,964**;
- observed-only unsafe misses from those escapes: **3**.

Interpretation: path-sensitive observed traces can reduce validation width substantially, but only when complete interposition is guaranteed. `observed-only` is therefore rejected as a universal architecture.

### EXP-CC8-VOLATILE-003 — non-object semantic dependencies

100,000 generated operations; 24,843 used a volatile input and 5,041 experienced a relevant volatile change.

If the dependency was omitted from the object trace, those changes were invisible. An explicit volatile receipt detected all constructed changes by definition.

Interpretation: time/current workspace regime/random/external snapshot cannot be silently treated as ordinary object state when they affect semantics.

### EXP-CC8-EFFECT-ESCAPE-004 — pre-effect vs post-hoc authority

100,000 generated operations included 18,039 external-effect attempts; 6,408 were deliberately unauthorized/stale.

- pre-effect gateway irreversible violations: **0**;
- post-hoc monitor irreversible violations: **6,408**.

This is deliberately simple but captures a hard asymmetry: observing an irreversible call after it happened cannot make it authorized or reliably undo it.

### EXP-CC8-ENVELOPE-FUZZ-005 — executable OTCC reference

The `CC_RC1_3_REFERENCE.py` prototype defines typed static envelopes and observed traces across:
- object reads;
- object writes;
- predicates;
- invariants;
- volatile inputs;
- effects;
- required capabilities.

100,000 generated traces:
- legitimate traces: **97,128**;
- legitimate false rejects: **0**;
- injected envelope escapes: **2,872**;
- escapes detected: **2,872 / 2,872**.

Boundary: this validates the subset-checker logic in the generated workload; it does not prove a real Python/FRANK compiler can infer complete envelopes.

### EXP-CC8-OUTBOX-006 — crash/retry sanity proxy

100,000 constructed operations with 2% crash probability and 3% relay-duplicate probability:
- naive state-then-effect lost-effect rate: **0.01951**;
- outbox lost-intent rate: **0**;
- outbox duplicate-delivery rate: **0.02939**;
- duplicate real effects with ideal idempotency: **0**.

The rates are input parameters/proxy outcomes, not production estimates. The mechanism matches the externally documented outbox tradeoff: durable atomic intent prevents the dual-write loss mode; relay becomes at-least-once and therefore needs idempotency.

---

## 5. CC-RC1.3 semantic contract

The OTCC is a **semantic object**, not a frozen text syntax.

### A. Model-visible proposal

Minimum cognition-facing semantics:

```text
op_id
args
basis_state_ref
provenance_ref
causal_episode_ref?
opaque capability/resource refs when needed
```

The model may additionally predict/explain effects or dependencies, but those fields are non-authoritative.

### B. Trusted static envelope

Derived by the runtime/compiler from `op_id + op_semantics_version/hash + args/types`:

```text
may_read_objects
may_write_objects
may_read_predicates_or_ranges
may_touch_invariants
may_read_volatile_or_temporal_inputs
may_emit_effect_classes
required_capability_classes
coordination_scope_candidates
```

Unknown reflection/FFI/tool/native access either has an explicit host wrapper/effect declaration or forces conservative escalation.

### C. Runtime observed trace

Complete interposition records what this execution actually touched:

```text
did_read_objects
version_witnesses
did_read_predicates/ranges
predicate/index epochs
did_touch_invariants
invariant epochs
did_read_volatile inputs + receipts
did_request effects
did_use capability handles
workspace/channel revisions
episode/outcome/reentry refs
```

Hard invariant:

`observed_trace ⊆ trusted_static_envelope`

Escape => abort/fail closed/widen/recompile. Never silently learn a broader authority surface from model/runtime behavior.

### D. Freshness validation

`state_root` remains immutable identity of the basis snapshot but no longer needs to be the only pass/fail bit.

Validate the relevant witnesses:
- object versions for actual object dependencies;
- predicate/range/index epochs for set-valued/negative reads;
- invariant epochs or proven merge/coordination class;
- temporal/regime/source-state receipts;
- op semantics hash/version;
- capability validity, scope, revocation and expiry;
- nonce/replay/idempotency rules;
- causal episode/re-entry compatibility where relevant.

If coverage is incomplete or uncertain, widen scope up to whole-root/global closure.

### E. Internal state versus external effects

`PURE_TRANSFORM` / reversible local computation may remain speculative when invariant rules permit.

`STATE_PROPOSAL` commits only after closure validation.

`EFFECT_PROPOSAL` becomes:

`validate -> atomically commit state + durable effect intent -> gateway rechecks current capability/freshness -> idempotent external release -> effect receipt`

This keeps the fundamental authority boundary outside the model and gives crash/replay semantics a concrete durable boundary.

---

## 6. Cross-branch architecture delta

### Clay

G7's asymmetric coordination compiler should consume **trusted compiler-derived** object/predicate/invariant/effect summaries. The phrase “ClayCode supplies summaries” must never mean “accept whatever the model wrote.”

### FRANK

The in-progress hybrid-freshness scheduler gains a representation for `semantic_dirty`: channel revisions, state/predicate dependencies and regime witnesses can be attached to workspace reads. This gives the FRANK live test a concrete question: does scoped witness freshness predict when pre-query refresh changes focus/response/state better than wall-clock age or whole workspace root?

### GWT

Episode/source-state/regime/predictive-value fields become ordinary typed causal/temporal witnesses in ClayCode. This unifies observability vocabulary while preserving the scientific rule that receipt presence is not itself proof of functional GWT or consciousness.

### Hyperposition

Delta semantics remain independent:
- `ADD`
- `RETRACT`
- `REPLACE`
- `COMPENSATE`

OTCC maps these changes through semantic topology `S`, invariant/coordination topology `C` and physical topology `P` without conflating them.

### Emergence

OTCC can make interventions, lesions, rescue and outcome/re-entry causally traceable. It does not upgrade correlation or integration into emergence evidence and does not support phenomenal-consciousness claims.

---

## 7. Negative results / revisions

1. Object-only read/write freshness is **not** universal: negative predicates/phantoms are a concrete counterexample.
2. Observed-runtime-trace-only safety is **not** universal: hidden/uninterposed accesses break it.
3. Object traces alone do not cover volatile/temporal semantics.
4. Whole-state root mismatch is safe but not minimally selective in the constructed independent-change workload.
5. Post-hoc effect observation cannot substitute for pre-effect authority.
6. Transactional outbox does not provide magical exactly-once delivery; idempotency/order/receipts remain required.
7. Cross-branch convergence is not independent replication.
8. No live Qwen3-4B result exists in CC8 because the registered HF inference provider is quota-blocked until 2026-09-01 UTC.
9. `CC_RC1_3_REFERENCE.py` is a research reference, not production security code.

Full list: `NEGATIVE_RESULTS.md`.

---

## 8. Highest-information next experiments

### 1. EXP-CC8-LIVE-OPREGISTRY-FOOTPRINT — highest priority

Implement 10–20 **real FRANK/Clay operations** in a trusted semantic registry. For every execution record:
- static envelope;
- observed trace;
- envelope escapes;
- object/predicate/invariant/temporal witnesses;
- actual underlying DB/file/tool accesses;
- validation width/cost;
- replay result.

Fuzz reflection, callbacks, dynamic dispatch, subprocess/tool calls and error paths. **Any undetected escape blocks scoped-closure promotion.**

### 2. EXP-CC8-PREDICATE-INVARIANT-FUZZ

Extract real FRANK uniqueness/capacity/branch/capability/workspace invariants. Compare:
- whole-root validation;
- object-only OCC;
- predicate/range witnesses;
- invariant epochs;
- hybrid observed trace.

Score misses, false rejects, retries, latency and replay fidelity.

### 3. EXP-FRANK-GWT-FRESHNESS-FACTORIAL

On synchronized live/twin traces compare:
- fixed 60 s heartbeat;
- every-query refresh;
- age threshold;
- semantic-dirty global flag;
- channel/dependency-scoped OTCC witnesses.

Measure focus change, response/task effect, later state, DB/WAL p99, write rate and stale decisions.

### 4. EXP-CC8-EFFECT-OUTBOX-FAULT-INJECTION

Prototype durable effect intents behind the capability gateway. Inject crashes/restarts/revocation:
- before state+intent commit;
- after commit before release;
- during release;
- after external success before receipt persistence;
- duplicate relay.

Measure lost effects, duplicate real effects, stale-cap rejection and deterministic replay.

### 5. EXP-LIVE-XENO-CLAY-FACTORIAL

When model quota/runtime is available, run pinned Qwen3-4B with semantically identical inputs:
- natural/free text;
- JSON/schema;
- compact ClayCode projection;
- state-aware Gamma;
- Gamma + OTCC validation;
- projection with compiler-derived safety metadata hidden versus visible.

Measure tokens, exactness, task success, invalid refs, repair rate, latency, energy/memory where available and authority rejects.

---

## 9. Promotion decision

**Canonical promotion: NOT PERFORMED.**

CC8 provides a stronger architecture candidate than CC7 because it falsifies universal object-only closure with a predicate/phantom counterexample, independently replicates that mechanism on Judge0, adds a hybrid static/dynamic closure rule, and connects external-effect reliability to durable intent. But all new numeric evidence remains synthetic/constructed and the decisive real FRANK operation-footprint and live Qwen tests remain open.

Therefore:

- `CC-RC1.2` is not marked REFUTED; its core survives.
- `CC-RC1.3 OTCC` is an **OPEN successor candidate** that refines the dependency/effect model.
- Canonical RAE scientific revision remains r2 unless later live/reproducible evidence warrants promotion.

## Final synthesis

The direction of ClayCode is now much clearer:

> **ClayCode should not ask an LLM to correctly describe everything an operation might touch. It should let the model choose a semantic operation, let trusted runtime semantics conservatively bound its possible effects/dependencies, observe the actual path under interposition, prove that path stays inside the bound, and then validate only the typed witnesses that matter — widening to global closure whenever sound scope cannot be established.**

That design simultaneously serves token efficiency, dynamic execution, scoped freshness, GWT/FRANK observability, Hyperposition invariants and the external authority boundary without making any one surface syntax canonical.
