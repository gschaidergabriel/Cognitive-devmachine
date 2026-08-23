# J-Space / GWT Boot Binding Contract v1

Status: SOURCE CANDIDATE / FAIL-CLOSED RUNTIME ADMISSION CONTRACT  
Date: 2026-08-23  
Primary owner architecture: `research_entity/global/ENTITYOS_FIXED_CLAUDE_ADAPTIVE_INFERENCE_INTEGRATION.md`  
Related: `MINI_ENTITY_JSPACE_GWT_INSTRUMENTED_COGNITION.md`, `AGENT_ZERO_GWT_JSPACE_COUPLING.md`

This contract turns the owner-required `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1` from a prose obligation into a machine-checkable identity gate. It grants **zero** model-quality, Whole-GWT, Claude-adapter, canonical-semantics, provider, BASE or whole-product credit by itself.

```clay
contract JSPACE_GWT_BOOT_BINDING_RECEIPT_V1 {
  R0 OBSERVE {
    owner_requirement = "bundled ~0.8B core + fixed versioned J-Space/GWT integration";
    runtime_credit_before_receipt = 0;
    authority = "MiniUnifiedDB + deterministic gates";
    truth_law = "JSPACE_SIGNAL != FACT";
  }

  R1 INFER {
    invariant ARTIFACT_IDENTITY != SEMANTIC_IDENTITY;
    invariant JSPACE_DEFINITION_REQUIRES_SPARSITY_K;
    invariant CLOSED_EXTERNAL_ENGINE != FULL_LOCAL_LATENT;
  }

  R2 GENERATE {
    candidate BYTE_HASH_ONLY;
    candidate BYTE_HASH_PLUS_CANONICAL_SEMANTIC_HASH;
  }

  R3 COUNTER {
    counter BYTE_HASH_PLUS_CANONICAL_SEMANTIC_HASH {
      claim = "semantic normalization can hide meaningful persisted-byte differences";
      answer = "retain both digests; neither replaces the other";
    }
  }

  R4 DISCRIMINATE {
    require source(repo_commit, repo_tree, dirty=false);
    require bundled_core(checkpoint_sha256, tokenizer_sha256, runtime_identity);
    require lens(implementation_commit, artifact_sha256, semantic_content_sha256,
                 fit_corpus_sha256, fit_prompt_count, source_layers, target_layer,
                 finite_check_passed=true);
    require workspace(jspace_profile_sha256, lens_profile_sha256,
                      gwt_policy_sha256, workspace_calibration_sha256,
                      jspace_mode, jspace_sparsity_k, gwt_slot_limit);
    require control_projection(zero_identity_sha256, grf_sha256, hyperposition_state_sha256?);
    require claude_adapter(adapter_version, capability_profile_sha256, transport_profile_sha256);
    require runtime(execution_surface, started=true, first_engine_choice, first_action_origin);
    require FREE_ONLY => paid_or_unknown_network_attempts == 0;
    require FREE_ONLY => paid_or_unknown_secret_lookups == 0;
  }

  R5 EMERGENT {
    law DUAL_LENS_IDENTITY = artifact_sha256 + semantic_content_sha256;
    law PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY;
    law WORKSPACE_POLICY_IDENTITY includes jspace_sparsity_k;
  }

  R6 VERIFY {
    structural_gate = tool("the artefact/blogpost_entity/mini_cognition/jspace_boot_binding_v1.py");
    promotion = "requires an actually-started exact-source authorized runtime receipt";
  }
}
```

## Why two lens digests are mandatory

Anthropic's public Jacobian Lens `save()` persists a PyTorch checkpoint containing `J`, `n_prompts`, `source_layers`, and `d_model`. A raw file digest is necessary supply-chain evidence, but it is not sufficient as the sole semantic identity: serialization details can change bytes while the loaded matrices remain identical. Conversely, a normalized semantic digest must not replace the raw artifact digest because exact persisted bytes still matter for provenance and reproducibility.

The admitted pair is therefore:

- `artifact_sha256`: SHA-256 of the exact persisted lens file bytes;
- `semantic_content_sha256`: domain-separated digest of the loaded J matrices and defining metadata using `ordered-fp32-finite-v1`.

### `ordered-fp32-finite-v1`

1. load with `torch.load(..., map_location="cpu", weights_only=True)`;
2. require exactly the public lens checkpoint fields needed by this contract;
3. require positive `n_prompts` and `d_model`;
4. require sorted, unique, non-negative `source_layers` and exactly matching J-matrix keys;
5. require every J matrix to be exactly `d_model x d_model`;
6. convert each persisted matrix to CPU contiguous IEEE float32;
7. reject NaN, +Inf and -Inf before hashing;
8. encode floats as little-endian float32 in C order;
9. hash a versioned domain separator, `n_prompts`, `d_model`, layer count, then each layer id, shape and matrix bytes in ascending layer order.

The method intentionally hashes the **persisted loaded values**, not an imagined pre-save higher-precision tensor. If a save downcasts values, the persisted semantics change and the semantic digest records those changed values.

## J-Space parameter binding

The current Transformer Circuits definition treats J-lens vectors as an overcomplete frame and defines J-space only after an allowable sparsity `k` is chosen. Therefore a boot receipt that binds lens bytes but omits the active `jspace_sparsity_k` is not a complete identity for the operational J-space. GWT slot limit is separately bound because workspace selection policy is not identical to J-space sparsity.

Neither `jspace_sparsity_k` nor `gwt_slot_limit` receives a canonical default from this contract. Both remain calibration outputs tied to the exact checkpoint/tokenizer/runtime/workspace profile.

## Fail-closed evidence boundary

A valid structural receipt means only:

```text
IDENTITIES_PRESENT + POLICY_FIELDS_VALID + RECEIPT_CANONICALLY_HASHABLE
```

It does **not** mean:

```text
MODEL_WORKED
JSPACE_IS_CORRECT
GWT_IMPROVED_REASONING
CLAUDE_ADAPTER_PASSED
WHOLE_PRODUCT_PASSED
```

Exact runtime credit still requires an actually-started authorized execution surface, clean exact source/tree identity, exact bundled checkpoint/tokenizer/runtime, exact lens artifact+semantic identity, calibrated workspace policy, Zero/GRF projection identity, Claude adapter identity, first-engine/first-action provenance, and FREE_ONLY compliance.

## Current execution note

At contract creation, the project host is intentionally offline and the currently exposed Vercel connector surface does not provide executable Sandbox start/exec operations. Therefore this contract is source/mechanism work only. It must be exercised on the next authorized exact Ubuntu start through the supervisor-required prestart/poststart observation boundary.
