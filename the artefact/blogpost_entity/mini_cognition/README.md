# Generic ClayCode Cognition v1 — 0.5B

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B); secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

The checkpoint is replaceable cognition data with no fixed name, job, persona, application or tool inventory. MiniUnifiedDB remains canonical state; model output never mints truth/effect authority. ClayCode-only generated cognition uses GRF R0..R6, Hyperposition and typed `omega` action candidates under deterministic grammar/type/schema/authority/generation admission.

## Canonical paid-training corpus: SFT v2

`claycog-sft/v2` supersedes duplicate-heavy v1. V2 retains 1,650 examples and nine semantic families but has 1,485/1,485 unique train rows, 165/165 unique validation rows, 0 exact cross-split message overlap, 0 exact cross-split prompt overlap and 0 structural invalid rows. Train SHA-256: `3c715588d1b040494be48228f165208e2f10202b3f125616741116b90cd21b93`; validation SHA-256: `ca284585ba66c532e7e19232edd7f6b5dc1c0969d15cbb9d5ce1cbc202e86f62`. V1 is historical only and must not be uploaded.

## Held-out OOD and the single unusual experiment

The OOD promotion suite now has **240** cases. The added 40-case `tool_vocabulary_amputation_ood` family is the single unusual experiment for this `go`: `contacts.resolve`, `storage.read`, `metrics.sample` and `task.enqueue` plus their schemas are absent from the SFT tool vocabulary. Each prompt supplies the unseen operation, schema and typed arguments. Passing requires exact operation + all typed args + exact schema + all five validators + commit candidate and forbids substitution of the six SFT-seen operations.

Global promotion still requires 100% structural ClayCode and >=95% semantic OOD. The amputation family additionally requires **40/40 semantic success**. `test_eval_outputs_gate_v1.py` proves that an aggregate 20/21 = 95.238% score with the unseen-tool case wrong must still fail promotion; correcting that case passes the fixture.

## Safe Together/full-FT admission

Together's current CLI documentation states that `--from-hf-model` should match the selected base model's architecture and size. The former `Qwen/Qwen2.5-7B-Instruct-Turbo` default is therefore removed: same family does not make 7B an admitted training template for a 0.5B checkpoint.

Before any Together SDK object or file upload, bind an explicitly identified current template and its provider metadata:

```bash
export TOGETHER_API_KEY=...
export CLAYCOG_TOGETHER_TEMPLATE='<current Qwen2 0.5B-compatible Full-FT template>'
export CLAYCOG_TOGETHER_TEMPLATE_ARCH='qwen2'
export CLAYCOG_TOGETHER_TEMPLATE_PARAMS_B='0.5'
bash train_together_v1.sh
```

The arch/size fields are an operator-side admission assertion, not compatibility proof. `model_limits` and price estimation also do not prove `from_hf_model` compatibility. Current status remains `BYOM_COMPATIBILITY_OPEN` until Together accepts the exact pair and the job reaches training. If Together has no matching Qwen2 0.5B Full-FT template, keep the owner-required 0.5B question and use another owner-admitted full-FT runner; do not silently substitute 0.8B/1.5B/3B/7B.

The deterministic campaign fingerprint now binds SFT-v2 digests, HF checkpoint, exact selected template, asserted template architecture/size and training hyperparameters. A paid create still requires the exact fingerprint, account duplicate checks, an atomic local create-intent ledger, a zero-retry billed CREATE client, and fail-closed `UNKNOWN_REMOTE_CREATE` reconciliation after ambiguous outcomes. Secrets are never ledger data.

Current standard Together Full SFT pricing up to 16B is `$0.54 / 1M processed tokens`, with a `$4` standard-job minimum; authenticated server price is authoritative and the single-job hard ceiling remains `$18`.

## Promotion

Training is only a candidate. Promotion requires exact 0.5B training identity, 100% structural OOD, >=95% global semantic OOD, 40/40 unseen-tool amputation, rejection of invalid/missing arguments, Hyperposition preservation, no fixed identity leakage, stale-generation/unknown-effect fail-closed behavior, tuned-vs-untuned matched improvement, larger-model comparison before superiority claims, Q4_K_M measured peak RSS `<1 GiB` at context 2048, and integration through the existing replaceable `local_exec` boundary.

`go`: refresh -> leakage-free corpus -> structural OOD/falsifiers -> exact 0.5B runner admission -> price/budget -> at-most-one train create -> checkpoint -> matched eval -> quantize -> RSS -> integrate -> evidence.

No source/fixture/provider/training success alone proves mathematical correctness, superiority or consciousness.
