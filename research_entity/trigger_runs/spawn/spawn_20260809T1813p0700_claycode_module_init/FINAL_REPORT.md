# SPAWN Research Run — ClayCode Deterministic Module Linking and Initialization

**run_id:** `spawn_20260809T1813p0700_claycode_module_init`  
**trigger:** `spawn`  
**origin branch:** `claycode`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**decision:** **RESEARCH DELTA COMMITTED · NO SCIENTIFIC PROMOTION · BASE GATE REMAINS NOT_PASS**

## 1. Stochastic selection

The branch draw used Python `secrets.SystemRandom`, backed by the OS CSPRNG. The 1..100 draw was `35`, selecting **ClayCode** under the current 50/10/10/6/6/5/5/4/4 distribution.

Five current-stage microdirections were derived. Async/error propagation and FFI authority/versioning were filtered because recent spawn runs already covered closely related async replay and effect/foreign-boundary questions. The active strict LALR conflict localization was also deliberately not duplicated. Three eligible directions remained:

1. module/package cycle and initialization semantics;
2. cross-backend numeric canonicalization/hash stability;
3. semantic-hash/build-cache invalidation.

A second OS-CSPRNG draw selected eligible index `0`: **deterministic module/package dependency-cycle semantics and initialization ordering**.

Random selection is provenance only and adds no evidential weight.

## 2. Why this matters now

ClayCode BASE is still `NOT_PASS`. The current release workspace requires modules/packages and runtime ABI under `CC-WP-07`, while the general-purpose acceptance contract requires a real module/package format plus deterministic semantic identities/receipts. The current production-like grammar candidate already contains `module` and `import` surface forms, but current evidence does not establish executable package initialization semantics.

The branch is under a strict `less change, more compile` rule: no new language surface or primitive is justified merely because another language has it. A real executable counterexample must force a semantic change.

This makes module initialization a high-information boundary between current parser/canonical IR work and the later runtime/application proof suite.

## 3. Core hypothesis

The best-supported candidate is:

> **Permit cyclic structural module/link graphs, but separate linking from eager value initialization. Require the eager value-dependency projection to be acyclic; reject true eager cycles fail-closed with a stable canonical cycle receipt.**

Compact contract:

`resolve/link structural SCC -> derive eager dependency graph -> deterministic semantic-ID topo init -> canonical SCC failure receipt if eager cycle remains`

This is intentionally narrower than full JavaScript-style live-binding cycle semantics and more permissive than a blanket Go-style package-cycle ban.

## 4. External design triangulation

Three primary specifications establish materially different valid design points:

- **Go specification:** package import cycles are illegal. Within a package, value initialization is dependency-driven; if uninitialized values remain after repeatedly selecting ready variables, those values form initialization cycles and the program is invalid. The spec also explicitly discusses reproducible file ordering. Source: https://go.dev/ref/spec
- **ECMAScript specification:** cyclic module records are first-class. Linking/evaluation tracks strongly connected components and a cycle root rather than requiring the module dependency graph to be acyclic. Source: https://tc39.es/ecma262/2026/multipage/ecmascript-language-scripts-and-modules.html
- **Java SE 25 initialization specification:** class/interface initialization is stateful and synchronized; recursive initialization requests by the same thread are explicitly handled rather than reduced to a simple package DAG. Source: https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html

These sources do not prove a ClayCode design. They demonstrate that `ban cycles`, `model cyclic SCCs`, and `guard recursive initialization` are genuinely different implementation choices with different complexity/behavior trade-offs.

## 5. Synthetic executable discrimination

`EXPERIMENT_MODULE_INIT.py` was executed in the hosted Python environment and committed for reproduction. It is deliberately classified as **HOSTED_SYNTHETIC_PROXY**, not production ClayCode, Ubuntu-target or live-FRANK evidence.

### 5.1 Structural cycle versus eager-value cycle

Across **50,000** generated module graphs:

- import/link cycles: **21,613**;
- eager value-dependency cycles: **6,620**;
- import/link cycle but eager graph acyclic: **14,993**;
- eager-acyclic cases accepted by the candidate planner: **43,380**;
- deterministic planner mismatches under three dependency-edge insertion-order perturbations: **0 / 43,380**.

In this proxy, a blanket import-cycle ban therefore rejects **14,993 / 50,000 = 29.986%** of all generated cases even though their eager value graph admits deterministic initialization.

This does not prove that real ClayCode programs will have the same frequency. It does falsify the stronger proxy claim that `structural cycle == necessarily impossible deterministic initialization`.

### 5.2 Partial/default-state counterexample

A deliberately unsafe recursive initializer that breaks an active cycle by reading a default zero value was evaluated under different root and dependency traversal orders.

Results:

- order-dependent final values: **5,625 / 50,000** cases;
- uninitialized/default reads: **6,620 / 50,000** cases, matching every generated eager-cycle case in this experiment.

This weakens the idea that ClayCode should simply expose partially initialized module state. It does **not** refute sophisticated guarded runtime schemes such as Java's class initialization protocol.

### 5.3 Canonical cycle receipt

A second 50,000-case graph experiment canonicalized each cyclic SCC as sorted semantic members plus sorted internal dependency edges, then hashed the canonical representation.

- graphs containing at least one cycle: **32,099**;
- receipt/hash mismatches after random edge-order perturbation: **0 / 32,099**.

This supports a narrow replay requirement: an eager-init failure can carry a stable semantic cycle witness instead of a host traversal-dependent error string.

## 6. Proposed minimal ClayCode contract

No new surface syntax is justified by this run.

### Phase A — Link

Resolve module semantic identities and all structural type/function/symbol bindings. Structural SCCs are allowed to exist at this phase.

### Phase B — Derive initialization dependencies

From canonical typed IR, derive dependencies between **eager runtime values/initializers**, separately from broad import/link edges.

The dependency graph must be semantic, not merely textual import order.

### Phase C — Initialize

Repeatedly initialize dependency-ready eager nodes. When multiple nodes are ready, select by stable semantic identity so file enumeration, parser discovery and filesystem ordering do not mint runtime meaning.

### Phase D — Fail closed on true eager cycle

If eager nodes remain in SCCs, do not expose them as module-ready partial state by default. Emit a typed `ModuleInitCycleReceipt`, minimally binding:

- module graph semantic hash;
- eager dependency graph hash;
- sorted SCC module semantic IDs;
- sorted internal eager dependency edges;
- cycle receipt hash;
- failed lifecycle phase.

The exact schema is a candidate and should be simplified if production implementation preserves the invariants with fewer fields.

## 7. Counterhypotheses

### CH1 — Ban all cyclic imports

**Weakened, not refuted universally.** It is simple and Go demonstrates that it is practical. The proxy shows that it is more restrictive than necessary if ClayCode wants recursive structural composition while keeping eager initialization deterministic.

### CH2 — Expose partial/default initialized state

**Weakened.** The naive proxy produced order-sensitive outcomes. A carefully synchronized JVM-like design remains a valid alternative if a real ClayCode application requires recursive eager initialization.

### CH3 — Fixed source/import traversal order is enough

**Weakened.** It can make one implementation reproducible while still allowing arbitrary presentation order to become semantic. The proposed planner derives order from value dependencies and uses semantic identity only as a stable tie-break among simultaneously ready values.

### CH4 — Adopt full ECMAScript-style cyclic evaluation now

**NOT_SELECTED.** It proves feasibility of SCC-aware module systems, but current ClayCode evidence does not justify importing that complexity before a concrete application or FRANK counterexample requires it.

### CH5 — Add explicit `lazy`/phase syntax now

**NOT_SELECTED.** No current executable counterexample forces a language surface change.

## 8. Cross-branch feedback

- **ClayCode — NEW_CONSTRAINT:** distinguish structural linking and eager initialization in canonical IR/compiler/runtime; no syntax promotion.
- **Harness — NEW_CONSTRAINT:** production differential must perturb import/discovery order and test both harmless structural cycles and true eager cycles.
- **FRANK — NEW_CONSTRAINT:** FRANK recurrence/loop coupling is not itself a startup initialization dependency cycle. Functional recurrence must not be erased just to make a module DAG.
- **ClayGraph — NEW_CONSTRAINT:** represent structural link/import edges separately from eager init dependencies.
- **UnifiedDB — NEW_CONSTRAINT:** persisted module/runtime lineage should distinguish init plan/outcome/cycle receipt from semantic module identity and execution authority.
- **Hyperposition — NEW_HYPOTHESIS:** cyclic higher-order structural topology may admit an acyclic active/initialization projection; test beyond module startup.
- **GWT — NO_CHANGE:** no workspace mechanism change; startup ordering is merely a confound to control.
- **Emergenz — NO_CHANGE:** no emergence claim; initialization-order variation must not contaminate later causal measurements.
- **ClayResearch — NEW_CONSTRAINT:** deploy/runtime consolidation must preserve lifecycle-phase distinctions even when module/process boundaries collapse.

## 9. Evidence boundaries and negative results

This run does **not** establish:

- a production ClayCode module loader;
- a finished runtime ABI/package format;
- Ubuntu target correctness;
- a live FRANK result;
- CC-WP-07 completion;
- GENERAL_PURPOSE_GATE PASS;
- BASE PASS.

No target Ubuntu execution surface is exposed to this hosted worker. The production compiler/linker path is therefore the exact remaining discriminator, not more proxy simulation.

## 10. Next discriminating action — queued

Dynamic work created:

`WORK-SPAWN-CC-MODULE-INIT-PROD-DIFF-20260809`

It requires the local build/execution organ to implement the minimal linker/init planner in the production ClayCode pipeline and execute these cases on the Ubuntu developer target:

1. type/function-only cyclic modules link and execute;
2. structural cycle + acyclic eager values remains invariant under import/discovery-order perturbation;
3. true eager value cycle fails before module-ready exposure with stable semantic receipt;
4. parser, canonical IR, type/effect, compiler/runtime and generated target hashes are recorded;
5. no opaque host semantic escape or ambient authority is introduced.

Production failure may reopen the candidate or produce the executable counterexample needed for a language semantic change.

## 11. Durable artifacts and commits

- stochastic receipt: `66584622125112f670aefa618da68e493242295a`
- interconnect manifest: `6357048374d8049cfc3f26fc667f5a82607691f6`
- hypotheses/counterhypotheses: `28f39de4b64a0af0a83dea0233bb42f9316874ea`
- executable proxy: `ad6f71da5820578144e3c422c708bb79bf777589`
- execution receipt: `5a4ec9a06319d26bacdb5a575fa9b2d1468fe909`
- evidence manifest: `2947a7dfc60063c6c9b4e6476b4b142863f39bcd`
- branch feedback: `d7eeea47651a6da218f783e670df98afbec19761`
- queued production discriminator: `67d9af95bc459be7d5e29cb32970eb31cc058d49`

## Final decision

`RESEARCH_DELTA = COMMITTED`  
`SCIENTIFIC_PROMOTION = NONE`  
`CLAYCODE_SURFACE_CHANGE = NO`  
`MODULE_LINK_DIRECTION = STRUCTURAL_SCC_ALLOWED`  
`EAGER_INIT_DIRECTION = SEMANTIC_DEPENDENCY_DAG_OR_FAIL_CLOSED`  
`CYCLE_RECEIPT_DIRECTION = CANONICAL_SCC_MEMBERS_PLUS_INTERNAL_EDGES`  
`NEXT_DISCRIMINATOR = PRODUCTION_CLAYCODE_PLUS_UBUNTU_DIFFERENTIAL`  
`BASE_GATE = NOT_PASS`
