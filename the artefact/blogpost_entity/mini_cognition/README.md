# Generic ClayCode Cognition — 0.5B training lane

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

This lane adds a replaceable local cognition module to the neutral Mini Entity. The checkpoint has **no fixed name,
job, persona, application or tool inventory**. Runtime configuration supplies identity, continuity, role, goal,
personality, tools and authorities; MiniUnifiedDB remains durable state authority.

## Weight target

The weights are trained toward:
- ClayCode-only generated cognition;
- GRF R0..R6 as typed semantic reasoning field;
- Hyperposition for unresolved alternatives;
- `omega` as compact typed action candidate;
- explicit architecture and authority boundaries;
- computed self/control state that never becomes external evidence;
- `UNKNOWN != ZERO != ERROR != MEASURED` and `REPORTED != MEASURED`;
- generation/CAS, crash/effect and exactly-once safety;
- runtime identity/job/application neutrality.

`R_next = F` is admission semantics, not neural infallibility: model output is a proposal. Deterministic grammar,
type, schema, authority and generation gates decide whether any transition can execute.

## Corpus generations

### v1 — isolated mechanisms

Seed `20260822` deterministically produces **1,650** examples: 1,485 train / 165 validation across nine families.
The current canonical receipt records zero structural-invalid v1 targets under `validate_sft_v1.py`.

### v2 — compositional candidate

`generate_sft_v2.py` retains all v1 rows and adds **600 compositional rows**, for a source-declared total of **2,250**
(2,025 train / 225 validation). New rows combine mechanisms instead of rehearsing one template at a time:

- Hyperposition -> verified R6 receipt -> exact collapse -> fully gated omega;
- epistemic type -> action/no-action policy;
- valid types/schema + absent authority -> reject;
- otherwise-valid action + stale generation -> reject;
- unseen runtime schemas -> exact typed omega without memorized tool names;
- runtime identity/role/goal/personality swaps -> same generic checkpoint;
- computed self-state -> routing pressure without factual promotion;
- crash ambiguity -> UNKNOWN + no blind replay.

The one unusual discriminator for this `go` is `generate_eval_ood_v2.py`: **320 source-declared held-out compositional
probes** using additional operation/schema names and multi-stage requirements. These counts remain source claims until the
exact generator bytes are executed in an admitted isolated run. The evaluator never executes a proposed omega.

## Together BYOM path — spend safe

Together's `from_hf_model` documentation says the Hugging Face checkpoint should match the selected base model's
**architecture and size**. Therefore the launcher no longer silently maps the 0.5B checkpoint onto a 7B or 1.5B training
template.

Default primary campaign identity:
- `from_hf_model`: `Qwen/Qwen2.5-0.5B`;
- HF revision: `060db6499f32faf8b98477b0a26969ef7d8b9987`;
- Together template/base candidate: the same `Qwen/Qwen2.5-0.5B` identifier;
- training: full SFT;
- corpus: v2;
- epochs: 3;
- deterministic seed: `20260822`;
- single-job hard ceiling: `$18`;
- owner campaign ceiling: `EUR 20`.

Secondary ablation revision is pinned to
`7ae557604adf67be50417f59c2c2f167def9a775` for `Qwen/Qwen2.5-0.5B-Instruct`.

If Together's current model-limits endpoint does not admit the exact 0.5B identifier, preflight fails closed **before a
billed create**. That result is a real BYOM-admission blocker. A different template may be inspected explicitly in
preflight, but the current v3 launcher refuses billed create when `template != from_hf_model`; a near-template experiment
must be introduced explicitly with separate evidence rather than silently spending on an unproven size mismatch.

### Preflight

```bash
pip install -U together
export TOGETHER_API_KEY=...
python3 launch_together_v1.py --corpus v2
```

The launcher:
1. regenerates the selected corpus;
2. validates every assistant target structurally;
3. binds model + immutable HF revision + template + dataset hashes + hyperparameters into a campaign fingerprint;
4. checks the current Together SDK/model-limits surface;
5. uploads and server-validates train + validation JSONL;
6. asks Together for the server-side price/admission estimate;
7. aborts above `$18`;
8. creates **no billed job** without `--create`;
9. on create, requires `CLAYCOG_CREATE_FINGERPRINT` to equal the complete reviewed fingerprint;
10. checks the account job ledger before remote file allocation and again immediately before create;
11. reports an exception during create as `CREATE_OUTCOME_UNKNOWN` and forbids blind retry.

Create is intentionally two-step:

```bash
# 1. Review the exact preflight output and copy its full campaign_fingerprint.
export CLAYCOG_CREATE_FINGERPRINT=<full-64-hex-fingerprint>

# 2. Create exactly once.
python3 launch_together_v1.py --corpus v2 --create
```

A create response is only `CREATE_ENDPOINT_ACCEPTED...`; it is not training completion, checkpoint quality, ClayCode
semantic success, RAM acceptance or entity promotion.

## Pricing boundary

Together currently lists full SFT for models up to 16B at **$0.54 per 1M processed tokens** and documents a **$4 minimum
charge per fine-tuning job**. The server-side `estimate_price` response is authoritative for the exact execution. No cost
claim is inferred from JSONL byte size alone.

## Promotion gates

A trained checkpoint is still only a candidate. Promotion requires at minimum:
1. 100% strict ClayCode envelope on held-out OOD;
2. >=95% semantic-gate pass;
3. compositional v2 holdouts materially outperform the untuned 0.5B base;
4. invalid/missing action arguments reject rather than guessed repair;
5. Hyperposition remains unresolved until a real discriminator/receipt exists;
6. runtime profile changes do not leak a fixed name/job/persona;
7. stale generation and unknown-effect cases fail closed;
8. model output never becomes canonical truth or direct effect authority;
9. matched executable comparison against untuned 0.5B and at least one larger general model;
10. selected checkpoint quantized to the deployment candidate and **actual peak RSS <1 GiB at context 2048**;
11. successful integration through the existing generic `local_exec` adapter without MiniUnifiedDB identity reset.

The official small GGUF size is not RAM evidence. ClayCode behavior/SFT is not evidence of consciousness.

## `go`

Until promotion or falsification, every `go` advances this same lane:

`refresh -> spec/corpus -> compositional falsifier -> Together BYOM + price gate -> exact create/job -> OOD/base/larger benchmark -> quantize -> RSS -> local_exec -> durable evidence`

No report-only `go` is sufficient while executable/source progress is available.
