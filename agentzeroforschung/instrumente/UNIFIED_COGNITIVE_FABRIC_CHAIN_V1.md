# UNIFIED COGNITIVE FABRIC CHAIN / v1

Status: SOURCE/MECHANISM CANDIDATE — RUNTIME CREDIT ZERO

This is composition, not a new receipt family, state authority, truth authority, or second boot validator.

```claycode
chain UCF_RUNTIME_CHAIN_V1 {
  boot := canonical_validate(JSPACE_GWT_BOOT_BINDING_RECEIPT/v1, bundled_manifest, repository_source_lock);
  cycle := canonical_validate(UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1);

  require cycle.boot_binding.receipt_sha256 == sha256(canonical_json(boot.receipt));
  require cycle.boot_binding.manifest_file_sha256 == sha256(boot.manifest_bytes);
  require cycle.boot_binding.source_lock_sha256 == sha256(canonical_json(boot.source_lock));
  require all(cycle.boot_binding.digests != placeholder_zero_or_ff);

  require boot.source.dirty == false;
  require cycle.source(commit, tree) == boot.source(main_sha, tree_sha);
  require cycle.core(manifest, checkpoint, tokenizer, runtime) == boot.core(manifest, checkpoint, tokenizer, runtime);
  require cycle.identity(Zero, GRF) == boot.identity(Zero, GRF);
  require cycle.fabric(jspace_profile, lens_profile?, workspace_policy, workspace_calibration) == boot.fabric(jspace_profile, lens_profile?, workspace_policy, workspace_calibration);
  require Claude_Code -> cycle.adapter(version, capability_profile) == boot.claude_adapter(version, capability_profile);

  law SELF_CONSISTENT_RUNTIME_OBSERVATION != SOURCE_AUTHORITY;
  law VALID_CYCLE != VALID_BOOT_ANCESTRY;
  law SOURCE_LOCK_UNBOUND -> NO_CHAIN_PASS;
  law JSPACE_SIGNAL != FACT;
  law MODEL_RESULT == CANDIDATE_ONLY;
}
```

The executable composition is `validate_unified_cognitive_fabric_chain_v1.py`. It reuses the canonical boot validator and the canonical UCF receipt validator, then adds only ancestry/cross-stage identity checks.

## Counterexample

A caller may coherently rewrite all self-reported checkpoint/tokenizer/runtime/J-Space/lens/workspace identities in boot and cycle evidence. That still cannot pass against the unchanged repository source lock.

The falsifier intentionally uses non-placeholder alternate digests. After the canonical placeholder guard landed, the historical `ffff...` poison is rejected earlier and no longer tests source-lock ancestry.

## Evidence boundary

Source tests can establish only fail-closed composition behavior. They do not establish exact Ubuntu runtime execution, real Qwen3.5 weight loading, Jacobian-Lens execution, measured GWT calibration, Claude runtime success, model quality, Whole-GWT PASS, or whole-product PASS.
