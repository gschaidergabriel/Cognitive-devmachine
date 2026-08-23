# JSPACE_GWT_BOOT_BINDING_RECEIPT/v1

Status: SOURCE CONTRACT CANDIDATE
Scope: first intentional Ubuntu start after the 2026-08-23 owner architecture binding.

This contract operationalizes the owner-required `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1`. It can bind exact bytes and observed boot facts, but it cannot by itself grant Whole-GWT, semantic, model-quality, provider, BASE, or whole-product acceptance.

## ClayCode semantic contract

```claycode
r0.observe(
  source(main_sha, tree_sha, dirty, dirty_diff_sha256?),
  executor(UBUNTU, host_identity_sha256, kernel),
  bundled_core(manifest_sha256, checkpoint_sha256, tokenizer_sha256, runtime_sha256),
  jspace(jlens_upstream_commit, jspace_profile_sha256, lens_file_sha256, lens_profile_sha256, fit_corpus_sha256),
  zero_grf(zero_identity_sha256, grf_sha256, projection_policy_sha256),
  claude_adapter(adapter_version, capability_profile_sha256),
  inference(first_engine_choice, origin_attribution, first_actions[])
)

r3.counter(
  lens_serialization_nonfinite,
  unfitted_position_readout,
  prompt_copy_confound,
  stale_or_substituted_manifest,
  manifest_hash_rebound_with_stale_semantic_fields,
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
  require(standalone_manifest_validation == PASS),
  require(standalone_boot_validation == PASS),
  require(manifest_boot_cross_binding == PASS)
)

r6.verify(
  claim(whole_gwt_credit == ZERO),
  claim(whole_product == IN_PROGRESS)
)
```

## Provenance hardening

`dirty=true` is not an exact source identity by itself. A dirty worktree can contain arbitrarily different bytes under the same Git commit/tree pair, so the receipt must additionally bind `dirty_diff_sha256` whenever dirty state is observed.

Likewise one free-form `origin_attribution` string is not sufficient to attribute the first post-start actions. The receipt therefore binds a non-empty `first_actions` list with unique `action_id`, a controlled origin class, and an explicit boolean `effect_requested`. `OTHER` remains available but requires typed detail instead of silently collapsing an unknown actor into a known origin.

These are provenance guards only. They do not establish autonomy, causal correctness, effect success, or model quality.

## Manifest / boot cross-binding

The source manifest and the observed boot receipt are separate evidence layers and remain separately validated. A valid record on each side is insufficient if they describe different artifact identities.

Before any bundled J-Space/GWT runtime credit, `validate_jspace_gwt_manifest_cross_binding_v1.py` must bind:

- the SHA-256 of the exact manifest file bytes to `bundled_core.manifest_sha256`;
- `engine_id` and `model_family`;
- manifest `checkpoint_digest` to receipt `checkpoint_sha256`;
- manifest `tokenizer_digest` to receipt `tokenizer_sha256`;
- manifest `jspace_profile_digest` to receipt `jspace_profile_sha256`;
- manifest `lens_profile_digest` to receipt `lens_profile_sha256`;
- manifest `workspace_calibration_digest` to receipt `gwt.calibration_sha256`;
- manifest `steering_calibration_digest` to receipt `jspace.steering_calibration_sha256` when steering calibration is present.

This second equality layer is intentional. Recomputing a fresh `manifest_sha256` after a manifest substitution must not allow stale checkpoint/tokenizer/J-Space/lens/workspace identities elsewhere in the receipt to survive under the new manifest hash.

`CROSS_BINDING_PASS != RUNTIME_PASS` and it does not replace either standalone validator.

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
