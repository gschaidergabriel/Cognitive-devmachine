# the artefact — Multi-use Mini Entity pipeline all-in-one

`the artefact/` is the canonical product workspace for the current owner-directed Mini Entity program in `gschaidergabriel/clay-global-research-entity/main`.

The previous ClayVerse single-container endpoint is superseded as the active product target. Historical ClayVerse/EntityOS material remains bounded implementation/research evidence only where it helps the current product; it is not allowed to override the current Mini Entity owner directives.

Current authority:

- `research_entity/global/MINI_ENTITY_CLAYCOG_05B_TRAINING_DIRECTIVE.md`
- `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`
- `research_entity/rooms/PROGRAM_STATE.json`

The product is **IN_PROGRESS**. Source presence, a green component test, a generated corpus, a fine-tuning job, a quantized file, or an inference demo never implies whole-product acceptance.

## Latest go re-entry — 2026-08-22

Current source reality is newer than `PROGRAM_STATE.json` 7.5 and must not be regressed to that stale blocker list.

- Cognition PR #862 / merge `2f9fda0a70d5fc483b73782733d3680a093ef470` is now canonical: the one SFT-v2 ClayCode validator requires runtime bindings and `return c` at the turn-body level; any omega commit requires an exact top-level commit plus exactly one grammar/types/schema/authority/generation gate, exact runtime-config authority/generation, and rejects comments, dead/nested control-flow gates, duplicate gates/commits and reject+commit. Exact validator blob `3b9bdcd37cdc40a5c3fa48647d44737f38bc3fb1` was independently reconstructed in an isolated Linux container; `py_compile`, a valid omega control, dead-control rejection and comment-smuggling rejection passed. Donor evidence for the same exact blob had focused 16/16 gate tests plus all 1,485 train + 165 validation SFT-v2 targets structurally valid under their exact expected hashes.
- OOD semantic calls are no longer raw-substring-only after #838 / `e073e3577334d4dce723ffca378e61528bf0ed24`: the canonical evaluator uses a comment/string-safe non-executing call extractor, so marker text in strings/comments does not earn semantic-call credit.
- Global unusual-experiment coordination is reconciled by #870 / `84c6c5f03c138f545f5ebd0fc9e9644fbe5464bc`: exactly one unusual experiment is retained for this user-triggered `go`, `QWEN25_05B_VS_SMALLEST_CURRENT_TOGETHER_QWEN_FULLFT_TEMPLATE_ARCHITECTURE_FALSIFIER`. Offline secret-poisoning remains an ordinary deterministic regression.
- The three previously confirmed native source defects now all have bounded source fixes: #769 canonical profile-v2 fail-closed admission, #830 presentation-language neutrality, and #850 local-exec parent-secret isolation. #861 / `00a14d78e3312b7683e1bea62dd980bffcda0146` reconciles the exact-repro workflow with the #769 fail-closed contract. #868 / `985a845be95d57fb6cedb28f70bf9548bccd1085` additionally traces both active and verified-empty local-exec boundaries and requires the empty cycle to infer/persist rather than short-circuit. #852 / `8eeada1aec95779137b35ca0314f5ab06d6b0541` binds the existing presentation-neutrality and profile-v2 admission-order source falsifiers into that same single canonical unittest adapter. These remain source/test-coverage improvements until the exact fused runtime path actually executes.
- Exact PR-head GitHub Actions attempts still terminate before any visible step (`steps=null`), including #852 head `8d4f3ed222ffc5c44626c84ec0f7d267c0fdbe0d` workflow run `32562432801` / job `97005988407`. This is execution-admission/control-plane failure with zero runtime test credit, not a code-test failure and not PASS.
- No Together provider request, upload, billed create or training occurred in this go. Current Together BYOM docs require an architecture-compatible training template, while the current Full fine-tuning table lists Qwen3.5/3.6 bases but no Qwen2/Qwen2.5 base. Architecture-compatible qwen2 Full-FT provider/runner admission remains the paid-campaign blocker; model quality, GGUF Q4_K_M and measured <1 GiB RSS remain downstream gates.

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

The canonical validator now combines the runtime-binding gate with exact top-level omega admission. Required identity/role/goal/personality bindings cannot be spoofed from strings or moved under nested control flow, and omega commit/gate credit cannot be supplied by comments, dead control flow or duplicates.

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

The current exact PR admission workflow also compiles the canonical launcher/create-safety/provider-contract boundary and runs both no-network create-safety and SDK-v2 provider-contract regressions. Campaign identity now additionally binds seed/effective learning-rate/warmup and verifies created-job identity after durable `JOB_KNOWN` persistence. Exact GitHub-hosted runner attempts remain admission-blocked before any visible step (`steps=null`). This is runner admission failure with zero test credit, not a ClayCog test failure and not PASS.

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

PR #861 / merge `00a14d78e3312b7683e1bea62dd980bffcda0146` reconciles the canonical native exact-repro workflow with the #769 fail-closed contract without weakening it: generic local-exec secret isolation and rollback are exercised through an admitted neutral fixture profile, while the shipped canonical v2 profile is separately required to remain fail-closed until parity exists.

PR #868 / merge `985a845be95d57fb6cedb28f70bf9548bccd1085` strengthens that single exact-repro entry by requiring both active and verified-empty `local_exec` cycles to execute the configured runner, remain secret-file/network clean under `strace`, advance continuity, persist two outputs/study rows and keep DB integrity. PR #852 / merge `8eeada1aec95779137b35ca0314f5ab06d6b0541` then binds the already-canonical presentation-neutrality and semantic-admission source falsifiers into the same adapter rather than creating a parallel test path. The #852 exact Actions attempt again failed before any visible job step, so these additions have source/test-coverage credit only until an admitted runner starts.

The original defect evidence is durable at:

`blogpost_entity/receipts/2026-08-22_GO_NATIVE_0_7_CURRENT_MAIN_RUNTIME_FALSIFIERS_GPT56SOL.json`

Current fusion/re-entry evidence is durable at:

- `blogpost_entity/receipts/2026-08-22_GO_MAIN_REENTRY_NATIVE_COGNITION_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_GO_LOCAL_EXEC_ENV_FRESH_MAIN_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_GO_NATIVE_REENTRY_852_TOGETHER_BLOCKER_GPT56SOL.json`

The next native promotion attempt must use the exact current fused source, source-bound rebuild it, rerun the secret/semantic/atomicity/CAS matrix under the #861/#868/#852 test contract, and then separately close full native profile-v2 compile+`pipeline_gate` parity. Do not remove the fail-closed v2 guard merely to obtain a green runtime path.

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
+ #861 exact-repro split contract + #868 active/verified-empty I/O boundary + #852 semantic source guards
-> exact fused source-bound rebuild/runtime execution when an admitted runner actually starts
-> repeat secret/semantic/atomicity/CAS falsifiers
-> implement coherent canonical profile-v2 compile envelope + post-inference pipeline_gate parity
-> remove v2 fail-closed guard only after exact parity evidence
-> release provenance/portability gates

COGNITION
SFT v2 + #862 exact top-level canonical admission + #838 real-call OOD semantics + exact typed-omega OOD gate
+ exact provider-contract/campaign-identity/architecture-discriminator safety fences
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
- `blogpost_entity/receipts/2026-08-22_GO_CLAYCOG_BYOM_ARCHITECTURE_AUDIT_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_GO_MAIN_REENTRY_NATIVE_COGNITION_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_GO_LOCAL_EXEC_ENV_FRESH_MAIN_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_GO_CLAYCOG_TOPLEVEL_OMEGA_FRESH_FUSION_GPT56SOL.json`
- `blogpost_entity/receipts/2026-08-22_GO_NATIVE_REENTRY_852_TOGETHER_BLOCKER_GPT56SOL.json`

## Acceptance boundary

Current acceptance: **IN_PROGRESS**.

A reproducible ELF does not prove semantic safety. A valid corpus does not prove learned cognition. A Together create does not prove model quality. A Q4 file size does not prove process RSS. A fluent ClayCode trace does not prove truth. A source-level fail-closed guard does not prove full semantic parity. Only the full admitted pipeline, measured under its exact contracts, can promote the Mini Entity candidate.