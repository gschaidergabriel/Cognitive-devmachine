# Reserved Trigger: `claycode`

Research ClayCode as the internal semantic language/IR for Synthetic Clay and as the primary architecture/implementation IR of the next FRANK architecture. Use the Master Research Trigger Protocol, Interconnected Research Mesh Protocol and Goodman Anti-Echo Protocol.

## Mandatory foundation hierarchy

Every `claycode` run MUST load all registered scientific branches. Priority is:

`frank -> clay -> claygraph -> gwt -> hyperposition -> emergenz -> claycode history`

### FRANK — primary target feedback

Load newest completed and in-progress FRANK research, including `FRANK_ARCHITECTURE.claycode.json`, `CLAYCODE_ARCHITECTURE_MAPPING.md`, experiments, negative results, runtime/code observations, Topic Packets and micro-packets. If no FRANK ClayCode architecture artifact exists yet, record that absence and use the newest FRANK report/architecture contract as provisional requirements; never fabricate it.

### ClayGraph — mandatory deep substrate input

Every ClayCode run MUST deeply ingest the newest ClayGraph completed and in-progress research, including where present:

- accepted/current ClayGraph and newest candidate graph;
- `CLAYGRAPH_SCHEMA.claycode.json`;
- graph evolution decisions and parent→candidate deltas;
- `SELF_USE_BENCHMARK.json` and retrieval/latency/token measurements;
- `DATABASE_INVENTORY.json` and `MIGRATION_PLAN.json`;
- `FRANK_CLAYGRAPH_FEEDBACK.json`;
- graph activation/assembly, temporal, provenance, conflict/unknown/revoked and relation semantics;
- negative results showing where graph consolidation or spreading activation fails.

ClayGraph is not treated as a generic external database. ClayCode must research whether its semantic IR can faithfully represent and operate the graph substrate: typed nodes/relations, n-ary/higher-order relations, activation state, assemblies, temporal/version semantics, evidence ancestry, replay, migration transitions, isolation boundaries and graph mutation rules.

If ClayGraph exposes a missing ClayCode primitive, unsafe authority assumption, ambiguous identity rule or transition-closure gap, ClayCode must generate a falsifiable hypothesis and test whether the language should be changed. If ClayCode evidence refutes a ClayGraph assumption, write that contradiction back to ClayGraph rather than conforming the language to a bad graph design.

Run `tools/research_interconnect_preflight.py --trigger claycode --run-id <run_id>` and materialize `INTERCONNECT_MANIFEST.json` before Fusion 1. The preflight must show ClayGraph as a deep input and all seven registered scientific branches.

## Mandatory executable ClayCode loop

ClayCode is not researched only as prose or JSON architecture. Every substantive `claycode` run must attempt to turn at least one current language hypothesis into an executable artifact: parser, canonicalizer, type/effect checker, compiler/lowering pass, interpreter/VM fragment, roundtrip checker, fuzz harness, or generated host-language program.

Capability sources:
- `research_entity/global/E2B_RESEARCH_CAPABILITY.json`
- `research_entity/global/SANDBOXAPI_RESEARCH_CAPABILITY.json`

`e2b_sandbox` is currently `RUNTIME_VERIFIED` and is the **preferred external execution surface** for ClayCode compiler/runtime experiments. `sandboxapi_sandbox` remains an intended independent secondary backend but is currently `BLOCKED_NOT_SUBSCRIBED`; do not count it as runtime evidence until its own successful execution receipt exists.

The run should, where scientifically relevant:

1. write real ClayCode source examples and counterexamples;
2. parse them into the current canonical IR;
3. validate types, semantic classes, basis/closure and authority rules appropriate to the tested candidate;
4. lower or compile them into an executable host representation;
5. execute the generated program in E2B, preferably as a separate process from the compiler itself;
6. run positive, negative, mutation/fuzz and semantic-preservation tests;
7. use local/Judge0 differential replication when it adds independent information;
8. capture compile errors, runtime errors, bridge/tooling failures, counterexamples, timings and repair iterations;
9. turn those observations into hypotheses, negative results, compiler revisions and cross-branch feedback.

Every nontrivial executable experiment must emit an `EXECUTABLE_RESEARCH_RECEIPT.json` (or an array/ledger of equivalent receipts) containing at least:

- ClayCode source hash and candidate/compiler version;
- canonical IR/semantic hash where applicable;
- provenance/contract-instance hash where applicable;
- lowering/compiler target and generated-code hash;
- sandbox provider/runtime/language identity;
- test/fuzz corpus identity;
- stdout/stderr/exit status and available time/memory data;
- expected-vs-observed semantic result;
- failure/counterexample classification;
- repair/change applied, if any;
- affected hypothesis/negative-result IDs;
- whether the learning changed ClayCode, FRANK, ClayGraph, GWT, Hyperposition, Emergenz or Clay.

A successful compilation is not automatically scientific support: differential/reference/oracle tests must establish which semantic property was preserved. A compiler/typechecker accepting a program does not prove the source intent was adequate; CC-RC1.5 intent-adequacy boundaries remain separate.

### Executable identity rule learned from E2B

The first real E2B ClayCode compiler experiment exposed that ordering and duplicate set-like constraints changed one monolithic contract hash. CC-Lab v0.2 therefore separates:

- `semantic_hash` — canonical executable meaning, insensitive to ordering/duplication for fields explicitly typed as sets;
- `contract_hash` — exact provenance-bound contract instance, including proposal/adequacy ancestry.

Do not collapse these identities. If future ClayCode introduces ordered/weighted preferences or ordered effects, they require an explicitly ordered type and must not be normalized as sets.

### Sandbox fallback and replication

If E2B is unavailable, quota-limited or fails, record the exact blocker and automatically fall back to local sandbox and/or Judge0. The run may proceed, but it must not claim E2B evidence. If SandboxAPI becomes subscribed and runtime-verified, use it as an independent second backend for target-sensitive compiler/runtime replication, especially multi-language lowering tests.

Stateful sessions/package installation may be used only when the active provider/plan actually exposes them. Never infer session persistence from a one-shot execution API.

The long-term self-hosting research path is:

`host bootstrap compiler -> executable ClayCode parser/type/effect system -> ClayCode lowering/interpreter -> ClayGraph/FRANK runtime components generated from Clay semantics -> progressively more of the compiler/runtime specified in ClayCode`

but self-hosting never grants self-modification or effect authority by itself.

## Mandatory Goodman anti-echo review

FRANK and ClayCode are a feedback pair. Their agreement is not independent evidence.

For every FRANK-derived assumption materially changing ClayCode semantics, representation, runtime, compiler, gateway, state model or self-hosting architecture, apply `research_entity/global/GOODMAN_ANTI_ECHO_PROTOCOL.md` and write `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

Each relevant assumption receives one verdict:

- `SUPPORTED` — independently supported;
- `REFINED` — partially supported, scope/semantics changed;
- `REFUTED` — counterevidence wins, preserve negative/supersession evidence;
- `UNRESOLVED` — insufficient independent evidence, keep open.

Before `SUPPORTED` or `REFINED`: collapse shared ancestry, seek independent evidence or a genuinely new discriminating experiment, state a counterhypothesis/falsifier, run an adversarial check and preserve evidence class. ClayGraph reuse of the same FRANK/Clay evidence also counts as shared ancestry, not replication.

## Bidirectional integration

ClayCode must test both FRANK and ClayGraph demands against the language/runtime design:

- FRANK missing primitive → research/add only if independently justified;
- ClayGraph missing primitive/identity/relation/activation semantics → research/add only if justified;
- invalid FRANK or ClayGraph assumption → refute/narrow and write back to the mesh;
- safer/more efficient ClayCode representation/transition model → write delta so next FRANK and ClayGraph runs reconsider their architectures.

The result is a falsifiable co-evolution loop, not a consensus loop.

## Core research questions

- Can ClayCode faithfully represent the newest FRANK architecture and newest ClayGraph substrate?
- Can the same semantic IR express exact canonical state and bounded associative activation without conflating activation with truth?
- Which graph semantics belong in canonical IR versus reader-specific projection/wire syntax?
- Can Clay-written runtimes interpret/transform ClayCode without circular ambiguity or hidden authority escalation?
- What remains deterministic outside the model: parser, schema, canonicalization, capability checks, commit gateway, rollback and receipts?
- Can a Qwen-class 4B model operate on the internal state language rather than imitate surface syntax?

## Required research dimensions

- FRANK architecture coverage: modules/organs, state contracts, transitions, dependencies, invariants, causal/GWT links and authority boundaries;
- ClayGraph coverage: typed entity/relation identity, temporal/provenance/conflict semantics, activation/assembly state, graph mutation, migration and replay;
- Goodman ancestry/independence analysis;
- self-description/reflection without representation=authority confusion;
- canonical AST/IR and deterministic roundtrip;
- state/version/provenance/unknown/conflict/revoked semantics;
- transition closure, scoped freshness and trusted dependency/effect derivation;
- activation/assembly/workspace primitives;
- outcome/re-entry/credit primitives;
- external capability/commit boundary;
- parser/validator/compiler fuzzing;
- executable compiler/interpreter/runtime artifacts and their receipts;
- context/token/repair cost versus JSON/key=value/natural-language baselines;
- reader-specific projections and live-reader break-even;
- Qwen-4B simulation/live tests, explicitly labeled `simulation_only` when no target model is run;
- bootstrapping/self-hosting path: host runtime -> ClayCode runtime -> ClayGraph/Synthetic-Clay/FRANK system.

## Required outputs and completion gate

Every completed ClayCode run must include at minimum:

- `INTERCONNECT_MANIFEST.json` covering all seven branches;
- `TOOL_EXECUTION_MANIFEST.json`;
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`;
- hypotheses/experiments/negative results appropriate to the run;
- executable-research receipt(s) when an executable experiment was attempted;
- a final report section explicitly naming the ClayGraph findings that changed, supported or challenged ClayCode.

Before completion or strong promotion run:

`python tools/goodman_filter_check.py validate-run research_entity/trigger_runs/claycode/<run_id>`

A ClayCode run that omits the current ClayGraph substrate input is incomplete even if its FRANK Goodman review passes.

A language candidate is not promoted because it looks compact, alien, agrees with FRANK or fits ClayGraph. Promotion requires semantic preservation, bounded repair cost, target-reader performance, safety/authority invariants and non-circular evidential support.

Write the final report to `research_entity/trigger_runs/claycode/<run_id>/FINAL_REPORT.md` and finish with the mandatory status footer.
