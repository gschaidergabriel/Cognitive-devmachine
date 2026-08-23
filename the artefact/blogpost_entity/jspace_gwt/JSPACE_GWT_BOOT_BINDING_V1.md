# JSPACE_GWT_BOOT_BINDING_RECEIPT/v1

Status: SOURCE CONTRACT CANDIDATE  
Scope: first intentional Ubuntu start after the 2026-08-23 owner architecture binding.

This contract operationalizes the owner-required `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1`. It binds source, executor, bundled cognition, J-Space/lens, GWT, Zero/GRF, Claude-adapter, first-action and execution-policy identities. It cannot by itself grant Whole-GWT, semantic, model-quality, provider, BASE, or whole-product acceptance.

## ClayCode semantic contract

```claycode
r0.observe(
  source(main_sha, tree_sha, dirty, dirty_diff_sha256?),
  executor(UBUNTU, host_identity_sha256, kernel),
  bundled_core(manifest_sha256, checkpoint_sha256, tokenizer_sha256, runtime_sha256),
  jspace(
    jlens_upstream_commit,
    lens_file_sha256,
    lens_semantic_sha256,
    lens_semantic_digest_method,
    lens_profile_sha256,
    fit_corpus_sha256,
    n_prompts,
    d_model,
    source_layers,
    sparsity_k
  ),
  gwt(workspace_policy_sha256, calibration_sha256, slot_count),
  zero_grf(zero_identity_sha256, grf_sha256, projection_policy_sha256),
  claude_adapter(adapter_version, capability_profile_sha256),
  inference(first_engine_choice, origin_attribution, first_actions[]),
  policy(free_only, paid_or_unknown_network_attempts, paid_or_unknown_secret_lookups)
)

r3.counter(
  lens_serialization_nonfinite,
  lens_file_semantics_alias,
  unfitted_position_readout,
  prompt_copy_confound,
  missing_jspace_sparsity_identity,
  stale_or_substituted_manifest,
  dirty_source_without_byte_identity,
  unattributed_or_duplicate_first_action,
  free_only_boundary_breach,
  gwt_workspace_mistaken_for_truth,
  claude_candidate_mistaken_for_authority
)

r4.discriminate(
  require(dirty == true -> sha256(dirty_diff_sha256)),
  require(unique(first_actions.action_id)),
  require(first_actions.origin in [ZERO, HOOK_TIMER, CLAUDE_CODE, PROXY_SANDBOX_CONTROLLER, OTHER]),
  require(first_actions.origin == OTHER -> nonempty(origin_detail)),
  require(type(first_actions.effect_requested) == bool),
  require(pre_save_all_finite == true),
  require(post_load_all_finite == true),
  require(lens_file_sha256 == sha256(exact_persisted_lens_bytes)),
  require(lens_semantic_sha256 == ordered_fp32_finite_v1(exact_persisted_lens)),
  require(sparsity_k >= 1),
  require(minimum_readout_position >= skip_first_positions),
  require(all(observed_readout_positions >= minimum_readout_position)),
  require(prompt_copy_confound_guard_enabled == true),
  require(exact_bytes_verified == true),
  require(free_only => paid_or_unknown_network_attempts == 0),
  require(free_only => paid_or_unknown_secret_lookups == 0)
)

r6.verify(
  claim(whole_gwt_credit == ZERO),
  claim(whole_product == IN_PROGRESS)
)
```

## Provenance hardening

`dirty=true` is not an exact source identity by itself. A dirty worktree can contain different bytes under the same Git commit/tree pair, so the receipt additionally binds `dirty_diff_sha256` whenever dirty state is observed.

A free-form `origin_attribution` is also insufficient for the first post-start actions. The receipt therefore binds a non-empty `first_actions` list with unique `action_id`, a controlled origin class and explicit boolean `effect_requested`. `OTHER` requires typed `origin_detail`.

These fields establish provenance only; they do not establish autonomy, causal correctness, effect success, or model quality.

## Dual lens identity

The receipt binds two deliberately different identities:

- `lens_file_sha256`: SHA-256 of the exact persisted lens artifact bytes;
- `lens_semantic_sha256`: canonical digest of the persisted loaded J matrices and defining metadata.

Neither replaces the other. Exact file identity is supply-chain/provenance evidence. Semantic identity prevents serialization-container details from being the only identity of the loaded Jacobian matrices.

`lens_semantic_digest_method` is fixed to `ordered-fp32-finite-v1` for this schema:

1. load with `torch.load(..., map_location="cpu", weights_only=True)`;
2. require `J`, `n_prompts`, `source_layers`, `d_model`;
3. require positive prompt/model dimensions, sorted unique non-negative source layers, exact matrix-layer agreement and `d_model × d_model` matrices;
4. canonicalize each persisted matrix to CPU contiguous float32;
5. reject NaN, +Inf and -Inf;
6. encode as little-endian float32 in C order;
7. SHA-256 a versioned domain separator, prompt/model/layer metadata and matrices in ascending layer order.

The digest represents persisted loaded values, not an imagined pre-save higher-precision tensor. Lossy persistence therefore changes semantic identity.

The canonical validator has two modes:

```text
validate_jspace_gwt_boot_binding_v1.py RECEIPT.json
  -> STRUCTURAL_ONLY

validate_jspace_gwt_boot_binding_v1.py RECEIPT.json LENS.pt
  -> recompute exact file + semantic identities
  -> EXACT_LENS_ARTIFACT_VERIFIED on success
```

Only the second form establishes the lens-artifact portion of an exact boot binding.

## J-Space sparsity is identity-bearing

The 2026 Transformer Circuits definition uses J-lens vectors as an overcomplete frame and defines operational J-space with an allowable sparsity `k`. The receipt therefore binds `sparsity_k` separately from GWT `slot_count`.

```text
SPARSITY_K != GWT_SLOT_COUNT
```

Neither has a universal canonical value here; both remain exact checkpoint/tokenizer/runtime calibration outputs.

## External measurement hardening

Current upstream Jacobian-Lens fits with a configurable leading-position skip. Upstream issue #5 reports readout/prompt-copy measurement pitfalls, while issue #6 reports float16 persistence overflow risk. The receipt therefore binds the upstream commit and retains fail-closed numeric-finiteness and readout-position controls.

Primary references:
- https://github.com/anthropics/jacobian-lens
- https://github.com/anthropics/jacobian-lens/issues/5
- https://github.com/anthropics/jacobian-lens/issues/6
- https://transformer-circuits.pub/2026/workspace/index.html

These guards do not prove a lens is well-conditioned or semantically useful. They only close known false-credit paths.

## FREE_ONLY boundary

While current execution policy is `FREE_ONLY`, the receipt must state `free_only=true` with both `paid_or_unknown_network_attempts=0` and `paid_or_unknown_secret_lookups=0`. Any non-zero value fails closed. This records policy compliance; it does not authorize future paid execution.

## Evidence boundary

A passing structural validator means only that the receipt is coherent with this source contract. Exact lens binding additionally requires the lens-file verification mode. Runtime credit still requires an actually observed exact-source Ubuntu boot and all exact artifact identities. J-Space measurements remain `MEASURED_INTERPRETABILITY`, not canonical fact. GWT workspace stability remains control evidence, not truth. Claude Code results remain candidate inference.
