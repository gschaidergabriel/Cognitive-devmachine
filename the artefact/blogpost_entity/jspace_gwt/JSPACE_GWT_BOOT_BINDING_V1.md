# JSPACE_GWT_BOOT_BINDING_RECEIPT/v1

Status: SOURCE CONTRACT CANDIDATE
Scope: first intentional Ubuntu start after the 2026-08-23 owner architecture binding.

This contract operationalizes the owner-required `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1`. It can bind exact bytes and observed boot facts, but it cannot by itself grant Whole-GWT, semantic, model-quality, provider, BASE, or whole-product acceptance.

## ClayCode semantic contract

```claycode
r0.observe(
  source(main_sha, tree_sha, dirty=false),
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
  inference(first_engine_choice, origin_attribution),
  policy(free_only, paid_or_unknown_network_attempts, paid_or_unknown_secret_lookups)
)

r3.counter(
  lens_serialization_nonfinite,
  lens_file_semantics_alias,
  unfitted_position_readout,
  prompt_copy_confound,
  missing_jspace_sparsity_identity,
  stale_or_substituted_manifest,
  gwt_workspace_mistaken_for_truth,
  claude_candidate_mistaken_for_authority
)

r4.discriminate(
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

## Dual lens identity

The receipt binds two deliberately different identities:

- `lens_file_sha256`: exact persisted lens artifact bytes;
- `lens_semantic_sha256`: canonical digest of the persisted loaded J matrices and defining metadata.

Neither replaces the other. The byte digest preserves exact supply-chain/provenance identity. The semantic digest prevents the runtime contract from treating serialization-container differences as the only identity of the loaded Jacobian matrices.

`lens_semantic_digest_method` is fixed to `ordered-fp32-finite-v1` for this schema:

1. load the public JacobianLens checkpoint with `torch.load(..., map_location="cpu", weights_only=True)`;
2. require `J`, `n_prompts`, `source_layers`, and `d_model`;
3. require positive `n_prompts`/`d_model`, sorted unique non-negative source layers, exact matrix-layer key agreement, and `d_model x d_model` matrices;
4. convert each persisted matrix to CPU contiguous float32;
5. reject NaN/+Inf/-Inf;
6. encode floats as little-endian float32 in C order;
7. SHA-256 a versioned domain separator plus prompt/model/layer metadata and matrices in ascending layer order.

The semantic hash is over **persisted loaded values**, not an imagined pre-save fp32 state. Any lossy serialization therefore remains visible in the semantic identity.

The canonical validator supports two modes:

```text
validate_jspace_gwt_boot_binding_v1.py RECEIPT.json
    -> STRUCTURAL_ONLY

validate_jspace_gwt_boot_binding_v1.py RECEIPT.json LENS.pt
    -> recomputes exact byte + semantic identities
    -> EXACT_LENS_ARTIFACT_VERIFIED on success
```

Only the second form can establish the lens-artifact part of an exact boot binding.

## J-Space sparsity is identity-bearing

The 2026 Transformer Circuits paper defines the J-lens vectors as an overcomplete frame and defines J-space only after an allowable sparsity level `k` is chosen. Therefore this receipt binds `sparsity_k` separately from GWT `slot_count`.

`SPARSITY_K != GWT_SLOT_COUNT`

Neither receives a universal canonical value. Both must remain tied to exact checkpoint/tokenizer/runtime calibration evidence.

## External measurement hardening

Current upstream Jacobian-Lens code fits with a configurable leading-position skip whose default is 16. Current upstream issue #5 reports that `apply()` can still return those unfitted positions and that prompt-token copying can confound naive concept-presence measurements. Current upstream issue #6 reports that the default float16 lens serialization can overflow large finite fp32 Jacobians to `inf`.

Therefore this receipt binds the exact upstream commit and makes numeric finiteness plus position-policy checks explicit fail-closed conditions.

Primary upstream references:
- https://github.com/anthropics/jacobian-lens
- https://github.com/anthropics/jacobian-lens/issues/5
- https://github.com/anthropics/jacobian-lens/issues/6
- https://transformer-circuits.pub/2026/workspace/index.html

These guards do not prove that a lens is well-conditioned or semantically valid. They only block known classes of false measurement credit.

## Evidence boundary

A passing structural validator means only that the receipt is coherent with this source contract. Exact lens binding additionally requires the lens-file verification mode. Runtime credit still requires an actually observed exact-source Ubuntu boot and all other exact artifact hashes. J-Space measurements remain `MEASURED_INTERPRETABILITY`, not canonical fact. GWT workspace stability remains a control observation, not truth. Claude Code results remain candidate inference.

The current `FREE_ONLY` execution boundary remains unchanged. This contract performs no provider key lookup, network request, training, billed create, or paid execution.
