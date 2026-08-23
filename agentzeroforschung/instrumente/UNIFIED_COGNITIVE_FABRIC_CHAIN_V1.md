# UNIFIED COGNITIVE FABRIC CHAIN / v1

Status: SOURCE/MECHANISM CANDIDATE — RUNTIME CREDIT ZERO

This is **not** a new receipt family and **not** a second boot validator. It composes the two existing authorities:

```claycode
chain UCF_RUNTIME_CHAIN_V1 {
  boot := canonical_validate(
    JSPACE_GWT_BOOT_BINDING_RECEIPT/v1,
    bundled_manifest,
    repository_source_lock
  );

  cycle := canonical_validate(UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1);

  require cycle.boot_binding.schema == "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1";
  require cycle.boot_binding.receipt_sha256 == sha256(canonical_json(boot.receipt));
  require cycle.boot_binding.manifest_file_sha256 == sha256(boot.manifest_bytes);
  require cycle.boot_binding.source_lock_sha256 == sha256(canonical_json(boot.source_lock));
  require all(cycle.boot_binding.digests != placeholder_zero_or_ff);

  require boot.source.dirty == false;
  require cycle.source(commit, tree) == boot.source(main_sha, tree_sha);
  require cycle.core(manifest, checkpoint, tokenizer, runtime)
       == boot.core(manifest, checkpoint, tokenizer, runtime);
  require cycle.identity(Zero, GRF) == boot.identity(Zero, GRF);
  require cycle.fabric(jspace_profile, lens_profile?, workspace_policy, workspace_calibration)
       == boot.fabric(jspace_profile, lens_profile?, workspace_policy, workspace_calibration);
  require Claude_Code -> cycle.adapter(version, capability_profile)
       == boot.claude_adapter(version, capability_profile);

  law SELF_CONSISTENT_RUNTIME_OBSERVATION != SOURCE_AUTHORITY;
  law VALID_CYCLE != VALID_BOOT_ANCESTRY;
  law SOURCE_LOCK_UNBOUND -> NO_CHAIN_PASS;
  law JSPACE_SIGNAL != FACT;
  law MODEL_RESULT == CANDIDATE_ONLY;
  law FREE_ONLY -> secret_touch_count==0 && network_touch_count==0;
}
```

Canonical executable composition:

`agentzeroforschung/instrumente/validate_unified_cognitive_fabric_chain_v1.py`

It imports and reuses:

- `the artefact/blogpost_entity/jspace_gwt/validate_jspace_gwt_boot_binding_v1.py` for the complete boot receipt + bundled manifest + repository source-lock gate;
- `agentzeroforschung/instrumente/validate_unified_cognitive_fabric_receipt_v1.py` for the downstream Fabric-cycle structure/authority gate.

The chain adds only ancestry and cross-stage identity checks. It does not duplicate either validator's semantics.

## Required cycle addition

`UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1` carries:

```json
{
  "boot_binding": {
    "schema": "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1",
    "receipt_sha256": "<sha256 canonical boot receipt>",
    "manifest_file_sha256": "<sha256 exact bundled manifest bytes>",
    "source_lock_sha256": "<sha256 canonical repository source lock>"
  }
}
```

Unknown, missing, placeholder, dirty, UNBOUND or identity-divergent boot ancestry fails closed.

## Strong deterministic counterexample

A caller may coherently rewrite **all** self-reported checkpoint/tokenizer/J-Space/lens/workspace identities in both boot and cycle evidence. That still cannot pass if the repository-owned source lock remains unchanged: the canonical boot validator rejects the alternate manifest before the Fabric cycle receives ancestry credit.

The counterexample deliberately uses non-placeholder alternate digests. This matters because placeholder identities are now rejected earlier by the canonical boot/manifest guards; using `ffff...` as the poisoned checkpoint would no longer exercise the intended source-lock ancestry mechanism.

## Evidence boundary

A source test PASS means only that the composition mechanism is fail-closed under its fixtures. It does **not** imply exact Ubuntu/AgentZero execution, real Qwen3.5 weights, Jacobian-Lens runtime success, measured GWT calibration, Claude adapter runtime PASS, model quality, Whole-GWT PASS or whole-product PASS.

Current repository source lock is intentionally `UNBOUND`; therefore real chain promotion remains blocked until exact bundled artifact bytes are measured and admitted.
