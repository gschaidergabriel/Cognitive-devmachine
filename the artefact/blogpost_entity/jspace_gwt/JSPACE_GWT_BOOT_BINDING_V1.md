# JSPACE_GWT_BOOT_BINDING_RECEIPT/v1

Status: SOURCE CONTRACT CANDIDATE
Scope: first intentional Ubuntu start after the 2026-08-23 owner architecture binding.

This contract operationalizes the owner-required `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1`. It can bind exact bytes and observed boot facts, but it cannot by itself grant Whole-GWT, semantic, model-quality, provider, BASE, or whole-product acceptance.

## ClayCode semantic contract

```claycode
r0.observe(
  source(main_sha, tree_sha, dirty, dirty_diff_sha256?),
  executor(UBUNTU, host_identity_sha256, kernel),
  bundled_core(manifest_version, manifest_sha256, checkpoint_sha256, tokenizer_sha256, runtime_sha256, quantization_runtime_identity?),
  jspace(
    jlens_upstream_commit,
    jspace_profile_sha256,
    lens_file_sha256,
    lens_semantic_sha256,
    lens_semantic_digest_method,
    lens_profile_sha256,
    steering_calibration_sha256?,
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
  policy(free_only, paid_or_unknown_network_attempts, paid_or_unknown_secret_lookups),
  source_lock(manifest_file_sha256, manifest_identity_sha256, integration_identity_sha256)
)

r3.counter(
  lens_serialization_nonfinite,
  lens_file_semantics_alias,
  missing_jspace_sparsity_identity,
  unfitted_position_readout,
  prompt_copy_confound,
  stale_or_substituted_manifest,
  cross_bundle_calibration_alias,
  runtime_receipt_self_authorizes_manifest,
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
  require(boot_manifest_sha256 == source_lock.manifest_file_sha256),
  require(boot_checkpoint_sha256 == bundled_manifest.checkpoint_digest),
  require(boot_tokenizer_sha256 == bundled_manifest.tokenizer_digest),
  require(boot_jspace_profile_sha256 == bundled_manifest.jspace_profile_digest),
  require(boot_lens_profile_sha256 == bundled_manifest.lens_profile_digest),
  require(boot_workspace_calibration_sha256 == bundled_manifest.workspace_calibration_digest),
  require(source_lock.integration_identity_sha256 == bundled_manifest.integration_identity_sha256),
  require(free_only => paid_or_unknown_network_attempts == 0),
  require(free_only => paid_or_unknown_secret_lookups == 0)
)

r6.verify(
  claim(whole_gwt_credit == ZERO),
  claim(whole_product == IN_PROGRESS)
)
```

## Atomic bundled-cognition binding

The boot receipt is not allowed to self-authorize a plausible collection of digests. Runtime admission composes three separately scoped objects:

1. the repository-owned canonical `mini-entity-bundled-cognition-manifest/v1`;
2. `BUNDLED_COGNITION_SOURCE_LOCK/v1` as the explicit source-side admission lock;
3. the observed `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1`.

The source lock binds both the raw manifest file digest and the manifest validator's complete and semantic integration identities. The boot receipt must match the admitted manifest for engine/model/checkpoint/tokenizer, optional quantization/runtime identity, J-Space profile, lens profile, optional steering calibration and workspace calibration.

The repository ships the source-lock file intentionally as `UNBOUND`. This is a fail-closed state: it must remain unable to admit cognition until exact bundled checkpoint/tokenizer/runtime/J-Space/lens/workspace artifacts have been measured and the corresponding manifest has been explicitly admitted.

This composition preserves `PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY`: a valid-looking J-Space/lens/workspace tuple from another calibration bundle cannot receive boot admission merely because individual digests are syntactically valid.

## Dual lens identity

The receipt binds two distinct lens identities:

- `lens_file_sha256`: the exact persisted lens artifact bytes;
- `lens_semantic_sha256`: canonical identity of the persisted loaded Jacobian matrices plus defining metadata.

Neither replaces the other. Exact bytes preserve supply-chain/provenance identity; semantic identity prevents serialization-container differences from becoming the only identity of the loaded geometry.

`lens_semantic_digest_method` is fixed to `ordered-fp32-finite-v1`:

1. load the JacobianLens checkpoint with `torch.load(..., map_location="cpu", weights_only=True)`;
2. require `J`, `n_prompts`, `source_layers`, `d_model`;
3. require positive dimensions, sorted unique non-negative source layers, exact matrix/layer agreement, and `d_model × d_model` matrices;
4. canonicalize persisted matrices to CPU contiguous float32;
5. reject NaN/+Inf/-Inf;
6. encode little-endian float32 in C order;
7. hash a versioned domain separator, prompt/model/layer metadata and matrices in ascending layer order.

The semantic digest covers persisted loaded values, not an imagined pre-save higher-precision state.

## J-Space sparsity is identity-bearing

The 2026 Transformer Circuits definition treats J-lens vectors as an overcomplete frame and defines operational J-space using an allowable sparsity `k`. The receipt therefore binds a positive `sparsity_k` separately from GWT `slot_count`.

```text
SPARSITY_K != GWT_SLOT_COUNT
```

The already-admitted `jspace_profile_sha256` remains the source-side profile identity. `sparsity_k` is an explicit observed runtime parameter under that profile; this contract does not invent a universal default.

## Provenance hardening

`dirty=true` is not an exact source identity by itself. A dirty worktree can contain arbitrarily different bytes under the same Git commit/tree pair, so the receipt additionally binds `dirty_diff_sha256` whenever dirty state is observed.

Likewise one free-form `origin_attribution` is insufficient to attribute the first post-start actions. The receipt binds a non-empty `first_actions` list with unique `action_id`, a controlled origin class, and an explicit boolean `effect_requested`. `OTHER` requires typed detail.

These are provenance guards only. They do not establish autonomy, causal correctness, effect success, or model quality.

## External measurement hardening

Current upstream Jacobian-Lens code fits with a configurable leading-position skip whose default is 16. Current upstream issue #5 reports readout/prompt-copy measurement pitfalls and issue #6 reports default float16 serialization overflow risk. Numeric finiteness and position-policy checks therefore remain fail-closed.

Primary upstream references:
- https://github.com/anthropics/jacobian-lens
- https://github.com/anthropics/jacobian-lens/issues/5
- https://github.com/anthropics/jacobian-lens/issues/6
- https://transformer-circuits.pub/2026/workspace/index.html

These guards do not prove a lens is well-conditioned or semantically useful. They only block known false-credit paths.

## FREE_ONLY boundary

While current execution policy is `FREE_ONLY`, the receipt states `free_only=true` and requires both `paid_or_unknown_network_attempts=0` and `paid_or_unknown_secret_lookups=0`. Any non-zero value fails closed. This records policy compliance and does not authorize future paid execution.

## Validation modes

```text
python validate_jspace_gwt_boot_binding_v1.py RECEIPT.json BUNDLED_MANIFEST.json SOURCE_LOCK.json
    -> MANIFEST_BOUND_STRUCTURAL_ONLY

python validate_jspace_gwt_boot_binding_v1.py RECEIPT.json BUNDLED_MANIFEST.json SOURCE_LOCK.json LENS.pt
    -> manifest/source-lock binding + recomputed lens byte/semantic identity
    -> EXACT_LENS_ARTIFACT_VERIFIED
```

Only the second form establishes the lens-artifact portion of the boot binding.

## Evidence boundary

A passing structural validator means only that the receipt is coherent with the source-lock/manifest contract. Exact lens binding additionally requires lens-file verification. Runtime credit still requires an actually observed exact-source Ubuntu boot and exact artifact identities. J-Space measurements remain `MEASURED_INTERPRETABILITY`, not canonical fact. GWT workspace stability remains control evidence, not truth. Claude Code results remain candidate inference.
