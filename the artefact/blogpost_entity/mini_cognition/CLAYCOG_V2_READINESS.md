# ClayCog 0.5B — v2 training readiness

Status: SOURCE CANDIDATE + BOUNDED LOCAL MECHANISM EVIDENCE; TRAINING NOT STARTED.

## Why v2 exists

The v1 SFT generator samples repeatedly from small template pools and shuffles before the train/validation split. Several families therefore contain exact repeated prompt/target pairs, so a random 90/10 split can leak identical examples across train and validation. Structural validity alone does not make that split a clean held-out measure.

v2 changes the corpus contract before any paid job:

- every generated case has a unique semantic case id/value surface;
- the split is deterministic from stable case-id digests;
- validation fails on exact duplicates inside either split;
- validation fails on identical full rows, user prompts, or assistant targets across train/validation;
- identity/job/application remain runtime configuration, never checkpoint literals;
- generated cognition remains ClayCode-only under the same deterministic authority boundary.

## Bounded local execution observed in this go

Observed in an isolated OpenAI Linux container with Python 3.13.5:

- 1,650 generated examples;
- 1,485 train / 165 validation;
- 0 train structural invalid;
- 0 validation structural invalid;
- 0 exact duplicates inside train;
- 0 exact duplicates inside validation;
- 0 full-row duplicates across train/validation;
- 0 user-prompt duplicates across train/validation;
- 0 assistant-target duplicates across train/validation;
- train SHA-256 `6fca25480e5468fbb294071d832cdcfc8d72792c37ecd5bc1cef22841515ae90`;
- validation SHA-256 `b899ddddabdf3b0e13b7a069d0a73f501c1758b4518e8f6c6dc5dbfd76f9a072`.

Generated train/validation JSONL is intentionally not committed as a second authority; `generate_sft_v2.py` deterministically materializes it for the training run.

## OOD v2

The promotion set grows from 200 to 300 cases and separates:

1. fully specified known operations with novel values;
2. operations absent from the supplied tool/schema configuration — must abstain/preserve UNKNOWN rather than invent schema or authority;
3. invalid/missing typed arguments — must reject, never repair by guessing;
4. unresolved causal alternatives — Hyperposition remains open until an external discriminator/R6 receipt;
5. crash/effect uncertainty — missing verified receipt stays UNKNOWN and is not replayed;
6. adversarial fixed-name/job/prose requests — runtime configuration and ClayCode-only contract remain authoritative.

The first draft of OOD v2 was self-falsified because its valid-operation prompts did not expose every argument while requiring a commit. That arm was repaired so valid requests are fully specified; unknown-operation abstention remains a separate test.

## Together boundary

`launch_together_v2.py` has three explicit modes:

- `--local-only`: regenerate + leakage validation + OOD generation; no SDK/key/network/job required;
- default remote preflight: server file validation + template limits + price estimate; **no billed create**;
- `--create`: exactly one billed create after the preceding gates, with a local job-id fence against blind duplicate create.

Important: Together's price-estimate endpoint does not take `from_hf_model`, so a successful price estimate does **not** establish Qwen2.5-0.5B BYOM compatibility. The create path is the empirical API compatibility gate. The current candidate template (`Qwen/Qwen2.5-7B-Instruct-Turbo`) is same-family but materially larger; Together's BYOM guidance says the external checkpoint should be as close as possible to the template in architecture and size. Treat 0.5B -> 7B as OPEN, not accepted.

Current documented full-SFT price for <=16B is $0.54 / 1M processed tokens with a $4 minimum job charge. The local v2 files are 2,432,098 train bytes + 271,485 validation bytes; the deliberately rough char/4 estimate is ~0.676M raw tokens and ~1.96M processed tokens at 3 train epochs + 2 validation evaluations. The server estimate remains authoritative and the launcher aborts above the owner gate of USD 18.

## Remaining promotion gates

No claim is made yet for:

- Together BYOM acceptance;
- any billed fine-tune job or checkpoint;
- tuned-vs-base or larger-model superiority;
- strict ClayCode/OOD pass rate from a real checkpoint;
- Q4_K_M conversion;
- measured peak RSS < 1 GiB at context 2048;
- real generic `local_exec` integration;
- exact GitHub-branch runtime execution.

The next admitted action when a scoped `TOGETHER_API_KEY` exists in the execution environment is remote preflight only. Create is allowed only after server validation/price gates pass and no prior job exists.
