# JSPACE_GWT_BOOT_BINDING_RECEIPT/v1

Status: SOURCE CONTRACT CANDIDATE
Scope: first intentional Ubuntu start after the 2026-08-23 owner architecture binding.

This contract operationalizes the owner-required `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1`. It can bind exact bytes and observed boot facts, but it cannot by itself grant Whole-GWT, semantic, model-quality, provider, BASE, or whole-product acceptance.

## ClayCode semantic contract

```claycode
r0.observe(
  source(main_sha, tree_sha, dirty, dirty_diff_sha256?),
  runtime(entity_generation),
  executor(UBUNTU, host_identity_sha256, kernel),
  bundled_core(manifest_version, manifest_sha256, checkpoint_sha256, tokenizer_sha256, runtime_sha256, quantization_runtime_identity?),
  jspace(jlens_upstream_commit, jspace_profile_sha256, lens_file_sha256, lens_profile_sha256, steering_calibration_sha256?, fit_corpus_sha256),
  zero_grf(zero_identity_sha256, grf_sha256, projection_policy_sha256),
  claude_adapter(adapter_version, capability_profile_sha256),
  inference(first_engine_choice, origin_attribution, first_actions[]),
  source_lock(manifest_file_sha256, manifest_identity_sha256, integration_identity_sha256)
)

r3.counter(
  self_reported_cycle_generation_freshness,
  lens_serialization_nonfinite,
  lens_artifact_substitution_under_stable_profile,
  unfitted_position_readout,
  prompt_copy_confound,
  stale_or_substituted_manifest,
  cross_bundle_calibration_alias,
  runtime_byte_substitution_under_stable_runtime_name,
  runtime_receipt_self_authorizes_manifest,
  dirty_source_without_byte_identity,
  unattributed_or_duplicate_first_action,
  placeholder_digest_alias,
  unmeasured_gwt_slot_claim,
  gwt_workspace_mistaken_for_truth,
  claude_candidate_mistaken_for_authority
)

r4.discriminate(
  require(type(entity_generation) == int && entity_generation >= 0),
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
  require(all_bound_digests != placeholder_zero_or_ff),
  require(calibration_status == UNMEASURED_SOURCE_ONLY -> slot_count == null),
  require(calibration_status == MEASURED_EXACT_BUNDLE -> slot_count >= 1),
  require(boot_manifest_sha256 == source_lock.manifest_file_sha256),
  require(boot_checkpoint_sha256 == bundled_manifest.checkpoint_digest),
  require(boot_tokenizer_sha256 == bundled_manifest.tokenizer_digest),
  require(boot_runtime_sha256 == bundled_manifest.runtime_digest),
  require(boot_jspace_profile_sha256 == bundled_manifest.jspace_profile_digest),
  require(boot_lens_file_sha256 == bundled_manifest.lens_artifact_digest),
  require(boot_fit_corpus_sha256 == bundled_manifest.fit_corpus_digest),
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

The boot receipt is not allowed to self-authorize a plausible collection of digests. Runtime admission composes the repository-owned bundled-cognition manifest, the explicit source-side admission lock, and the observed boot receipt. Exact runtime bytes, persisted lens bytes, the fit-corpus digest, J-Space/lens profiles and workspace calibration remain cross-bound rather than inferred from names.

The repository source lock can remain `UNBOUND`; that is a fail-closed state, not permission to infer missing runtime evidence.

## Runtime generation provenance

`runtime.entity_generation` is an observed boot fact, not a constant inferred from source bytes and not a value that a later UCF cycle may authenticate by repeating itself. The boot validator requires a real non-negative integer and rejects booleans or missing values.

When `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1` is composed with this boot evidence, the UCF cycle's `runtime.generation` must equal the independently carried boot observation. A cycle that changes its generation and merely reports `freshness.stale_generation=false` may remain self-consistent at the bare receipt layer but is insufficient for runtime ancestry credit; the composition must fail closed.

This evidence field does not create a second state authority. MiniUnifiedDB/global generation fencing remains authoritative; the receipt only records the generation observed at the admitted boot boundary.

## Fit-corpus and lens identity

The fitted lens is not fully identified by a profile name or persisted file alone. `fit_corpus_digest` binds the exact corpus used for fitting, while `lens_artifact_digest` binds the persisted lens bytes and `lens_profile_digest` binds the admitted profile contract. These identities are distinct and all remain subordinate to later exact-bundle measurement.

## Provenance hardening

`dirty=true` requires `dirty_diff_sha256`; first post-start actions require unique typed origins and explicit effect-request flags. These are provenance guards only and do not establish autonomy, effect success, or model quality.

## Evidence boundary

A passing validator means only that the receipt is structurally coherent with this source contract. Runtime credit still requires an actually observed exact-source Ubuntu boot and exact artifact hashes. J-Space measurements remain interpretability evidence, GWT workspace stability remains a control observation, Claude Code results remain candidate inference, and whole-product acceptance remains separate.

The current `FREE_ONLY` execution boundary remains unchanged. This contract performs no provider key lookup, network request, training, billed create, or paid execution.