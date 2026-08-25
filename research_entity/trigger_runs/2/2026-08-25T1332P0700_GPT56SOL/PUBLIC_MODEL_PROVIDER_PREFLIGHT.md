# Trigger 2 — public model/provider preflight delta

Date: 2026-08-25T13:32+07:00  
Organ: GPT-5.6 Sol / ChatGPT organ  
User trigger: `triggerwort 2`  
Program: EntityOS + HCU  
Target: Qwen3.5-0.8B full-fine-tuning research lane  
Execution class: PUBLIC_SOURCE_RESEARCH_ONLY

## Re-entry identity

- Canonical `main` observed immediately before this delta: `4831af488d47931c6b4db521499fe1bf50706ba8`.
- Parallel current-main Trigger-2 corpus convergence already exists at `19e23f32eea9bf74cc0651e8f5a85e830546345c`; this file does not duplicate that corpus/recipe authority.
- Retained Trigger-2 implementation/research lane: PR #1956, branch `research/trigger2-qwen35-08b-hcu-fullft-20260825`.
- PR head observed before write: `30d3285f92f8f4007710b28ba55bc835b0f6de44`.

## R0 — official model identity evidence

Primary source: `https://huggingface.co/Qwen/Qwen3.5-0.8B-Base`

Observed public immutable revision for the Base candidate during this run:

`Qwen/Qwen3.5-0.8B-Base@dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68`

The official Qwen model material describes the 0.8B family as a hybrid language stack with hidden size 1024 and 24 language-model layers, using Gated DeltaNet/linear-attention blocks plus periodic full-attention blocks. This is model-specific architecture evidence and is not ancestry evidence for reusing Qwen3-0.6B J-Space coordinates.

Status consequence:

- `BASE_CANDIDATE_PUBLIC_REVISION_BOUND = true`
- `BASE_CANDIDATE_SELECTED_FOR_FULL_FT = false`
- tokenizer / processor / chat-template / weight-file digests still require the final pre-freeze identity manifest;
- the post-trained `Qwen/Qwen3.5-0.8B` candidate still requires the same immutable identity treatment before Base-vs-post-trained selection.

## R0/R1 — Together public capability boundary

Primary public sources reviewed:

- `https://www.together.ai/fine-tuning`
- `https://www.together.ai/pricing`
- current Together fine-tuning support/docs surfaced on 2026-08-25
- Together March 2026 Qwen3.5 update

Observed public facts:

1. Together publicly offers both LoRA and full fine-tuning.
2. Together's public fine-tuning page advertises broad Hugging Face/open-model compatibility.
3. The current public supervised full-FT price for models up to 16B is listed as `$0.54 / 1M processed tokens`, with a `$4 minimum job charge`.
4. The March 2026 Qwen3.5 announcement explicitly names larger Qwen3.5 variants, but this research pass did not find an explicit service-level listing of `Qwen3.5-0.8B`.

Therefore the generic compatibility statement is not promoted into exact-model provider admission.

Fail-closed status:

`TOGETHER_QWEN35_08B_FULL_FT_COMPATIBILITY = UNVERIFIED_EXACT_MODEL`

No credential lookup, API preflight, upload, job creation, training, endpoint creation, billing action, or provider model call was performed.

## Recipe / acceptance delta

This run adds the following requirements to the Trigger-2 pre-job gate:

- pin exact immutable revision + tokenizer + processor/chat-template + actual consumed weight identity for whichever 0.8B source checkpoint wins selection;
- compare Base vs post-trained 0.8B under one frozen, matched baseline/pilot protocol before selecting the single full-FT source checkpoint;
- do not treat provider marketing-level universal compatibility as proof that the exact 0.8B model is currently accepted for full FT;
- retain exact provider compatibility as a future authority-gated pre-job discriminator;
- because Qwen3.5-0.8B is hybrid, post-FT J-Space evaluation must stratify candidate intervention/observation sites by DeltaNet versus full-attention site class rather than importing Qwen3-0.6B layer semantics;
- the old Qwen3-0.6B terminal negative remains method/counterevidence only and creates zero positive Qwen3.5 J-Space labels.

## Training state

`BASE_MODEL_SELECTION_PENDING`

Training credit from this delta: `0`  
Qwen3.5 J-Space runtime credit from this delta: `0`  
Whole HCU runtime credit from this delta: `0`  
Whole EntityOS/HCU runtime credit from this delta: `0`

## Next highest-information gate

Construct the deterministic, matched Base-vs-post-trained Qwen3.5-0.8B baseline/pilot specification with exact identity manifests and sealed family-level holdout. Provider compatibility remains a separate pre-job gate and must not be inferred from generic public compatibility language.
