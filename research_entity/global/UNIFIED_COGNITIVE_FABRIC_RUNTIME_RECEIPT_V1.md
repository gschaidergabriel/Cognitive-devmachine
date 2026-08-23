# UNIFIED COGNITIVE FABRIC RUNTIME RECEIPT / v1

Status: SOURCE CONTRACT CANDIDATE
Owner-architecture basis: current 2026-08-23 Mini Entity / EntityOS / Zero + bundled ~0.8B Unified J-Space/GWT architecture
Evidence class: SOURCE ONLY until emitted and validated on exact admitted runtime bytes

## Purpose

Define **one** canonical executable evidence envelope for the Unified Cognitive Workspace Fabric.

The supervisor's previously named `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1` is not a second ledger or competing receipt family. It is the boot phase of this same envelope:

```text
UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1 phase=BOOT_BINDING
```

Subsequent complete cognition evidence uses:

```text
UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1 phase=INFERENCE_CYCLE
```

Required laws:

```text
ONE_COGNITIVE_FABRIC -> ONE_RUNTIME_EVIDENCE_ENVELOPE
NO_PARALLEL_JSPACE_GWT_RECEIPT_AUTHORITY
PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY
COMPILED_EXTERNAL != FULL_LOCAL_LATENT
JSPACE_SIGNAL != FACT
```

The last three laws bind the 2026-08-23 J-Space transfer falsifier: the architecture may transfer across engines/models, but latent geometry, lens profiles, workspace bands, intervention strengths and thresholds do not receive credit unless calibrated on the exact model/tokenizer/runtime identity.

## ClayCode semantic contract

```text
fabric_receipt_v1(
  receipt_type="UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1",
  phase,
  source_exact,
  entity_generation,
  zero_binding,
  bundled_cognition_binding,
  calibration_binding,
  workspace_transition,
  inference_packet,
  candidate_result,
  validation_reconciliation,
  effect_boundary,
  secret_network_counters,
  terminal_digest
)

law(model_output != canonical_truth)
law(model_output != direct_effect_authority)
law(workspace_stability != factual_truth)
law(stale_identity_or_manifest -> reject)
law(FREE_ONLY && (secret_lookup_count>0 || network_attempt_count>0) -> reject)
law(canonical_write -> validation_decision==ACCEPTED_CANDIDATE)
law(effect_admitted -> effect_requested)
law(CLAUDE_CODE -> jspace_mode==COMPILED_EXTERNAL)
law(LOCAL_08B && phase==INFERENCE_CYCLE && jspace_observed -> calibration_status==MEASURED_EXACT)
```

## Evidence groups

### 1. Exact source / executor

Bind:
- exact repository commit and tree OIDs;
- dirty state;
- executor/runtime identity;
- environment digest;
- start/completion timestamps.

Source presence, mergeability, READY status or a runner failure before visible steps gives no executable credit.

### 2. One entity / one generation

Bind:
- Mini Entity version;
- EntityOS version;
- current generation;
- Zero identity digest;
- GRF digest;
- workspace-policy digest.

Stale Zero/GRF/generation inputs fail closed.

### 3. Bundled ~0.8B cognition identity

Bind the exact bundled manifest plus:
- checkpoint digest;
- tokenizer digest;
- J-Space profile digest;
- lens profile digest;
- workspace calibration digest;
- quantization/runtime identity.

Changing inference engines or upgrading weights never resets MiniUnifiedDB continuity.

### 4. Calibration provenance

The receipt explicitly records whether the current bundled-core geometry is:
- `UNCALIBRATED`;
- `BOUND_EXACT` — exact identities match, but promotion measurements are incomplete;
- `MEASURED_EXACT` — exact identity plus the required empirical calibration set is present.

Calibration binds its own checkpoint/tokenizer/runtime/lens/workspace-calibration identities back to the bundled-core identities. Cross-model or cross-runtime silent reuse is rejected.

For `MEASURED_EXACT`, the receipt also records completed evidence for:
- model-specific workspace-band measurement;
- causal intervention/ablation measurement;
- multi-token/OOD failure coverage;
- comparison against a simpler baseline.

`BOOT_BINDING` may truthfully expose `UNCALIBRATED`/`BOUND_EXACT`; it does not manufacture runtime J-Space credit.

A local `INFERENCE_CYCLE` that claims J-Space observations from the bundled 0.8B core requires `MEASURED_EXACT`.

### 5. Unified J-Space/GWT transition

Bind:
- workspace digest before/after competition;
- GWT candidate refs, admission and winner;
- J-Space observation refs;
- Thalamus decisions;
- EPQ digest;
- Hyperposition, ClayCode and omega refs.

At most one winner is admitted by this v1 envelope. A winner must itself be admitted.

### 6. Engine scheduling

Engine class is one of:
- `LOCAL_08B`;
- `CLAUDE_CODE`;
- `ADAPTIVE_BACKEND`;
- `DETERMINISTIC_ONLY`.

Claude Code must bind adapter version + capability-profile digest and must declare `COMPILED_EXTERNAL`; no public/private latent access is inferred from the Claude name.

Adaptive engines bind a capability profile and one explicit J-Space mode:
- `FULL_LOCAL_LATENT`;
- `LOCAL_OBSERVE_ONLY`;
- `COMPILED_EXTERNAL`;
- `PLAIN_COMPATIBILITY`.

### 7. Candidate-only return / reconciliation

Every learned/external result returns as candidate inference. Bind:
- full `InferencePacket` digest;
- candidate-result digest (or null for deterministic-only);
- `candidate_only=true`;
- deterministic reconciliation digest/decision;
- canonical-write decision;
- effect request/admission decision.

No model result directly mints canonical truth or effects.

### 8. FREE_ONLY boundary

Record explicit secret/key lookup and network-attempt counters.

With `FREE_ONLY=true`, any PAID/SUBSCRIPTION/UNKNOWN external touch is rejected. Current control remains stricter than owner campaign wording.

### 9. Terminal identity

Bind terminal status and SHA-256 over canonical JSON with `terminal_digest` omitted from its own preimage. Unknown/aborted results remain explicit.

## `BOOT_BINDING`

At the next intentional Ubuntu host start this is the first observation boundary. It binds frozen prestart lineage to exact poststart source/executor, one generation, Zero/GRF, bundled 0.8B identities/calibration status, workspace identity, Claude adapter capability identity when present, first engine class, first-action origin, and secret/network counters.

This phase **satisfies** the supervisor's `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1` requirement. Do not emit a separate competing ledger for the same evidence boundary.

## `INFERENCE_CYCLE`

Binds one full cycle:

```text
canonical state/evidence
-> Zero/GRF projection
-> unified J-Space/GWT competition
-> engine scheduling
-> InferencePacket
-> candidate result
-> deterministic validation/reconciliation
-> canonical write/effect decision
```

Strong negative controls remain:
- stale Zero/GRF/generation;
- stale bundled manifest;
- calibration geometry copied from a different checkpoint/tokenizer/runtime;
- local J-Space claim without `MEASURED_EXACT`;
- Claude claiming `FULL_LOCAL_LATENT`;
- adaptive capability mismatch;
- multiple GWT winners;
- candidate direct-state/effect authority;
- workspace stable while evidence is factually wrong;
- FREE_ONLY external touch;
- post-receipt mutation.

## Validator

`the artefact/blogpost_entity/validate_unified_cognitive_fabric_receipt_v1.py` implements the deterministic source-level envelope checks.

`the artefact/blogpost_entity/test_unified_cognitive_fabric_receipt_v1.py` defines regression cases. These source tests do **not** create runtime credit until exact branch/runtime bytes actually execute on an admitted surface.

## Promotion boundary

This contract creates no bundled-core, J-Space, GWT, Claude, model-quality, BASE, Whole-GWT, provider, training, resource or whole-product PASS by itself.

Exact runtime acceptance remains blocked until an intentionally started, exact-source Ubuntu path emits and validates the relevant phase receipt while all higher-priority FREE_ONLY, truth, provenance, effect and Harness-immutability laws remain satisfied.
