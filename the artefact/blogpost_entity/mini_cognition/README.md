# Generic ClayCode Cognition — 0.5B training lane

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

The checkpoint is a replaceable cognition module for the neutral Mini Entity. It has **no fixed name, job, persona,
application or tool inventory**. Runtime configuration supplies identity, continuity, role, goal, personality, tools
and authorities; MiniUnifiedDB remains durable state authority.

## Target representation

The weights are trained toward:
- ClayCode-only generated cognition;
- GRF R0..R6 as a typed semantic reasoning field;
- Hyperposition for unresolved alternatives;
- typed `omega` action candidates;
- explicit architecture and external-authority boundaries;
- computed self/control state that never becomes external evidence;
- `UNKNOWN != ZERO != ERROR != MEASURED` and `REPORTED != MEASURED`;
- generation/CAS, crash/effect and exactly-once safety;
- runtime identity/job/application neutrality.

`R_next = F` is admission semantics, not a neural correctness claim. The model proposes; deterministic grammar, type,
schema, authority and generation gates decide whether any transition can execute.

## Corpora

### v1 — isolated mechanisms

Seed `20260822` produces **1,650** examples: 1,485 train / 165 validation across nine mechanism families. The canonical
v1 receipt records zero structural-invalid targets and binds the exact train/validation SHA-256 values.

### v2 — compositional candidate

`generate_sft_v2.py` retains all v1 examples and adds **600 compositional examples**, for an asserted total of **2,250**
(2,025 train / 225 validation). New rows require multiple mechanisms in one turn:

- Hyperposition -> verified R6 receipt -> exact collapse -> fully gated omega;
- epistemic type -> action/no-action policy;
- valid schema/types but absent authority -> reject;
- otherwise-valid action with stale generation -> reject;
- unseen runtime operation schemas -> exact typed omega without memorized tool names;
- runtime identity/role/goal/personality swaps -> same generic checkpoint;
- computed self-state -> routing pressure without factual promotion;
- crash ambiguity -> UNKNOWN + no blind replay.

The one unusual discriminator for this `go` is `generate_eval_ood_v2.py`: **320 held-out compositional probes** using
additional operation/schema names and multi-stage requirements. Source-declared counts are not runtime evidence until the
exact branch generator executes; the PR admission runner now regenerates and checks them.

## Together BYOM — spend-safe path

Together documents `from_hf_model` as a Hugging Face starting checkpoint that should match the selected base model's
**architecture and size**. Therefore the launcher no longer silently pairs the 0.5B checkpoint with a 7B or 1.5B base.

Default primary campaign:
- `from_hf_model`: `Qwen/Qwen2.5-0.5B`;
- immutable HF revision: `060db6499f32faf8b98477b0a26969ef7d8b9987`;
- default Together template: the same `Qwen/Qwen2.5-0.5B` identifier;
- full SFT, v2 corpus, 3 epochs, deterministic seed `20260822`;
- single-job hard ceiling `$18`;
- owner campaign ceiling `EUR 20`.

The Instruct ablation is pinned to revision `7ae557604adf67be50417f59c2c2f167def9a775`.

If Together's current model-limits endpoint does not admit the exact 0.5B identifier, preflight fails closed before a
billed CREATE. That is a real compatibility result, not permission to silently substitute a larger template. Explicit
alternate templates can be inspected with `--template` in preflight, but current billed create refuses
`template != from_hf_model` until a separate evidence-backed compatibility rule is admitted.

### Preflight

```bash
pip install -U together
export TOGETHER_API_KEY=...
python3 launch_together_v1.py --corpus v2
```

Preflight:
1. regenerates the selected corpus;
2. validates assistant targets structurally;
3. binds model + immutable revision + template + dataset hashes + corpus generation + hyperparameters into one campaign fingerprint;
4. checks the current Together SDK/model-limits surface;
5. uploads and server-validates train + validation files;
6. obtains the server price/admission estimate;
7. aborts above `$18`;
8. creates no billed job without `--create`.

Create requires the exact reviewed fingerprint:

```bash
export CLAYCOG_CREATE_FINGERPRINT=<full-64-hex-preflight-fingerprint>
python3 launch_together_v1.py --corpus v2 --create
```

Paid-create safety is stronger than an account-list check:
- the launcher checks the provider job ledger before and immediately before create;
- an atomic local `0600` create-intent record reserves the exact campaign;
- the billed CREATE uses a Together client with automatic retries disabled;
- any exception after the intent is armed becomes `UNKNOWN_REMOTE_CREATE`;
- subsequent create attempts fail closed until the exact provider state is reconciled;
- no API key/token is written to the local intent ledger.

A create response is not training completion, model quality, semantic promotion or RAM evidence.

## Pricing

Together's current standard table lists full SFT up to 16B at **$0.54 per 1M processed tokens** and its current fine-tune
pricing documentation applies a **$4 minimum charge per job**. The live server estimate wins over local token/byte guesses.

## Promotion gates

A trained checkpoint is only a candidate. Promotion requires at minimum:
1. 100% strict ClayCode envelope on held-out OOD;
2. >=95% semantic-gate pass;
3. compositional v2 materially beats untuned 0.5B on the same held-out tasks;
4. invalid/missing action arguments reject instead of guessed repair;
5. unresolved alternatives remain Hyperposition until a real discriminator exists;
6. runtime profile changes do not leak a fixed name/job/persona;
7. stale generation and unknown-effect cases fail closed;
8. model output never becomes canonical truth or direct effect authority;
9. matched comparison with at least one larger general model before any superiority claim;
10. deployment quantization plus **measured peak RSS <1 GiB at context 2048**;
11. successful `local_exec` integration without resetting MiniUnifiedDB identity/state.

GGUF file size alone is not RSS evidence. ClayCode behavior or SFT is not evidence of consciousness.

## `go`

`refresh -> corpus/spec -> compositional falsifier -> Together BYOM/preflight -> exact create/job -> OOD/base/larger benchmark -> quantize -> RSS -> local_exec -> durable evidence`

No report-only `go` is sufficient while executable/source progress is available.
