# CLAYCOG 0.5B strict-admission GO receipt — 2026-08-22

Status: SOURCE_CANDIDATE + BOUNDED_MECHANISM_EVIDENCE; EXACT_PR_RUNNER_NOT_OBSERVED

## Authority joined

Current program authority resolved from current `main`, not the 2026-08-17 cache:

- active program: `MINI_ENTITY_PIPELINE_ALL_IN_ONE`;
- active stage: `MINI_ENTITY_PIPELINE_CLAY_PLUS_05B_COGNITION`;
- active 0.5B directive: `research_entity/global/MINI_ENTITY_CLAYCOG_05B_TRAINING_DIRECTIVE.md`;
- Together is allowed only as the bounded owner-authorized training campaign, never as Mini Entity product identity/runtime requirement.

## Frontier selected

Before spending owner-authorized training budget, establish that SFT targets actually satisfy the fail-closed `CLAYCODE_COGNITION_V1` grammar/admission contract.

The prior `validate_sft_v1.py` checked prefix/balance/required and forbidden substrings but did not parse statements/calls or enforce intrinsic arity. Therefore historical `0 invalid` corpus counts did not establish the stronger specification claim.

## Exactly one unusual experiment for this user-triggered GO

Intervention: five deliberately invalid but superficially ClayCode-shaped targets were presented to the prior admission logic:

1. natural-language prose in the function body;
2. invented intrinsic;
3. wrong `focus_set` arity;
4. trailing garbage after a valid call;
5. invented constructor.

Observed prior result:

```json
{"lines":5,"bad":0,"ok":true}
```

All five mutations were false accepts.

Observed hardened-logic result on the same mutation bundle:

```json
{"lines":5,"bad":5,"ok":false}
```

A syntactically valid `omega` candidate with grammar/types/schema/authority/generation gates before commit remained admitted after correcting the test fixture to the canonical four-argument `omega_arg` arity.

Interpretation: the hypothesis "substring/balance validation is sufficient training admission" is REJECTED.

This bounded mutation result is mechanism evidence only. It does not prove full-corpus, model, Together, quantized-RSS, or whole Mini Entity acceptance.

## Source delta

PR: `#777` — `Harden ClayCode 0.5B corpus admission before training`

Current candidate rebased/merged onto current owner state through merge commit:

`1d5626c2e44ecfa722cf7aa370e6ba505da23e0e`

Changed product/cognition files:

- `the artefact/blogpost_entity/mini_cognition/validate_sft_v1.py`
  - strict statement/expression/call parsing;
  - JSON string literal validation;
  - intrinsic allowlist;
  - exact arity checking;
  - trailing-text rejection;
  - pre-commit `omega` grammar/types/schema/authority/generation gate ordering;
  - reject+commit contradiction rejection.
- `the artefact/blogpost_entity/mini_cognition/test_validate_sft_v1.py`
  - mutation regressions;
  - omega ordering regression;
  - valid omega control;
  - rebuild + validate all 1,650 canonical generator targets.
- `the artefact/blogpost_entity/mini_cognition/README.md`
  - historical weak-validation boundary made explicit.
- `the artefact/README.md`
  - stale ClayVerse endpoint replaced with current Multi-use Mini Entity + optional 0.5B cognition endpoint.

## Parallel fusion / non-duplication

While this GO was active, current `main` independently gained:

- `#772` / `f231b2d...`: idempotent Together billed-create campaign fingerprint + local durable intent ledger + zero-retry create + ambiguous remote outcome fail-closed;
- `#773` / `6a831bc...`: current 0.5B status-footer owner law;
- `#778` / `cb46a34...`: focused GitHub-hosted ClayCode admission PR workflow.

The candidate was explicitly re-bound on top of these changes rather than overwriting or duplicating them.

## Isolated execution boundary

The five-case bounded mutation falsifier was observed in an isolated container.

A focused GitHub-hosted PR workflow now exists on `main`, but no started workflow/job/status was observed for the candidate head during this GO. Therefore:

- full 1,650-target regression runtime credit: **NOT ESTABLISHED**;
- GitHub runner/control-plane state: **NO STARTED JOB OBSERVED**;
- this is not classified as a semantic test failure;
- source candidate must not be promoted solely because the regression file exists.

## Together compatibility / cost boundary

Current public Together documentation supports `from_hf_model` for BYOM fine-tuning and current public pricing lists Full SFT through 16B at `$0.54 / 1M processed tokens` with a `$4` minimum per training job.

Exact `Qwen/Qwen2.5-0.5B` + selected Qwen2.5 Together template acceptance remains **UNKNOWN** until the live provider preflight/create path accepts the checkpoint under the exact campaign. No secret was available to this worker and no paid job was created.

## Promotion state after this GO

- strict admission mechanism: strengthened source candidate;
- mutation falsifier: mechanism supported;
- exact full corpus runtime: unresolved;
- Together BYOM checkpoint/template acceptance: unresolved;
- training job: not started by this GO;
- tuned checkpoint quality: nonexistent/unresolved;
- Q4_K_M measured RSS <1 GiB @ 2048: unresolved;
- local_exec integration of tuned model: unresolved;
- whole Mini Entity acceptance: IN_PROGRESS.

## Highest-information next executable steps

1. obtain an actually-started isolated exact-head execution of `test_validate_sft_v1.py` and preserve source identity + output;
2. if green, run preflight with runtime-injected Together secret: exact corpus validation/upload, template limits, server estimate, BYOM compatibility gate; do not create a billed job if compatibility or estimate is uncertain;
3. only after exact fingerprint confirmation and owner budget gates, create at most one paid campaign;
4. evaluate tuned 0.5B on OOD vs base and larger model, then Q4_K_M + measured RSS + configured `local_exec` integration;
5. in parallel, continue the current Native Mini Entity 0.7 exact build/runtime/fault lane without duplicating active PR work.
