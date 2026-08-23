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
  jspace(jlens_upstream_commit, jspace_profile_sha256, lens_file_sha256, lens_profile_sha256, steering_calibration_sha256?, fit_corpus_sha256),
  zero_grf(zero_identity_sha256, grf_sha256, projection_policy_sha256),
  claude_adapter(adapter_version, capability_profile_sha256),
  inference(first_engine_choice, origin_attribution, first_actions[]),
  source_lock(manifest_file_sha256, manifest_identity_sha256, integration_identity_sha256)
)

r3.counter(
  lens_serialization_nonfinite,
  unfitted_position_readout,
  prompt_copy_confound,
  stale_or_substituted_manifest,
  cross_bundle_calibration_alias,
  runtime_byte_substitution_under_stable_runtime_name,
  runtime_receipt_self_authorizes_manifest,
  dirty_source_without_byte_identity,
  unattributed_or_duplicate_first_action,
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
  require(minimum_readout_position >= skip_first_positions),
  require(all(observed_readout_positions >= minimum_readout_position)),
  require(prompt_copy_confound_guard_enabled == true),
  require(exact_bytes_verified == true),
  require(boot_manifest_sha256 == source_lock.manifest_file_sha256),
  require(boot_checkpoint_sha256 == bundled_manifest.checkpoint_digest),
  require(boot_tokenizer_sha256 == bundled_manifest.tokenizer_digest),
  require(boot_runtime_sha256 == bundled_manifest.runtime_digest),
  require(boot_jspace_profile_sha256 == bundled_manifest.jspace_profile_digest),
  require(boot_lens_profile_sha256 == bundled_manifest.lens_profile_digest),
  require(boot_workspace_calibration_sha256 == bundled_manifest.workspace_calibration_digest),
  require(source_lock.integration_identity_sha256 == bundled_manifest.integration_identity_sha256)
)

r6.verify(
  claim(whole_gwt_credit == ZERO),
  claim(whole_product == IN_PROGRESS)
)
```

## Atomic bundled-cognition binding

The boot receipt is not allowed to self-authorize a plausible collection of digests. Runtime admission now composes three separately scoped objects:

1. the repository-owned canonical `mini-entity-bundled-cognition-manifest/v1`;
2. `BUNDLED_COGNITION_SOURCE_LOCK/v1` as the explicit source-side admission lock;
3. the observed `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1`.

The source lock binds both the raw manifest file digest and the manifest validator's complete and semantic integration identities. The boot receipt must then match the admitted manifest for engine/model/checkpoint/tokenizer, exact runtime bytes, optional quantization/runtime identity, J-Space profile, lens profile, optional steering calibration and workspace calibration. `runtime_digest` is identity-bearing in the bundled manifest when present and is mandatory for boot admission; a stable runtime name cannot authorize different executable bytes.

The repository ships the source-lock file intentionally as `UNBOUND`. This is a fail-closed state, not a missing-data convenience: it must remain unable to admit cognition until exact bundled checkpoint/tokenizer/runtime/J-Space/lens/workspace artifacts have been measured and the corresponding manifest has been explicitly admitted.

Validation CLI:

```text
python validate_jspace_gwt_boot_binding_v1.py RECEIPT.json BUNDLED_MANIFEST.json SOURCE_LOCK.json
```

This composition preserves `PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY`: a valid-looking J-Space/lens/workspace tuple from another calibration bundle cannot receive boot admission merely because every individual digest is syntactically valid.

## Provenance hardening

`dirty=true` is not an exact source identity by itself. A dirty worktree can contain arbitrarily different bytes under the same Git commit/tree pair, so the receipt must additionally bind `dirty_diff_sha256` whenever dirty state is observed.

Likewise one free-form `origin_attribution` string is not sufficient to attribute the first post-start actions. The receipt therefore binds a non-empty `first_actions` list with unique `action_id`, a controlled origin class, and an explicit boolean `effect_requested`. `OTHER` remains available but requires typed detail instead of silently collapsing an unknown actor into a known origin.

These are provenance guards only. They do not establish autonomy, causal correctness, effect success, or model quality.

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

A passing validator means only that the receipt is structurally coherent with this source contract. Runtime credit still requires an actually observed exact-source Ubuntu boot and exact artifact hashes. J-Space measurements remain `MEASURED_INTERPRETABILITY`, not canonical fact. GWT workspace stability remains a control observation, not truth. Claude Code results remain candidate inference.

The current `FREE_ONLY` execution boundary remains unchanged. This contract performs no provider key lookup, network request, training, billed create, or paid execution.
