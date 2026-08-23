# JSPACE_GWT_BOOT_BINDING_RECEIPT/v1

Status: SOURCE CONTRACT CANDIDATE  
Scope: first intentional Ubuntu start after the 2026-08-23 owner architecture binding.

This contract operationalizes the owner-required `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1`. It can bind exact bytes and observed boot facts, but it cannot by itself grant Whole-GWT, semantic, model-quality, provider, BASE, or whole-product acceptance.

## ClayCode semantic contract

```claycode
r0.observe(
  source(main_sha, tree_sha, dirty),
  executor(UBUNTU, host_identity_sha256, kernel),
  bundled_core(manifest_sha256, checkpoint_sha256, tokenizer_sha256, runtime_sha256, layer_count, d_model),
  jspace(jlens_upstream_commit, lens_file_sha256, lens_profile_sha256, fit_corpus_sha256,
         source_checkpoint_sha256, source_tokenizer_sha256, d_model, source_layers),
  gwt(workspace_policy_sha256, calibration_sha256),
  zero_grf(zero_identity_sha256, grf_sha256, projection_policy_sha256),
  claude_adapter(adapter_version, capability_profile_sha256),
  inference(first_engine_choice, origin_attribution, inference_packet_sha256),
  control(FREE_ONLY, paid_or_unknown_provider_network_attempted = false),
  artifact_bindings(path, sha256, size_bytes)
)

r3.counter(
  boolean_exact_bytes_without_hashing,
  path_escape_or_artifact_substitution,
  cross_checkpoint_or_cross_tokenizer_lens_transplant,
  residual_width_or_layer_geometry_mismatch,
  lens_serialization_nonfinite,
  unfitted_position_readout,
  prompt_copy_confound,
  gwt_workspace_mistaken_for_truth,
  claude_candidate_mistaken_for_authority
)

r4.discriminate(
  hash_every_bound_artifact_under_one_explicit_root,
  require(jspace.source_checkpoint_sha256 == bundled_core.checkpoint_sha256),
  require(jspace.source_tokenizer_sha256 == bundled_core.tokenizer_sha256),
  require(jspace.d_model == bundled_core.d_model),
  require(all(source_layers within bundled_core.layer_count)),
  require(pre_save_all_finite == true),
  require(post_load_all_finite == true),
  require(minimum_readout_position >= skip_first_positions),
  require(all(observed_readout_positions >= minimum_readout_position)),
  require(prompt_copy_confound_guard_enabled == true),
  require(FREE_ONLY == true),
  require(paid_or_unknown_provider_network_attempted == false)
)

r6.verify(
  claim(whole_gwt_credit == ZERO),
  claim(whole_product == IN_PROGRESS)
)
```

## Exact artifact-root binding

`exact_bytes_verified: true` is not trusted as self-authenticating evidence. The validator requires an explicit artifact root and independently resolves, sizes, and SHA-256 hashes every required bound file. Absolute paths, missing files, symlink/path escapes outside the root, size mismatches, declared-digest mismatches, and byte-digest mismatches fail closed.

Required roles:

- `bundled_manifest`
- `checkpoint`
- `tokenizer`
- `runtime`
- `lens_file`
- `lens_profile`
- `fit_corpus`
- `workspace_policy`
- `gwt_calibration`
- `zero_identity`
- `grf`
- `projection_policy`
- `claude_capability_profile`

Run:

```bash
python validate_jspace_gwt_boot_binding_v1.py RECEIPT.json ARTIFACT_ROOT
```

## J-Space provenance and geometry binding

A well-formed lens file is not sufficient. Its receipt must bind the same checkpoint and tokenizer as the bundled core, the same residual width (`d_model`), and a sorted unique set of source layers inside the bundled core's admitted layer range. This blocks a false-green in which valid lens bytes from another checkpoint/runtime are transplanted into the current bundle.

This follows the current owner law that no lens/layer/band/threshold is canonical without exact checkpoint+tokenizer+runtime calibration. It also matches the upstream Jacobian-Lens representation, where fitted per-layer Jacobians act in a model residual width rather than a model-independent universal space.

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

A passing validator means only that the receipt is structurally coherent and the named artifact bytes/provenance are mutually bound under this source contract. Runtime credit still requires an actually observed exact-source Ubuntu boot. J-Space measurements remain `MEASURED_INTERPRETABILITY`, not canonical fact. GWT workspace stability remains a control observation, not truth. Claude Code results remain candidate inference.

The current `FREE_ONLY` execution boundary remains explicit in the receipt. The validator rejects a receipt that does not bind FREE_ONLY or admits a paid/unknown provider-network attempt.
