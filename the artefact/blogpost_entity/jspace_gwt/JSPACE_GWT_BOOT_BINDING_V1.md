# JSPACE_GWT_BOOT_BINDING_RECEIPT/v1

Status: SOURCE CONTRACT CANDIDATE
Scope: first intentional Ubuntu start after the 2026-08-23 owner architecture binding.

This contract operationalizes the owner-required `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1`. It can bind exact bytes and observed boot facts, but it cannot by itself grant Whole-GWT, semantic, model-quality, provider, BASE, or whole-product acceptance.

## ClayCode semantic contract

```claycode
r0.observe(
  source(main_sha, tree_sha, dirty, dirty_diff_sha256?),
  executor(UBUNTU, host_identity_sha256, kernel),
  bundled_core(manifest_version, manifest_sha256, checkpoint_sha256, tokenizer_sha256, runtime_sha256, quantization_runtime_identity?, cognition_mode),
  jspace(jlens_upstream_commit, jspace_profile_sha256, lens_file_sha256, lens_profile_sha256, steering_calibration_sha256?, fit_corpus_sha256),
  zero_grf(zero_identity_sha256, grf_sha256, projection_policy_sha256),
  claude_adapter(adapter_version, capability_profile_sha256),
  inference(first_engine_choice, origin_attribution, first_actions[]),
  source_lock(manifest_file_sha256, manifest_identity_sha256, integration_identity_sha256, runtime_sha256)
)

r3.counter(
  lens_serialization_nonfinite,
  unfitted_position_readout,
  prompt_copy_confound,
  stale_or_substituted_manifest,
  cross_bundle_calibration_alias,
  runtime_receipt_self_authorizes_manifest,
  caller_substitutes_source_lock,
  caller_substitutes_admitted_manifest,
  nonlocal_engine_claims_local_latent_credit,
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
  require(cognition_mode in [FULL_LOCAL_LATENT, LOCAL_OBSERVE_ONLY]),
  require(boot_manifest_sha256 == source_lock.manifest_file_sha256),
  require(boot_checkpoint_sha256 == bundled_manifest.checkpoint_digest),
  require(boot_tokenizer_sha256 == bundled_manifest.tokenizer_digest),
  require(boot_runtime_sha256 == source_lock.runtime_sha256),
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

## Fixed repository trust anchor

The boot receipt is not allowed to self-authorize a plausible collection of digests. Runtime admission composes three separately scoped objects:

1. the repository-owned canonical `mini-entity-bundled-cognition-manifest/v1` at the fixed path `the artefact/blogpost_entity/mini_cognition/bundled_cognition_manifest_admitted_v1.json`;
2. `BUNDLED_COGNITION_SOURCE_LOCK/v1` at the fixed path `the artefact/blogpost_entity/mini_cognition/bundled_cognition_source_lock_v1.json`;
3. the observed `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1` supplied by the booting runtime.

The caller may supply only the observed receipt. It may not select or substitute the admitted manifest or source-lock path. A string such as `authority=repository_source_tree` inside caller-controlled bytes is not sufficient authority; the validator itself chooses the repository-owned trust-anchor files relative to its own checked-in location.

The source lock binds the raw admitted-manifest file digest, the manifest validator's complete and semantic integration identities, and the exact local runtime artifact digest. The boot receipt must then match that admitted bundle for engine/model/checkpoint/tokenizer/runtime, optional quantization/runtime identity, J-Space profile, lens profile, optional steering calibration and workspace calibration.

The repository ships the source-lock file intentionally as `UNBOUND`. This is a fail-closed state, not a missing-data convenience: all identity fields remain null until exact bundled checkpoint/tokenizer/runtime/J-Space/lens/workspace artifacts have been measured, the fixed admitted manifest has been created, and those exact identities have been explicitly reviewed and bound. `UNBOUND` cannot admit cognition.

Only the local bundled modes `FULL_LOCAL_LATENT` and `LOCAL_OBSERVE_ONLY` may pass this boot gate. `COMPILED_EXTERNAL` and other remote/closed-engine modes cannot receive local J-Space/hidden-state credit through this receipt.

Validation CLI:

```text
python validate_jspace_gwt_boot_binding_v1.py RECEIPT.json
```

Alternate caller-supplied manifest/source-lock paths are intentionally rejected. This preserves `PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY`: a valid-looking J-Space/lens/workspace tuple or a self-authored source lock from another calibration bundle cannot receive boot admission merely because every individual digest is syntactically valid.

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

A passing validator means only that the observed receipt matches the repository-owned admitted bundle and source-lock contract. Runtime credit still requires an actually observed exact-source Ubuntu boot and exact artifact hashes. J-Space measurements remain `MEASURED_INTERPRETABILITY`, not canonical fact. GWT workspace stability remains a control observation, not truth. Claude Code results remain candidate inference.

The current `FREE_ONLY` execution boundary remains unchanged. This contract performs no provider key lookup, network request, training, billed create, or paid execution.
