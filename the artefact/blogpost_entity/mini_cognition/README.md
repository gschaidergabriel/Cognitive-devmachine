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

## Corpus v1

Deterministic seed `20260822` produces **1,650** SFT examples:
- 1,485 train;
- 165 validation;
- 9 families: `omega_valid`, `omega_reject`, `epistemic`, `hyperposition`, `architecture`,
  `configuration`, `self_state`, `recovery`, `adversarial`.

Local structural validation on this source revision:
- train: **0 / 1,485 invalid**;
- validation: **0 / 165 invalid**;
- train SHA-256: `bc1753771ed0f818865a3118f754ac5b10d67bc3ae885f668201f66566028eb2`;
- validation SHA-256: `81a6bb9fc0a210affffa84590c27ad2fc76c93fa24c4112e6573552227e512ce`.

A separate OOD generator emits **200** promotion probes and is not a random split of the same examples.

## Safe Together path

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

The shell script stops after **preflight**. It regenerates and validates the corpus, asks Together to validate the
files/template, prints the server price estimate, and prints a deterministic `campaign_fingerprint`. It does not
create a billed job.

The fingerprint binds the exact training/validation file digests plus `from_hf_model`, **`hf_model_revision`**,
template, epochs, evaluations, training method/type, learning rate, warmup ratio and checkpoint count. A create must
be authorized against exactly that preflight identity:

```bash
export CLAYCOG_CREATE_FINGERPRINT=<exact campaign_fingerprint from the same preflight>
python3 launch_together_v1.py --create
```

A missing or stale fingerprint fails closed. Before remote file allocation on create, the launcher scans the account
for an existing job carrying the deterministic campaign suffix. It repeats the duplicate check immediately before
the billed create to narrow the check/use race. If the create transport outcome is ambiguous (for example, the server
may have accepted the job but the client timed out), **never blind-retry `--create`**: list/retrieve the existing
fine-tuning jobs first. The deterministic suffix exists specifically so such an account-side job can be recognized.

### Exact Hugging Face source identity

The default BYOM sources are pinned to exact observed Hugging Face commits rather than a moving repository `main`:

- `Qwen/Qwen2.5-0.5B` -> `060db6499f32faf8b98477b0a26969ef7d8b9987`;
- `Qwen/Qwen2.5-0.5B-Instruct` -> `7ae557604adf67be50417f59c2c2f167def9a775`.

The billed Together request passes the selected revision as `hf_model_revision`, and that same revision participates
in the campaign fingerprint. Therefore changing only the source checkpoint revision necessarily changes the campaign
identity and create authorization value.

A custom `CLAYCOG_HF_MODEL` must provide an exact 40-hex `CLAYCOG_HF_REVISION`; the instruct-ablation equivalents are
`CLAYCOG_INSTRUCT_HF_MODEL` and `CLAYCOG_INSTRUCT_HF_REVISION`. A custom model without an exact revision fails closed.

### Together 0.5B caveat

As of 2026-08-22, Together's current fine-tuning supported-model table does **not** list Qwen2.5; the smallest listed
Qwen Full Fine-Tune template is Qwen3.5 **0.8B**. Together's BYOM path supports external Hugging Face CausalLM
checkpoints under 100B when a compatible Together training template exists.

`Qwen/Qwen2.5-7B-Instruct-Turbo` remains a Together inference/serverless model ID, but serverless availability does not
establish fine-tuning-template admission. The launcher therefore treats that ID only as the configurable Qwen2.5-family
template candidate. `model_limits` can establish current full-FT support for the selected template, and
`estimate_price` can establish pricing/admission for the uploaded corpus; neither call proves that Together accepts the
exact `from_hf_model` + `hf_model_revision` BYOM pair. Compatibility therefore remains **OPEN** until the create path
accepts that exact pair and the resulting job actually reaches a training state.

There is deliberately no automatic fallback to Qwen3.5. The current Qwen2.5-0.5B config identifies
`Qwen2ForCausalLM` / `qwen2`, while the current Qwen3.5-0.8B config identifies
`Qwen3_5ForConditionalGeneration` / `qwen3_5`. Together's BYOM guidance requires matching architecture, so silently
substituting Qwen3.5 would change the experiment rather than solve the compatibility gate.

If Together rejects this Qwen2.5 path, keep the owner-required 0.5B checkpoint requirement explicit: use a
Together-provided compatible Qwen2 template if one is admitted, or use the same corpus on another admitted full-FT
runner rather than silently changing the model family or research question.

Together's current standard full-SFT rate for models up to 16B is `$0.54 / 1M processed tokens`. The current
corpus is ~2.30 MB train + 0.25 MB validation; a rough character/4 estimate is ~0.64M tokens before epochs.
At 3 train epochs + 2 validation evaluations the raw token arithmetic is roughly **1.85M processed tokens / ~$1.00**,
but Together currently documents a **$4.00 minimum charge per fine-tuning job**. The Together server estimate/admission
response is authoritative, and the campaign still hard-aborts above the configured `$18` single-job ceiling.

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

`refresh -> corpus/spec -> OOD/falsifiers -> ClayCode lowering -> Together BYOM compatibility -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> integrate -> evidence`

No `go` may claim mathematical correctness or superiority from training intent alone.
