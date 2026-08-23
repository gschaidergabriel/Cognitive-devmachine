# JSPACE_GWT_BOOT_BINDING_RECEIPT/v1

Status: source/mechanism admission instrument.  
Scope: first intentional Ubuntu/EntityOS start after the J-Space/GWT owner-architecture binding.

## ClayCode/GRF contract

```text
R0 OBSERVE {
  host_state = INTENTIONALLY_OFFLINE_BEFORE_START
  architecture_credit = OWNER_SOURCE_ONLY
  jspace_runtime_credit = 0
  whole_gwt_credit = 0
}

R2 GENERATE receipt JSPACE_GWT_BOOT_BINDING_RECEIPT/v1 {
  bind(source.commit, source.tree, dirty_state)
  bind(bundled_core_manifest, checkpoint, tokenizer, local_runtime)
  bind(jacobian_lens -> checkpoint, tokenizer, d_model, source_layers)
  bind(workspace_policy, zero_identity, grf_projection)
  bind(claude_adapter, claude_capability_profile)
  bind(first_engine_choice, first_action_origin, inference_packet)
  bind(FREE_ONLY, paid_or_unknown_provider_network_attempted = false)
}

R3 COUNTER {
  H_foreign_lens := lens bytes are valid but fitted for another checkpoint/tokenizer
  H_split_fabric := J-Space and GWT boot as independent unbound authorities
  H_origin_gap := first action occurs without attributable engine/origin
}

R4 DISCRIMINATE {
  reject digest/path mismatch
  reject foreign checkpoint/tokenizer lens provenance
  reject d_model/layer incompatibility
  reject fabric_mode != UNIFIED_JSPACE_GWT
  reject missing Claude boundary expectations
  reject paid/unknown provider network under FREE_ONLY
}

R6 VERIFY {
  PASS => credit = BOOT_BINDING_ONLY
  PASS != model_quality
  PASS != semantic_truth
  PASS != whole_runtime
  PASS != whole_GWT
  PASS != BASE
}
```

## Why this gate exists

The current owner architecture makes J-Space and GWT one cognitive fabric and keeps Claude Code as targeted candidate inference rather than identity, truth, durable-memory, or effect authority. The supervisor requires exact boot binding before granting any J-Space/GWT runtime credit.

The upstream Anthropic Jacobian Lens is model-specific: it stores per-layer Jacobian matrices with a fixed residual width (`d_model`) and transports residuals with those fitted matrices. Therefore a lens artifact that is individually well-formed but belongs to another checkpoint/tokenizer is a dangerous false-green unless provenance and geometry are cross-bound at boot.

## Required artifact roles

Every receipt binds an exact file under the admitted root with `path`, `sha256`, and `size_bytes`:

- `bundled_core_manifest`
- `checkpoint`
- `tokenizer`
- `local_runtime`
- `jacobian_lens`
- `workspace_policy`
- `zero_identity`
- `grf_projection`
- `claude_adapter`
- `claude_capability_profile`

The verifier resolves every path strictly under the supplied root, hashes the file, checks size, and fails closed on missing/escaped/substituted bytes.

## Required cross-bindings

- `core.checkpoint_sha256 == artifacts[checkpoint].sha256`
- `core.tokenizer_sha256 == artifacts[tokenizer].sha256`
- `jspace_lens.artifact_sha256 == artifacts[jacobian_lens].sha256`
- `jspace_lens.source_checkpoint_sha256 == core.checkpoint_sha256`
- `jspace_lens.source_tokenizer_sha256 == core.tokenizer_sha256`
- `jspace_lens.d_model == core.d_model`
- every `source_layer` is unique, sorted, integer, and inside `[0, layer_count)`
- `workspace.fabric_mode == UNIFIED_JSPACE_GWT`
- workspace, Zero identity and GRF digests equal their bound artifact digests
- Claude adapter and capability-profile digests equal their bound artifacts
- expected boundary flags are all true: tool-less, ephemeral, structured-output, environment-isolated
- `control.free_only == true`
- `control.paid_or_unknown_provider_network_attempted == false`

## First-action attribution

The first admitted action binds:

- `engine_class`: `LOCAL_HOOKABLE | CLAUDE_CODE | DETERMINISTIC_TOOL | NO_MODEL_REQUIRED`
- `origin`: engine class or explicit `HOOK | TIMER | PROXY_CONTROLLER | SANDBOX_CONTROLLER | OTHER`
- `inference_packet_sha256`

This prevents a post-start action from being retroactively attributed to Zero/Claude/J-Space merely because it happened after boot.

## Deterministic negative regressions

The focused test suite includes a cross-checkpoint lens-provenance mismatch: every test artifact may exist and hash correctly, while the lens declares a different checkpoint digest. Required result: `LENS_SOURCE_CHECKPOINT_MISMATCH` and no credit.

This is an ordinary deterministic negative regression. It is **not** an unusual-experiment lease claim.

For the user-triggered `go` that created this instrument, the available immutable user-message timestamp was only minute precision (`2026-08-23T09:51+07:00`). Under `GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md`, no canonical timestamp-fallback lease key may be invented from that metadata. Macrocycle classification is therefore:

`COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`

## Verifier

```bash
python tools/verify_jspace_gwt_boot_binding.py RECEIPT.json --root /admitted/entityos/root
```

`--no-file-check` exists only for schema/cross-binding review and can never be runtime evidence.

## Evidence law

`ARCHITECTURE_SOURCE_PRESENT != BOOT_BINDING_PASS != JSPACE_RUNTIME_PASS != WHOLE_GWT_PASS`

A passing boot-binding receipt proves only that the named start boundary is internally exact and compatible enough to begin runtime evaluation. Runtime behavior, model quality, workspace semantics, Claude boundary behavior, J-Space causal usefulness and production acceptance still require separate executable receipts.
