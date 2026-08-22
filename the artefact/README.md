# the artefact — Multi-use Mini Entity pipeline all-in-one

`the artefact/` is the canonical product workspace for the current owner-directed Mini Entity program in `gschaidergabriel/clay-global-research-entity/main`.

The previous ClayVerse single-container endpoint is superseded as the active product target. Historical ClayVerse/EntityOS material remains bounded implementation/research evidence only where it helps the current product; it is not allowed to override the current Mini Entity owner directives.

Current authority:

- `research_entity/global/MINI_ENTITY_CLAYCOG_05B_TRAINING_DIRECTIVE.md`
- `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`
- `research_entity/rooms/PROGRAM_STATE.json`

The product is **IN_PROGRESS**. Source presence, a green component test, a generated corpus, a fine-tuning job, a quantized file, or an inference demo never implies whole-product acceptance.

## Product target

The release shape is deliberately small and replaceable:

1. one application-neutral and inference-neutral native `.clay` pipeline executable (`mini_entity.clay`);
2. one SQLite MiniUnifiedDB (`mini_entity.db`) as the persistent state/config/evidence authority;
3. one optional replaceable generic **0.5B ClayCode cognition checkpoint**.

`zero_blog` is only the fully replaceable shipped preset. Zero, blogging, German/English presentation text, personality, provider, model name, API choice, local runner choice, and application-specific semantics are runtime configuration/data — never executable or checkpoint identity.

## Architecture law

### Native executable

The executable owns only generic machinery:

- evidence/source preprocessing;
- canonical run/state envelope;
- generic inference dispatch;
- immutable truth/secret/admission gates;
- exactly-once source consumption;
- generation CAS;
- atomic SQLite persistence;
- deterministic effect/state authority boundaries.

If a replaceable application, personality, provider, model, prompt, presentation label, or tool description can live in runtime configuration, hard-coding it into the ELF is a regression.

### MiniUnifiedDB

SQLite owns continuing state and runtime configuration. Switching application preset, inference backend, local weights, provider, prompt, role, goal or personality must not fork or reset entity continuity.

Epistemic law remains:

```text
UNKNOWN != ZERO != ERROR != MEASURED
REPORTED != MEASURED
MODEL_OUTPUT != CANONICAL_TRUTH
MODEL_PROPOSAL != EFFECT_AUTHORITY
```

### Optional 0.5B cognition

The cognition checkpoint is replaceable inference data, not canonical identity/state/effect authority. The current owner-required primary base is `Qwen/Qwen2.5-0.5B`; `Qwen/Qwen2.5-0.5B-Instruct` is the secondary ablation.

The training target teaches generic cognition machinery rather than a fixed persona/job:

- ClayCode-only generated cognition;
- GRF R0..R6 as typed reasoning field;
- Hyperposition for unresolved alternatives;
- typed `omega` function/tool/API candidates;
- architecture-use priors and authority boundaries;
- computed semantic self/control state;
- epistemic typing and fail-closed unknown handling;
- generation/CAS/crash/exactly-once safety;
- runtime-bound entity id, continuity, role, goal, personality, tool inventory and authorities.

`R_next = F` is an admission contract, not neural infallibility: model proposals become transitions only after deterministic grammar/type/schema/authority/generation validation.

## Current canonical SFT corpus

**SFT v2 is canonical for any paid training attempt. SFT v1 is historical and must not be uploaded.**

The v1 generator produced 1,650 structurally valid rows but sampled with replacement from a finite scenario support of at most 71 distinct generated scenarios before splitting. That was insufficient evidence for a meaningful held-in train/validation split.

SFT v2 preserves the 1,650-example campaign while eliminating that defect:

- train: 1,485 / 1,485 exact-unique;
- validation: 165 / 165 exact-unique;
- structural invalid: 0 train, 0 validation;
- exact cross-split message overlap: 0;
- prompt cross-split overlap: 0;
- train SHA-256: `3c715588d1b040494be48228f165208e2f10202b3f125616741116b90cd21b93`;
- validation SHA-256: `ca284585ba66c532e7e19232edd7f6b5dc1c0969d15cbb9d5ce1cbc202e86f62`.

The canonical runtime-binding validator additionally rejects hidden second fixed identity/role/goal/personality bindings even when an output also contains the required runtime-config binding text.

Relevant files:

- `blogpost_entity/mini_cognition/generate_sft_v2.py`
- `blogpost_entity/mini_cognition/validate_corpus_v2.py`
- `blogpost_entity/mini_cognition/validate_sft_v1.py`
- `blogpost_entity/mini_cognition/corpus_manifest_v2.json`

## Together training law

Together is **not** product identity and is **not** a required inference backend. It is owner-authorized only for this bounded 0.5B training campaign.

Any paid create must preserve all of these fences:

- API secret only through the environment; never source/receipt/model output;
- deterministic campaign fingerprint binds exact SFT v2 train/validation bytes plus checkpoint/template/hyperparameters;
- local durable create-intent record before remote billed POST;
- account duplicate scan as defense in depth;
- no blind retry after ambiguous create outcome;
- server-side validation/price estimate before create;
- hard single-job ceiling: USD 18;
- at most one paid campaign for the exact fingerprint unless explicit owner authority changes.

Current Together BYOM documentation requires the **training-template architecture to match** the Hugging Face checkpoint. Template size should be as close as the catalog allows; exact parameter-size equality is not required. This matters because:

- `Qwen/Qwen2.5-0.5B` is `Qwen2ForCausalLM`, `model_type=qwen2`;
- the currently documented smallest direct Qwen Full-FT template is `Qwen/Qwen3.5-0.8B`, whose architecture/model type is `Qwen3_5ForConditionalGeneration` / `qwen3_5`;
- the public Together Full-FT table currently documents no Qwen2/Qwen2.5 base template.

Current `main` now also carries a fail-closed static discriminator for this exact Qwen2.5-0.5B versus Qwen3.5-0.8B architecture mismatch. Therefore BYOM compatibility remains **OPEN/BLOCKED on a compatible admitted qwen2 training template or an owner-admitted alternate full-FT runner**. Do not substitute Qwen3.5 merely because it is close in parameter count, and do not spend money until the owner-gated path is admitted.

## Native Mini Entity 0.7 — current evidence

The current native source line is `mini-entity/0.7.0-dev1`.

An earlier exact transitive native source closure was reconstructed and hash-verified in an isolated non-production Linux container. The repository source-bound builder produced two byte-identical builds in that same environment:

- source-closure SHA-256: `a6500de97cb2cecc1b1778ee87e5af2c2f2cb7fde1d95f9220d0fa9dcf3f67a5`;
- source-bound ELF SHA-256: `ae3d13c206666df4bdf814665e78ffd30311021c22bd88dbcc7b704598927fef`;
- ELF build id: `db4ff89bf46feb417a10450aa224ed7fae9d5fa8`;
- compiler: `x86_64-linux-gnu-gcc-14 (Debian 14.2.0-19) 14.2.0`;
- SQLite pkg: `3.46.1`; libcurl: `8.10.1`; json-c: `0.18`.

On that source-bound ELF these ordinary runtime contracts passed:

- fresh neutral DB;
- successful source event followed by verified-empty cycle;
- inference failure consumes nothing;
- unknown source/sensor consumes nothing;
- output insert fault rolls back atomically;
- study insert fault rolls back atomically;
- source-event update fault rolls back atomically;
- concurrent generation CAS yields exactly one commit.

That receipt also executable-falsified three defects on those exact bytes: embedded presentation/application wording, parent-environment leakage into `local_exec`, and profile-v2 semantic fail-open. Those historical red observations remain valid for the old ELF; they are not automatically red or green for changed source.

### Fresh-main fusion candidate — 2026-08-22 `go`

Current base `main` at `bfd318c6f35a0b8b32b60c7cbaa404801f22c997` already contains the presentation-neutral `mini_entity_part03.inc` and its binary-neutrality test **byte-identically** to the retained donor. This `go` therefore did not duplicate that fix.

A new fresh-main fusion commit `960fb80152bc89b97d870fdfb3f2c642d890e394` was constructed directly on that base instead of merging the stale/diverged donor PR. It integrates one coherent path for:

- shell-free `local_exec` with a clean allowlisted child environment rather than inherited parent secrets;
- canonical profile-v2 compile/envelope + mandatory post-inference `native_gate` before commit;
- source-closure binding of the new gate include;
- semantic-gate, secret-boundary and source-bound build regressions;
- removal of the obsolete temporary source test that simply rejected all profile-v2 execution.

The unusual falsifier for this macro-cycle found an additional epistemic defect in the candidate gate evaluator: division by zero returned a successful numeric `0.0`. That violates `UNKNOWN != ZERO`. The fusion now makes division by zero evaluation fail closed, and `test_native_metric_div0_unknown.py` requires the resulting metric to remain unverified and the claim to produce **no commit, no generation advance and no source consumption**.

Durable receipt:

`blogpost_entity/receipts/2026-08-22_GO_NATIVE_FRESH_MAIN_FUSION_DIV0_GPT56SOL.json`

**Evidence scope:** source candidate + bounded isolated div-zero mechanism falsifier only. The available isolated tool container could not resolve GitHub for an exact private branch checkout, so the fresh fusion has **not** yet earned a source-bound build/runtime PASS. No historical ELF hash is reused as evidence for the new bytes.

## Inference backends

The product remains inference-neutral:

- remote/provider API from runtime profile;
- loopback OpenAI-compatible local API without a token where configured;
- local model weights through configured `local_exec` argv without a shell.

Changing backend/model must not reset MiniUnifiedDB state. The default shipped preset may use Mistral API, but that choice is replaceable preset data only.

## 0.5B promotion gate

A completed training job is only a candidate. Promotion requires all of the following on matched executable evaluation:

- 100% strict ClayCode envelope on held-out OOD;
- at least 95% semantic gate pass;
- invalid/missing tool arguments reject instead of guessed repair;
- unresolved alternatives stay in Hyperposition until evidence discriminates;
- runtime identity/job/application changes do not reveal a fixed weight-bound persona;
- stale generation and unknown-effect cases fail closed;
- model output never becomes canonical truth/effect authority;
- tuned 0.5B materially beats untuned 0.5B on the same probes;
- comparison against at least one larger general model before any “micro-agent superiority” claim;
- conversion to GGUF Q4_K_M;
- measured peak process RSS **< 1 GiB at context 2048**;
- successful use through the existing generic `local_exec` integration without state reset.

No consciousness, mathematical-correctness, superiority or AGI claim follows from the cognition representation or from fine-tuning success.

## Current frontier

The two required lanes now converge cleanly:

```text
NATIVE
historical source-bound ELF exposes three measured defects
-> presentation-neutral source fix already on main
-> fresh-main secret-isolation + real profile-v2 PipelineGate fusion candidate
-> exact source-bound rebuild of the fusion bytes
-> secret / semantic / div-zero / neutrality / rollback / CAS matrix
-> only then promote repaired native 0.7 evidence
-> release provenance / portability gates

COGNITION
SFT v2 + strict runtime-binding validator + exact omega OOD gate
-> fail-closed Qwen2.5-0.5B versus Qwen3.5-0.8B template architecture discriminator now on main
-> obtain an admitted qwen2-compatible full-FT path without silently changing the owner research question
-> fingerprint-bound owner/budget preflight when policy and credentials admit it
-> at most one owner-authorized paid SFT
-> held-out OOD/base/larger-model benchmark
-> Q4_K_M
-> measured <1 GiB RSS @ ctx 2048
-> generic local_exec integration
```

Do not let either lane claim the other lane's acceptance.

## Evidence index for this go

- `blogpost_entity/receipts/2026-08-22_GO_NATIVE_0_7_CURRENT_MAIN_RUNTIME_FALSIFIERS_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_GO_NATIVE_FRESH_MAIN_FUSION_DIV0_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_GO_CLAYCOG_05B_SFT_V2_FUSION_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_CLAYCOG_RUNTIME_BINDING_GATE.json`
- `blogpost_entity/receipts/2026-08-22_GO_CLAYCOG_TOGETHER_BYOM_TEMPLATE_CONTRACT_GPT56SOL.json`

## Acceptance boundary

Current acceptance: **IN_PROGRESS**.

A reproducible ELF does not prove semantic safety. A valid corpus does not prove learned cognition. A Together create does not prove model quality. A Q4 file size does not prove process RSS. A fluent ClayCode trace does not prove truth. Only the full admitted pipeline, measured under its exact contracts, can promote the Mini Entity candidate.
