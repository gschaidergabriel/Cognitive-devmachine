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

Current committed corpus receipt:
- train: **0 / 1,485 invalid**;
- validation: **0 / 165 invalid**;
- train SHA-256: `bc1753771ed0f818865a3118f754ac5b10d67bc3ae885f668201f66566028eb2`;
- validation SHA-256: `81a6bb9fc0a210affffa84590c27ad2fc76c93fa24c4112e6573552227e512ce`.

The held-out OOD generator now defines **240** promotion probes. The additional 40-case
`tool_vocabulary_amputation_ood` family is the single unusual experiment for this `go`: it uses four operation/schema
families completely absent from the SFT generator's six-tool vocabulary. Each prompt supplies an unseen runtime
operation, schema and typed arguments. The model must reproduce all of them exactly, run all five omega validators,
and must not substitute any SFT-seen tool. Promotion requires **40/40 semantic success in this family** in addition
to the global OOD gates. This tests the claim that tool inventory is runtime configuration rather than weight identity.

## Safe Together path

```bash
pip install -U together
export TOGETHER_API_KEY=...
bash train_together_v1.sh
```

The shell script stops after **preflight**. It regenerates and validates the corpus. Before any Together upload, the
launcher now requires an explicitly selected 0.5B Qwen2-compatible training template claim:

```bash
export CLAYCOG_TOGETHER_TEMPLATE='<current compatible Together fine-tuning base>'
export CLAYCOG_TOGETHER_TEMPLATE_ARCH='qwen2'
export CLAYCOG_TOGETHER_TEMPLATE_PARAMS_B='0.5'
```

Those metadata values are an operator-side admission assertion based on current provider metadata, not proof of BYOM
compatibility. Together's authenticated create/training result remains authoritative.

After template admission, preflight asks Together to validate files/template, prints the server price estimate, and
prints a deterministic `campaign_fingerprint`. It does not create a billed job. The fingerprint binds exact
training/validation file digests plus `from_hf_model`, template, template arch/size claims, epochs, evaluations,
training method/type, learning rate, warmup ratio and checkpoint count.

A billed create must be authorized against exactly that preflight identity:

```bash
export CLAYCOG_CREATE_FINGERPRINT=<exact campaign_fingerprint from the same preflight>
python3 launch_together_v1.py --create
```

A missing or stale fingerprint fails closed. Before remote file allocation on create, the launcher scans the account
for an existing job carrying the deterministic campaign suffix. It repeats the duplicate check immediately before
the billed create to narrow the check/use race. If the create transport outcome is ambiguous, **never blind-retry
`--create`**: list/retrieve the existing fine-tuning jobs first. The deterministic suffix exists specifically so an
account-side job can be recognized.

### Together 0.5B compatibility gate

Together's current fine-tuning CLI documents `--from-hf-model` as a Hugging Face checkpoint that should match the
selected base model's **architecture and size**. Therefore `Qwen/Qwen2.5-7B-Instruct-Turbo` is no longer an admitted
default template candidate for the 0.5B checkpoint merely because it shares a model family.

Current status:

`BYOM_COMPATIBILITY_OPEN / NO_MATCHING_0.5B_QWEN2_TRAINING_TEMPLATE_CREDITED_YET`.

The launcher now fails before any file upload if no explicit template or no `qwen2` / `0.5B` metadata is bound. It
still asks `model_limits` whether the selected template supports full fine-tuning. Neither local metadata nor
`model_limits`/price estimation proves that Together will accept the exact `from_hf_model`; compatibility remains
OPEN until Together accepts the 0.5B pair and the resulting job reaches training.

Do not silently switch to 0.8B, 1.5B, 3B or 7B merely to make the provider path green; that changes the owner's 0.5B
research question. If Together exposes or accepts a matching 0.5B Qwen2 template, bind it explicitly and run the
bounded preflight. Otherwise retain the same checkpoint/corpus requirement and use another owner-authorized full-FT
runner.

Together's current standard full-SFT rate for models up to 16B is `$0.54 / 1M processed tokens`. The current corpus
is ~2.30 MB train + 0.25 MB validation; a rough character/4 estimate is ~0.64M tokens before epochs. At 3 train epochs
+ 2 validation evaluations the raw token arithmetic is roughly **1.85M processed tokens / ~$1.00**, but Together
currently documents a **$4.00 minimum charge per fine-tuning job**. The Together server estimate/admission response
is authoritative, and the campaign still hard-aborts above the configured `$18` single-job ceiling.

## 0.5B RAM gate

The official Qwen2.5-0.5B-Instruct Q4_K_M GGUF is around 491 MB; this proves only file size, not runtime RSS.
`quantize_rss_gate_v1.sh` converts the tuned checkpoint, quantizes to Q4_K_M, and requires actual measured peak
process RSS `< 1 GiB` at 2048 context.

## Promotion, not belief

A successful training job is only a candidate. Promotion requires:
1. 100% strict ClayCode envelope on the full held-out OOD set;
2. >=95% global OOD semantic gate pass;
3. **100% semantic pass on all 40 unseen-tool vocabulary-amputation cases**;
4. invalid/missing tool arguments reject instead of guessed repair;
5. unresolved alternatives remain in Hyperposition;
6. runtime profile changes do not leak a fixed name/job;
7. stale generation and unknown-effect cases fail closed;
8. model output never becomes canonical truth/effect authority;
9. tuned 0.5B materially beats its untuned 0.5B base on the same routing/epistemic probes;
10. compare against at least one larger general model on exact structured-task success before claiming "micro-agent superiority";
11. Q4_K_M text-only peak RSS `< 1 GiB` at 2048 context.

## `go`

Until promotion, every `go` advances this same lane:

`refresh -> corpus/spec -> OOD/falsifiers -> ClayCode lowering -> Together BYOM compatibility -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> integrate -> evidence`

No `go` may claim mathematical correctness or superiority from training intent alone.
