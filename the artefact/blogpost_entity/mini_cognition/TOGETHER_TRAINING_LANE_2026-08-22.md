# Together training lane decision — 2026-08-22

Status: CURRENT EVIDENCE CANDIDATE
Trigger: `go`
Source main at branch creation: `659cc2471b73bcefebb6a57694e6737cc2107cc5`

## Question

Which checkpoint currently satisfies the combined owner-facing product constraints:

1. approximately 1B parameters / very small local cognition module;
2. Full fine-tuning on Together rather than silently switching to a different training provider;
3. generic ClayCode/GRF/Hyperposition/typed-omega cognition with no fixed entity name/job/persona/application;
4. local Q4_K_M release shape plausibly below 1 GiB, with actual context-2048 peak RSS still required before promotion.

## Current provider evidence

Primary sources refreshed 2026-08-22:

- Together supported fine-tuning models: `https://docs.together.ai/docs/fine-tuning/supported-models`
- Together BYOM contract: `https://docs.together.ai/docs/fine-tuning/byom`
- Together pricing: `https://www.together.ai/pricing`
- Qwen3.5-0.8B upstream model: `https://huggingface.co/Qwen/Qwen3.5-0.8B`
- Qwen3.5-0.8B config: `https://huggingface.co/Qwen/Qwen3.5-0.8B/blob/main/config.json`

Observed current facts:

- BYOM requires a Together catalog base/template whose architecture matches the Hugging Face checkpoint.
- The current Full fine-tuning table lists Qwen3.5 0.8B, 2B, 4B, 9B, 27B, but no Qwen2/Qwen2.5 Full-FT base.
- `Qwen/Qwen2.5-0.5B` is Qwen2-family and therefore has no currently documented architecture-compatible Together Full-FT template.
- `Qwen/Qwen3.5-0.8B` is explicitly present in Together's current Full-FT catalog and its upstream model card reports 0.8B language-model parameters.
- Public Q4_K_M GGUFs for Qwen3.5-0.8B are currently observed around 528-608 MB. This is file-size evidence only, not a peak-RSS claim.

## Discriminator result

### Lane A — owner-directive historical primary

`Qwen/Qwen2.5-0.5B`

Result: `BLOCKED_ON_TOGETHER_FULL_FT_TEMPLATE_ARCHITECTURE`

Reason: no current documented Qwen2/Qwen2.5 Full-FT Together base exists. A Qwen3.5 template is not an admissible substitute for Qwen2 weights merely because it is close in size.

### Lane B — current Together-native ~1B candidate

`Qwen/Qwen3.5-0.8B` / `Qwen/Qwen3.5-0.8B-Base`

Result: `CATALOG_SUPPORTED_CANDIDATE`

Why it fits the product goal better today:

- 0.8B is the smallest currently documented Qwen Full-FT catalog model on Together;
- it is close to the requested ~1B class;
- architecture/template pairing is direct instead of BYOM-cross-family;
- observed Q4_K_M file sizes are comfortably below 1 GiB;
- the existing application-neutral ClayCode SFT corpus can remain a cognition-behavior dataset, but architecture/tokenizer/template compatibility must be revalidated before any paid create.

## Non-negotiable gates before paid training

Do not create a billed job solely from this document.

Required next gates:

1. owner/policy authority must explicitly admit the 0.8B architecture change if the repository's exact 0.5B checkpoint identity remains binding;
2. pin an exact 40-hex Hugging Face revision for the selected 0.8B checkpoint;
3. regenerate/validate tokenized corpus and strict ClayCode/OOD gates against the selected tokenizer/template;
4. use Together's authenticated model-limits + price-estimate preflight;
5. preserve deterministic campaign fingerprint, zero-retry billed create, local CREATE_ARMED ledger, duplicate-job fence, exact job-identity verification and USD/EUR campaign budget gate;
6. after training, evaluate tuned vs untuned same-base and at least one larger general model;
7. quantize the exact selected checkpoint to Q4_K_M;
8. measure actual peak process RSS at context 2048 and require `< 1 GiB` before promotion.

## Exactly one unusual experiment

`MODEL_FIT_TRIANGLE_08B`

Intervention: require a candidate to satisfy all three externally checkable constraints simultaneously:

`Together Full-FT catalog admission` + `sub-1B-class parameters` + `observed Q4_K_M file <1 GiB`.

Outcome:

- Qwen2.5-0.5B: REJECT for current Together Full-FT admission, despite attractive size.
- Qwen3.5-0.8B: RETAIN as the first current candidate satisfying all three at source/evidence scope.

This does not prove training success, model quality, peak RSS, consciousness, mathematical correctness or whole Mini Entity acceptance.
