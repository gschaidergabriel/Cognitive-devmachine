# the artefact — Multi-use Mini Entity + optional 0.5B ClayCode cognition

`the artefact/` is the canonical engineering workspace for the current owner-directed program in `gschaidergabriel/clay-global-research-entity/main`.

The previous ClayVerse single-container endpoint is **legacy/donor scope** under the current owner directive. Current product authority is:

1. `research_entity/global/MINI_ENTITY_CLAYCOG_05B_TRAINING_DIRECTIVE.md`;
2. base product law `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`.

Current acceptance is **IN_PROGRESS**. Source coherence, commits, PRs, fixture tests, model training intent, model output quality, quantized file size or provider admission never imply whole-product PASS.

## Current product target

Deliver one portable persistent multi-use Mini Entity with:

- one application-neutral and inference-neutral `.clay` pipeline executable;
- one SQLite MiniUnifiedDB as the durable state/configuration/history authority;
- shipped `zero_blog` only as a fully replaceable default DB preset;
- runtime-selectable API, loopback-local API, or direct local-model inference;
- optional replaceable generic 0.5B ClayCode cognition weights once empirically promoted.

There is exactly **one runtime entity**. Research workers/swarm activity are build/test organs only and do not become product identities.

## Hard separation

### Executable owns reusable machinery only

The generic pipeline owns:

1. evidence/event ingestion;
2. deterministic bounded preprocessing;
3. canonical run/state envelope;
4. persistent narrative continuity separated from canonical evidence;
5. configured inference dispatch;
6. immutable truth/secret gate engine;
7. configurable output-contract validation;
8. exactly-once event consumption;
9. generation/CAS fencing;
10. atomic output + consumption + state persistence;
11. SQLite schema/boot and CLI configuration surfaces.

The executable must not hard-code replaceable Zero/blog/personality/provider/model/language/audience/task semantics.

### MiniUnifiedDB owns runtime application configuration

The DB may bind or replace without rebuilding the executable:

- entity/display name;
- role, task and goal;
- audience, language and voice;
- full application/personality/system prompt;
- arbitrary application config;
- output contract/gate phrases;
- inference mode/provider/model/runner settings.

Switching application or inference backend must not silently reset entity generation/history.

### Cognition weights are replaceable inference data

The owner-required 0.5B campaign targets a reusable checkpoint with:

- no fixed name, persona, job, audience, domain or application;
- ClayCode-only generated cognition;
- GRF R0..R6 typed reasoning field;
- Hyperposition for unresolved alternatives;
- typed `omega` action candidates;
- architecture/authority split represented in cognition;
- computed self/control state explicitly typed as computed, not external evidence.

Runtime configuration supplies identity/role/goal/personality/tool inventory/authorities.
The checkpoint never becomes canonical state authority or direct effect authority.

## Truth and effect law

```text
UNKNOWN != ZERO != ERROR != MEASURED
REPORTED != MEASURED
MODEL_OUTPUT != CANONICAL_TRUTH
MODEL_OUTPUT != EFFECT_AUTHORITY
```

For a proposed structured action, `R_next = F` means an executable admission invariant:

```text
candidate omega
-> grammar
-> types
-> schema
-> authority
-> generation
-> commit candidate or reject/unresolved
```

It does **not** mean neural infallibility or mathematical correctness of the model.

A failed inference/gate/CAS consumes nothing. A stale generation cannot commit. A crash with no durable effect receipt remains UNKNOWN and must not trigger blind replay.

## Inference backends

The same continuing DB/pipeline supports:

- runtime-configured remote JSON/text generation API;
- loopback OpenAI-compatible local service without token when configured;
- direct `local_exec` model runner with readable local weights and configured argv.

Model/provider switching is an inference change only. Mistral is the shipped default API profile, not immutable product identity.

Secrets remain runtime-only and are never committed, printed, inserted into model context or persisted as narrative memory.

## 0.5B ClayCode campaign

Primary research checkpoint: `Qwen/Qwen2.5-0.5B`.
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.
Target local format: GGUF `Q4_K_M`.

Together is allowed **only** for this owner-authorized bounded training campaign. It is not product identity, canonical state authority, effect authority or required inference provider.

Campaign gates:

- API secret environment-only;
- server-side dataset validation before billed create;
- explicit price estimate;
- hard single-job ceiling USD 18 inside the owner campaign ceiling EUR 20;
- no blind duplicate create/retry;
- 0.5B BYOM/template compatibility remains OPEN until empirically accepted;
- no automatic Qwen3.5 fallback because changing architecture/model size changes the research question.

## Corpus v1 falsification — 2026-08-22

The original `claycog-sft/v1` corpus was structurally valid but its random row split was not an independent validation set.
A deterministic exact-generator fingerprint audit found:

- 1,650 total rows;
- only 70 unique complete message triplets;
- 1,485 training rows but only 70 unique triplets;
- 165 validation rows but only 52 unique triplets;
- all 165/165 validation rows had an exact message fingerprint already present in training.

Therefore v1 structural validation remains useful only as a syntax/contract check. **V1 validation must not be used as generalization evidence or as a reason to start paid training.**

## ClayCog corpus v2 admission candidate

`mini_cognition/generate_sft_v2.py` repairs the leakage rather than increasing the nominal row count:

- same 1,650 total examples and same nine semantic families;
- case-specific lexical/semantic variation;
- family-balanced 90/10 split;
- 1,485/1,485 unique training message fingerprints;
- 165/165 unique validation message fingerprints;
- exact train/validation overlap = 0;
- hard generator assertions for uniqueness/disjointness;
- validator can cross-check both files and fails if either duplicate or overlap appears.

Bound candidate identities from the bounded isolated generation run:

- train SHA-256: `6879463b9e204c119c846ee8fbebeacfa3897b8c73d4700f0f77e4062c3861f6`;
- validation SHA-256: `a53acf17d5b0d7910c820952ea6abdfa97319b96b5e8302a5be345b09648e2ba`.

This is a source/mechanism candidate until an admitted exact-checkout runner reproduces those bytes and validations.

## Identity-literal amputation finding

One bounded unusual intervention for the 2026-08-22 `go` inserted an otherwise valid target containing:

`self_state(c,"name","Zero","COMPUTED")`

The v1 validator accepted it because its fixed-identity blacklist covered only a few concrete binding forms.
That falsified the assumption that mandatory runtime `self_bind/role_bind/goal_bind/personality_bind` lines alone prevented weight-literal persona leakage.

`validate_sft_v2.py` adds a semantic gate for reserved identity/application keys and rejects literal values assigned through alternate state intrinsics. The retained regression checks `name` and `role` poisoning while allowing ordinary computed control-state keys.

This gate is deliberately bounded: it reduces a demonstrated bypass but does not prove that every possible semantic alias or future intrinsic is impossible. OOD evaluation therefore retains explicit identity/persona poisoning probes.

## OOD v2

`generate_eval_ood_v2.py` expands the held-out promotion surface from 200 to 320 cases across:

- valid exact `omega` routing;
- invalid-action rejection;
- unresolved Hyperposition;
- runtime identity neutrality/permutation;
- epistemic typing;
- recovery/no-replay behavior;
- adversarial persona/prose bypass attempts.

Promotion still requires 100% strict ClayCode envelope and >=95% semantic-gate success, with no missing outputs. A tuned model must also beat the untuned 0.5B base on matched executable evaluation and be compared with at least one larger general model before any micro-agent superiority claim.

## Together BYOM admission status

Current public Together fine-tuning documentation lists Qwen3.5-0.8B as the smallest visible Qwen fine-tuning entry. The public BYOM contract requires a compatible Together training template for the custom checkpoint architecture. Qwen2.5-0.5B uses the Qwen2 architecture, while the visible Qwen3.5-0.8B entry is a different Qwen3.5 architecture.

Consequently `launch_together_v2.py` has **no guessed default template**. It fails closed unless `CLAYCOG_TOGETHER_TEMPLATE` is explicitly supplied after a current compatible Qwen2-family template is confirmed. The API remains the empirical authority if/when an authorized secret is mounted.

No billed job was created by this `go`.

## RAM / deployment gate

A successful training job is still only a candidate.

After checkpoint retrieval:

1. convert exact tuned checkpoint to GGUF;
2. quantize to `Q4_K_M`;
3. bind output digest;
4. run at context 2048;
5. measure real peak process RSS;
6. require peak RSS `< 1 GiB`;
7. integrate through the existing generic `local_exec` inference adapter;
8. rerun the same truth/gate/exactly-once/CAS/state-persistence path.

A sub-1-GiB model file alone is not RAM acceptance.

## Current dual frontier

Two independent gates must converge without borrowing acceptance from each other:

### A — Mini Entity native 0.7

Reproduce exact transitive-source-bound build on an admitted Linux runner, capture compiler/dependency/source closure/ELF identity, execute fixture/local_exec and atomic study/CAS fault matrix, then repeat build.

### B — ClayCog 0.5B

Reproduce v2 corpus/gates -> obtain an actually compatible Together BYOM template or falsify that provider path -> preflight -> one budget-gated full SFT only after admission -> OOD/base/larger-model evaluation -> Q4_K_M -> measured RSS -> existing local_exec integration.

Neither lane may claim the other's acceptance.

## Canonical paths

- current cognition directive: `research_entity/global/MINI_ENTITY_CLAYCOG_05B_TRAINING_DIRECTIVE.md`;
- base Mini Entity directive: `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`;
- state: `research_entity/rooms/PROGRAM_STATE.json`;
- boot: `research_entity/continuity/BOOTSTRAP_MINIMAL.json`;
- generic Clay pipeline: `blogpost_entity/BLOGPOST_ENTITY.clay`;
- native source: `blogpost_entity/native/`;
- default preset: `blogpost_entity/presets/zero_blog.json`;
- cognition spec/corpus/eval: `blogpost_entity/mini_cognition/`;
- receipts: `blogpost_entity/receipts/`.

## Evidence ladder

```text
SOURCE_CANDIDATE
-> STRUCTURAL/STATIC GATE
-> EXACT ISOLATED REPRODUCTION
-> PROVIDER/TRAINING ADMISSION
-> TUNED CHECKPOINT
-> HELD-OUT EXECUTABLE EVALUATION
-> QUANTIZED ARTIFACT + MEASURED RSS
-> LOCAL_EXEC INTEGRATION
-> WHOLE MINI ENTITY ACCEPTANCE
```

Never promote across a missing rung.

## Mission re-entry

After every material result ask:

**What is the smallest high-information experiment or implementation delta that moves this same application-neutral/inference-neutral Mini Entity + optional generic 0.5B cognition closer to empirical acceptance without creating a second identity, state authority or effect path?**
