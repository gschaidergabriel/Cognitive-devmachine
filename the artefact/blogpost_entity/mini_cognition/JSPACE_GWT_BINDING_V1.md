# J-Space / GWT Binding v1 — Mini Entity fail-closed product contract

Status: SOURCE CONTRACT / RUNTIME UNVERIFIED
Owner architecture source: `5f3c2a7cc9aeab8f851d38450fa50a3e1451d767`
Fresh source base: `32d82c400d92a4a006eacc1b51ae7fd4e4ad32ea`

## Purpose

The owner architecture makes the bundled approximately-0.8B cognition core plus Unified J-Space/GWT a first-class Mini Entity subsystem. Current `main` already contains the source-only `JSPACE_TRANSFER_ASSUMPTION_FALSIFIER`, which rejects direct transplantation of Claude/J-space geometry and requires model-specific calibration. This file does not repeat that experiment: it operationalizes the surviving conclusion as a fail-closed identity/calibration validator without claiming that the exact Qwen3.5-0.8B checkpoint has already run through Anthropic's Jacobian Lens.

The contract separates four things that must never collapse into one another:

```text
model bytes
!= fitted lens bytes
!= measured latent telemetry
!= canonical MiniUnifiedDB truth
```

ClayCode semantic form:

```text
module clay.cog.jspace_binding_v1
fn admit(b:Map)->Map {
  grf_observe(b,"R0","exact model/tokenizer/lens/workspace identities","MEASURED")
  authority_bind(b,"canonical_truth","MiniUnifiedDB")
  authority_deny(b,"JSpace","canonical_truth")
  authority_deny(b,"model_output","canonical_truth")
  collapse_guard(b,"unmeasured workspace calibration cannot become configured fact")
  omega_validate(b,"identity|digest|shape|calibration|mode|authority")
  return b
}
```

## Required binding manifest

A manifest admitted by `validate_jspace_gwt_binding_v1.py` binds at least:

- exact current Mini Entity source SHA;
- owner architecture commit;
- model id, runtime class and architecture;
- checkpoint and tokenizer SHA-256;
- model layer count and residual width;
- Jacobian-Lens implementation and exact Git revision;
- fitted lens SHA-256;
- fitting corpus SHA-256 and prompt count;
- source layers, target layer, `dim_batch`, `max_seq_len`;
- workspace policy digest;
- explicit slot-calibration status;
- canonical truth/effect authority boundaries;
- exact bundled-core local J-Space mode (`LOCAL_OBSERVE_ONLY` or `FULL_LOCAL_LATENT`);
- intervention mode separately (`DISABLED` or `RESEARCH_INTERVENTION`).

The validator deliberately does **not** accept placeholder all-zero/all-`f` digests.

## Calibration law

`slot_calibration.status = UNMEASURED` means there is no admitted `selected_max_slots` and no calibration receipt. A default like `max_slots=3` may exist in an experiment configuration, but it cannot be promoted into the fixed product manifest until measured on exact bound bytes.

`slot_calibration.status = MEASURED` requires both a positive selected slot count and a SHA-256-bound calibration receipt.

Likewise, layer bands, steering coefficients, truth thresholds and workspace occupancy thresholds are not owner facts merely because they are plausible.

## Observer / intervention split

The binding contract applies to the bundled/hookable local core, so its admitted J-Space mode is either `LOCAL_OBSERVE_ONLY` or `FULL_LOCAL_LATENT`. `COMPILED_EXTERNAL` and `PLAIN_COMPATIBILITY` remain valid inference-profile modes elsewhere in the architecture, but they cannot satisfy a local fitted-lens binding.

Intervention authority is orthogonal. Default `intervention_mode=DISABLED` may not carry an intervention payload. `RESEARCH_INTERVENTION` requires `FULL_LOCAL_LATENT`, a separate receipt digest, a finite non-zero intervention coefficient and `canonical_write_allowed=false`.

An intervention result remains candidate research evidence. It cannot bypass the normal grammar/type/schema/authority/generation/effect path or write canonical state directly.

## Qwen3.5 / Jacobian-Lens source compatibility boundary

The already-merged 2026-08-23 transfer falsifier establishes that geometry/calibration cannot be copied from Claude. A narrower static adapter review retains a **plausible but unverified** local execution path:

- Anthropic `jacobian-lens@581d398613e5602a5af361e1c34d3a92ea82ba8e` tries standard Hugging Face layout `model` before wrapper layout `model.language_model`, and its `HFLensModel` operates on residual block hooks plus a final norm/unembedding;
- Qwen3.5 is a hybrid decoder family using a 3:1 sequence of Gated DeltaNet linear-attention blocks and full-attention blocks;
- current upstream evidence supports using the language-only `Qwen3_5ForCausalLM / Qwen3_5TextModel` surface first, where the expected official `jlens` layout is `model`; the multimodal `Qwen3_5ForConditionalGeneration` wrapper remains a fallback surface if exact checkpoint loading requires it.

This is ordinary source compatibility analysis, not an additional unusual experiment and not runtime evidence. It supports a source-level compatibility hypothesis only. Hybrid attention internals are not proof of incompatibility, but neither the layout match nor the generic Qwen examples prove that exact `from_hf -> fit -> apply` succeeds for the selected checkpoint/runtime.

Required next executable gate:

```text
exact checkpoint + tokenizer
-> exact transformers/torch runtime
-> prefer Qwen3_5ForCausalLM text backbone
-> jlens.from_hf(...) and verify expected Layout("model")
-> one tiny forward/apply smoke
-> bounded jacobian_for_prompt
-> small fit corpus
-> reload/apply exact lens
-> persist digests + resource/timing/error receipt
```

Any failure is preserved as evidence. No fallback may silently switch to another model while retaining the same binding identity.

## Evidence class

This contract plus its local regression suite can establish only:

`SOURCE_BINDING_VALIDATOR_MECHANISM_SUPPORTED`

It cannot establish:

- exact Qwen3.5-0.8B Jacobian-Lens runtime compatibility;
- a real J-space layer band;
- optimal GWT slot count;
- causal steering efficacy;
- consciousness;
- canonical semantics;
- model quality;
- whole Mini Entity product PASS.
