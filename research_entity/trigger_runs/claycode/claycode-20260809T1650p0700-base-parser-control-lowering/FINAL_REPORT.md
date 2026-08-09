# ClayCode Trigger Run — BASE parser/control/lowering convergence

Run: `claycode-20260809T1650p0700-base-parser-control-lowering`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**  
Gate advancement: **NONE**

## Executive result

This run found a concrete executable BASE-stage counterexample and converted it into a bounded implementation delta:

**The currently admitted ClayCode G9 V3 source is not self-conformant with its currently admitted `grammar.ebnf`.**

G9 V3 uses relational operators such as `>` and `>=` and uses an `if` control form inside its main cycle. The EBNF operator production does not include `<`, `>`, `<=`, `>=`, and the grammar has no `if_stmt` production.

This is exactly the kind of executable/compiler counterexample the BASE acceptance contract requires before changing language surface. The appropriate response is **not a broad ClayCode redesign**. A small candidate repair adds relational operators plus an explicit `if` control production, then the real parser/canonicalizer must prove semantic preservation.

A local synthetic executable probe used that smallest repair to parse/type-check a `LoopDynamicsReadout` fixture, lower it to a Python reference target and execute four regime cases. Result: **4/4 positive cases passed**, and a mutation referencing an undeclared field was rejected before lowering.

This does **not** pass BASE. It is not the target Ubuntu host, not E2B, not a full ClayCode compiler, and not native/WASM execution.

## Current-state grounding

Verified remote canonical state:
- entity version: `RAE-8.8`;
- revision: `2`;
- state hash: `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`;
- current program stage: `BASE_CLAYCODE_RELEASE`;
- current ClayCode release workspace: 14 work packages, all still OPEN at run start;
- current rule: `less change, more compile`;
- Frank v0.1 operational target: Ubuntu Linux developer system only.

The latest stack points to:
- `research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay`;
- `research_entity/claycode/g9/grammar.ebnf`;
- `research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay`.

The direct guessed path `research_entity/frank/FRANK_ARCHITECTURE.claycode.json` returned 404. Repository-wide private code search did not expose a reliable path-discovery result, so this run does **not** claim the artifact is globally absent. The latest completed FRANK architecture/organ-lineage Fusion report was used as the provisional current FRANK requirement source.

## Interconnected branch grounding

All current registered scientific branches were included. Deep inputs were taken for ClayCode, ClayGraph and UnifiedDB; current stack/mesh/fusion material covered Clayresearch, FRANK, GWT, Emergenz, Hyperposition and Harness.

Important current cross-branch constraints retained:
- recurrence != emergence;
- stable cycle != failure;
- low state delta + high unresolved pressure can indicate stagnation;
- ClayGraph activation != truth;
- UnifiedDB logical unification != physical monolith;
- model output != effect authority;
- FRANK may propose Harness changes but may not execute or delegate its own Harness mutation;
- shared project ancestry != independent replication.

See `INTERCONNECT_MANIFEST.json` and `BRANCH_FEEDBACK_MANIFEST.json`.

## Fusion 1 — internal evidence before outside confirmation

### ClayCode

Current G9 V3 already contains the right high-level semantic separation for the present stage:
- `Delta<T>` and incremental receipts;
- provenance expressions distinct from truth/authority;
- capability-bearing effects;
- dialect contracts;
- UnifiedDB cognitive views;
- ClayGraph deltas;
- GWT selection vs causal-credit axes;
- `EffectIntent` lowered by Needle;
- bounded equivalence search;
- reader/context-rent semantics;
- native cognition task boundary.

The current problem uncovered here is earlier and more concrete: the admitted source and admitted grammar disagree about executable syntax/control.

### ClayGraph

Current schema requires:
- graph/source epochs;
- versioned logical nodes/edges;
- activation/salience separate from authority;
- hyperrelations with typed member roles;
- projection receipts;
- selection receipts;
- receiver delivery/reconstruction/use/effect/outcome/reentry receipts;
- invalidation queues.

No new ClayCode semantic primitive is justified by this run. Existing G9 records, typed relations, delta/provenance and receipt semantics appear capable of representing this substrate. The next test is executable roundtrip/lowering, not language expansion.

### UnifiedDB

Current schema requires:
- state epochs and root hashes;
- semantic transactions with idempotency/base epoch/authority scope;
- transaction ops;
- semantic records with epistemic class/source/version status;
- query receipts;
- revisioned dynamic work specifications;
- capability/resource observations with freshness;
- execution truth classes.

Again, no new ClayCode semantic primitive is justified by this run. Existing G9 record/delta/provenance/effect semantics appear sufficient pending executable transaction/replay tests.

### FRANK / Harness

The latest architecture Fusion makes BASE the immediate bottleneck: ClayCode must express and execute the fused FRANK semantics before H1/H2/H3 advance. The newly distributed loop-of-loops hypothesis specifically asked ClayCode to represent recurrent state, timescale, budget, halt, dynamics, intervention and rollback semantics in executable typed IR.

The loop requirement therefore became the fixture for this run, but its project ancestry was not treated as independent evidence.

## Hypotheses and counterhypotheses

The detailed matrix is in `HYPOTHESIS_MATRIX.json`.

Strongest result:
- `H-CC-BASE-001` — **SUPPORTED_LOCAL_SYNTHETIC**: current G9 V3 and grammar are not self-conformant for sampled constructs.

Key open hypotheses:
- the minimal grammar repair can preserve canonical semantic identity;
- staged legality-checked lowering will expose escape hatches better than a direct transpiler;
- WASI 0.3 can cover a large fraction of ClayCode's typed host boundary without ambient authority;
- current G9 records are sufficient for ClayGraph/UnifiedDB semantics without new primitives;
- the current architecture grammar still needs a verified path to a genuinely general-purpose executable control core.

## External research — hypothesis-guided

Primary/authoritative technical sources used:
- MLIR Dialect Conversion documentation;
- WebAssembly Component Model WIT documentation;
- Component Model Canonical ABI documentation;
- WASI documentation;
- WASI 0.3 documentation.

### Result A — progressive lowering is a strong implementation analogue

MLIR's conversion framework explicitly separates:
- conversion target legality;
- rewrite patterns;
- optional type conversion;
- partial vs full conversion.

A full conversion succeeds only when illegal source operations have been completely legalized into the target representation. This is a strong engineering analogue for ClayCode's requirement that no semantic escape hatch survive lowering silently.

**ClayCode implication:** implement explicit legality sets per lowering stage and fail the build if unlowered semantic operations remain.

### Result B — WIT is an interface language, not a behavior language

WIT deliberately describes interfaces/worlds/types rather than program behavior. This is useful for ClayCode because ClayCode should remain the behavior/semantic IR while WIT can be a generated host-boundary contract.

**ClayCode implication:** do not replace ClayCode with WIT; generate WIT or equivalent ABI descriptions from typed ClayCode FFI/resource declarations.

### Result C — WASI capability model matches the authority boundary

Current WASI documentation specifies a capability-based sandbox: components start without ambient authority and only receive explicitly granted host access.

**ClayCode implication:** this independently supports preserving the current `model output != authority` and `EffectIntent -> external gateway` design rather than using unrestricted ambient host FFI.

### Result D — WASI 0.3 materially improves the async option

WASI 0.3, released June 11 2026, adds native Component Model async primitives including `async func`, `stream<T>` and `future<T>`.

**ClayCode implication:** BASE can test typed async/resource lowering against this ABI before inventing a bespoke scheduler semantics. Native Ubuntu lowering remains a competing candidate and must be benchmarked.

## Executable experiment

Artifact: `EXECUTABLE_RESEARCH_RECEIPT.json`

### Counterexamples from admitted G9 V3

1. `rule diff>0 => ADD_OR_STRENGTHEN`
   - `>` absent from current EBNF operator set.

2. `rule valid_generation requires count(distinct(classes))>=2 && count(executable)>=1`
   - `>=` absent from current EBNF operator set.

3. `if residual.effect { ... }`
   - no `if_stmt` exists in current grammar.

Control sample:
- `rule gwt.broadcast!=gwt.use`
- `!=` is present in the grammar.

### Candidate repair

Non-promoted candidate:
- add `<`, `>`, `<=`, `>=` to operator production;
- add `if_stmt = "if", expr, block`;
- require longest-match tokenization for multi-character operators.

Artifact: `GRAMMAR_REPAIR_CANDIDATE.ebnf`.

### LoopDynamicsReadout probe

Source artifact: `LOOP_DYNAMICS_PROBE.clay`.

Typed inputs:
- `state_delta`;
- `residual_pressure`;
- `instability`;
- `recurrence_delta`.

Observed classifications:
- diverging/overthinking;
- stalled;
- productive limit cycle;
- converging fixed point.

Execution:
- lowered to Python reference target;
- 4/4 expected classifications matched;
- undeclared-field mutation was rejected;
- no host capability/effect was granted by the program.

This demonstrates only the tested control/lowering slice.

## Negative result

`NR-CC-20260809-G9-SELF-CONFORMANCE`:

The current admitted G9 V3 textual source cannot be considered parser-freezable against the current admitted EBNF without either:
1. a grammar repair; or
2. evidence that a different canonical parser surface owns those constructs.

This is preserved as a negative result/counterexample, not silently repaired in canonical files.

## Goodman anti-echo result

See `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

Summary:
- recurrent control requirement: **REFINED** by an independent self-conformance executable test;
- typed capability/effect boundary: **SUPPORTED** by independent WASI capability design plus project failure history;
- typed resource/ABI boundary: **SUPPORTED** by Component Model/WIT/Canonical ABI;
- immediate bespoke async scheduler: **REFINED** downward because WASI 0.3 provides a viable typed async lowering target;
- WASI as first backend: **UNRESOLVED** until matched Ubuntu target-host comparison against native lowering.

## Architecture / BASE delta

### Change now justified

A candidate surface grammar repair is justified.

### Change not justified

No new GWT, ClayGraph, UnifiedDB, Hyperposition, provenance, capability or FRANK semantic primitive is justified by this run.

### Highest-value implementation sequence

1. Bind the existing universal-core evidence to the current G9 stack instead of reimplementing it blindly.
2. Build a real parser for the frozen G9 surface and make **the current G9 V3 spec itself a mandatory self-conformance fixture**.
3. Add deterministic canonical IR + semantic hash and prove the candidate syntax repair does not alter canonical meaning unexpectedly.
4. Add type/effect diagnostics including authority/resource identity.
5. Implement a reference evaluator.
6. Introduce explicit lowering legality stages: Clay AST -> typed Clay IR -> backend IR.
7. Run the same small CLI/HTTP/effect exemplar through two candidate Ubuntu paths:
   - native/LLVM or equivalent;
   - WASI 0.3 Component Model/Wasmtime.
8. Select the first backend using measured implementation cost, diagnostics, latency, binary/runtime cost and authority isolation, not ideology.
9. Compile current ClayGraph projection/selection receipt and UnifiedDB semantic transaction/replay fixtures.
10. Only after these pass, expand toward APP-01..APP-10 and the full FRANK handoff.

## Stage impact

`BASE_CLAYCODE_RELEASE`: remains **IN_PROGRESS**.  
`GENERAL_PURPOSE_GATE`: remains **NOT_PASS**.  
No release work package is marked complete by this research run.

The run reduces uncertainty around CC-WP-01/02/04/06 but does not satisfy them.

## Tool/runtime limits

- E2B was specified by protocol as preferred, but no E2B tool surface was exposed to this hosted worker. Local executable fallback was used and clearly labeled.
- SandboxAPI was not used.
- Andreas' exact Ubuntu developer host was not accessible from this worker.
- Repository-local `research_interconnect_preflight.py`, `research_room.py`, provider-router and Goodman checker were not executable because no repository checkout/runtime surface was exposed. Equivalent manifests/reviews were written from verified remote state; no claim is made that those scripts themselves ran.

## Required next discriminating test

**Real G9 self-conformance compiler test on the Ubuntu target:**

`current G9 V3 source -> real parser -> typed canonical IR -> semantic hash -> type/effect -> LoopDynamicsReadout lowering -> target execution receipt`

Then run a matched native-vs-WASI 0.3 CLI/HTTP/effect exemplar.

If the parser cannot ingest current G9 without more than the minimal repair, preserve each failure as a new executable counterexample before changing semantics.

## Provenance

Origin actor: `chatgpt-secondary`  
Provider/model: OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
External evidence class: authoritative technical documentation  
Executable evidence class: local synthetic Linux execution  
Canonical promotion: none
