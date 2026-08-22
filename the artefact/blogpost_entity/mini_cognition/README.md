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

## Fast path

```bash
pip install -U 'together>=2'
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

The shell script stops after **preflight**. It regenerates and validates the corpus, validates/uploads the files,
checks current full-training limits for the requested base/template, and prints the server price estimate. It does
not create a billed job.

Only after a clean preflight:

```bash
python3 launch_together_v1.py --create
```

`--create` is intentionally a separate, exactly-once transition. Persist the returned job id and retrieve that job;
do not blindly repeat creation after a timeout or ambiguous client failure.

### Together 0.5B BYOM gate — corrected SDK-v2 path

Together's current SDK and fine-tuning documentation expose a BYOM path through `from_hf_model`. The SDK documents
that the Together `model` argument used as the training base/template should be as close as possible to the
Hugging Face checkpoint in **architecture and size**. Therefore the launcher no longer guesses a 7B Qwen2.5 model
for a 0.5B checkpoint.

Default pairing is now exact and fail-closed:

- BYOM checkpoint: `Qwen/Qwen2.5-0.5B`;
- Together base/template candidate: `Qwen/Qwen2.5-0.5B` itself;
- instruct ablation: exact `Qwen/Qwen2.5-0.5B-Instruct` / same-model pairing.

If Together's live `fine-tunes/models/limits` endpoint does not admit that exact model for full training, preflight
stops. A different candidate may be supplied explicitly through `--template` or `CLAYCOG_TOGETHER_TEMPLATE`, but
there is no automatic larger-model fallback. An explicit override remains a hypothesis until Together accepts it.

The launcher is locked to the current Together Python SDK v2 contract:
- `client.fine_tuning.get_model_limits(model=...)`;
- full training iff `limits.full_training` is present;
- file readiness through current `FileResponse.processed` (legacy status is fallback only);
- `estimate_price(..., training_type="full", training_method="sft")`;
- BYOM creation through `model=...` + `from_hf_model=...`, `lora=False`.

**Important evidence boundary:** preflight can prove local corpus validity, Together file processing, current template
limits and price/budget admission. It cannot prove that Together will accept the particular BYOM checkpoint. That
compatibility gate is only crossed when the single billed `create` request is accepted. A rejected create is a
useful falsification and must not trigger an automatic retry or a silent model-size change.

Together's current standard full-SFT rate for models up to 16B is `$0.54 / 1M processed tokens`, with a documented
**$4.00 minimum charge per fine-tuning job**. The current corpus is ~2.30 MB train + 0.25 MB validation; a rough
character/4 estimate is ~0.64M tokens before epochs. At 3 train epochs + 2 validation evaluations, raw token
arithmetic is roughly **1.85M processed tokens / ~$1.00**, so the minimum charge is likely to dominate. The Together
server estimate remains authoritative, and the launcher hard-aborts above the configured `$18` single-job ceiling.

## No-network launcher regression

Run before any paid preflight:

```bash
python3 test_launch_together_v2_contract.py
```

This uses a v2-only fake client and no secret/network. It rejects regressions to the old `model_limits`,
`supports_full_training`, dict estimate arguments or `processing_status`-only surface. Its bounded API-surface
collision falsifier also proves the preflight helpers never call `create` implicitly.

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
