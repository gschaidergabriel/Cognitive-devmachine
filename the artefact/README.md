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
- the currently documented smallest Qwen Full-FT template is `Qwen/Qwen3.5-0.8B`, whose architecture/model type is `Qwen3_5ForConditionalGeneration` / `qwen3_5`;
- the public Together Full-FT table currently documents no Qwen2/Qwen2.5 base template.

Therefore BYOM compatibility remains **OPEN/BLOCKED on a compatible admitted qwen2 training template or an owner-admitted alternate full-FT runner**. Do not substitute Qwen3.5 merely because it is close in parameter count, and do not spend money until an authenticated preflight establishes an actually admitted compatible path.

Public pricing refreshed on 2026-08-22 lists standard Full SFT up to 16B at **USD 0.54 / 1M processed tokens** with a **USD 4 minimum job charge**. Those numbers remain provider facts, not a quote for this exact custom checkpoint. Under the owner USD 18 single-job gate, price is therefore not the current blocker; **architecture-compatible provider admission is**.

The current exact PR admission workflow also compiles the canonical launcher/create-safety/provider-contract boundary and runs both no-network create-safety and SDK-v2 provider-contract regressions. Exact GitHub-hosted runner attempts remain admission-blocked before any visible step (`steps=null`). This is runner admission failure with zero test credit, not a ClayCog test failure and not PASS.

## Native Mini Entity 0.7 — current evidence

The current native source line is `mini-entity/0.7.0-dev1`.

The exact transitive current native source blobs and exact repository `build_native_bound.py` were reconstructed and hash-verified in an isolated non-production Linux container. The repository source-bound builder then produced two byte-identical builds in the same environment:

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

This closes the previous “source exists but current 0.7 was never actually built/run” gap at **same-environment source-bound mechanism scope**. It does not establish cross-environment reproducibility or final release acceptance.

### Current native blocker fusion status

Native 0.7 is **not promotable yet**. The three previously confirmed current-main defects are now source-fused as follows:

1. **Binary neutrality — SOURCE FIX FUSED:** the state-box presentation repair was fused via PR #830 / merge `b2d49a8e0e88b01927e9673a38dab9fbeb175b97`. Replaceable headings and interpretation prose now come from runtime configuration rather than executable presentation identity. Exact source-bound rebuild/runtime falsification of the fused head is still required before runtime credit.
2. **Local-runner secret boundary — SOURCE FIX FUSED:** PR #850 / merge `51c25c950eb4e2c68d834374d4bfc9f390a6d154` now launches configured local runners through a clean `/usr/bin/env -i` environment and admits only bounded non-secret runtime variables (`PATH`, `HOME`, `TMPDIR`, `LANG`, `TZ`). A focused source-bound runtime regression was added, but the exact GitHub job again failed before any visible runner step, so this has source/mechanism credit only and still requires exact execution.
3. **Canonical profile-v2 semantic admission — FAIL-CLOSED GUARD FUSED:** PR #769 / merge `659cc2471b73bcefebb6a57694e6737cc2107cc5` rejects canonical v2 profiles before inference/commit until native v2 parity exists. This closes the prior fail-open persistence path at source level; it does **not** implement the required full profile-driven compile envelope and post-inference `pipeline_gate`. The guard must remain until coherent parity is implemented and exactly executed.

A donor review during the same `go` also falsified the older #764 branch/body claim that its verified-empty pre-inference shortcut had already been removed: the exact donor head still contained that shortcut. The donor was repaired for evidence continuity, but main advanced through #769/#830, so the broad donor was intentionally not merged. Only its still-orthogonal secret-isolation mechanism was extracted onto fresh main as #850.

The existing native exact-repro workflow now has a source-level expectation mismatch: it applies the shipped `zero_blog` profile-v2 and expects successful `local_exec`, while #769 intentionally blocks profile-v2 until full parity exists. This workflow must be reconciled without weakening #769: use an admitted simple profile for backend/secret regression and separately assert canonical v2 fail-closed behavior until full parity is implemented.

The original defect evidence is durable at:

`blogpost_entity/receipts/2026-08-22_GO_NATIVE_0_7_CURRENT_MAIN_RUNTIME_FALSIFIERS_GPT56SOL.json`

Current fusion/re-entry evidence is durable at:

- `blogpost_entity/receipts/2026-08-22_GO_MAIN_REENTRY_NATIVE_COGNITION_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_GO_LOCAL_EXEC_ENV_FRESH_MAIN_GPT56SOL.json`

The next native promotion attempt must use the exact current fused source, reconcile the exact-repro workflow with the #769 fail-closed contract, source-bound rebuild it, rerun the secret/semantic/atomicity/CAS matrix, and then separately close full native profile-v2 compile+`pipeline_gate` parity. Do not remove the fail-closed v2 guard merely to obtain a green runtime path.

## Inference backends

The product remains inference-neutral:

- remote/provider API from runtime profile;
- loopback OpenAI-compatible local API without a token where configured;
- local model weights through configured `local_exec` argv without a shell and, after #850, without inheriting arbitrary parent secrets.

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
#769 fail-closed v2 admission + #830 presentation neutrality + #850 local_exec parent-secret isolation fused
-> reconcile canonical exact-repro workflow with #769 without weakening fail-closed semantics
-> exact source-bound rebuild
-> repeat secret/semantic/atomicity/CAS falsifiers
-> implement coherent canonical profile-v2 compile envelope + post-inference pipeline_gate parity
-> remove v2 fail-closed guard only after exact parity evidence
-> release provenance/portability gates

COGNITION
SFT v2 + strict runtime-binding/omega/OOD gates + exact provider-contract/campaign-identity/architecture-discriminator CI coverage
-> GitHub runner admission remains blocked before steps; zero exact-runner test credit
-> compatible qwen2 Full-FT runner/template admission
-> fingerprint-bound budget preflight
-> at most one owner-authorized paid SFT
-> held-out OOD/base/larger-model benchmark
-> Q4_K_M
-> measured <1 GiB RSS @ ctx 2048
-> generic local_exec integration
```

Do not let either lane claim the other lane's acceptance.

## Evidence index for this go

- `blogpost_entity/receipts/2026-08-22_GO_NATIVE_0_7_CURRENT_MAIN_RUNTIME_FALSIFIERS_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_GO_CLAYCOG_05B_SFT_V2_FUSION_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_CLAYCOG_RUNTIME_BINDING_GATE.json`
- `blogpost_entity/receipts/2026-08-22_GO_CLAYCOG_TOGETHER_BYOM_TEMPLATE_CONTRACT_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_GO_MAIN_REENTRY_NATIVE_COGNITION_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_GO_LOCAL_EXEC_ENV_FRESH_MAIN_GPT56SOL.json`

## Acceptance boundary

Current acceptance: **IN_PROGRESS**.

A reproducible ELF does not prove semantic safety. A valid corpus does not prove learned cognition. A Together create does not prove model quality. A Q4 file size does not prove process RSS. A fluent ClayCode trace does not prove truth. A source-level fail-closed guard does not prove full semantic parity. Only the full admitted pipeline, measured under its exact contracts, can promote the Mini Entity candidate.
