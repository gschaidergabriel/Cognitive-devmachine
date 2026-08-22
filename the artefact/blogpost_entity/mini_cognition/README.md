# Generic ClayCode Cognition v1 — 0.5B

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

This lane turns the existing neutral Mini Entity into a first-party local cognition option without binding the
binary or persistent entity identity to one model. The checkpoint has **no fixed name or job**; runtime configuration
supplies identity, continuity, role, goal, personality, tool inventory and authorities.

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

The separate 200-case OOD promotion suite remains distinct from this held-in validation split. Exact uniqueness alone is
not a claim of semantic generalization; OOD and matched base-model evaluation remain mandatory.

## Safe Together path

```bash
pip install -U together
export TOGETHER_API_KEY=...
# Required. Set only after current Together verification identifies a Qwen2-compatible
# Full-FT training template. There is deliberately no implicit template default.
export CLAYCOG_TOGETHER_TEMPLATE=...
bash train_together_v1.sh
```

The historical launcher filename is retained, but it now regenerates and validates **SFT v2 only**. The shell stops
after **preflight**. Before any file upload, the launcher requires an explicit template, rejects a Qwen3-family
substitution, and asks Together `model_limits` whether the supplied template supports Full fine-tuning. It then prints
the server price estimate and a deterministic `campaign_fingerprint`. It does not create a billed job.

The fingerprint binds the exact v2 training/validation file digests plus `from_hf_model`, **`hf_model_revision`**,
template, epochs, evaluations, training method/type, learning rate, warmup ratio and checkpoint count. A create must be
authorized against exactly that preflight identity:

```bash
export CLAYCOG_CREATE_FINGERPRINT=<exact campaign_fingerprint from the same preflight>
python3 launch_together_v1.py --create
```

A missing or stale fingerprint fails closed. Before remote file allocation on create, the launcher scans the account
for an existing job carrying the deterministic campaign suffix. It repeats the duplicate check immediately before
the billed create to narrow the check/use race. The billed POST uses a zero-retry client and an atomic local create-intent
ledger. If the create transport outcome is ambiguous, the local ledger remains `UNKNOWN_REMOTE_CREATE`; **never blind-retry
`--create`** until the exact provider state is reconciled.

### Exact Hugging Face source identity

The default BYOM source is pinned to an exact Hugging Face commit instead of moving repository `main`:

- `Qwen/Qwen2.5-0.5B` -> `060db6499f32faf8b98477b0a26969ef7d8b9987`;
- `Qwen/Qwen2.5-0.5B-Instruct` -> `7ae557604adf67be50417f59c2c2f167def9a775`.

The selected revision is part of the campaign fingerprint, persisted inside the local create-intent campaign descriptor,
emitted in preflight/create evidence, and passed to Together as `hf_model_revision`. Changing only the model revision
therefore produces a different paid-campaign identity. A custom `CLAYCOG_HF_MODEL` requires an exact 40-hex
`CLAYCOG_HF_REVISION`; the instruct equivalents are `CLAYCOG_INSTRUCT_HF_MODEL` and
`CLAYCOG_INSTRUCT_HF_REVISION`. Missing or malformed revisions fail closed.

### Together 0.5B caveat — refreshed 2026-08-22

Together's current documented **Full fine-tuning** table lists Qwen3.5 27B/9B/4B/2B/0.8B and Qwen3.6 27B, but no
Qwen2/Qwen2.5 Full-FT template. Together BYOM separately requires a Together base/training template whose architecture
matches the Hugging Face checkpoint; its guidance says to choose the closest available compatible size/context, not to
force exact parameter-count equality.

The owner-required weights remain `Qwen/Qwen2.5-0.5B`. `Qwen/Qwen2.5-7B-Instruct-Turbo` is currently documented as a
serverless inference model, which is **not** evidence that it is admitted by the fine-tuning API. It is therefore no
longer an implicit launcher probe/default. A Qwen2-compatible candidate must be supplied explicitly after current
verification, and `model_limits` must accept Full fine-tuning before any dataset upload. Even then, `model_limits` and
price estimation still do not prove `from_hf_model` compatibility: that remains OPEN until Together's create path
accepts the exact checkpoint/revision/template tuple and the job actually reaches training.

Do not silently fall back to Qwen3.5-0.8B. The current Qwen2.5-0.5B configuration is `Qwen2ForCausalLM` / `qwen2`,
whereas Qwen3.5-0.8B is `Qwen3_5ForConditionalGeneration` / `qwen3_5`; an automatic fallback changes the architecture
family and the owner-defined research question. If Together has no admitted Qwen2-compatible Full-FT template, use the
same 0.5B full-SFT corpus on another owner-admitted full-FT runner.

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
1. 100% strict ClayCode envelope on held-out OOD;
2. >=95% OOD semantic gate pass;
3. invalid/missing tool arguments reject instead of guessed repair;
4. unresolved alternatives remain in Hyperposition;
5. runtime profile changes do not leak a fixed name/job;
6. stale generation and unknown-effect cases fail closed;
7. model output never becomes canonical truth/effect authority;
8. tuned 0.5B materially beats its untuned 0.5B base on the same routing/epistemic probes;
9. compare against at least one larger general model on exact structured-task success before claiming "micro-agent superiority";
10. Q4_K_M text-only peak RSS `< 1 GiB` at 2048 context.

## `go`

Until promotion, every `go` advances this same lane:

`refresh -> corpus/spec -> OOD/falsifiers -> ClayCode lowering -> Together/full-FT runner admission -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> integrate -> evidence`

No `go` may claim mathematical correctness, consciousness or superiority from training intent alone.
