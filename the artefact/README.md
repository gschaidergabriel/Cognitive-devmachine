# the artefact — Multi-use Mini Entity pipeline all-in-one

`the artefact/` is the canonical product workspace for the current owner-directed Mini Entity program in `gschaidergabriel/clay-global-research-entity/main`.

The previous ClayVerse single-container endpoint and the former 0.5B-primary campaign are superseded as active product/training targets. Their accepted mechanisms remain bounded historical evidence only where they strengthen the current Mini Entity.

## Current authority

Read current repository state before making consequential claims. At the 2026-08-22 re-entry represented by this README, the relevant authority chain is:

1. `research_entity/global/MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md` — current cognition/training owner directive;
2. `research_entity/global/MINI_ENTITY_CLAYCOG_05B_TRAINING_DIRECTIVE.md` — prior supporting architecture/safety directive where not superseded;
3. `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md` — base Mini Entity product directive;
4. `research_entity/rooms/PROGRAM_STATE.json` — current program state;
5. `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` — current execution-control policy for research/provider spend.

The product is **IN_PROGRESS**. Source presence, a green component test, generated corpus, fine-tuning job, checkpoint, quantized file, or inference demo never implies whole-product acceptance.

## Product target

The release shape remains deliberately small and replaceable:

1. one application-neutral and inference-neutral native `.clay` pipeline executable (`mini_entity.clay`);
2. one SQLite MiniUnifiedDB (`mini_entity.db`) as persistent state/config/evidence authority;
3. one optional replaceable generic **approximately-1B ClayCode cognition checkpoint**.

The current primary training base selected by owner directive is `Qwen/Qwen3.5-0.8B`.

`zero_blog` is only the fully replaceable shipped preset. Zero, blogging, presentation language, personality, provider, model name, API choice, local runner choice, role, goal, audience and application semantics are runtime configuration/data — never executable or durable entity identity.

## Architecture law

### Native executable

The executable owns generic machinery only:

- evidence/source preprocessing;
- canonical run/state envelope;
- generic inference dispatch;
- immutable truth/secret/admission gates;
- exactly-once source consumption;
- generation CAS;
- atomic SQLite persistence;
- deterministic effect/state authority boundaries.

If a replaceable application, personality, provider, model, prompt, presentation label, or tool description can live in runtime configuration, hard-coding it into executable identity is a regression.

### MiniUnifiedDB

SQLite owns continuing state and runtime configuration. Switching application preset, inference backend, local weights, provider, prompt, role, goal or personality must not fork or reset entity continuity.

Epistemic law:

```text
UNKNOWN != ZERO != ERROR != MEASURED
REPORTED != MEASURED
MODEL_OUTPUT != CANONICAL_TRUTH
MODEL_PROPOSAL != EFFECT_AUTHORITY
```

### Replaceable ~1B cognition

The cognition checkpoint is inference data, not canonical identity/state/effect authority. It must remain reusable across applications and runtime identities.

Required learned machinery includes:

- ClayCode-only generated cognition;
- GRF R0..R6 as typed reasoning field;
- Hyperposition for unresolved alternatives;
- typed `omega` function/tool/API candidates;
- deterministic grammar/type/schema/authority/generation admission before effect eligibility;
- computed semantic self/control state without confusing it with external fact;
- UNKNOWN/ERROR/MEASURED epistemic separation;
- stale-generation rejection and crash ambiguity preservation;
- runtime-bound entity id, continuity, role, goal, personality, tool inventory and authorities.

`R_next = F` is an admission invariant, not neural infallibility.

## Canonical SFT v2 curriculum

SFT v2 is the current canonical ClayCog curriculum unless a newer admitted corpus supersedes it.

Current generated corpus invariants:

- total examples: 1,650;
- train: 1,485 / 1,485 exact-unique;
- validation: 165 / 165 exact-unique;
- structural invalid: 0 train, 0 validation;
- exact cross-split message overlap: 0;
- prompt cross-split overlap: 0;
- train SHA-256: `3c715588d1b040494be48228f165208e2f10202b3f125616741116b90cd21b93`;
- validation SHA-256: `ca284585ba66c532e7e19232edd7f6b5dc1c0969d15cbb9d5ce1cbc202e86f62`.

The corpus is **model- and provider-neutral**. `corpus_manifest_v2.json` binds model/provider selection outside corpus identity through the campaign descriptor rather than embedding a Qwen/provider identity in the curriculum manifest.

The current structural validator requires exact runtime identity/role/goal/personality bindings, exact top-level return semantics, and fail-closed omega admission. It also rejects reserved semantic identity slots that could smuggle fixed name/role/goal/personality/provider/model/checkpoint/job identity through alternate semantic calls.

Relevant files:

- `blogpost_entity/mini_cognition/generate_sft_v2.py`
- `blogpost_entity/mini_cognition/validate_corpus_v2.py`
- `blogpost_entity/mini_cognition/validate_sft_v1.py`
- `blogpost_entity/mini_cognition/claycode_syntax_v1.py`
- `blogpost_entity/mini_cognition/corpus_manifest_v2.json`

## Qwen3.5-0.8B direct Full-FT lane

The owner-selected campaign source path is a direct Full fine-tuning lane for `Qwen/Qwen3.5-0.8B`. The launcher is fail-closed around:

- exact model identity;
- exact SFT-v2 train/validation bytes;
- canonical local generation + corpus validation;
- machine-readable execution policy;
- provider Full-FT support check;
- server-side validation/price estimate before any billed create;
- bounded budget;
- deterministic campaign fingerprint;
- explicit fingerprint-bound create confirmation;
- duplicate-campaign scan;
- durable exclusive create-intent ledger;
- zero-retry billed create;
- post-create training-identity verification;
- UNKNOWN outcome after ambiguous create rather than blind retry.

Together is neither product identity nor required inference backend.

## Current FREE_ONLY execution boundary

The current supervisor execution policy has `verified_updates.free_only=true`.

Therefore the dormant Together 0.8B source lane is **not executable under the current control state**, even though the owner directive selects/permits that bounded campaign in principle. While FREE_ONLY remains true:

- no Together credential lookup;
- no Together import/network execution;
- no file upload;
- no authenticated `model_limits` call;
- no price-estimate request;
- no billed create;
- no training spend.

The launcher must reject the paid provider before secret lookup and before network. Owner campaign authority does not override a stricter current execution-control gate.

If FREE_ONLY is later explicitly cleared by current authority, re-read exact source/policy and perform preflight-only provider admission before any separately authorized billed create.

## Latest exact local cognition evidence — 2026-08-22

The exact cognition blobs at source `f807c0e86971be78da0054ff6a08406726c0aef3` were reconstructed in an isolated Linux runtime and Git-blob identity was verified before execution.

Observed at that exact source:

- Python compile: PASS;
- direct 0.8B launcher regression suite: 13 / 13 PASS;
- real `generate_sft_v2.py -> validate_corpus_v2.py` chain: PASS;
- full 1,650-row corpus regenerated with the canonical hashes above;
- reserved semantic identity-slot validation remained green for the admitted corpus;
- with machine-readable `free_only=true`, the launcher terminated at `FREE_ONLY_PROVIDER_REJECT` before secret lookup and before network;
- Together provider call/upload/create/training/spend: none.

Durable receipt:

`blogpost_entity/receipts/2026-08-22_GO_08B_EXACT_LOCAL_PREFLIGHT_RUNTIME_GPT56SOL.json`

The model-neutral SFT-v2 manifest was subsequently regenerated and merged with exact-blob evidence; the current materialized manifest no longer carries stale Qwen2.5 base identity.

## Evaluation and promotion boundary

The ~1B checkpoint is not promoted merely because the lane source, corpus, or local pre-provider path is green.

Promotion still requires the applicable current gates, including:

- an actually admitted training result with exact checkpoint identity when execution policy permits it;
- matched evaluation against the untuned base and a larger general model;
- OOD/semantic evaluation that cannot be gamed by strings/comments/dead control flow;
- failure/counterexample retention;
- Q4_K_M quantization;
- measured peak RSS below 1 GiB at context 2048;
- real generic `local_exec` integration without MiniUnifiedDB reset or fixed application identity.

Do not claim consciousness, AGI, mathematical correctness, superiority, successful Together training, `<1 GiB RAM`, or local integration from source structure alone.

## Native Mini Entity frontier

The native pipeline remains a separate whole-product acceptance frontier. Current cognition progress does not promote native runtime acceptance.

Native acceptance continues to require exact-current execution of the relevant neutrality, secret-isolation, profile-v2 semantic admission/parity, atomicity, generation-CAS and local inference contracts. Keep fail-closed guards in place where full profile parity is not yet implemented.

## Evidence law

Always distinguish:

```text
SOURCE CANDIDATE
MECHANISM SUPPORTED
EXACT RUNTIME VERIFIED
WHOLE PRODUCT ACCEPTED
```

A hosted workflow that fails before visible steps supplies zero runtime test credit. A provider catalog or source-defined campaign supplies zero training credit. A historical receipt does not automatically generalize to a newer source head.

Current GitHub source/history/receipts are the durable coordination ledger; executable claims remain bound to exact observed source/artifact/environment evidence.
