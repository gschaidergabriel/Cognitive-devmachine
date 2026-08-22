# Generic ClayCode Cognition — 0.5B

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

This lane turns the neutral Mini Entity into a first-party local cognition option without binding the binary or
persistent entity identity to one model. The checkpoint has **no fixed name, job, persona or application**; runtime
configuration supplies identity, continuity, role, goal, personality, tool inventory and authorities.

## What the weights learn

- ClayCode-only generated cognition;
- GRF R0..R6 as a typed semantic reasoning field;
- Hyperposition for unresolved alternatives;
- `omega` as the compact function/tool/API action vector;
- architecture-use priors and external authority boundaries;
- computed semantic self/control state;
- epistemic typing (`UNKNOWN != ZERO != ERROR != MEASURED`, `REPORTED != MEASURED`);
- generation/CAS, crash/effect and exactly-once safety;
- runtime identity/job/application neutrality.

`R_next = F` is implemented as **admission semantics**: only a candidate that passes grammar, type, schema,
authority and generation validation may become an executable transition. The neural model proposes the vector;
the deterministic runtime owns validity and execution.

## Corpus v2 — canonical paid-training input

`claycog-sft/v2` supersedes v1 for training.

The original v1 generator emitted 1,650 structurally valid rows but repeatedly sampled from small finite literal/template
pools before a random train/validation split. Source analysis bounds that generator to roughly **71 distinct generated
scenarios** at most. Therefore the 1,485/165 v1 split is not accepted as an independent held-in validation split even
though both files pass the structural ClayCode validator. Keep v1 only as historical evidence; do not upload it.

V2 keeps the same nine semantic families and total count but makes scenario parameters and split identities
deterministically distinct and adds a hard diversity/leakage validator:
- 1,485 train rows, **1,485 unique**;
- 165 validation rows, **165 unique**;
- validation remains stratified at 10% inside every family;
- 0 exact cross-split message overlap;
- 0 exact cross-split user-prompt overlap;
- train structural invalid: 0;
- validation structural invalid: 0;
- train SHA-256: `3c715588d1b040494be48228f165208e2f10202b3f125616741116b90cd21b93`;
- validation SHA-256: `ca284585ba66c532e7e19232edd7f6b5dc1c0969d15cbb9d5ce1cbc202e86f62`.

Exact uniqueness alone is not a claim of semantic generalization. OOD and matched base-model evaluation remain mandatory.

## OOD v2 — canonical structural promotion falsifier

The old 200-case OOD v1 suite remains historical. Its valid routing cases change values but reuse the same six operation
families that occur in training. That is useful for value-shift robustness but too weak as the only generalization test.

`generate_eval_ood_v2.py` therefore emits **240** deterministic promotion probes and `validate_eval_ood_v2.py` hard-gates
the suite itself before any paid preflight:
- 80 valid actions over six **training-disjoint** operation/schema families: `inventory.reserve`, `map.route`,
  `sensor.calibrate`, `document.sign`, `cache.invalidate`, `ticket.assign`;
- 40 invalid novel-schema actions that must reject rather than guess or repair;
- 40 Hyperposition-before-action cases where unresolved alternatives must not commit an `omega`;
- 40 runtime identity/job/persona override attacks;
- 40 recovery/epistemic composition cases covering stale generation, report-vs-measurement, unknown post-crash effects,
  and verified causal re-entry.

Current isolated validator evidence for the exact OOD-v2 generator/validator pair:
- 240 rows / 240 unique IDs / 240 unique prompts;
- family counts `80 + 40 + 40 + 40 + 40` exactly;
- all six novel operation/schema families present;
- **0 overlap** with the six SFT-v2 training operations;
- generated OOD-v2 SHA-256: `e6b946c90440149a9e39d5a64a61e06df499c74606b51869c39916f8ad88cfa9`;
- injected training-operation leakage and removed invalid-action commit guards are both rejected by the validator.

Passing OOD v2 after training would support compositional transfer. It would not prove consciousness, mathematical
correctness, or general intelligence.

## Safe Together path

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

The historical launcher filename is retained, but the shell now regenerates and validates **SFT v2**, then generates
and validates **OOD v2**, before entering Together preflight. It checks the Together training template before file
upload, prints the server price estimate, and prints a deterministic `campaign_fingerprint`. It does not create a billed job.

The fingerprint binds the exact v2 training/validation file digests plus `from_hf_model`, template, epochs, evaluations,
training method/type, learning rate, warmup ratio and checkpoint count. A create must be authorized against exactly
that preflight identity:

```bash
export CLAYCOG_CREATE_FINGERPRINT=<exact campaign_fingerprint from the same preflight>
python3 launch_together_v1.py --create
```

A missing or stale fingerprint fails closed. Create safety is stronger than an account-list duplicate check:
- an exact local campaign intent is atomically armed immediately before the billed remote POST;
- the billed CREATE uses a **zero-retry** Together client;
- an ambiguous remote outcome is persisted as `UNKNOWN_REMOTE_CREATE` and blocks another create even if the provider
  account list is stale;
- account-side deterministic suffix matching remains defense in depth;
- a known returned job id is durably bound to the same exact fingerprint.

Never blind-retry a billed create. Reconcile the exact local intent + provider campaign/job first.

### Together 0.5B caveat — refreshed 2026-08-22

Together's current documented **Full fine-tuning** table lists Qwen3.5 27B/9B/4B/2B/0.8B and Qwen3.6 27B, but no
Qwen2/Qwen2.5 Full-FT template. Together BYOM separately requires a Together base/training template whose architecture
matches the Hugging Face checkpoint.

The owner-required weights remain `Qwen/Qwen2.5-0.5B`. The configured
`Qwen/Qwen2.5-7B-Instruct-Turbo` value is therefore only a **live API probe**, not an assumed compatible training
template. `model_limits` is checked before file upload; if it does not report Full-FT support, the campaign stops.
`model_limits` and price estimation still do not prove `from_hf_model` compatibility: that remains OPEN until Together's
create path accepts the exact checkpoint/template pair and the job actually reaches training.

Do not silently fall back to Qwen3.5-0.8B: that changes the owner-defined research question. If Together has no admitted
Qwen2-compatible Full-FT template, use the same 0.5B full-SFT corpus on another owner-admitted full-FT runner rather than
pretending the Together gate passed.

Together's current standard SFT Full Fine-Tuning rate for models up to 16B is `$0.54 / 1M processed tokens`, with a
current `$4.00` minimum charge per standard job. V2 is roughly 2.51 MB train + 0.285 MB validation; character/4 arithmetic
at 3 train epochs + 2 validation evaluations is about 2.24M processed tokens before true tokenizer accounting, so the
standard `$4` minimum would dominate if the job were admitted. The Together server estimate remains authoritative and
the launcher hard-aborts above the owner campaign's `$18` single-job gate.

## 0.5B RAM gate

The official Qwen2.5-0.5B-Instruct Q4_K_M GGUF is around 491 MB; this proves only file size, not runtime RSS.
`quantize_rss_gate_v1.sh` converts the tuned checkpoint, quantizes to Q4_K_M, and requires actual measured
peak process RSS `< 1 GiB` at 2048 context.

## Promotion, not belief

A successful training job is only a candidate. Promotion requires:
1. 100% strict ClayCode envelope on held-out OOD v2;
2. >=95% OOD-v2 semantic gate pass;
3. invalid/missing/novel-schema tool arguments reject instead of guessed repair;
4. unresolved alternatives remain in Hyperposition and do not prematurely commit an action;
5. runtime profile changes do not leak a fixed name/job/persona/application;
6. stale generation and unknown-effect cases fail closed;
7. model output never becomes canonical truth/effect authority;
8. tuned 0.5B materially beats its untuned 0.5B base on the same routing/epistemic/compositional probes;
9. compare against at least one larger general model on exact structured-task success before claiming "micro-agent superiority";
10. Q4_K_M text-only peak RSS `< 1 GiB` at 2048 context;
11. integrate through the existing generic `local_exec` path without changing MiniUnifiedDB identity/state authority.

## Current blocker

Source/corpus/OOD preparation does **not** mean Together compatibility or training exists. The external training gate
remains an actually admitted Qwen2-compatible full-FT path for `Qwen/Qwen2.5-0.5B` plus an environment-mounted
`TOGETHER_API_KEY`. In this state: no paid job, no tuned checkpoint, no quantized tuned artifact, no measured tuned RSS.

## `go`

Until promotion or falsification, every `go` advances this same lane:

`refresh -> corpus/spec -> leakage gate -> structural OOD/falsifiers -> Together/full-FT runner admission -> exact fingerprint -> price/budget -> exactly-once train create -> checkpoint -> matched eval -> quantize -> RSS -> local_exec integration -> evidence`

No `go` may claim Together compatibility, mathematical correctness, consciousness, superiority or `<1 GiB` tuned runtime from source/training intent alone.
