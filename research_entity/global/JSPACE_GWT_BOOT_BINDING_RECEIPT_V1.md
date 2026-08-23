# JSPACE_GWT_BOOT_BINDING_RECEIPT/v1

Status: SOURCE CONTRACT / CURRENT GO CANDIDATE
Owner-architecture dependency: 2026-08-23 unified Mini Entity / EntityOS / Zero J-Space/GWT architecture.

Purpose: make the first intentional Ubuntu host restart an exact identity-observation boundary before any J-Space/GWT, bundled-cognition, Claude-adapter, semantic, BASE or whole-product runtime credit can be considered.

## ClayCode contract

```clay
receipt JSPACE_GWT_BOOT_BINDING_RECEIPT/v1 {
  source := bind(git.commit, git.tree, worktree.dirty, worktree.diff_digest?)
  executor := bind(os, machine_id_digest, runner_identity_digest)
  prestart := bind(generation, agentzero_export_head, receipt_source_short)

  expected := bind(
    bundled_core_manifest_digest,
    checkpoint_digest,
    tokenizer_digest,
    runtime_digest,
    jspace_profile_digest,
    workspace_policy_digest,
    zero_identity_digest,
    grf_projection_digest,
    claude_adapter_digest,
    claude_capability_profile_digest,
    lens_profile_digest?,
    steering_calibration_digest?
  )

  observed := observe_same_identity_set(expected)
  poststart := bind(first_generation, first_inference_engine_choice, first_actions[])

  require exact(expected, observed)
  require attributed(first_actions.origin)
  require dirty(source) -> sha256(source.dirty_diff_digest)
  require no_unexpected(observed - expected)
  require boot_binding_credit == BOUND_OBSERVATION_ONLY
  require runtime_credit == 0
  require semantic_credit == 0
}
```

## Required fail-closed semantics

1. Every required identity digest is lowercase SHA-256 and must exist in both the expected and observed binding maps.
2. Optional lens/steering identities must either exist on both sides or neither side. Presence asymmetry is rejection.
3. A matching model family, engine id or checkpoint name is not sufficient. Exact digest mismatch in checkpoint, tokenizer, runtime, J-Space profile, workspace policy, Zero/GRF projection or Claude adapter identity rejects the binding.
4. Dirty source requires an explicit dirty-diff digest. A dirty tree without a bound diff identity is not an exact-source boot.
5. First actions must be attributed to `ZERO`, `HOOK_TIMER`, `CLAUDE_CODE`, `PROXY_SANDBOX_CONTROLLER`, or typed `OTHER` with detail. Unknown/unattributed origin is rejection.
6. This receipt is deliberately incapable of granting J-Space/GWT/model/Claude/semantic runtime PASS. It establishes only that the observed boot is identity-bound enough for later behavioral receipts to be meaningful.

## One bounded unusual discriminator for this `go`

`DIGEST_ALIAS_POISON`

Counter-reality: two runtime configurations share the same apparent engine/checkpoint identity while the tokenizer digest differs. A weak boot gate keyed by model id/checkpoint label would alias them and could incorrectly reuse a J-Space/lens/workspace calibration.

Required result: `BINDING_MISMATCH:tokenizer_digest` and no runtime/semantic credit.

The deterministic validator is `tools/validate_jspace_gwt_boot_binding.py`; focused regressions are `tests/test_validate_jspace_gwt_boot_binding.py`.

## Evidence boundary

A validator PASS is `SOURCE_BOUND_BOOT_OBSERVATION_ONLY`. It is not evidence that the bundled ~0.8B checkpoint is good, that a Jacobian lens is calibrated, that GWT behavior is correct, that Claude Code is safely integrated, that Zero is autonomous, or that BASE/whole-product acceptance passed. Those claims require separate exact-source Ubuntu execution and behavioral receipts after the intentional host start.
