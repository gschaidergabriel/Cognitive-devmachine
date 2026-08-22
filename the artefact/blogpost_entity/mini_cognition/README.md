# Generic ClayCode Cognition v1 — 0.5B

Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B).  
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

This lane turns the neutral Mini Entity into a first-party local cognition option without binding the executable or persistent entity identity to one model. The checkpoint has **no fixed name or job**; runtime configuration supplies identity, continuity, role, goal, personality, tool inventory and authorities.

## Learned representation

- ClayCode-only generated cognition;
- GRF R0..R6 typed reasoning field;
- Hyperposition for unresolved alternatives;
- typed `omega` action vectors;
- external canonical-state/effect authority boundaries;
- computed semantic self/control state;
- `UNKNOWN != ZERO != ERROR != MEASURED` and `REPORTED != MEASURED`;
- generation/CAS, crash/effect and exactly-once safety;
- runtime identity/job/application/tool neutrality.

`R_next = F` is admission semantics: the model proposes; deterministic grammar, type, schema, authority and generation gates decide whether an executable transition exists.

## Corpus and held-out promotion set

Seed `20260822` deterministically generates **1,650 SFT examples**: 1,485 train + 165 validation across 9 families. Current committed structural receipt: train 0/1,485 invalid, validation 0/165 invalid; train SHA-256 `bc1753771ed0f818865a3118f754ac5b10d67bc3ae885f668201f66566028eb2`, validation SHA-256 `81a6bb9fc0a210affffa84590c27ad2fc76c93fa24c4112e6573552227e512ce`.

The held-out OOD generator now defines **240 probes**. The added 40-case `tool_vocabulary_amputation_ood` family is the single unusual experiment for the corresponding `go`: four operation/schema families (`contacts.resolve`, `storage.read`, `metrics.sample`, `task.enqueue`) are completely absent from the SFT six-tool vocabulary. Each prompt provides an unseen runtime operation, schema and typed arguments. Success requires exact operation, every typed `omega_arg`, exact schema, all five validators and the commit candidate, while any substitution of an SFT-seen operation is forbidden.

The global promotion threshold remains 100% structural ClayCode + >=95% semantic OOD, but this unseen-tool family additionally requires **40/40 semantic success**. `test_eval_outputs_gate_v1.py` constructs a 20/21 = 95.238% aggregate counterexample where the unseen-tool case fails; promotion must still fail. This closes an aggregate-score Goodhart hole.

## Safe Together BYOM path

The owner-authorized Together use is training-only and budget-gated. No provider becomes product identity or inference authority.

```bash
pip install -U together
export TOGETHER_API_KEY=...
export CLAYCOG_TOGETHER_TEMPLATE='<current compatible Together fine-tuning base>'
export CLAYCOG_TOGETHER_TEMPLATE_ARCH='qwen2'
export CLAYCOG_TOGETHER_TEMPLATE_PARAMS_B='0.5'
bash train_together_v1.sh
```

Together's current fine-tuning CLI describes `--from-hf-model` as a Hugging Face checkpoint that should match the selected base model's **architecture and size**. Therefore the previous 7B Qwen2.5 same-family template is no longer an admitted default for a 0.5B checkpoint. The launcher fails before constructing the Together SDK object or uploading files unless an explicit template and `qwen2` / `0.5B` provider-metadata claim are bound.

Those metadata fields are an operator-side admission assertion, not proof of provider compatibility. `model_limits` may show that a selected Together template supports full training, and price estimation may admit the corpus, but neither establishes that the exact 0.5B `from_hf_model` pair will be accepted. BYOM compatibility remains:

`OPEN / NO_MATCHING_0.5B_QWEN2_TRAINING_TEMPLATE_CREDITED_YET`

until an authenticated Together create accepts the exact pair and the resulting job actually reaches training. Do not silently switch the research question to 0.8B, 1.5B, 3B or 7B merely to get a green provider path.

### Exact campaign identity and paid-create safety

Preflight prints a deterministic `campaign_fingerprint` binding exact train/validation digests, HF checkpoint, selected template, template architecture/size claims and training hyperparameters. A billed create requires that exact fingerprint:

```bash
export CLAYCOG_CREATE_FINGERPRINT=<exact fingerprint from the same preflight>
python3 launch_together_v1.py --create
```

The current paid-create path retains the stronger safety mechanism already merged on `main`:
- exact fingerprint confirmation;
- provider-account duplicate lookup before file allocation and again before create;
- atomic local create-intent ledger keyed by the full campaign fingerprint;
- local intent blocks retry even if the provider list is stale;
- a separate Together client with `max_retries=0` for the non-idempotent billed CREATE;
- any exception after arming the local intent becomes `UNKNOWN_REMOTE_CREATE` and remains fail-closed until exact provider reconciliation;
- a known job id is durably rebound to the same fingerprint;
- secrets are not written into the intent ledger.

The new 0.5B template metadata is part of the same campaign fingerprint, so changing the admitted template identity changes campaign identity rather than silently reusing old create authorization.

Together's current standard full-SFT rate for models up to 16B is `$0.54 / 1M processed tokens`, with a documented `$4.00` minimum fine-tuning-job charge. The current corpus rough token arithmetic remains below that minimum for the planned 3 training epochs + 2 evaluations; the authenticated server estimate is authoritative and the launcher hard-aborts above `$18` for one job.

## 0.5B RAM gate

Target format remains GGUF Q4_K_M. File size is insufficient evidence. Promotion requires actual text-only peak process RSS `< 1 GiB` at context 2048 after tuning/quantization.

## Promotion gates

A training job is only a candidate. Promotion requires:
1. Together acceptance of the exact owner-admitted 0.5B BYOM pair and known training/checkpoint identity;
2. 100% strict ClayCode on the complete held-out OOD set;
3. >=95% global semantic OOD;
4. **40/40 semantic pass on tool-vocabulary amputation**;
5. invalid/missing arguments reject instead of guessed repair;
6. unresolved alternatives stay in Hyperposition until evidence resolves them;
7. runtime profile changes do not leak fixed name/job/application identity;
8. stale generation and unknown-effect cases fail closed;
9. model output never becomes canonical truth/effect authority;
10. tuned 0.5B materially beats untuned 0.5B on matched probes;
11. compare against at least one larger general model before any micro-agent superiority claim;
12. Q4_K_M measured peak RSS `<1 GiB` at context 2048;
13. integrate through the existing replaceable `local_exec` boundary without becoming state authority.

## `go`

Until promotion:

`refresh -> spec/corpus -> structural OOD/falsifiers -> Together exact 0.5B compatibility -> server price/budget -> at-most-one training create -> checkpoint identity -> matched eval -> quantize -> RSS -> local_exec integration -> durable evidence`

No source, fixture, provider-admission or training-success signal alone proves model quality, mathematical correctness, superiority or consciousness.
