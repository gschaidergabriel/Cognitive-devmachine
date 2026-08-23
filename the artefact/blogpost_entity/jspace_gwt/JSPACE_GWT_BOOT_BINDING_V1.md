# JSPACE_GWT_BOOT_BINDING_RECEIPT/v1

Status: SOURCE CONTRACT CANDIDATE
Scope: first intentional Ubuntu start after the 2026-08-23 owner architecture binding.

This contract operationalizes the owner-required `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1`. It can bind exact bytes and observed boot facts, but it cannot by itself grant Whole-GWT, semantic, model-quality, provider, BASE, or whole-product acceptance.

## ClayCode semantic contract

```claycode
r0.observe(
  source(main_sha, tree_sha, dirty),
  executor(UBUNTU, host_identity_sha256, kernel),
  bundled_core(manifest_sha256, integration_identity_sha256, checkpoint_sha256, tokenizer_sha256, runtime_sha256),
  jspace(jlens_upstream_commit, lens_file_sha256, lens_profile_sha256, fit_corpus_sha256),
  zero_grf(zero_identity_sha256, grf_sha256, projection_policy_sha256),
  claude_adapter(adapter_version, capability_profile_sha256),
  inference(first_engine_choice, origin_attribution)
)

r3.counter(
  lens_serialization_nonfinite,
  unfitted_position_readout,
  prompt_copy_confound,
  stale_or_substituted_manifest,
  runtime_self_lock_of_observed_manifest,
  gwt_workspace_mistaken_for_truth,
  claude_candidate_mistaken_for_authority
)

r4.discriminate(
  require(repository_source_lock.status == BOUND),
  require(repository_source_lock.authority == repository_source_tree),
  require(manifest_sha256 == repository_source_lock.manifest_identity_sha256),
  require(integration_identity_sha256 == repository_source_lock.integration_identity_sha256),
  require(pre_save_all_finite == true),
  require(post_load_all_finite == true),
  require(minimum_readout_position >= skip_first_positions),
  require(all(observed_readout_positions >= minimum_readout_position)),
  require(prompt_copy_confound_guard_enabled == true),
  require(exact_bytes_verified == true)
)

r6.verify(
  claim(whole_gwt_credit == ZERO),
  claim(whole_product == IN_PROGRESS)
)
```

## Repository source-lock boundary

The boot receipt is an observation. It is not allowed to define its own expected identity.

`bundled_core.manifest_sha256` and `bundled_core.integration_identity_sha256` MUST match the repository-owned `mini_cognition/bundled_cognition_source_lock_v1.json` loaded from the admitted source tree. The boot validator does not accept an alternate source-lock path from the caller.

The checked-in lock is intentionally `UNBOUND` while the exact bundled checkpoint/tokenizer/runtime/J-Space/lens/workspace calibration identities remain unmeasured. Therefore current product boot admission fails closed even if a runtime produces a syntactically complete, internally self-consistent receipt. A later evidence-backed source change may set the lock to `BOUND` only after the existing bundled-cognition manifest validator has produced the exact `manifest_identity_sha256` and `integration_identity_sha256` for the admitted bundle and the referenced evidence receipt is durable.

Invariant:

```claycode
runtime_observation != source_authority
self_consistent_receipt != admitted_bundle
source_lock.status != BOUND -> boot_admission = FAIL_CLOSED
```

This avoids a circular source-commit self-reference: source/tree identity remains explicit observed boot provenance, while the repository source tree itself carries the pre-existing expected bundled-cognition identities.

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

A passing validator means only that the receipt is structurally coherent with this source contract and matches the pre-existing repository bundle lock. Runtime credit still requires an actually observed exact-source Ubuntu boot and exact artifact hashes. J-Space measurements remain `MEASURED_INTERPRETABILITY`, not canonical fact. GWT workspace stability remains a control observation, not truth. Claude Code results remain candidate inference.

The current `FREE_ONLY` execution boundary remains unchanged. This contract performs no provider key lookup, network request, training, billed create, or paid execution.
