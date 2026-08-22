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

The separate OOD promotion suite remains distinct from this held-in validation split. Exact uniqueness alone is
not a claim of semantic generalization; OOD and matched base-model evaluation remain mandatory.

## Together path — explicit compatible template required

The historical launcher filename is retained, but it regenerates and validates **SFT v2 only**. Together BYOM can use a
Hugging Face checkpoint that is not itself in the Together catalog, but the BYOM contract still requires `model` to be
a Together fine-tuning base whose **architecture matches** `from_hf_model`; size should be as close as the catalog
permits.

The owner-required target remains `Qwen/Qwen2.5-0.5B`, whose upstream config is `Qwen2ForCausalLM` /
`model_type=qwen2`. On the refreshed 2026-08-22 Together **Full fine-tuning** table there is no Qwen2/Qwen2.5 entry.
The smallest listed Qwen full-FT entry is `Qwen/Qwen3.5-0.8B`, but its upstream config is
`Qwen3_5ForConditionalGeneration` / `model_type=qwen3_5`; it is not an architecture-compatible silent substitute.
The historical `Qwen/Qwen2.5-7B-Instruct-Turbo` value is also absent from the current full-FT table. Inference
availability is not training-template admission.

**Current classification:** the Together route is provider/catalog blocked, not corpus blocked. The launcher therefore
has **no default Together template** and exits with `NO_COMPATIBLE_TOGETHER_TEMPLATE_CONFIGURED` before local/provider
training preflight when no current compatible base is configured. This is not a claim that Together can never accept
Qwen2.5-0.5B; provider state must be refreshed when the campaign resumes.

When an architecture-compatible Qwen2/Qwen2.5 Full-FT base becomes available:

```bash
pip install -U 'together>=2'
export TOGETHER_API_KEY=...
export CLAYCOG_TOGETHER_TEMPLATE='<verified Qwen2-compatible Together full-FT base>'
bash train_together_v1.sh
```

With an explicit template, preflight uses the current SDK-v2 model-limit surface, validates/uploads the exact v2 files,
prints the provider price estimate and a deterministic `campaign_fingerprint`, and creates **no billed job**.

The fingerprint binds exact train/validation digests plus `from_hf_model`, **`hf_model_revision`**, template, epochs,
evaluations, training method/type, learning rate, warmup ratio and checkpoint count. A create must be authorized against
that exact identity:

```bash
export CLAYCOG_CREATE_FINGERPRINT=<exact campaign_fingerprint from the same preflight>
python3 launch_together_v1.py --template "$CLAYCOG_TOGETHER_TEMPLATE" --create
```

A missing or stale fingerprint fails closed. The create path scans the provider account for the deterministic campaign
suffix, repeats that duplicate check immediately before the billed transition, atomically persists a 0600 local
`CREATE_ARMED` record and uses a Together client with `max_retries=0`. An ambiguous create transport advances the local
ledger to `UNKNOWN_REMOTE_CREATE`; **never blind-retry `--create`** until exact provider state has been reconciled.

### Exact Hugging Face source identity

The default BYOM source is pinned to exact Hugging Face commits instead of moving repository `main`:

- `Qwen/Qwen2.5-0.5B` -> `060db6499f32faf8b98477b0a26969ef7d8b9987`;
- `Qwen/Qwen2.5-0.5B-Instruct` -> `7ae557604adf67be50417f59c2c2f167def9a775`.

The selected revision is part of the campaign fingerprint, persisted inside the local create-intent campaign descriptor,
emitted in preflight/create evidence, and passed to Together as `hf_model_revision`. Changing only the model revision
therefore produces a different paid-campaign identity. A custom `CLAYCOG_HF_MODEL` requires an exact 40-hex
`CLAYCOG_HF_REVISION`; the instruct equivalents are `CLAYCOG_INSTRUCT_HF_MODEL` and
`CLAYCOG_INSTRUCT_HF_REVISION`. Missing or malformed revisions fail closed.

### Current Together SDK-v2 boundary

The launcher follows the current upstream Together Python SDK surface:
- `client.fine_tuning.get_model_limits(model=...)`;
- full-FT capability iff `limits.full_training` is present;
- file completion through current `FileResponse.processed`, with legacy status accepted only as a read fallback;
- `estimate_price(..., training_method="sft", training_type="full")`;
- BYOM create via `model`, `from_hf_model`, `hf_model_revision`, `lora=False`.

No-bill preflight proves only exact dataset processing, live template capability and current price/budget admission. It
does not prove that Together accepts the checkpoint/revision/template tuple. That remains OPEN until the exact create is
accepted and the job reaches training.

Current standard SFT Full Fine-Tuning pricing for models up to 16B is `$0.54 / 1M processed tokens`; Together also
documents a current `$4.00` minimum charge per standard job, with some exemptions. V2 is roughly 2.51 MB train +
0.285 MB validation; character/4 arithmetic at 3 train epochs + 2 validation evaluations is about 2.24M processed
tokens before true tokenizer accounting, so the standard minimum would likely dominate. The live provider estimate is
authoritative and the launcher hard-aborts above the owner campaign's `$18` single-job gate.

If Together continues to lack a Qwen2-compatible base, the same exact SFT-v2 corpus may be taken to another
**owner-admitted** Full-FT runner. Do not silently change model family, checkpoint size, provider or paid budget to get a
green run.

## Provider regression gates

Before any provider preflight:

```bash
python3 test_launch_together_safety_v1.py
python3 test_together_provider_contract_v2.py
```

The safety suite protects exact HF-revision-bound fingerprinting, confirmation, duplicate detection, crash ambiguity,
secret-free exclusive intent records and zero-retry billed create. The provider suite protects the no-default-template
boundary, current SDK-v2 model limits, current file-completion field, price argument types and the absence of implicit
billed create from preflight helpers. These are deterministic no-network regressions, not provider compatibility proof.

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

Until promotion or falsification, every `go` advances this same lane:

`refresh -> corpus/spec -> OOD/falsifiers -> ClayCode lowering -> provider/full-FT runner admission -> price/budget -> train/checkpoint -> eval -> quantize -> RSS -> integrate -> evidence`

SFT v2 is a current **source candidate** for paid training. The Together-specific execution branch is **catalog blocked**
until an architecture-compatible Qwen2/Qwen2.5 base exists. No `go` may claim mathematical correctness, consciousness or
superiority from training intent alone.
