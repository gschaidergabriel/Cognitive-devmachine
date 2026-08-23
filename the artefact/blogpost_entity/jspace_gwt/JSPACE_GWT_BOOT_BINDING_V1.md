# JSPACE_GWT_BOOT_BINDING_RECEIPT/v1

Status: SOURCE CONTRACT CANDIDATE
Scope: first intentional Ubuntu start after the 2026-08-23 owner architecture binding.

This contract operationalizes the owner-required `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1`. It binds repository admission identity **and** independently observed artifact bytes. It cannot by itself grant Whole-GWT, semantic, model-quality, provider, BASE, causal-use, or whole-product acceptance.

## ClayCode semantic contract

```claycode
r0.observe(
  source(main_sha, tree_sha, dirty, dirty_diff_sha256?),
  executor(UBUNTU, host_identity_sha256, kernel),
  bundled_core(manifest_version, manifest_sha256, checkpoint_sha256, tokenizer_sha256, runtime_sha256, layer_count, d_model, quantization_runtime_identity?),
  jspace(jlens_upstream_commit, jspace_profile_sha256, lens_file_sha256, lens_profile_sha256, steering_calibration_sha256?, fit_corpus_sha256, source_checkpoint_sha256, source_tokenizer_sha256, d_model, source_layers[]),
  gwt(workspace_policy_sha256, calibration_sha256, calibration_status, slot_count?),
  zero_grf(zero_identity_sha256, grf_sha256, projection_policy_sha256),
  claude_adapter(adapter_version, capability_profile_sha256, enabled),
  inference(first_engine_choice, origin_attribution, inference_packet_sha256, first_actions[]),
  control(free_only, paid_or_unknown_provider_network_attempted),
  artifact_bindings(role -> path + sha256 + size_bytes),
  source_lock(manifest_file_sha256, manifest_identity_sha256, integration_identity_sha256)
)

r3.counter(
  boolean_exact_bytes_without_hashing,
  path_escape_or_artifact_substitution,
  cross_checkpoint_or_cross_tokenizer_lens_transplant,
  residual_width_or_layer_geometry_mismatch,
  jspace_profile_byte_substitution,
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
  unbound_inference_packet,
  placeholder_digest_alias,
  unmeasured_gwt_slot_claim,
  paid_or_unknown_provider_network_under_free_only,
  gwt_workspace_mistaken_for_truth,
  claude_candidate_mistaken_for_authority
)

r4.discriminate(
  require(dirty == true -> sha256(dirty_diff_sha256)),
  require(unique(first_actions.action_id)),
  require(first_actions.origin in [ZERO, HOOK_TIMER, CLAUDE_CODE, PROXY_SANDBOX_CONTROLLER, OTHER]),
  require(first_actions.origin == OTHER -> nonempty(origin_detail)),
  require(type(first_actions.effect_requested) == bool),
  require(sha256(inference_packet) == inference_packet_sha256),
  require(pre_save_all_finite == true),
  require(post_load_all_finite == true),
  require(minimum_readout_position >= skip_first_positions),
  require(all(observed_readout_positions >= minimum_readout_position)),
  require(prompt_copy_confound_guard_enabled == true),
  require(exact_bytes_verified == true),
  require(all_required_artifacts_opened_and_hashed_under_one_root),
  require(jspace.source_checkpoint_sha256 == bundled_core.checkpoint_sha256),
  require(jspace.source_tokenizer_sha256 == bundled_core.tokenizer_sha256),
  require(jspace.d_model == bundled_core.d_model),
  require(source_layers == sorted(unique(source_layers))),
  require(all(source_layers within bundled_core.layer_count)),
  require(all_bound_digests != placeholder_zero_or_ff),
  require(calibration_status == UNMEASURED_SOURCE_ONLY -> slot_count == null),
  require(calibration_status == MEASURED_EXACT_BUNDLE -> slot_count >= 1),
  require(boot_manifest_sha256 == source_lock.manifest_file_sha256),
  require(boot_checkpoint_sha256 == bundled_manifest.checkpoint_digest),
  require(boot_tokenizer_sha256 == bundled_manifest.tokenizer_digest),
  require(boot_runtime_sha256 == bundled_manifest.runtime_digest),
  require(boot_jspace_profile_sha256 == bundled_manifest.jspace_profile_digest),
  require(boot_lens_file_sha256 == bundled_manifest.lens_artifact_digest),
  require(boot_lens_profile_sha256 == bundled_manifest.lens_profile_digest),
  require(boot_workspace_calibration_sha256 == bundled_manifest.workspace_calibration_digest),
  require(source_lock.integration_identity_sha256 == bundled_manifest.integration_identity_sha256),
  require(free_only == true),
  require(paid_or_unknown_provider_network_attempted == false)
)

r6.verify(
  claim(whole_gwt_credit == ZERO),
  claim(whole_product == IN_PROGRESS)
)
```

## Two independent provenance layers

The boot receipt is not allowed to self-authorize a plausible collection of digest strings. Runtime admission composes two independent mechanisms that must both pass:

1. **Repository admission identity**
   - canonical `mini-entity-bundled-cognition-manifest/v1`;
   - `BUNDLED_COGNITION_SOURCE_LOCK/v1`;
   - boot receipt fields cross-bound to manifest identity.

2. **Observed artifact-byte identity**
   - an explicit `ARTIFACT_ROOT` supplied at validation time;
   - every required role resolves beneath that root;
   - path, file type, size, declared SHA-256 and independently computed SHA-256 must agree.

Neither mechanism substitutes for the other. The source lock proves which integration the repository admits; artifact-root verification proves that the runtime receipt actually points at those bytes rather than merely repeating their names or digests.

Required artifact roles are:

- `bundled_manifest`;
- `checkpoint`;
- `tokenizer`;
- `runtime`;
- `jspace_profile`;
- `lens_file`;
- `lens_profile`;
- `fit_corpus`;
- `workspace_policy`;
- `gwt_calibration`;
- `zero_identity`;
- `grf`;
- `projection_policy`;
- `claude_capability_profile`;
- `steering_calibration` only when the receipt declares a steering calibration digest.

Absolute paths, missing files, non-files, symlink/path escape outside the admitted root, size mismatch, declared-digest mismatch and actual byte substitution fail closed.

Validation CLI:

```text
python validate_jspace_gwt_boot_binding_v1.py RECEIPT.json BUNDLED_MANIFEST.json SOURCE_LOCK.json ARTIFACT_ROOT
```

## Atomic bundled-cognition binding

The source lock binds both the raw manifest file digest and the manifest validator's complete and semantic integration identities. The boot receipt must match the admitted manifest for engine/model/checkpoint/tokenizer, exact runtime bytes, exact persisted lens artifact bytes, optional quantization/runtime identity, J-Space profile, lens profile, optional steering calibration and workspace calibration.

`runtime_digest` and `lens_artifact_digest` are identity-bearing in the bundled manifest when present and are mandatory for boot admission. A stable runtime name cannot authorize different executable bytes, and a stable lens profile identity cannot authorize a different persisted lens artifact.

The repository ships the source-lock file intentionally as `UNBOUND`. This is a fail-closed state, not a missing-data convenience: it must remain unable to admit cognition until exact bundled checkpoint/tokenizer/runtime/J-Space/lens/workspace artifacts have been measured and the corresponding manifest has been explicitly admitted.

This composition preserves `PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY`: a valid-looking J-Space/lens/workspace tuple from another calibration bundle cannot receive boot admission merely because every individual digest is syntactically valid.

## J-Space provenance and geometry binding

A well-formed lens file is not sufficient. Its receipt must bind the same checkpoint and tokenizer as the bundled core, the same residual width (`d_model`), and a sorted unique set of source layers inside the bundled core's admitted layer range.

`jspace_profile_sha256` is also independently byte-bound. A profile digest that matches the manifest but does not correspond to the file under the admitted artifact root is rejected.

This closes a false-green where valid lens/profile bytes from another checkpoint/runtime could be transplanted into the current bundle while syntactic digest fields remained mutually plausible.

These guards do **not** prove that a lens is well-conditioned, semantically useful, or causally used by Zero. They establish exact provenance prerequisites for the later perturbation/ablation gate.

## Lens artifact identity versus lens profile identity

`lens_profile_digest` and `lens_artifact_digest` are deliberately distinct:

- `lens_profile_digest` binds the admitted calibration/profile contract;
- `lens_artifact_digest` binds the exact persisted lens file bytes used by the booted bundle.

Neither digest alone substitutes for runtime measurement or proves semantic usefulness. Exact artifact identity only closes substitution under a stable profile identity; model-specific lens quality and causal utility still require exact Qwen/J-Space calibration and intervention evidence.

## Provenance hardening

`dirty=true` is not an exact source identity by itself. A dirty worktree can contain arbitrarily different bytes under the same Git commit/tree pair, so the receipt additionally binds `dirty_diff_sha256` whenever dirty state is observed.

One free-form `origin_attribution` string is not sufficient to attribute the first post-start actions. The receipt therefore binds a non-empty `first_actions` list with unique `action_id`, a controlled origin class, and an explicit boolean `effect_requested`. `OTHER` remains available but requires typed detail.

The receipt additionally binds `inference_packet_sha256`, so the first engine choice cannot be detached from the exact targeted inference packet that was admitted.

These are provenance guards only. They do not establish autonomy, causal correctness, effect success, or model quality.

## Identity and calibration hardening

Cross-binding only helps if every bound identity is real. A syntactically valid SHA containing only zeroes or only `f` characters is rejected by both the bundled cognition manifest validator and the boot/source-lock validator. Test fixtures must use non-placeholder digests.

The GWT slot count follows the owner epistemic law `UNKNOWN != ZERO != MEASURED`:

- `UNMEASURED_SOURCE_ONLY` requires `slot_count: null`;
- `MEASURED_EXACT_BUNDLE` requires an integer `slot_count >= 1` on the exact cross-bound bundle.

`null` means no admitted slot-count measurement. It is neither numeric zero nor an implicit default.

## FREE_ONLY execution fence

The receipt explicitly records `control.free_only` and `control.paid_or_unknown_provider_network_attempted`. The validator fails closed unless FREE_ONLY is true and no paid/unknown-provider network attempt occurred.

This is an evidence/admission fence. It does not itself prove that an external provider was not contacted; the exact executor receipt and network/provider evidence must support the field at runtime.

## External measurement hardening

Current upstream Jacobian-Lens code fits with a configurable leading-position skip whose default is 16. Current upstream issue #5 reports that `apply()` can still return those unfitted positions and that prompt-token copying can confound naive concept-presence measurements. Current upstream issue #6 reports that the default float16 lens serialization can overflow large finite fp32 Jacobians to `inf`.

Therefore this receipt binds the exact upstream commit and makes numeric finiteness plus position-policy checks explicit fail-closed conditions.

Primary upstream references:
- https://github.com/anthropics/jacobian-lens
- https://github.com/anthropics/jacobian-lens/issues/5
- https://github.com/anthropics/jacobian-lens/issues/6
- https://transformer-circuits.pub/2026/workspace/index.html

These guards block known false measurement credit; they do not establish semantic or causal validity.

## Causal-use boundary

Even a perfect boot binding proves **provenance**, not that a J-Space/GWT state changed Zero's behavior.

The next causal promotion gate must compare matched executions where the canonical task/evidence and external Zero interface are held fixed while a bounded J-Space-derived workspace variable is intervened on. At minimum compare:

1. matched no-J-Space/control projection;
2. normal measured J-Space/GWT capsule;
3. one predeclared slot ablation or permutation that preserves receipt identity and does not alter canonical evidence.

A causal-use claim requires a reproducible downstream difference attributable to that intervention and a negative/control condition. Claude self-report, capsule presence, receipt validity, workspace stability or output coherence are not sufficient.

`JSPACE_CAUSAL_USE != JSPACE_PROVENANCE`

`JSPACE_CAUSAL_USE != CLAUDE_SELF_REPORT`

## Evidence boundary

A passing validator means only that the receipt is structurally coherent, cross-bound to the repository-admitted manifest/SOURCE_LOCK identity, and independently bound to the named artifact bytes under the supplied root.

Runtime credit still requires an actually observed exact-source Ubuntu boot. J-Space measurements remain `MEASURED_INTERPRETABILITY`, not canonical fact. GWT workspace stability remains a control observation, not truth. Claude Code results remain candidate inference. Causal-use credit remains zero until intervention evidence exists.

The current `FREE_ONLY` execution boundary remains unchanged. This validator performs no provider key lookup, network request, training, billed create, or paid execution.
