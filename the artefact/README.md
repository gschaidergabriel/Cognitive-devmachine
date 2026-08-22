# the artefact — Multi-use Mini Entity + optional 0.5B ClayCode cognition

`the artefact/` is the canonical engineering workspace for the current owner-directed Mini Entity program in
`gschaidergabriel/clay-global-research-entity/main`.

The previous ClayVerse single-container endpoint is **legacy/donor scope** under the current owner directive. It must
not override the current program merely because older README/bootstrap material still exists.

Current authority:
1. `research_entity/global/MINI_ENTITY_CLAYCOG_05B_TRAINING_DIRECTIVE.md`;
2. `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md` as the base product law.

Current acceptance is **IN_PROGRESS**. Source, PR, fixture, provider, training, quantization or component success is not
whole Mini Entity acceptance.

## Product target

One portable persistent multi-use Mini Entity:

- one application-neutral and inference-neutral `.clay` pipeline executable;
- one SQLite MiniUnifiedDB owning durable state/configuration/history;
- `zero_blog` only as a fully replaceable shipped DB preset;
- runtime-selectable remote API, loopback local API, or direct local-model inference;
- one optional replaceable generic 0.5B ClayCode cognition checkpoint after empirical promotion.

There is exactly one product runtime entity. Research workers/swarm are temporary build/test organs only.

## Hard separation

The executable owns reusable mechanics only: evidence normalization, canonical run/state envelope, inference dispatch,
truth/secret gates, exactly-once consumption, generation/CAS fencing and atomic SQLite persistence.

MiniUnifiedDB/runtime configuration owns replaceable application semantics: entity/display name, role, task, goal,
personality, audience, language, system/application prompt, tool inventory, provider/model/runner configuration and
output contract.

The optional cognition weights own only generic cognition machinery. They must not contain a fixed name, job, persona,
audience, domain or application. Runtime configuration supplies those values.

## ClayCode cognition law

The 0.5B target emits ClayCode only and learns:

- GRF R0..R6 as typed reasoning space;
- Hyperposition for unresolved alternatives;
- typed `omega` structured-action candidates;
- explicit epistemic typing and provenance;
- architecture/authority boundaries;
- computed self/control state that is not confused with external evidence.

Core truth/effect invariants:

```text
UNKNOWN != ZERO != ERROR != MEASURED
REPORTED != MEASURED
MODEL_OUTPUT != CANONICAL_TRUTH
MODEL_OUTPUT != EFFECT_AUTHORITY
```

`R_next = F` is an executable admission invariant, not a claim that a neural network is mathematically infallible:

```text
omega candidate
-> grammar
-> types
-> schema
-> authority
-> generation
-> commit candidate OR reject/unresolved
```

A failed inference/gate/CAS consumes nothing. Unknown post-crash effects remain unknown and are never blindly replayed.

## Canonical SFT input — v2

`claycog-sft/v2` is the current paid-training candidate on `main`.

The original v1 corpus is retained only as historical/syntax evidence. It was rejected as paid-training input after a
deterministic leakage audit showed that its nominal 1,650 rows were heavily repeated and its validation split was not
independent enough to support generalization claims.

Current v2 manifest:

- 1,650 total examples;
- 1,485 train / 165 validation;
- 1,485 unique train rows;
- 165 unique validation rows;
- exact full-message cross-split overlap: 0;
- user-prompt cross-split overlap: 0;
- train SHA-256: `3c715588d1b040494be48228f165208e2f10202b3f125616741116b90cd21b93`;
- validation SHA-256: `ca284585ba66c532e7e19232edd7f6b5dc1c0969d15cbb9d5ce1cbc202e86f62`.

Exact uniqueness is necessary but not sufficient. Promotion still needs hardened ClayCode admission, semantic OOD,
matched untuned/larger-model comparisons and real runtime measurement.

## Together training boundary

Owner-authorized Together use is limited to this bounded 0.5B training campaign. Together is not product identity,
state authority, effect authority or a required inference provider.

Already canonical safety on `main` includes:

- exact local campaign fingerprint before billed create;
- duplicate-create fencing;
- atomic local create-intent ledger;
- zero automatic retry for the non-idempotent billed CREATE;
- `UNKNOWN_REMOTE_CREATE` on ambiguous transport outcome;
- no blind duplicate create/retry;
- USD 18 hard single-job gate inside the owner's EUR 20 campaign ceiling;
- secrets environment-only.

Provider/model compatibility is still an open external gate. Current public Together fine-tuning material observed on
2026-08-22 does not establish an admitted Qwen2/Qwen2.5 0.5B Full-FT template. A same-vendor 7B or Qwen3.5 0.8B model
must not be silently substituted and called the requested experiment. Open source-hardening/fusion work removes stale
template assumptions and keeps compatibility fail-closed until an exact compatible provider path is admitted.

No billed training job is currently credited as started.

## Promotion boundary

A training job or low loss is not promotion. The selected checkpoint must satisfy all of the following at the accepted
source/model identity:

1. strict ClayCode structural validity on held-out evaluation;
2. semantic task success, including exact typed omega arguments/schema and rejection of malformed actions;
3. identity/application neutrality under runtime profile changes and adversarial persona injections;
4. unresolved alternatives preserved rather than fluency-collapsed;
5. stale-generation and unknown-effect cases fail closed;
6. tuned 0.5B beats the untuned 0.5B base on the same executable benchmark;
7. compare with at least one larger general model before any micro-agent superiority claim;
8. quantize selected exact checkpoint to GGUF Q4_K_M;
9. measure actual peak process RSS `< 1 GiB` at context 2048;
10. integrate only through the existing generic `local_exec` inference path and preserve normal truth/CAS/persistence laws.

Model file size alone is not RAM acceptance.

## Native Mini Entity lane

Native Mini Entity 0.7 is an independent required lane. Current source/versioning/build provenance mechanisms exist,
but exact-current repeat build/runtime/fault-matrix acceptance remains open. Historical 0.6 fixture/local inference
receipts are bounded evidence only and cannot be inherited by 0.7 without source-bound execution.

Neither lane may borrow the other's acceptance:

```text
native 0.7 executable PASS != cognition checkpoint PASS
cognition checkpoint PASS != native 0.7 executable PASS
both component PASS != whole Mini Entity PASS
```

## Current convergence frontier

### A — native 0.7

Exact transitive-source-bound build -> compiler/dependency/ELF identity -> fixture/local_exec -> atomic study/output/event/
generation CAS fault matrix -> deterministic repeat build.

### B — generic 0.5B cognition

Canonical leakage-free SFT v2 -> close intrinsic/semantic validator gaps -> held-out OOD hardening -> exact provider/
template admission -> budget-gated full SFT -> tuned/base/larger-model benchmark -> Q4_K_M -> measured RSS -> existing
local_exec integration.

## Canonical paths

- owner cognition directive: `research_entity/global/MINI_ENTITY_CLAYCOG_05B_TRAINING_DIRECTIVE.md`;
- base Mini Entity directive: `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`;
- minimal boot: `research_entity/continuity/BOOTSTRAP_MINIMAL.json`;
- current program state: `research_entity/rooms/PROGRAM_STATE.json`;
- generic pipeline: `blogpost_entity/BLOGPOST_ENTITY.clay`;
- native implementation: `blogpost_entity/native/`;
- replaceable default preset: `blogpost_entity/presets/zero_blog.json`;
- cognition corpus/eval/training tooling: `blogpost_entity/mini_cognition/`;
- receipts: `blogpost_entity/receipts/`.

## Evidence warning

At this branch point, `PROGRAM_STATE.json` still contains stale v1 cognition fields even though `main` already contains
canonical SFT v2. Do not use those stale v1 fields to authorize training. Reconcile the cognition subsection without
deleting unrelated native/runtime evidence.

The governing question for every `go` is:

**What is the smallest high-information implementation or falsifier that moves this same neutral Mini Entity + generic
0.5B cognition toward empirical acceptance without creating a second identity, state authority, inference identity or
effect path?**
