# ClayCode BASE — 14-Blocker Burn-down

Run context: 2026-08-09 · actor `chatgpt-secondary` · canonical parent `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Decision

The “14 blockers” are the fourteen `CC-WP-*` packages in `research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json`. Their all-OPEN bookkeeping is stale as a picture of research/implementation progress, but it is still correct that **none may be declared PASS yet** under the BASE acceptance law: production ClayCode and Ubuntu developer-host receipts are mandatory.

This burn-down converts the fourteen broad OPEN labels into one executable closure chain. It deliberately does not promote proxy experiments to production acceptance.

Global constraints:

- Frank v0.1 target host is exclusively the Ubuntu Linux developer system.
- Android/mobile/edge/Windows/macOS/BSD work is not a BASE release blocker.
- Default policy is `less change, more compile`; core-language change requires an executable counterexample.
- Model output/proposals never grant execution authority.
- Hosted/container/proxy experiments are regression evidence, not Ubuntu BASE acceptance.

## 14-package closure map

### CC-WP-01 — SPEC-FREEZE

Current blocker class: `FUSION/FREEZE`, not lack of candidate semantics.

Evidence already available: G9 V3 semantic candidate, Dialect Registry V3, same-day parser/control/effect/identity/async/atomic/HTTP-DB research, and repeated negative result that no new FRANK-specific or HTTP/DB-specific core primitive has yet been forced.

Closure action: freeze a BASE semantic manifest that references the exact G9/Dialect/source hashes plus admitted refinements only. Every excluded candidate must be marked superseded/not-selected, not silently lost. Any remaining semantic dispute moves to an executable counterexample fixture instead of blocking the freeze indefinitely.

PASS evidence: frozen semantic manifest + source hashes + unresolved-counterexample list.

### CC-WP-02 — PARSER-CANON

Current blocker class: `ACTIVE_FRONTEND_REPAIR`.

Evidence already available: `D_LALR_GRAMMAR_REPAIR_CANDIDATE_V4.lark`; strict-LALR repair workflow; `tools/claycode_base_frontend_validation.py`; full-current-G9 + Dialect validation gate. The gate intentionally does not claim typed canonical-AST closure by itself.

Closure action: obtain strict construction receipt and full-corpus repaired-frontend receipt, then implement deterministic canonical AST/IR serialization and semantic-hash roundtrip. Reject reserved keyword misuse and preserve Unicode/newline boundaries deterministically.

PASS evidence: strict receipt + full-corpus receipt + canonical roundtrip/hash receipt with mutation discrimination.

### CC-WP-03 — IR-TYPES

Current blocker class: `PRODUCTION_INTEGRATION`.

Evidence already available: typed-control evaluator proxy; adaptive learner state candidate; semantic/state-version/trace identity separation; atomic CAS/ABA candidate and 200k ABA discriminator; no proxy counterexample forcing new surface syntax.

Closure action: materialize the admitted records/enums/collections/results/epochs/resources/semantic identities in the production canonical IR and checker. Integrate version/epoch-bound identity for semantic state where value equality is not identity.

PASS evidence: positive/negative typed IR corpus + canonical semantic identity receipts + real FRANK/adaptive-state fixtures accepted without untyped escape hatch.

### CC-WP-04 — TYPE-EFFECT

Current blocker class: `EXECUTABLE_CHECKER`.

Evidence already available: control/effect research, effect-authority proxy with 100k broker fuzz cases and deliberate ambient/structural-forgery negative controls. The central implementation constraint is that descriptive capability data is not bearer possession.

Closure action: implement static type/effect summaries plus runtime authority separation. Invalid effect/control/capability combinations need precise diagnostics. Foreign lowering must satisfy authority closure rather than inherit ambient OS authority.

PASS evidence: checker negative corpus + effect-summary stability + forged/stale/revoked capability rejection + APP-08 authority-closure receipt.

### CC-WP-05 — EVALUATOR

Current blocker class: `PRODUCTION_EVALUATOR`.

Evidence already available: FRANK recurrence typed-control proxy produced 0 mismatches over 200,000 randomized inputs; generated lowering also 0 mismatches; mutation variants were detected.

Closure action: move that ordinary typed-control subset into the production evaluator and extend to the frozen BASE core. Compare production evaluator against frozen reference fixtures.

PASS evidence: deterministic evaluator receipt, replay/roundtrip receipt and zero unexplained differential mismatches across mandatory core fixtures.

### CC-WP-06 — COMPILER-LOWERING

Current blocker class: `PRODUCTION_LOWERING_CHAIN`.

Evidence already available: evaluator-to-generated-Python and native GCC shadows support deterministic lowering; HTTP+SQLite semantic-spec proxy passed 17/17 plus 4/4 mutation detection. Neither was the real compiler.

Closure action: implement one real source -> parser -> canonical IR -> type/effect -> lowering -> backend chain on Ubuntu first. Bind translation receipts to source semantic hash, effect manifest, adapter ABI/set, capability context, generated target hash, runtime identity and outcome.

PASS evidence: reproducible native and/or WASM/WASI Ubuntu build/run receipt plus differential translation validation.

### CC-WP-07 — RUNTIME-ABI-FFI

Current blocker class: `RUNTIME_AUTHORITY/RESOURCE_REALIZATION`.

Evidence already available: effect-authority experiment falsifies ambient backend and structural bearer-token validation; HTTP/SQLite research supports typed adapter-first architecture; async/resource research requires explicit semantic resource identity.

Closure action: implement Ubuntu runtime ABI and typed FFI with opaque/sealed host capability handles, explicit resource identity/lifetime, module/package identity, and reserve/commit/rollback receipts. Descriptive serialized capability records must be non-authoritative.

PASS evidence: ABI/FFI conformance receipts, lifecycle/restart/replay tests and foreign-code authority-closure tests.

### CC-WP-08 — STDLIB-SDK

Current blocker class: `PRODUCTION_ADAPTERS`.

Evidence already available: HTTP+SQLite vertical proxy passed 17/17 CRUD/validation/transaction tests and all four semantic mutations were detected. This supports adapters before syntax changes.

Closure action: implement the minimum Ubuntu stdlib/SDK needed by the acceptance applications: collections, files/process, HTTP/network, SQLite/database transaction adapter, async/concurrency, UI/event-loop adapter and numerical/backend interop.

PASS evidence: stdlib API/ABI hashes plus application-linked execution receipts; no untyped hidden authority escape.

### CC-WP-09 — CONCURRENCY-MEMORY

Current blocker class: `PRODUCTION_ATOMICS/ASYNC`.

Evidence already available: async replay research; atomic CAS/ABA work showed value-only stale acceptance in 200000/200000 constructed ABA histories and version-bound stale acceptance in 0/200000; cross-backend exact semantic counters held while physical retry counts varied.

Closure action: implement errors, task/replay identity, atomics/CAS and explicit memory-order contract sufficient for BASE. Physical retry attempts belong to execution trace unless explicitly program-observable; semantic state uses epoch/version identity where required.

PASS evidence: production Ubuntu ABA/order/retry differential, invalid failure-order rejection, race/replay tests and semantic-vs-execution hash receipt.

### CC-WP-10 — GENERAL-APP-SUITE

Current blocker class: `TARGET_HOST_EXECUTION`.

Current workspace still records zero production applications passed. Proxy slices must not populate that list.

Closure action: drive the production toolchain through all required apps: CLI, HTTP website, DB service, concurrent service, GUI/interactive app, compiler/tool, GPU/ML/numerical backend, sandboxed system effect, FRANK component, then full FRANK handoff fixture. Reuse the HTTP/SQLite and authority negative controls as mandatory regressions.

PASS evidence: one reproducible Ubuntu receipt per required application with exact source/compiler/runtime hashes and zero unexplained failures.

### CC-WP-11 — FUZZ-CONFORMANCE

Current blocker class: `PRODUCTION-SURFACE COVERAGE`.

Evidence already available: same-day proxy property/differential/mutation experiments at 100k–200k scale for recurrence, authority, atomics and HTTP/DB. They are useful oracle seeds, not compiler conformance.

Closure action: port those discriminators into the production parser/IR/checker/evaluator/lowering/runtime tests; add parser roundtrip, semantic-hash mutation, invalid-program generation, FFI fault injection and application differential tests.

PASS evidence: unit/property/fuzz/mutation/roundtrip/conformance summary with seeds/hashes and no unexplained P0/P1 failures.

### CC-WP-12 — CORPUS-HELDOUT

Current blocker class: `MISSING RELEASE CORPUS ARTIFACT`.

Closure action: generate positive and negative examples from frozen semantics and real checker diagnostics; freeze train/validation/test provenance; add leak checks and held-out executable fixtures. Include effect-authority, ABA, mixed-epoch, parser-keyword/Unicode/newline, rollback and adaptive visual-state cases.

PASS evidence: corpus manifest, generator hash, split/provenance hashes, leak audit and held-out execution receipt.

### CC-WP-13 — HARNESS-HANDOFF

Current blocker class: `PRODUCTION FRANK DIFFERENTIAL`.

Evidence already available: FRANK loop slice can be represented by ordinary typed control in proxy tests; Harness research provides state/authority/Needle/adaptive boundaries; no new FRANK-specific primitive was forced by the tested loop slice.

Closure action: compile at least one frozen real FRANK subsystem through the production pipeline, then expand to the H1 differential fixture. No semantic escape hatch, ambient authority or ad-hoc Python-only bypass may count.

PASS evidence: frozen FRANK source/IR/backend receipts, differential oracle and handoff manifest consumed by H2/H3.

### CC-WP-14 — BASE-AUDIT

Current blocker class: `DEPENDENT FINAL GATE`.

Closure action: after WP-01..13 evidence exists, generate `CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json`, verify hashes, enumerate application receipts and remaining counterexamples, rerun the acceptance contract and decide PASS/NOT_PASS. No package is promoted merely because research agrees.

PASS evidence: validated manifest + all mandatory Ubuntu app receipts + unresolved P0/P1 count zero + explicit GENERAL_PURPOSE_GATE/CLAYCODE_RELEASE_GATE verdict.

## Critical path

The closure order is deliberately narrow:

`WP01 freeze -> WP02 parser/canon -> WP03 IR/types -> WP04 type/effect -> WP05 evaluator -> WP06 lowering -> WP07 runtime/FFI -> WP08 stdlib -> WP09 concurrency -> WP10 app suite -> WP11 conformance -> WP12 heldout -> WP13 FRANK handoff -> WP14 audit`.

Parallelization is allowed only where artifacts are immutable or write scopes do not race. The parser repair worker must not be race-edited while its strict/full-corpus receipts are pending.

## Immediate repo decisions

1. Keep all fourteen package gate statuses non-PASS until their acceptance evidence exists.
2. Treat the repaired D grammar/full-corpus workflow as the active WP02 frontend path.
3. Reuse existing same-day executable research as regression oracles rather than inventing new semantics.
4. Route production/Ubuntu-only work to the local build organ with repository checkout and target-host execution.
5. On every result, update this burn-down and the release workspace from receipts, not narrative confidence.

## Evidence anchors

- `research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json`
- `research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay`
- `research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay`
- `research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V4.lark`
- `tools/claycode_strict_lalr_probe.py`
- `tools/claycode_base_frontend_validation.py`
- commit `f0a52b2719b8fb014ed4c1c51d54f062325cb5da` — full-corpus repaired frontend gate
- commit `3a0d3bb6c28eb94e7686e0d4d32cf9176a1a6499` — effect intent vs execution authority
- commit `02225987d906ae2550b4525eaa0de13811906038` — FRANK loop evaluator/lowering discriminator
- commit `d27e1a1e24d685aad800a76185ee73fda9eb6dd6` — atomic CAS/ABA + Ubuntu follow-up
- commit `e183455d5889881b9be016eb9272c4b4216a9238` — HTTP+SQLite vertical proxy + Ubuntu follow-up

Final state of this document: `BLOCKER_SCOPE_RESOLVED_TO_EXECUTABLE_CLOSURE_PLAN`; BASE gate remains `NOT_PASS` until receipts satisfy the acceptance law.
